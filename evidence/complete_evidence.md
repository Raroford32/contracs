# Complete Evidence Collection for Attack Chain Design

## Contract: 0xa7569A44f348d3D70d8ad5889e50F78E33d80D35 (Tokemak autoUSD)

**Date:** 2026-02-04
**TVL:** $20,224,182 USDC

---

## SECTION 1: ON-CHAIN STATE EVIDENCE

### 1.1 Contract Addresses (VERIFIED)

| Contract | Address | Role |
|----------|---------|------|
| Proxy | 0xa7569A44f348d3D70d8ad5889e50F78E33d80D35 | User-facing entry point |
| Implementation | 0xfb2ebdedc38a7d19080e44ab1d621bc9afad0695 | AutopoolETH logic |
| Admin (ERC-1967) | 0x84a317a45248d6d3f92f40102680ffeda2ab95c0 | Proxy admin |
| SystemRegistry | 0x2218f90a98b0c070676f249ef44834686daa4285 | Central registry |
| AccessController | 0x37767cbff88cb623e9404e959560984f7d742df6 | RBAC |
| SystemSecurityL1 | 0xe57a2ec5ef4cc7f6576bb1ed5ec3759878f39b20 | Nav operation tracking |
| AutopoolRegistry | 0x7e5828a3a6ae75426d739e798140513a2e2964e4 | Pool registry |

### 1.2 Destination Vaults (VERIFIED)

| Address | Type | Underlying |
|---------|------|------------|
| 0x8aca8accfb69adeff607431e0f25466b7b76a8ad | ERC20DestinationVault | ERC20 tokens |
| 0x7876f91bb22148345b3de16af9448081e9853830 | FluidDestinationVault | Fluid protocol |

### 1.3 Price Oracles (VERIFIED)

| Address | Type | Purpose |
|---------|------|---------|
| 0x792587b191eb0169da6beefa592859b47f0651fe | **BalancerV3StableMathOracle** | LP token pricing |
| 0x5f4ec3df9cbd43714fe2740f5e3616155c5b8419 | Chainlink ETH/USD | Base price |
| 0x8fffffd4afb6115b954bd326cbe7b4ba576818f6 | Chainlink USDC/USD | Base asset price |
| 0xaed0c38402a5d19df6e4c03f4e2dced6e29c1ee9 | Chainlink DAI/USD | Stablecoin price |
| 0x3e7d1eab13ad0104d2750b8863b489d65364e32d | Chainlink USDT/USD | Stablecoin price |

### 1.4 DeFi Protocol Integrations (VERIFIED)

| Address | Protocol | Role |
|---------|----------|------|
| 0xa0b86991c6218b36c1d19d4a2e9eb0ce3606eb48 | USDC Token | Base asset |
| 0x87870bca3f3fd6335c3f4ce8392d69350b4fa4e2 | Aave V3 Pool | Yield source |
| 0xbebc44782c7db0a1a60cb6fe97d0b483032ff1c7 | Curve 3pool | Yield source |
| 0x85b2b559bc2d21104c4defdd6efca8a20343361d | Balancer StablePool | Yield source |

### 1.5 Supporting Libraries (VERIFIED)

| Address | Contract |
|---------|----------|
| 0xd7bd5bcfaf5f3f9c92c430225e81978ef41b59a8 | AutopoolDebt |
| 0x319535b89fa9eb30554045245e6bfdbd486d96d7 | AutopoolStrategyHooks |
| 0x1f11f08aa558f6313e3885a9a1ddb5365148b179 | WithdrawalQueue |
| 0xf85b8eb4e7b2d26b7a72c172d0b7718f9ad4a8c8 | Autopool4626 |

---

## SECTION 2: SOURCE CODE EVIDENCE

### 2.1 Critical Code Patterns Identified

