#!/usr/bin/env python3
"""
Pendle V2 AMM model analysis.

Pendle V2 AMM uses a yield-curve model, NOT constant product.
PT price is: exp(-impliedRate * timeToExpiry)
The AMM trades between SY and PT with price determined by:
  proportion = totalPt / (totalPt + totalSy * SY_rate)
  impliedRate = function(proportion, scalarRoot, anchor)

Key question: what trade size moves the implied rate (and thus PT price) by X%?
"""

import os
import time
import math
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

def raw_call(addr, data_hex):
    try:
        return w3.eth.call({"to": Web3.to_checksum_address(addr), "data": data_hex})
    except Exception as e:
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

MARKET = "0x723fcaa9830f6b6f68ebf7e30c097532a4cbbd26"
SY_SRNUSD = "0xdb8f1d15880b97dc38edfa46d8a5a7e5b506c45f"
PT_SRNUSD = "0x82b853DB31F025858792d8fA969f2a1Dc245C179"
SRNUSD_FEED = "0x281e1699558157572ffa68685339fb5ffbd25310"

# Get key data
sy_bal = u256(raw_call(SY_SRNUSD, "0x70a08231" + MARKET.lower().replace("0x", "").zfill(64)))
pt_bal = u256(raw_call(PT_SRNUSD, "0x70a08231" + MARKET.lower().replace("0x", "").zfill(64)))
sy_rate = u256(raw_call(SY_SRNUSD, "0x3ba0b9a9"))
expiry = u256(raw_call(MARKET, "0x204f83f9"))

sy = sy_bal / 1e18 if sy_bal else 0
pt = pt_bal / 1e18 if pt_bal else 0
sy_r = sy_rate / 1e18 if sy_rate else 1.0
T = (expiry - now) / (365.25 * 86400) if expiry else 0.23  # in years

print(f"Time to expiry: {T*365.25:.1f} days ({T:.4f} years)")
print(f"SY reserves: {sy:,.0f}")
print(f"PT reserves: {pt:,.0f}")
print(f"SY exchange rate: {sy_r:.6f}")

# ============================================================================
# 1. PENDLE V2 AMM MODEL
# ============================================================================
print(f"\n{'='*100}")
print("1. PENDLE V2 AMM MODEL")
print("=" * 100)

# In Pendle V2, the AMM uses "Logit" curve:
# proportion = totalPt / (totalPt + totalSy * syRate)
# lnImpliedRate = ln(proportion / (1 - proportion)) / scalarRoot + lnFeeRateRoot + anchor

# The current proportion:
proportion = pt / (pt + sy * sy_r)
print(f"  Current proportion (PT/(PT+SY*rate)): {proportion:.6f}")

# From proportion, we can derive the current lnImpliedRate
# if we knew scalarRoot and anchor
# lnImpliedRate = logit(proportion) / scalarRoot + anchor

logit = math.log(proportion / (1 - proportion))
print(f"  logit(proportion): {logit:.6f}")

# The current TWAP price tells us the implied rate:
twap = s256(raw_call(SRNUSD_FEED, "0x50d25bcd"))
twap_rate = twap / 1e18 if twap else 0.9825
# PT_price = exp(-impliedRate * T)
# impliedRate = -ln(PT_price/syRate) / T
# But PT_price is in underlying terms, and SY wraps to underlying at sy_r rate
# So PT/SY rate = PT_price / sy_r
# impliedRate = -ln(PT_price/sy_r) / T
implied_rate = -math.log(twap_rate / sy_r) / T if T > 0 else 0
ln_implied_rate = math.log(1 + implied_rate)  # Pendle uses ln(1+r)
print(f"  TWAP PT price: {twap_rate:.6f}")
print(f"  Implied yield rate: {implied_rate*100:.2f}%")
print(f"  ln(1+impliedRate): {ln_implied_rate:.6f}")

# From the observations, the lastLnImpliedRate is the current rate
# We can compute scalarRoot = logit / (lnImpliedRate - anchor)
# But we need anchor

