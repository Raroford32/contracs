# Finding: MetaOracleDeviationTimelock Backup=Primary Misconfiguration

## Status: E2 (Confirmed misconfiguration with real risk, not yet E3 permissionless drain)

## Summary

Six Morpho Blue markets on Ethereum mainnet use `MetaOracleDeviationTimelock` (Steakhouse Financial) oracle wrappers where **the backup oracle returns the exact same price as the primary oracle**. This defeats the MetaOracle's deviation detection mechanism entirely — the system compares an oracle against itself (or its functional clone), finding 0% deviation always.

The MetaOracle is designed to detect stablecoin depegs by comparing a "hardcoded at-par" primary oracle against an independent market-price backup oracle. When backup=primary, the depeg detection circuit is dead — the oracle will continue reporting "at par" even during a total collapse of the underlying.

**Total exposed supply: ~$58.5M across 6 markets**
**Total exposed borrow: ~$46.8M across 6 markets**

The largest single market (sUSDD/USDT) has **$51.7M supply / $40.9M borrow** backed by USDD — a Justin Sun / TRON ecosystem stablecoin that previously depegged to $0.93 in June 2022.

## Scan Methodology

Scanned all 767 unique oracles across 956 active Morpho Blue markets. Detected 32 EIP-1167 minimal proxy clones pointing to MetaOracle implementation `0xcc319ef091bc520cf6835565826212024b2d25ec`. Decoded immutable storage for all 32, compared primary vs backup price output. Found 6 where `primary.price() == backup.price()` (0.000000% divergence).

Script: `scripts/metaoracle_step4_lean.py`
Results: `analysis/engagements/morpho-metaoracle/scan_results.txt`
JSON: `analysis/engagements/bridge-finality-gap/notes/metaoracle_scan_results.json`

## Affected Markets (6 total)

### Group 1: sUSDD Markets (~$51.8M supply, ~$41.0M borrow) — HIGHEST RISK

| Market | Oracle | Supply | Borrow | LLTV | ChalTL | HealTL |
|---|---|---|---|---|---|---|
| sUSDD/USDT | `0x8c0a...8154` | $51.7M | $40.9M | 92% | 1800s | 3600s |
| sUSDD/USDC | `0x7be4...9f1f` | $97.8K | $85.0K | 92% | 1800s | 3600s |

**Collateral: sUSDD** (Savings USDD, ERC4626 vault at `0xC5d6A7B61d18AfA11435a889557b068BB9f29930`)
- sUSDD exchange rate: 1.042847 USDD per sUSDD (yield-accruing)
- Underlying: USDD (Decentralized USD) — TRON/Justin Sun ecosystem stablecoin
- USDD Ethereum supply: ~6.7M tokens
- USDD total supply (all chains): ~$124M
- **Historical depeg**: $0.93 in June 2022 (7% depeg)
- **No Chainlink feed for USDD** on Ethereum

**Oracle mechanics**: Primary (`0xb11b...b457`) and backup (`0x5908...03c1`) are **different contracts with different bytecode** but both return identical prices (1042801074648223165000000). Both derive from sUSDD's on-chain exchange rate; neither queries an independent USDD/USD market price.

```
Primary price(): 1042801074648223165000000 (1.0428 in 24 decimals)
Backup price():  1042801074648223165000000 (1.0428 in 24 decimals)
Divergence:      0.000000%
```

### Group 2: NUSD Markets (~$6.7M supply, ~$5.8M borrow)

| Market | Oracle | Supply | Borrow | LLTV | ChalTL | HealTL |
|---|---|---|---|---|---|---|
| PT-sNUSD-5MAR2026/USDC | `0xe846...82a9` | $4.7M | $4.0M | 77% | 14400s | 43200s |
| PT-srNUSD-28MAY2026/USDC | `0x0d07...21de3` | $1.3M | $1.2M | 92% | 14400s | 43200s |
| PT-sNUSD-4JUN2026/USDC | `0x7250...1fbc` | $475K | $435K | 86% | 14400s | 43200s |
| srNUSD/USDC | `0x9e10...f4be` | $158K | $138K | 92% | 14400s | 43200s |

**Underlying: NUSD (Neutrl)** — Synthetic dollar, launched Nov 2025
- Market cap: ~$227M, age ~4 months
- Historical depeg: $0.975 (2.5% depeg, November 2025)
- No Chainlink feed; redemption is KYC-gated only
- DEX liquidity: ~$10M in Curve pools
- Three of four backup oracles use OracleRouter that routes back to the same primary contract

