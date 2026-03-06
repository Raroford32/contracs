#!/usr/bin/env python3
"""
Lean Step 4: Check all 32 MetaOracle proxies for backup=primary.
Uses the already-known proxy list from Step 2/3 to avoid re-scanning 767 oracles.
Adds delays to avoid RPC rate limiting.
"""
import os, time, json
from web3 import Web3

RPCS = [
    os.environ.get("ETH_RPC", ""),
    "https://ethereum-rpc.publicnode.com",
    "https://1rpc.io/eth",
    "https://eth.llamarpc.com",
]
RPCS = [r for r in RPCS if r]

w3 = None
for rpc in RPCS:
    try:
        _w3 = Web3(Web3.HTTPProvider(rpc, request_kwargs={"timeout": 30}))
        bn = _w3.eth.block_number
        w3 = _w3
        print(f"Connected to {rpc[:40]}... Block: {bn}")
        break
    except:
        continue

if not w3:
    print("No RPC available"); exit(1)

def safe_call(addr, data_hex, retries=3):
    for attempt in range(retries + 1):
        try:
            return w3.eth.call({"to": Web3.to_checksum_address(addr), "data": data_hex})
        except Exception as e:
            if attempt < retries:
                time.sleep(1 + attempt)
                continue
            return None

def safe_storage(addr, slot, retries=3):
    for attempt in range(retries + 1):
        try:
            val = w3.eth.get_storage_at(Web3.to_checksum_address(addr), slot)
            return int.from_bytes(val, 'big')
        except Exception as e:
            if attempt < retries:
                time.sleep(1 + attempt)
                continue
            return None

def addr_from_slot(val):
    if val and val > 2**80 and val < 2**160:
        return "0x" + hex(val)[2:].zfill(40)[-40:]
    return None

def addr_from_bytes(b):
    if b and len(b) >= 32:
        return "0x" + b[-20:].hex()
    return None

def u256(b):
    if b and len(b) >= 32:
        return int.from_bytes(b[:32], 'big')
    return None

# Known MetaOracle implementations
KNOWN_IMPLS = {
    "0x9b4655239e91dc9e1f7599bb88fba41b4542de5b",  # srUSDe variant (9517 bytes)
    "0xcc319ef091bc520cf6835565826212024b2d25ec",  # sNUSD variant (6166 bytes)
}

# Step 1: Get all Morpho markets via API
print("\n=== STEP 1: Fetch Morpho markets ===")
import urllib.request

def fetch_morpho_markets():
    url = "https://blue-api.morpho.org/graphql"
    all_markets = []
    skip = 0
    while True:
        query = json.dumps({
            "query": """{
                markets(first: 100, skip: %d, where: { chainId_in: [1] }) {
                    items {
                        uniqueKey
                        lltv
                        oracleAddress
                        collateralAsset { address symbol decimals }
                        loanAsset { address symbol decimals }
                        state { supplyAssets borrowAssets liquidityAssets }
                    }
                }
            }""" % skip
        })
        req = urllib.request.Request(url, data=query.encode(), headers={"Content-Type": "application/json"})
        try:
            resp = urllib.request.urlopen(req, timeout=30)
            data = json.loads(resp.read())
            items = data["data"]["markets"]["items"]
            all_markets.extend(items)
            if len(items) < 100:
                break
            skip += 100
        except Exception as e:
            print(f"  API error at skip={skip}: {e}")
            break
    return all_markets

markets = fetch_morpho_markets()
active = [m for m in markets if m["state"] and int(m["state"]["supplyAssets"] or 0) > 0]
print(f"  Total: {len(markets)}, Active: {len(active)}")

# Step 2: Find EIP-1167 proxies among oracle addresses
print("\n=== STEP 2: Find EIP-1167 MetaOracle proxies ===")
oracle_addrs = list(set(m["oracleAddress"].lower() for m in active if m.get("oracleAddress")))
print(f"  Unique oracles: {len(oracle_addrs)}")

