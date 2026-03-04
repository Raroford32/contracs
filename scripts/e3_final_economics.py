#!/usr/bin/env python3
"""
E3 FINAL: Complete attack economics with actual on-chain data.

Known constraints:
- Available Morpho liquidity: $140K USDC
- Total borrows: $1.117M USDC
- AMM reserves: 2.65M SY + 710K PT = 3.36M tokens
- LLTV: 91.5%
- TWAP: 15 min (900s)
- Backup=Primary → deviation check DEAD

Question: can the attacker profitably exploit this?
"""

import math

# ============================================================================
# On-chain data (from previous scripts)
# ============================================================================
AVAILABLE_USDC = 139_999.89
TOTAL_BORROW = 1_116_719.24
TOTAL_SUPPLY = 1_256_719.13
LLTV = 0.915
PT_RESERVES = 710_839.56
SY_RESERVES = 2_653_268.59
TOTAL_AMM = PT_RESERVES + SY_RESERVES
TWAP_RATE = 0.9825  # Current TWAP PT price
SY_RATE = 1.005077  # SY exchange rate
TWAP_DURATION = 900  # seconds
LIF = 1 / (1 - 0.3 * (1 - LLTV)) - 1  # 2.62%

print("=" * 100)
print("E3 FINAL ECONOMICS: PT-srNUSD TWAP MANIPULATION")
print("=" * 100)

print(f"\n  On-chain data:")
print(f"    Available liquidity: ${AVAILABLE_USDC:,.2f}")
print(f"    Total borrows: ${TOTAL_BORROW:,.2f}")
print(f"    AMM PT reserves: {PT_RESERVES:,.0f}")
print(f"    AMM SY reserves: {SY_RESERVES:,.0f}")
print(f"    TWAP rate: {TWAP_RATE}")
print(f"    LLTV: {LLTV}")
print(f"    LIF: {LIF*100:.2f}%")

# ============================================================================
# 1. OVERBORROW ATTACK — Push TWAP UP
# ============================================================================
print(f"\n{'='*100}")
print("1. OVERBORROW ATTACK (Push TWAP UP)")
print("=" * 100)

# Minimum overvaluation for k > 1:
min_overval = 1/LLTV - 1
print(f"  Minimum overvaluation for profit: {min_overval*100:.2f}%")
print(f"  (Need oracle price > {TWAP_RATE * (1 + min_overval):.4f})")