## How MetaOracleDeviationTimelock Should Work

```
Normal state:  Use primary oracle (assumes underlying at par, derives price from exchange rate only)
Depeg event:   primary ≠ backup by > maxDiscount threshold for > challengeTimelock
               → anyone calls challenge() → switch to backup (market-price oracle)
               → positions repriced to true market value → liquidations trigger
Recovery:      primary ≈ backup for > healingTimelock → heal() → switch back to primary
```

## What's Broken

When backup returns the same price as primary:

```
deviation = |primary.price() - backup.price()| / average
         = |X - X| / X
         = 0%
         (always, regardless of what happens in the real world)
```

The `challenge()` function will **always revert** with "Deviation threshold not met". The MetaOracle's safety mechanism is permanently non-functional.

## On-Chain Evidence

### sUSDD/USDT MetaOracle (`0x8c0a...8154`) — Immutable Storage:
```
slot[0] = 0xb11b835214e1ffa6016298ade857723f33d7b457 (primary oracle)
slot[1] = 0x59080ad0f7693c41a5bf99d4044c079c23f803c1 (backup oracle)
slot[2] = 10000000000000000 (maxDiscount = 1.0%)
slot[3] = 1800 (challengeTimelock = 30 min)
slot[4] = 3600 (healingTimelock = 1 hour)
slot[5] = primary (currently active = primary)

Primary price(): 1042801074648223165000000
Backup price():  1042801074648223165000000
Divergence:      0.000000%

challenge() → REVERTS "Deviation threshold not met" (always)
```

### PT-sNUSD-5MAR2026/USDC MetaOracle (`0xe846...82a9`):
```
Primary (0xd25a...): PendleChainlinkOracle for sNUSD
Backup (0x385a...):  OracleRouter → target = 0xd25a... (SAME as primary!)
Divergence: 0.000000%
```

## Risk Assessment

### What happens if USDD depegs (e.g., drops to $0.80):

**Without the bug (healthy MetaOracle):**
1. Primary oracle continues reporting sUSDD/USDT ≈ 1.04 (at par)
2. Backup oracle reports sUSDD/USDT ≈ 0.83 (true market price)
3. Deviation = 20% > 1% threshold → challenge fires after 30 min
4. Oracle switches to backup → positions repriced → underwater borrowers liquidated
5. Loss limited to the 30-min exposure window

**With the bug (degenerate MetaOracle):**
1. Primary oracle reports sUSDD/USDT ≈ 1.04 (at par, WRONG)
2. Backup oracle ALSO reports sUSDD/USDT ≈ 1.04 (at par, WRONG)
3. Deviation = 0% → challenge NEVER fires
4. Oracle NEVER switches → collateral stays overvalued indefinitely
5. Existing borrowers: their sUSDD collateral (worth $0.83 each) backs $1.04 of debt
6. New attackers: deposit depegged sUSDD (bought at $0.80), borrow USDT at inflated $1.04 rate

### Depeg exploitation scenario (sUSDD/USDT, the $51.7M market):

```
Precondition: USDD depegs to $0.80 on markets

1. Attacker buys sUSDD on open market at ~$0.80 per USDD equivalent
2. Deposits sUSDD into Morpho sUSDD/USDT market
3. Oracle reports 1 sUSDD = $1.0428 (wrong, actually ~$0.834)
4. Borrows 91.5% × deposit × $1.0428 = extraction at 25% premium
5. With flash loans: repeatable until market's $51.7M supply drained

Maximum at-risk value: ~$51.7M (sUSDD/USDT supply)
Net profit margin per cycle: ~25% of deposit amount (at 20% depeg)
```

### Impact matrix by depeg severity:

| Depeg % | USDD Price | Oracle Reports | True Collateral Value | Bad Debt Potential |
|---|---|---|---|---|
| 5% | $0.95 | $1.0428 | $0.99 | ~$2.7M |
| 10% | $0.90 | $1.0428 | $0.94 | ~$5.1M |
| 20% | $0.80 | $1.0428 | $0.83 | ~$10.6M |
| 50% | $0.50 | $1.0428 | $0.52 | ~$25.5M |

### Severity:

| Factor | Assessment |
|---|---|
| Trigger | External depeg event (not attacker-controllable) |
| Probability of USDD depeg | Medium — depegged to $0.93 in June 2022 |
| Probability of NUSD depeg | Medium — depegged to $0.975 in Nov 2025 (4 months ago) |
| Impact if triggered | **Critical** — up to $58.5M at risk across all 6 markets |
| Permissionless exploitation | Yes — anyone can deposit depegged collateral and borrow |
| Time to exploit | Immediate once depeg occurs (no timelock protection) |
| Fix complexity | Low — redeploy MetaOracle proxies with correct backup addresses |