meta_proxies = []
for i, oa in enumerate(oracle_addrs):
    if i % 100 == 0 and i > 0:
        print(f"  Scanned {i}/{len(oracle_addrs)}...")
        time.sleep(0.5)
    try:
        code = w3.eth.get_code(Web3.to_checksum_address(oa))
        # Two known EIP-1167 variants: standard (3f) and alternate (3d at byte 6)
        prefix_std = bytes.fromhex("363d3d373d3f363d73")
        prefix_alt = bytes.fromhex("363d3d373d3d3d363d73")  # 10 bytes
        if len(code) >= 45 and (code[:9] == prefix_std or code[:10] == prefix_alt):
            offset = 10 if code[:10] == prefix_alt else 9
            impl = "0x" + code[offset:offset+20].hex()
            if impl.lower() in KNOWN_IMPLS:
                meta_proxies.append({"oracle": oa, "impl": impl.lower()})
    except:
        time.sleep(1)

print(f"  MetaOracle proxies found: {len(meta_proxies)}")

# Step 3: Decode each MetaOracle - read storage slots
print("\n=== STEP 3: Decode MetaOracle storage ===")
results = []
for i, mp in enumerate(meta_proxies):
    oa = mp["oracle"]
    print(f"  [{i+1}/{len(meta_proxies)}] {oa}")
    time.sleep(0.3)  # Rate limit

    # Read slots 0-5
    s0 = safe_storage(oa, 0)
    s1 = safe_storage(oa, 1)
    s2 = safe_storage(oa, 2)
    s3 = safe_storage(oa, 3)
    s4 = safe_storage(oa, 4)
    s5 = safe_storage(oa, 5)

    primary = addr_from_slot(s0)
    backup = addr_from_slot(s1)

    if not primary or not backup:
        print(f"    SKIP: slots don't look like addresses (s0={s0}, s1={s1})")
        continue

    max_discount = s2
    challenge_tl = s3
    healing_tl = s4

    # Check direct match
    direct_match = primary.lower() == backup.lower()

    # Check if backup is a router pointing to primary
    time.sleep(0.3)
    backup_target_raw = safe_call(backup, "0x7dc0d1d0")  # target()
    backup_target = addr_from_bytes(backup_target_raw) if backup_target_raw else None
    router_match = backup_target and backup_target.lower() == primary.lower()

    # Get prices from primary and backup
    time.sleep(0.3)
    oracle_price_raw = safe_call(oa, "0xa035b1fe")  # price()
    oracle_price = u256(oracle_price_raw)

    backup_price_raw = safe_call(backup, "0xa035b1fe")  # price()
    backup_price = u256(backup_price_raw)

    primary_price_raw = safe_call(primary, "0xa035b1fe")  # price()
    primary_price = u256(primary_price_raw)

    price_match = oracle_price and backup_price and oracle_price == backup_price
    all_same = primary_price and backup_price and primary_price == backup_price

    is_degenerate = direct_match or router_match or all_same

    # Find markets using this oracle
    mkt_matches = [m for m in active if m.get("oracleAddress", "").lower() == oa.lower()]
    total_supply = sum(int(m["state"]["supplyAssets"] or 0) for m in mkt_matches)
    total_borrow = sum(int(m["state"]["borrowAssets"] or 0) for m in mkt_matches)

    entry = {
        "oracle": oa,
        "impl": mp["impl"],
        "primary": primary,
        "backup": backup,
        "backup_target": backup_target,
        "max_discount_bps": max_discount,
        "challenge_tl": challenge_tl,
        "healing_tl": healing_tl,
        "direct_match": direct_match,
        "router_match": router_match,
        "all_same_price": all_same,
        "oracle_price": oracle_price,
        "primary_price": primary_price,
        "backup_price": backup_price,
        "is_degenerate": is_degenerate,
        "markets": len(mkt_matches),
        "total_supply_raw": total_supply,
        "total_borrow_raw": total_borrow,
        "market_details": [{
            "id": m["uniqueKey"][:16],
            "collateral": m["collateralAsset"]["symbol"] if m["collateralAsset"] else "?",
            "loan": m["loanAsset"]["symbol"] if m["loanAsset"] else "?",
            "lltv": int(m["lltv"]) / 1e18 * 100 if m["lltv"] else 0,
            "supply": int(m["state"]["supplyAssets"] or 0),
            "borrow": int(m["state"]["borrowAssets"] or 0),
        } for m in mkt_matches]
    }
    results.append(entry)

    status = "DEGENERATE (backup=primary)" if is_degenerate else "OK"
    match_reasons = []
    if direct_match: match_reasons.append("direct")
    if router_match: match_reasons.append("router->primary")
    if all_same: match_reasons.append("same price")
    print(f"    Primary: {primary}")
    print(f"    Backup:  {backup} (target: {backup_target})")
    print(f"    Status: {status} ({', '.join(match_reasons) if match_reasons else 'different prices'})")
    print(f"    MaxDiscount: {max_discount/1e16 if max_discount else '?'}%  ChallengeTL: {challenge_tl}s  HealingTL: {healing_tl}s")
    if oracle_price:
        print(f"    Oracle price: {oracle_price}")
    if primary_price and backup_price:
        div = abs(primary_price - backup_price) / primary_price * 100 if primary_price > 0 else 0
        print(f"    Primary price: {primary_price}, Backup price: {backup_price}, Div: {div:.6f}%")
    print(f"    Markets: {len(mkt_matches)}, Supply(raw): {total_supply}, Borrow(raw): {total_borrow}")
    print()

