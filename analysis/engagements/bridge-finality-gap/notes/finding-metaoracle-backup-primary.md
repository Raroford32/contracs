# Finding: MetaOracleDeviationTimelock Backup=Primary Misconfiguration

## Status: E2 (Confirmed misconfiguration with real risk, not yet E3 permissionless drain)

## Summary

Two Morpho Blue markets on Ethereum mainnet use `MetaOracleDeviationTimelock` (Steakhouse Financial) oracle wrappers where **the backup oracle points to the exact same contract as the primary oracle**. This defeats the MetaOracle's deviation detection mechanism entirely — the system compares an oracle against itself, finding 0% deviation always.

**Total exposed**: ~$7.7M in borrow across two markets.

## Affected Markets

| Market | Borrow | LLTV | Oracle | Primary | Backup | Backup=Primary? |
|---|---|---|---|---|---|---|
| PT-sNUSD-5MAR2026/USDC | $6.5M | 77% | `0xe846...` | `0xd25a...` | OracleRouter→`0xd25a...` | **YES** |
| PT-srNUSD-28MAY2026/USDC | $1.1M | 91.5% | `0x0D07...` | `0x2b28...` | OracleRouter→`0x2b28...` | **YES** |
| PT-srUSDe-2APR2026/USDC | $12.1M | — | `0x8B41...` | `0x527c...` | `0xfbba...` | NO (works) |

Both affected markets share:
- Same MetaOracle implementation: `0xcc319ef091bc520cf6835565826212024b2d25ec` (6166 bytes)
- Same OracleRouter owner: `0x1a9e836c455792654d8f657941ff59160eed7146` (Gnosis Safe, threshold 2)

## How MetaOracleDeviationTimelock Should Work

```
Normal:     Use primary oracle (assumes underlying at par)
Depeg:      primary ≠ backup by > threshold for > challengeTimelock
            → permissionless challenge → switch to backup
            → backup includes Chainlink underlying/USD feed
Recovery:   primary ≈ backup for > healingTimelock → switch back
```

## What's Broken

The OracleRouter (backup) points to the SAME contract as the primary oracle. The deviation comparison:

```
deviation = |primary.price() - backup.price()| / average
         = |X - X| / X
         = 0%
         (always, regardless of what happens in the real world)
```

**The deviation check will NEVER fire.** The MetaOracleDeviationTimelock's safety mechanism is completely non-functional.

## On-Chain Evidence

### Storage layout of MetaOracle proxy at `0xe846...` (PT-sNUSD):
```
slot[0] = 0xd25a93... (primary oracle)
slot[1] = 0x385ad6... (backup oracle = OracleRouter)
slot[2] = 10000000000000000 (maxDiscount = 1%)
slot[3] = 14400 (challengeTimelock = 4 hours)
slot[4] = 43200 (healingTimelock = 12 hours)
slot[5] = 0xd25a93... (currently active = primary)
```

### OracleRouter backup at `0x385ad6...`:
```
selector 0x7dc0d1d0 → 0xd25a93... (target = SAME as primary!)
selector 0x8da5cb5b → 0x1a9e83... (owner = Gnosis Safe 2-of-N)
price() = primary.price() = identical
```

### Confirmed via price comparison:
```
Primary price:  999743753170979199000000
Backup price:   999743753170979199000000
Divergence:     0.00000000%
```

## Underlying Risk: NUSD (Neutrl)

NUSD is a synthetic dollar from **Neutrl protocol** (launched Nov 2025):
- **Market cap**: ~$227M
- **Age**: ~4 months public
- **Historical depeg**: $0.975 (2.5% depeg, November 2025)
- **Chainlink feed**: NONE
- **Direct redemption**: KYC-gated only
- **DEX liquidity**: ~$10M Curve pool
- **Structural risks**: OTC-locked positions, perp hedging, liquidity-duration mismatch

The absence of a Chainlink feed for NUSD is likely WHY the backup was set to the same oracle — there's no independent price feed to compare against. But this means the MetaOracleDeviationTimelock provides a false sense of security.

## Oracle Type Analysis

### PT-sNUSD oracle chain (deterministic):
```
MetaOracle proxy (45 bytes, EIP-1167)
  → MetaOracleDeviationTimelock impl (6166 bytes)
    → Primary: Wrapper oracle (2598 bytes)
      → PendleChainlinkOracle feed (951 bytes)
         0 STATICCALL, 0 SSTORE, 2 TIMESTAMP opcodes
         PURE TIME-BASED COMPUTATION
         price = f(block.timestamp, expiry, maxDiscountPerYear)
         CANNOT BE MANIPULATED
         Always returns near $1.00 regardless of market conditions
```

