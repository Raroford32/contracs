#!/usr/bin/env python3
"""
EXPANDED SCAN: Find ALL MetaOracleDeviationTimelock deployments and check backup=primary.

Strategy:
1. Query Morpho Blue API for ALL markets — find every unique oracle
2. Check each oracle's bytecode for EIP-1167 proxy pattern
3. For proxies pointing to known MetaOracle impls, decode primary/backup
4. Also scan for OracleRouter contracts and their targets
5. Check Steakhouse Financial deployments beyond just NUSD

Known MetaOracle implementations:
- 0xcc319ef091bc520cf6835565826212024b2d25ec (6166 bytes) — used by sNUSD, srNUSD
- 0x9b4655239e91dc9e1f7599bb88fba41b4542de5b (9517 bytes) — used by srUSDe
"""

import json
import os
import time
import urllib.request
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
        _w3 = Web3(Web3.HTTPProvider(rpc, request_kwargs={"timeout": 15}))
        bn = _w3.eth.block_number
        w3 = _w3
        print(f"Connected. Block: {bn}")
        break
    except:
        continue

def raw_call(addr, data_hex, retries=2):
    for attempt in range(retries + 1):
        try:
            return w3.eth.call({"to": Web3.to_checksum_address(addr), "data": data_hex})
        except Exception as e:
            if attempt < retries:
                time.sleep(0.5)
                continue
            return f"REVERT: {str(e)[:120]}"

def u256(data, offset=0):
    if not data or isinstance(data, str) or len(data) < offset + 32: return None
    return int.from_bytes(data[offset:offset+32], 'big')

def s256(data, offset=0):
    if not data or isinstance(data, str) or len(data) < offset + 32: return None
    val = int.from_bytes(data[offset:offset+32], 'big')
    if val >= 2**255: val -= 2**256
    return val

def addr_from(data, offset=0):
    if not data or isinstance(data, str) or len(data) < offset + 32: return None
    return "0x" + data[offset+12:offset+32].hex()

def decode_string(data):
    if not data or isinstance(data, str) or len(data) < 64: return None
    try:
        offset = u256(data, 0)
        length = u256(data, offset)
        return data[offset+32:offset+32+length].decode('utf-8', errors='replace')
    except:
        return None

# Known MetaOracle implementation addresses
META_IMPL_1 = "0xcc319ef091bc520cf6835565826212024b2d25ec"  # 6166 bytes
META_IMPL_2 = "0x9b4655239e91dc9e1f7599bb88fba41b4542de5b"  # 9517 bytes
KNOWN_IMPLS = {META_IMPL_1, META_IMPL_2}

MORPHO = "0xBBBBBbbBBb9cC5e90e3b3Af64bdAF62C37EEFFCb"

# ============================================================================
# STEP 1: Get ALL Morpho Blue markets from API
# ============================================================================
print("=" * 120)
print("STEP 1: FETCH ALL MORPHO BLUE MARKETS")
print("=" * 120)

all_markets = []
skip = 0
while True:
    query = """
    {
      markets(where: { chainId_in: [1] }, first: 100, skip: %d) {
        items {
          uniqueKey
          lltv
          collateralAsset { address symbol }
          loanAsset { address symbol decimals }
          oracleAddress
          state {
            supplyAssets
            borrowAssets
            liquidityAssets
          }
        }
      }
    }
    """ % skip

    url = "https://blue-api.morpho.org/graphql"
    data = json.dumps({"query": query}).encode()
    req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"})
    try:
        resp = urllib.request.urlopen(req, timeout=15)
        result = json.loads(resp.read().decode())
        items = result.get("data", {}).get("markets", {}).get("items", [])
        if not items:
            break
        all_markets.extend(items)
        skip += 100
        print(f"  Fetched {len(all_markets)} markets...")
        if len(items) < 100:
            break
    except Exception as e:
        print(f"  API error at skip={skip}: {e}")
        break