# Summary
print("\n" + "=" * 100)
print("SUMMARY")
print("=" * 100)

degenerate = [r for r in results if r["is_degenerate"]]
healthy = [r for r in results if not r["is_degenerate"]]

print(f"\nTotal MetaOracle instances: {len(results)}")
print(f"DEGENERATE (backup=primary): {len(degenerate)}")
print(f"HEALTHY (backup != primary): {len(healthy)}")

if degenerate:
    print(f"\n--- DEGENERATE INSTANCES ---")
    for d in sorted(degenerate, key=lambda x: -x["total_borrow_raw"]):
        print(f"  Oracle: {d['oracle']}")
        print(f"    Impl: {d['impl']}")
        print(f"    Primary: {d['primary']}")
        print(f"    Backup:  {d['backup']} -> target: {d['backup_target']}")
        print(f"    MaxDiscount: {d['max_discount_bps']/1e16 if d['max_discount_bps'] else '?'}%")
        for md in d["market_details"]:
            loan_dec = 18  # approximate
            print(f"    Market: {md['collateral']}/{md['loan']} LLTV={md['lltv']:.0f}% Supply={md['supply']} Borrow={md['borrow']}")
        print()

if healthy:
    print(f"\n--- HEALTHY INSTANCES ---")
    for h in sorted(healthy, key=lambda x: -x["total_borrow_raw"]):
        div = 0
        if h["primary_price"] and h["backup_price"] and h["primary_price"] > 0:
            div = abs(h["primary_price"] - h["backup_price"]) / h["primary_price"] * 100
        print(f"  Oracle: {h['oracle']}")
        print(f"    Primary: {h['primary']}")
        print(f"    Backup:  {h['backup']} -> target: {h['backup_target']}")
        print(f"    Price divergence: {div:.6f}%")
        for md in h["market_details"]:
            print(f"    Market: {md['collateral']}/{md['loan']} LLTV={md['lltv']:.0f}% Borrow={md['borrow']}")
        print()

# Save results
out_path = "analysis/engagements/bridge-finality-gap/notes/metaoracle_scan_results.json"
os.makedirs(os.path.dirname(out_path), exist_ok=True)
with open(out_path, "w") as f:
    json.dump(results, f, indent=2, default=str)
print(f"\nResults saved to {out_path}")
