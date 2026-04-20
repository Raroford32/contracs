#!/usr/bin/env python3
"""
Check for upgrade/ownership takeover vectors
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

def get_balance(addr):
    result = rpc_call("eth_getBalance", [addr, "latest"])
    if result and 'result' in result:
        return int(result['result'], 16) / 1e18
    return 0

def get_source(addr):
    url = f"https://api.etherscan.io/v2/api?chainid=1&module=contract&action=getsourcecode&address={addr}&apikey={ETHERSCAN_API}"
    result = subprocess.run(["curl", "-s", url], capture_output=True, text=True)
    try:
        data = json.loads(result.stdout)
        if data.get("status") == "1" and data.get("result"):
            return data["result"][0]
    except:
        pass
    return None

# Load contracts
with open("contracts.txt", "r") as f:
    contracts = [line.strip() for line in f if line.strip().startswith("0x")]

print("=" * 80)
print("CHECKING FOR UPGRADE/OWNERSHIP TAKEOVER VECTORS")
print("=" * 80)

upgrade_vectors = []

for i, addr in enumerate(contracts):
    if i % 30 == 0:
        print(f"Scanning {i}/{len(contracts)}...")

    balance = get_balance(addr)
    if balance < 50:  # Skip low balance
        continue

    time.sleep(0.25)

    # Check for unprotected upgrade functions
    upgrade_funcs = {
        "0x3659cfe6": "upgradeTo(address)",
        "0x4f1ef286": "upgradeToAndCall(address,bytes)",
        "0xf2fde38b": "transferOwnership(address)",
        "0x715018a6": "renounceOwnership()",
        "0xe30c3978": "pendingOwner()",
        "0x79ba5097": "acceptOwnership()",
        "0x8129fc1c": "initialize()",
        "0xc4d66de8": "initialize(address)",
        "0x485cc955": "initialize(address,address)",
    }

    for selector, func_name in upgrade_funcs.items():
        # Add dummy parameter for functions with args
        data = selector
        if "address" in func_name:
            data = selector + "0000000000000000000000000000000000000000000000000000000000000001"
        if "bytes" in func_name:
            data = data[:10+64] + "0000000000000000000000000000000000000000000000000000000000000040"
            data = data + "0000000000000000000000000000000000000000000000000000000000000000"

        # Try estimating gas (checks if callable)
        result = rpc_call("eth_estimateGas", [{
            "to": addr,
            "data": data,
            "from": "0x0000000000000000000000000000000000000001"
        }])

        if result and 'result' in result:
            gas = int(result['result'], 16)
            if gas < 200000:  # Reasonable gas means function exists and might be callable
                # Verify with actual call
                call_result = rpc_call("eth_call", [{
                    "to": addr,
                    "data": data,
                    "from": "0x0000000000000000000000000000000000000001"
                }, "latest"])

                err = call_result.get('error', {}).get('message', '') if call_result else ''
                res = call_result.get('result', '') if call_result else ''

                if 'revert' not in err.lower() and 'ownable' not in err.lower():
                    finding = {
                        "address": addr,
                        "balance": balance,
                        "function": func_name,
                        "gas": gas,
                        "result": res[:66] if res else err[:50]
                    }
                    upgrade_vectors.append(finding)
                    print(f"\n[!!] {addr} ({balance:.1f} ETH)")
                    print(f"     {func_name} callable! Gas: {gas}")
                    print(f"     Result: {res[:66] if res else err[:50]}")

# Summary
print("\n" + "=" * 80)
print("UPGRADE/OWNERSHIP VECTORS FOUND")
print("=" * 80)

for v in upgrade_vectors:
    print(f"\n{v['address']} ({v['balance']:.2f} ETH)")
    print(f"  Function: {v['function']}")
    print(f"  Gas: {v['gas']}")

with open("upgrade_vectors.json", "w") as f:
    json.dump(upgrade_vectors, f, indent=2)

print(f"\n[*] Found {len(upgrade_vectors)} potential upgrade vectors")