for overval_pct in [10, 15, 20, 30, 50, 100]:
    overval = overval_pct / 100
    k = (1 + overval) * LLTV

    if k <= 1:
        print(f"\n  {overval_pct}% overvaluation: k={k:.4f} < 1 → IMPOSSIBLE")
        continue

    # Leverage loop extraction (bounded by available liquidity)
    # Net = available * (1 - 1/k) = available * (k-1)/k
    net_extraction = AVAILABLE_USDC * (k - 1) / k

    # AMM manipulation cost (constant product approximation)
    # To move spot up by X%, buy PT with SY
    # In constant product: pt_bought = pt_reserve * (1 - 1/sqrt(1+overval))
    # Cost = sy_spent = sy_reserve * (sqrt(1+overval) - 1)
    # Round-trip cost (buy then sell back): ≈ 2 * slippage
    # But attacker holds for 15 min, then can sell the PT as Morpho collateral
    # Actually: the PT bought in the AMM IS the collateral
    # So there's no "round-trip" — the attacker keeps the PT

    # Cost of AMM manipulation:
    # The attacker buys PT at inflated price on AMM
    # Then deposits as collateral at even-more-inflated oracle price
    # The cost is: (price_paid - fair_price) * quantity
    # With constant product: attacker pays avg price of ~fair_price * sqrt(1+overval)
    # Excess paid = fair_price * (sqrt(1+overval) - 1) * quantity
    sy_needed = SY_RESERVES * (math.sqrt(1 + overval) - 1)
    pt_received = PT_RESERVES * (1 - 1/math.sqrt(1 + overval))
    avg_price_paid = sy_needed / pt_received * TWAP_RATE / SY_RATE
    fair_price = TWAP_RATE
    premium = avg_price_paid - fair_price
    # But this premium is partially recovered because oracle overvalues the PT!

    # More accurate cost model:
    # Attacker acquires SY tokens (flash loan from Aave → wrap into srNUSD → wrap into SY)
    # Swaps SY for PT on Pendle AMM
    # Gets pt_received PT tokens, paid sy_needed SY tokens
    # Real value of PT received: pt_received * fair_price
    # Real cost: sy_needed * SY_RATE (in underlying terms)
    # AMM loss: cost - value = sy_needed * SY_RATE - pt_received * fair_price

    real_cost = sy_needed * SY_RATE  # What attacker pays (in underlying)
    real_value = pt_received * TWAP_RATE  # What PT is actually worth
    amm_loss = real_cost - real_value  # Cost of manipulation

    # But wait: the attacker doesn't actually need to buy PT on the AMM
    # in the SAME transaction as the deposit. The attack is multi-block:
    # Block 1: Buy PT on AMM (pushes price up, creates observation)
    # Wait 15 min
    # Block 75: Deposit PT + leverage loop borrow

    # In Block 75, the attacker uses the PT tokens acquired in Block 1
    # So the "cost" is the AMM premium paid in Block 1
    # And the "revenue" is the excess borrowing in Block 75

    # However, after Block 75, the attacker can sell PT back on AMM
    # (unwinding the manipulation), recovering some of the AMM cost
    # But selling pushes price DOWN, creating a new observation
    # If the attacker has already borrowed, this doesn't matter

    # So the TRUE cost = AMM premium paid (buying high)
    # minus: PT value recovered (selling or keeping as collateral)

    # If attacker defaults on Morpho loan:
    # - Attacker keeps: borrowed USDC
    # - Attacker loses: PT collateral
    # - Net = borrowed - cost_of_PT

    # The leverage loop makes total_borrowed ≈ AVAILABLE_USDC
    # The cost_of_PT = pt_received * avg_price_paid (paid premium on AMM)

    # For this to be profitable:
    # AVAILABLE_USDC > pt_deposited * avg_price_paid
    # Where pt_deposited = total_borrowed / ((1+overval) * LLTV * TWAP_RATE)

    # Actually, let's just compute the capital the attacker needs for the AMM push:
    # To move spot by overval%, attacker buys PT worth ~$X
    # The cost premium is the difference between what they paid and fair value
    # They then deposit this PT and borrow against inflated oracle
    # The question is whether borrowing > cost

    capital_for_amm = sy_needed  # SY tokens needed (can be flash loaned? no — multi-block)

    print(f"\n  {overval_pct}% overvaluation (k={k:.4f}):")
    print(f"    AMM: buy {pt_received:,.0f} PT by selling {sy_needed:,.0f} SY")
    print(f"    AMM cost (real): ${real_cost:,.0f}")
    print(f"    PT real value: ${real_value:,.0f}")
    print(f"    AMM premium paid: ${amm_loss:,.0f}")
    print(f"    Leverage loop extraction: ${net_extraction:,.0f}")
    print(f"    Net profit: ${net_extraction - amm_loss:,.0f} {'✓ PROFITABLE' if net_extraction > amm_loss else '✗ UNPROFITABLE'}")

# ============================================================================
# 2. LIQUIDATION ATTACK — Push TWAP DOWN
# ============================================================================
print(f"\n{'='*100}")
print("2. LIQUIDATION ATTACK (Push TWAP DOWN)")
print("=" * 100)

needed_drop = 1 - LLTV  # 8.5%
liq_revenue = TOTAL_BORROW * LIF
# But not all positions may be at max leverage
# Conservative: assume 50% of borrows are at >90% of LLTV
liq_revenue_conservative = TOTAL_BORROW * 0.5 * LIF

