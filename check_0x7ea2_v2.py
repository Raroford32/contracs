#!/usr/bin/env python3
"""
Deep check of 0x7ea2df0f49d1cf7cb3a328f0038822b08aeb0ac1 (261 ETH)
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
OWNER_SLOT0 = "0x331d077518216c07c87f4f18ba64cd384c411f84"

print("=" * 80)
print(f"ANALYZING: {ADDR}")
print("=" * 80)

# Get bytecode  
code = rpc_call("eth_getCode", [ADDR, "latest"])
if code and "result" in code:
    bytecode = code["result"]
    print(f"Bytecode length: {(len(bytecode)-2)//2} bytes")
    print(f"First 100 chars: {bytecode[:100]}")

# The address at slot 0 is likely the owner
print(f"\nLikely owner (slot 0): {OWNER_SLOT0}")

# Test withdraw from owner address vs attacker
print("\n=== Testing withdraw() ===")

# As attacker
gas1 = rpc_call("eth_estimateGas", [{"from": ATTACKER, "to": ADDR, "data": "0x3ccfd60b"}, "latest"])
if gas1 and "result" in gas1:
    print(f"withdraw() as ATTACKER: gas = {int(gas1['result'], 16)}")
elif gas1 and "error" in gas1:
    print(f"withdraw() as ATTACKER: REVERTS - {gas1['error'].get('message', '')[:50]}")

# As owner
gas2 = rpc_call("eth_estimateGas", [{"from": OWNER_SLOT0, "to": ADDR, "data": "0x3ccfd60b"}, "latest"])
if gas2 and "result" in gas2:
    print(f"withdraw() as OWNER: gas = {int(gas2['result'], 16)}")
elif gas2 and "error" in gas2:
    print(f"withdraw() as OWNER: REVERTS - {gas2['error'].get('message', '')[:50]}")

# Check if owner is EOA
owner_code = rpc_call("eth_getCode", [OWNER_SLOT0, "latest"])
if owner_code and "result" in owner_code:
    code_len = (len(owner_code["result"]) - 2) // 2
    if code_len == 0:
        print(f"Owner is EOA (no code)")
    else:
        print(f"Owner is contract ({code_len} bytes)")

# Try to decompile - find function selectors in bytecode
print("\n=== Function selectors ===")
bytecode = code["result"] if code else ""
# Look for PUSH4 (0x63) patterns
selectors = set()
for i in range(0, len(bytecode) - 10, 2):
    if bytecode[i:i+2] == "63":
        sel = bytecode[i+2:i+10]
        if len(sel) == 8:
            selectors.add(sel)

# Known selectors
known = {
    "3ccfd60b": "withdraw()",
    "8da5cb5b": "owner()",
    "f2fde38b": "transferOwnership(address)",
    "2e1a7d4d": "withdraw(uint256)",
    "18160ddd": "totalSupply()",
    "70a08231": "balanceOf(address)",
}

for sel in sorted(selectors):
    name = known.get(sel, "unknown")
    if name != "unknown":
        print(f"  0x{sel}: {name}")

