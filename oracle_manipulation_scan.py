#!/usr/bin/env python3
"""
Oracle Manipulation Vulnerability Scanner - CLAUDE.md Methodology
Looking for:
1. Spot price usage (getReserves, slot0) without TWAP
2. Lending protocols with manipulatable collateral valuation
3. Liquidation logic that can be exploited
4. Price oracle without staleness checks
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
print("ORACLE MANIPULATION VULNERABILITY SCAN")
print("=" * 80)

oracle_findings = []

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

    # PATTERN 1: Direct AMM price reads (spot price)
    spot_price_patterns = [
        "getreserves()", "reserve0", "reserve1",  # Uniswap V2
        "slot0()", "sqrtpricex96",  # Uniswap V3
        "getamountout", "getamountin",  # Router
    ]

    has_spot_price = any(p in src_lower for p in spot_price_patterns)
    if has_spot_price:
        # Check if there's TWAP or averaging
        has_twap = any(p in src_lower for p in ["twap", "observe", "timeweighted", "average"])
        if not has_twap:
            score += 4
            vulnerabilities.append("SPOT_PRICE_NO_TWAP")

    # PATTERN 2: Lending/Collateral logic
    lending_patterns = [
        "collateral", "borrowlimit", "healthfactor", "liquidat",
        "maxborrow", "loantovalue", "ltv", "collateralfactor"
    ]

    has_lending = any(p in src_lower for p in lending_patterns)
    if has_lending:
        score += 3
        vulnerabilities.append("LENDING_LOGIC")

        # Check for price dependency in lending
        if has_spot_price:
            score += 3
            vulnerabilities.append("LENDING_SPOT_PRICE")

    # PATTERN 3: Chainlink without staleness check
    if "chainlink" in src_lower or "aggregatorv3" in src_lower or "latestanswer" in src_lower:
        # Check for staleness validation
        has_staleness_check = any(p in src_lower for p in [
            "updatedat", "answeredinround", "staleness", "heartbeat"
        ])
        if not has_staleness_check:
            score += 2
            vulnerabilities.append("CHAINLINK_NO_STALENESS")

    # PATTERN 4: Price in critical operations
    critical_ops = [
        "swap", "exchange", "convert", "redeem", "withdraw",
        "borrow", "repay", "liquidate"
    ]

    if any(p in src_lower for p in critical_ops):
        # Check for price usage in these operations
        lines = src.split('\n')
        for j, line in enumerate(lines):
            if any(p in line.lower() for p in critical_ops):
                # Look for price in context
                context_start = max(0, j-5)
                context_end = min(len(lines), j+5)
                context = '\n'.join(lines[context_start:context_end])
                if any(p in context.lower() for p in ["price", "rate", "getreserves", "slot0"]):
                    if "PRICE_IN_CRITICAL_OP" not in vulnerabilities:
                        score += 2
                        vulnerabilities.append("PRICE_IN_CRITICAL_OP")
                    break

    # PATTERN 5: Flash loan callback with price usage
    flash_callbacks = ["onflashloan", "executeoperation", "uniswapv2call", "uniswapv3flashcallback"]
    if any(p in src_lower for p in flash_callbacks):
        if has_spot_price or any(p in src_lower for p in ["price", "getamount"]):
            score += 4
            vulnerabilities.append("FLASH_CALLBACK_PRICE")

    # PATTERN 6: Sandwich-able operations
    if "swap" in src_lower and "deadline" not in src_lower:
        score += 1
        vulnerabilities.append("NO_DEADLINE_CHECK")

    if score >= 4:
        finding = {
            "address": addr,
            "name": name,
            "balance": balance,
            "score": score,
            "vulnerabilities": vulnerabilities
        }
        oracle_findings.append(finding)
        print(f"\n[!!] {name} ({addr[:12]}...) - {balance:.1f} ETH - Score: {score}")
        print(f"     Vulnerabilities: {vulnerabilities}")

# Sort by score
oracle_findings.sort(key=lambda x: (x['score'], x['balance']), reverse=True)

print("\n" + "=" * 80)
print("TOP ORACLE MANIPULATION FINDINGS")
print("=" * 80)

for i, f in enumerate(oracle_findings[:15]):
    print(f"\n{i+1}. {f['name']} ({f['address']})")
    print(f"   Balance: {f['balance']:.2f} ETH | Score: {f['score']}")
    print(f"   Vulnerabilities: {f['vulnerabilities']}")

with open("oracle_findings.json", "w") as f:
    json.dump(oracle_findings, f, indent=2)

print(f"\n[*] Found {len(oracle_findings)} contracts with oracle manipulation patterns")
