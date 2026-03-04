#!/usr/bin/env python3
"""
E3 DISCRIMINATOR BATTERY — Test every attack vector simultaneously.

Vector 1: srNUSD Pendle AMM liquidity + observation cardinality
Vector 3: MetaOracle writable functions (state machine attack)
Vector 6: Pendle observation cardinality
Vector 8: OracleRouter unprotected functions
Vector 11: Feed max discount / upside behavior
"""

import os
import time
import json
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
print(f"Time: {time.strftime('%Y-%m-%d %H:%M:%S UTC', time.gmtime(now))}\n")

def raw_call(addr, data_hex):
    try:
        return w3.eth.call({"to": Web3.to_checksum_address(addr), "data": data_hex})
    except Exception as e:
        return f"REVERT: {str(e)[:100]}"

def u256(data, offset=0):
    if not data or isinstance(data, str) or len(data) < offset + 32: return None
    return int.from_bytes(data[offset:offset+32], 'big')

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

ZERO = "0x" + "0" * 40

# ============================================================================
# VECTOR 1 + 6: srNUSD Pendle AMM Analysis
# ============================================================================
print("=" * 100)
print("VECTOR 1+6: srNUSD PENDLE AMM — LIQUIDITY + OBSERVATION CARDINALITY")
print("=" * 100)

# The srNUSD TWAP feed reads from PLP-srNUSD-28MAY2026
# From earlier scan: selector 0x80f55605 => 0x723fcaa9830f6b6f68ebf7e30c097532a4cbbd26
PENDLE_MARKET_SRNUSD = "0x723fcaa9830f6b6f68ebf7e30c097532a4cbbd26"

print(f"\n  Pendle Market: {PENDLE_MARKET_SRNUSD}")
sym = decode_string(raw_call(PENDLE_MARKET_SRNUSD, "0x95d89b41"))
print(f"  Symbol: {sym}")

# Check bytecode size
code = w3.eth.get_code(Web3.to_checksum_address(PENDLE_MARKET_SRNUSD))
print(f"  Bytecode: {len(code)} bytes")

# Full selector scan on the Pendle market
sels = set()
for i in range(len(code) - 4):
    if code[i] == 0x63:
        sel = code[i+1:i+5].hex()
        sels.add(sel)

print(f"  Selectors: {len(sels)} found. Probing all...")
responding = []
for sel in sorted(sels):
    result = raw_call(PENDLE_MARKET_SRNUSD, "0x" + sel)
    if isinstance(result, bytes) and len(result) >= 32:
        val = u256(result)
        if val is not None and val > 0:
            responding.append((sel, val, result))

for sel, val, result in responding:
    if val < 2**160 and val > 2**80:
        a = addr_from(result)
        sym2 = decode_string(raw_call(a, "0x95d89b41"))
        print(f"    0x{sel} => {a} ({sym2 or '?'})")
    elif val > 1700000000 and val < 2000000000:
        ts = time.strftime('%Y-%m-%d %H:%M UTC', time.gmtime(val))
        days = (val - now) / 86400
        print(f"    0x{sel} => {ts} ({days:.1f}d)")
    elif val < 10**30:
        print(f"    0x{sel} => {val}")
    else:
        print(f"    0x{sel} => {val} ({val/1e18:.6f} if /e18)")

