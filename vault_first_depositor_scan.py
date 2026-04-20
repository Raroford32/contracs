#!/usr/bin/env python3
"""
CLAUDE.md Methodology: First Depositor / Vault Donation Attack Scanner
Looking for:
- ERC4626 vaults with totalSupply=0 potential
- Share inflation via donation
- Exchange rate manipulation
- Empty pool bootstrap attacks
"""
import json
import subprocess
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

def eth_call(to, data):
    result = rpc_call("eth_call", [{"to": to, "data": data}, "latest"])
    if result and 'result' in result:
        return result['result']
    return None

# Load contracts
with open("contracts.txt", "r") as f:
    contracts = [line.strip() for line in f if line.strip().startswith("0x")]

print("=" * 80)
print("VAULT/FIRST DEPOSITOR ATTACK SCAN (CLAUDE.md Methodology)")
print("=" * 80)

vault_candidates = []

for i, addr in enumerate(contracts):
    if i % 30 == 0:
        print(f"Scanning {i}/{len(contracts)}...")

    balance = get_balance(addr)
    if balance < 20:  # Focus on 20+ ETH
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

    # PATTERN 1: ERC4626 Vault patterns
    has_vault_pattern = any(p in src_lower for p in [
        "totalsupply", "totalassets", "converttoassets", "converttoshares",
        "deposit(", "withdraw(", "redeem(", "mint(",
        "previewdeposit", "previewredeem", "previewmint", "previewwithdraw"
    ])

    # PATTERN 2: Share/exchange rate calculation
    has_share_calc = any(p in src_lower for p in [
        "shares =", "amount *", "/ totalsupply", "* totalsupply",
        "exchangerate", "pricepershare", "tokenpershare", "shareprice",
        "getpriceperfullshare", "getunderlying"
    ])

    # PATTERN 3: Direct balance usage (donation attack surface)
    has_direct_balance = any(p in src_lower for p in [
        "address(this).balance", "balanceof(address(this))",
        "token.balanceof(", "underlying.balanceof(",
        "asset.balanceof("
    ])

    # PATTERN 4: No empty state protection
    has_empty_check = any(p in src_lower for p in [
        "totalsupply == 0", "totalsupply() == 0", "totalsupply > 0",
        "_totalsupply == 0", "supply == 0", "require(totalsupply"
    ])

    # PATTERN 5: Division operations (rounding exploitation)
    has_division = "/" in src and ("amount" in src_lower or "shares" in src_lower)

    # Scoring
    score = 0
    vectors = []

    if has_vault_pattern:
        score += 3
        vectors.append("VAULT_PATTERN")

    if has_share_calc:
        score += 2
        vectors.append("SHARE_CALC")

    if has_direct_balance:
        score += 3
        vectors.append("DIRECT_BALANCE")

    if not has_empty_check and has_share_calc:
        score += 3
        vectors.append("NO_EMPTY_CHECK")

    if has_division and has_share_calc:
        score += 1
        vectors.append("DIVISION_RISK")

    if score >= 5:
        # Check current state on chain
        total_supply = None

        # Try totalSupply()
        ts_result = eth_call(addr, "0x18160ddd")  # totalSupply()
        if ts_result and ts_result != "0x" and len(ts_result) >= 66:
            try:
                total_supply = int(ts_result, 16)
            except:
                pass

        finding = {
            "address": addr,
            "name": name,
            "balance": balance,
            "score": score,
            "vectors": vectors,
            "totalSupply": total_supply
        }
        vault_candidates.append(finding)

        print(f"\n[!!] {name} ({addr[:12]}...) - {balance:.1f} ETH")
        print(f"     Vectors: {vectors}")
        print(f"     TotalSupply: {total_supply}")

# Sort by score
vault_candidates.sort(key=lambda x: (x['score'], x['balance']), reverse=True)

print("\n" + "=" * 80)
print("TOP VAULT/FIRST DEPOSITOR CANDIDATES")
print("=" * 80)

for i, v in enumerate(vault_candidates[:20]):
    print(f"\n{i+1}. {v['name']} ({v['address']})")
    print(f"   Balance: {v['balance']:.2f} ETH | Score: {v['score']}")
    print(f"   Vectors: {', '.join(v['vectors'])}")
    print(f"   TotalSupply: {v['totalSupply']}")

with open("vault_candidates.json", "w") as f:
    json.dump(vault_candidates, f, indent=2)

print(f"\n[*] Found {len(vault_candidates)} vault candidates for first depositor analysis")
