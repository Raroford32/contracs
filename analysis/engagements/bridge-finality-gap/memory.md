# Memory (bridge-finality-gap)

## Pinned Reality
- chain_id: 1 (Ethereum Mainnet)
- fork_block: 24539674 (pinned 2026-02-26)
- discriminator_block: ~24554258 (live 2026-02-28)
- attacker_tier: permissionless (flash loan capable)
- capital_model: flash loans from Aave V3 / Morpho Blue (0% fee)

## Phase 1: Bridge Protocols — COMPLETE, SUB-E3

**Across Protocol (HC-1):** All 5 vectors confirmed. L2 finality gap is sole remaining vector. DESIGN RISK — not immediately actionable.
**Celer/Synapse/Hop:** Deprioritized.

## Phase 2: DeFi Composition Survey — COMPLETE

Pivoted per user directive to find immediately exploitable, permissionless composition drain.

## Phase 3: Morpho Blue ERC-4626 Donation Attack — EXHAUSTED

Kill chain economics prove collateral-side donation ALWAYS fails:
```
profit = A*(T+A+D)/(T+A)*LLTV - A - D
d(profit)/dD = A*LLTV/(T+A) - 1 < 0 always (LLTV < 1)
```
- 901 MorphoChainlinkOracleV2 oracles scanned; ZERO have QUOTE_VAULT set
- Evidence: notes/morpho-erc4626-analysis.md, scripts/morpho_market_scanner.py

## Phase 4: Second Wave — ALL EXHAUSTED

### Pendle PT Oracle — NOT EXPLOITABLE
- Aave uses `PendlePriceCapAdapter`: deterministic linear discount, NO AMM data input
- Morpho uses `SparkLinearDiscountOracle`: deterministic, NO market data
- Some Morpho markets use Pendle AMM 15-min TWAP — manipulation requires multi-block validator control
- PT markets on Morpho have negligible liquidity (<$70K largest)
- $4.6B PT on Aave protected by Chaos Labs Edge Oracle (off-chain with anomaly detection)
- Evidence: scripts/pendle_pt_scanner.py (found 60+ PT markets, all tiny)

### LRT Oracle Deviation — NOT EXPLOITABLE
- rsETH Chainlink mainnet deviation: **0.5%** (NOT 2% — the 2% was rETH/ETH internal feed)
- Aave uses CAPO adapter: caps exchange rate growth to ~9.83%/year
- Morpho lacks CAPO but 0.5% deviation → ~0.4% profit at 77% LLTV, non-atomic, marginal
- Moonwell exploit ($1M) was oracle MALFUNCTION, not deviation arbitrage
- ezETH April 2024 depeg: market event, not oracle manipulation

### Balancer V2 Forks — NOT EXPLOITABLE ON MAINNET
- $128M exploit (Nov 2025): rounding in `_upscale()` ComposableStablePool with rate providers
- Ethereum mainnet: CSPv6 pools PAUSED, CSPv5 DRAINED, all factories DISABLED
- No unpatched Balancer V2 fork on Ethereum mainnet (forks affected: Beets, BEX, other L1s)
- Aura/Gyroscope/Swaap: not vulnerable (different pool types or wrapper-only)

### Euler V2 + EulerSwap — LOW ATTACK SURFACE
- $4M security spend, 45+ audits, Certora formal verification, $3.5M CTF
- EulerSwap: JIT borrowing, single-LP pools, acknowledged `calcLimits()` double-counting (ChainSecurity)
- Cool-off period prevents same-block flash loan attacks when set > 0
- Bug bounty: $7.5M (Cantina) — $1M+ for high severity
- TVL: ~$533M (Euler V2), EulerSwap relatively small
- No immediately exploitable surface identified

### Morpho Oracle Misconfiguration — PATTERN CONFIRMED, NO LIVE TARGET FOUND
- PAXG/USDC ($230K, Oct 2024): SCALE_FACTOR off by 10^12 due to wrong decimals
- Steakhouse wstETH/wM: decimal error, disclosed by whitehat before exploit
- Aerodrome cUSDO/USDC ($49K, May 2025): custom LP oracle manipulation on Base
- Safeguards added: Oracle Tester tool, interface warnings, MetaOracleDeviationTimelock
- Recent market scan (71 markets, last 30 days): no obviously misconfigured oracles with significant liquidity
- Most interesting: srRoyUSDC/USDC ($31K, pure convertToAssets), xPRISM/USDC (donation-sensitive) — all too small or blocked by LLTV economics

### Vault Oracle Deep Dive (recent markets with HAS_VAULT + NO_FEEDS):
| Market | Oracle Pattern | Vault TVL | Morpho Supply | Viable? |
|--------|---------------|-----------|---------------|---------|
| srRoyUSDC/USDC | pure convertToAssets | $6.7M | $31K | NO — TVL too large for donation |
| xPRISM/USDC | pure convertToAssets, donation-sensitive | $5M | $1 | NO — no supply |
| WOUSD/USDC | pure convertToAssets, donation-sensitive | $517K | $1 | NO — no supply |

## Solvency Equation (Morpho Blue)
totalSupplyAssets >= totalBorrowAssets + badDebt
Violated when: oracle reads manipulated exchange rate → bad debt via over-borrowing

## Last Experiment
- Scanned 71 recently created Morpho markets for novel collateral and oracle configs
- Deep-dived 9 interesting oracles (vault-based, custom, high-LLTV)
- Result: No live misconfigured oracle with exploitable liquidity found
- Belief change: Morpho's oracle ecosystem has matured significantly since PAXG; curated vaults filter effectively

## Next Discriminator
- **Fluid Protocol**: Unified lending+DEX — check if shared liquidity creates composition vulnerability
- **Cross-protocol oracle disagreement**: Check if same asset priced differently across protocols enabling arbitrage
- **New protocol launches**: Monitor for low-TVL, under-audited protocols on mainnet

## Open Unknowns
- Fluid Protocol architecture and attack surface (agent still running)
- Whether any unscanned Morpho market (of 1216 total) has a live misconfiguration
- EulerSwap `calcLimits()` double-counting: acknowledged but impact unquantified
