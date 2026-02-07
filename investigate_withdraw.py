#!/usr/bin/env python3
"""
CAREFUL investigation of contracts with callable withdraw()
Remember Parity lesson - gas estimate doesn't mean execution works!
"""
import json
import subprocess
import time

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

ATTACKER = "0xDeaDbeefdEAdbeefdEadbEEFdeadbeEFdEaDbeeF"

# Suspicious contracts
targets = [
    ("0x2ccfa2acf6ff744575ccf306b44a59b11c32e44b", 415.70),
    ("0xdbfb513d25df56b4c3f5258d477a395d4b735824", 293.04),
    ("0xb958a8f59ac6145851729f73c7a6968311d8b633", 293.00),
]

print("=" * 80)
print("CAREFUL INVESTIGATION - WITHDRAW CALLABLE CONTRACTS")
print("=" * 80)

for addr, balance in targets:
    print(f"\n{'='*80}")
    print(f"Contract: {addr}")
    print(f"Balance: {balance:.2f} ETH")
    print("=" * 80)
    
    # Get bytecode
    code_resp = rpc_call("eth_getCode", [addr, "latest"])
    code = code_resp.get("result", "0x") if code_resp else "0x"
    print(f"Bytecode length: {(len(code)-2)//2} bytes")
    
    if len(code) < 10:
        print("  -> No code - EOA or selfdestructed")
        continue
    
    # Show first part of bytecode
    print(f"Bytecode start: {code[:100]}...")
    
    # CRITICAL: Test a RANDOM function to check for echo behavior
    random_selector = "0xdeadbeef"
    random_resp = eth_call(addr, random_selector)
    print(f"\nEcho test (0xdeadbeef):")
    if random_resp and "result" in random_resp:
        result = random_resp["result"]
        if result and result != "0x":
            print(f"  Returns: {result[:66]}...")
            if "deadbeef" in result.lower():
                print("  -> WARNING: Echoes calldata (like Parity proxy)")
        else:
            print(f"  Returns: empty/0x")
    elif random_resp and "error" in random_resp:
        print(f"  REVERTS (good - not echoing)")
    
    # Test withdraw() via eth_call (not just gas estimate)
    print(f"\nwithdraw() eth_call test:")
    withdraw_resp = eth_call(addr, "0x3ccfd60b", ATTACKER)
    if withdraw_resp and "result" in withdraw_resp:
        result = withdraw_resp["result"]
        print(f"  Returns: {result}")
        if result and result != "0x":
            if "3ccfd60b" in result.lower():
                print("  -> Echoes selector - NOT real execution")
            else:
                print("  -> Returns data - investigating further")
    elif withdraw_resp and "error" in withdraw_resp:
        err = withdraw_resp.get("error", {})
        print(f"  REVERTS: {err.get('message', str(err))[:60]}")
    
    # Check storage
    print(f"\nStorage analysis:")
    for slot in range(10):
        storage = rpc_call("eth_getStorageAt", [addr, hex(slot), "latest"])
        if storage and "result" in storage:
            val = int(storage["result"], 16)
            if val != 0:
                if val < 2**160 and val > 1000:
                    print(f"  Slot {slot}: 0x{storage['result'][-40:]} (address)")
                elif val < 1000:
                    print(f"  Slot {slot}: {val}")
                else:
                    print(f"  Slot {slot}: {val / 1e18:.4f} (if ETH scale)")
    
    # Try other common functions
    print(f"\nOther function tests:")
    funcs = [
        ("0x8da5cb5b", "owner()"),
        ("0x893d20e8", "getOwner()"),
        ("0x12065fe0", "getBalance()"),
        ("0xf2fde38b12345678901234567890123456789012345678901234567890123456", "transferOwnership(addr)"),
    ]
    
    for sel, name in funcs:
        resp = eth_call(addr, sel[:10])
        if resp and "result" in resp:
            result = resp["result"]
            if result and result != "0x" and not (sel[:10].lower() in result.lower()):
                val = int(result, 16) if result else 0
                if val < 2**160 and val != 0:
                    print(f"  {name}: 0x{result[-40:]}")
                elif val != 0:
                    print(f"  {name}: {val}")
    
    time.sleep(0.5)