print(f"  Total markets fetched: {len(all_markets)}")

# Filter to markets with actual activity
active_markets = []
for m in all_markets:
    supply = int(m["state"]["supplyAssets"]) if m["state"]["supplyAssets"] else 0
    borrow = int(m["state"]["borrowAssets"]) if m["state"]["borrowAssets"] else 0
    if supply > 0 or borrow > 0:
        active_markets.append(m)

print(f"  Active markets (supply > 0): {len(active_markets)}")

# Collect unique oracle addresses
oracle_addresses = set()
for m in active_markets:
    if m.get("oracleAddress"):
        oracle_addresses.add(m["oracleAddress"].lower())

print(f"  Unique oracle addresses: {len(oracle_addresses)}")

# ============================================================================
# STEP 2: Check each oracle for EIP-1167 proxy pattern
# ============================================================================
print(f"\n{'=' * 120}")
print("STEP 2: SCAN ALL ORACLES FOR EIP-1167 PROXY (MetaOracle)")
print("=" * 120)

eip1167_oracles = []
other_oracles = []

for i, oracle_addr in enumerate(sorted(oracle_addresses)):
    if i % 50 == 0 and i > 0:
        print(f"  Scanned {i}/{len(oracle_addresses)}...")

    try:
        code = w3.eth.get_code(Web3.to_checksum_address(oracle_addr))
    except:
        continue

    if len(code) == 45:
        # EIP-1167 minimal proxy
        impl = "0x" + code[10:30].hex()
        eip1167_oracles.append({
            "oracle": oracle_addr,
            "impl": impl.lower(),
            "is_meta": impl.lower() in KNOWN_IMPLS
        })
    elif len(code) >= 40 and code[:3] == bytes.fromhex("363d3d"):
        # Could be EIP-1167 variant
        impl = "0x" + code[10:30].hex()
        eip1167_oracles.append({
            "oracle": oracle_addr,
            "impl": impl.lower(),
            "is_meta": impl.lower() in KNOWN_IMPLS
        })

print(f"\n  EIP-1167 proxy oracles found: {len(eip1167_oracles)}")

# Group by implementation
impl_groups = {}
for o in eip1167_oracles:
    impl = o["impl"]
    if impl not in impl_groups:
        impl_groups[impl] = []
    impl_groups[impl].append(o["oracle"])

print(f"  Unique implementations: {len(impl_groups)}")
for impl, oracles in sorted(impl_groups.items(), key=lambda x: -len(x[1])):
    code_len = len(w3.eth.get_code(Web3.to_checksum_address(impl)))
    known_tag = " *** KNOWN MetaOracle ***" if impl in KNOWN_IMPLS else ""
    print(f"    {impl} ({code_len} bytes): {len(oracles)} proxies{known_tag}")

# ============================================================================
# STEP 3: For EVERY EIP-1167 proxy, check if it's a MetaOracle and decode
# ============================================================================
print(f"\n{'=' * 120}")
print("STEP 3: DECODE ALL EIP-1167 ORACLE PROXIES")
print("=" * 120)

# For each proxy, read storage slots to find primary/backup
# MetaOracle storage layout:
# slot[0] = primary oracle address
# slot[1] = backup oracle address
# slot[2] = maxDiscount
# slot[3] = challengeTimelock
# slot[4] = healingTimelock
# slot[5] = currently active oracle

meta_oracles = []
non_meta_proxies = []

