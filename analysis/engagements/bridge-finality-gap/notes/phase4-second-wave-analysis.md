# Phase 4: Second Wave Analysis — Pendle PT, LRT Oracle, Balancer V2, Euler V2, Morpho Misconfig

## Date: 2026-02-28
## Chain: Ethereum Mainnet (block ~24554258)

## Summary

All six investigation targets from Phase 2 survey have been exhausted. None present an immediately exploitable, permissionless drain on Ethereum mainnet.

---

## 1. Pendle PT Oracle Mispricing — NOT EXPLOITABLE

### Oracle Types (3 distinct approaches):

**A. Aave PendlePriceCapAdapter (BGD Labs)**
- Deterministic linear discount: `price = underlying_price * (1 - discount_rate * time_to_maturity)`
- Does NOT read Pendle AMM data at all
- Growth capped by CAPO mechanism
- Killswitch: LTV → 0 when AMM reaches 96% PT concentration
- **Cannot be manipulated via flash loans or AMM manipulation**

**B. Morpho SparkLinearDiscountOracle**
- Also deterministic: `baseDiscountPerYear` set at market creation
- No market data input whatsoever
- Configuration risk only: if discount rate set too low, overvalues PT during yield spikes
- **Cannot be manipulated**

**C. Pendle AMM 15-min TWAP**
- Used by some Morpho curators (Steakhouse)
- Geometric mean in log-space, single block contributes ~1.3% weight
- Dynamic fees scale with rate impact
- Multi-block manipulation: requires sustained capital across ~75 blocks + validator control
- Cost: tens of millions for deep pools, cheaper for thin pools
- **Theoretically possible but requires builder/validator tier, not permissionless**

### On-Chain Scan Results:
- 60+ PT markets on Morpho (scanned all 1216 markets)
- Largest: PT-USDe/DAI ($70K supply), PT-sUSDE/DAI ($30K supply)
- ALL PT markets have negligible liquidity
- Even with perfect oracle manipulation, extraction is <$100K

---

## 2. LRT Oracle Deviation Arbitrage — NOT EXPLOITABLE

### rsETH Chainlink Feed:
- Address: 0x03c68933f7a3F76875C0bc670a58e69294cDFD01
- Deviation threshold: **0.5%** (not 2% as initially estimated)
- Heartbeat: 24 hours
- Feed type: Reference Price (market rate, not exchange rate)

### Aave Protection:
- CAPO adapter caps exchange rate growth to ~9.83%/year
- Reads on-chain exchange rate, NOT market price
- MINIMUM_SNAPSHOT_DELAY: 14 days

### Morpho Risk:
- rsETH/USDA market: 77% LLTV, Redstone feed with 1% deviation
- Maximum extractable: ~0.77% per $1M deployed, non-atomic
- Not profitable after gas and timing risk

### Moonwell Exploit Context:
- Was oracle MALFUNCTION ($5.8M/token instead of $3.5K), not deviation arbitrage
- On Base/Optimism, not Ethereum mainnet
- Moonwell had zero price sanity checks

### ezETH Depeg (April 2024):
- Liquidity crisis, not oracle manipulation
- $65M+ liquidations across protocols
- Demonstrated oracle design tradeoff (market rate vs exchange rate)

---

## 3. Balancer V2 Rounding Exploit — NOT EXPLOITABLE ON MAINNET

### The Vulnerability:
- `_upscale()` always uses `mulDown` instead of `mulUp`
- With non-unitary scaling factors (rate providers like wstETH/ETH), creates precision loss
- Amplified by ComposableStablePool's BPT-as-token design
- Exploited via 65-iteration batchSwap cycle draining pool to sub-100K wei

### Ethereum Mainnet Status:
- CSPv6 pools: PAUSED by Hypernative within 20 minutes
- CSPv5 pools: expired pause windows, ALREADY DRAINED during exploit
- All factories: DISABLED
- Remaining V2 TVL in Weighted/Gyro pools (not affected)