# KEY: Try Pendle V2 market readState to get observation cardinality
# readState(address router) returns a struct with:
#   totalPt, totalSy, lastLnImpliedRate, observationIndex,
#   observationCardinality, observationCardinalityNext
# selector: 0x68c8fbb3 readState(address)
# But we don't know the router address... try with zero address
print(f"\n  Trying readState(0x0)...")
data = "0x68c8fbb3" + "0" * 64  # readState(address(0))
result = raw_call(PENDLE_MARKET_SRNUSD, data)
if isinstance(result, bytes) and len(result) >= 192:
    totalPt = u256(result, 0)
    totalSy = u256(result, 32)
    lastLnImpliedRate = u256(result, 64)
    observationIndex = u256(result, 96)
    observationCardinality = u256(result, 128)
    observationCardinalityNext = u256(result, 160)
    print(f"    totalPt: {totalPt} ({totalPt/1e18:,.4f})")
    print(f"    totalSy: {totalSy} ({totalSy/1e18:,.4f})")
    print(f"    lastLnImpliedRate: {lastLnImpliedRate}")
    print(f"    observationIndex: {observationIndex}")
    print(f"    >>> observationCardinality: {observationCardinality}")
    print(f"    >>> observationCardinalityNext: {observationCardinalityNext}")

    if observationCardinality and observationCardinality <= 5:
        print(f"    >>> LOW CARDINALITY! TWAP is based on very few observations!")
        print(f"    >>> A single large trade could significantly shift the TWAP!")

    if totalPt and totalSy:
        total = totalPt + totalSy
        pt_pct = totalPt / total * 100
        print(f"    Total liquidity: {total/1e18:,.4f} tokens")
        print(f"    PT concentration: {pt_pct:.2f}%")
        print(f"    >>> {'HIGH PT CONCENTRATION — thin SY liquidity!' if pt_pct > 70 else 'Moderate'}")
else:
    print(f"    readState result: {result}")
    # Try without parameter
    result2 = raw_call(PENDLE_MARKET_SRNUSD, "0x68c8fbb3")
    print(f"    readState() no param: {result2}")

# Also try to get reserves directly
# Try Pendle V2 specific selectors
pendle_v2_sels = {
    "0xd3637567": "readTokens()",
    "0xd9548e53": "expiry()",
    "0x2f13b60c": "isExpired()",
    "0x18160ddd": "totalSupply()",
    "0x0902f1ac": "getReserves()",
}

for sel, name in pendle_v2_sels.items():
    result = raw_call(PENDLE_MARKET_SRNUSD, sel)
    if isinstance(result, bytes) and len(result) >= 32:
        if name == "readTokens()":
            sy = addr_from(result, 0)
            pt = addr_from(result, 32)
            yt = addr_from(result, 64)
            if sy and sy != ZERO:
                print(f"    {name}: SY={sy}, PT={pt}, YT={yt}")
        elif name == "isExpired()":
            print(f"    {name}: {bool(u256(result))}")
        elif name == "expiry()":
            val = u256(result)
            if val and val > 1700000000:
                ts = time.strftime('%Y-%m-%d %H:%M UTC', time.gmtime(val))
                days = (val - now) / 86400
                print(f"    {name}: {ts} ({days:.1f}d)")
        elif name == "totalSupply()":
            val = u256(result)
            print(f"    {name}: {val} ({val/1e18:,.4f})")
        else:
            val = u256(result)
            print(f"    {name}: {val}")

# Also check: the TWAP feed for srNUSD (at 0x281e1699...)
# It referenced PLP-srNUSD market and had TWAP_DURATION=900
# Let's check if it also references a Pendle oracle contract
SRNUSD_FEED = "0x281e1699558157572ffa68685339fb5ffbd25310"
print(f"\n  srNUSD TWAP feed selectors (for Pendle oracle ref):")
code2 = w3.eth.get_code(Web3.to_checksum_address(SRNUSD_FEED))
sels2 = set()
for i in range(len(code2) - 4):
    if code2[i] == 0x63:
        sel = code2[i+1:i+5].hex()
        sels2.add(sel)

for sel in sorted(sels2):
    result = raw_call(SRNUSD_FEED, "0x" + sel)
    if isinstance(result, bytes) and len(result) >= 32:
        val = u256(result)
        if val is not None and val > 0:
            if val < 2**160 and val > 2**80:
                a = addr_from(result)
                sym3 = decode_string(raw_call(a, "0x95d89b41"))
                print(f"    0x{sel} => {a} ({sym3 or '?'})")
            elif val > 1700000000 and val < 2000000000:
                ts = time.strftime('%Y-%m-%d %H:%M UTC', time.gmtime(val))
                print(f"    0x{sel} => {ts}")
            else:
                print(f"    0x{sel} => {val}")

