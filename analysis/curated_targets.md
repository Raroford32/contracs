# Curated High-Value DeFi Targets for Deep Analysis

Generated: 2026-02-15
Source: contracts.txt lines 200-1568 (1369 addresses scanned)
Filter: verified source, >$500K in ETH/WETH/USDC/USDT/DAI, not previously analyzed

## Tier 1: Highest Priority (Custom DeFi Logic + Significant Holdings)

### 1. RollupProcessor (Aztec) - $3.28M
- **Address:** `0x737901bea3eeb88459df9ef1be8ff3ae1b42a2ba`
- **Holdings:** 1,158.8 ETH, 150K DAI, USDT
- **Why interesting:** Aztec Connect rollup processor - bridge between L1 and private L2. Complex deposit/withdrawal logic, proof verification, bridge interactions. Custom rollup settlement logic with privacy features.
- **Attack surface:** Bridge logic, proof verification bypass, deposit/withdrawal accounting, rollup state manipulation.

### 2. CollateralJoin1 (MakerDAO) - $3.01M
- **Address:** `0x2d3cd7b81c93f188f3cb8ad87c8acc73d6226e3a`
- **Holdings:** 1,115.3 WETH
- **Why interesting:** MakerDAO collateral adapter - handles WETH deposits into the Maker system. Core piece of CDP infrastructure.
- **Attack surface:** Join/exit accounting, collateral ratio manipulation, interaction with Vat.

### 3. PerpetualProxy (dYdX Perpetual) - $1.89M [PROXY]
- **Address:** `0x09403fd14510f8196f7879ef514827cd76960b5d`
- **Implementation:** `0xe883b3ef`
- **Holdings:** 698.3 WETH
- **Why interesting:** Perpetual futures protocol with margin trading. Complex liquidation logic, funding rate calculations, position management through proxy.
- **Attack surface:** Margin calculation, liquidation thresholds, funding rate manipulation, proxy upgrade path.

### 4. CrossProxy (Nerve/Cross-chain) - $1.75M [PROXY]
- **Address:** `0xfceaaaeb8d564a9d0e71ef36f027b9d162bc334e`
- **Implementation:** `0x8f8165fc`
- **Holdings:** 1.19M USDC, 537K USDT
- **Why interesting:** Cross-chain bridge proxy with substantial stablecoin holdings. Bridge logic is a high-value attack surface.
- **Attack surface:** Cross-chain message verification, deposit/withdrawal matching, proxy upgrade authority.

### 5. yVault (Yearn) - $1.34M
- **Address:** `0xe1237aa7f535b0cc33fd973d66cbf830354d16c7`
- **Holdings:** 495.9 WETH
- **Why interesting:** Yearn vault with custom yield strategy. ERC4626-like accounting with strategy interactions.
- **Attack surface:** Share price manipulation, strategy interaction, deposit/withdrawal rounding, donation attacks.

### 6. LiquidityPoolV2 (Kyber/Custom) - $1.29M
- **Address:** `0x35ffd6e268610e764ff6944d07760d0efe5e40e5`
- **Holdings:** 413.1 ETH, 64K USDC, 77K DAI, 13.3 WETH
- **Why interesting:** Custom liquidity pool with V2 designation suggesting protocol evolution. Multi-asset pool.
- **Attack surface:** Pool invariant, swap calculations, liquidity provision/removal edge cases, fee accounting.

### 7. Router [PROXY] - $1.20M
- **Address:** `0x367e59b559283c8506207d75b0c5d8c66c4cd4b7`
- **Implementation:** `0xf9fe4275`
- **Holdings:** 91.2 WETH, 721K USDC, 222K USDT, 7K DAI
- **Why interesting:** DeFi router proxy holding significant multi-token balances. Routers with residual balances suggest token approval / sweep issues.
- **Attack surface:** Token approval exploitation, sweep functions, routing logic bypass, proxy upgrade.

### 8. MoneyMarket (Compound V1-era) - $1.15M
- **Address:** `0x3fda67f7583380e67ef93072294a7fac882fd7e7`
- **Holdings:** 426.6 WETH
- **Why interesting:** Early money market protocol. Older Solidity, potentially less battle-tested accounting.
- **Attack surface:** Interest rate model, liquidation logic, supply/borrow accounting, oracle dependency.

### 9. MarginPool (dYdX/Custom) - $1.15M
- **Address:** `0x5934807cc0654d46755ebd2848840b616256c6ef`
- **Holdings:** 418.0 WETH, 19.9K USDC
- **Why interesting:** Margin trading pool with leveraged position management. Complex accounting.
- **Attack surface:** Margin requirements, position liquidation, interest accrual, cross-collateral interaction.