#### Pattern 1: Price Safety Asymmetry
```
Location: AutopoolDebt.sol

FLASH REBALANCE:
  if (!result.pricesWereSafe) {
      revert InvalidPrices();  // REVERTS
  }

DEBT REPORTING:
  result.pricesWereSafe = isSpotSafe;
  // NO REVERT - CONTINUES EXECUTION
```

#### Pattern 2: Documented Attackable Price Function
```
Location: IDestinationVault.sol

/// @notice Get the current value of our held pool shares in terms of the base asset
/// @dev This price can be attacked is not validate to be in any range
/// @return price Value of 1 unit of the underlying LP token in terms of the base asset
function getUnderlyerCeilingPrice() external returns (uint256 price);
```

#### Pattern 3: Three-Tier Valuation System
```
Location: Autopool4626.sol

DEPOSIT: totalIdle + totalDebtMax  (higher value, fewer shares)
WITHDRAW: totalIdle + totalDebtMin (lower value, fewer assets)
GLOBAL: totalIdle + totalDebt (average)
```

#### Pattern 4: 1-Day Staleness Window
```
Location: AutopoolDebt.sol

uint256 public constant MAX_DEBT_REPORT_AGE_SECONDS = 1 days;
```

### 2.2 Flash Rebalance Callback Flow
```
1. SOLVER calls flashRebalance()
2. _handleRebalanceOut() - withdraw from destinationOut
   - Gets prices via getRangePricesLP()
   - Sends assets to receiver
3. receiver.onFlashLoan() - CALLBACK TO SOLVER (ATTACKER CONTROL)
4. _handleRebalanceIn() - deposit to destinationIn
   - Gets NEW prices via getRangePricesLP()
   - pricesWereSafe CHECKED HERE
5. Update debt accounting
```

---

## SECTION 3: TRANSACTION TRACE EVIDENCE

### 3.1 updateDebtReporting Transaction
**Hash:** 0x5cbfa7c6ddc93210c48a44cd872c6942e2ecf3fe4c9def269621c2b3b5d06b7c
**From:** 0x1a65e4844a3af0f1733ee9e1a474dc7db3c396a3
**Function:** updateDebtReporting(uint256)

**Call Statistics:**
- Total calls: 389
- Unique addresses: 69

**Critical Call Sequence:**
```
1. CALL → AutopoolETH Proxy (0x544407e2)
2.   DELEGATECALL → Implementation (0x544407e2)
3.     STATICCALL → SystemRegistry (0xc3d0cbfb)
4.     CALL → SystemSecurityL1 (0x78b3218e)
5.       STATICCALL → SystemRegistry
6.       STATICCALL → AutopoolRegistry
7.     STATICCALL → AccessController (role check)
8.     DELEGATECALL → AutopoolStrategyHooks
9.     DELEGATECALL → AutopoolDebt
10.      DELEGATECALL → WithdrawalQueue
11.        DELEGATECALL → StructuredLinkedList
12.      ... price oracle calls ...
13.      CALL → DestinationVaultMainRewarder (rewards claim)
```

### 3.2 Role Holders (VERIFIED)
| Role | Address |
|------|---------|
| AUTO_POOL_REPORTING_EXECUTOR | 0x1a65e4844a3af0f1733ee9e1a474dc7db3c396a3 |

---

## SECTION 4: ORACLE VULNERABILITY EVIDENCE

### 4.1 BalancerV3StableMathOracle Analysis

**Location:** 0x792587b191eb0169da6beefa592859b47f0651fe

#### Flash Loan Exposure (CRITICAL)
```
VULNERABILITIES IDENTIFIED:

1. NO HISTORICAL SNAPSHOTS
   - Uses current balances from IVaultExplorer.getPoolTokenInfo()
   - No block-based comparison

2. LIVE STATE QUERIES
   - Token balances queried synchronously
   - Amplification parameter queried live
   - Rate providers called live

3. NO BLOCK-BASED GUARDS
   - No minimum block delay
   - No historical balance tracking
   - No last-update timestamp validation

4. POOL STATE DEPENDENCIES
   - Balances (primary invariant input)
   - Rate provider outputs
   - Amplification factor
   - Total LP supply
```