# ============================================================================
# VECTOR 3: MetaOracle STATE MACHINE ATTACK
# ============================================================================
print(f"\n{'='*100}")
print("VECTOR 3: METAORACLE STATE MACHINE — WRITABLE FUNCTIONS")
print("=" * 100)

META_ORACLE = "0xe8465B52E106d98157d82b46cA566CB9d09482A9"
META_IMPL = "0xcc319ef091bc520cf6835565826212024b2d25ec"

# The MetaOracle has 19 SSTOREs — it can write state
# Let's check ALL selectors and see which ones DON'T revert when called
# (non-view functions that anyone can call)
impl_code = w3.eth.get_code(Web3.to_checksum_address(META_IMPL))
impl_sels = set()
for i in range(len(impl_code) - 4):
    if impl_code[i] == 0x63:
        sel = impl_code[i+1:i+5].hex()
        impl_sels.add(sel)

# We already know the view functions. Let's find the non-view ones.
known_views = {"2289445e", "362a07ae", "3682152b", "498e8b6e", "836efd31",
               "a035b1fe", "ad891006", "bd8f238e", "d83ed440", "d94ad837"}

unknown_sels = impl_sels - known_views
print(f"  Known view selectors: {len(known_views)}")
print(f"  Unknown selectors to test: {len(unknown_sels)}")

print(f"\n  Testing unknown selectors (looking for non-reverting state-changing functions):")
for sel in sorted(unknown_sels):
    result = raw_call(META_ORACLE, "0x" + sel)
    if isinstance(result, str) and "REVERT" in result:
        # Check if it reverts with specific error message
        err = result[:80]
        if "require" in err.lower() or "only" in err.lower() or "auth" in err.lower():
            print(f"    0x{sel}: AUTH GATED — {err}")
        elif "challenge" in err.lower() or "deviation" in err.lower():
            print(f"    0x{sel}: CHALLENGE RELATED — {err}")
        else:
            # Try with some dummy parameter
            result2 = raw_call(META_ORACLE, "0x" + sel + "0" * 64)
            if isinstance(result2, bytes):
                print(f"    0x{sel}: Succeeds with param! Returns {len(result2)} bytes")
            else:
                pass  # Normal revert, skip
    elif isinstance(result, bytes):
        val = u256(result)
        if val is not None:
            print(f"    0x{sel}: Returns {val} (already known? new view?)")

# Try specific challenge-related function signatures
challenge_sels = {
    "0x5a9e4d17": "challenge()",
    "0x6fdca5e0": "acceptChallenge()",
    "0x37664643": "heal()",
    "0x8456cb59": "pause()",
    "0x3f4ba83a": "unpause()",
    "0x7e3e7608": "triggerChallenge()",
    "0xf2fde38b": "transferOwnership(address)",
}

print(f"\n  Testing known challenge/admin function selectors:")
for sel, name in challenge_sels.items():
    result = raw_call(META_ORACLE, sel)
    if isinstance(result, str) and "REVERT" in result:
        err = result[:100]
        print(f"    {name}: REVERTS — {err}")
    elif isinstance(result, bytes):
        print(f"    {name}: SUCCEEDS! Returns {len(result)} bytes, val={u256(result)}")
    else:
        print(f"    {name}: {result}")

# ============================================================================
# VECTOR 8: ORACLEROUTER UNPROTECTED FUNCTIONS
# ============================================================================
print(f"\n{'='*100}")
print("VECTOR 8: ORACLEROUTER — UNPROTECTED FUNCTIONS")
print("=" * 100)

