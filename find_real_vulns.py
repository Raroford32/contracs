#!/usr/bin/env python3
"""
Look for REAL vulnerabilities in verified source code
Focus on:
1. Unprotected selfdestruct
2. Unprotected admin functions
3. Reentrancy patterns
4. Access control issues
"""
import json
import subprocess
import time
import re

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

# Load high-value from scan
with open("scan_results.json", "r") as f:
    data = json.load(f)

high_value = data["high_value"]

print("=" * 80)
print("SOURCE CODE VULNERABILITY ANALYSIS")
print("=" * 80)

findings = []

checked = 0
for addr, balance, ctype in high_value:
    if balance < 50:
        continue
    if "PARITY" in ctype:
        continue  # Skip known Parity proxies
    
    checked += 1
    if checked > 30:  # Limit to 30 contracts for now
        break
    
    time.sleep(0.4)
    source = get_source(addr)
    
    if not source:
        continue
    
    src = source.get("SourceCode", "")
    name = source.get("ContractName", "")
    
    if not src or len(src) < 100:
        continue
    
    # Look for vulnerability patterns
    vulns = []
    
    # 1. selfdestruct without proper access control
    if "selfdestruct" in src.lower():
        # Check if it's in a function without onlyOwner
        selfd_matches = list(re.finditer(r'selfdestruct\s*\(', src, re.IGNORECASE))
        for match in selfd_matches:
            # Get surrounding context
            start = max(0, match.start() - 500)
            end = min(len(src), match.end() + 100)
            context = src[start:end]
            
            if 'onlyOwner' not in context and 'require(msg.sender' not in context and 'require(owner' not in context:
                vulns.append("UNPROTECTED_SELFDESTRUCT")
    
    # 2. Dangerous delegatecall patterns
    if "delegatecall" in src.lower():
        # delegatecall to user-controlled address
        dc_matches = list(re.finditer(r'\.delegatecall\s*\(', src, re.IGNORECASE))
        for match in dc_matches:
            start = max(0, match.start() - 200)
            context = src[start:match.end()]
            # Check if target is from user input
            if 'msg.sender' in context or '_target' in context or '_addr' in context:
                vulns.append("DELEGATECALL_TO_USER_ADDR")
    
    # 3. tx.origin for authentication
    if "tx.origin" in src:
        if "require(tx.origin" in src or "tx.origin ==" in src:
            vulns.append("TX_ORIGIN_AUTH")
    
    # 4. Unchecked external call return value
    if ".call" in src and "require(" not in src[src.find(".call"):src.find(".call")+100]:
        # More detailed check needed
        pass
    
    # 5. Integer overflow in older contracts (pre-0.8.0)
    compiler = source.get("CompilerVersion", "")
    if "0.4" in compiler or "0.5" in compiler or "0.6" in compiler or "0.7" in compiler:
        if "SafeMath" not in src and ("+" in src or "-" in src or "*" in src):
            # Could have overflow, but need more analysis
            pass
    
    if vulns:
        findings.append((addr, balance, name, vulns))
        print(f"\n[POTENTIAL] {addr}")
        print(f"  Balance: {balance:.2f} ETH")
        print(f"  Contract: {name}")
        print(f"  Issues: {vulns}")

print("\n" + "=" * 80)
print("SUMMARY")
print("=" * 80)
print(f"Checked: {checked} contracts")
print(f"Potential issues: {len(findings)}")

for addr, bal, name, vulns in findings:
    print(f"\n{addr} ({bal:.2f} ETH) - {name}")
    for v in vulns:
        print(f"  - {v}")

