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

## Phase 6: MetaOracle Broad Scan — E2 FINDING (REVISED: 3 NUSD instances confirmed degenerate)

### Finding: MetaOracleDeviationTimelock Backup=Primary via OracleRouter
- Scanned all 767 unique oracles across 956 active Morpho markets
- Found 32 MetaOracle EIP-1167 proxies → 6 initially flagged (0% divergence at scan time)
- **REVISED 2026-03-06**: Deep source code + immutable audit corrections applied

### CONFIRMED DEGENERATE (3 NUSD markets, ~$6.2M supply / ~$5.3M borrow):
- **PT-sNUSD-5MAR2026/USDC**: $4.7M / $4.0M — backup OracleRouter → primary (MATURED 2026-03-05)
- **PT-srNUSD-28MAY2026/USDC**: $1.3M / $1.2M — backup OracleRouter → primary
- **srNUSD/USDC**: $158K / $138K — backup OracleRouter → primary

### DOWNGRADED (3 markets — Informational):
- **PT-sNUSD-4JUN2026/USDC**: $475K / $435K — backup has independent RedStone NUSD_FUNDAMENTAL feed (not OracleRouter)
- **sUSDD/USDT**: $51.7M / $40.9M — backup HAS independent Ojo USDD/USDT feed
- **sUSDD/USDC**: $97.8K / $85K — same architecture as sUSDD/USDT

### Key corrections:
- sUSDD: Backup includes independent USDD/USDT Ojo feed → MetaOracle WORKS during depeg
- PT-sNUSD-4JUN2026: Bytecode comparison revealed backup has BASE_FEED_2=RedStone NUSD_FUNDAMENTAL (independent)
- PT-sNUSD-5MAR2026: MATURED 2026-03-05; PendleChainlinkOracle latestAnswer() REVERTS post-maturity but latestRoundData() still returns 1.0 → oracle still functional

### E2 status rationale (3 degenerate NUSD markets)
- OracleRouter routing provably confirmed: backup.oracle() = primary address
- challenge() always reverts with 0% divergence (backup = primary via routing)
- If NUSD depegs, oracle never switches → unlimited bad debt accumulation
- BUT depeg is external event, not attacker-triggerable → cannot reach E3
- 12+ attack vectors tested and falsified

### Evidence
- `scripts/metaoracle_step4_lean.py` (scan script)
- `analysis/engagements/bridge-finality-gap/notes/finding-metaoracle-backup-primary.md` (REVISED finding)
- Oracle immutable analysis: `/tmp/oracle_immutables.py`, `/tmp/feed_analysis.py`, `/tmp/backup_feeds.py`
- PT-sNUSD-4JUN2026 bytecode comparison: `/tmp/check_4jun_immutables.py`, `/tmp/verify_4jun_feeds.py`
- Post-maturity oracle check: `/tmp/deep_oracle_check.py`
- Full NUSD verification: `/tmp/verify_all_nusd.py`

## Phase 7: Deep Source Code Composition Analysis — NO E3 VECTOR

### Full source code review of all engagement contracts:
- Across SpokePool (96KB), HubPool, Ethereum_SpokePool
- Synapse FastBridge, Celer cBridge V2, Hop L1 ETH Bridge
- Metis L1StandardBridge
- All MetaOracle/MorphoChainlinkOracleV2/OracleRouter contracts

### 25+ composition chains evaluated (A-Y), all falsified:
- **Bridge→MetaOracle**: No bridge can trigger NUSD depeg → no composition path
- **Across unsafeDeposit + emergencyDelete**: Both require admin/owner
- **Across _noRevertTransfer → pending refunds**: Deferred refunds are credits, not exploitable
- **Synapse destTxHash arbitrary**: No on-chain verification, but RELAYER_ROLE required
- **Celer signer self-update**: Requires 2/3 quorum of existing signers
- **Hop challengeTransferBond**: Permissionless but requires real stake + 10-day resolution
- **Cross-bridge token composition**: Off-chain mitigated (dataworker route restrictions)
- **Post-maturity PT oracle + MetaOracle**: Oracle still returns 1.0 via latestRoundData()
- **MetaMorpho reflexive loops**: Vault donation attack economically infeasible (LLTV < 1)
- All remaining chains require either admin keys, external market events, or are architecturally blocked

### Post-maturity oracle discovery:
- PT-sNUSD-5MAR2026 matured 2026-03-05 (timestamp 1772668800)
- PendleChainlinkOracle.latestAnswer() REVERTS post-maturity
- PendleChainlinkOracle.latestRoundData() still returns answer=1.0 (18 dec)
- MorphoChainlinkOracleV2 uses latestRoundData() → oracle still functional
- No immediate exploit from maturity transition

## Last Experiment
- Full source code composition analysis across all engagement contracts
- PT-sNUSD-4JUN2026 bytecode comparison: backup has independent RedStone NUSD_FUNDAMENTAL feed
- Post-maturity oracle behavior verified on-chain
- 25+ composition chains systematically evaluated and falsified
- Result: No E3 vector; degenerate market count revised from 4 to 3 (~$6.2M)
- Belief change: PT-sNUSD-4JUN2026 NOT degenerate (RedStone independent backup)

## Next Discriminator
- None remaining. All vectors exhausted across 7 phases. Finding is E2-complete for 3 NUSD markets.

## Conclusion
After exhaustive investigation across 7 phases covering:
- 1216 Morpho Blue markets, 901 oracles, 767 unique oracle contracts
- 32 MetaOracle instances fully decoded, immutable params read, source code audited
- Full source code review: MetaOracle, MorphoChainlinkOracleV2, SavingsUsdd, Pot, Vat, UsddJoin
- Full source code review: Across SpokePool/HubPool, Synapse FastBridge, Celer cBridge, Hop Bridge
- 25+ cross-protocol composition chains systematically evaluated
- Aave V3 (incl. 19+ e-mode categories, CAPO mechanism)
- Euler V2 + EulerSwap (calcLimits quantified)
- Fluid Protocol (163 vaults + DEX, shared liquidity layer)
- Pendle PT (60+ markets, post-maturity oracle behavior), LRT oracles, Balancer V2 forks
- Uniswap V4 hooks, recent 2026 exploit patterns

**One E2 finding: 3 NUSD MetaOracle instances with backup=primary via OracleRouter, ~$6.2M at conditional risk.**
**3 markets downgraded**: PT-sNUSD-4JUN2026 (RedStone backup), sUSDD/USDT & sUSDD/USDC (Ojo backup).
**No E3 permissionless profitable exploit achievable** — the NUSD finding requires an external depeg event.

## Open Unknowns (Residual, Low-Probability)
- NUSD depeg event could trigger ~$5.3M bad debt across 3 degenerate NUSD markets (no safety mechanism)
- PT-sNUSD-5MAR2026 matured — oracle still functional but market should wind down
- Ojo USDD/USDT feed reliability untested under stress (single provider, always 1.0 for 50+ rounds)
- RedStone NUSD_FUNDAMENTAL feed reliability under depeg conditions untested
- Novel protocol launches with untested oracle designs
