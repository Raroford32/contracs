#!/usr/bin/env python3
"""
Deep check of 0x7ea2df0f49d1cf7cb3a328f0038822b08aeb0ac1 (261 ETH)
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

ADDR = "0x7ea2df0f49d1cf7cb3a328f0038822b08aeb0ac1"
ATTACKER = "0xDeaDbeefdEAdbeefdEadbEEFdeadbeEFdEaDbeeF"

print("=" * 80)
print(f"ANALYZING: {ADDR}")
print("=" * 80)

# Get balance
bal = rpc_call("eth_getBalance", [ADDR, "latest"])
print(f"Balance: {int(bal['result'], 16) / 1e18:.2f} ETH")

# Get source
source = get_source(ADDR)
if source:
    name = source.get("ContractName", "")
    src = source.get("SourceCode", "")
    print(f"Contract: {name}")
    
    if src:
        # Find relevant functions
        lines = src.split('\n')
        print("\n=== KEY FUNCTIONS ===")
        
        for keyword in ['withdraw', 'owner', 'admin', 'transfer']:
            found = False
            for i, line in enumerate(lines):
                if f'function' in line.lower() and keyword in line.lower():
                    if not found:
                        print(f"\n--- {keyword} functions ---")
                        found = True
                    print(f"{i}: {line.strip()[:80]}")
        
        # Check for access control
        print("\n=== ACCESS CONTROL ===")
        for i, line in enumerate(lines):
            if 'require' in line.lower() and ('owner' in line.lower() or 'admin' in line.lower() or 'msg.sender' in line.lower()):
                print(f"{i}: {line.strip()[:100]}")
else:
    print("Source not verified")

# Check storage
print("\n=== STORAGE ===")
for slot in range(15):
    storage = rpc_call("eth_getStorageAt", [ADDR, hex(slot), "latest"])
    if storage and "result" in storage:
        val = int(storage["result"], 16)
        if val != 0:
            if val < 2**160 and val > 1000:
                print(f"Slot {slot}: 0x{storage['result'][-40:]} (address)")
            elif val < 1000:
                print(f"Slot {slot}: {val}")
            else:
                print(f"Slot {slot}: {val / 1e18:.4f} (if ETH scale)")

# Test functions
print("\n=== FUNCTION TESTS ===")

# Owner
owner_resp = eth_call(ADDR, "0x8da5cb5b")
if owner_resp and "result" in owner_resp:
    result = owner_resp["result"]
    if result and int(result, 16) != 0:
        owner = "0x" + result[-40:]
        print(f"owner(): {owner}")

# Test withdraw as attacker
withdraw_resp = rpc_call("eth_estimateGas", [{"from": ATTACKER, "to": ADDR, "data": "0x3ccfd60b"}, "latest"])
if withdraw_resp and "result" in withdraw_resp:
    gas = int(withdraw_resp["result"], 16)
    print(f"withdraw() gas estimate: {gas}")
    
    # Actually call it to see return
    call_resp = eth_call(ADDR, "0x3ccfd60b", ATTACKER)
    print(f"withdraw() eth_call: {call_resp}")

# Check if it's a token contract
name_resp = eth_call(ADDR, "0x06fdde03")  # name()
if name_resp and "result" in name_resp:
    result = name_resp["result"]
    if result and len(result) > 66:
        # Decode string
        try:
            hex_str = result[130:]  # Skip offset and length
            name = bytes.fromhex(hex_str.rstrip('0')).decode('utf-8', errors='ignore')
            print(f"Token name: {name}")
        except:
            pass

symbol_resp = eth_call(ADDR, "0x95d89b41")  # symbol()
if symbol_resp and "result" in symbol_resp:
    result = symbol_resp["result"]
    if result and len(result) > 66:
        try:
            hex_str = result[130:]
            symbol = bytes.fromhex(hex_str.rstrip('0')).decode('utf-8', errors='ignore')
            print(f"Token symbol: {symbol}")
        except:
            pass

