# Phase 8: Novel Multi-Vector Composition Attack Surface Analysis

## Methodology Shift
Previous phases scanned for known vulnerability patterns (oracle misconfigs, ERC-4626 donation, staleness).
This phase pivots to deep economic reasoning about NOVEL multi-vector composition attacks — vulnerabilities that exist ONLY in the interaction between multiple protocols.

## Research Intelligence

### Novel 2025-2026 Exploit Patterns
| Exploit | Date | Loss | Novel Mechanism |
|---|---|---|---|
| Balancer V2 Rounding Cascade | Nov 2025 | $128M | Drain pool to wei-level → 65+ micro-swaps compounding rounding error → BPT underpriced. Required creating artificial boundary conditions FIRST. |
| Cork Protocol (Uni V4 Hook) | May 2025 | $12M | Direct external call to hook bypassing PoolManager → injected custom hook data → fake derivatives |
| Bunni (Uni V4 Hook) | Sep 2025 | $8.4M | Rounding error in withdrawal + flash loan amplification within V4 hook |
| 1inch Fusion (Intent/Solver) | Mar 2025 | $5M | Calldata buffer overflow corrupted settlement function — traditional heap exploitation in smart contract |
| Venus wUSDM (Vault Composition) | Feb 2025 | $717K | Flash donate to ERC-4626 vault → inflated exchange rate → overborrow on lending protocol |

### Key Insight: "Assumption Gap Exploitation"
Protocol A assumes X about Protocol B, but Protocol B only guarantees Y. The gap between guarantee and assumption is where novel vulnerabilities live.

## Composition Attack Surface Map (Base Chain)

### 1. Shared Collateral Tokens Across Protocols
The same LRT tokens (weETH, cbETH, wstETH) serve as collateral in Aave V3, Morpho Blue, AND Moonwell simultaneously on Base. Cascading liquidation events would hit all protocols at once, routing through the same Aerodrome/Uniswap pools.

**Oracle pricing verified across protocols (current block):**
| Token | Aave V3 | Moonwell | Difference |
|---|---|---|---|
| weETH | $2,237.48 | $2,235.17 | 0.10% |
| cbETH | $2,309.31 | $2,307.90 | 0.06% |
| wrsETH | $2,189.72 | $2,189.72 | 0.00% |

During normal conditions, prices agree within 0.1%. CAPO limits upside, not downside. Downside tracking depends on the base Chainlink feed.

**Verdict: Known risk, mitigated by CAPO design. Not a novel exploitable vector.**

### 2. Governance Token Dual-Roles
Flash-loan governance mitigated: AERO requires 4-year veAERO lock, WELL uses snapshot-based voting, MORPHO is owner-controlled.

**Verdict: Not exploitable due to mitigations.**

### 3. Aerodrome as Shared Liquidation Route
All Base lending protocols route liquidations through same DEX pools. Depth determines cascading liquidation success.

### 4. MetaMorpho Vault Composition (Reflexive Loop Check)
**On-chain verification (Ethereum mainnet):** Checked all 132 Morpho Blue markets with >$100K borrow.
- Only 1 MetaMorpho vault token used as collateral: aMUSD/USDC ($228K borrow, negligible)
- **No reflexive loops detected** (direct or 2-hop)
- **No MetaMorpho vault lends into a market where its own token is collateral**

**Verdict: Reflexive loop architecture exists but not currently instantiated. Too small to exploit.**

---

## Deep Investigation: Pendle PT Oracle Architecture on Morpho Blue

### PT Markets Overview (14 with >$100K borrow)

| Market | Supply | Borrow | Oracle Type | Maturity |
|---|---|---|---|---|
| PT-reUSD-25JUN2026/USDC | $47.7M | $43.0M | MorphoChainlinkOracleV2 | Jun 25, 2026 |
| PT-srUSDe-2APR2026/USDC | $14.3M | $12.1M | MetaOracleDeviationTimelock (9517b impl) | Apr 2, 2026 |
| PT-sNUSD-5MAR2026/USDC | $7.3M | $6.6M | MetaOracleDeviationTimelock (6166b impl) | Mar 5, 2026 |
| PT-cUSD-23JUL2026/USDC | $2.4M | $2.0M | MorphoChainlinkOracleV2 | Jul 23, 2026 |
| PT-siUSD-26MAR2026/USDC | $1.9M | $1.6M | MorphoChainlinkOracleV2 | Mar 26, 2026 |
| PT-stcUSD-23JUL2026/USDC | $1.8M | $1.6M | MorphoChainlinkOracleV2 | Jul 23, 2026 |

