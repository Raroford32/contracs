#!/usr/bin/env python3
"""
Scan for donation attacks and cross-contract reentrancy
Focus on:
1. Contracts using balanceOf(this) in value calculations
2. External calls followed by state changes (CEI violations)
3. Callbacks that can be exploited
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
print("DONATION ATTACK & REENTRANCY SCANNER")
print("=" * 80)

findings = []

for i, addr in enumerate(contracts):
    if i % 50 == 0:
        print(f"Scanning {i}/{len(contracts)}...")

    balance = get_balance(addr)
    if balance < 40:  # Focus on 40+ ETH
        continue

    time.sleep(0.25)
    source_data = get_source(addr)
    if not source_data:
        continue

    src = source_data.get("SourceCode", "")
    name = source_data.get("ContractName", "Unknown")

    if not src:
        continue

    # Parse multi-file
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
    lines = src.split('\n')

    # PATTERN 1: Donation attack surface
    # Contract uses balanceOf(this) in calculations
    if "balanceof(address(this))" in src_lower or "address(this).balance" in src_lower:
        # Check if it's used in division or share calculation
        for j, line in enumerate(lines):
            if "balanceof(address(this))" in line.lower() or "address(this).balance" in line.lower():
                # Check surrounding context for calculations
                context = "\n".join(lines[max(0,j-3):min(len(lines),j+5)])
                if "/" in context or "div" in context.lower():
                    score += 4
                    vulnerabilities.append("DONATION_ATTACK_SURFACE")
                    break

    # PATTERN 2: CEI Violation (external call before state change)
    # Look for .call/.transfer/.send followed by state changes
    for j, line in enumerate(lines):
        if any(p in line for p in [".call{", ".transfer(", ".send("]):
            # Check following lines for state changes
            for k in range(j+1, min(j+10, len(lines))):
                if any(p in lines[k] for p in ["+=", "-=", "= ", "["] + ["storage"]):
                    if "=" in lines[k] and "return" not in lines[k].lower():
                        # Check for reentrancy guard
                        func_start = j
                        for m in range(j, max(0, j-30), -1):
                            if "function " in lines[m]:
                                func_start = m
                                break
                        func_context = "\n".join(lines[func_start:j+15])
                        if "nonreentrant" not in func_context.lower() and "reentrancyguard" not in func_context.lower():
                            score += 5
                            vulnerabilities.append("CEI_VIOLATION")
                            break
            if "CEI_VIOLATION" in vulnerabilities:
                break

    # PATTERN 3: Callback exploitation
    callback_patterns = [
        "onERC721Received",
        "onERC1155Received",
        "tokensReceived",
        "tokensToSend",
        "onFlashLoan",
        "uniswapV2Call",
    ]
    for pattern in callback_patterns:
        if pattern.lower() in src_lower:
            # Check if callback has vulnerable logic
            for j, line in enumerate(lines):
                if pattern.lower() in line.lower() and "function" in line.lower():
                    # Get function body
                    func_body = ""
                    brace_count = 0
                    started = False
                    for k in range(j, min(j+50, len(lines))):
                        if '{' in lines[k]:
                            started = True
                        if started:
                            brace_count += lines[k].count('{') - lines[k].count('}')
                            func_body += lines[k] + "\n"
                            if brace_count <= 0:
                                break

                    # Check for state changes in callback
                    if any(p in func_body for p in ["+=", "-=", "mapping", "balances["]):
                        score += 3
                        vulnerabilities.append(f"CALLBACK_STATE_CHANGE:{pattern}")
                        break

    # PATTERN 4: Read-only reentrancy (view functions during external calls)
    # Look for staticcall or view calls that might return stale data
    if "staticcall" in src_lower:
        for j, line in enumerate(lines):
            if "staticcall" in line.lower():
                # Check if result is used in value calculation
                context = "\n".join(lines[j:min(len(lines), j+10)])
                if "/" in context or "mul" in context.lower():
                    score += 2
                    vulnerabilities.append("READ_ONLY_REENTRANCY_SURFACE")
                    break

    # PATTERN 5: Missing zero checks on divisor
    for j, line in enumerate(lines):
        if "/" in line and "totalsupply" in line.lower():
            # Check if there's a zero check
            func_start = j
            for m in range(j, max(0, j-30), -1):
                if "function " in lines[m]:
                    func_start = m
                    break
            func_context = "\n".join(lines[func_start:j+1])
            if "== 0" not in func_context and "> 0" not in func_context:
                score += 2
                vulnerabilities.append("NO_ZERO_CHECK_DIVISION")
                break

    # PATTERN 6: Unchecked external call return
    for j, line in enumerate(lines):
        if ".call{" in line or ".call(" in line:
            if "require" not in lines[j] and "if" not in lines[j]:
                # Check next line
                if j+1 < len(lines):
                    if "require" not in lines[j+1] and "if" not in lines[j+1]:
                        score += 2
                        vulnerabilities.append("UNCHECKED_CALL_RETURN")
                        break

    if score >= 4:
        finding = {
            "address": addr,
            "name": name,
            "balance": balance,
            "score": score,
            "vulnerabilities": vulnerabilities,
        }
        findings.append(finding)
        print(f"\n[!!] {name} ({addr[:12]}...) - {balance:.1f} ETH - Score: {score}")
        print(f"     Vulnerabilities: {vulnerabilities}")

# Sort by score
findings.sort(key=lambda x: (x['score'], x['balance']), reverse=True)

print("\n" + "=" * 80)
print("TOP DONATION/REENTRANCY FINDINGS")
print("=" * 80)

for i, f in enumerate(findings[:15]):
    print(f"\n{i+1}. {f['name']} ({f['address']})")
    print(f"   Balance: {f['balance']:.2f} ETH | Score: {f['score']}")
    print(f"   Vulnerabilities: {f['vulnerabilities']}")

with open("donation_reentrancy_findings.json", "w") as f:
    json.dump(findings, f, indent=2)

print(f"\n[*] Found {len(findings)} contracts with donation/reentrancy patterns")