### PT-srNUSD oracle chain (TWAP-based):
```
MetaOracle proxy (45 bytes, EIP-1167)
  → MetaOracleDeviationTimelock impl (6166 bytes)
    → Primary: Wrapper oracle
      → TWAP feed (8679 bytes, 15 STATICCALL)
         Reads from Pendle market PLP-srNUSD-28MAY2026
         TWAP window: 900 seconds (15 minutes)
         CAN BE MANIPULATED
         AND deviation check is dead (backup=primary)
```

## Risk Scenarios

### PT-sNUSD (LLTV 77%, $6.5M borrow):
- **Break-even depeg**: NUSD at $0.77 (23% depeg)
- **Historical worst**: $0.975 (far from break-even)
- **Bad debt at 30% depeg**: ~$596K
- **Risk**: Moderate — requires extreme depeg event

### PT-srNUSD (LLTV 91.5%, $1.1M borrow):
- **Break-even depeg**: NUSD at $0.915 (8.5% depeg)
- **Historical worst**: $0.975 (close but not there yet)
- **Bad debt at 10% depeg**: ~$18K
- **Bad debt at 15% depeg**: ~$79K
- **Risk**: Higher — 91.5% LLTV means thin margin
- **Additional risk**: TWAP oracle is manipulable AND deviation check is dead

## Attack Sequence (Non-Atomic, Multi-Step)

For PT-srNUSD (easier target due to higher LLTV + TWAP oracle):