for o in eip1167_oracles:
    oracle_addr = o["oracle"]
    impl = o["impl"]

    # Read first 6 storage slots
    slots = []
    for s in range(6):
        try:
            val = w3.eth.get_storage_at(Web3.to_checksum_address(oracle_addr), s)
            slots.append(int.from_bytes(val, 'big'))
        except:
            slots.append(0)

    # Check if slot[0] and slot[1] look like addresses (20 bytes)
    # and slot[2]-slot[4] look like small numbers (timeouts, percentages)
    slot0_addr = "0x" + hex(slots[0])[2:].zfill(40)[-40:] if slots[0] > 2**80 and slots[0] < 2**160 else None
    slot1_addr = "0x" + hex(slots[1])[2:].zfill(40)[-40:] if slots[1] > 2**80 and slots[1] < 2**160 else None

    if slot0_addr and slot1_addr:
        # Likely a MetaOracle-like pattern (two oracle addresses)
        primary = slot0_addr
        backup = slot1_addr
        max_discount = slots[2]
        challenge_tl = slots[3]
        healing_tl = slots[4]
        active = "0x" + hex(slots[5])[2:].zfill(40)[-40:] if slots[5] > 2**80 else hex(slots[5])

        meta_oracles.append({
            "oracle": oracle_addr,
            "impl": impl,
            "primary": primary,
            "backup": backup,
            "max_discount": max_discount,
            "challenge_timelock": challenge_tl,
            "healing_timelock": healing_tl,
            "active": active,
        })
    else:
        non_meta_proxies.append({"oracle": oracle_addr, "impl": impl, "slots": slots[:3]})

print(f"  MetaOracle-pattern proxies: {len(meta_oracles)}")
print(f"  Non-MetaOracle proxies: {len(non_meta_proxies)}")

# ============================================================================
# STEP 4: Check backup=primary for each MetaOracle
# ============================================================================
print(f"\n{'=' * 120}")
print("STEP 4: CHECK BACKUP=PRIMARY ON ALL META-ORACLES")
print("=" * 120)

backup_equals_primary = []
backup_different = []

for mo in meta_oracles:
    oracle = mo["oracle"]
    primary = mo["primary"]
    backup = mo["backup"]

    # The backup might be an OracleRouter that POINTS to the primary
    # Check backup's target
    backup_target = None
    backup_code = None
    try:
        backup_code = w3.eth.get_code(Web3.to_checksum_address(backup))
    except:
        pass

    # Try OracleRouter target selector (0x7dc0d1d0)
    target_result = raw_call(backup, "0x7dc0d1d0")
    if isinstance(target_result, bytes) and len(target_result) >= 32:
        backup_target = addr_from(target_result)

    # Check direct equality or router-target equality
    direct_match = primary.lower() == backup.lower()
    router_match = backup_target and backup_target.lower() == primary.lower()

    # Also compare prices
    primary_price = None
    backup_price = None

    # Try price() selector (0xa035b1fe)
    pp = raw_call(oracle, "0xa035b1fe")
    if isinstance(pp, bytes) and len(pp) >= 32:
        primary_price = u256(pp)

    # Get price from backup oracle directly
    bp = raw_call(backup, "0xa035b1fe")
    if isinstance(bp, bytes) and len(bp) >= 32:
        backup_price = u256(bp)

    price_match = primary_price and backup_price and primary_price == backup_price

    is_match = direct_match or router_match or price_match

    entry = {
        **mo,
        "backup_target": backup_target,
        "backup_code_len": len(backup_code) if backup_code else 0,
        "primary_price": primary_price,
        "backup_price": backup_price,
        "direct_match": direct_match,
        "router_match": router_match,
        "price_match": price_match,
    }

    if is_match:
        backup_equals_primary.append(entry)
    else:
        backup_different.append(entry)

print(f"\n  BACKUP = PRIMARY: {len(backup_equals_primary)} instances")
for entry in backup_equals_primary:
    div = "0.00%" if entry["price_match"] else "N/A"
    print(f"    Oracle: {entry['oracle']}")
    print(f"      Primary: {entry['primary']}")
    print(f"      Backup:  {entry['backup']}")
    if entry["router_match"]:
        print(f"      Backup→target: {entry['backup_target']} (= primary)")
    if entry["direct_match"]:
        print(f"      Direct address match!")
    print(f"      Max discount: {entry['max_discount']/1e16 if entry['max_discount'] else 'N/A'}%")
    print(f"      Challenge timelock: {entry['challenge_timelock']}s")
    print()

