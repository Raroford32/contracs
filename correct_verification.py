#!/usr/bin/env python3
"""
CORRECTED VERIFICATION - Using actual getter functions
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

WALLETS = [
    "0xbd6ed4969d9e52032ee3573e643f6a1bdc0a7e1e",
    "0x3885b0c18e3c4ab0ca2b8dc99771944404687628",
    "0x4615cc10092b514258577dafca98c142577f1578",
    "0xddf90e79af4e0ece889c330fca6e1f8d6c6cf0d8",
    "0x379add715d9fb53a79e6879653b60f12cc75bcaf",
    "0xb39036a09865236d67875f6fd391e597b4c8425d",
    "0x58174e9b3178074f83888b6147c1a7d2ced85c6f",
    "0xfcbcd2da9efa379c7d3352ffd3d5877cc088cbba",
    "0x98669654f4ab5ccede76766ad19bdfe230f96c65",
]

# Correct selectors
SEL_NUM_OWNERS = "0x4123cb6b"  # m_numOwners()
SEL_REQUIRED = "0x746c9171"    # m_required()

print("=" * 80)
print("CORRECTED VERIFICATION - Using Actual Getter Functions")
print("=" * 80)
print()
print("Previous analysis was WRONG - I misread storage layout")
print("Now calling m_numOwners() and m_required() directly")
print()

results = []

for wallet in WALLETS:
    time.sleep(0.3)
    
    # Get balance
    bal = rpc_call("eth_getBalance", [wallet, "latest"])
    balance_wei = int(bal["result"], 16) if bal and "result" in bal else 0
    balance_eth = balance_wei / 1e18
    
    # Call m_numOwners() - the CORRECT way
    num_owners_resp = rpc_call("eth_call", [{"to": wallet, "data": SEL_NUM_OWNERS}, "latest"])
    m_numOwners = 0
    if num_owners_resp and "result" in num_owners_resp:
        try:
            m_numOwners = int(num_owners_resp["result"], 16)
        except:
            pass
    
    # Call m_required()
    required_resp = rpc_call("eth_call", [{"to": wallet, "data": SEL_REQUIRED}, "latest"])
    m_required = 0
    if required_resp and "result" in required_resp:
        try:
            m_required = int(required_resp["result"], 16)
        except:
            pass
    
    status = "INITIALIZED - NOT EXPLOITABLE" if m_numOwners > 0 else "CHECK NEEDED"
    
    results.append({
        "wallet": wallet,
        "balance_eth": balance_eth,
        "m_numOwners": m_numOwners,
        "m_required": m_required,
        "status": status
    })
    
    print(f"{wallet}")
    print(f"  Balance: {balance_eth:.2f} ETH | m_numOwners: {m_numOwners} | m_required: {m_required}")
    print(f"  Status: {status}")
    print()

print("=" * 80)
print("SUMMARY")
print("=" * 80)

exploitable = [r for r in results if r["m_numOwners"] == 0]
initialized = [r for r in results if r["m_numOwners"] > 0]

print(f"\nInitialized (NOT exploitable): {len(initialized)}")
print(f"Potentially exploitable: {len(exploitable)}")

total_locked = sum(r["balance_eth"] for r in initialized)
print(f"\nTotal ETH in initialized wallets: {total_locked:.2f} ETH")
print(f"These funds are LOCKED (require owner signatures), NOT exploitable")

if exploitable:
    print(f"\nPotentially exploitable wallets:")
    for r in exploitable:
        print(f"  {r['wallet']}: {r['balance_eth']:.2f} ETH")
else:
    print(f"\n*** NO EXPLOITABLE WALLETS FOUND ***")
    print("All wallets have m_numOwners > 0 (properly initialized)")

