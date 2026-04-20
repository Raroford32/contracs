#!/usr/bin/env python3
"""
Deep investigation of promising targets
"""
import json
import subprocess
import time

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

def eth_call(to, data, from_addr=None):
    call_obj = {"to": to, "data": data}
    if from_addr:
        call_obj["from"] = from_addr
    return rpc_call("eth_call", [call_obj, "latest"])

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

print("=" * 80)
print("INVESTIGATION 1: ArbitrageETHStaking (0x5eee...)")
print("=" * 80)

ARBIT = "0x5eee354e36ac51e9d3f7283005cab0c55f423b23"

# Get source
source = get_source(ARBIT)
if source:
    src = source.get("SourceCode", "")
    print(f"Source code length: {len(src)} chars")
    print("\n--- Relevant code snippets ---")
    
    # Find withdraw and interesting functions
    lines = src.split('\n')
    for i, line in enumerate(lines):
        if any(x in line.lower() for x in ['withdraw', 'owner', 'require', 'transfer', 'balance']):
            if 'function' in line.lower() or 'require' in line.lower():
                print(f"{i}: {line.strip()[:100]}")

print()

# Check owner
# owner() selector = 0x8da5cb5b
owner_result = eth_call(ARBIT, "0x8da5cb5b")
if owner_result and "result" in owner_result:
    owner = "0x" + owner_result["result"][-40:]
    print(f"Owner: {owner}")

# Check balance in contract
bal_resp = rpc_call("eth_getBalance", [ARBIT, "latest"])
print(f"ETH Balance: {int(bal_resp['result'], 16) / 1e18:.2f} ETH")

print("\n" + "=" * 80)
print("INVESTIGATION 2: AdminUpgradeabilityProxy (0xf74b...)")
print("=" * 80)

PROXY = "0xf74bf048138a2b8f825eccabed9e02e481a0f6c0"

source = get_source(PROXY)
if source:
    print(f"Contract: {source.get('ContractName')}")
    print(f"Implementation slot check...")

# Standard proxy storage slot for implementation
# EIP-1967: bytes32(uint256(keccak256('eip1967.proxy.implementation')) - 1)
IMPL_SLOT = "0x360894a13ba1a3210667c828492db98dca3e2076cc3735a920a3ca505d382bbc"
impl_result = rpc_call("eth_getStorageAt", [PROXY, IMPL_SLOT, "latest"])
if impl_result and "result" in impl_result:
    impl = "0x" + impl_result["result"][-40:]
    print(f"Implementation (EIP-1967): {impl}")
    
    # Get implementation source
    time.sleep(0.3)
    impl_source = get_source(impl)
    if impl_source:
        print(f"Implementation contract: {impl_source.get('ContractName')}")

# Admin slot
ADMIN_SLOT = "0xb53127684a568b3173ae13b9f8a6016e243e63b6e8ee1178d6a717850b5d6103"
admin_result = rpc_call("eth_getStorageAt", [PROXY, ADMIN_SLOT, "latest"])
if admin_result and "result" in admin_result:
    admin = "0x" + admin_result["result"][-40:]
    print(f"Admin (EIP-1967): {admin}")

bal_resp = rpc_call("eth_getBalance", [PROXY, "latest"])
print(f"ETH Balance: {int(bal_resp['result'], 16) / 1e18:.2f} ETH")

print("\n" + "=" * 80)
print("INVESTIGATION 3: Unverified Contract (0xa1a1...)")  
print("=" * 80)

UNVERIFIED = "0xa1a111bc074c9cfa781f0c38e63bd51c91b8af00"

# Get bytecode
code_resp = rpc_call("eth_getCode", [UNVERIFIED, "latest"])
code = code_resp.get("result", "") if code_resp else ""
print(f"Bytecode length: {(len(code)-2)//2} bytes")
print(f"Bytecode: {code[:200]}...")

# Try common function selectors
selectors = {
    "0x8da5cb5b": "owner()",
    "0x3ccfd60b": "withdraw()",
    "0x2e1a7d4d": "withdraw(uint256)",
    "0x51cff8d9": "withdraw(address)",
    "0x12065fe0": "getBalance()",
    "0x893d20e8": "getOwner()",
    "0xf2fde38b": "transferOwnership(address)",
}

print("\nTrying common function selectors:")
for sel, name in selectors.items():
    result = eth_call(UNVERIFIED, sel)
    if result and "result" in result:
        val = result["result"]
        if val != "0x" and len(val) > 2:
            print(f"  {name}: {val[:66]}...")

# Check storage
print("\nStorage slots:")
for slot in range(10):
    storage = rpc_call("eth_getStorageAt", [UNVERIFIED, hex(slot), "latest"])
    if storage and "result" in storage:
        val = storage["result"]
        if int(val, 16) != 0:
            print(f"  Slot {slot}: {val}")

bal_resp = rpc_call("eth_getBalance", [UNVERIFIED, "latest"])
print(f"ETH Balance: {int(bal_resp['result'], 16) / 1e18:.2f} ETH")

print("\n" + "=" * 80)
print("INVESTIGATION 4: MoonCatRescue (0x60cd...)")
print("=" * 80)

MOONCAT = "0x60cd862c9c687a9de49aecdc3a99b74a4fc54ab6"

source = get_source(MOONCAT)
if source:
    src = source.get("SourceCode", "")
    print(f"Contract: {source.get('ContractName')}")
    print(f"Source length: {len(src)} chars")
    
    # Look for withdrawal functions
    if "withdraw" in src.lower():
        lines = src.split('\n')
        in_withdraw = False
        for i, line in enumerate(lines):
            if 'function' in line.lower() and 'withdraw' in line.lower():
                in_withdraw = True
            if in_withdraw:
                print(f"  {line.rstrip()[:100]}")
                if '}' in line and line.strip().startswith('}'):
                    in_withdraw = False
                    print("  ---")

bal_resp = rpc_call("eth_getBalance", [MOONCAT, "latest"])
print(f"ETH Balance: {int(bal_resp['result'], 16) / 1e18:.2f} ETH")