### Oracle Architecture Discovery: MetaOracleDeviationTimelock (Steakhouse Financial)

**Contract identification:** The 45-byte EIP-1167 minimal proxies used by PT-sNUSD and PT-srUSDe oracles delegate to `MetaOracleDeviationTimelock` by Steakhouse Financial (Solidity v0.8.28, Cantina audited).

**Three-layer oracle stack:**
```
Layer 0: EIP-1167 Proxy (45 bytes)
  → Layer 1: MetaOracleDeviationTimelock (6166 bytes impl)
      ├── primaryOracle: MorphoChainlinkOracleV2 (2598 bytes)
      │   └── BASE_FEED_1: PendleChainlinkOracle adapter
      │       └── reads Pendle AMM TWAP (PT-to-asset geometric mean)
      │   └── (assumes underlying stablecoin = 1:1 with loan token)
      └── backupOracle: OracleRouter (1888 bytes, owner-upgradeable)
          └── MorphoChainlinkOracleV2 with:
              └── BASE_FEED_1: PendleChainlinkOracle (TWAP)
              └── BASE_FEED_2: Chainlink underlying/USD (depeg protection)
```

### MetaOracleDeviationTimelock State Machine

| Parameter | PT-sNUSD | PT-srUSDe |
|---|---|---|
| Challenge timelock | 4 hours | 16 hours |
| Healing timelock | 12 hours | 24 hours |
| Deviation threshold | 1.00% | 0.75% |
| Current state | isPrimary = true | isPrimary = true |
| Primary price | 0.99973 | 0.99658 |
| Backup price | 0.99973 | 0.99630 |
| Price divergence | ~0% | 0.028% |

**How it works:**
1. Normal: Uses primary oracle (Pendle TWAP, assumes stablecoin at par)
2. If `|primary - backup| / average > threshold` for `challengeTimelock`: permissionless switch to backup
3. Backup includes Chainlink underlying/USD feed for depeg protection
4. If prices reconverge for `healingTimelock`: permissionless switch back to primary
5. On revert from current oracle: automatic fallback to other oracle

### PT-sNUSD-5MAR2026 Maturity Analysis

**Current state (March 4, 2026 ~12:20 UTC):**
- PT token: `0x54Bf2659B5CdFd86b75920e93C0844c0364F5166`
- Symbol: PT-sNUSD-5MAR2026
- isExpired: false (not yet expired)
- Total supply: 71,823,016 tokens
- Oracle price: 0.99973 (only 0.027% discount from par)

**Underlying PendleChainlinkOracle feed:**
- Address: `0xe488ee19e06eb9d5fef39b076682d959db87168b` (951 bytes)
- Decimals: 18
- latestAnswer: 0.999734 * 1e18
- roundId: 0, updatedAt: 0 (placeholder values — Pendle adapter returns these)

**Maturity behavior (from Pendle V2 docs + code analysis):**
1. At maturity, Pendle's `market.observe()` returns fixed rate → TWAP converges to 1.0
2. PT becomes redeemable 1:1 for underlying (via SY, adjusted by PY index)
3. MetaOracleDeviationTimelock has NO maturity awareness — just monitors deviation
4. Post-maturity: both oracles agree (PT = underlying = 1:1), deviation drops to ~0
5. If Pendle TWAP has issues post-maturity → try/catch fallback to backup oracle

### Multi-Vector Attack Hypothesis: FALSIFIED

**Original hypothesis:** At/near PT maturity, oracle discontinuity + liquidity drain + TWAP manipulation creates extractable value.

**Why it fails:**

1. **No discontinuity:** Pendle TWAP smoothly converges to 1.0 at maturity. No sudden jump.

2. **Max discount cap:** The 1% cap means oracle can never show PT below 99% of underlying. Near maturity, actual discount is 0.027%, well within cap. Downward manipulation is bounded.

3. **Primary/backup failover:** MetaOracleDeviationTimelock automatically switches if primary TWAP deviates from backup (which includes Chainlink feed). 4-hour challenge window prevents flash manipulation.

4. **Oracle revert protection:** `price()` uses try/catch — if current oracle reverts, automatically uses the other. Post-maturity staleness triggers graceful fallback.

5. **Small extraction window:** With PT at 0.99973, there's only 0.027% of "room" to overvalue. On $6.5M borrow, that's ~$1,755 theoretical maximum — not economically viable after gas and flash loan costs.

