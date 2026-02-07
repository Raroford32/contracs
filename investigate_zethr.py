#!/usr/bin/env python3
"""
Investigate Zethr contract tx.origin vulnerability
"""
import json
import subprocess
import time

RPC = "https://mainnet.infura.io/v3/bfc7283659224dd6b5124ebbc2b14e2c"
ETHERSCAN_API = "5UWN6DNT7UZCEJYNE3J6FCVAWH4QJW255K"

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

ZETHR = "0xd48b633045af65ff636f3c6edd744748351e020d"

print("=" * 80)
print("ZETHR CONTRACT ANALYSIS")
print("=" * 80)

source = get_source(ZETHR)
if source:
    src = source.get("SourceCode", "")
    
    # Find tx.origin usage
    lines = src.split('\n')
    print("Lines containing tx.origin:")
    for i, line in enumerate(lines):
        if 'tx.origin' in line.lower():
            # Show context
            start = max(0, i-2)
            end = min(len(lines), i+3)
            print(f"\n--- Line {i} ---")
            for j in range(start, end):
                marker = ">>>" if j == i else "   "
                print(f"{marker} {j}: {lines[j][:100]}")

    # Find withdraw functions
    print("\n\nWithdraw functions:")
    in_func = False
    depth = 0
    for i, line in enumerate(lines):
        if 'function' in line.lower() and 'withdraw' in line.lower():
            in_func = True
            depth = 0
            print(f"\n--- Line {i} ---")
        
        if in_func:
            print(f"{i}: {line[:100]}")
            depth += line.count('{') - line.count('}')
            if depth <= 0 and '}' in line and '{' not in line:
                in_func = False