## Comparison: All 32 MetaOracle Instances

- **6 DEGENERATE** (backup=primary, 0% divergence): listed above
- **26 HEALTHY** (backup ≠ primary, non-zero divergence): functioning as designed
  - Typical divergence range: 0.0005% to 0.51%
  - All use distinct primary/backup oracle contracts with independent price sources

All 32 share the same implementation: `0xcc319ef091bc520cf6835565826212024b2d25ec`

## Why This Is E2 (Not E3)

E3 requires a **permissionless profitable exploit reproducible on a pinned fork**. This finding requires an **external precondition** (USDD or NUSD depeg) that is not attacker-controllable:

- We cannot trigger a USDD/NUSD depeg on a fork (it's cross-chain, market-driven)
- The misconfiguration is provably present (0% divergence on-chain, challenge always reverts)
- The economic impact is calculable but conditional on the depeg event
- The MetaOracle's design intent (switch oracle on depeg) is provably defeated

```
E3 STATUS: NOT MET — requires external precondition
CLASSIFICATION: E2 safety mechanism failure with conditional critical impact
```

## E3 Escalation Attempts (12 Vectors, All Falsified for NUSD Markets)

### Vector 1: OVERBORROW (Push TWAP UP) — MATHEMATICALLY IMPOSSIBLE
PT price is bounded by maturity redemption value. Max overvaluation from rate=0 is ~2.3%. At 91.5% LLTV, break-even requires >9.3% overvaluation. 2.3% << 9.3%.

### Vector 2: LIQUIDATION (Push TWAP DOWN) — ECONOMICALLY INFEASIBLE
AMM manipulation cost ($500K+) >> liquidation revenue ($29K). Even at 10x market size, still unprofitable.

### Vector 3: MetaOracle state machine — DEAD END
`challenge()` always reverts. `acceptChallenge`/`heal` unreachable.

### Vectors 4-12: All Falsified
Post-maturity, SY exchange rate, observation cardinality, OracleRouter functions, cross-market composition, maturity boundary, max discount, Pendle LP — all tested and found non-exploitable. See detailed analysis in earlier sections.

### sUSDD-specific E3 attempts:
- Both primary and backup derive from sUSDD's ERC4626 `convertToAssets()` rate
- Cannot flash-loan manipulate the exchange rate (rate = totalAssets/totalSupply, both are USDD balances)
- No external call in the oracle contracts that could be used for re-entrancy
- No admin functions accessible without Gnosis Safe multisig

## Evidence Artifacts

- Full scan script: `scripts/metaoracle_step4_lean.py`
- Scan results: `analysis/engagements/morpho-metaoracle/scan_results.txt`
- JSON results: `analysis/engagements/bridge-finality-gap/notes/metaoracle_scan_results.json`
- Previous NUSD deep-dive: `scripts/bypass_gates_step*.py`, `scripts/e3_*.py`
- Oracle probes: `scripts/pendle_oracle_deep_probe.py`, `scripts/pendle_proxy_oracle_decode.py`
- NUSD analysis: `scripts/nusd_identity_probe.py`, `scripts/trace_nusd_underlying.py`

## Recommendations

1. **Immediate (Critical)**: Redeploy MetaOracle proxies for all 6 affected markets with correct independent backup oracles
   - sUSDD markets: backup must query USDD/USD market price (Curve TWAP, Redstone, or any independent source)
   - NUSD markets: backup must be independent of the primary's price derivation
2. **Deployment validation**: Add factory-level check that `primary.price() != backup.price()` at deployment time (or at minimum verify addresses are not routed to the same endpoint)
3. **Monitoring**: Real-time alert for any MetaOracle where divergence stays at exactly 0% for >1 day
4. **Audit scope expansion**: Future audits should include deployment parameter verification, not just code review

## Why This Survived Prior Audits

1. The MetaOracle contract code is **correctly implemented** — the bug is in **deployment configuration**
2. Auditors review contract logic, not deployment parameters and oracle routing
3. The OracleRouter indirection (backup → router → primary) obscures the circular reference
4. The sUSDD case is particularly subtle: two different contracts with different bytecode but functionally identical outputs (both read the same on-chain exchange rate with no independent market price input)
5. Detection required checking **every deployed instance's actual price outputs** across all 767 unique oracles — a scale that demands automated scanning, not manual review
