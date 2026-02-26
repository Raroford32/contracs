#!/usr/bin/env python3
"""
Find the correct requestSlowFill selector by trying different struct type encodings.
The issue is that the canonical ABI encoding of the struct type may differ.
"""
from web3 import Web3
import requests

RPC_URL = "http://15.235.183.30:8545"

# Try various possible function signatures
# The V3RelayData struct might be encoded differently in the ABI
signatures = [
    # Standard tuple form
    "requestSlowFill((address,address,address,address,address,uint256,uint256,uint256,uint32,uint32,uint32,bytes))",
    # With V3RelayData name (shouldn't affect selector, but let's be thorough)
    "requestSlowFill(V3RelayData)",
    # Maybe depositId is uint256 not uint32?
    "requestSlowFill((address,address,address,address,address,uint256,uint256,uint256,uint256,uint256,uint256,bytes))",
    # Maybe some fields are int256
    "requestSlowFill((address,address,address,address,address,uint256,uint256,int64,uint32,uint32,uint32,bytes))",
    # Maybe depositId/fillDeadline/exclusivityDeadline are all uint256
    "requestSlowFill((address,address,address,address,address,uint256,uint256,uint256,uint32,uint32,uint32,bytes))",
]

# Get the implementation bytecode
w3 = Web3(Web3.HTTPProvider(RPC_URL, request_kwargs={"timeout": 30}))
impl_addr = "0x5e5b726c81f43b953a62ad87e2835c85c4d9dd3b"
code = w3.eth.get_code(Web3.to_checksum_address(impl_addr)).hex()

print(f"Implementation bytecode length: {len(code)} chars")
print()

# First, let's extract all 4-byte selectors from the bytecode
# PUSH4 opcode = 0x63, followed by 4 bytes
# In EVM dispatch, selectors appear after PUSH4 and are compared with CALLDATALOAD(0)
selectors_found = set()
i = 0
while i < len(code) - 8:
    # Look for PUSH4 (0x63)
    if code[i:i+2] == "63":
        sel = code[i+2:i+10]
        selectors_found.add(sel)
    i += 2

print(f"Found {len(selectors_found)} potential selectors in bytecode")
print()

# Check each candidate signature
for sig in signatures:
    sel = Web3.keccak(text=sig)[:4].hex()
    found = sel in selectors_found
    print(f"  {sig}")
    print(f"    selector: 0x{sel}  found: {found}")

print()

# Also check against the Etherscan ABI
print("Fetching ABI from Etherscan for the proxy...")
etherscan_url = f"https://api.etherscan.io/v2/api?chainid=1&module=contract&action=getabi&address={impl_addr}&apikey=5UWN6DNT7UZCEJYNE3J6FCVAWH4QJW255K"
resp = requests.get(etherscan_url, timeout=30)
data = resp.json()

if data.get("status") == "1":
    abi = json.loads(data["result"])
    import json
    for item in abi:
        if item.get("name") == "requestSlowFill":
            print(f"\nFound requestSlowFill in ABI:")
            print(json.dumps(item, indent=2))

            # Reconstruct the canonical signature from the ABI
            inputs = item.get("inputs", [])
            if inputs:
                components = inputs[0].get("components", [])
                types = []
                for c in components:
                    types.append(c["type"])
                canonical = f"requestSlowFill(({','.join(types)}))"
                sel = Web3.keccak(text=canonical)[:4].hex()
                found = sel in selectors_found
                print(f"\nCanonical from ABI: {canonical}")
                print(f"  selector: 0x{sel}  found_in_bytecode: {found}")
else:
    print(f"  Etherscan error: {data}")

# Also try the proxy ABI
print("\nFetching ABI from Etherscan for the proxy address...")
proxy_url = f"https://api.etherscan.io/v2/api?chainid=1&module=contract&action=getabi&address=0x5c7BCd6E7De5423a257D81B442095A1a6ced35C5&apikey=5UWN6DNT7UZCEJYNE3J6FCVAWH4QJW255K"
resp2 = requests.get(proxy_url, timeout=30)
data2 = resp2.json()

if data2.get("status") == "1":
    abi2 = json.loads(data2["result"])
    for item in abi2:
        if item.get("name") == "requestSlowFill":
            print(f"\nFound requestSlowFill in proxy ABI:")
            print(json.dumps(item, indent=2))

            inputs = item.get("inputs", [])
            if inputs:
                components = inputs[0].get("components", [])
                types = []
                for c in components:
                    types.append(c["type"])
                canonical = f"requestSlowFill(({','.join(types)}))"
                sel = Web3.keccak(text=canonical)[:4].hex()
                found = sel in selectors_found
                print(f"\nCanonical from proxy ABI: {canonical}")
                print(f"  selector: 0x{sel}  found_in_bytecode: {found}")

# Let's also search for "requestSlowFill" in the known 4byte directory
# by trying some more variations with V3RelayData struct ordering
print("\n\n--- Brute force: search bytecode for ALL 4-byte selectors ---")
print("Looking for requestSlowFill selector among bytecode selectors...")

# Check if 14ee8885 or close matches exist
target = "14ee8885"
print(f"\nTarget selector 0x{target} in bytecode: {target in code}")

# Let's also look at what the actual proxy ABI says
# Maybe the contract has been upgraded and uses a different struct
# Let's check the V3SpokePoolInterface source
print("\n--- Checking source for the actual struct definition ---")
