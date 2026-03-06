# Finding: MetaOracleDeviationTimelock Backup=Primary Misconfiguration

## Status: E2 (Confirmed for NUSD markets; REVISED for sUSDD markets)

## Summary — REVISED 2026-03-06

**Original claim (6 markets, ~$58.5M)**: All 6 MetaOracle instances where `primary.price() == backup.price()` were flagged as degenerate.

**Correction after deep source code + immutable parameter audit**: The sUSDD markets are **NOT truly degenerate**. The backup oracle includes an independent USDD/USDT market price feed (Ojo). The 0% divergence at scan time is *expected behavior* when USDD trades at par. The NUSD markets **ARE genuinely degenerate** — backup routes via OracleRouter directly back to primary.

### Revised scope:
- **3 NUSD markets (~$6.2M supply, ~$5.3M borrow): CONFIRMED degenerate** — backup=primary via OracleRouter
- **3 markets DOWNGRADED (Informational)**:
  - PT-sNUSD-4JUN2026/USDC ($475K/$435K): backup has independent RedStone NUSD_FUNDAMENTAL feed
  - sUSDD/USDT ($51.7M/$40.9M): backup has independent Ojo USDD/USDT feed
  - sUSDD/USDC ($97.8K/$85K): same architecture as sUSDD/USDT

## Why the Original Scan Was Misleading

The scan compared `primary.price()` vs `backup.price()` at a single point in time. Both returned identical values for all 6 instances. This was interpreted as "backup=primary always."

**The flaw**: for the sUSDD oracles, the backup includes a USDD/USDT market price feed that returns 1.0 when USDD is at par. The prices are equal NOW but would diverge during a depeg. This is correct MetaOracle behavior, not a misconfiguration.

For the NUSD oracles, the backup literally routes through an `OracleRouter` contract whose `oracle()` function returns the primary oracle's address. This IS permanent backup=primary.

## Detailed Oracle Architecture (Source-Code Verified)

### sUSDD Primary Oracle (`0xb11b...b457`)
- **Contract**: `MorphoChainlinkOracleV2` (Morpho Labs, Solidity 0.8.21)
- **BASE_VAULT**: address(0) → returns 1
- **BASE_FEED_1**: `0xb96ef4e8...` — **"Ojo Yield Risk Engine sUSDD / USDD Exchange Rate"** (18 dec)
- **BASE_FEED_2**: address(0) → returns 1
- **QUOTE_FEED_1**: address(0) → returns 1
- **QUOTE_FEED_2**: address(0) → returns 1
- **SCALE_FACTOR**: 1,000,000

**Price formula**: `price = 1e6 × sUSDD_USDD_rate`
→ Hardcodes USDD/USDT = $1.00 (via SCALE_FACTOR normalization)

### sUSDD Backup Oracle (`0x5908...03c1`)
- **Contract**: `MorphoChainlinkOracleV2` (same code, different immutables)
- **BASE_VAULT**: address(0) → returns 1
- **BASE_FEED_1**: `0xb96ef4e8...` — **SAME Ojo sUSDD/USDD feed** (18 dec)
- **BASE_FEED_2**: `0x014f606c...` — **"USDD / USDT Exchange Rate"** (18 dec, Ojo) ← INDEPENDENT
- **QUOTE_FEED_1**: `0xc3866d72...` — **"Dummy feed with 12 decimals"** (returns 1e12 always)
- **QUOTE_FEED_2**: address(0) → returns 1
- **SCALE_FACTOR**: 1

**Price formula**: `price = sUSDD_USDD_rate × USDD_USDT_rate / 1e12`
→ Includes actual USDD/USDT market price via Ojo feed

