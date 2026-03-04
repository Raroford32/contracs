#!/usr/bin/env python3
"""
STEP 5: Investigate the backup=primary misconfiguration.
- Is this specific to PT-sNUSD or systemic across all MetaOracleDeviationTimelock instances?
- Check PT-srNUSD-28MAY2026 (same implementation 0xcc319ef...)
- Check PT-srUSDe-2APR2026 (different implementation 0x9b4655...)

STEP 6: What is NUSD/sNUSD? Can the underlying depeg?
- If yes → the backup=primary misconfiguration enables oracle manipulation

STEP 7: Check PendleChainlinkOracle expiry behavior.
- Selector 0x204f83f9 = 1772668800 = expiry timestamp
- What does the oracle return AFTER this timestamp?
- Does it lock at 1.0? Continue TWAP? Revert?
"""

import os
import time
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
        print(f"Block: {bn}")
        break
    except:
        continue

now = w3.eth.get_block("latest")["timestamp"]
print(f"Time: {time.strftime('%Y-%m-%d %H:%M:%S UTC', time.gmtime(now))}")

def raw_call(addr, data_hex):
    try:
        return w3.eth.call({"to": Web3.to_checksum_address(addr), "data": data_hex})
    except Exception as e:
        return f"REVERT: {e}"

def u256(data, offset=0):
    if isinstance(data, str): return None
    if data and len(data) >= offset + 32:
        return int.from_bytes(data[offset:offset+32], 'big')
    return None

def addr_from(data, offset=0):
    if isinstance(data, str): return None
    if data and len(data) >= offset + 32:
        return "0x" + data[offset+12:offset+32].hex()
    return None

# ============================================================================
# STEP 5: SYSTEMIC CHECK — All MetaOracle instances
# ============================================================================
print("=" * 100)
print("STEP 5: SYSTEMIC BACKUP=PRIMARY CHECK ACROSS ALL METAORACLE INSTANCES")
print("=" * 100)

# All EIP-1167 proxy oracles (45 bytes) from our earlier scan
META_ORACLES = [
    ("PT-srUSDe-2APR2026", "0x8B417d1e0C08d8005B7Ca1d5ebbc72Ea877DB391", 12_068_119, "0x9b4655239e91dc9e1f7599bb88fba41b4542de5b"),
    ("PT-sNUSD-5MAR2026",  "0xe8465B52E106d98157d82b46cA566CB9d09482A9", 6_555_145, "0xcc319ef091bc520cf6835565826212024b2d25ec"),
    ("PT-srNUSD-28MAY2026", "0x0D07087b26b28995a66050f5bb7197D439221DE3", 1_116_632, "0xcc319ef091bc520cf6835565826212024b2d25ec"),
]

