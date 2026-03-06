# Memory (bridge-finality-gap)

## Pinned Reality
- chain_id: 1 (Ethereum Mainnet)
- fork_block: 24539674 (pinned 2026-02-26)
- discriminator_block: ~24554470 (live 2026-02-28)
- attacker_tier: permissionless (flash loan capable)
- capital_model: flash loans from Aave V3 / Morpho Blue (0% fee)

## Phase 1: Bridge Protocols — COMPLETE, SUB-E3
**Across Protocol (HC-1):** All 5 vectors confirmed. L2 finality gap is sole remaining vector. DESIGN RISK — not immediately actionable.

## Phase 2: DeFi Composition Survey — COMPLETE
Pivoted per user directive to find immediately exploitable, permissionless composition drain.

## Phase 3: Morpho Blue ERC-4626 Donation Attack — EXHAUSTED
Kill chain economics prove collateral-side donation ALWAYS fails:
```
d(profit)/dD = A*LLTV/(T+A) - 1 < 0 always (LLTV < 1)
```
- 901 oracles scanned; ZERO have QUOTE_VAULT set

## Phase 4: Second Wave — ALL EXHAUSTED
- Pendle PT Oracle: deterministic, NO AMM data → NOT EXPLOITABLE
- LRT Oracle Deviation: 0.5% threshold, CAPO-blocked → NOT EXPLOITABLE
- Balancer V2 Forks: all paused/drained/disabled on mainnet → NOT EXPLOITABLE
- Euler V2 + EulerSwap: 45+ audits, formal verification → LOW SURFACE
- Morpho Oracle Misconfig: pattern confirmed, no live target → NOT EXPLOITABLE

## Phase 5: Third Wave — ALL EXHAUSTED

### Fluid Protocol — NOT EXPLOITABLE
- Architecture: shared Liquidity Layer, 163 vaults, DEX pools, ~$3.3B TVL
- Oracle: Chainlink + Redstone external (NOT Fluid DEX prices)
- Circuit breakers restrict abnormal large withdrawals/borrows per block
- 7+ years zero exploits, Cantina competition, MixBytes audit, $500K bounty
- Evidence: scripts/fluid_onchain_analysis.py, scripts/fluid_oracle_check.py

### EulerSwap calcLimits() — NOT EXPLOITABLE
- CS-EULSWP-015: double-counts LP's vault balance in VIEW function
- Actual swap() enforces limits independently via vault withdraw/borrow
- Bonding curve invariant verified in SwapLib.finish()
- $500K live CTF: no funds compromised
- Evidence: agent research of ChainSecurity audit PDF

### Full Morpho Oracle Scan (all 1216 markets) — NO NEW TARGETS
- Active markets: 948 (supply > 0)
- Anomalies: 2 (PAXG/USDC=known exploit, BOBO/USDS=$5K memecoin)
- Zero new exploitable oracle misconfigurations
- Evidence: scripts/morpho_full_oracle_scan.py

### Aave V3 E-Mode — NO VULNERABILITY
- All 19+ e-mode categories have priceSource = 0x0 (standard oracle)
- No custom e-mode oracle to manipulate
- Evidence: scripts/aave_emode_analysis.py

### Uniswap V4 Hooks — NO IMMEDIATE COMPOSITION DRAIN
- Cork Protocol exploit ($11M, May 2025) was hook-specific, not core V4
- No lending drain via V4 hook reported as of Feb 2026
- $15.5M bug bounty active

### 2026 Exploit Pattern Analysis
- Serial oracle misconfig attacker: Moonwell ($1.78M), Ploutos ($388K)
- Targets: small/new/unaudited protocols, NOT established Morpho/Aave/Euler
- Confirms investigation angle correct but no new live targets exist

## Phase 6: MetaOracle Broad Scan — E2 FINDING (REVISED: 4 NUSD instances confirmed)

### Finding: MetaOracleDeviationTimelock Backup=Primary via OracleRouter
- Scanned all 767 unique oracles across 956 active Morpho markets
- Found 32 MetaOracle EIP-1167 proxies → 6 initially flagged (0% divergence at scan time)
- **REVISED 2026-03-06**: Deep source code + immutable audit showed sUSDD markets are NOT degenerate