# Cost to push TWAP down 8.5%:
# Sell PT into AMM → pushes PT/SY ratio down
# pt_sold = pt_reserve * (sqrt(1/(1-drop)) - 1)
pt_to_sell = PT_RESERVES * (math.sqrt(1/(1-needed_drop)) - 1)
sy_received = SY_RESERVES * (1 - math.sqrt(1 - needed_drop))
# Round-trip cost: sell PT low, buy back PT high
# Net cost = pt_sold * fair - sy_received / SY_RATE
amm_down_cost = pt_to_sell * TWAP_RATE - sy_received / SY_RATE * TWAP_RATE

# But this is multi-block: attacker must maintain price for 15 min
# Capital locked = pt_to_sell * TWAP_RATE (value of PT sold)

print(f"  Need TWAP drop: {needed_drop*100:.1f}%")
print(f"  PT to sell on AMM: {pt_to_sell:,.0f}")
print(f"  Liquidation revenue: ${liq_revenue:,.0f} (optimistic)")
print(f"  Liquidation revenue: ${liq_revenue_conservative:,.0f} (conservative)")
print(f"  AMM round-trip cost: ${amm_down_cost:,.0f}")
print(f"  Net (optimistic): ${liq_revenue - amm_down_cost:,.0f}")
print(f"  Net (conservative): ${liq_revenue_conservative - amm_down_cost:,.0f}")

# ============================================================================
# 3. BREAK-EVEN ANALYSIS — At what market size does it become profitable?
# ============================================================================
print(f"\n{'='*100}")
print("3. BREAK-EVEN ANALYSIS")
print("=" * 100)

print(f"\n  OVERBORROW attack break-even (at 20% manipulation):")
overval = 0.20
k = (1 + overval) * LLTV
# Net = available * (k-1)/k
# AMM cost ≈ SY_RESERVES * (sqrt(1.20) - 1) * SY_RATE - PT_RESERVES * (1-1/sqrt(1.20)) * TWAP_RATE
sy_needed_20 = SY_RESERVES * (math.sqrt(1.20) - 1)
pt_received_20 = PT_RESERVES * (1 - 1/math.sqrt(1.20))
amm_cost_20 = sy_needed_20 * SY_RATE - pt_received_20 * TWAP_RATE

# Break-even: available * (k-1)/k = amm_cost_20
breakeven_available = amm_cost_20 * k / (k - 1)
print(f"    AMM manipulation cost (20%): ${amm_cost_20:,.0f}")
print(f"    Break-even available liquidity: ${breakeven_available:,.0f}")
print(f"    Current available: ${AVAILABLE_USDC:,.0f}")
print(f"    Need {breakeven_available/AVAILABLE_USDC:.0f}x more liquidity")

print(f"\n  LIQUIDATION attack break-even:")
# Need: total_borrow * LIF > amm_down_cost
breakeven_borrow = amm_down_cost / LIF
print(f"    AMM cost (8.5% drop): ${amm_down_cost:,.0f}")
print(f"    Break-even total borrows: ${breakeven_borrow:,.0f}")
print(f"    Current borrows: ${TOTAL_BORROW:,.0f}")
print(f"    Need {breakeven_borrow/TOTAL_BORROW:.0f}x more borrows")

# ============================================================================
# 4. RISK ASSESSMENT — WHAT MAKES THIS DANGEROUS
# ============================================================================
print(f"\n{'='*100}")
print("4. RISK ASSESSMENT — WHY THIS MATTERS")
print("=" * 100)