for name, oracle_addr, borrow, impl in META_ORACLES:
    print(f"\n  {name} | Borrow: ${borrow:,.0f}")
    print(f"  Oracle: {oracle_addr}")
    print(f"  Impl: {impl[:20]}...")

    # Read primary oracle (0x2289445e) and backup oracle (0x836efd31)
    primary = addr_from(raw_call(oracle_addr, "0x2289445e"))
    backup = addr_from(raw_call(oracle_addr, "0x836efd31"))

    # Read max discount
    max_disc = u256(raw_call(oracle_addr, "0xd94ad837"))
    twap_dur = u256(raw_call(oracle_addr, "0x498e8b6e"))
    heartbeat = u256(raw_call(oracle_addr, "0xd83ed440"))

    print(f"  Primary oracle: {primary}")
    print(f"  Backup oracle:  {backup}")
    print(f"  TWAP duration:  {twap_dur}s ({twap_dur/3600:.1f}h)" if twap_dur else "  TWAP: ?")
    print(f"  Heartbeat:      {heartbeat}s ({heartbeat/3600:.1f}h)" if heartbeat else "  Heartbeat: ?")
    print(f"  Max discount:   {max_disc/1e18*100:.2f}%" if max_disc else "  Max discount: ?")

    # Check if backup oracle is an OracleRouter that points back to primary
    if backup:
        backup_target = addr_from(raw_call(backup, "0x7dc0d1d0"))
        backup_owner = addr_from(raw_call(backup, "0x8da5cb5b"))

        if backup_target:
            print(f"  Backup target:  {backup_target}")
            print(f"  Backup owner:   {backup_owner}")

            if primary and backup_target.lower() == primary.lower():
                print(f"  >>> !!! BACKUP = PRIMARY !!! Deviation check is DEAD!")
                print(f"  >>> Total exposed: ${borrow:,.0f}")
            else:
                print(f"  >>> Backup and primary are DIFFERENT — deviation check works")
                # Check backup oracle's price
                bp = u256(raw_call(backup, "0xa035b1fe"))
                pp = u256(raw_call(primary, "0xa035b1fe"))
                if bp and pp:
                    div = abs(bp - pp) / max(bp, pp) * 100
                    print(f"  >>> Primary price: {pp}")
                    print(f"  >>> Backup price:  {bp}")
                    print(f"  >>> Divergence:    {div:.6f}%")
        else:
            # Backup might not be an OracleRouter — try different selectors
            bp = u256(raw_call(backup, "0xa035b1fe"))
            print(f"  Backup price: {bp}")
            if bp and primary:
                pp = u256(raw_call(primary, "0xa035b1fe"))
                if pp:
                    div = abs(bp - pp) / max(bp, pp) * 100
                    print(f"  Primary price: {pp}")
                    print(f"  Divergence:    {div:.6f}%")

# ============================================================================
# STEP 6: WHAT IS NUSD/sNUSD? DEPEG RISK?
# ============================================================================
print(f"\n{'='*100}")
print("STEP 6: NUSD/sNUSD UNDERLYING ANALYSIS")
print("=" * 100)

PT_SNUSD = "0x54Bf2659B5CdFd86b75920e93C0844c0364F5166"

# PT's SY address
for sel_name, sel in [("0xc54a44b6", "SY()"), ("0xd94073d4", "unknown_addr")]:
    result = raw_call(PT_SNUSD, sel_name)
    if isinstance(result, bytes):
        a = addr_from(result)
        if a and a != "0x" + "0" * 40:
            print(f"  PT.{sel}: {a}")

# The PendleChainlinkOracle points to PT address: 0x54bf...
# From its other selector: 0xd94073d4 => 0x54bf... (the PT token)
# Let me check the PendleChainlinkOracle
PENDLE_FEED = "0xe488ee19e06eb9d5fef39b076682d959db87168b"
# Selector 0x204f83f9 = 1772668800 = expiry
# Let me check what the feed actually reads

# Get the feed's code for more selectors
code = w3.eth.get_code(Web3.to_checksum_address(PENDLE_FEED))
selectors = set()
for i in range(len(code) - 4):
    if code[i] == 0x63:
        sel = code[i+1:i+5].hex()
        selectors.add(sel)

print(f"\n  PendleChainlinkOracle all selectors ({len(selectors)} found):")
for sel in sorted(selectors):
    result = raw_call(PENDLE_FEED, "0x" + sel)
    if isinstance(result, bytes) and len(result) >= 32:
        val = u256(result)
        if val is not None:
            if val == 0:
                print(f"    0x{sel} => 0")
            elif val > 1700000000 and val < 2000000000:
                ts_str = time.strftime('%Y-%m-%d %H:%M:%S UTC', time.gmtime(val))
                hours_to = (val - now) / 3600
                print(f"    0x{sel} => {ts_str} ({hours_to:.1f}h)")
            elif val < 2**160 and val > 2**80:
                a = addr_from(result)
                # Check if it's an ERC20
                sym_result = raw_call(a, "0x95d89b41")
                sym = None
                if isinstance(sym_result, bytes) and len(sym_result) > 64:
                    try:
                        offset = u256(sym_result, 0)
                        length = u256(sym_result, offset)
                        sym = sym_result[offset+32:offset+32+length].decode('utf-8', errors='replace')
                    except:
                        pass
                print(f"    0x{sel} => {a} ({sym or '?'})")
            else:
                print(f"    0x{sel} => {val}")

