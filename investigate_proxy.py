#!/usr/bin/env python3
"""
Deep investigation of AdminUpgradeabilityProxy - 291 ETH
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

PROXY = "0xf74bf048138a2b8f825eccabed9e02e481a0f6c0"

print("=" * 80)
print("AdminUpgradeabilityProxy Analysis")
print("=" * 80)

# EIP-1967 slots
IMPL_SLOT = "0x360894a13ba1a3210667c828492db98dca3e2076cc3735a920a3ca505d382bbc"
ADMIN_SLOT = "0xb53127684a568b3173ae13b9f8a6016e243e63b6e8ee1178d6a717850b5d6103"

# Get implementation
impl_resp = rpc_call("eth_getStorageAt", [PROXY, IMPL_SLOT, "latest"])
impl = "0x" + impl_resp["result"][-40:] if impl_resp else None
print(f"Implementation: {impl}")

# Get admin
admin_resp = rpc_call("eth_getStorageAt", [PROXY, ADMIN_SLOT, "latest"])
admin = "0x" + admin_resp["result"][-40:] if admin_resp else None
print(f"Admin: {admin}")

# Get balance
bal = rpc_call("eth_getBalance", [PROXY, "latest"])
print(f"Balance: {int(bal['result'], 16) / 1e18:.2f} ETH")

# Check if implementation is a contract
if impl:
    code = rpc_call("eth_getCode", [impl, "latest"])
    code_len = (len(code.get("result", "0x")) - 2) // 2 if code else 0
    print(f"Implementation code length: {code_len} bytes")
    
    # Try to get source
    source = get_source(impl)
    if source:
        print(f"Implementation contract name: {source.get('ContractName', 'Unknown')}")
        src = source.get("SourceCode", "")
        if src:
            print(f"Source length: {len(src)} chars")
    else:
        print("Implementation source not verified")

# Check admin contract
if admin:
    admin_code = rpc_call("eth_getCode", [admin, "latest"])
    admin_code_len = (len(admin_code.get("result", "0x")) - 2) // 2 if admin_code else 0
    print(f"\nAdmin code length: {admin_code_len} bytes")
    
    if admin_code_len > 0:
        admin_source = get_source(admin)
        if admin_source:
            print(f"Admin contract name: {admin_source.get('ContractName', 'Unknown')}")

# Check what the proxy forwards to
print("\n=== Testing proxy functions ===")

# Common function selectors
test_funcs = [
    ("0x8da5cb5b", "owner()"),
    ("0x5c60da1b", "implementation()"),
    ("0xf851a440", "admin()"),
    ("0x3ccfd60b", "withdraw()"),
]

for sel, name in test_funcs:
    resp = rpc_call("eth_call", [{"to": PROXY, "data": sel}, "latest"])
    if resp and "result" in resp:
        result = resp["result"]
        if result != "0x" and len(result) > 2:
            if len(result) == 66:
                # Might be address
                print(f"{name}: 0x{result[-40:]}")
            else:
                print(f"{name}: {result[:66]}...")

# Check proxy source
print("\n=== Proxy Source ===")
proxy_source = get_source(PROXY)
if proxy_source:
    src = proxy_source.get("SourceCode", "")
    print(f"Source length: {len(src)} chars")
    
    # Look for admin-only functions
    if "onlyAdmin" in src or "ifAdmin" in src:
        print("Has admin modifier")
    
    # Look for upgrade functions
    if "upgradeTo" in src:
        print("Has upgradeTo function")
    if "upgradeToAndCall" in src:
        print("Has upgradeToAndCall function")

