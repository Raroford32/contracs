#!/usr/bin/env python3
"""
Token Callback Reentrancy Scanner - CLAUDE.md Methodology
Looking for:
1. ERC777 tokensReceived/tokensToSend hooks without reentrancy guards
2. ERC1155 onERC1155Received without guards
3. ERC721 onERC721Received without guards
4. Read-only reentrancy during callbacks
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
print("TOKEN CALLBACK REENTRANCY SCAN")
print("=" * 80)

callback_findings = []

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

    # Check for reentrancy guards
    has_reentrancy_guard = any(p in src_lower for p in [
        "nonreentrant", "reentrancyguard", "_locked", "_status", "mutex"
    ])

    # PATTERN 1: ERC777 callbacks
    if "tokensreceived" in src_lower or "tokenstosend" in src_lower:
        # Check if it's just interface definition or actual implementation
        if "function tokensreceived" in src_lower or "function tokenstosend" in src_lower:
            if not has_reentrancy_guard:
                score += 4
                vulnerabilities.append("ERC777_CALLBACK_NO_GUARD")

                # Find the callback implementation
                lines = src.split('\n')
                for j, line in enumerate(lines):
                    if "tokensreceived" in line.lower() or "tokenstosend" in line.lower():
                        if "function" in line.lower():
                            context = '\n'.join(lines[j:min(j+15, len(lines))])
                            if "balanceof" in context.lower() or "totalsupply" in context.lower():
                                score += 2
                                vulnerabilities.append("READS_BALANCE_IN_CALLBACK")

    # PATTERN 2: ERC1155 callbacks
    if "onerc1155received" in src_lower or "onerc1155batchreceived" in src_lower:
        if not has_reentrancy_guard:
            score += 3
            vulnerabilities.append("ERC1155_CALLBACK_NO_GUARD")

    # PATTERN 3: ERC721 callbacks
    if "onerc721received" in src_lower:
        if not has_reentrancy_guard:
            score += 2
            vulnerabilities.append("ERC721_CALLBACK_NO_GUARD")

    # PATTERN 4: Flash loan callbacks
    if any(p in src_lower for p in ["onflashloan", "executeoperation", "flashloancallback"]):
        if not has_reentrancy_guard:
            score += 4
            vulnerabilities.append("FLASH_CALLBACK_NO_GUARD")

    # PATTERN 5: Uniswap callbacks
    if any(p in src_lower for p in ["uniswapv2call", "uniswapv3flashcallback", "pancakecall"]):
        if not has_reentrancy_guard:
            score += 4
            vulnerabilities.append("UNISWAP_CALLBACK_NO_GUARD")

    # PATTERN 6: External calls before state changes (CEI violation)
    # Look for patterns like: call -> state change
    if ".call{" in src or ".call(" in src or "safeTransfer" in src:
        lines = src.split('\n')
        for j, line in enumerate(lines):
            if any(p in line.lower() for p in [".call{", ".call(", "safetransfer", "transfer("]):
                # Check if there's a state change AFTER this in the same function
                # Look at next 15 lines for assignments
                for k in range(j+1, min(j+15, len(lines))):
                    next_line = lines[k]
                    # Look for state changes (assignments, mappings)
                    if any(p in next_line for p in ['=', '+=', '-=', 'delete ']):
                        if 'require' not in next_line and 'if' not in next_line.lower():
                            if not has_reentrancy_guard:
                                if "CEI_VIOLATION" not in vulnerabilities:
                                    score += 3
                                    vulnerabilities.append("CEI_VIOLATION")
                                break

    # PATTERN 7: Read-only reentrancy risk
    # Contracts that call view functions during state inconsistency
    if any(p in src_lower for p in ["balanceof", "totalsupply", "getreserves"]):
        # Check if these are called after external calls
        lines = src.split('\n')
        for j, line in enumerate(lines):
            if any(p in line.lower() for p in [".call{", ".call(", "safetransfer"]):
                # Look for view function calls in next lines
                for k in range(j+1, min(j+10, len(lines))):
                    if any(p in lines[k].lower() for p in ["balanceof", "totalsupply", "getreserves"]):
                        if not has_reentrancy_guard:
                            if "READ_ONLY_REENTRY_RISK" not in vulnerabilities:
                                score += 3
                                vulnerabilities.append("READ_ONLY_REENTRY_RISK")
                            break

    if score >= 3:
        finding = {
            "address": addr,
            "name": name,
            "balance": balance,
            "score": score,
            "vulnerabilities": vulnerabilities,
            "has_reentrancy_guard": has_reentrancy_guard
        }
        callback_findings.append(finding)
        print(f"\n[!!] {name} ({addr[:12]}...) - {balance:.1f} ETH - Score: {score}")
        print(f"     Vulnerabilities: {vulnerabilities}")
        print(f"     Has Guard: {has_reentrancy_guard}")

# Sort by score
callback_findings.sort(key=lambda x: (x['score'], x['balance']), reverse=True)

print("\n" + "=" * 80)
print("TOP TOKEN CALLBACK REENTRANCY FINDINGS")
print("=" * 80)

for i, f in enumerate(callback_findings[:15]):
    print(f"\n{i+1}. {f['name']} ({f['address']})")
    print(f"   Balance: {f['balance']:.2f} ETH | Score: {f['score']}")
    print(f"   Vulnerabilities: {f['vulnerabilities']}")
    print(f"   Has Reentrancy Guard: {f['has_reentrancy_guard']}")

with open("callback_findings.json", "w") as f:
    json.dump(callback_findings, f, indent=2)

print(f"\n[*] Found {len(callback_findings)} contracts with callback reentrancy patterns")
