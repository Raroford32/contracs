#!/usr/bin/env python3
"""
E3 DISCRIMINATOR: Stale TWAP exploitation on PT-srNUSD.

Key insight: All TWAP observations are 73-80+ hours old.
If the market is illiquid, a single trade could dominate the TWAP.

Pendle V2 TWAP uses cumulative lnImpliedRate like Uniswap V3 TWAP.
TWAP = (cumulativeLast - cumulativeOld) / (timestampLast - timestampOld)

If timestampOld is 80 hours ago and we make one trade NOW:
- The new observation has current timestamp
- But the TWAP window is only 15 min (900s)
- So it needs observations within the last 15 min
- If none exist, it interpolates/extrapolates from the nearest observation

Question: does Pendle extrapolate from stale observations, or does it use
the last known rate? This is CRITICAL for attack feasibility.
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
print(f"Time: {time.strftime('%Y-%m-%d %H:%M:%S UTC', time.gmtime(now))}\n")

def raw_call(addr, data_hex):
    try:
        return w3.eth.call({"to": Web3.to_checksum_address(addr), "data": data_hex})
    except Exception as e:
        return f"REVERT: {str(e)[:120]}"

def u256(data, offset=0):
    if not data or isinstance(data, str) or len(data) < offset + 32: return None
    return int.from_bytes(data[offset:offset+32], 'big')

def s256(data, offset=0):
    """Signed int256"""
    if not data or isinstance(data, str) or len(data) < offset + 32: return None
    val = int.from_bytes(data[offset:offset+32], 'big')
    if val >= 2**255:
        val -= 2**256
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

MARKET = "0x723fcaa9830f6b6f68ebf7e30c097532a4cbbd26"
SY_SRNUSD = "0xdb8f1d15880b97dc38edfa46d8a5a7e5b506c45f"
PT_SRNUSD = "0x82b853DB31F025858792d8fA969f2a1Dc245C179"
SRNUSD_FEED = "0x281e1699558157572ffa68685339fb5ffbd25310"

# ============================================================================
# 1. SCAN ALL OBSERVATIONS — How many exist? How stale?
# ============================================================================
print("=" * 100)
print("1. FULL OBSERVATION SCAN — ALL SLOTS")
print("=" * 100)

observations = []
for idx in range(100):  # scan up to 100
    padded_idx = hex(idx)[2:].zfill(64)
    data = "0x252c09d7" + padded_idx  # observations(uint256)
    result = raw_call(MARKET, data)
    if isinstance(result, bytes) and len(result) >= 96:
        ts = u256(result, 0) & 0xFFFFFFFF  # uint32
        lnCumulative = u256(result, 32)
        initialized = u256(result, 64)
        if ts > 0:
            age_hours = (now - ts) / 3600
            observations.append({
                'idx': idx,
                'ts': ts,
                'age_hours': age_hours,
                'lnCumulative': lnCumulative,
                'initialized': bool(initialized)
            })
        else:
            # Stop at first empty slot
            break
    else:
        break

print(f"  Total observations: {len(observations)}")
if observations:
    newest = min(observations, key=lambda o: o['age_hours'])
    oldest = max(observations, key=lambda o: o['age_hours'])
    print(f"  Newest: idx={newest['idx']}, {newest['age_hours']:.1f}h ago ({time.strftime('%Y-%m-%d %H:%M', time.gmtime(newest['ts']))})")
    print(f"  Oldest: idx={oldest['idx']}, {oldest['age_hours']:.1f}h ago ({time.strftime('%Y-%m-%d %H:%M', time.gmtime(oldest['ts']))})")

    # Show all observations sorted by timestamp
    sorted_obs = sorted(observations, key=lambda o: o['ts'])
    print(f"\n  All observations (sorted by time):")
    for o in sorted_obs:
        print(f"    [{o['idx']:3d}] {time.strftime('%Y-%m-%d %H:%M:%S', time.gmtime(o['ts']))} ({o['age_hours']:.1f}h ago) cumulative={o['lnCumulative']}")

    # Calculate implied rates between consecutive observations
    if len(sorted_obs) >= 2:
        print(f"\n  Implied rates between observations:")
        for i in range(1, len(sorted_obs)):
            prev = sorted_obs[i-1]
            curr = sorted_obs[i]
            dt = curr['ts'] - prev['ts']
            if dt > 0:
                d_cum = curr['lnCumulative'] - prev['lnCumulative']
                rate = d_cum / dt if dt > 0 else 0
                print(f"    [{prev['idx']}→{curr['idx']}] dt={dt}s, rate={rate/1e18:.10f}")

# ============================================================================
# 2. PENDLE MARKET STATE — Get current implied rate and other params
# ============================================================================
print(f"\n{'='*100}")
print("2. PENDLE MARKET STATE")
print("=" * 100)

# Try various selectors for market state
market_sels = {
    "0x3ba0b9a9": "exchangeRate()",
    "0x18160ddd": "totalSupply()",
    "0x1b3ed722": "getReserves()",
    "0x09218e91": "lastImpliedRate()",
    "0x69d38ed2": "scalarRoot()",
    "0x10b5ad68": "initialAnchor()",
    "0x204f83f9": "expiry()",
    "0x0dfe1681": "token0()",
    "0xd21220a7": "token1()",
    "0x7158da7c": "readTokens()",
}

for sel, name in market_sels.items():
    result = raw_call(MARKET, sel)
    if isinstance(result, bytes) and len(result) >= 32:
        val = u256(result)
        if val is not None and val > 0:
            if val < 2**160 and val > 2**80:
                a = addr_from(result)
                sym = decode_string(raw_call(a, "0x95d89b41"))
                print(f"  {name}: {a} ({sym})")
            elif val > 1700000000 and val < 2000000000:
                ts = time.strftime('%Y-%m-%d %H:%M UTC', time.gmtime(val))
                days = (val - now) / 86400
                print(f"  {name}: {ts} ({days:.1f} days)")
            else:
                print(f"  {name}: {val}")
                if name == "exchangeRate()":
                    print(f"    = {val/1e18:.10f}")
                elif name == "totalSupply()":
                    print(f"    = {val/1e18:,.2f}")
                elif "Rate" in name or "rate" in name:
                    print(f"    = {val/1e18:.10f}")
                elif name in ["scalarRoot()", "initialAnchor()"]:
                    print(f"    = {val/1e18:.6f}")
    elif isinstance(result, bytes) and len(result) >= 96:
        # Multi-return
        if name == "readTokens()":
            sy = addr_from(result, 0)
            pt = addr_from(result, 32)
            yt = addr_from(result, 64)
            print(f"  {name}: SY={sy}, PT={pt}, YT={yt}")
        elif name == "getReserves()":
            r0 = u256(result, 0)
            r1 = u256(result, 32)
            print(f"  {name}: r0={r0}, r1={r1}")

# ============================================================================
# 3. TWAP FEED INTERNALS — How does it compute the TWAP?
# ============================================================================
print(f"\n{'='*100}")
print("3. TWAP FEED INTERNALS")
print("=" * 100)

# The feed at 0x281e1699... is 8679 bytes with 15 STATICCALL
# It reads from the Pendle market
# Key selectors we already know:
# 0x26d89545 => 900 (TWAP duration)
# 0x80f55605 => market address
# 0x4ae5fa9b => 1e18 (scale)

# Let's see what the feed actually calls
# The feed likely calls market.observe(uint32[] secondsAgos)
# Pendle V2 observe returns (uint216[] lnImpliedRateCumulatives)

# Try market.observe([0, 900]) = observe current and 15 min ago
# observe(uint32[]) selector = 0x883bdbfd (Uniswap V3 compatible)
# But Pendle might use different selector

# Let's scan the market for observe-like functions
market_code = w3.eth.get_code(Web3.to_checksum_address(MARKET))
print(f"  Market bytecode: {len(market_code)} bytes")

# Try Pendle's observe function
# In Pendle V2, it's observe(uint32 duration) that returns the TWAP directly
# PendlePYOracleLib.getOracleRate(market, duration) is the standard way

# Let's try calling the feed's latestRoundData and observe the return
lrd = raw_call(SRNUSD_FEED, "0xfeaf968c")
if isinstance(lrd, bytes):
    roundId = u256(lrd, 0)
    answer = s256(lrd, 32)
    startedAt = u256(lrd, 64)
    updatedAt = u256(lrd, 96)
    answeredInRound = u256(lrd, 128)
    print(f"  latestRoundData():")
    print(f"    roundId: {roundId}")
    print(f"    answer: {answer} ({answer/1e18:.10f})")
    print(f"    startedAt: {startedAt}")
    print(f"    updatedAt: {updatedAt}")
    if updatedAt and updatedAt > 1700000000:
        age = (now - updatedAt) / 3600
        print(f"      = {time.strftime('%Y-%m-%d %H:%M UTC', time.gmtime(updatedAt))} ({age:.1f}h ago)")
    elif updatedAt == 0:
        print(f"      = 0 !!! NO STALENESS DATA !!!")
    print(f"    answeredInRound: {answeredInRound}")

# Also check latestAnswer directly
la = raw_call(SRNUSD_FEED, "0x50d25bcd")
if isinstance(la, bytes):
    val = s256(la)
    if val:
        print(f"  latestAnswer(): {val/1e18:.10f}")

# ============================================================================
# 4. SIMULATE TWAP MANIPULATION — What trade size moves it?
# ============================================================================
print(f"\n{'='*100}")
print("4. TWAP MANIPULATION FEASIBILITY")
print("=" * 100)

# AMM reserves
sy_balance = u256(raw_call(SY_SRNUSD, "0x70a08231" + MARKET.lower().replace("0x", "").zfill(64)))
pt_balance = u256(raw_call(PT_SRNUSD, "0x70a08231" + MARKET.lower().replace("0x", "").zfill(64)))

if sy_balance and pt_balance:
    sy = sy_balance / 1e18
    pt = pt_balance / 1e18
    total = sy + pt
    print(f"  SY reserves: {sy:,.2f}")
    print(f"  PT reserves: {pt:,.2f}")
    print(f"  Total liquidity: {total:,.2f}")
    print(f"  PT/Total ratio: {pt/total:.4f}")
    print(f"  SY/PT ratio: {sy/pt:.4f}")

    # Pendle V2 uses a modified constant product with time-decay
    # But for rough estimate, constant product approximation:
    # To move price by X%, need to trade ~X%/2 of reserves (rough)

    # For 8.5% price move:
    needed_pct = 8.5
    trade_size_rough = total * needed_pct / 200  # rough constant product
    print(f"\n  To move spot price {needed_pct}% (constant product approx):")
    print(f"    Trade size: ~{trade_size_rough:,.0f} tokens")
    print(f"    In USD: ~${trade_size_rough:,.0f}")

    # But the TWAP is over 15 minutes
    # If the TWAP has stale observations (all 73h+ old):
    # The 15-min TWAP might use interpolation from the last known point
    # A single trade creating a new observation could shift the TWAP significantly

    # Key question: with all observations >73h old, what does observe(900) return?
    # In Uniswap V3 / Pendle V2 TWAP:
    # - observe(900) asks "what was the cumulative value 900 seconds ago?"
    # - If no observation exists at that exact time, it interpolates
    # - If the newest observation is >900s old, it uses the CURRENT value
    #   and the interpolated past value
    # - The "current value" includes any trades in THIS block

    print(f"\n  CRITICAL: All observations are >73h old")
    print(f"  When observe(900) is called:")
    print(f"  - 'now' cumulative = last_obs_cumulative + lastLnRate * (now - lastTs)")
    print(f"  - '900s ago' cumulative = same (both extrapolated from same stale point)")
    print(f"  - TWAP = (now_cum - ago_cum) / 900")
    print(f"  - = lastLnRate * 900 / 900 = lastLnRate")
    print(f"  - So TWAP = last stored implied rate (constant)")
    print(f"")
    print(f"  IF attacker trades and creates a NEW observation:")
    print(f"  - observe('now') = newObservation's cumulative")
    print(f"  - observe('900s ago') = still extrapolated from old stale obs")
    print(f"  - TWAP = weighted average of old rate and new rate")
    print(f"  - The weight depends on how long the trade has been in effect")
    print(f"  - If done at start of 15-min window: full weight")
    print(f"  - If done at end: minimal weight")

    print(f"\n  ATTACK SCENARIO (multi-block, 15 min):")
    print(f"  1. Block N: Swap large amount to distort AMM spot price")
    print(f"     - This creates ONE new observation with extreme rate")
    print(f"  2. Wait 900 seconds (~75 blocks at 12s)")
    print(f"  3. Block N+75: The 15-min TWAP now fully reflects the distorted rate")
    print(f"  4. Borrow against the inflated TWAP oracle")
    print(f"  5. Swap back (unwind AMM position)")
    print(f"  6. Walk away with excess borrows")

# ============================================================================
# 5. CHECK MARKET ACTIVITY — How often does it trade?
# ============================================================================
print(f"\n{'='*100}")
print("5. MARKET ACTIVITY CHECK")
print("=" * 100)

# Check recent blocks for Swap events on the market
# Swap event in Pendle V2:
# event Swap(address indexed caller, address indexed receiver, int256 netPtOut, int256 netSyOut, ...)
# But we can't easily query events without an event filter
# Let's check the LP token supply changes as a proxy for activity

lp_supply = u256(raw_call(MARKET, "0x18160ddd"))
if lp_supply:
    print(f"  LP supply: {lp_supply/1e18:,.2f}")

# Check the last observation more carefully
# The newest observation tells us when the last trade happened
if observations:
    newest = min(observations, key=lambda o: o['age_hours'])
    print(f"  Last observation: {newest['age_hours']:.1f}h ago")
    print(f"    = {time.strftime('%Y-%m-%d %H:%M:%S UTC', time.gmtime(newest['ts']))}")
    print(f"  Market appears INACTIVE for {newest['age_hours']:.0f}+ hours")
    print(f"  This means: TWAP is using extrapolated stale data!")

# ============================================================================
# 6. CHECK PENDLE MARKET OBSERVATIONS COUNT
# ============================================================================
print(f"\n{'='*100}")
print("6. OBSERVATION RING BUFFER — FULL SCAN")
print("=" * 100)

# The observations array is a ring buffer. Need to find its actual size.
# In Pendle V2, the cardinality determines the ring buffer size.
# Let's read the state struct which contains observationIndex and cardinality

# Try market._storage() or state()
# Pendle V2 market state is stored in a single struct
# activeBalance, totalSy, totalPt are in the struct
# observationIndex and cardinality are also in the struct

# Let's try to find these via raw slot reads
# Pendle V2 MarketStorage is at slot 0 typically
for slot in range(10):
    storage = w3.eth.get_storage_at(Web3.to_checksum_address(MARKET), slot)
    val = int.from_bytes(storage, 'big')
    if val > 0:
        # Try to decode packed struct fields
        hex_val = storage.hex()
        print(f"  slot[{slot}]: 0x{hex_val}")
        print(f"    as uint256: {val}")
        # Try to find small numbers that could be cardinality
        for byte_offset in range(0, 32, 2):
            small_val = int.from_bytes(storage[byte_offset:byte_offset+2], 'big')
            if 0 < small_val < 1000:
                pass  # print but only if meaningful
        # Try uint16 at various positions
        for i in range(0, 30, 2):
            u16 = int.from_bytes(storage[i:i+2], 'big')
            if 2 <= u16 <= 500:
                print(f"    uint16 at byte[{i}]: {u16}")

# Count actual observations
total_obs = len(observations)
print(f"\n  Total initialized observations found: {total_obs}")
if total_obs > 0:
    time_span = max(o['ts'] for o in observations) - min(o['ts'] for o in observations)
    print(f"  Time span of observations: {time_span/3600:.1f}h")
    if total_obs > 1:
        avg_interval = time_span / (total_obs - 1)
        print(f"  Average interval: {avg_interval:.0f}s ({avg_interval/60:.1f}min)")

# ============================================================================
# 7. EXACT TWAP COMPUTATION — What does the oracle actually return now?
# ============================================================================
print(f"\n{'='*100}")
print("7. TWAP COMPUTATION TRACE")
print("=" * 100)

# The feed at 0x281e1699... calls the Pendle market to get TWAP
# Let's check what it computes vs what a post-manipulation state would compute

current_twap = s256(raw_call(SRNUSD_FEED, "0x50d25bcd"))
if current_twap:
    print(f"  Current TWAP answer: {current_twap/1e18:.10f}")

# Check if there's a way to preview what the TWAP would be after a trade
# For this we'd need to simulate the trade, but we can estimate

# The feed calls PendlePtOracle.getPtToAssetRate(market, duration)
# or similar. Let's check the feed's internal calls.

# Try known Pendle oracle selectors on the feed
pendle_oracle_sels = {
    "0x3a98ef39": "getOracleRate()",
    "0x0aa33a24": "version()",
    "0xc45a0155": "factory()",
}

for sel, name in pendle_oracle_sels.items():
    result = raw_call(SRNUSD_FEED, sel)
    if isinstance(result, bytes) and len(result) >= 32:
        val = u256(result)
        if val is not None:
            if val < 2**160 and val > 2**80:
                a = addr_from(result)
                sym = decode_string(raw_call(a, "0x95d89b41"))
                print(f"  {name}: {a} ({sym})")
            else:
                print(f"  {name}: {val}")

# The feed factory
feed_factory = addr_from(raw_call(SRNUSD_FEED, "0xc45a0155"))
if feed_factory:
    print(f"\n  Feed factory: {feed_factory}")
    factory_sym = decode_string(raw_call(feed_factory, "0x06fdde03"))
    print(f"  Factory name: {factory_sym}")

# ============================================================================
# 8. MULTI-BLOCK ATTACK FEASIBILITY
# ============================================================================
print(f"\n{'='*100}")
print("8. MULTI-BLOCK ATTACK ECONOMICS (REFINED)")
print("=" * 100)

if sy_balance and pt_balance:
    sy = sy_balance / 1e18
    pt = pt_balance / 1e18

    # Current TWAP rate
    rate = current_twap / 1e18 if current_twap else 0.9825

    LLTV = 0.915
    leverage = 1 / (1 - LLTV)
    market_supply = 1_100_000  # USD

    print(f"  Current rate: {rate:.6f}")
    print(f"  LLTV: {LLTV}")
    print(f"  Max leverage: {leverage:.2f}x")
    print(f"  Market supply: ${market_supply:,.0f}")

    # For liquidation attack (push DOWN):
    # Need to push TWAP down by (1 - LLTV) * current_rate = 8.5%
    # Morpho LIF at 91.5% LLTV = 2.62%
    # Revenue = $1.1M * 2.62% = $28.8K
    lif = 1 / (1 - 0.3 * (1 - LLTV)) - 1
    liq_revenue = market_supply * lif
    print(f"\n  LIQUIDATION ATTACK (push TWAP down 8.5%):")
    print(f"    Revenue: ${liq_revenue:,.0f}")

    # For overborrow attack (push UP):
    # Need to push TWAP up enough that oracle overvalues PT
    # With 91.5% LLTV, even small overvaluation gets amplified
    # But max extraction is bounded by market supply

    # Key insight: multi-block attack
    # Step 1: Flash loan SY tokens
    # Step 2: Sell SY for PT in Pendle AMM (pushes PT price UP)
    #         This costs price impact but creates a new observation
    # Step 3: Hold for 15 minutes (no one trades because market is inactive)
    # Step 4: TWAP now reflects inflated PT price
    # Step 5: Deposit PT as collateral in Morpho, borrow against inflated price
    # Step 6: Swap back in AMM to restore price (recover most of manipulation cost)
    # Step 7: Keep excess borrows

    # The COST is the round-trip price impact:
    # Buy PT at inflated price, sell PT at (restored) lower price
    # Approximation: for constant product, round-trip cost ≈ 2 * slippage
    # Slippage for x% price impact ≈ x% of trade size

    for overval_pct in [2, 5, 10, 15, 20]:
        overval = overval_pct / 100
        # Trade needed to move spot by X%:
        # In constant product: trade ≈ reserve * (sqrt(1+X) - 1)
        # Simplified: trade ≈ reserve * X / 2
        import math
        trade_to_move = pt * (math.sqrt(1 + overval) - 1)
        # Round-trip cost: buy high, sell low
        # Cost ≈ trade_size * overval (simplified)
        roundtrip_cost = trade_to_move * overval * rate  # in USD

        # Extraction via overborrow:
        # Oracle overvalues PT by X%, so 1 PT worth (rate*(1+X)) instead of rate
        # Max initial capital = market_supply / leverage
        max_capital = market_supply / leverage
        # Phantom value = capital * leverage * overval
        phantom = max_capital * leverage * overval
        # Extraction = phantom * LLTV
        extraction = phantom * LLTV

        net = extraction - roundtrip_cost

        print(f"\n  Overvaluation {overval_pct}%:")
        print(f"    Trade to move spot: {trade_to_move:,.0f} PT (~${trade_to_move * rate:,.0f})")
        print(f"    Round-trip AMM cost: ~${roundtrip_cost:,.0f}")
        print(f"    Extraction (overborrow): ~${extraction:,.0f}")
        print(f"    Net profit: ~${net:,.0f} {'PROFITABLE' if net > 0 else 'UNPROFITABLE'}")
        if roundtrip_cost > 0:
            print(f"    ROI: {extraction/roundtrip_cost:.2f}x")

    # ============================================================================
    # 9. CAPITAL REQUIREMENTS AND FLASH LOAN AVAILABILITY
    # ============================================================================
    print(f"\n{'='*100}")
    print("9. CAPITAL AND FLASH LOAN ANALYSIS")
    print("=" * 100)

    print(f"  Attack requires:")
    print(f"    1. Flash loan for AMM manipulation (SY tokens)")
    print(f"    2. PT tokens for collateral deposit")
    print(f"    3. Hold position for 15 min (can't use flash loan)")
    print(f"")
    print(f"  CRITICAL CONSTRAINT: Multi-block = NO flash loans for capital!")
    print(f"  Attacker needs REAL capital to:")
    print(f"    a) Distort AMM (buy PT) - capital locked for 15 min")
    print(f"    b) Deposit PT as collateral - capital locked until repay")
    print(f"")
    print(f"  However: Attacker CAN:")
    print(f"    1. Use own capital to distort AMM (buy PT high)")
    print(f"    2. Wait 15 min for TWAP to settle")
    print(f"    3. Flash loan to deposit PT + borrow in same tx")
    print(f"    4. Use borrowed funds to buy MORE PT")
    print(f"    5. Loop leverage within single tx (post-TWAP settling)")
    print(f"    6. Walk away with borrowed funds > PT value")
    print(f"")
    print(f"  Alternative: two-phase attack")
    print(f"    Phase 1 (tx1): Buy PT on Pendle AMM to distort price")
    print(f"    Phase 2 (tx2, 15 min later): ")
    print(f"      - Deposit the PT bought in phase 1 as Morpho collateral")
    print(f"      - Borrow against inflated TWAP price")
    print(f"      - The PT you bought IS your collateral!")
    print(f"      - No additional capital needed for phase 2")

    # Calculate the two-phase attack:
    print(f"\n  TWO-PHASE ATTACK CALCULATION:")
    for buy_amount in [100_000, 200_000, 500_000, 1_000_000]:
        # Phase 1: Buy $X of PT on AMM
        # Price impact: buy_amount / (2 * total_liquidity * rate)
        pt_bought = buy_amount / rate  # PT tokens bought
        # Price impact using constant product approximation
        price_impact = pt_bought / (2 * total) if total > 0 else 0
        inflated_rate = rate * (1 + price_impact * 2)  # rough

        # Phase 2: Deposit pt_bought as collateral
        # Oracle says each PT is worth inflated_rate
        collateral_oracle_value = pt_bought * inflated_rate
        # Can borrow up to LLTV * collateral_oracle_value
        max_borrow = collateral_oracle_value * LLTV
        # True value of collateral = pt_bought * rate (before manipulation)
        true_collateral = pt_bought * rate
        # Profit = max_borrow - true_collateral (if walk away)
        # But: attacker paid price_impact in phase 1
        phase1_cost = buy_amount * price_impact  # slippage cost

        # The attacker paid buy_amount for the PT but got pt_bought PT tokens
        # True value of PT received = pt_bought * rate = buy_amount / rate * rate = buy_amount
        # So phase 1 cost = price_impact on the buy (paying more than fair value)
        actual_pt_cost = buy_amount  # what attacker paid
        # At inflated oracle: borrow = pt_bought * inflated_rate * LLTV
        # The attacker can then borrow and not repay
        # Loss = actual_pt_cost - max_borrow (attacker loses the PT, gains the borrow)
        net = max_borrow - actual_pt_cost

        print(f"\n    Buy ${buy_amount:,.0f} of PT:")
        print(f"      PT received: {pt_bought:,.0f}")
        print(f"      Price impact: {price_impact*100:.2f}%")
        print(f"      Inflated rate: {inflated_rate:.6f}")
        print(f"      Collateral (oracle): ${collateral_oracle_value:,.0f}")
        print(f"      Max borrow: ${max_borrow:,.0f}")
        print(f"      Capital at risk: ${actual_pt_cost:,.0f}")
        print(f"      Net (borrow - capital): ${net:,.0f} {'PROFITABLE' if net > 0 else ''}")

print("\nDone.")