print(f"\n  BACKUP ≠ PRIMARY: {len(backup_different)} instances")
for entry in backup_different:
    pp = entry["primary_price"]
    bp = entry["backup_price"]
    if pp and bp and pp > 0:
        div = abs(pp - bp) / pp * 100
    else:
        div = None
    print(f"    Oracle: {entry['oracle']}")
    print(f"      Primary: {entry['primary']}")
    print(f"      Backup:  {entry['backup']} (target: {entry['backup_target']})")
    if div is not None:
        print(f"      Price divergence: {div:.4f}%")
    print()

# ============================================================================
# STEP 5: Map affected MetaOracles to Morpho markets
# ============================================================================
print(f"\n{'=' * 120}")
print("STEP 5: MAP ALL AFFECTED ORACLES TO MORPHO MARKETS")
print("=" * 120)

affected_oracle_addrs = set(e["oracle"].lower() for e in backup_equals_primary)

affected_markets = []
for m in active_markets:
    if m.get("oracleAddress", "").lower() in affected_oracle_addrs:
        loan_dec = int(m["loanAsset"]["decimals"]) if m["loanAsset"].get("decimals") else 18
        supply = int(m["state"]["supplyAssets"]) / 10**loan_dec if m["state"]["supplyAssets"] else 0
        borrow = int(m["state"]["borrowAssets"]) / 10**loan_dec if m["state"]["borrowAssets"] else 0
        available = int(m["state"]["liquidityAssets"]) / 10**loan_dec if m["state"]["liquidityAssets"] else 0
        lltv = int(m["lltv"]) / 1e18 * 100 if m["lltv"] else 0

        affected_markets.append({
            "id": m["uniqueKey"],
            "collateral": m["collateralAsset"]["symbol"] if m["collateralAsset"] else "?",
            "collateral_addr": m["collateralAsset"]["address"] if m["collateralAsset"] else "?",
            "loan": m["loanAsset"]["symbol"] if m["loanAsset"] else "?",
            "oracle": m["oracleAddress"],
            "lltv": lltv,
            "supply": supply,
            "borrow": borrow,
            "available": available,
        })

# Sort by borrow descending
affected_markets.sort(key=lambda x: -x["borrow"])

total_supply = sum(m["supply"] for m in affected_markets)
total_borrow = sum(m["borrow"] for m in affected_markets)

print(f"\n  AFFECTED MORPHO MARKETS (backup=primary):")
print(f"  Total: {len(affected_markets)} markets")
print(f"  Total supply: ${total_supply:,.2f}")
print(f"  Total borrow: ${total_borrow:,.2f}")
print()

for m in affected_markets:
    print(f"    {m['collateral']}/{m['loan']}:")
    print(f"      Market ID: {m['id'][:20]}...")
    print(f"      Collateral: {m['collateral_addr']}")
    print(f"      Oracle: {m['oracle']}")
    print(f"      LLTV: {m['lltv']:.1f}%")
    print(f"      Supply: ${m['supply']:,.2f}")
    print(f"      Borrow: ${m['borrow']:,.2f}")
    print(f"      Available: ${m['available']:,.2f}")
    print()

# ============================================================================
# STEP 6: Also check backup≠primary oracles — what's the divergence?
# ============================================================================
print(f"\n{'=' * 120}")
print("STEP 6: ALL MetaOracle INSTANCES — DIVERGENCE REPORT")
print("=" * 120)

