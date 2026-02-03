#!/usr/bin/env python3
"""
Analyze contract bytecode to find function selectors
"""
import json
import subprocess
import re

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

# Known function selectors
KNOWN_SELECTORS = {
    "0dcd7a6c": "multisend(address,address[],uint256[])",
    "2079fb9a": "owners(uint256)",
    "3ccfd60b": "withdraw()",
    "8da5cb5b": "owner()",
    "f2fde38b": "transferOwnership(address)",
    "a9059cbb": "transfer(address,uint256)",
    "23b872dd": "transferFrom(address,address,uint256)",
    "095ea7b3": "approve(address,uint256)",
    "70a08231": "balanceOf(address)",
    "18160ddd": "totalSupply()",
    "dd62ed3e": "allowance(address,address)",
    "79cc6790": "burnFrom(address,uint256)",
    "42966c68": "burn(uint256)",
    "40c10f19": "mint(address,uint256)",
    "8b9d7cd3": "claim()",
    "92379af7": "distribute()",
    "8456cb59": "pause()",
    "3f4ba83a": "unpause()",
}

ATTACKER = "0xDeaDbeefdEAdbeefdEadbEEFdeadbeEFdEaDbeeF"

targets = [
    ("0x2ccfa2acf6ff744575ccf306b44a59b11c32e44b", 415.70),
    ("0xdbfb513d25df56b4c3f5258d477a395d4b735824", 293.04),
    ("0xb958a8f59ac6145851729f73c7a6968311d8b633", 293.00),
]

print("=" * 80)
print("BYTECODE ANALYSIS - EXTRACT FUNCTION SELECTORS")
print("=" * 80)

for addr, balance in targets:
    print(f"\n{'='*80}")
    print(f"Contract: {addr} ({balance:.2f} ETH)")
    print("=" * 80)
    
    # Get bytecode
    code_resp = rpc_call("eth_getCode", [addr, "latest"])
    code = code_resp.get("result", "0x") if code_resp else "0x"
    
    # Find all 4-byte selectors in bytecode (look for PUSH4 patterns)
    # In EVM bytecode, function selectors are often loaded with PUSH4 (0x63)
    # followed by the 4-byte selector
    
    selectors_found = set()
    
    # Method 1: Look for PUSH4 pattern (0x63 + 4 bytes)
    code_bytes = code[2:] if code.startswith("0x") else code
    for i in range(0, len(code_bytes) - 10, 2):
        if code_bytes[i:i+2] == "63":  # PUSH4
            selector = code_bytes[i+2:i+10]
            if len(selector) == 8:
                selectors_found.add(selector)
    
    # Method 2: Look for explicit patterns like 0x + selector in comparisons
    pattern = r'[0-9a-f]{8}'
    potential = re.findall(pattern, code_bytes.lower())
    for p in potential:
        if p in KNOWN_SELECTORS:
            selectors_found.add(p)
    
    print(f"Found {len(selectors_found)} potential selectors")
    
    # Test each found selector
    print("\nTesting selectors:")
    for sel in sorted(selectors_found):
        name = KNOWN_SELECTORS.get(sel, "unknown")
        
        # Try eth_call
        resp = eth_call(addr, "0x" + sel)
        
        # Try gas estimate
        gas_resp = rpc_call("eth_estimateGas", [{"from": ATTACKER, "to": addr, "data": "0x" + sel}, "latest"])
        
        if gas_resp and "result" in gas_resp:
            gas = int(gas_resp["result"], 16)
            result_str = resp.get("result", "0x") if resp else "error"
            
            # Skip if gas is just base tx cost (21000)
            if gas > 21100:
                if name != "unknown":
                    print(f"  0x{sel} - {name}: gas={gas}")
                else:
                    print(f"  0x{sel} - unknown: gas={gas}, returns={result_str[:20]}...")

# Let's specifically test the first contract more
print("\n" + "=" * 80)
print("DETAILED TEST: 0x2ccfa2acf6ff744575ccf306b44a59b11c32e44b (415 ETH)")
print("=" * 80)

addr = "0x2ccfa2acf6ff744575ccf306b44a59b11c32e44b"

# This looks like a multisend contract based on selector 0x0dcd7a6c
# Try calling owners(0), owners(1), etc.
print("\nChecking owners array:")
for i in range(5):
    # owners(uint256) = 0x2079fb9a + uint256
    data = "0x2079fb9a" + hex(i)[2:].zfill(64)
    resp = eth_call(addr, data)
    if resp and "result" in resp:
        result = resp["result"]
        if result and result != "0x" and int(result, 16) != 0:
            owner = "0x" + result[-40:]
            print(f"  owners({i}): {owner}")

# Check slot 0 value (might be owner count)
storage = rpc_call("eth_getStorageAt", [addr, "0x0", "latest"])
if storage and "result" in storage:
    print(f"\nSlot 0 (possible owner count): {int(storage['result'], 16)}")

