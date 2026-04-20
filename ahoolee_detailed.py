#!/usr/bin/env python3
"""
Detailed analysis of AhooleeTokenSale - checking all state variables
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

def eth_call(to, data, from_addr="0x0000000000000000000000000000000000000001"):
    result = rpc_call("eth_call", [{"to": to, "data": data, "from": from_addr}, "latest"])
    return result

def get_storage(addr, slot):
    result = rpc_call("eth_getStorageAt", [addr, slot, "latest"])
    if result and 'result' in result:
        return result['result']
    return None

def get_balance(addr):
    result = rpc_call("eth_getBalance", [addr, "latest"])
    if result and 'result' in result:
        return int(result['result'], 16) / 1e18
    return 0

TARGET = "0x575cb87ab3c2329a0248c7d70e0ead8e57f3e3f7"

print("=" * 80)
print("AHOOLEE TOKEN SALE - DETAILED STATE ANALYSIS")
print("=" * 80)
print(f"Balance: {get_balance(TARGET):.4f} ETH")

# Function selectors from the source code
state_vars = {
    "owner()": "0x8da5cb5b",
    "symbol()": "0x95d89b41",
    "token()": "0xfc0c546a",
    "beneficiary()": "0x38af3eed",
    "collected()": "0x71192b17",
    "totalSold()": "0xe3a9db1a",
    "tokensPerEthPrice()": "0xdb741be0",
    "startTime()": "0x78e97925",
    "softCap()": "0x36b29447",
    "hardCapLow()": "0x38e64a51",
    "endTime()": "0x3197cbb6",
    "hardCapHigh()": "0x5dc0c8e5",
    "softCapReached()": "0xe7c34e39",
    "crowdsaleFinished()": "0x9c3a82eb",
}

print("\n[STATE VARIABLES]")
for name, sel in state_vars.items():
    result = eth_call(TARGET, sel)
    if result and result.get('result'):
        r = result['result']
        if r == "0x" or len(r) < 4:
            print(f"  {name}: (empty)")
            continue
        try:
            val = int(r, 16)
            if name == "symbol()":
                # Decode string
                print(f"  {name}: (bytes)")
            elif "address" in name.lower() or name in ["owner()", "token()", "beneficiary()"]:
                addr = "0x" + r[26:]
                print(f"  {name}: {addr}")
            elif val > 10**15 and val < 10**22:  # Likely ETH/wei
                print(f"  {name}: {val/1e18:.4f} ETH ({val} wei)")
            elif val > 1500000000 and val < 2000000000:  # Likely timestamp
                from datetime import datetime
                dt = datetime.fromtimestamp(val)
                print(f"  {name}: {val} ({dt})")
            else:
                print(f"  {name}: {val}")
        except:
            print(f"  {name}: {r[:66]}")
    else:
        print(f"  {name}: (error)")

# Detailed storage analysis
print("\n[STORAGE SLOTS DECODED]")
# Based on source code layout:
# 0: owner
# 1: symbol
# 2: token
# 3: beneficiary
# 4: collected
# 5: totalSold
# 6: tokensPerEthPrice
# 7: startTime
# 8: softCap
# 9: hardCapLow
# 10: endTime
# 11: hardCapHigh
# 12-13: participants count
# 14: softCapReached
# 15: crowdsaleFinished

slot_names = {
    0: "owner",
    1: "symbol",
    2: "token",
    3: "beneficiary",
    4: "collected",
    5: "totalSold",
    6: "tokensPerEthPrice",
    7: "startTime",
    8: "softCap",
    9: "hardCapLow",
    10: "endTime (not used)",
    11: "hardCapHigh",
}

for i in range(20):
    val = get_storage(TARGET, hex(i))
    if val and val != "0x" + "0"*64:
        name = slot_names.get(i, f"slot_{i}")
        int_val = int(val, 16) if val.startswith("0x") else 0

        if i == 0 or i == 2 or i == 3:  # addresses
            print(f"  Slot {i} ({name}): 0x{val[26:]}")
        elif i == 1:  # symbol string
            print(f"  Slot {i} ({name}): {bytes.fromhex(val[2:]).decode('utf-8', errors='ignore').strip()}")
        elif int_val > 10**15 and int_val < 10**22:
            print(f"  Slot {i} ({name}): {int_val/1e18:.4f} ETH")
        elif int_val > 1500000000 and int_val < 2000000000:
            from datetime import datetime
            try:
                dt = datetime.fromtimestamp(int_val)
                print(f"  Slot {i} ({name}): {int_val} ({dt})")
            except:
                print(f"  Slot {i} ({name}): {int_val}")
        else:
            print(f"  Slot {i} ({name}): {int_val} (0x{val[2:]})")

# Check if we can find softCapReached and crowdsaleFinished
print("\n[CRITICAL BOOLEAN FLAGS]")

# Look at slots around where booleans might be
# In Solidity 0.4.x, booleans can be packed
for i in range(14, 25):
    val = get_storage(TARGET, hex(i))
    if val:
        int_val = int(val, 16)
        if int_val in [0, 1]:  # Boolean
            print(f"  Slot {i}: {bool(int_val)}")
        elif int_val > 0:
            print(f"  Slot {i}: {int_val} / 0x{val[2:]}")

# Check beneficiary balance and if it's accessible
print("\n[BENEFICIARY ANALYSIS]")
beneficiary = "0xb40060deae8fd58acc4ad97ef28e924a9dfd0be3"
print(f"Beneficiary address: {beneficiary}")
print(f"Beneficiary ETH balance: {get_balance(beneficiary):.4f} ETH")

# Check if beneficiary is a contract
code_result = rpc_call("eth_getCode", [beneficiary, "latest"])
if code_result and code_result.get('result'):
    code = code_result['result']
    print(f"Beneficiary code length: {len(code)} chars")
    if len(code) > 2:
        print("  -> Beneficiary is a CONTRACT")
        # Check if it's a Parity wallet
        if len(code) < 200:
            print("  -> SHORT CODE - Likely Parity wallet!")
    else:
        print("  -> Beneficiary is an EOA")

# Check owner analysis
print("\n[OWNER ANALYSIS]")
owner = "0xddbc86c2e739ce2f8e3865ede799a239336a2db1"
print(f"Owner address: {owner}")
print(f"Owner ETH balance: {get_balance(owner):.4f} ETH")

owner_code = rpc_call("eth_getCode", [owner, "latest"])
if owner_code and owner_code.get('result'):
    code = owner_code['result']
    if len(code) > 2:
        print("  -> Owner is a CONTRACT")
    else:
        print("  -> Owner is an EOA (accessible by whoever has private key)")

# Summary
print("\n" + "=" * 80)
print("EXPLOIT ASSESSMENT")
print("=" * 80)
print("""
The AhooleeTokenSale contract has 191.5 ETH locked.

KEY FINDINGS:
1. endTime has passed (Sept 2017)
2. Owner is an EOA - can call withdraw() if they have private key
3. withdraw() requires softCapReached to be true
4. withdraw() sends funds to beneficiary contract

POTENTIAL EXPLOIT PATHS:
1. If we are/can become the owner -> call withdraw()
2. If beneficiary is exploitable -> funds would go there
3. If crowdsaleFinished is true -> users can claim tokens

BLOCKERS:
- withdraw() requires softCapReached (need to check if true)
- Only owner can call withdraw()
- Beneficiary is a contract (may be inaccessible)
""")
