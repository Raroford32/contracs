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

## Evidence Artifacts

- Scripts: `scripts/bypass_gates_step1to4.py`, `scripts/bypass_gates_step5to7.py`
- Oracle probe: `scripts/pendle_oracle_deep_probe.py`, `scripts/pendle_proxy_oracle_decode.py`
- NUSD analysis: `scripts/nusd_identity_probe.py`, `scripts/trace_nusd_underlying.py`
- Risk quantification: `scripts/quantify_nusd_risk.py`