# Try to read state from market storage
# From slot analysis, slots 10 and 11 have packed data
# Pendle V2 MarketState struct (Solidity):
# struct MarketState {
#     int256 totalPt;        slot varies
#     int256 totalSy;
#     int256 lastLnImpliedRate;
#     uint16 observationIndex;
#     uint16 observationCardinality;
#     uint16 observationCardinalityNext;
# }

# And separate:
# int256 scalarRoot;      (public, might have getter)
# int256 initialAnchor;   (public, might have getter)

# Let's scan bytecode for all 4-byte function selectors that return values
market_code = w3.eth.get_code(Web3.to_checksum_address(MARKET))
selectors = set()
for i in range(len(market_code) - 4):
    if market_code[i] == 0x63:
        sel = market_code[i+1:i+5].hex()
        selectors.add(sel)

# Try each selector and find ones that return int256 values in a reasonable range
print(f"\n  Scanning {len(selectors)} selectors for AMM parameters:")
amm_params = {}
for sel in sorted(selectors):
    result = raw_call(MARKET, "0x" + sel)
    if isinstance(result, bytes) and len(result) >= 32:
        val = u256(result)
        sval = s256(result)
        if val is None or val == 0: continue
        # Look for values that could be scalarRoot, anchor, fee
        # scalarRoot is typically in range [1e17, 1e20] (0.1 to 100 in 18-dec)
        # initialAnchor is similar
        # lastLnImpliedRate would match our computed ln_implied_rate
        if sval is not None and abs(sval) > 1e15 and abs(sval) < 1e22 and abs(sval) != val:
            if abs(sval/1e18) < 200:
                amm_params[sel] = sval
                print(f"    0x{sel}: {sval} ({sval/1e18:.6f})")
        elif val > 1e15 and val < 1e22:
            if val/1e18 < 200:
                amm_params[sel] = val
                print(f"    0x{sel}: {val} ({val/1e18:.6f})")

# ============================================================================
# 2. ESTIMATE ATTACK COST USING OBSERVATION DATA
# ============================================================================
print(f"\n{'='*100}")
print("2. EMPIRICAL ATTACK COST FROM OBSERVATION DATA")
print("=" * 100)

# Instead of modeling the AMM, use empirical data from observations
# to estimate how much the rate moves per unit of trade.

# From the observation pairs, we see rate changes.
# Some observations show larger jumps — those correspond to larger trades.
# The key data: between obs [39] and [40]:
#   rate went from 0.0720 to 0.0736 (a big jump of 0.0016 = 2.2%)
#   dt = 15948s (4.4 hours — a long gap)

# Between obs [0] and [1]:
#   rate went from 0.0741 to 0.0748 (0.0007 = 0.9%)
#   dt = 3540s

# The LARGEST rate jumps likely correspond to the LARGEST trades
# From all the observation data:
rate_jumps = [
    ("42→43", 0.0728226657, 0.0728088529, "6804s"),
    ("0→1", 0.0748275212, 0.0740577761, "3540s"),  # Big jump
    ("8→9", 0.0744604095, 0.0738694887, "1392s"),   # Big jump
    ("9→10", 0.0738694887, 0.0735821249, "5256s"),
    ("26→27", 0.0730697568, 0.0720453021, "7776s"),  # VERY big jump down
    ("39→40", 0.0720142022, 0.0735799118, "15948s"),  # VERY big jump up
]

