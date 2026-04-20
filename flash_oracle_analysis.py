#!/usr/bin/env python3
"""
CLAUDE.md Flash Loan + Oracle Manipulation Analysis
Focus on composition attacks that are economically feasible
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

# Load interesting protocols
with open("priority_targets.json", "r") as f:
    protocols = json.load(f)

print("=" * 80)
print("FLASH LOAN + ORACLE MANIPULATION COMPOSITION ANALYSIS")
print("=" * 80)

# Focus on oracle-dependent contracts
oracle_contracts = []
for p in protocols:
    if "oracle_vectors" in p.get("vectors", {}) and p["vectors"]["oracle_vectors"]:
        oracle_contracts.append(p)
    elif "ORACLE_DEPENDENT" in str(p.get("vectors", {})):
        oracle_contracts.append(p)

print(f"\nAnalyzing {len(oracle_contracts)} oracle-dependent contracts...")

findings = []

for contract in oracle_contracts:
    addr = contract['address']
    name = contract['name']
    balance = contract['balance']

    print(f"\n[ANALYZING] {name} at {addr}")
    print(f"Balance: {balance:.2f} ETH")

    time.sleep(0.3)
    source_data = get_source(addr)
    if not source_data:
        print("  [SKIP] No verified source")
        continue

    src = source_data.get("SourceCode", "")

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

    # CLAUDE.md Oracle Attack Vectors Analysis

    # 1. Spot price usage (directly manipulatable via flash loan)
    spot_price_vulnerable = False
    if "getReserves" in src:
        print("  [!] Uses Uniswap V2 getReserves - SPOT PRICE")
        spot_price_vulnerable = True
    if "slot0" in src:
        print("  [!] Uses Uniswap V3 slot0 - SPOT PRICE")
        spot_price_vulnerable = True
    if "getAmountOut" in src and "flashLoan" not in src:
        print("  [!] Uses getAmountOut - potentially manipulatable")
        spot_price_vulnerable = True

    # 2. TWAP with short window
    short_twap = False
    if "observe" in src or "consult" in src:
        # Check for window < 30 minutes
        twap_matches = re.findall(r'(\d+)\s*(?:seconds|minutes|hours)', src.lower())
        for match in twap_matches:
            val = int(match)
            if val < 1800 and "seconds" in src.lower():
                print(f"  [!] Short TWAP window: {val} seconds")
                short_twap = True

    # 3. Chainlink without staleness check
    chainlink_no_stale = False
    if "latestRoundData" in src or "latestAnswer" in src:
        if "updatedAt" not in src and "timestamp" not in src:
            print("  [!] Chainlink oracle without timestamp check")
            chainlink_no_stale = True

    # 4. Custom oracle that could be manipulated
    custom_oracle = False
    if "getPrice" in src or "price()" in src:
        if "onlyOwner" not in src and "Chainlink" not in src:
            print("  [!] Custom price function - check if manipulatable")
            custom_oracle = True

    # 5. Flash loan callback presence (can use for manipulation)
    has_flash_loan = "flashLoan" in src or "onFlashLoan" in src or "executeOperation" in src

    # Calculate attack feasibility
    attack_vectors = []

    if spot_price_vulnerable:
        attack_vectors.append({
            "type": "SPOT_PRICE_MANIPULATION",
            "method": "Flash loan large amount, swap to manipulate price, exploit, swap back",
            "difficulty": "TIER_2_MEV_SEARCHER",
            "potential_profit": "Depends on position size being liquidated or value being extracted"
        })

    if short_twap:
        attack_vectors.append({
            "type": "TWAP_MANIPULATION",
            "method": "Multi-block price manipulation over TWAP window",
            "difficulty": "TIER_3_SOPHISTICATED",
            "potential_profit": "Lower due to sustained manipulation cost"
        })

    if chainlink_no_stale:
        attack_vectors.append({
            "type": "STALE_PRICE_EXPLOITATION",
            "method": "Wait for oracle downtime/stale price, exploit price deviation",
            "difficulty": "TIER_1_DEFI_USER",
            "potential_profit": "Opportunistic - depends on market conditions"
        })

    if custom_oracle:
        attack_vectors.append({
            "type": "CUSTOM_ORACLE_MANIPULATION",
            "method": "Analyze custom price source for manipulation vectors",
            "difficulty": "VARIES",
            "potential_profit": "Depends on oracle implementation"
        })

    if attack_vectors:
        finding = {
            "address": addr,
            "name": name,
            "balance": balance,
            "attack_vectors": attack_vectors,
            "has_flash_loan_callback": has_flash_loan,
            "source_patterns": {
                "spot_price": spot_price_vulnerable,
                "short_twap": short_twap,
                "chainlink_no_stale": chainlink_no_stale,
                "custom_oracle": custom_oracle
            }
        }
        findings.append(finding)
        print(f"  [!!] Found {len(attack_vectors)} potential attack vectors")

print("\n" + "=" * 80)
print("PRIORITY FLASH LOAN + ORACLE ATTACK TARGETS")
print("=" * 80)

# Sort by balance and number of vectors
findings.sort(key=lambda x: (len(x['attack_vectors']), x['balance']), reverse=True)

for i, f in enumerate(findings):
    print(f"\n{i+1}. {f['name']} ({f['address'][:10]}...)")
    print(f"   Balance: {f['balance']:.2f} ETH")
    print(f"   Attack Vectors:")
    for v in f['attack_vectors']:
        print(f"     - {v['type']}: {v['difficulty']}")

# Save
with open("flash_oracle_targets.json", "w") as f:
    json.dump(findings, f, indent=2)

print(f"\n[*] Saved {len(findings)} flash loan + oracle targets")
