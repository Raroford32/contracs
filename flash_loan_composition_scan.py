#!/usr/bin/env python3
"""
Deep scan for flash loan + composition attack vectors
Looking for:
1. Spot price usage that can be manipulated
2. Flash loan callbacks with vulnerable logic
3. Cross-protocol value extraction
4. Price oracle manipulation opportunities
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
print("FLASH LOAN + COMPOSITION ATTACK SCANNER")
print("=" * 80)

findings = []

# Key vulnerability patterns
SPOT_PRICE_PATTERNS = [
    r"getReserves\s*\(",
    r"slot0\s*\(",
    r"\.price\s*\(",
    r"getAmountOut\s*\(",
    r"getAmountsOut\s*\(",
    r"pairFor\s*\(",
    r"\.token0\s*\(",
    r"\.token1\s*\(",
]

FLASH_PATTERNS = [
    r"onFlashLoan\s*\(",
    r"executeOperation\s*\(",
    r"uniswapV2Call\s*\(",
    r"uniswapV3FlashCallback\s*\(",
    r"uniswapV3SwapCallback\s*\(",
    r"flashLoanCallback\s*\(",
    r"receiveFlashLoan\s*\(",
    r"IFlash",
]

LENDING_PATTERNS = [
    r"borrow\s*\(",
    r"repay\s*\(",
    r"liquidat",
    r"collateral",
    r"healthFactor",
    r"getAccountLiquidity",
]

DEX_INTEGRATION_PATTERNS = [
    r"IUniswap",
    r"ISushiswap",
    r"ICurve",
    r"IBalancer",
    r"swap\s*\(",
    r"addLiquidity",
    r"removeLiquidity",
]

for i, addr in enumerate(contracts):
    if i % 50 == 0:
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

    # Check for spot price patterns
    has_spot_price = False
    spot_price_types = []
    for pattern in SPOT_PRICE_PATTERNS:
        if re.search(pattern, src, re.IGNORECASE):
            has_spot_price = True
            spot_price_types.append(pattern.split("\\")[0])

    if has_spot_price:
        score += 3
        vulnerabilities.append(f"SPOT_PRICE:{','.join(list(set(spot_price_types))[:3])}")

    # Check for flash loan integration
    has_flash = False
    flash_types = []
    for pattern in FLASH_PATTERNS:
        if re.search(pattern, src, re.IGNORECASE):
            has_flash = True
            flash_types.append(pattern.split("\\")[0])

    if has_flash:
        score += 3
        vulnerabilities.append(f"FLASH_LOAN:{','.join(list(set(flash_types))[:3])}")

    # Check for lending integration
    has_lending = False
    for pattern in LENDING_PATTERNS:
        if re.search(pattern, src, re.IGNORECASE):
            has_lending = True
            break

    if has_lending:
        score += 2
        vulnerabilities.append("LENDING_INTEGRATION")

    # Check for DEX integration
    has_dex = False
    dex_types = []
    for pattern in DEX_INTEGRATION_PATTERNS:
        if re.search(pattern, src, re.IGNORECASE):
            has_dex = True
            dex_types.append(pattern.replace("\\s*", "").replace("\\(", ""))

    if has_dex:
        score += 2
        vulnerabilities.append(f"DEX:{','.join(list(set(dex_types))[:3])}")

    # Critical: Flash loan + spot price = likely vulnerable
    if has_flash and has_spot_price:
        score += 5
        vulnerabilities.append("FLASH_SPOT_COMBO")

    # Check for price-dependent transfers
    if re.search(r"(price|rate|oracle).*(transfer|send|call\{value)", src_lower):
        score += 3
        vulnerabilities.append("PRICE_DEPENDENT_TRANSFER")

    # Check for donation attack surface
    if "balanceof(address(this))" in src_lower and has_spot_price:
        score += 2
        vulnerabilities.append("DONATION_SURFACE")

    # Check for reserves-based calculation
    if "getreserves" in src_lower and ("/" in src or "mul" in src_lower):
        # Look for calculations using reserves
        lines = src.split('\n')
        for j, line in enumerate(lines):
            if "getreserves" in line.lower():
                # Check surrounding lines for calculations
                context = "\n".join(lines[max(0,j-5):min(len(lines),j+10)])
                if "/" in context or "mul" in context.lower():
                    score += 3
                    vulnerabilities.append("RESERVES_CALCULATION")
                    break

    # Check for time-weighted vs spot
    if has_spot_price:
        has_twap = any(p in src_lower for p in ["twap", "observe", "cumulative", "time-weighted"])
        if not has_twap:
            score += 2
            vulnerabilities.append("NO_TWAP_PROTECTION")

    if score >= 5:
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
print("TOP FLASH LOAN COMPOSITION FINDINGS")
print("=" * 80)

for i, f in enumerate(findings[:15]):
    print(f"\n{i+1}. {f['name']} ({f['address']})")
    print(f"   Balance: {f['balance']:.2f} ETH | Score: {f['score']}")
    print(f"   Vulnerabilities: {f['vulnerabilities']}")

with open("flash_composition_findings.json", "w") as f:
    json.dump(findings, f, indent=2)

print(f"\n[*] Found {len(findings)} contracts with flash loan/composition patterns")