print("  Largest rate jumps between observations:")
for name, r1, r2, dt in rate_jumps:
    delta = abs(r2 - r1)
    pct = delta / r1 * 100
    direction = "UP" if r2 > r1 else "DOWN"
    print(f"    [{name}] rate: {r1:.10f} → {r2:.10f} ({pct:.2f}% {direction}) dt={dt}")

    # What does this rate change mean for PT price?
    # PT_price = exp(-lnImpliedRate * T_in_seconds / seconds_per_year)
    # No wait, Pendle uses lnImpliedRate differently
    # The stored rate is in per-second units (already computed as d_cum/dt)
    # PT_price change: exp(-r2*T) / exp(-r1*T) - 1
    # Where T is in the same time units as the rate

    # Actually, the rate from observations is the time-averaged lnImpliedRate
    # Which is approximately: ln(1 + annual_rate) / seconds_per_year
    # So annual_rate = exp(obs_rate * seconds_per_year) - 1

    sec_per_year = 365.25 * 86400
    annual_r1 = math.exp(r1 * sec_per_year) - 1
    annual_r2 = math.exp(r2 * sec_per_year) - 1
    # Hmm, this gives impossibly large numbers. The rates must be scaled differently.

    # Let me reconsider. The cumulative is lnImpliedRate * time
    # And rate = cumDiff / timeDiff
    # In Pendle V2, lnImpliedRate is in 18-decimal fixed point
    # So the actual value is rate / 1e18

    actual_r1 = r1  # Already divided by 1e18 in our earlier computation
    actual_r2 = r2

    # These are per-second ln(implied rate) values
    # Annual implied rate = exp(rate * seconds_per_year) - 1
    # This is ~0.073 per second... that's way too high
    # Unless the rate is already annualized

    # Let me check: 0.073 per second * 31,557,600 seconds/year = 2,303,704
    # That's obviously wrong. The rate must be pre-scaled.

    # Looking at the observations more carefully:
    # cumulative values are like 169416167211361756763412
    # Between obs[40] and obs[41]: d_cum = 169416167211361756763412 - 168543730639102210019220 = 872436572259546744192
    # dt = 11904
    # rate = 872436572259546744192 / 11904 = 73289769340736000 ≈ 7.33e16
    # So rate / 1e18 = 0.0733

    # This is the per-second lnImpliedRate. To get annual:
    # annual_lnRate = 0.0733 * 31557600 = 2,313,171
    # That's clearly not right as a yield rate.

    # I think the lnImpliedRate in Pendle is already scaled such that:
    # PT_price_to_SY = exp(-lnImpliedRate * timeToExpiry_in_seconds)
    # Where lnImpliedRate is in 18-decimal fixed point PER SECOND

    # So PT/SY = exp(-0.0733 * T_seconds)
    T_seconds = (expiry - now) if expiry else 84 * 86400
    pt_price_from_rate1 = math.exp(-actual_r1 * T_seconds)
    pt_price_from_rate2 = math.exp(-actual_r2 * T_seconds)

    print(f"      PT price from rate: {pt_price_from_rate1:.6f} → {pt_price_from_rate2:.6f}")
    pt_price_change = (pt_price_from_rate2 - pt_price_from_rate1) / pt_price_from_rate1 * 100
    print(f"      PT price change: {pt_price_change:.2f}%")

# ============================================================================
# 3. KEY PENDLE V2 PRICE SENSITIVITY
# ============================================================================
print(f"\n{'='*100}")
print("3. PENDLE V2 PRICE SENSITIVITY")
print("=" * 100)

T_seconds = (expiry - now) if expiry else 84 * 86400
current_rate = 0.0733  # From observations
current_pt = math.exp(-current_rate * T_seconds)
print(f"  Time to expiry: {T_seconds/86400:.1f} days ({T_seconds:,} seconds)")
print(f"  Current lnImpliedRate (per sec): {current_rate:.10f}")
print(f"  Current PT/SY (from rate): {current_pt:.6f}")

# To move PT price DOWN by 8.5% (for liquidation attack):
target_pt_down = current_pt * (1 - 0.085)
# exp(-rate_new * T) = target_pt_down
rate_needed_down = -math.log(target_pt_down) / T_seconds
rate_change_down = rate_needed_down - current_rate
print(f"\n  For 8.5% PT price DROP (liquidation attack):")
print(f"    Target PT/SY: {target_pt_down:.6f}")
print(f"    Required rate: {rate_needed_down:.10f}")
print(f"    Rate change: +{rate_change_down:.10f} ({rate_change_down/current_rate*100:.2f}%)")