### 10. BatchExchange [PROXY] (Gnosis Protocol v1) - $794K
- **Address:** `0x6f400810b62df8e13fded51be75ff5393eaa841f`
- **Implementation:** `0xed4d0549`
- **Holdings:** 170.9 WETH, 294K USDC, 12K USDT, 26K DAI
- **Why interesting:** Batch auction exchange with solver-based order matching. Complex batch settlement logic.
- **Attack surface:** Batch settlement accounting, solver manipulation, order matching edge cases, token approval model.

## Tier 2: High Priority (Interesting Logic + Moderate Holdings)

### 11. CEther (Compound fork) - $847K
- **Address:** `0x7b4a7fd41c688a7cb116534e341e44126ef5a0fd`
- **Holdings:** 313.7 ETH
- **Why interesting:** Compound-style ETH lending token. Exchange rate manipulation, liquidation edge cases.

### 12. fETH - $1.09M
- **Address:** `0xf786c34106762ab4eeb45a51b42a62470e9d5332`
- **Holdings:** 404.1 ETH
- **Why interesting:** Fractional/wrapped ETH with deposit logic. Share accounting vulnerabilities.

### 13. ArbitrageETHStaking - $584K
- **Address:** `0x5eee354e36ac51e9d3f7283005cab0c55f423b23`
- **Holdings:** 216.3 ETH
- **Why interesting:** Arbitrage + staking combination. Novel mechanism combining two DeFi primitives.

### 14. BondedECDSAKeepFactory (Keep Network) - $698K
- **Address:** `0xa7d9e842efb252389d613da88eda3731512e40bd`
- **Holdings:** 258.6 ETH
- **Why interesting:** ECDSA keep factory for tBTC. Bond management, keep creation, slashing logic.

### 15. KyberReserve - $532K
- **Address:** `0x9149c59f087e891b659481ed665768a57247c79e`
- **Holdings:** Custom reserve with deposit/pricing logic.

### 16. CycloneV2dot2 - $540K
- **Address:** `0xd619c8da0a58b63be7fa69b4cc648916fe95fa1b`
- **Holdings:** 200 ETH
- **Why interesting:** Privacy mixer v2.2. Merkle tree, nullifier, proof verification. Tornado Cash variant.

### 17. WorkLock (NuCypher) - $786K
- **Address:** `0xe9778e69a961e64d3cdbb34cf6778281d34667c2`
- **Holdings:** 291.2 ETH
- **Why interesting:** Work-based token distribution mechanism. Escrow + vesting + work verification.

## Tier 3: Unclassified High-Value (Needs Manual Review)

### 18. DerivaDEX [PROXY] - $706K
- **Address:** `0x6fb8aa6fc6f27e591423009194529ae126660027`
- **Holdings:** 459K USDC, 246K USDT
- **Why interesting:** Derivatives DEX with proxy pattern. Substantial stablecoin holdings.

### 19. Root [PROXY] - $669K
- **Address:** `0xe5c405c5578d84c5231d3a9a29ef4374423fa0c2`
- **Holdings:** 85K USDC, 435K USDT, 147K DAI
- **Why interesting:** Root proxy with significant multi-stablecoin holdings. Unknown protocol, needs source review.

### 20. L1_ERC20_Bridge - $538K
- **Address:** `0x3666f603cc164936c1b87e207f36beba4ac5f18a`
- **Holdings:** 538K USDC
- **Why interesting:** L1 ERC20 bridge, cross-domain token handling.

## Selection Criteria for Deep Analysis

**Best candidates for deep security analysis** (ranked by: custom logic complexity * holdings * novelty):

1. **RollupProcessor** - Aztec rollup settlement with privacy proofs. Unique logic, high value.
2. **CrossProxy** - Cross-chain bridge with $1.75M stablecoins. Bridge bugs are highest severity.
3. **PerpetualProxy** - Perpetual futures with margin/liquidation. Complex financial math.
4. **LiquidityPoolV2** - Multi-asset pool with custom invariant. DEX logic with $1.29M.
5. **yVault** - Vault accounting with strategy interactions. Classic ERC4626 attack surface.
6. **Router [PROXY]** - $1.2M residual balances in a router. Potential sweep/approval issues.
7. **BatchExchange [PROXY]** - Batch auction settlement logic. Solver-based, complex ordering.
8. **MoneyMarket** - Early money market, potentially older/weaker accounting patterns.
9. **fETH** - Custom fractional ETH with $1.09M. Share price manipulation potential.
10. **DerivaDEX [PROXY]** - Derivatives exchange, complex financial logic.