6. **Pendle AMM design:** Near maturity, the AMM curve naturally concentrates liquidity around par value, making manipulation MORE expensive, not less (contrary to naive assumption about "liquidity draining").

**Verdict: NOT EXPLOITABLE. The MetaOracleDeviationTimelock architecture with PendleChainlinkOracle adapter handles maturity correctly. Steakhouse's multi-oracle design specifically addresses the failure modes we hypothesized.**

### PT-srUSDe-2APR2026 Price Divergence Analysis

The 0.028% divergence between primary (0.99658) and backup (0.99630) prices is explained by:
- Primary: Pendle TWAP × (assumes stablecoin at par)
- Backup: Pendle TWAP × Chainlink underlying/USD feed

The underlying (srUSDe = staked restaked USDe) may have a slight secondary market discount captured by the Chainlink feed but not by the "at par" assumption in the primary oracle. This is the DESIGNED behavior — the backup is more conservative.

---

## Vault Donation Attack Surface (Morpho Ethereum)

### Methodology
Checked 13 largest ERC-4626 vault-collateral markets for donation susceptibility:
`totalAssets ≈ balanceOf(underlying)` → donating underlying inflates exchange rate

### Results
Most vaults use **internal balance tracking** (totalAssets != balanceOf), making donation infeasible:
- sUSDS, stUSDS, sUSDe, weETH: Internal tracking via protocol-specific accounting
- syrupUSDC, syrupUSDT: Maple vault internal tracking
- sdeUSD, wsrUSD, siUSD, stcUSD: Wrapped savings rate with internal tracking

**No exploitable donation vectors found among top vault-collateral markets.**

---

## Summary: Phase 8 Conclusions

### Hypotheses Tested and Results

| Hypothesis | Surface | Result |
|---|---|---|
| PT maturity oracle discontinuity | Pendle × Morpho | FALSIFIED — MetaOracleDeviationTimelock handles smoothly |
| PT TWAP manipulation near maturity | Pendle AMM × Morpho | FALSIFIED — cap + failover + AMM curve design |
| Vault-on-vault reflexive loop | MetaMorpho × Morpho | NOT INSTANTIATED — only 1 tiny vault as collateral |
| Cross-protocol oracle disagreement | Aave × Moonwell (Base) | KNOWN — <0.1% difference, CAPO mitigated |
| Governance token flash-loan attack | Moonwell × Aerodrome | MITIGATED — time-locked voting mechanisms |
| ERC-4626 donation attack | Vault × Morpho | MITIGATED — internal balance tracking |

### Key Architectural Observations

1. **MetaOracleDeviationTimelock** is a sophisticated oracle wrapper that handles many failure modes we hypothesized. Multi-oracle with permissionless state machine is a strong defense.

2. **Pendle's oracle design** converges smoothly at maturity, and the PendleChainlinkOracle adapter provides Chainlink-compatible interface to lending protocols.

3. **The "assumption gap"** between Pendle TWAP oracle and Chainlink underlying feed IS captured by the MetaOracleDeviationTimelock's primary/backup deviation monitoring.

4. **Reflexive vault loops** remain architecturally possible but are not currently instantiated with meaningful TVL on Ethereum mainnet.

### What Would Be Needed for a Novel Attack

The most promising remaining avenues (for future monitoring, not current exploitation):
1. A MetaMorpho vault gaining significant usage as collateral in a market it lends to (reflexive amplification)
2. A new PT market using a simpler oracle (no MetaOracleDeviationTimelock) with significant TVL
3. An underlying stablecoin depeg severe enough to exceed the deviation threshold before the challenge timelock expires (race condition)
4. Cross-chain message/bridge composition with lending protocol state

## Key Sources
- Steakhouse MetaOracleDeviationTimelock: [GitHub](https://github.com/Steakhouse-Financial/steakhouse-oracles), [Cantina audit](https://cantina.xyz/portfolio/715b51f9-d8a3-4a45-8b5e-41654af28c2f)
- [Deep Dive into Pendle Oracles in Lending Markets (Wong's Blog)](https://blog.wssh.dev/posts/pendle-oracle)
- [Pendle PT Oracle Integration](https://docs.pendle.finance/pendle-v2/Developers/Oracles/HowToIntegratePtAndLpOracle)
- [Morpho Community Oracles](https://docs.morpho.org/tools/community/oracles/)
- Morpho docs: "it is not recommended to list any ERC4626 vault as a loan asset"
- OpenZeppelin: ERC-4626's exchange rate risks for collateral usage