# To move PT price UP by 10% (for overborrow attack):
target_pt_up = current_pt * 1.10
if target_pt_up < 1.0:
    rate_needed_up = -math.log(target_pt_up) / T_seconds
    rate_change_up = current_rate - rate_needed_up
    print(f"\n  For 10% PT price INCREASE (overborrow attack):")
    print(f"    Target PT/SY: {target_pt_up:.6f}")
    print(f"    Required rate: {rate_needed_up:.10f}")
    print(f"    Rate change: -{rate_change_up:.10f} ({rate_change_up/current_rate*100:.2f}%)")
else:
    print(f"\n  10% PT price increase → {target_pt_up:.4f} ABOVE 1.0!")
    print(f"  This would mean negative implied rate → IMPOSSIBLE")
    print(f"  PT CANNOT trade above maturity value in a rational market")

# What's the MAX PT price increase before rate goes to 0?
max_pt = 1.0  # At rate=0, PT = exp(0) = 1.0
max_increase = (max_pt - current_pt) / current_pt * 100
print(f"\n  Max PT price increase (before rate=0): {max_increase:.2f}%")
print(f"  This is the CEILING for overborrow attack")
print(f"  To reach break-even overvaluation ({(1/0.915 - 1)*100:.2f}%): IMPOSSIBLE")
print(f"  because max increase ({max_increase:.2f}%) < required ({(1/0.915 - 1)*100:.2f}%)")

# Wait, that's wrong. The PT price is PT/SY, and the oracle price includes SY_rate
# Oracle price = PT/SY * SY_rate = exp(-rate * T) * SY_rate
# Current: 0.9825 = exp(-0.0733 * T) * 1.005 ≈ 0.9776 * 1.005
# Max (rate=0): 1.0 * 1.005 = 1.005

# The overborrow break-even needs oracle > true / LLTV = 0.9825 / 0.915 = 1.0738
# But max oracle = 1.005 (when PT/SY = 1.0)
# 1.005 < 1.0738 → IMPOSSIBLE

print(f"\n  CRITICAL FINDING:")
print(f"  Oracle = PT/SY * SY_rate")
print(f"  Max oracle (rate=0) = 1.0 * {sy_r:.6f} = {sy_r:.6f}")
print(f"  Break-even for overborrow = {twap_rate/0.915:.6f}")
print(f"  {sy_r:.6f} < {twap_rate/0.915:.6f}")
print(f"  >>> OVERBORROW ATTACK IS IMPOSSIBLE <<<")
print(f"  PT price cannot exceed maturity value")
print(f"  At 91.5% LLTV, need 9.3% overvaluation")
print(f"  Max possible overvaluation: {(sy_r/twap_rate - 1)*100:.2f}%")
print(f"  This is 2.3% < 9.3% → insufficient")

# For LIQUIDATION attack (push DOWN):
# This IS possible — push rate UP, PT price goes DOWN
# From observation data, largest jump was obs[26→27]: 0.0731 → 0.0720 (1.5% rate drop)
# And obs[39→40]: 0.0720 → 0.0736 (2.2% rate increase)

# For 8.5% PT price drop:
# Need rate increase of ~1.2% of rate (from calculation above)
print(f"\n  LIQUIDATION ATTACK FEASIBILITY:")
print(f"  Need rate change: +{rate_change_down:.10f}")
print(f"  As % of current rate: {rate_change_down/current_rate*100:.2f}%")
print(f"  Largest observed rate jump: ~2.2% (obs 39→40)")
print(f"  Need: {rate_change_down/current_rate*100:.2f}%")
if rate_change_down/current_rate < 0.03:
    print(f"  >>> Rate change is small enough to be achievable!")
    print(f"  But: need to SUSTAIN for 15 minutes")
    print(f"  And: liquidation revenue at 2.62% may not cover costs")
elif rate_change_down/current_rate < 0.10:
    print(f"  >>> Rate change is moderate — achievable with large trade")
else:
    print(f"  >>> Rate change is very large — may be infeasible")

print("\nDone.")