ORACLE_ROUTER = "0x385ad6da207565bb232c0cc93602a3b785a16960"
router_code = w3.eth.get_code(Web3.to_checksum_address(ORACLE_ROUTER))
print(f"  OracleRouter: {ORACLE_ROUTER}")
print(f"  Bytecode: {len(router_code)} bytes")

router_sels = set()
for i in range(len(router_code) - 4):
    if router_code[i] == 0x63:
        sel = router_code[i+1:i+5].hex()
        router_sels.add(sel)

print(f"  {len(router_sels)} selectors found. Testing all:")
for sel in sorted(router_sels):
    result = raw_call(ORACLE_ROUTER, "0x" + sel)
    if isinstance(result, bytes) and len(result) >= 32:
        val = u256(result)
        if val is not None and val > 0:
            if val < 2**160 and val > 2**80:
                a = addr_from(result)
                print(f"    0x{sel} => {a}")
            else:
                print(f"    0x{sel} => {val}")
    elif isinstance(result, str) and "REVERT" in result:
        # Try with param
        result2 = raw_call(ORACLE_ROUTER, "0x" + sel + "0" * 64)
        if isinstance(result2, bytes) and len(result2) >= 32:
            print(f"    0x{sel}: Needs param, returns {len(result2)} bytes (val={u256(result2)})")

# Try known setter selectors
setter_sels = {
    "0xb6f9de95": "setOracle(address)",
    "0x7adbf973": "setOracle(address)",
    "0x2f380b35": "setTarget(address)",
    "0xf2fde38b": "transferOwnership(address)",
    "0x13af4035": "setOwner(address)",
    "0x8129fc1c": "initialize()",
    "0xc4d66de8": "initialize(address)",
}

print(f"\n  Testing setter selectors:")
for sel, name in setter_sels.items():
    result = raw_call(ORACLE_ROUTER, sel + "0" * 64)
    if isinstance(result, str) and "REVERT" in result:
        err = result[:80]
        if "owner" in err.lower() or "auth" in err.lower() or "caller" in err.lower():
            print(f"    {name}: OWNER GATED — {err}")
        else:
            print(f"    {name}: REVERTS — {err}")
    elif isinstance(result, bytes):
        print(f"    !!! {name}: DOES NOT REVERT! Returns {len(result)} bytes")

# ============================================================================
# VECTOR 11: CAN PT PRICE > 1.0 IN THE FEED?
# ============================================================================
print(f"\n{'='*100}")
print("VECTOR 11: CAN PT BE PRICED ABOVE 1.0?")
print("=" * 100)

# The deterministic PendleChainlinkOracle for sNUSD:
# price = f(timestamp, expiry, maxDiscountPerYear)
# At timestamp == expiry: timeToMaturity = 0, discount = 0, price = 1.0
# At timestamp > expiry: timeToMaturity = max(0, expiry - timestamp) = 0, price = 1.0
# The price CANNOT exceed 1.0 in a deterministic linear discount formula
# UNLESS... the formula has a bug

FEED_SNUSD = "0xe488ee19e06eb9d5fef39b076682d959db87168b"
feed_price = u256(raw_call(FEED_SNUSD, "0x50d25bcd"))
if feed_price is None:
    # Try latestRoundData
    lrd = raw_call(FEED_SNUSD, "0xfeaf968c")
    if isinstance(lrd, bytes):
        feed_price = u256(lrd, 32)

print(f"  sNUSD feed price: {feed_price}")
if feed_price:
    print(f"    = {feed_price / 1e18:.10f}")
    if feed_price > 1e18:
        print(f"    >>> PT PRICED ABOVE 1.0! Overvaluation possible!")
    elif feed_price == 1e18:
        print(f"    >>> PT priced at exactly 1.0 (at/past maturity)")
    else:
        discount_pct = (1 - feed_price / 1e18) * 100
        print(f"    >>> Discount: {discount_pct:.6f}%")