all_meta = backup_equals_primary + backup_different
for entry in all_meta:
    pp = entry["primary_price"]
    bp = entry["backup_price"]
    if pp and bp and pp > 0:
        div = abs(pp - bp) / pp * 100
    else:
        div = None

    # Find markets using this oracle
    markets_using = [m for m in active_markets if m.get("oracleAddress", "").lower() == entry["oracle"].lower()]
    total_borrow_m = sum(int(m["state"]["borrowAssets"] or 0) for m in markets_using)

    status = "BACKUP=PRIMARY" if entry in backup_equals_primary else "OK"

    if total_borrow_m > 0 or entry in backup_equals_primary:
        print(f"  Oracle: {entry['oracle']}")
        print(f"    Impl: {entry['impl']}")
        print(f"    Status: {status}")
        if div is not None:
            print(f"    Divergence: {div:.6f}%")
        print(f"    Markets: {len(markets_using)}, Total borrow: ${total_borrow_m/1e6:,.2f}M (raw/1e6)")
        print()

# ============================================================================
# STEP 7: SCAN FOR NON-MORPHO USAGE OF MetaOracle
# ============================================================================
print(f"\n{'=' * 120}")
print("STEP 7: SCAN FOR OTHER PROTOCOL USAGE")
print("=" * 120)

# Check if the MetaOracle implementations are referenced by other contracts
# We can check known DeFi protocols that might use these oracles
# Aave, Compound, Euler, etc.

# For now, check if any of the affected backup/primary oracles are used elsewhere
# by looking at their recent callers (we can't do this without an indexer)

# Instead, check the OracleRouter owner's other deployments
# The owner is Gnosis Safe at 0x1a9e836c455792654d8f657941ff59160eed7146

# Check all unique OracleRouter contracts found
router_addrs = set()
for entry in all_meta:
    backup_code_len = entry.get("backup_code_len", 0)
    if backup_code_len > 0 and backup_code_len < 5000:
        # Could be an OracleRouter
        router_addrs.add(entry["backup"].lower())
        if entry.get("backup_target"):
            # Also check what the router targets
            pass

print(f"  Potential OracleRouter contracts: {len(router_addrs)}")
for ra in sorted(router_addrs):
    try:
        code = w3.eth.get_code(Web3.to_checksum_address(ra))
        # Get owner
        owner_result = raw_call(ra, "0x8da5cb5b")  # owner()
        owner = addr_from(owner_result) if isinstance(owner_result, bytes) else None
        # Get target
        target_result = raw_call(ra, "0x7dc0d1d0")
        target = addr_from(target_result) if isinstance(target_result, bytes) else None
        print(f"    {ra}: {len(code)} bytes, owner={owner}, target={target}")
    except:
        pass

# Also search for additional EIP-1167 implementations that could be MetaOracle variants
# by checking code similarity
print(f"\n  Checking non-known implementations for MetaOracle-like behavior:")
for impl, oracles in impl_groups.items():
    if impl not in KNOWN_IMPLS:
        try:
            code = w3.eth.get_code(Web3.to_checksum_address(impl))
            # Check if it has challenge-like selectors
            has_challenge = False
            for i in range(len(code) - 4):
                if code[i] == 0x63:
                    sel = code[i+1:i+5].hex()
                    if sel in ["d2ef7398", "b166bf6b", "e2997d6b"]:  # Known MetaOracle selectors
                        has_challenge = True
                        break
            if has_challenge:
                print(f"    {impl} ({len(code)} bytes): HAS MetaOracle selectors! {len(oracles)} proxies")
                KNOWN_IMPLS.add(impl)
            else:
                print(f"    {impl} ({len(code)} bytes): no MetaOracle selectors, {len(oracles)} proxies")
        except:
            pass

print("\n" + "=" * 120)
print("SCAN COMPLETE")
print("=" * 120)

print(f"\nSUMMARY:")
print(f"  Total Morpho markets scanned: {len(active_markets)}")
print(f"  EIP-1167 proxy oracles: {len(eip1167_oracles)}")
print(f"  MetaOracle instances: {len(meta_oracles)}")
print(f"  BACKUP=PRIMARY instances: {len(backup_equals_primary)}")
print(f"  Affected Morpho markets: {len(affected_markets)}")
print(f"  Total exposed supply: ${total_supply:,.2f}")
print(f"  Total exposed borrow: ${total_borrow:,.2f}")

print("\nDone.")