#### Attack Surface
```
An attacker can:
1. Flash loan large amounts to Balancer pool
2. Manipulate pool balances within transaction
3. Call price oracle during manipulation
4. Receive artificially skewed price
5. Exploit price in Tokemak operations
```

### 4.2 Price Computation Flow
```
AutopoolETH.updateDebtReporting()
  → AutopoolDebt._recalculateDestInfo()
    → DestinationVault.getRangePricesLP()
      → SystemRegistry.rootPriceOracle()
        → BalancerV3StableMathOracle.getSpotPrice()
          → IVaultExplorer.getPoolTokenInfo() [MANIPULABLE]
          → StableMath.computeInvariant() [USES MANIPULATED DATA]
          → StableMath.computeOutGivenExactIn() [RETURNS BAD PRICE]
```

---

## SECTION 5: ECONOMIC EVIDENCE

### 5.1 Current State
| Metric | Value |
|--------|-------|
| totalAssets | $20,224,182 USDC |
| totalSupply | 18,965,072 shares |
| NAV/share | $1.0664 |
| Base Asset | USDC (6 decimals) |
| Share Decimals | 18 |

### 5.2 Fee Parameters
| Parameter | Value |
|-----------|-------|
| FEE_DIVISOR | 10,000 (100% basis) |
| MAX_DEBT_REPORT_AGE_SECONDS | 86,400 (1 day) |
| BASE_ASSET_INIT_DEPOSIT | 100,000 |
| profitUnlockPeriod | 86,400 (default) |

---

## SECTION 6: ACCESS CONTROL EVIDENCE

### 6.1 Role-Based Permissions
| Role | Permission | Address |
|------|------------|---------|
| SOLVER | flashRebalance | Unknown |
| AUTO_POOL_REPORTING_EXECUTOR | updateDebtReporting | 0x1a65e4844... |
| AUTO_POOL_FEE_UPDATER | Fee configuration | Unknown |
| AUTO_POOL_MANAGER | Shutdown, settings | Unknown |
| STRATEGY_HOOK_CONFIGURATION | Hook management | Unknown |

### 6.2 External Controls
- All role changes via AccessController (0x37767cbff88cb623e9404e959560984f7d742df6)
- Proxy admin at 0x84a317a45248d6d3f92f40102680ffeda2ab95c0

---

## SECTION 7: GAPS REMAINING

### 7.1 Still Unknown
- [ ] Exact storage slot values for assetBreakdown
- [ ] Full list of registered destination vaults
- [ ] Complete hook configuration
- [ ] Historical flashRebalance transactions (if any)
- [ ] RootPriceOracle main address
- [ ] SOLVER role holder

### 7.2 Evidence Quality Assessment
| Category | Quality | Notes |
|----------|---------|-------|
| Contract Architecture | HIGH | Fully mapped |
| Source Code | HIGH | Verified contracts |
| Transaction Traces | MEDIUM | Single tx analyzed |
| Price Oracle Flow | HIGH | Critical path identified |
| Economic Parameters | MEDIUM | Some from code, not live |
| Access Control | LOW | Missing role holders |

---

## SECTION 8: ATTACK CHAIN PREREQUISITES

### 8.1 Required Capabilities
1. Flash loan provider (Aave, Balancer, etc.)
2. Ability to interact with Balancer V3 pools
3. Transaction simulation capability
4. MEV/bundle submission (optional for frontrunning)

### 8.2 Attack Windows
1. **During updateDebtReporting**: Prices accepted without safety check
2. **During flashRebalance callback**: Attacker has transaction control
3. **When debt reports are stale**: Fresh prices used from manipulable oracles

### 8.3 Economic Requirements
- Must exceed min/max debt spread to profit
- Must overcome gas costs (~$50-100)
- Must overcome flash loan fees (~0.05-0.09%)
- Net profit threshold: >$10,000 to be significant

