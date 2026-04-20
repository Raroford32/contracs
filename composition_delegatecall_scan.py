#!/usr/bin/env python3
"""
CLAUDE.md Methodology: Composition and Delegatecall Attack Scanner
Looking for:
- Delegatecall to user-controllable addresses
- Cross-protocol dependencies
- External contract integrations with manipulation potential
- Callback patterns
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
print("COMPOSITION & DELEGATECALL VULNERABILITY SCAN")
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

    # PATTERN 1: Delegatecall patterns
    if "delegatecall" in src_lower:
        # Check if target is user-controlled
        delegatecall_lines = []
        lines = src.split('\n')
        for j, line in enumerate(lines):
            if "delegatecall" in line.lower():
                delegatecall_lines.append((j+1, line.strip()[:80]))

        # Check for dangerous patterns
        dangerous_delegate = False
        for ln, code in delegatecall_lines:
            # If parameter comes from user input
            if any(p in code.lower() for p in ["_target", "_to", "_contract", "target", "impl"]):
                dangerous_delegate = True

        if delegatecall_lines:
            score += 4 if dangerous_delegate else 2
            vulnerabilities.append({
                "type": "DELEGATECALL",
                "dangerous": dangerous_delegate,
                "lines": delegatecall_lines[:3]
            })

    # PATTERN 2: External protocol dependencies
    external_deps = []
    dep_patterns = [
        (r"IUniswap", "Uniswap"),
        (r"ICurve", "Curve"),
        (r"IAave", "Aave"),
        (r"ICompound|ICToken", "Compound"),
        (r"IChainlink|AggregatorV3", "Chainlink"),
        (r"ILido|stETH", "Lido"),
        (r"IWETH", "WETH"),
        (r"IBalancer", "Balancer"),
    ]

    for pattern, dep_name in dep_patterns:
        if re.search(pattern, src, re.IGNORECASE):
            external_deps.append(dep_name)

    if len(external_deps) >= 2:
        score += 3
        vulnerabilities.append({
            "type": "MULTI_PROTOCOL_DEP",
            "protocols": external_deps
        })

    # PATTERN 3: Arbitrary call execution
    if any(p in src for p in [".call(", ".call{value:"]):
        # Find the call patterns
        call_lines = []
        lines = src.split('\n')
        for j, line in enumerate(lines):
            if ".call(" in line or ".call{" in line:
                # Check if target is user-controlled
                if any(p in line.lower() for p in ["_to", "_target", "target", "recipient"]):
                    call_lines.append((j+1, line.strip()[:80]))

        if call_lines:
            score += 3
            vulnerabilities.append({
                "type": "ARBITRARY_CALL",
                "lines": call_lines[:3]
            })

    # PATTERN 4: Callback patterns (ERC777, hooks, etc.)
    callbacks = []
    callback_patterns = [
        "tokensReceived", "tokensToSend", "onERC721Received",
        "onERC1155Received", "onFlashLoan", "uniswapV2Call",
        "executeOperation", "flashLoanCallback"
    ]

    for cb in callback_patterns:
        if cb.lower() in src_lower:
            callbacks.append(cb)

    if callbacks:
        score += 2
        vulnerabilities.append({
            "type": "CALLBACK_PATTERN",
            "callbacks": callbacks
        })

    # PATTERN 5: Low-level assembly with sload/sstore
    if "assembly" in src_lower and ("sload" in src_lower or "sstore" in src_lower):
        score += 2
        vulnerabilities.append({
            "type": "RAW_STORAGE_ACCESS"
        })

    # PATTERN 6: Create2 with user input (potential address collision)
    if "create2" in src_lower:
        score += 2
        vulnerabilities.append({
            "type": "CREATE2_DEPLOYMENT"
        })

    # PATTERN 7: Approve patterns that could be abused
    if "approve(" in src_lower and "type(uint256).max" in src_lower:
        score += 1
        vulnerabilities.append({
            "type": "INFINITE_APPROVAL"
        })

    # PATTERN 8: Price oracle usage without TWAP
    if any(p in src_lower for p in ["getprice", "latestanswer", "getlatestprice"]):
        if "twap" not in src_lower and "average" not in src_lower:
            score += 2
            vulnerabilities.append({
                "type": "SPOT_PRICE_ORACLE"
            })

    # Only save significant findings
    if score >= 4:
        finding = {
            "address": addr,
            "name": name,
            "balance": balance,
            "score": score,
            "vulnerabilities": vulnerabilities
        }
        findings.append(finding)
        print(f"\n[!!] {name} ({addr[:12]}...) - {balance:.1f} ETH - Score: {score}")
        for v in vulnerabilities:
            print(f"     {v['type']}: {v}")

# Sort by score
findings.sort(key=lambda x: (x['score'], x['balance']), reverse=True)

print("\n" + "=" * 80)
print("TOP COMPOSITION/DELEGATECALL FINDINGS")
print("=" * 80)

for i, f in enumerate(findings[:15]):
    print(f"\n{i+1}. {f['name']} ({f['address']})")
    print(f"   Balance: {f['balance']:.2f} ETH | Score: {f['score']}")
    for v in f['vulnerabilities']:
        print(f"   - {v['type']}")

with open("composition_findings.json", "w") as f:
    json.dump(findings, f, indent=2)

print(f"\n[*] Found {len(findings)} contracts with composition vulnerabilities")
