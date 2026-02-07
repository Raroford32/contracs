#!/usr/bin/env python3
"""
VERIFY ACTUAL GETTER FUNCTIONS
Test if the critique is correct about storage layout
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
        return {"error": result.stdout}

WALLET = "0xbd6ed4969d9e52032ee3573e643f6a1bdc0a7e1e"
ATTACKER = "0xDeaDbeefdEAdbeefdEadbEEFdeadbeEFdEaDbeeF"
OWNER_FROM_STORAGE = "0xc8668bf0a13efa2d508642006fb4965878ca1fd9"

print("=" * 70)
print("CRITICAL VERIFICATION: Testing actual getter functions")
print("=" * 70)
print(f"Wallet: {WALLET}")
print()

# Function selectors from Parity wallet ABI
# m_numOwners() - 0x4123cb6b
# m_required() - 0x746c9171 (or similar)
# isOwner(address) - 0x2f54bf6e

# Let's compute the correct selectors
import hashlib

def get_selector(sig):
    # keccak256 of function signature
    from Crypto.Hash import keccak
    k = keccak.new(digest_bits=256)
    k.update(sig.encode())
    return "0x" + k.hexdigest()[:8]

try:
    from Crypto.Hash import keccak
    selector_numOwners = get_selector("m_numOwners()")
    selector_required = get_selector("m_required()")
    selector_isOwner = get_selector("isOwner(address)")
    print(f"m_numOwners() selector: {selector_numOwners}")
    print(f"m_required() selector: {selector_required}")
    print(f"isOwner(address) selector: {selector_isOwner}")
except:
    # Fallback to known selectors
    selector_numOwners = "0x4123cb6b"
    selector_required = "0x746c9171"
    selector_isOwner = "0x2f54bf6e"
    print("Using hardcoded selectors")
    print(f"m_numOwners() selector: {selector_numOwners}")
    print(f"m_required() selector: {selector_required}")
    print(f"isOwner(address) selector: {selector_isOwner}")

print()
print("-" * 70)
print("CALLING GETTER FUNCTIONS")
print("-" * 70)

# Call m_numOwners()
result = rpc_call("eth_call", [{"to": WALLET, "data": selector_numOwners}, "latest"])
print(f"\nm_numOwners() call:")
print(f"  Result: {result}")
if "result" in result:
    val = result["result"]
    if val and val != "0x":
        try:
            num = int(val, 16)
            print(f"  Decoded: {num}")
        except:
            print(f"  Raw: {val}")

# Call m_required()
result = rpc_call("eth_call", [{"to": WALLET, "data": selector_required}, "latest"])
print(f"\nm_required() call:")
print(f"  Result: {result}")
if "result" in result:
    val = result["result"]
    if val and val != "0x":
        try:
            num = int(val, 16)
            print(f"  Decoded: {num}")
        except:
            print(f"  Raw: {val}")

# Call isOwner(owner_address)
is_owner_data = selector_isOwner + "000000000000000000000000" + OWNER_FROM_STORAGE[2:].lower()
result = rpc_call("eth_call", [{"to": WALLET, "data": is_owner_data}, "latest"])
print(f"\nisOwner({OWNER_FROM_STORAGE[:10]}...) call:")
print(f"  Result: {result}")
if "result" in result:
    val = result["result"]
    if val and val != "0x":
        try:
            num = int(val, 16)
            print(f"  Decoded: {num} ({'TRUE - IS OWNER' if num == 1 else 'FALSE - NOT OWNER'})")
        except:
            print(f"  Raw: {val}")

# Call isOwner(attacker)
is_owner_data = selector_isOwner + "000000000000000000000000" + ATTACKER[2:].lower()
result = rpc_call("eth_call", [{"to": WALLET, "data": is_owner_data}, "latest"])
print(f"\nisOwner({ATTACKER[:10]}...) call:")
print(f"  Result: {result}")
if "result" in result:
    val = result["result"]
    if val and val != "0x":
        try:
            num = int(val, 16)
            print(f"  Decoded: {num} ({'TRUE - IS OWNER' if num == 1 else 'FALSE - NOT OWNER'})")
        except:
            print(f"  Raw: {val}")

# Test with a random nonsense function to check echo behavior
print()
print("-" * 70)
print("TESTING ECHO BEHAVIOR (calling random function)")
print("-" * 70)

random_data = "0xdeadbeef12345678"
result = rpc_call("eth_call", [{"to": WALLET, "data": random_data}, "latest"])
print(f"\nCalling 0xdeadbeef12345678:")
print(f"  Result: {result}")

random_gas = rpc_call("eth_estimateGas", [{"to": WALLET, "data": random_data}, "latest"])
print(f"  Gas estimate: {random_gas}")

# Compare with initWallet gas
init_data = "0xe46dcfeb" + "0" * 248  # Minimal initWallet call
init_gas = rpc_call("eth_estimateGas", [{"to": WALLET, "data": init_data}, "latest"])
print(f"\ninitWallet gas estimate: {init_gas}")

print()
print("-" * 70)
print("STORAGE SLOT VERIFICATION")
print("-" * 70)

# Check all storage slots 0-10
for slot in range(10):
    storage = rpc_call("eth_getStorageAt", [WALLET, hex(slot), "latest"])
    if storage and "result" in storage:
        val = storage["result"]
        val_int = int(val, 16) if val else 0
        if val_int != 0:
            print(f"Slot {slot}: {val_int} (hex: {val})")