### CONFIRMED DEGENERATE (4 NUSD markets, ~$6.7M supply / ~$5.8M borrow):
- **PT-sNUSD-5MAR2026/USDC**: $4.7M / $4.0M — backup OracleRouter → primary
- **PT-srNUSD-28MAY2026/USDC**: $1.3M / $1.2M — backup OracleRouter → primary
- **PT-sNUSD-4JUN2026/USDC**: $475K / $435K — backup OracleRouter → primary
- **srNUSD/USDC**: $158K / $138K — backup OracleRouter → primary

### DOWNGRADED (2 sUSDD markets, ~$51.8M — Informational):
- **sUSDD/USDT**: $51.7M / $40.9M — backup HAS independent Ojo USDD/USDT feed
- **sUSDD/USDC**: $97.8K / $85K — same architecture
- 0% divergence is EXPECTED when USDD at par; backup WOULD diverge during depeg
- Concern: Ojo USDD/USDT feed reported exactly 1.0 for 50+ rounds, reliability untested

### Key correction: sUSDD oracles
- Primary = MorphoChainlinkOracleV2: price = 1e6 × Ojo_sUSDD_USDD_rate (hardcodes USDD=$1)
- Backup = MorphoChainlinkOracleV2: price = Ojo_sUSDD_USDD_rate × Ojo_USDD_USDT_rate / dummy
- Backup INCLUDES independent USDD/USDT market price feed (Ojo, 0x014f606c...)
- During depeg: backup would report lower price → challenge() would fire → MetaOracle WORKS

### E2 status rationale (NUSD markets)
- OracleRouter routing provably confirmed: backup.oracle() = primary address
- challenge() always reverts with 0% divergence (backup = primary via routing)
- If NUSD depegs, oracle never switches → unlimited bad debt accumulation
- BUT depeg is external event, not attacker-triggerable → cannot reach E3
- 12+ attack vectors tested and falsified across both NUSD and sUSDD

### Evidence
- `scripts/metaoracle_step4_lean.py` (scan script)
- `analysis/engagements/bridge-finality-gap/notes/finding-metaoracle-backup-primary.md` (REVISED finding)
- Oracle immutable analysis: `/tmp/oracle_immutables.py`, `/tmp/feed_analysis.py`, `/tmp/backup_feeds.py`
- MetaOracle source: Sourcify (no admin functions, no upgradeability)
- MorphoChainlinkOracleV2 source: Sourcify (immutable config, no staleness checks)
- SavingsUsdd source: Sourcify (MakerDAO DSR fork, no admin functions)

## Last Experiment
- Deep source code audit of MetaOracle, MorphoChainlinkOracleV2, SavingsUsdd
- Decoded all immutable constructor params for primary and backup sUSDD oracles
- Found backup oracle HAS independent USDD/USDT Ojo feed (was previously assumed identical)
- Verified NUSD backup oracles route via OracleRouter directly to primary (genuinely degenerate)
- Result: sUSDD downgraded to Informational; NUSD confirmed E2 ($6.7M)
- Belief change: MAJOR — sUSDD finding was based on false assumption about oracle architecture

## Next Discriminator
- None remaining. All vectors exhausted. Finding is E2-complete for NUSD markets.

## Conclusion
After exhaustive investigation across 6 phases covering:
- 1216 Morpho Blue markets, 901 oracles, 767 unique oracle contracts
- 32 MetaOracle instances fully decoded, immutable params read, source code audited
- Full source code review: MetaOracle, MorphoChainlinkOracleV2, SavingsUsdd, Pot, Vat, UsddJoin
- Aave V3 (incl. 19+ e-mode categories, CAPO mechanism)
- Euler V2 + EulerSwap (calcLimits quantified)
- Fluid Protocol (163 vaults + DEX, shared liquidity layer)
- Pendle PT (60+ markets), LRT oracles, Balancer V2 forks
- Uniswap V4 hooks, recent 2026 exploit patterns

**One E2 finding: 4 NUSD MetaOracle instances with backup=primary via OracleRouter, ~$6.7M at conditional risk.**
**sUSDD markets downgraded**: backup has independent Ojo USDD/USDT feed (Informational — reliability concern only).
**No E3 permissionless profitable exploit achievable** — the NUSD finding requires an external depeg event.

## Open Unknowns (Residual, Low-Probability)
- NUSD depeg event could trigger ~$5.8M bad debt across 4 NUSD markets (no safety mechanism)
- Ojo USDD/USDT feed reliability untested under stress (single provider, always 1.0 for 50+ rounds)
- Novel protocol launches with untested oracle designs