# For the TWAP-based srNUSD feed, check if PT can go above 1.0
print(f"\n  srNUSD TWAP feed check:")
srnusd_price_result = raw_call(SRNUSD_FEED, "0xfeaf968c")  # latestRoundData
if isinstance(srnusd_price_result, bytes):
    srnusd_answer = u256(srnusd_price_result, 32)
    if srnusd_answer:
        print(f"    TWAP price: {srnusd_answer / 1e18:.10f}")
        if srnusd_answer > 1e18:
            print(f"    >>> TWAP SHOWS PT > 1.0! Can manipulate further upward!")

# ============================================================================
# VECTOR 4: POST-MATURITY BEHAVIOR
# ============================================================================
print(f"\n{'='*100}")
print("VECTOR 4: POST-MATURITY — WHAT HAPPENS TO SNNUSD POSITIONS?")
print("=" * 100)

PT_SNUSD = "0x54Bf2659B5CdFd86b75920e93C0844c0364F5166"
expiry = 1772668800  # March 5, 2026 00:00:00 UTC
hours_to = (expiry - now) / 3600
print(f"  PT-sNUSD expiry: {time.strftime('%Y-%m-%d %H:%M UTC', time.gmtime(expiry))}")
print(f"  Hours to expiry: {hours_to:.2f}")

# Check: what is the Morpho Blue market ID for PT-sNUSD?
# We can check if positions can still be opened/closed after maturity
# The key question: does Morpho Blue check anything about the collateral?
# Answer: No — Morpho just calls oracle.price() and checks LLTV
# If oracle.price() works post-maturity, positions work normally
# If oracle.price() reverts → positions frozen (no liquidation, no new borrows)

print(f"\n  Post-maturity oracle behavior:")
print(f"  - Deterministic feed returns 1.0 at/after maturity (confirmed)")
print(f"  - Primary oracle wraps this with SCALE_FACTOR")
print(f"  - MetaOracle passes through → price works post-maturity")
print(f"  - No liquidation blackout expected")
print(f"  BUT: PT-sNUSD can be redeemed 1:1 for sNUSD after maturity")
print(f"  If sNUSD is worth < $1.0 (NUSD depeg), redeemed collateral is worth < $1.0")
print(f"  Oracle still says $1.0 → bad debt")

# Check: is there a way to manipulate the PT redemption post-maturity?
# In Pendle V2, after maturity:
# - PT holders call redeemPY() on the market → get SY back
# - SY holders call redeem() on SY → get underlying back
# - The PY index at maturity determines the conversion

# Check if PY index is manipulable
# The PY index comes from the SY exchange rate at maturity
SY_SNUSD = "0x10c5e7711eaddc1b6b64e40ef1976fc462666409"
sy_rate = u256(raw_call(SY_SNUSD, "0x3ba0b9a9"))  # exchangeRate()
print(f"\n  SY-sNUSD exchange rate: {sy_rate}")
if sy_rate:
    print(f"    = {sy_rate / 1e18:.8f}")
    print(f"    1 SY = {sy_rate / 1e18:.8f} sNUSD underlying")

# Check SY internals
print(f"\n  SY-sNUSD selector scan:")
sy_code = w3.eth.get_code(Web3.to_checksum_address(SY_SNUSD))
print(f"  Bytecode: {len(sy_code)} bytes")
sy_sels = set()
for i in range(len(sy_code) - 4):
    if sy_code[i] == 0x63:
        sel = sy_code[i+1:i+5].hex()
        sy_sels.add(sel)

for sel in sorted(sy_sels):
    result = raw_call(SY_SNUSD, "0x" + sel)
    if isinstance(result, bytes) and len(result) >= 32:
        val = u256(result)
        if val is not None and val > 0:
            if val < 2**160 and val > 2**80:
                a = addr_from(result)
                sym3 = decode_string(raw_call(a, "0x95d89b41"))
                print(f"    0x{sel} => {a} ({sym3 or '?'})")
            elif val < 10**30:
                print(f"    0x{sel} => {val}")

print("\nDone.")