### Depeg scenario (sUSDD — REVISED):
```
If USDD depegs to $0.80:
  Primary: 1e6 × 1.0428 = 1.0428e24 (still assumes USDD=$1)
  Backup:  1.0428 × 0.80 / 1e-12 = 0.8342e24 (reflects depeg)
  Deviation: ~20% > 1% threshold → challenge() FIRES after 30 min
  Oracle switches to backup → positions repriced → liquidations trigger

CONCLUSION: sUSDD MetaOracle WOULD function correctly during a depeg,
            IF the Ojo USDD/USDT feed updates to the depegged price.
```

### Ojo USDD/USDT Feed Reliability Concerns:
- Feed has reported exactly 1.000000000000000000 for 50+ consecutive rounds
- Updates approximately once per day
- Last 50 rounds (back to Jan 15, 2026): always 1.0
- Single oracle provider (no Chainlink decentralized network)
- **UNTESTED under depeg conditions** — has never needed to report a non-par price
- If this feed fails to update during a depeg, the backup oracle would remain at par

### NUSD Primary Oracle (PT-sNUSD-5MAR2026) (`0xd25a...`)
- **Contract**: `MorphoChainlinkOracleV2`
- **BASE_FEED_1**: `0xe488ee19...` — Pendle-related oracle feed
- All other feeds/vaults: address(0)
- **SCALE_FACTOR**: 1,000,000

### NUSD Backup Oracle (`0x385a...`)
- **Contract**: `OracleRouter`
- **oracle()**: `0xd25a93399d82e1a08d9da61d21fdff7f3e65eb27` — **SAME AS PRIMARY!**
- Routes `price()` directly to primary oracle
- **This IS genuinely degenerate**: backup = primary via routing

### srNUSD Primary Oracle (`0xe10a...`)
- Uses custom oracle (not standard MorphoChainlinkOracleV2 pattern — embedded address `0x5822...`)
- **SCALE_FACTOR**: 1,000,000

### srNUSD Backup Oracle (`0x39e1...`)
- **Contract**: `OracleRouter`
- **oracle()**: `0xe10a7d39e4ed00351dfe17378b5896e5f8ab422f` — **SAME AS PRIMARY!**
- **This IS genuinely degenerate**: backup = primary via routing

## Confirmed Affected Markets (3 NUSD markets — degenerate backup=primary)

| Market | Oracle | Supply | Borrow | LLTV | ChalTL | HealTL | Notes |
|---|---|---|---|---|---|---|---|
| PT-sNUSD-5MAR2026/USDC | `0xe846...82a9` | $4.7M | $4.0M | 77% | 14400s | 43200s | MATURED 2026-03-05 |
| PT-srNUSD-28MAY2026/USDC | `0x0d07...21de3` | $1.3M | $1.2M | 92% | 14400s | 43200s | |
| srNUSD/USDC | `0x9e10...f4be` | $158K | $138K | 92% | 14400s | 43200s | |

**Total confirmed at risk: ~$6.2M supply / ~$5.3M borrow**

### Post-maturity note (PT-sNUSD-5MAR2026):
- Matured at timestamp 1772668800 (2026-03-05 00:00 UTC)
- PendleChainlinkOracle adapter: `latestAnswer()` REVERTS post-maturity, but `latestRoundData()` still returns answer=1.0 (18 dec)
- MorphoChainlinkOracleV2 uses `latestRoundData()` → oracle still functional post-maturity
- Market should wind down as PT converges to underlying value

**Underlying: NUSD (Neutrl)** — Synthetic dollar, launched Nov 2025
- Market cap: ~$227M, age ~4 months
- Historical depeg: $0.975 (2.5% depeg, November 2025)
- No Chainlink feed; redemption is KYC-gated only
- DEX liquidity: ~$10M in Curve pools
- Three of four backup oracles use OracleRouter that routes back to the same primary contract
- PT-sNUSD-4JUN2026 backup uses independent RedStone NUSD_FUNDAMENTAL feed (not degenerate)

## Downgraded Markets (3 markets — Informational)

