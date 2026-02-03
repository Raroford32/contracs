#!/usr/bin/env python3
"""
Get and analyze DynamicLiquidTokenConverter source
"""
import json
import subprocess

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

ADDR = "0x0337184a497565a9bd8e300dad50270cd367f206"

source = get_source(ADDR)
if source:
    src = source.get("SourceCode", "")
    
    # Find the line with _to.transfer
    lines = src.split('\n')
    for i, line in enumerate(lines):
        if '_to.transfer(address(this).balance)' in line:
            # Print 30 lines before and 10 after
            start = max(0, i - 30)
            end = min(len(lines), i + 10)
            print(f"Context around line {i}:")
            print("-" * 60)
            for j in range(start, end):
                marker = ">>> " if j == i else "    "
                print(f"{marker}{j}: {lines[j][:100]}")
            print("-" * 60)
            break

