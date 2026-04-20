#!/usr/bin/env python3
"""
CLAUDE.md Deep Analysis - Focus on Composition, Boundaries, Flash Loan vectors
Per the methodology: kernel contradictions, not basic access control
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

def eth_call(to, data, block="latest"):
    return rpc_call("eth_call", [{"to": to, "data": data}, block])

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
        return None
    except:
        return None

def get_abi(addr):
    url = f"https://api.etherscan.io/v2/api?chainid=1&module=contract&action=getabi&address={addr}&apikey={ETHERSCAN_API}"
    result = subprocess.run(["curl", "-s", url], capture_output=True, text=True)
    try:
        data = json.loads(result.stdout)
        if data.get("status") == "1" and data.get("result"):
            return json.loads(data["result"])
    except:
        pass
    return None

# Load interesting protocols
with open("interesting_protocols.json", "r") as f:
    protocols = json.load(f)

print("=" * 80)
print("CLAUDE.MD KERNEL CONTRADICTION ANALYSIS")
print("Focus: Composition, Boundaries, Flash Loan, Oracle Manipulation Vectors")
print("=" * 80)

# Sort by balance (highest first)
protocols.sort(key=lambda x: x['balance'], reverse=True)

findings = []

for protocol in protocols:
    addr = protocol['address']
    name = protocol['name']
    balance = protocol['balance']
    indicators = protocol['indicators']

    print(f"\n{'='*60}")
    print(f"[ANALYZING] {name} at {addr}")
    print(f"Balance: {balance:.2f} ETH")
    print(f"Indicators: {indicators}")
    print("="*60)

    time.sleep(0.3)

    # Get source code
    source_data = get_source(addr)
    if not source_data:
        print("  [SKIP] No verified source")
        continue

    src = source_data.get("SourceCode", "")
    compiler = source_data.get("CompilerVersion", "")

    # Parse source (may be JSON for multi-file)
    if src.startswith("{{"):
        try:
            # Double curly brace JSON format
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

    # CLAUDE.md Kernel Contradiction Analysis

    # 1. BOUNDARY STATE ANALYSIS - First Depositor / Empty State
    empty_state_risk = False
    if "totalSupply" in src:
        # Check for division by totalSupply without protection
        if re.search(r'totalSupply\s*[=!<>]', src) or "/ totalSupply" in src or "/totalSupply" in src:
            if "totalSupply == 0" not in src and "totalSupply() == 0" not in src:
                empty_state_risk = True
                print("  [!] Potential first depositor vulnerability - no totalSupply==0 check")

    # 2. ORACLE MANIPULATION ANALYSIS
    oracle_vectors = []
    if "ORACLE_DEPENDENT" in indicators:
        # Check for Chainlink patterns
        if "latestRoundData" in src:
            if "updatedAt" not in src or "stalePrice" not in src.lower():
                oracle_vectors.append("STALE_PRICE_RISK")
                print("  [!] Uses latestRoundData without staleness check")

        # Check for spot price usage (manipulatable)
        if "getReserves" in src or "slot0" in src:
            oracle_vectors.append("SPOT_PRICE_MANIPULATION")
            print("  [!] Uses spot price (getReserves/slot0) - flash loan manipulatable")

        # Check for TWAP without proper window
        if "observe" in src or "consult" in src:
            # Look for window parameter
            if re.search(r'window\s*<\s*\d+', src):
                oracle_vectors.append("SHORT_TWAP_WINDOW")
                print("  [!] Short TWAP window potentially manipulatable")

    # 3. REENTRANCY ANALYSIS (beyond basic nonReentrant)
    reentrancy_vectors = []
    if "POTENTIAL_REENTRANCY" in indicators:
        # Check for external calls before state updates (CEI violation)
        external_calls = re.findall(r'\.call\{[^}]*\}\(|\.transfer\(|\.send\(', src)

        # Check for read-only reentrancy (view functions during callbacks)
        if "balanceOf" in src and ("callback" in src.lower() or "receive" in src):
            reentrancy_vectors.append("READ_ONLY_REENTRANCY")
            print("  [!] Potential read-only reentrancy - balanceOf during callbacks")

        # Cross-function reentrancy
        if len(external_calls) > 0:
            if "locked" not in src and "nonReentrant" not in src and "_notEntered" not in src:
                reentrancy_vectors.append("NO_REENTRANCY_GUARD")
                print("  [!] External calls without reentrancy guard")

    # 4. FLASH LOAN ATTACK SURFACE
    flash_loan_vectors = []
    if "flashLoan" in src or "onFlashLoan" in src or "executeOperation" in src:
        flash_loan_vectors.append("FLASH_LOAN_ENABLED")
        print("  [+] Flash loan functionality detected")

        # Check if flash loan can be used for price manipulation
        if any(v in oracle_vectors for v in ["SPOT_PRICE_MANIPULATION", "SHORT_TWAP_WINDOW"]):
            flash_loan_vectors.append("FLASH_ORACLE_MANIPULATION")
            print("  [!] Flash loan + oracle manipulation vector detected")

    # 5. SHARE/ASSET CALCULATION ISSUES (ERC4626-like)
    share_calc_issues = []
    if "convertToShares" in src or "convertToAssets" in src or "previewDeposit" in src:
        # Check for rounding attacks
        if "mulDiv" in src:
            share_calc_issues.append("HAS_MULDIV")
        else:
            if "* shares" in src or "/ shares" in src or "*shares" in src or "/shares" in src:
                share_calc_issues.append("POTENTIAL_ROUNDING")
                print("  [!] Share calculation without mulDiv - potential rounding attack")

    # 6. COMPOSITION VULNERABILITIES
    composition_risks = []
    # Check for callback-dependent logic
    if "safeTransfer" in src or "safeTransferFrom" in src:
        if "ERC777" in src or "tokensReceived" in src:
            composition_risks.append("ERC777_CALLBACK")
            print("  [!] ERC777 token callback during transfer")
        if "onERC721Received" in src or "ERC721" in src:
            composition_risks.append("ERC721_CALLBACK")
            print("  [!] ERC721 callback during transfer")

    # Check for permit/approval patterns that could be exploited
    if "permit" in src.lower() and "DOMAIN_SEPARATOR" in src:
        composition_risks.append("HAS_PERMIT")
        # Check for front-running permit attacks
        if "transferFrom" in src and "approve" not in src[:src.find("permit")]:
            composition_risks.append("PERMIT_FRONTRUN_RISK")
            print("  [!] Permit pattern - potential front-run attack")

    # 7. ARITHMETIC BOUNDARY ANALYSIS
    arithmetic_risks = []
    if "0.6" in compiler or "0.7" in compiler:
        if "SafeMath" not in src:
            arithmetic_risks.append("UNCHECKED_MATH_OLD")
            print("  [!] Old compiler without SafeMath")

    # Check for type(uint256).max patterns
    if "type(uint256).max" in src or "uint256(-1)" in src or "0xffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff" in src:
        if "allowance" in src:
            arithmetic_risks.append("INFINITE_APPROVAL")

    # Collect all vectors
    all_vectors = {
        "empty_state_risk": empty_state_risk,
        "oracle_vectors": oracle_vectors,
        "reentrancy_vectors": reentrancy_vectors,
        "flash_loan_vectors": flash_loan_vectors,
        "share_calc_issues": share_calc_issues,
        "composition_risks": composition_risks,
        "arithmetic_risks": arithmetic_risks
    }

    # Score the finding
    risk_score = 0
    risk_score += 3 if empty_state_risk else 0
    risk_score += len(oracle_vectors) * 2
    risk_score += len(reentrancy_vectors) * 2
    risk_score += len(flash_loan_vectors) * 2
    risk_score += len(share_calc_issues)
    risk_score += len(composition_risks)
    risk_score += len(arithmetic_risks)

    if risk_score > 0:
        finding = {
            "address": addr,
            "name": name,
            "balance": balance,
            "compiler": compiler,
            "risk_score": risk_score,
            "vectors": all_vectors,
            "requires_deep_dive": risk_score >= 4
        }
        findings.append(finding)

        print(f"\n  [RISK SCORE] {risk_score}")
        if risk_score >= 4:
            print("  [!!!] HIGH PRIORITY - Requires deep verification on fork")

    time.sleep(0.2)

# Sort findings by risk score
findings.sort(key=lambda x: x['risk_score'], reverse=True)

print("\n" + "=" * 80)
print("PRIORITIZED FINDINGS FOR FORK VERIFICATION")
print("=" * 80)

for i, f in enumerate(findings[:10]):
    print(f"\n{i+1}. {f['name']} ({f['address'][:10]}...)")
    print(f"   Balance: {f['balance']:.2f} ETH | Risk Score: {f['risk_score']}")
    vectors = [k for k, v in f['vectors'].items() if v]
    print(f"   Vectors: {', '.join(vectors)}")

# Save for next phase
with open("priority_targets.json", "w") as f:
    json.dump(findings, f, indent=2)

print(f"\n[*] Saved {len(findings)} findings to priority_targets.json")