| Market | Oracle | Supply | Borrow | LLTV | Status |
|---|---|---|---|---|---|
| PT-sNUSD-4JUN2026/USDC | `0x7250...1fbc` | $475K | $435K | 86% | Backup has independent RedStone NUSD_FUNDAMENTAL feed |
| sUSDD/USDT | `0x8c0a...8154` | $51.7M | $40.9M | 92% | Backup has independent Ojo USDD/USDT feed |
| sUSDD/USDC | `0x7be4...9f1f` | $97.8K | $85.0K | 92% | Same architecture as sUSDD/USDT |

### PT-sNUSD-4JUN2026 downgrade rationale:
- Bytecode comparison of primary vs backup oracle revealed 6 diff regions
- Backup oracle has BASE_FEED_2 = RedStone NUSD_FUNDAMENTAL feed (8 decimals)
- Backup oracle has QUOTE_FEED_1 = Dummy 12-decimal feed (normalization)
- This is NOT an OracleRouter — it's a MorphoChainlinkOracleV2 with independent price derivation
- RedStone NUSD_FUNDAMENTAL returns 1.0 (at par), last updated 2026-03-06
- During NUSD depeg: backup would report lower price → challenge() would fire → MetaOracle WORKS
- Evidence: `/tmp/check_4jun_immutables.py`, `/tmp/verify_4jun_feeds.py`

### sUSDD downgrade rationale:
- Backup includes independent USDD/USDT Ojo feed (0x014f606c...)
- During depeg: backup would report lower price → challenge() fires → MetaOracle WORKS
- Concern: Ojo USDD/USDT feed reliability untested (50+ rounds at exactly 1.0, single provider)

**Risk**: Low-Medium. All three backup oracles ARE functionally different from their primaries and would diverge during a depeg. However, feed reliability under stress is untested for both RedStone NUSD_FUNDAMENTAL and Ojo USDD/USDT.

## How MetaOracleDeviationTimelock Works

Source: `MetaOracleDeviationTimelock.sol` (Steakhouse Financial, Solidity 0.8.20)

```
Normal state:  currentOracle = primaryOracle
Depeg event:   primary.price() ≠ backup.price() by > deviationThreshold
               → anyone calls challenge() → challengeExpiresAt set
               → after challengeTimelockDuration, if still deviant:
               → anyone calls acceptChallenge() → currentOracle = backupOracle
Recovery:      primary ≈ backup (deviation < threshold)
               → anyone calls heal() → healingExpiresAt set
               → after healingTimelockDuration, if still converged:
               → anyone calls acceptHealing() → currentOracle = primaryOracle
```

Key properties (verified from source):
- **No admin functions.** All 6 state transitions are permissionless.
- **No upgradeability.** Configuration set once in `initialize()` (OpenZeppelin `initializer` modifier).
- **`initialize()` checks**: `require(primaryOracle != backupOracle)` — checks ADDRESS only, not behavior.
- **Silent fallback in `price()`**: if currentOracle reverts, silently returns the other oracle's price.

## What's Broken (NUSD Markets Only)

When backup routes to primary via OracleRouter:

```
deviation = |primary.price() - backup.price()| / average
         = |X - OracleRouter.price()| / average
         = |X - primary.price()| / average    (OracleRouter calls primary)
         = |X - X| / X
         = 0%
         (ALWAYS, regardless of what happens in the real world)
```

The `challenge()` function will **always revert** with "Deviation threshold not met". The MetaOracle's safety mechanism is permanently non-functional for these 4 NUSD markets.

## On-Chain Evidence

### PT-sNUSD-5MAR2026/USDC MetaOracle (`0xe846...82a9`):
```
Primary (0xd25a...): MorphoChainlinkOracleV2 — BASE_FEED_1 = Pendle oracle
Backup (0x385a...):  OracleRouter → oracle() = 0xd25a... (SAME as primary!)

Primary price(): 1000000000000000000000000 (1.0 in 24 dec)
Backup price():  1000000000000000000000000 (1.0 in 24 dec)
Divergence: 0.000000%
challenge() → REVERTS "Deviation threshold not met" (always)
```

