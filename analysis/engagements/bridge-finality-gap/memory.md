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

## Phase 6: MetaOracle Broad Scan — E2 FINDING (6 degenerate instances)

### Finding: MetaOracleDeviationTimelock Backup=Primary Misconfiguration
- Scanned all 767 unique oracles across 956 active Morpho markets
- Found 32 MetaOracle EIP-1167 proxies → 6 DEGENERATE (backup=primary price)
- **sUSDD/USDT**: $51.7M supply / $40.9M borrow (LARGEST — USDD/Justin Sun ecosystem)
- **sUSDD/USDC**: $97.8K supply / $85K borrow
- **PT-sNUSD-5MAR2026/USDC**: $4.7M supply / $4.0M borrow (NUSD/Neutrl)
- **PT-srNUSD-28MAY2026/USDC**: $1.3M supply / $1.2M borrow
- **PT-sNUSD-4JUN2026/USDC**: $475K supply / $435K borrow
- **srNUSD/USDC**: $158K supply / $138K borrow
- **Total at risk: ~$58.5M supply / ~$46.8M borrow**

### Key insight: sUSDD case
- Primary and backup are DIFFERENT contracts (different bytecode) but IDENTICAL output
- Both derive sUSDD price from on-chain exchange rate; NEITHER queries USDD/USD market price
- USDD has NO Chainlink feed on Ethereum
- USDD depegged to $0.93 in June 2022

### E2 status rationale
- Misconfiguration provably confirmed: challenge() always reverts with 0% divergence
- If underlying depegs, oracle never switches → unlimited bad debt accumulation
- BUT depeg is external event, not attacker-triggerable → cannot reach E3
- 12 attack vectors tested and falsified for NUSD markets
- sUSDD oracle exchange rate not flash-loan manipulable

### Evidence
- `scripts/metaoracle_step4_lean.py` (scan script)
- `analysis/engagements/morpho-metaoracle/scan_results.txt` (full results)
- `analysis/engagements/bridge-finality-gap/notes/finding-metaoracle-backup-primary.md` (detailed finding)
- `analysis/engagements/bridge-finality-gap/notes/metaoracle_scan_results.json`

## Last Experiment
- Full MetaOracle scan: 767 oracles → 32 MetaOracle → 6 degenerate
- sUSDD investigation: confirmed both oracle contracts return identical prices from same rate source
- Result: E2 finding (conditional critical impact), E3 not achievable (external trigger required)
- Belief change: Scale of exposure much larger than initially found ($58.5M vs $7.7M); sUSDD/USDT is dominant risk

## Next Discriminator
- None remaining. All vectors exhausted. Finding is E2-complete.

## Conclusion
After exhaustive investigation across 6 phases covering:
- 1216 Morpho Blue markets, 901 oracles, 767 unique oracle contracts
- 32 MetaOracle instances fully decoded and compared
- Aave V3 (incl. 19+ e-mode categories, CAPO mechanism)
- Euler V2 + EulerSwap (calcLimits quantified)
- Fluid Protocol (163 vaults + DEX, shared liquidity layer)
- Pendle PT (60+ markets), LRT oracles, Balancer V2 forks
- Uniswap V4 hooks, recent 2026 exploit patterns

**One E2 finding: 6 MetaOracle instances with disabled safety mechanism, ~$58.5M at conditional risk.**
**No E3 permissionless profitable exploit achievable** — the finding requires an external depeg event.

## Open Unknowns (Residual, Low-Probability)
- USDD depeg event could trigger immediate ~$51.7M bad debt in sUSDD/USDT market
- NUSD depeg event could trigger ~$5.8M bad debt across 4 NUSD markets
- Novel protocol launches with untested oracle designs
