#!/usr/bin/env python3
"""
Investigate DynamicLiquidTokenConverter potential vulnerability
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

ADDR = "0x0337184a497565a9bd8e300dad50270cd367f206"
ATTACKER = "0xDeaDbeefdEAdbeefdEadbEEFdeadbeEFdEaDbeeF"

print("=" * 80)
print("DynamicLiquidTokenConverter Investigation")
print("=" * 80)

# Get balance
bal = rpc_call("eth_getBalance", [ADDR, "latest"])
print(f"Balance: {int(bal['result'], 16) / 1e18:.2f} ETH")

# Get source
source = get_source(ADDR)
if source:
    src = source.get("SourceCode", "")
    
    # Find the function with the transfer pattern
    lines = src.split('\n')
    print("\nSearching for transfer functions...")
    
    in_func = False
    func_start = 0
    for i, line in enumerate(lines):
        if 'function' in line and not in_func:
            if 'public' in line or 'external' in line:
                func_start = i
                in_func = True
        
        if in_func and '_to.transfer(address(this).balance)' in line:
            # Found it - print the whole function
            print(f"\n--- Function starting at line {func_start} ---")
            depth = 0
            for j in range(func_start, min(len(lines), i+20)):
                print(f"{j}: {lines[j]}")
                depth += lines[j].count('{') - lines[j].count('}')
                if depth == 0 and j > func_start and '{' in src:
                    break
            in_func = False
        
        if in_func and '}' in line and line.strip() == '}':
            in_func = False

# Check owner
print("\n\nChecking owner:")
owner_resp = eth_call(ADDR, "0x8da5cb5b")
if owner_resp and "result" in owner_resp:
    result = owner_resp["result"]
    if result and len(result) >= 42:
        owner = "0x" + result[-40:]
        print(f"Owner: {owner}")
        
        # Check if owner has code
        owner_code = rpc_call("eth_getCode", [owner, "latest"])
        if owner_code and "result" in owner_code:
            code_len = (len(owner_code["result"]) - 2) // 2
            print(f"Owner code length: {code_len} (0 = EOA)")

# Try to find the function that transfers balance
# Based on the source, look for function names

