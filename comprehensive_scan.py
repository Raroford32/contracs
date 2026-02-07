#!/usr/bin/env python3
"""
Comprehensive contract scanner with proper verification
"""
import json
import subprocess
import time
import sys

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

def get_balance(addr):
    resp = rpc_call("eth_getBalance", [addr, "latest"])
    if resp and "result" in resp:
        return int(resp["result"], 16) / 1e18
    return 0

def get_code(addr):
    resp = rpc_call("eth_getCode", [addr, "latest"])
    if resp and "result" in resp:
        return resp["result"]
    return "0x"

def identify_contract_type(code, addr):
    """Identify contract type from bytecode patterns"""
    if code == "0x" or len(code) < 10:
        return "EOA_OR_SELFDESTRUCTED"
    
    code_lower = code.lower()
    
    # Known patterns
    if "273930d21e01ee25e4c219b63259d214872220a2" in code_lower:
        return "PARITY_PROXY_ACTIVE"
    if "863df6bfa4469f3ead0be8f9f2aae51c91a907b4" in code_lower:
        return "PARITY_PROXY_KILLED"
    if len(code) < 120:  # Very short - likely minimal proxy
        return "MINIMAL_PROXY"
    
    # ERC20 patterns (transfer selector: a9059cbb)
    if "a9059cbb" in code_lower:
        return "ERC20_TOKEN"
    
    # Common DeFi patterns
    if "swap" in code_lower or "70a08231" in code_lower:  # balanceOf
        return "DEFI_CONTRACT"
    
    # Multisig patterns  
    if "submitTransaction" in code_lower or "confirmTransaction" in code_lower:
        return "MULTISIG"
    
    return "UNKNOWN_CONTRACT"

# Load contracts
with open("contracts.txt", "r") as f:
    contracts = [line.strip() for line in f if line.strip().startswith("0x")]

print(f"Scanning {len(contracts)} contracts...")
print()

# Categorize and get balances
high_value = []  # > 10 ETH
medium_value = []  # 1-10 ETH
categories = {}

for i, addr in enumerate(contracts):
    if i % 50 == 0:
        print(f"Progress: {i}/{len(contracts)}")
    
    balance = get_balance(addr)
    code = get_code(addr)
    ctype = identify_contract_type(code, addr)
    
    if ctype not in categories:
        categories[ctype] = []
    categories[ctype].append((addr, balance))
    
    if balance > 10:
        high_value.append((addr, balance, ctype))
    elif balance > 1:
        medium_value.append((addr, balance, ctype))
    
    time.sleep(0.15)  # Rate limit

print()
print("=" * 80)
print("SCAN RESULTS")
print("=" * 80)

print("\nCONTRACT CATEGORIES:")
for ctype, addrs in sorted(categories.items(), key=lambda x: -len(x[1])):
    total_bal = sum(b for _, b in addrs)
    print(f"  {ctype}: {len(addrs)} contracts, {total_bal:.2f} ETH")

print(f"\nHIGH VALUE (>10 ETH): {len(high_value)} contracts")
high_value.sort(key=lambda x: -x[1])
for addr, bal, ctype in high_value[:30]:
    print(f"  {addr}: {bal:.2f} ETH ({ctype})")

print(f"\nMEDIUM VALUE (1-10 ETH): {len(medium_value)} contracts")
medium_value.sort(key=lambda x: -x[1])
for addr, bal, ctype in medium_value[:20]:
    print(f"  {addr}: {bal:.2f} ETH ({ctype})")

# Save results
with open("scan_results.json", "w") as f:
    json.dump({
        "high_value": [(a, b, c) for a, b, c in high_value],
        "medium_value": [(a, b, c) for a, b, c in medium_value],
        "categories": {k: [(a, b) for a, b in v] for k, v in categories.items()}
    }, f, indent=2)

print("\nResults saved to scan_results.json")
