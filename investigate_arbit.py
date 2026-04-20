#!/usr/bin/env python3
"""
Deep investigation of ArbitrageETHStaking - Owner is zero address!
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

ARBIT = "0x5eee354e36ac51e9d3f7283005cab0c55f423b23"
ATTACKER = "0xDeaDbeefdEAdbeefdEadbEEFdeadbeEFdEaDbeeF"

print("=" * 80)
print("ARBITRAGE ETH STAKING - DETAILED ANALYSIS")
print("=" * 80)

# Get full source
source = get_source(ARBIT)
if source:
    src = source.get("SourceCode", "")
    print("\n=== FULL SOURCE CODE ===\n")
    print(src)
    print("\n" + "=" * 80)

# Check contract state
print("\n=== CONTRACT STATE ===")

# owner()
owner_result = eth_call(ARBIT, "0x8da5cb5b")
if owner_result and "result" in owner_result:
    owner = "0x" + owner_result["result"][-40:]
    print(f"Owner: {owner}")

# Check all storage slots
print("\nStorage slots:")
for slot in range(20):
    storage = rpc_call("eth_getStorageAt", [ARBIT, hex(slot), "latest"])
    if storage and "result" in storage:
        val = storage["result"]
        val_int = int(val, 16)
        if val_int != 0:
            if val_int < 2**160 and val_int > 1000:
                print(f"  Slot {slot}: 0x{val[-40:]} (address)")
            elif val_int < 1e12:
                print(f"  Slot {slot}: {val_int}")
            else:
                print(f"  Slot {slot}: {val_int / 1e18:.4f} (ETH scale)")

# Get balance
bal_resp = rpc_call("eth_getBalance", [ARBIT, "latest"])
balance = int(bal_resp['result'], 16) / 1e18
print(f"\nContract ETH Balance: {balance:.2f} ETH")

# Check if there are any onlyOwner functions that could be exploited
# Since owner is 0x0, if we can call from 0x0 (we can't), we'd have access
# OR if there's a function that doesn't properly check and allows withdrawal

print("\n=== TESTING FUNCTION CALLS ===")

# Try calling various functions
funcs = [
    ("0x3ccfd60b", "withdraw()"),
    ("0xd0e30db0", "deposit()"),
]

for sel, name in funcs:
    gas_resp = rpc_call("eth_estimateGas", [{"from": ATTACKER, "to": ARBIT, "data": sel}, "latest"])
    if gas_resp and "result" in gas_resp:
        print(f"{name}: Gas estimate = {int(gas_resp['result'], 16)}")
    elif gas_resp and "error" in gas_resp:
        print(f"{name}: REVERTS - {gas_resp['error'].get('message', '')[:60]}")

