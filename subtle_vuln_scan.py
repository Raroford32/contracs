#!/usr/bin/env python3
"""
Subtle Vulnerability Scanner - CLAUDE.md Methodology
Looking for:
1. tx.origin authentication (bypassable via phishing)
2. Integer overflow/underflow in old Solidity (pre-0.8)
3. Incorrect decimal handling
4. Cross-function reentrancy
5. Unprotected selfdestruct
6. Signature replay attacks
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

def get_balance(addr):
    result = rpc_call("eth_getBalance", [addr, "latest"])
    if result and 'result' in result:
        return int(result['result'], 16) / 1e18
    return 0

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

# Load contracts
with open("contracts.txt", "r") as f:
    contracts = [line.strip() for line in f if line.strip().startswith("0x")]

print("=" * 80)
print("SUBTLE VULNERABILITY SCAN")
print("=" * 80)

findings = []

for i, addr in enumerate(contracts):
    if i % 25 == 0:
        print(f"Scanning {i}/{len(contracts)}...")

    balance = get_balance(addr)
    if balance < 30:  # Focus on 30+ ETH
        continue

    time.sleep(0.25)
    source_data = get_source(addr)
    if not source_data:
        continue

    src = source_data.get("SourceCode", "")
    name = source_data.get("ContractName", "Unknown")
    compiler = source_data.get("CompilerVersion", "")

    if not src:
        continue

    # Parse multi-file JSON
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

    src_lower = src.lower()
    vulnerabilities = []
    score = 0

    # PATTERN 1: tx.origin authentication
    if "tx.origin" in src:
        # Check if used in require/if for auth
        lines = src.split('\n')
        for j, line in enumerate(lines):
            if "tx.origin" in line:
                if any(p in line.lower() for p in ["require", "if", "=="]):
                    score += 4
                    vulnerabilities.append({
                        "type": "TX_ORIGIN_AUTH",
                        "line": j+1,
                        "code": line.strip()[:60]
                    })
                    break

    # PATTERN 2: Pre-0.8 Solidity without SafeMath
    is_old_solidity = False
    if compiler:
        version_match = re.search(r'v?0\.([4-7])\.', compiler)
        if version_match:
            is_old_solidity = True

    if is_old_solidity:
        # Check for SafeMath usage
        has_safemath = "safemath" in src_lower
        if not has_safemath:
            # Look for arithmetic operations
            if any(p in src for p in ['+', '-', '*', '/']):
                score += 3
                vulnerabilities.append({
                    "type": "OLD_SOLIDITY_NO_SAFEMATH",
                    "compiler": compiler
                })

    # PATTERN 3: Unprotected selfdestruct
    if "selfdestruct" in src_lower or "suicide" in src_lower:
        lines = src.split('\n')
        for j, line in enumerate(lines):
            if "selfdestruct" in line.lower() or "suicide" in line.lower():
                # Check context for protection
                context_start = max(0, j-10)
                context_end = min(len(lines), j+3)
                context = '\n'.join(lines[context_start:context_end])

                # Check if protected
                if "onlyowner" not in context.lower() and "require(msg.sender" not in context.lower():
                    score += 5
                    vulnerabilities.append({
                        "type": "UNPROTECTED_SELFDESTRUCT",
                        "line": j+1,
                        "code": line.strip()[:60]
                    })

    # PATTERN 4: ecrecover without nonce/replay protection
    if "ecrecover" in src_lower:
        has_nonce = any(p in src_lower for p in ["nonce", "replay", "used", "processed"])
        if not has_nonce:
            score += 3
            vulnerabilities.append({
                "type": "ECRECOVER_NO_REPLAY_PROTECTION"
            })

    # PATTERN 5: Division before multiplication (precision loss)
    lines = src.split('\n')
    for j, line in enumerate(lines):
        # Look for patterns like: x / y * z (should be x * z / y)
        if re.search(r'\/ \w+ \*', line) or re.search(r'\/\w+\*', line):
            score += 2
            vulnerabilities.append({
                "type": "DIV_BEFORE_MUL",
                "line": j+1,
                "code": line.strip()[:60]
            })
            break

    # PATTERN 6: Unchecked return values on transfer
    for j, line in enumerate(lines):
        if ".transfer(" in line or ".send(" in line:
            # Check if return value is used
            if "require" not in line and "if" not in lines[j-1] if j > 0 else True:
                if line.strip().endswith(");"):
                    # Likely unchecked
                    pass  # .transfer reverts anyway, .send returns bool

    # PATTERN 7: Delegate call to user input
    for j, line in enumerate(lines):
        if "delegatecall" in line.lower():
            # Check if target comes from parameter
            if any(p in line.lower() for p in ["_target", "_to", "target", "_contract"]):
                score += 5
                vulnerabilities.append({
                    "type": "DELEGATECALL_USER_INPUT",
                    "line": j+1,
                    "code": line.strip()[:60]
                })
                break

    # PATTERN 8: Public burn/mint without proper access control
    for j, line in enumerate(lines):
        if re.search(r"function\s+(burn|mint)\s*\(", line, re.IGNORECASE):
            if "external" in line or "public" in line:
                # Check next few lines for access control
                context = '\n'.join(lines[j:min(j+5, len(lines))])
                if "onlyowner" not in context.lower() and "require" not in context.lower():
                    score += 3
                    vulnerabilities.append({
                        "type": "PUBLIC_MINT_BURN_NO_AUTH",
                        "line": j+1,
                        "code": line.strip()[:60]
                    })
                    break

    if score >= 3:
        finding = {
            "address": addr,
            "name": name,
            "balance": balance,
            "score": score,
            "compiler": compiler,
            "vulnerabilities": vulnerabilities
        }
        findings.append(finding)
        print(f"\n[!!] {name} ({addr[:12]}...) - {balance:.1f} ETH - Score: {score}")
        for v in vulnerabilities:
            print(f"     {v['type']}")

# Sort by score
findings.sort(key=lambda x: (x['score'], x['balance']), reverse=True)

print("\n" + "=" * 80)
print("TOP SUBTLE VULNERABILITY FINDINGS")
print("=" * 80)

for i, f in enumerate(findings[:15]):
    print(f"\n{i+1}. {f['name']} ({f['address']})")
    print(f"   Balance: {f['balance']:.2f} ETH | Score: {f['score']}")
    print(f"   Compiler: {f['compiler'][:30]}")
    for v in f['vulnerabilities']:
        if 'line' in v:
            print(f"   - {v['type']} (line {v['line']}): {v.get('code', '')[:50]}")
        else:
            print(f"   - {v['type']}")

with open("subtle_findings.json", "w") as f:
    json.dump(findings, f, indent=2)

print(f"\n[*] Found {len(findings)} contracts with subtle vulnerabilities")