### Forks on Mainnet:
- Aura Finance: Convex-style wrapper, NOT a pool fork
- Gyroscope: Custom E-CLP pools, NOT ComposableStablePool
- Swaap: Different pool math
- **No unpatched ComposableStablePool on Ethereum mainnet**

---

## 4. Euler V2 + EulerSwap — LOW ATTACK SURFACE

### Security Posture:
- ~$4M security spend
- 45+ audits from 13 firms
- Certora formal verification (Holy Grail property: accounts stay healthy)
- $1.25M Cantina competition: no high/medium findings
- $3.5M live CTF: no funds compromised
- $7.5M bug bounty active

### EulerSwap Specifics:
- Single-LP pools, JIT borrowing from Euler V2 vaults
- ChainSecurity acknowledged findings:
  1. `calcLimits()` double-counting LP's vault balance
  2. Rounding imprecision in deposit/withdraw
- $500K live CTF: no funds compromised
- Cool-off period prevents same-block flash loan attacks

### Remaining Theoretical Surface:
- Cool-off period = 0 vaults (governor responsibility)
- ERC-4626 `convertToAssets()` resolution in EulerRouter (same donation risk)
- L2 oracle manipulation on FIFO chains (not Ethereum mainnet)
- JIT borrow cascade under extreme volatility

---

## 5. Morpho Oracle Misconfiguration — PATTERN CONFIRMED, NO LIVE TARGET

### Proven Precedents:
- PAXG/USDC ($230K, Oct 2024): SCALE_FACTOR off by 10^12
- wstETH/wM, WBTC/wM (Oct 2024): decimal errors, whitehat disclosure
- Aerodrome cUSDO/USDC ($49K, May 2025): custom LP oracle on Base

### Current Safeguards:
- Oracle Tester pre-deployment tool
- Interface warnings (red/yellow/blacklist)
- MetaOracleDeviationTimelock (Steakhouse, June 2025)
- Vault V2 fixes faulty-oracle edge case

### Our Scan Results:
- 71 markets created in last 30 days analyzed
- 44 have supply > 0
- 9 oracles deep-dived (vault-based, custom, high-LLTV)
- No obviously misconfigured oracle with exploitable liquidity found
- Notable: Several HAS_VAULT + NO_FEEDS oracles exist but underlying vaults are large ($500K-$6.7M TVL)

---

## Kill Chain Economics Summary

Every oracle-based attack on Morpho Blue hits the same wall:

**Collateral-side inflation** (donation, rate manipulation):
```
profit = deposit * inflated_rate * LLTV - deposit - manipulation_cost
Since LLTV < 1: manipulation_cost always exceeds profit gain
```

**Loan-side inflation** (Venus pattern):
```
No Morpho market has QUOTE_VAULT set. Vector does not exist.
```

**Oracle misconfiguration** (PAXG pattern):
```
Requires a live market with wrong SCALE_FACTOR AND sufficient liquidity.
No such market found among 1216 scanned.
```

**AMM-based oracle manipulation** (TWAP):
```
15-min TWAP + concentrated liquidity + dynamic fees →
requires multi-block validator control (not permissionless)
```

---

## Conclusion

After exhaustive analysis of 6 composition targets across 1216+ Morpho markets, 901 oracles, 60+ PT markets, and multiple lending protocols:

**No immediately exploitable, permissionless composition vulnerability exists on Ethereum mainnet** in the investigated protocols (Morpho Blue, Aave V3, Pendle, Euler V2/EulerSwap, Balancer V2).

The DeFi ecosystem's defense layers are effective:
1. **Aave CAPO**: Blocks exchange rate manipulation at the oracle level
2. **Morpho economics**: LLTV < 1 makes collateral-side donation unprofitable
3. **Pendle deterministic oracles**: Removes AMM manipulation surface
4. **Balancer patch/pause**: Eliminates rounding attack on mainnet
5. **Euler formal verification**: Proves core invariant holds
