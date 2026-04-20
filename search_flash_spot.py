#!/usr/bin/env python3
"""
Search for contracts with flash loan callbacks or spot price dependencies
These are the actual exploitable patterns per CLAUDE.md
"""
import json
import subprocess
import time
import re

RPC = "https://mainnet.infura.io/v3/bfc7283659224dd6b5124ebbc2b14e2c"
ETHERSCAN_API = "5UWN6DNT7UZCEJYNE3J6FCVAWH4QJW255K"

def get_balance(addr):
    payload = {"jsonrpc": "2.0", "method": "eth_getBalance", "params": [addr, "latest"], "id": 1}
    cmd = ["curl", "-s", "-X", "POST", "-H", "Content-Type: application/json",
           "-d", json.dumps(payload), RPC]
    result = subprocess.run(cmd, capture_output=True, text=True)
    try:
        data = json.loads(result.stdout)
        return int(data['result'], 16) / 1e18
    except:
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
print("SEARCHING FOR FLASH LOAN + SPOT PRICE EXPLOITABLE PATTERNS")
print("=" * 80)

exploitable_patterns = []

for i, addr in enumerate(contracts):
    if i % 20 == 0:
        print(f"Scanning {i}/{len(contracts)}...")

    balance = get_balance(addr)
    if balance < 30:  # Skip low balance
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

    # EXPLOITABLE PATTERN 1: Flash loan callback + price dependency
    has_flash_callback = any(p in src_lower for p in [
        "onflashloan", "executeoperation", "flashloancallback",
        "uniswapv2call", "uniswapv3flashcallback", "pancakecall"
    ])

    # EXPLOITABLE PATTERN 2: Spot price from AMM reserves (manipulatable)
    has_spot_price = any(p in src_lower for p in [
        "getreserves()", "reserve0", "reserve1",
        "slot0()", "sqrtpricex96", "liquidity()"
    ])

    # Pattern 3: Uses price in critical operations
    uses_price_critical = any(p in src_lower for p in [
        "liquidate", "collateral", "healthfactor",
        "getprice", "borrowlimit", "maxborrow"
    ])

    # Pattern 4: Token callbacks (ERC777, ERC721, ERC1155)
    has_token_callback = any(p in src_lower for p in [
        "tokensreceived", "tokenstosend",
        "onerc721received", "onerc1155received"
    ])

    # Pattern 5: External call before state update (reentrancy)
    # Look for .call{ followed by state changes
    has_reentry_pattern = False
    if ".call{" in src or ".call(" in src:
        if "nonreentrant" not in src_lower and "reentrancyguard" not in src_lower:
            # Check if there's a state change after an external call
            lines = src.split('\n')
            for j, line in enumerate(lines):
                if ".call" in line.lower():
                    # Look for state changes in next 10 lines
                    for k in range(j+1, min(j+10, len(lines))):
                        if any(p in lines[k] for p in ['=', '+=', '-=']):
                            if 'require' not in lines[k] and 'if' not in lines[k]:
                                has_reentry_pattern = True
                                break

    # Score
    score = 0
    vectors = []

    if has_flash_callback:
        score += 3
        vectors.append("FLASH_CALLBACK")

    if has_spot_price:
        score += 3
        vectors.append("SPOT_PRICE_DEP")

    if uses_price_critical:
        score += 2
        vectors.append("PRICE_CRITICAL")

    if has_token_callback:
        score += 2
        vectors.append("TOKEN_CALLBACK")

    if has_reentry_pattern:
        score += 2
        vectors.append("REENTRY_PATTERN")

    if score >= 3:
        finding = {
            "address": addr,
            "name": name,
            "balance": balance,
            "score": score,
            "vectors": vectors
        }
        exploitable_patterns.append(finding)
        print(f"  [!!] {name} ({addr[:10]}...) - {balance:.1f} ETH - {vectors}")

# Sort by score and balance
exploitable_patterns.sort(key=lambda x: (x['score'], x['balance']), reverse=True)

print("\n" + "=" * 80)
print("TOP EXPLOITABLE TARGETS")
print("=" * 80)

for i, p in enumerate(exploitable_patterns[:20]):
    print(f"\n{i+1}. {p['name']} ({p['address']})")
    print(f"   Balance: {p['balance']:.2f} ETH | Score: {p['score']}")
    print(f"   Vectors: {', '.join(p['vectors'])}")

# Save
with open("exploitable_targets.json", "w") as f:
    json.dump(exploitable_patterns, f, indent=2)

print(f"\n[*] Found {len(exploitable_patterns)} potentially exploitable contracts")
