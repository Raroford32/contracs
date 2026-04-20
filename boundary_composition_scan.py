#!/usr/bin/env python3
"""
Boundary Conditions and Composition Attack Scanner - CLAUDE.md Final Pass
Looking for:
1. Empty state / boundary conditions
2. Multi-protocol dependencies
3. Flash loan integrations
4. Deprecated protocol risks
5. Cross-contract interactions
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

def eth_call(to, data):
    result = rpc_call("eth_call", [{"to": to, "data": data}, "latest"])
    if result and 'result' in result:
        return result['result']
    return None

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
print("BOUNDARY CONDITIONS & COMPOSITION ATTACK SCAN")
print("=" * 80)

findings = []

for i, addr in enumerate(contracts):
    if i % 25 == 0:
        print(f"Scanning {i}/{len(contracts)}...")

    balance = get_balance(addr)
    if balance < 50:  # Focus on 50+ ETH
        continue

    time.sleep(0.25)
    source_data = get_source(addr)
    if not source_data:
        continue

    src = source_data.get("SourceCode", "")
    name = source_data.get("ContractName", "Unknown")

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

    # PATTERN 1: Empty state boundary conditions
    empty_checks = [
        ("totalsupply == 0", "EMPTY_SUPPLY_CHECK"),
        ("totalsupply() == 0", "EMPTY_SUPPLY_CHECK"),
        ("totalassets == 0", "EMPTY_ASSETS_CHECK"),
        ("balance == 0", "EMPTY_BALANCE_CHECK"),
        ("amount == 0", "ZERO_AMOUNT_CHECK"),
    ]

    for pattern, vuln_type in empty_checks:
        if pattern in src_lower:
            # Good - they check for empty state
            pass
        else:
            # Check if they SHOULD check (have division operations)
            if "totalsupply" in src_lower and "/" in src:
                if vuln_type == "EMPTY_SUPPLY_CHECK":
                    # Missing empty check with division
                    score += 2
                    vulnerabilities.append("MISSING_EMPTY_SUPPLY_CHECK")
                    break

    # PATTERN 2: Multi-protocol integrations
    protocol_interfaces = [
        ("IUniswap", "Uniswap"),
        ("ICurve", "Curve"),
        ("IAave", "Aave"),
        ("ICompound", "Compound"),
        ("ILido", "Lido"),
        ("IYearn", "Yearn"),
        ("IBalancer", "Balancer"),
        ("IMaker", "Maker"),
        ("ISushi", "Sushi"),
    ]

    integrated_protocols = []
    for pattern, protocol in protocol_interfaces:
        if pattern.lower() in src_lower:
            integrated_protocols.append(protocol)

    if len(integrated_protocols) >= 2:
        score += 4
        vulnerabilities.append(f"MULTI_PROTOCOL:{','.join(integrated_protocols)}")

    # PATTERN 3: Flash loan callbacks
    flash_patterns = [
        "onflashloan", "executeoperation", "uniswapv2call",
        "uniswapv3flashcallback", "flashloancallback"
    ]

    has_flash = any(p in src_lower for p in flash_patterns)
    if has_flash:
        score += 3
        vulnerabilities.append("FLASH_CALLBACK")

        # Check if uses spot price in flash callback
        if any(p in src_lower for p in ["getreserves", "slot0", "price"]):
            score += 3
            vulnerabilities.append("FLASH_WITH_SPOT_PRICE")

    # PATTERN 4: External address dependencies
    external_calls = src.count(".call(") + src.count(".call{")
    if external_calls >= 5:
        score += 2
        vulnerabilities.append(f"HIGH_EXTERNAL_CALLS:{external_calls}")

    # PATTERN 5: State-dependent calculations without cache
    if "msg.value" in src and "address(this).balance" in src:
        # Dangerous pattern - msg.value changes balance
        score += 2
        vulnerabilities.append("MSGVALUE_BALANCE_INTERACTION")

    # PATTERN 6: First depositor vulnerability markers
    if "deposit" in src_lower and "shares" in src_lower:
        if "totalsupply() == 0" not in src_lower and "totalSupply == 0" not in src_lower:
            lines = src.split('\n')
            for j, line in enumerate(lines):
                if "shares" in line.lower() and "/" in line:
                    if "totalsupply" in line.lower() or "totalassets" in line.lower():
                        score += 3
                        vulnerabilities.append("FIRST_DEPOSITOR_RISK")
                        break

    # PATTERN 7: Cross-function state dependency
    # Look for functions that read state modified by other functions without guards
    state_modifiers = []
    state_readers = []

    lines = src.split('\n')
    for j, line in enumerate(lines):
        if "function" in line:
            # Find function name
            match = re.search(r"function\s+(\w+)", line)
            if match:
                func_name = match.group(1)
                # Check function body for state changes vs reads
                func_body = ""
                brace_count = 0
                for k in range(j, min(j+50, len(lines))):
                    if '{' in lines[k]:
                        brace_count += lines[k].count('{')
                    if '}' in lines[k]:
                        brace_count -= lines[k].count('}')
                    func_body += lines[k] + "\n"
                    if brace_count <= 0 and k > j:
                        break

                # Check for state modification
                if "+=" in func_body or "-=" in func_body or " = " in func_body:
                    state_modifiers.append(func_name)
                # Check for state reading in critical ops
                if "require" in func_body and ("balance" in func_body or "supply" in func_body):
                    state_readers.append(func_name)

    # Check on-chain state
    ts = eth_call(addr, "0x18160ddd")  # totalSupply()
    total_supply = None
    if ts and ts != "0x":
        try:
            total_supply = int(ts, 16)
        except:
            pass

    # Check for potentially exploitable empty state
    if total_supply == 0 and score >= 2:
        score += 3
        vulnerabilities.append("CURRENT_EMPTY_STATE")

    if score >= 4:
        finding = {
            "address": addr,
            "name": name,
            "balance": balance,
            "score": score,
            "vulnerabilities": vulnerabilities,
            "total_supply": total_supply
        }
        findings.append(finding)
        print(f"\n[!!] {name} ({addr[:12]}...) - {balance:.1f} ETH - Score: {score}")
        print(f"     Vulnerabilities: {vulnerabilities}")

# Sort by score
findings.sort(key=lambda x: (x['score'], x['balance']), reverse=True)

print("\n" + "=" * 80)
print("TOP BOUNDARY/COMPOSITION FINDINGS")
print("=" * 80)

for i, f in enumerate(findings[:15]):
    print(f"\n{i+1}. {f['name']} ({f['address']})")
    print(f"   Balance: {f['balance']:.2f} ETH | Score: {f['score']}")
    print(f"   TotalSupply: {f['total_supply']}")
    print(f"   Vulnerabilities: {f['vulnerabilities']}")

with open("boundary_findings.json", "w") as f:
    json.dump(findings, f, indent=2)

print(f"\n[*] Found {len(findings)} contracts with boundary/composition patterns")