### srNUSD/USDC MetaOracle (`0x9e10...f4be`):
```
Primary (0xe10a...): Custom oracle (embedded address 0x5822...)
Backup (0x39e1...):  OracleRouter → oracle() = 0xe10a... (SAME as primary!)

Primary price(): 1005274330606077473000000 (1.0053 in 24 dec)
Backup price():  1005274330606077473000000 (1.0053 in 24 dec)
Divergence: 0.000000%
challenge() → REVERTS "Deviation threshold not met" (always)
```

### sUSDD/USDT MetaOracle (`0x8c0a...8154`) — REVISED:
```
Primary (0xb11b...): MorphoChainlinkOracleV2
  BASE_FEED_1 = Ojo sUSDD/USDD rate
  Formula: price = 1e6 × sUSDD_rate (assumes USDD=$1)

Backup (0x5908...): MorphoChainlinkOracleV2
  BASE_FEED_1 = Ojo sUSDD/USDD rate (SAME)
  BASE_FEED_2 = Ojo USDD/USDT market rate (INDEPENDENT!)
  QUOTE_FEED_1 = Dummy 12-dec feed (normalization)
  Formula: price = sUSDD_rate × USDD_USDT_rate / 1e12

Current state: primary=backup=1.0428e24 (USDD at par → expected)
Depeg state: backup would report lower price → challenge() would fire
STATUS: NOT DEGENERATE — backup has independent market price feed
```

## Risk Assessment (NUSD Markets)

### What happens if NUSD depegs:

**Without the bug (healthy MetaOracle):**
1. Primary continues reporting PT/sNUSD/srNUSD at par
2. Backup reports market-adjusted price reflecting NUSD depeg
3. Deviation exceeds threshold → challenge fires after 4 hours
4. Oracle switches → positions repriced → liquidations trigger

**With the bug (degenerate MetaOracle, as deployed):**
1. Primary reports at par (WRONG if NUSD has depegged)
2. Backup also reports at par (routes back to primary, also WRONG)
3. Deviation = 0% → challenge NEVER fires
4. Oracle NEVER switches → collateral stays overvalued indefinitely
5. Bad debt accumulates without bound

### Severity (NUSD Markets):

| Factor | Assessment |
|---|---|
| Trigger | External depeg event (not attacker-controllable) |
| Probability of NUSD depeg | Medium — depegged to $0.975 in Nov 2025 (4 months ago) |
| Impact if triggered | **High** — up to $6.2M at risk across 3 markets |
| Permissionless exploitation | Yes — anyone can deposit depegged collateral and borrow USDC |
| Time to exploit | Immediate once depeg occurs (no timelock protection) |
| Fix complexity | Low — redeploy MetaOracle proxies with independent backup |

## E3 Escalation Attempts (All Falsified)

### NUSD-specific (12 Vectors, All Falsified)

1. **OVERBORROW** (Push PT TWAP UP): Mathematically impossible — PT bounded by maturity value
2. **LIQUIDATION** (Push TWAP DOWN): Economically infeasible — cost >> revenue
3. **MetaOracle state machine**: challenge() always reverts (0% divergence)
4-12. Post-maturity, SY exchange rate, observation cardinality, OracleRouter functions, cross-market composition, maturity boundary, max discount, Pendle LP — all tested and found non-exploitable.

### sUSDD-specific (7 Vectors, All Falsified — plus finding is downgraded)

1. **Exchange rate manipulation**: IMPOSSIBLE — Pot.chi from governance-only dsr
2. **Donation attack**: IMPOSSIBLE — totalAssets = pie × chi (internal accounting, no ERC20 balance)
3. **USDD bridge mint**: No permissionless path — MakerDAO Vat/Join architecture
4. **USDD DEX manipulation**: Zero liquidity for USDD_NEW on Ethereum
5. **MetaOracle reinit**: `initialize()` uses OpenZeppelin `initializer` — one-time only
6. **Drip timing**: ~0.0001% per interval — negligible
7. **Cross-protocol composition**: sUSDD/USDD not listed in Aave, Euler, or other lending markets

