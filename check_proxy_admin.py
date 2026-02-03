#!/usr/bin/env python3
"""
Check ProxyAdmin ownership and implementation
"""
import json
import subprocess

RPC = "https://mainnet.infura.io/v3/bfc7283659224dd6b5124ebbc2b14e2c"
ETHERSCAN_API = "5UWN6DNT7UZCEJYNE3J6FCVAWH4QJW255K"

def rpc_call(method, params):
    payload = {"jsonrpc": "2.0", "method": method, "params": params, "id": 1}
    cmd = ["curl", "-s", "-X", "POST", "-H", "Content-Type: application/json",
           "-d", json.dumps(payload), RPC]
    result = subprocess.run(cmd, capture_output=True, text=True)
    try:
        return json.loads(result.stdout)
    except:
        return None

def eth_call(to, data):
    return rpc_call("eth_call", [{"to": to, "data": data}, "latest"])

def get_source(addr):
    url = f"https://api.etherscan.io/v2/api?chainid=1&module=contract&action=getsourcecode&address={addr}&apikey={ETHERSCAN_API}"
    result = subprocess.run(["curl", "-s", url], capture_output=True, text=True)
    try:
        data = json.loads(result.stdout)
        if data.get("status") == "1" and data.get("result"):
            return data["result"][0]
        return None
    except:
        return None

PROXY_ADMIN = "0x94ace08a344efa23ac118aa94a66a8d699e8a1a1"
PROXY = "0xf74bf048138a2b8f825eccabed9e02e481a0f6c0"
IMPL = "0x0634ee9e5163389a04b3ff6c9b05de71c24c1916"

print("=" * 80)
print("ProxyAdmin Analysis")
print("=" * 80)

# Check ProxyAdmin owner
owner_resp = eth_call(PROXY_ADMIN, "0x8da5cb5b")  # owner()
if owner_resp and "result" in owner_resp:
    owner = "0x" + owner_resp["result"][-40:]
    print(f"ProxyAdmin owner: {owner}")
    
    # Check if owner is EOA or contract
    owner_code = rpc_call("eth_getCode", [owner, "latest"])
    owner_code_len = (len(owner_code.get("result", "0x")) - 2) // 2 if owner_code else 0
    if owner_code_len == 0:
        print(f"Owner is EOA")
    else:
        print(f"Owner is contract ({owner_code_len} bytes)")

# Get ProxyAdmin source
source = get_source(PROXY_ADMIN)
if source:
    src = source.get("SourceCode", "")
    print(f"\nProxyAdmin source length: {len(src)} chars")
    
    # Print key functions
    lines = src.split('\n')
    for i, line in enumerate(lines):
        if 'function' in line and ('upgrade' in line.lower() or 'change' in line.lower()):
            print(f"  {line.strip()[:80]}")

print("\n" + "=" * 80)
print("Implementation Analysis (0x0634...)")
print("=" * 80)

# Check implementation bytecode for known patterns
impl_code = rpc_call("eth_getCode", [IMPL, "latest"])
code = impl_code.get("result", "") if impl_code else ""
print(f"Code length: {(len(code)-2)//2} bytes")

# Try common selectors on implementation (via proxy)
print("\nTesting implementation functions via proxy:")
selectors = [
    ("0x8da5cb5b", "owner()"),
    ("0x3ccfd60b", "withdraw()"),
    ("0x2e1a7d4d", "withdraw(uint256)"),
    ("0x12065fe0", "getBalance()"),
    ("0x70a08231", "balanceOf(address)"),  # need to add address param
]

for sel, name in selectors:
    resp = eth_call(PROXY, sel)
    if resp and "result" in resp:
        result = resp["result"]
        if result and result != "0x":
            if len(result) == 66:
                val = int(result, 16)
                if val < 2**160 and val > 0:
                    print(f"  {name}: 0x{result[-40:]}")
                else:
                    print(f"  {name}: {val}")
            else:
                print(f"  {name}: {result[:40]}...")

# Check implementation storage slots
print("\nImplementation storage (via proxy):")
for slot in range(10):
    storage = rpc_call("eth_getStorageAt", [PROXY, hex(slot), "latest"])
    if storage and "result" in storage:
        val = int(storage["result"], 16)
        if val != 0:
            if val < 2**160 and val > 1000:
                print(f"  Slot {slot}: 0x{storage['result'][-40:]} (address)")
            elif val < 1000:
                print(f"  Slot {slot}: {val}")
            else:
                print(f"  Slot {slot}: {val} ({val / 1e18:.4f} if ETH)")