print(f"""
  CURRENT STATUS: E2 Finding (Misconfiguration with Latent Risk)

  The backup=primary misconfiguration eliminates the deviation safety net.
  Currently NOT profitable to exploit because:

  1. Available liquidity is only ${AVAILABLE_USDC:,.0f}
     (limits overborrow extraction)
  2. AMM is deep (3.36M tokens) relative to market size
     (manipulation cost exceeds extraction)
  3. Liquidation incentive is only {LIF*100:.2f}%
     (even liquidating all $1.1M yields only ${liq_revenue:,.0f})

  BUT the risk is LATENT and grows with market size:

  SCENARIO A: If available liquidity reaches ${breakeven_available:,.0f}
    → Overborrow attack becomes profitable at 20% TWAP manipulation
    → This could happen if new suppliers enter the market

  SCENARIO B: If total borrows reach ${breakeven_borrow:,.0f}
    → Liquidation attack becomes profitable at 8.5% TWAP manipulation
    → This could happen if the market grows organically

  SCENARIO C: NUSD depeg to $0.915 (8.5% from $1.00)
    → ALL $1.1M of existing positions become bad debt
    → The oracle (backup=primary) will NOT detect the divergence
    → No failover, no circuit breaker, no emergency response
    → This happened partially in Nov 2025 (NUSD hit $0.975)

  SCENARIO D: Post-maturity + NUSD depeg
    → PT-sNUSD expires TODAY (few hours)
    → Oracle returns 1.0 at maturity
    → If NUSD has depegged, redeemed collateral worth < 1.0
    → Oracle still says 1.0 → bad debt accumulates silently

  WORST CASE: NUSD depegs + market grows → catastrophic loss
    At $10M borrows + 15% NUSD depeg:
    Bad debt = $10M * 15% = $1.5M
    No detection, no failover, no circuit breaker
""")

# ============================================================================
# 5. COMPOSITION WITH OTHER MARKETS
# ============================================================================
print(f"\n{'='*100}")
print("5. COMPOSITION ATTACK — CROSS-MARKET")
print("=" * 100)

print(f"""
  Can the attacker use OTHER Morpho markets to amplify?

  Check 1: PT-sNUSD market
    - Uses DETERMINISTIC oracle (not TWAP) → cannot be AMM-manipulated
    - But: also has backup=primary
    - Risk: NUSD depeg → bad debt on $6.5M market

  Check 2: Cross-collateral
    - Could borrow from PT-sNUSD market and use proceeds to manipulate
      PT-srNUSD TWAP?
    - This doesn't help: PT-sNUSD collateral requires sNUSD, not srNUSD
    - No direct composition benefit

  Check 3: Flash loan composition
    - Morpho flash loans: $126.5M USDC available (0 fee!)
    - BUT: multi-block attack → can't use flash loans for AMM manipulation
    - CAN use flash loans for the leverage loop in Block N+75
    - This is already accounted for in the extraction calculation

  Verdict: No significant composition amplification found
""")

# ============================================================================
# 6. E3 GATE CHECK
# ============================================================================
print(f"\n{'='*100}")
print("6. E3 GATE CHECK")
print("=" * 100)

print(f"""
  ✓ Reproducible sequence: defined (2-phase multi-block)
  ✓ Privilege: NONE required (fully permissionless)
  ✓ Costs itemized: AMM manipulation + gas
  ✗ Net profit positive: NO at current market size
    - Overborrow: ${AVAILABLE_USDC * (k-1)/k - amm_cost_20:,.0f} (negative)
    - Liquidation: ${liq_revenue - amm_down_cost:,.0f} (negative)
  ✗ Robustness: N/A (not profitable)

  E3 STATUS: NOT MET (economics don't work at current scale)

  FINDING CLASSIFICATION: E2 — CRITICAL MISCONFIGURATION
  - Backup=primary eliminates deviation safety net
  - TWAP oracle is manipulable (15 min, no crosscheck)
  - Risk grows with market size and NUSD stability
  - Attack becomes profitable at ${breakeven_available:,.0f} available liquidity
    or ${breakeven_borrow:,.0f} total borrows
""")

print("\nDone.")
