# Phase 7: L2 Chain Lending Protocol Security Scan

## Objective
Scan lending protocols across L2 chains (Base, Arbitrum, ZKsync Era, Optimism) for exploitable oracle misconfigurations, focusing on:
- ERC-4626 vault donation attack vectors (Venus wUSDM pattern)
- Oracle feed mismatches (wrong feed for wrong token)
- Stale oracle feeds on active markets
- Zombie protocols with residual TVL and weak protections
- Fresh/unaudited deployments

## Background: Venus wUSDM Pattern (Feb 2025)
A serial attacker exploited Venus Protocol on ZKsync Era for $716K by:
1. Flash loaning USDM
2. Donating to the wUSDM vault to inflate `totalAssets/totalSupply` exchange rate (1.06 → 1.76)
3. Borrowing against inflated collateral value
4. Self-liquidating for profit

This pattern affects ANY lending protocol using ERC-4626 vault tokens as collateral where the oracle reads the vault's exchange rate directly without rate-of-change caps.

## Results by Protocol

### Moonwell (Base) — $90M TVL — CLEAN
- 20 markets identified and verified
- Initial scan flagged 7 markets as "EXTREME MISPRICE" — ALL FALSE POSITIVES
- Root cause: Compound V2 oracle convention stores price as `price * 1e(36 - underlyingDecimals)`
  - USDC (6 dec): raw price 999,940,000,000,000,000,000,000,000,000 = $0.9999 ✓
  - cbXRP (6 dec): raw 1,292,715,000,000,000,000,000,000,000,000 = $1.29 ✓
  - LBTC (8 dec): raw 641,249,940,842,846,926,956,000,000,000,000 = $64,125 ✓
- Markets with `underlying()` reverting are "native token" markets (newer contract pattern, 10873 bytes vs 7544 bytes for older), NOT oracle misconfigurations
- No ERC-4626 vault tokens used as collateral
- Previous exploit (Feb 2026, $1.78M): cbETH OEV wrapper misconfiguration — already patched

### Seamless Protocol (Base) — DEAD
- All 18 reserves FROZEN with $0 prices
- Fully migrated to Morpho vaults
- No attack surface

### Aave V3 (Base) — $300M+ TVL — CLEAN
- 15 reserves active
- Vault-like tokens (cbETH, ezETH) protected by CAPO (Correlated Asset Price Oracle)
  - Rate-of-change caps prevent sudden exchange rate inflation
  - Snapshot ratio + max yearly growth percent enforced
- No direct ERC-4626 vault collateral (tokens use different wrapper patterns)
- Oracle sources verified for key markets

### Dolomite (Arbitrum) — $800M TVL — CLEAN
- 75 markets enumerated via `DolomiteMargin.getNumMarkets()`
- Only ERC-4626 vault found: mGLP (Market #8) — status: CLOSING with $0 value
- All active markets (WETH $4.3M, WBTC $13.2M, USDC $5.4M) use standard Chainlink oracles
- No exploitable ERC-4626 exposure

### ZeroLend (ZKsync Era) — $838K TVL — CLEAN
- 21 reserves checked with Aave V3 config bitmap decoding
- Active markets use Pyth network feeds wrapped in Chainlink aggregator interfaces
  - USDC.e ($99K): 2.3h staleness — within normal Pyth heartbeat ✓
  - WETH ($443K): 0.2h staleness ✓
  - ZK ($106K): 1.3h staleness ✓
- Dead/stale oracle markets ALL have protections:
  - PEPE (16,356h stale): FROZEN, borrow disabled
  - SWORD (492,300h stale): FROZEN, borrow disabled
  - VC (492,300h stale): FROZEN, borrow disabled
  - wUSDM: PAUSED + FROZEN, $28 liquidity only
- wUSDM oracle described as "Capped USDT/USD" — feed mismatch flagged but market is paused+frozen with negligible liquidity

### ReactorFusion (ZKsync Era) — $479K TVL — CLEAN
- 6 markets, all oracle prices within expected ranges
- No anomalies detected

### Morpho Blue (Base) — $1B+ TVL — INCOMPLETE
- ChainlinkOracleV2Factory: 0 new oracle deployments in last 60 days
- CreateMarket event scan: incomplete due to public Base RPC rate limiting
- Architecture uses `baseVault/quoteVault` parameters that can directly read ERC-4626 exchange rates
- This remains the most interesting target but requires paid RPC access for complete scanning
- Known protection: Morpho's Yield Risk Engine provides curator-level rate monitoring

### Fresh Lending Deployments (All L2s)
- Arbitrum: 0 new lending protocol deployments in last 7 days
- ZKsync: 0 new lending deployments in last 7 days
- Base/Optimism: Scan incomplete (RPC payload size limits)

## Protection Mechanisms Observed

| Protocol | Protection Against ERC-4626 Donation | Status |
|---|---|---|
| Aave V3 | CAPO (rate-of-change caps per vault) | Well protected |
| Gearbox | Bounded min/max oracle ranges | Well protected |
| Euler EVK | Internal balance tracking + virtual deposits | Well protected |
| Morpho Blue | Yield Risk Engine (curator monitoring) | Partial — "most vaults vulnerable" per docs |
| Silo V2 | Virtual shares for own vaults | Partial — external vaults may not be |
| Moonwell | No vault collateral | N/A — no exposure |
| Dolomite | No active vault collateral | N/A — no exposure |
| ZeroLend | wUSDM frozen | Mitigated post-exploit |

## Serial Attacker Profile (Active Feb 2026)
A serial attacker has been linked to at least 4 exploits:
- Moonwell ($1.78M, cbETH OEV wrapper, AI-co-authored code)
- Ploutos ($388K, BTC/USD feed misconfigured for USDC)
- MakinaFi ($4.13M, Jan 2026)
- Venus ($716K, wUSDM donation attack)

Pattern: targets fresh deployments and governance proposals within blocks of creation. Exploits oracle misconfigurations, not complex DeFi composition.

## Conclusion
No immediately exploitable oracle misconfiguration found across scanned L2 lending protocols. The ERC-4626 donation attack vector has been widely recognized and mitigated since the Venus incident. Active protocols either:
1. Don't use ERC-4626 vault tokens as collateral
2. Have rate-of-change caps (CAPO) protecting vault exchange rates
3. Have frozen/paused vulnerable markets post-incident

The remaining open target is Morpho Blue on Base ($1B+), which requires paid RPC access for complete market enumeration. Its `baseVault/quoteVault` oracle architecture directly reads ERC-4626 exchange rates and is the most likely vector for a donation-style attack in the current DeFi landscape.