# Now check what NUSD/sNUSD is
# From the scan, we should find the market/oracle/SY references
# Let me directly check the SY (Standardized Yield) to find underlying

# ============================================================================
# STEP 7: PendleChainlinkOracle EXPIRY BEHAVIOR
# ============================================================================
print(f"\n{'='*100}")
print("STEP 7: PENDLE ORACLE EXPIRY BEHAVIOR")
print("=" * 100)

# The feed has expiry 1772668800 = March 5, 2026 00:00:00 UTC
expiry = 1772668800
hours_to_expiry = (expiry - now) / 3600
print(f"  Expiry: {time.strftime('%Y-%m-%d %H:%M:%S UTC', time.gmtime(expiry))}")
print(f"  Hours to expiry: {hours_to_expiry:.2f}")
print(f"  Seconds to expiry: {expiry - now}")

# 0x598e5451 => 200000000000000000 = 0.2 * 1e18
# This could be maxAnnualRate or maxDiscountPerYear
# For a PT maturing in 0 seconds, discount = maxDiscountPerYear * 0/year = 0
# So even with 20% annual max, the discount at maturity = 0

# Check if the oracle has a "rateAtExpiry" or "priceAtExpiry" concept
# The implementation might hardcode PT = 1.0 at/after maturity

# Key question: what does the PendleChainlinkOracle return when
# block.timestamp >= expiry?
# We can't easily test this without a fork, but we can infer from the code

print(f"\n  PendleChainlinkOracle analysis:")
print(f"    0x204f83f9 = {expiry} (expiry/deadline)")
print(f"    0x598e5451 = 0.2 * 1e18 (maxDiscount or maxRate = 20%)")
print(f"    0xd94073d4 = PT token address")
print(f"    0x313ce567 = 18 (decimals)")

print(f"\n  If this is a SparkLinearDiscountOracle variant:")
print(f"    price = 1e18 * (1 - min(maxDiscount, discountRate * timeToMaturity/year))")
print(f"    At maturity: timeToMaturity = 0 → discount = 0 → price = 1e18")
print(f"    After maturity: timeToMaturity would be negative → discount = 0 → price = 1e18")
print(f"    This would be DETERMINISTIC, not TWAP-based")
print(f"    >>> If it's deterministic, it cannot be manipulated!")
print(f"    >>> The 20% is likely maxDiscountPerYear, not TWAP-related")

# But wait — the MetaOracle has TWAP duration (14400s) and heartbeat (43200s)
# These parameters make no sense for a deterministic oracle
# Unless the MetaOracle wrapper ADDS TWAP logic on top of the feed
# OR the inner "primary oracle" is NOT the feed directly — it's a ChainlinkOracleV2
# that reads the feed and could add its own logic

# Let's verify: does the primary oracle (0xd25a93...) have its own cap/discount logic?
PRIMARY = "0xd25a93399d82e1a08d9da61d21fdff7f3e65eb27"
print(f"\n  Primary oracle (0xd25a93...) full selector scan:")
code = w3.eth.get_code(Web3.to_checksum_address(PRIMARY))
selectors2 = set()
for i in range(len(code) - 4):
    if code[i] == 0x63:
        sel = code[i+1:i+5].hex()
        selectors2.add(sel)

for sel in sorted(selectors2):
    result = raw_call(PRIMARY, "0x" + sel)
    if isinstance(result, bytes) and len(result) >= 32:
        val = u256(result)
        if val is not None and val > 0:
            if val < 2**160 and val > 2**80:
                print(f"    0x{sel} => {addr_from(result)}")
            else:
                print(f"    0x{sel} => {val}")

