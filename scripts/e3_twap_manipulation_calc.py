#!/usr/bin/env python3
"""
E3 DISCRIMINATOR: Calculate exact TWAP manipulation economics for PT-srNUSD.

Key parameters:
- LLTV: 91.5% → leverage ratio: 1/(1-0.915) = 11.76x
- TWAP: 15 min (900 seconds)
- Backup=primary → deviation check dead
- srNUSD market: PLP-srNUSD-28MAY2026

Steps:
1. Get AMM reserves by reading token balances directly
2. Calculate TWAP manipulation cost (Pendle V2 AMM mechanics)
3. Calculate extraction via leverage loop
4. Compare: is extraction > manipulation cost?
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
        return f"REVERT: {str(e)[:120]}"

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
ERC20_BALANCE_OF = "0x70a08231"  # balanceOf(address)

# ============================================================================
# 1. Get AMM reserves by reading token balances in the market
# ============================================================================
print("=" * 100)
print("1. AMM RESERVES — GET TOKEN BALANCES IN PENDLE MARKET")
print("=" * 100)

MARKET = "0x723fcaa9830f6b6f68ebf7e30c097532a4cbbd26"
SY_SRNUSD = "0xdb8f1d15880b97dc38edfa46d8a5a7e5b506c45f"

# From readTokens: SY=0xdb8f..., need PT address
# Market selector scan showed: 0x2c8ce6bc => SY
# Let me find PT by scanning tokens
# The PT for srNUSD-28MAY2026 should be the collateral token in the Morpho market
PT_SRNUSD = "0x82b853DB31F025858792d8fA969f2a1Dc245C179"  # from Morpho API

# Check balances in the market
market_addr_padded = MARKET.lower().replace("0x", "").zfill(64)

# SY balance in market
sy_bal_data = raw_call(SY_SRNUSD, ERC20_BALANCE_OF + market_addr_padded)
sy_balance = u256(sy_bal_data)
print(f"  SY-srNUSD balance in market: {sy_balance}")
if sy_balance:
    print(f"    = {sy_balance / 1e18:,.4f} SY tokens")

# PT balance in market
pt_bal_data = raw_call(PT_SRNUSD, ERC20_BALANCE_OF + market_addr_padded)
pt_balance = u256(pt_bal_data)
print(f"  PT-srNUSD balance in market: {pt_balance}")
if pt_balance:
    print(f"    = {pt_balance / 1e18:,.4f} PT tokens")

# PT total supply
pt_supply = u256(raw_call(PT_SRNUSD, "0x18160ddd"))
print(f"  PT-srNUSD totalSupply: {pt_supply}")
if pt_supply:
    print(f"    = {pt_supply / 1e18:,.4f}")

# SY exchange rate
sy_rate = u256(raw_call(SY_SRNUSD, "0x3ba0b9a9"))
if sy_rate:
    print(f"  SY exchange rate: {sy_rate / 1e18:.8f}")

# Try to get the Pendle oracle state using known Pendle router
# Common Pendle V2 router on mainnet
PENDLE_ROUTER = "0x888888888889758F76e7103c6CbF23ABbF58F946"
PENDLE_ROUTER_V4 = "0x00000000005BBB0EF59571E58418F9a4357b68A0"

# Try readState with both routers
for router_name, router_addr in [("RouterV3", PENDLE_ROUTER), ("RouterV4", PENDLE_ROUTER_V4)]:
    padded = router_addr.lower().replace("0x", "").zfill(64)
    data = "0x68c8fbb3" + padded  # readState(address)
    result = raw_call(MARKET, data)
    if isinstance(result, bytes) and len(result) >= 192:
        totalPt = u256(result, 0)
        totalSy = u256(result, 32)
        lastLnImpliedRate = u256(result, 64)
        observationIndex = u256(result, 96)
        observationCardinality = u256(result, 128)
        observationCardinalityNext = u256(result, 160)
        print(f"\n  readState({router_name}):")
        print(f"    totalPt: {totalPt / 1e18:,.4f}")
        print(f"    totalSy: {totalSy / 1e18:,.4f}")
        print(f"    lastLnImpliedRate: {lastLnImpliedRate}")
        print(f"    observationIndex: {observationIndex}")
        print(f"    >>> observationCardinality: {observationCardinality}")
        print(f"    >>> observationCardinalityNext: {observationCardinalityNext}")

        if observationCardinality:
            blocks_per_observation = 900 / observationCardinality  # rough
            print(f"    Blocks per observation: ~{blocks_per_observation:.1f}")
            if observationCardinality <= 10:
                print(f"    !!! LOW CARDINALITY — few TWAP samples!")
            else:
                print(f"    Moderate cardinality")
    else:
        print(f"\n  readState({router_name}): {result[:60] if isinstance(result, str) else 'empty'}")

# ============================================================================
# 2. Try to read observations directly
# ============================================================================
print(f"\n{'='*100}")
print("2. TWAP OBSERVATIONS — CHECK FRESHNESS AND DENSITY")
print("=" * 100)

# Pendle V2 market.observations(uint256 index)
# Returns (uint32 blockTimestamp, uint216 lnImpliedRateCumulative, bool initialized)
for idx in range(5):
    padded_idx = hex(idx)[2:].zfill(64)
    data = "0x252c09d7" + padded_idx  # observations(uint256)
    result = raw_call(MARKET, data)
    if isinstance(result, bytes) and len(result) >= 96:
        ts = u256(result, 0) & 0xFFFFFFFF  # uint32
        lnCumulative = u256(result, 32)
        initialized = u256(result, 64)
        if ts > 0:
            age = (now - ts) / 3600
            print(f"  observation[{idx}]: ts={time.strftime('%H:%M:%S', time.gmtime(ts))} ({age:.1f}h ago), init={bool(initialized)}")
        else:
            print(f"  observation[{idx}]: empty (ts=0)")

# ============================================================================
# 3. MANIPULATION ECONOMICS
# ============================================================================
print(f"\n{'='*100}")
print("3. TWAP MANIPULATION ECONOMICS")
print("=" * 100)

# Current oracle price for srNUSD
META_SRNUSD = "0x0D07087b26b28995a66050f5bb7197D439221DE3"
current_price = u256(raw_call(META_SRNUSD, "0xa035b1fe"))
if current_price:
    print(f"  Current oracle price: {current_price / 1e24:.8f}")

# The TWAP feed for srNUSD
SRNUSD_FEED = "0x281e1699558157572ffa68685339fb5ffbd25310"
lrd = raw_call(SRNUSD_FEED, "0xfeaf968c")
if isinstance(lrd, bytes):
    feed_answer = u256(lrd, 32)
    print(f"  Feed answer (TWAP): {feed_answer}")
    if feed_answer:
        print(f"    = {feed_answer / 1e18:.8f}")

# Morpho market data
LLTV = 0.915  # 91.5%
leverage_ratio = 1 / (1 - LLTV)
print(f"\n  LLTV: {LLTV*100:.1f}%")
print(f"  Max leverage ratio: {leverage_ratio:.2f}x")

current_rate = feed_answer / 1e18 if feed_answer else 0.9825
print(f"  Current PT/underlying rate: {current_rate:.6f}")

# For profitable attack: oracle_price * LLTV > true_price
# oracle_price > true_price / LLTV
target_rate = current_rate / LLTV
print(f"  Break-even oracle rate: {target_rate:.6f}")
print(f"  Required TWAP manipulation: {(target_rate / current_rate - 1) * 100:.2f}% upward")

# With leverage loop amplification:
# Attacker deposits $C of PT, borrows $C * LLTV of USDC
# Buys more PT with USDC, deposits again, etc.
# Total exposure = C / (1 - LLTV) = C * leverage_ratio
# Total borrowed = C * LLTV / (1 - LLTV)

# If oracle overvalues by X%:
# Each dollar of "phantom" collateral value = X% * oracle_value
# Total phantom value = X% * C * leverage_ratio
# Extraction = phantom_value * LLTV = X% * C * leverage_ratio * LLTV

for overval_pct in [1, 2, 3, 5, 10]:
    overval = overval_pct / 100
    # Per $100K of initial capital:
    initial = 100_000
    total_collateral_oracle = initial * leverage_ratio
    total_borrowed = initial * LLTV / (1 - LLTV)
    phantom_value = total_collateral_oracle * overval
    extraction = phantom_value * LLTV
    # But extraction is bounded by market supply
    print(f"\n  Overvaluation {overval_pct}% (oracle at {current_rate * (1 + overval):.4f}):")
    print(f"    Initial capital: ${initial:,.0f}")
    print(f"    Total collateral (oracle): ${total_collateral_oracle:,.0f}")
    print(f"    Total borrowed: ${total_borrowed:,.0f}")
    print(f"    Phantom value: ${phantom_value:,.0f}")
    print(f"    Potential extraction: ${extraction:,.0f}")

# The constraint: the srNUSD market has only ~$1.1M of SUPPLY
# So the max borrowable is $1.1M
# Working backwards: if market supply = $1.1M and leverage = 11.76x
# Max initial capital = $1.1M / 11.76 = $93.5K
# But then at 2% overvaluation:
# Extraction = $93.5K * 11.76 * 0.02 * 0.915 = $20.1K
# At 5% overvaluation:
# Extraction = $93.5K * 11.76 * 0.05 * 0.915 = $50.3K

print(f"\n  Market supply constraint: ~$1.1M")
print(f"  Max leveraged capital: ${1_100_000 / leverage_ratio:,.0f}")

# Check if any other markets use PT-srNUSD as collateral
# or if there's more supply available

# ============================================================================
# 4. ALTERNATIVE: Liquidation attack (push TWAP DOWN)
# ============================================================================
print(f"\n{'='*100}")
print("4. ALTERNATIVE — LIQUIDATION ATTACK (PUSH TWAP DOWN)")
print("=" * 100)

print(f"  Current positions in PT-srNUSD market: ~$1.1M borrow")
print(f"  LLTV: 91.5% — positions very close to liquidation threshold")
print(f"  If TWAP is pushed DOWN by {(1 - LLTV) * 100:.1f}%:")
print(f"    Oracle would show {current_rate * LLTV:.4f} instead of {current_rate:.4f}")
print(f"    Existing positions become liquidatable!")
print(f"    Liquidator buys discounted collateral")
print(f"    Profit = liquidation incentive (typically 5-15%)")
print(f"    On $1.1M of positions → potential ${1_100_000 * 0.05:,.0f} to ${1_100_000 * 0.15:,.0f}")
print(f"\n  But: deviation check is dead → even DOWNWARD manipulation undetected!")
print(f"  Need: sustained TWAP move of ~8.5% for 15 minutes")

# ============================================================================
# 5. Check Morpho Blue liquidation incentive
# ============================================================================
print(f"\n{'='*100}")
print("5. MORPHO BLUE LIQUIDATION MECHANICS")
print("=" * 100)

# Morpho Blue uses the LLTV-based liquidation
# The liquidation incentive factor (LIF) in Morpho Blue:
# For repaid/seized, the seized collateral is worth (1 + liquidationIncentive) * repaid
# liquidationIncentive = min(maxLIF, 1/(1-cursor * (1-LLTV)) - 1)
# Where cursor is 0.3 by default
# For LLTV = 0.915: 1/(1 - 0.3 * (1-0.915)) - 1 = 1/(1-0.0255) - 1 = 0.02617 = 2.6%

cursor = 0.3
lif = 1 / (1 - cursor * (1 - LLTV)) - 1
max_lif = 0.15  # 15%
actual_lif = min(max_lif, lif)
print(f"  LLTV: {LLTV}")
print(f"  Cursor: {cursor}")
print(f"  Liquidation incentive: {actual_lif * 100:.2f}%")
print(f"  Per $1M liquidated: ${1_000_000 * actual_lif:,.0f} incentive")

# The liquidation attack sequence:
# 1. Flash loan SY/srNUSD tokens
# 2. Swap in Pendle AMM to dump PT price (or add SY liquidity)
# 3. Maintain for 15 minutes (multi-block)
# 4. TWAP drops → positions become liquidatable
# 5. Liquidate positions → earn 2.6% incentive
# 6. Unwind the AMM position
# 7. Return flash loan

# Cost: price impact from dumping + impermanent loss + opportunity cost for 15 min
# Revenue: 2.6% of liquidated amount

print(f"\n  LIQUIDATION ATTACK SEQUENCE:")
print(f"  1. Acquire SY-srNUSD (or srNUSD tokens)")
print(f"  2. Dump PT in Pendle AMM → push spot price down 8.5%+")
print(f"  3. Maintain distorted price for 15 min TWAP window")
print(f"  4. TWAP drops → positions become liquidatable")
print(f"  5. Liquidate: seize PT collateral at 2.6% discount")
print(f"  6. Sell seized PT on market")
print(f"  7. Unwind AMM position")
print(f"\n  Revenue: ${1_100_000 * actual_lif:,.0f} from liquidation incentive")
print(f"  Cost: AMM manipulation (depends on liquidity depth)")
print(f"  Net: DEPENDS ON AMM DEPTH — need reserves data")

if sy_balance and pt_balance:
    total_amm = (sy_balance + pt_balance) / 1e18
    print(f"\n  AMM total tokens: {total_amm:,.0f}")
    # Rough cost to move price 8.5%: ~4.25% of reserves (constant product approx)
    cost_estimate = total_amm * 0.0425
    print(f"  Rough cost to move spot 8.5%: ~{cost_estimate:,.0f} tokens")
    print(f"  Revenue: ~{1_100_000 * actual_lif:,.0f} USDC")
    if cost_estimate > 0:
        roi = (1_100_000 * actual_lif) / cost_estimate
        print(f"  Rough ROI ratio: {roi:.2f}x (needs to be > 1)")

print("\nDone.")