```
E3 STATUS: NOT MET — requires external precondition (NUSD depeg)
CLASSIFICATION (NUSD, 3 markets): E2 safety mechanism failure with conditional high impact ($6.2M)
CLASSIFICATION (PT-sNUSD-4JUN2026): Informational — backup has independent RedStone NUSD_FUNDAMENTAL feed
CLASSIFICATION (sUSDD): Informational — backup has independent Ojo USDD/USDT feed, reliability concerns only
```

## Why This Is E2 (Not E3)

E3 requires a **permissionless profitable exploit reproducible on a pinned fork**. This finding requires an **external precondition** (NUSD depeg) that is not attacker-controllable:

- We cannot trigger a NUSD depeg on a fork (market-driven, cross-chain)
- The misconfiguration is provably present for 3 NUSD markets (OracleRouter→primary)
- PT-sNUSD-4JUN2026 was reclassified: backup uses independent RedStone NUSD_FUNDAMENTAL feed
- The economic impact is calculable but conditional on the depeg event
- The MetaOracle's design intent (switch oracle on depeg) is provably defeated for 3 NUSD markets

## Evidence Artifacts

- Full scan script: `scripts/metaoracle_step4_lean.py`
- Scan results: `analysis/engagements/morpho-metaoracle/scan_results.txt`
- JSON results: `analysis/engagements/bridge-finality-gap/notes/metaoracle_scan_results.json`
- Deep oracle immutable analysis: `/tmp/oracle_immutables.py`, `/tmp/feed_analysis.py`, `/tmp/backup_feeds.py`
- sUSDD vault source: Sourcify (SavingsUsdd.sol — MakerDAO DSR fork, no admin functions)
- MetaOracle source: Sourcify (MetaOracleDeviationTimelock.sol — no admin functions, no upgradeability)
- Primary/backup oracle source: Sourcify (MorphoChainlinkOracleV2.sol — immutable config, no staleness checks)
- NUSD deep-dive: `scripts/bypass_gates_step*.py`, `scripts/e3_*.py`
- Oracle probes: `scripts/pendle_oracle_deep_probe.py`, `scripts/pendle_proxy_oracle_decode.py`
- NUSD analysis: `scripts/nusd_identity_probe.py`, `scripts/trace_nusd_underlying.py`
- Pot/Vat/Join analysis: `/tmp/pot_check.py`, `/tmp/usdd_deep_chain.py`, `/tmp/real_join.py`

## Recommendations

1. **Immediate (High)**: Redeploy MetaOracle proxies for the 3 degenerate NUSD markets with independent backup oracles
   - Backup must query NUSD/USD market price from an independent source (not routing back to primary)
2. **Medium (sUSDD)**: Evaluate Ojo USDD/USDT feed reliability — consider adding a second independent data source
3. **Deployment validation**: Add factory-level check at deployment that backup oracle's price derivation is independent of primary (not just address comparison)
4. **Monitoring**: Real-time alert for any MetaOracle where divergence stays at exactly 0% for >1 day
5. **Audit scope expansion**: Future audits should include deployment parameter verification and oracle feed independence testing

## Why This Survived Prior Audits

1. The MetaOracle contract code is **correctly implemented** — the bug is in **deployment configuration** (OracleRouter pointing to primary)
2. Auditors review contract logic, not deployment parameters and oracle routing
3. The OracleRouter indirection (backup → router → primary) obscures the circular reference
4. The `initialize()` function checks `require(primaryOracle != backupOracle)` but this only compares addresses, not behavior — the OracleRouter has a different address but delegates to the same price source
5. Detection required checking **every deployed instance's actual price derivation chain** across all 767 unique oracles — not just comparing prices at a single point in time (which gives false positives when the underlying is at par)
