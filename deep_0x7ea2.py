#!/usr/bin/env python3
"""
Deep investigation of 0x7ea2 withdraw behavior
"""
import json
import subprocess

RPC = "https://mainnet.infura.io/v3/bfc7283659224dd6b5124ebbc2b14e2c"

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

ADDR = "0x7ea2df0f49d1cf7cb3a328f0038822b08aeb0ac1"
ATTACKER = "0xDeaDbeefdEAdbeefdEadbEEFdeadbeEFdEaDbeeF"

print("=" * 80)
print("DEEP WITHDRAW ANALYSIS")
print("=" * 80)

# Call withdraw() and check result
withdraw_resp = eth_call(ADDR, "0x3ccfd60b", ATTACKER)
print(f"withdraw() result: {withdraw_resp}")

# Check balanceOf(attacker)
balance_data = "0x70a08231" + "000000000000000000000000" + ATTACKER[2:].lower()
balance_resp = eth_call(ADDR, balance_data)
print(f"balanceOf(attacker): {balance_resp}")

# Check totalSupply
supply_resp = eth_call(ADDR, "0x18160ddd")
print(f"totalSupply(): {supply_resp}")

# Try all found function selectors
bytecode = rpc_call("eth_getCode", [ADDR, "latest"])
code = bytecode.get("result", "") if bytecode else ""

print("\n=== Testing all selectors with attacker ===")

# Find PUSH4 selectors
selectors = set()
for i in range(0, len(code) - 10, 2):
    if code[i:i+2] == "63":
        sel = code[i+2:i+10]
        if len(sel) == 8 and sel[0:2] not in ['00', 'ff']:
            selectors.add(sel)

for sel in sorted(selectors)[:20]:  # Test first 20
    gas_resp = rpc_call("eth_estimateGas", [{"from": ATTACKER, "to": ADDR, "data": "0x" + sel}, "latest"])
    if gas_resp and "result" in gas_resp:
        gas = int(gas_resp["result"], 16)
        if gas > 21100 and gas != 67764:  # Skip base cost and our known withdraw gas
            result = eth_call(ADDR, "0x" + sel, ATTACKER)
            r = result.get("result", "0x") if result else "error"
            print(f"  0x{sel}: gas={gas}, returns={r[:40]}...")

# Look for name/symbol to identify the token
print("\n=== Token identity ===")
name_resp = eth_call(ADDR, "0x06fdde03")
if name_resp and "result" in name_resp and len(name_resp["result"]) > 66:
    result = name_resp["result"]
    try:
        # String starts at offset 64, length at 64-128, data after
        str_offset = int(result[2:66], 16) * 2
        str_len = int(result[66:130], 16)
        str_data = result[130:130+str_len*2]
        name = bytes.fromhex(str_data).decode('utf-8', errors='ignore')
        print(f"Name: {name}")
    except:
        print(f"Name (raw): {result[:80]}")

symbol_resp = eth_call(ADDR, "0x95d89b41")
if symbol_resp and "result" in symbol_resp and len(symbol_resp["result"]) > 66:
    result = symbol_resp["result"]
    try:
        str_offset = int(result[2:66], 16) * 2
        str_len = int(result[66:130], 16)
        str_data = result[130:130+str_len*2]
        symbol = bytes.fromhex(str_data).decode('utf-8', errors='ignore')
        print(f"Symbol: {symbol}")
    except:
        print(f"Symbol (raw): {result[:80]}")

decimals_resp = eth_call(ADDR, "0x313ce567")
if decimals_resp and "result" in decimals_resp:
    result = decimals_resp["result"]
    if result and result != "0x":
        print(f"Decimals: {int(result, 16)}")