1. **Position**: Deposit PT-srNUSD as collateral in Morpho, borrow USDC up to 91.5% LLTV
2. **Manipulate**: Either:
   a. Wait for natural NUSD depeg (structural risk event)
   b. Sell large amounts of NUSD into Curve pool ($5M+ to depeg 10%)
   c. Manipulate Pendle AMM TWAP upward (15-min window, backup can't catch it)
3. **Extract**: Oracle never adjusts → borrower walks away with excess USDC
4. **Result**: Lenders eat bad debt; no liquidation mechanism triggers

**Key limitation**: Not atomic. Step 2 requires sustained depeg or significant capital.

## Why This Survived Audits

1. The MetaOracleDeviationTimelock contract itself is correctly implemented (Cantina audited)
2. The vulnerability is in the **deployment configuration**, not the code
3. The backup=primary may be intentional (no Chainlink feed exists for NUSD)
4. But the wrapper still advertises deviation detection that doesn't actually work
5. The combination of factors (young stablecoin + no Chainlink feed + KYC-gated redemption + high LLTV + dead deviation check) creates compound risk that each factor alone wouldn't

## Recommended Fix

1. **Immediate**: Update OracleRouter targets to include an independent NUSD price source
   - If no Chainlink feed: use a Curve TWAP oracle for NUSD/USDC
   - Or add a Redstone/API3 feed for NUSD
2. **If no independent feed available**: Reduce LLTV on PT-srNUSD from 91.5% to lower value
3. **Documentation**: Clearly indicate that the MetaOracleDeviationTimelock's deviation detection is non-functional for these markets

## E3 Escalation Attempt (Exhaustive)

### Approach

12 attack vectors were brainstormed and systematically tested against on-chain state:

1. TWAP manipulation (push UP) → overborrow via leverage loop
2. TWAP manipulation (push DOWN) → forced liquidation
3. MetaOracle state machine attack (challenge/heal cycle)
4. Post-maturity oracle freeze
5. SY exchange rate manipulation
6. Observation cardinality attack
7. NUSD depeg exploitation
8. OracleRouter unprotected functions
9. Cross-market composition
10. Maturity boundary race
11. Feed max discount bypass
12. Pendle single-sided LP attack

### On-Chain Data (as of block 24586620, 2026-03-04)

```
Morpho market (PT-srNUSD/USDC):
  Market ID: 0xc2bc5e1e304fb1ea103dcbee37ece3c7e9219fb4b2b19d8ffdf81c39f4fbf180
  Total supply: $1,256,719.13 USDC
  Total borrow: $1,116,719.24 USDC
  Available liquidity: $139,999.89 USDC (88.9% utilization)
  LLTV: 91.5%
  LIF: 2.62%

Pendle AMM (PLP-srNUSD-28MAY2026):
  SY reserves: 2,653,268.59 tokens
  PT reserves: 710,839.56 tokens
  Total liquidity: 3,364,108 tokens
  LP supply: 1,645,074.70
  TWAP duration: 900s (15 min)
  Observations: 85 (ring buffer full)
  Avg trade interval: ~103 min
  SY exchange rate: 1.005077
  Expiry: 2026-05-28 (84 days)

Oracle state:
  Current TWAP: 0.98245 (PT/underlying)
  lnImpliedRate: ~0.0734 (annualized)
  Current discount from par: 2.25%
  updatedAt: current block (fresh)

Flash loans:
  Morpho USDC: $126.5M available (0 fee)
  PT-srNUSD in Morpho: 1,296,509 tokens
```

### Vector 1: OVERBORROW (Push TWAP UP) — IMPOSSIBLE

**Fundamental constraint**: PT price is bounded by maturity redemption value.

```
Max PT/SY at rate=0:         1.000000
Max oracle (PT/SY * SY_rate): 1.005078
Break-even oracle (1/LLTV):   1.073770
Max possible overvaluation:    2.30%
Required for profit:           9.29%

2.30% << 9.29% → IMPOSSIBLE
```

At 91.5% LLTV, the attacker needs to overvalue PT by >9.29% to extract more than deposited. But PT cannot trade above its maturity value (1.0 SY). The maximum overvaluation from rate=0 (most optimistic case) is only 2.30%.

**This vector is mathematically impossible regardless of AMM manipulation cost.**

### Vector 2: LIQUIDATION (Push TWAP DOWN) — ECONOMICALLY INFEASIBLE

To trigger liquidation of existing positions (8.5% oracle drop):

```
Required implied rate change: 0.0734 → 0.4597 (526% increase)
Largest observed rate jump:   ~2.2%
Trade size needed:            ~239x the largest observed trade
```

This would require draining most SY from the Pendle AMM pool (~3.36M tokens).

```
Revenue: $29,221 (2.62% LIF on $1.117M borrows)
AMM manipulation cost: >> $29,221 (estimated > $500K based on pool depth)
```

Even at 10x market size ($11.2M borrows), revenue ($292K) is still below estimated AMM cost.

### Vector 3: MetaOracle State Machine — DEAD END

```
challenge() (0xd2ef7398): REVERTS "Deviation threshold not met"
  → Because backup=primary → deviation always 0%
acceptChallenge/heal: REVERTS "Not challenged"
  → Cannot reach these states without successful challenge
All OracleRouter setters: owner-gated (Gnosis Safe 2-of-N)
```

### Vectors 4-12: All Falsified

- **Post-maturity**: PendleChainlinkOracle correctly returns 1.0 at maturity
- **SY exchange rate**: SY wraps yield-bearing token, rate is market-driven not manipulable
- **Observation cardinality**: 85 slots, all initialized — sufficient for accurate TWAP
- **NUSD depeg**: External event, not attacker-triggered
- **OracleRouter functions**: All setters owner-gated
- **Cross-market**: PT-sNUSD uses deterministic oracle (no TWAP manipulation possible)
- **Maturity race**: No exploitable discontinuity at maturity boundary
- **Max discount**: Caps downward only (1%), not relevant to attack vectors
- **Pendle LP**: Adding liquidity doesn't directly affect TWAP observations

### E3 Gate Check

```
✓ Reproducible sequence defined (multi-block TWAP manipulation)
✓ Fully permissionless (no privilege needed)
✓ Costs itemized (AMM manipulation + gas)
✗ Net profit: NEGATIVE at all market sizes tested
  - Overborrow: IMPOSSIBLE (PT bounded by maturity value)
  - Liquidation: cost >> revenue (AMM too deep vs market size)
✗ Robustness: N/A (not profitable)
```

**E3 STATUS: NOT MET** — No permissionless profitable exploit exists at current or foreseeable market conditions.

### Why E3 Fails

The fundamental reason is the **ratio mismatch** between AMM depth and Morpho market size:

- AMM pool: 3.36M tokens (~$3.3M TVL)
- Morpho market: $1.26M supply ($140K available)
- To manipulate a $3.3M pool enough to exploit a $140K liquidity window is inherently unprofitable

Additionally, the 91.5% LLTV creates a paradox:
- High LLTV = high leverage (good for attacker)
- But high LLTV also means the break-even overvaluation is ~9.3%
- PT price is bounded at ~2.3% above current (maturity ceiling)
- So the "high leverage" can never be weaponized for overborrowing

## Evidence Artifacts

- Scripts: `scripts/bypass_gates_step1to4.py`, `scripts/bypass_gates_step5to7.py`
- Oracle probe: `scripts/pendle_oracle_deep_probe.py`, `scripts/pendle_proxy_oracle_decode.py`
- NUSD analysis: `scripts/nusd_identity_probe.py`, `scripts/trace_nusd_underlying.py`
- Risk quantification: `scripts/quantify_nusd_risk.py`
- E3 discriminator battery: `scripts/e3_discriminator_battery.py`
- TWAP manipulation calc: `scripts/e3_twap_manipulation_calc.py`
- Stale TWAP analysis: `scripts/e3_stale_twap_attack.py`
- Refined economics: `scripts/e3_refined_attack_model.py`, `scripts/e3_final_economics.py`
- Pendle AMM model: `scripts/e3_pendle_amm_model.py`
- Morpho market query: `scripts/e3_morpho_market_find.py`, `scripts/e3_morpho_api_query.py`
