#!/usr/bin/env python3
"""
Scan for reentrancy vulnerabilities
Focus on contracts with:
1. External calls (call, transfer, send)
2. State updates after calls
3. No reentrancy guard
"""
import json
import subprocess
import re
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

def get_balance(addr):
    result = rpc_call("eth_getBalance", [addr, "latest"])
    if result and 'result' in result:
        return int(result['result'], 16) / 1e18
    return 0

def get_code(addr):
    result = rpc_call("eth_getCode", [addr, "latest"])
    if result and 'result' in result:
        return result['result']
    return "0x"

def get_source(addr):
    url = f"https://api.etherscan.io/v2/api?chainid=1&module=contract&action=getsourcecode&address={addr}&apikey={ETHERSCAN_API}"
    result = subprocess.run(["curl", "-s", url], capture_output=True, text=True)
    try:
        data = json.loads(result.stdout)
        if data.get("status") == "1" and data.get("result"):
            return data["result"][0]
    except:
        pass
    return None

def analyze_reentrancy(source_code):
    """
    Analyze source code for reentrancy vulnerabilities.
    Returns list of findings.
    """
    findings = []
    lines = source_code.split('\n')

    # Patterns for external calls
    external_call_patterns = [
        r'\.call\{',
        r'\.call\(',
        r'\.transfer\(',
        r'\.send\(',
        r'\.delegatecall\(',
    ]

    # Patterns for state updates
    state_update_patterns = [
        r'\+=',
        r'\-=',
        r'=\s*[^=]',  # Assignment but not comparison
    ]

    # Reentrancy guard patterns
    guard_patterns = [
        r'nonreentrant',
        r'reentrancyguard',
        r'_locked',
        r'mutex',
        r'_notEntered',
    ]

    # Check for guards
    has_guard = any(re.search(p, source_code, re.IGNORECASE) for p in guard_patterns)

    # Find functions with external calls
    in_function = False
    function_name = ""
    function_start = 0
    brace_count = 0
    external_call_line = -1

    for i, line in enumerate(lines):
        # Track function boundaries
        func_match = re.search(r'function\s+(\w+)', line)
        if func_match and '{' in line:
            in_function = True
            function_name = func_match.group(1)
            function_start = i
            brace_count = line.count('{') - line.count('}')
            external_call_line = -1
        elif in_function:
            brace_count += line.count('{') - line.count('}')
            if brace_count <= 0:
                in_function = False

        # Look for external calls
        if in_function:
            for pattern in external_call_patterns:
                if re.search(pattern, line):
                    external_call_line = i
                    break

            # If we had an external call and now have state update
            if external_call_line >= 0 and external_call_line < i:
                for pattern in state_update_patterns:
                    if re.search(pattern, line) and '==' not in line:
                        # Potential CEI violation
                        findings.append({
                            "function": function_name,
                            "external_call_line": external_call_line + 1,
                            "state_update_line": i + 1,
                            "external_call": lines[external_call_line].strip()[:60],
                            "state_update": line.strip()[:60],
                            "has_guard": has_guard
                        })
                        break

    return findings

print("=" * 80)
print("REENTRANCY VULNERABILITY SCANNER")
print("=" * 80)

# Load contracts
with open("contracts.txt", "r") as f:
    contracts = [line.strip() for line in f if line.strip().startswith("0x")]

vulnerable_contracts = []

print(f"\nScanning {len(contracts)} contracts...")

for i, addr in enumerate(contracts):
    if i % 50 == 0:
        print(f"Progress: {i}/{len(contracts)}")

    balance = get_balance(addr)
    if balance < 20:  # Focus on 20+ ETH
        continue

    # Skip Parity wallets
    code = get_code(addr)
    if len(code) < 200:
        continue

    # Get source
    source_data = get_source(addr)
    if not source_data:
        continue

    src = source_data.get("SourceCode", "")
    contract_name = source_data.get("ContractName", "Unknown")

    if not src:
        continue

    # Parse multi-file format
    if src.startswith("{{"):
        try:
            src_json = json.loads(src[1:-1])
            sources = src_json.get("sources", {})
            src = "\n".join([v.get("content", "") for v in sources.values()])
        except:
            pass
    elif src.startswith("{"):
        try:
            src_json = json.loads(src)
            sources = src_json.get("sources", {})
            src = "\n".join([v.get("content", "") for v in sources.values()])
        except:
            pass

    findings = analyze_reentrancy(src)

    # Filter to unguarded findings
    unguarded = [f for f in findings if not f['has_guard']]

    if unguarded:
        vulnerable_contracts.append({
            "address": addr,
            "name": contract_name,
            "balance": balance,
            "findings": unguarded
        })
        print(f"\n[POTENTIAL] {addr[:20]}... ({contract_name})")
        print(f"  Balance: {balance:.2f} ETH")
        print(f"  Unguarded CEI violations: {len(unguarded)}")
        for f in unguarded[:3]:
            print(f"    - {f['function']}: call at L{f['external_call_line']}, state at L{f['state_update_line']}")

    time.sleep(0.3)

print("\n" + "=" * 80)
print(f"FOUND {len(vulnerable_contracts)} CONTRACTS WITH POTENTIAL REENTRANCY")
print("=" * 80)

# Deep analysis
for contract in sorted(vulnerable_contracts, key=lambda x: -x['balance'])[:5]:
    addr = contract['address']
    print(f"\n{'='*70}")
    print(f"[DETAILED] {addr}")
    print(f"Contract: {contract['name']} | Balance: {contract['balance']:.4f} ETH")
    print("=" * 70)

    for finding in contract['findings'][:5]:
        print(f"\nFunction: {finding['function']}")
        print(f"  External call (L{finding['external_call_line']}): {finding['external_call']}")
        print(f"  State update (L{finding['state_update_line']}): {finding['state_update']}")

# Save
with open("reentrancy_findings.json", "w") as f:
    json.dump(vulnerable_contracts, f, indent=2)

print(f"\n[*] Findings saved to reentrancy_findings.json")