# ============================================================================
# STEP 8: Check OTHER oracle types for same backup=primary pattern
# ============================================================================
print(f"\n{'='*100}")
print("STEP 8: CHECK IF BACKUP=PRIMARY EXISTS IN MORE MORPHO MARKETS")
print("=" * 100)

# We already found: PT-sNUSD uses backup = primary
# Let's check ALL the MorphoChainlinkOracleV2 oracles (2598-byte contracts)
# from the top PT markets
CV2_ORACLES = [
    ("PT-reUSD-25JUN2026", "0x12d66602C691Aa93E90415aB22FB0760695AC768", 42_966_205),
    ("PT-cUSD-23JUL2026", "0x25b30502467639E8FA118451105269e9B9813DD2", 2_025_408),
    ("PT-siUSD-26MAR2026", "0xEBC3653922FE589603b271D0EbD0cf7A666De343", 1_631_827),
    ("PT-stcUSD-23JUL2026", "0x11aEFbf08bAB2b3f3141c2CC4749A638c4c3b674", 1_552_305),
    ("PT-mAPOLLO-30APR2026", "0xd2943a157708a674ED6eAE27c37F91755e55154C", 1_128_929),
    ("PT-RLP-9APR2026", "0x89C3Dd5E0c78136EfE412e57CC05A7835EF9F501", 535_920),
    ("PT-mHYPER-30APR2026", "0x2ece0C95B840A80ECD67e2BAb0d7193Cb34F3CF7", 523_770),
]

print(f"\n  These use MorphoChainlinkOracleV2 directly (no MetaOracle wrapper).")
print(f"  Checking their BASE_FEED_1 for PendleChainlinkOracle patterns:")
for name, oracle, borrow in CV2_ORACLES:
    bf1 = addr_from(raw_call(oracle, "0x7bfbf0d5"))  # BASE_FEED_1
    bf2 = addr_from(raw_call(oracle, "0x2f9d31ad"))  # BASE_FEED_2
    bv = addr_from(raw_call(oracle, "0x07f8798d"))   # BASE_VAULT
    qf1 = addr_from(raw_call(oracle, "0x29f2ea6b"))  # QUOTE_FEED_1
    sf = u256(raw_call(oracle, "0xe2e35209"))         # SCALE_FACTOR

    print(f"\n  {name} (${borrow:,.0f})")
    print(f"    BASE_FEED_1: {bf1}")
    if bf1 and bf1 != "0x" + "0" * 40:
        # Check if BASE_FEED_1 is a PendleChainlinkOracle
        bf1_code = w3.eth.get_code(Web3.to_checksum_address(bf1))
        bf1_lrd = raw_call(bf1, "0xfeaf968c")
        if isinstance(bf1_lrd, bytes) and len(bf1_lrd) >= 160:
            updated_at = u256(bf1_lrd, 96)
            answer = u256(bf1_lrd, 32)
            print(f"    BASE_FEED_1 code: {len(bf1_code)} bytes")
            print(f"    latestRoundData: answer={answer}, updatedAt={updated_at}")
            if updated_at == 0:
                print(f"    >>> updatedAt=0 — PendleChainlinkOracle pattern!")
                # Check for expiry
                feed_expiry = u256(raw_call(bf1, "0x204f83f9"))
                if feed_expiry and feed_expiry > 1700000000:
                    hours_to = (feed_expiry - now) / 3600
                    print(f"    >>> expiry: {time.strftime('%Y-%m-%d %H:%M UTC', time.gmtime(feed_expiry))} ({hours_to:.1f}h)")
    print(f"    BASE_FEED_2: {bf2}")
    print(f"    BASE_VAULT:  {bv}")
    print(f"    QUOTE_FEED_1: {qf1}")
    print(f"    SCALE_FACTOR: {sf}")

print("\nDone.")
