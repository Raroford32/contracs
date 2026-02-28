# Memory (bridge-finality-gap)

## Pinned Reality
- chain_id: 1 (Ethereum Mainnet)
- fork_block: 24539674 (pinned 2026-02-26)
- discriminator_block: ~24554053 (live 2026-02-28)
- attacker_tier: permissionless (flash loan capable)
- capital_model: flash loans from Aave V3 / Morpho Blue (0% fee)

## Phase 1: Bridge Protocols — COMPLETE, SUB-E3

**Across Protocol (HC-1):** All 5 vectors confirmed. All alternative paths blocked. L2 finality gap is sole remaining vector. DESIGN RISK — not immediately actionable. See notes/composition-hypotheses.md.

**Celer/Synapse/Hop:** Deprioritized (well-designed or weakened by 0 signer-voter overlap).

## Phase 2: DeFi Composition Survey — COMPLETE

Pivoted per user directive to find immediately exploitable, permissionless composition drain.

### Survey Results (ranked by composition risk):
1. **Morpho Blue ERC-4626 vault collateral** — Proven pattern (ResupplyFi $9.6M, Venus $4M+)
2. **Pendle PT oracle mispricing** — $4B+ PT on Aave, novel oracle implementations
3. **LRT oracle deviation** — rsETH ~2% Chainlink deviation, Moonwell $1M exploit
4. **Ethena sUSDe cascade** — $5B+ TVL, multiple lending integrations
5. **Euler V2 + EulerSwap JIT** — Novel mechanics, live CTF
6. **Fluid unified lending+DEX** — Novel unified liquidity

## Phase 3: Morpho Blue ERC-4626 Donation Attack — EXHAUSTED

### Architecture Confirmed:
- MorphoChainlinkOracleV2 reads `convertToAssets()` LIVE with **NO growth cap**
- 901 oracle deployments found via factory scan
- Compared to Aave's CAPO (14-day snapshot + yearly growth cap)

### Vault Classification (donation sensitivity):
| Vault | Donation-Sensitive? | TVL | Morpho Borrows | Viable? |
|-------|-------------------|-----|----------------|---------|
| sUSDe | YES (balanceOf - unvested) | $6B | $145M+ | NO — TVL too large |
| siUSD | YES (balanceOf - epoch) | $119M | $73M | NO — TVL too large |
| sNUSD | YES (balanceOf - unvested) | $185M | $9.4M | NO — TVL too large |
| savETH | YES (balanceOf - unvested) | $9.3M | $4.66M | INSIDER ONLY — no avETH liquidity |
| pufETH | YES (stETH.balanceOf) | $62M | $531K | NO — TVL too large |
| sUSDS | NO (SSR rate accumulator) | N/A | $112M | Donation-resistant |
| stUSDS | NO (chi accumulator) | N/A | $44M | Donation-resistant |
| wsrUSD | NO (compoundFactor math) | N/A | $21M | Donation-resistant |
| stcUSD | NO (storedTotal internal) | N/A | $31.5M | Donation-resistant |
| sUSDD | NO (chi/RAY DSR pattern) | N/A | $60.3M | Donation-resistant |

### Kill Chain Economics (WHY collateral-side donation fails):
```
profit = A*(T+A+D)/(T+A)*LLTV - A - D
Since LLTV < 1: derivative d(profit)/dD = A*LLTV/(T+A) - 1 < 0 always
→ Donation ALWAYS costs more than extra borrow enabled
```

### Loan-side (QUOTE_VAULT) attack: NOT POSSIBLE
- Checked ALL known Morpho oracles — ZERO have QUOTE_VAULT set
- Morpho's explicit warning heeded: no vault tokens as loan assets

### savETH/WETH Design Vulnerability (confirmed but not permissionless):
- Oracle: pure convertToAssets(), NO Chainlink feeds, NO cap
- totalAssets = balanceOf() (confirmed via bytecode + on-chain match)
- avETH: 25 holders, no DEX pairs, controlled minting
- Available borrow: only 127 WETH ($457K)
- **Insider risk only** — not externally exploitable

### Evidence:
- notes/morpho-erc4626-analysis.md
- notes/morpho-oracle-scan.json
- scripts/morpho_market_scanner.py

## Solvency Equation (Morpho Blue)
For any market: totalSupplyAssets >= totalBorrowAssets + badDebt
Violated when: oracle reads manipulated exchange rate → bad debt created via over-borrowing

## Last Experiment
- Scanned 901 MorphoChainlinkOracleV2 oracles for vault references
- Verified totalAssets() implementation of 10+ vault tokens on-chain
- Checked QUOTE_VAULT on all known oracles (all zero)
- Result: ERC-4626 donation attack on Morpho Blue is NOT viable for permissionless external attackers
- Belief change: Collateral-side donation is fundamentally blocked by LLTV < 1 economics

## Next Discriminator
- **Pendle PT oracle**: Check if Chaos Labs / RedStone PT oracle can be manipulated via AMM liquidity attacks
- **rsETH oracle**: Check if ~2% Chainlink deviation threshold enables collateral arbitrage on Aave/Morpho
- **Balancer V2 forks**: Check if any unpatched forks exist on Ethereum mainnet with the Nov 2025 rounding bug
