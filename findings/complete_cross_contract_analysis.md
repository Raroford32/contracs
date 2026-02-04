# Complete Cross-Contract Analysis: f(x) Protocol + Convex FXN Integration

**Analysis Date**: 2026-02-04
**Contracts Analyzed**:
- StakingProxyERC20 (Convex): 0x8e0fd32e77ad1f85c94e1d1656f23f9958d85018
- FxUSDShareableRebalancePool (Gauge): 0x72a6239f1651a4556f4c40fe97575885a195f535
- MarketV2: 0x2c613d2c163247cd43fd05d6efc487c327d1b248
- WrappedTokenTreasuryV2: 0xdd8f6860f5a3eecd8b7a902df75cb7548387c224
- Treasury Proxy: 0x781ba968d5cc0b40eb592d5c8a9a3a4000063885

---

## Executive Summary

This analysis traces the complete cross-contract value flow and state dependencies across the Convex FXN and f(x) Protocol integration. The system involves:

1. **Convex Layer**: StakingProxyERC20 vaults that wrap gauge interactions
2. **f(x) Gauge Layer**: FxUSDShareableRebalancePool with liquidation/boost mechanics
3. **f(x) Core Layer**: Treasury + Market handling mints/redeems of fToken/xToken
4. **Oracle Layer**: Price feeds for collateral ratio calculations

**Key Finding**: The protocol is well-designed with appropriate access controls. No critical permissionless exploits identified. Several medium-risk vectors require privileged role access or social engineering.

---

## Complete Contract Architecture

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                           CONVEX LAYER                                           │
├─────────────────────────────────────────────────────────────────────────────────┤
│                                                                                  │
│  ┌──────────────────────────────────────────────────────────────────────────┐   │
│  │  StakingProxyERC20 (Vault Implementation)                                 │   │
│  │  - deposit(amount): Transfer LP → Gauge                                   │   │
│  │  - withdraw(amount): Gauge → User                                         │   │
│  │  - getReward(): Claim FXN + extra rewards [PERMISSIONLESS]               │   │
│  │  - earned(): Alternative claim to VAULT [PERMISSIONLESS, ASYMMETRIC]     │   │
│  │  - execute(to, value, data): Arbitrary call [OWNER ONLY]                 │   │
│  └──────────────────────────────────────────────────────────────────────────┘   │
│                                    │                                             │
│                                    │ delegatecall via clone                      │
│                                    ▼                                             │
│  ┌──────────────────────────────────────────────────────────────────────────┐   │
│  │  StakingProxyBase                                                         │   │
│  │  - _processFxn(): FXN fees → feeDepositor, rest → owner                  │   │
│  │  - _processExtraRewards(): Direct to owner                               │   │
│  │  - _checkpointRewards(): Update reward accounting                        │   │
│  └──────────────────────────────────────────────────────────────────────────┘   │
│                                                                                  │
└──────────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    │ interacts with
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────────┐
│                           f(x) GAUGE LAYER                                       │
├─────────────────────────────────────────────────────────────────────────────────┤
│                                                                                  │
│  ┌──────────────────────────────────────────────────────────────────────────┐   │
│  │  FxUSDShareableRebalancePool (Gauge Implementation)                       │   │
│  │                                                                           │   │
│  │  PERMISSIONLESS:                                                          │   │
│  │  - checkpoint(account): Update boost/rewards [ANYONE]                     │   │
│  │  - claim(): Claim accumulated rewards                                     │   │
│  │                                                                           │   │
│  │  ROLE-PROTECTED:                                                          │   │
│  │  - liquidate(maxAmount, minBaseOut): [LIQUIDATOR_ROLE]                   │   │
│  │  - toggleVoteSharing(staker): [VE_SHARING_ROLE]                          │   │
│  │  - withdrawFrom(receiver, owner, amount): [WITHDRAW_FROM_ROLE]           │   │
│  │                                                                           │   │
│  │  VULNERABLE TO execute():                                                 │   │
│  │  - acceptSharedVote(newOwner): Can be called by vault via execute()      │   │
│  │    → Requires isStakerAllowed[newOwner][caller] to be true               │   │
│  └──────────────────────────────────────────────────────────────────────────┘   │
│                                    │                                             │
│                                    │ liquidate() calls                           │
│                                    ▼                                             │
└──────────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────────┐
│                           f(x) MARKET LAYER                                      │
├─────────────────────────────────────────────────────────────────────────────────┤
│                                                                                  │
│  ┌──────────────────────────────────────────────────────────────────────────┐   │
│  │  MarketV2 (via proxy)                                                     │   │
│  │                                                                           │   │
│  │  - mintFToken(baseIn, recipient, minOut): Deposit eETH → get fToken      │   │
│  │  - mintXToken(baseIn, recipient, minOut): Deposit eETH → get xToken      │   │
│  │  - redeemFToken(fTokenIn, recipient, minOut): Burn fToken → get eETH     │   │
│  │  - redeemXToken(xTokenIn, recipient, minOut): Burn xToken → get eETH     │   │
│  │                                                                           │   │
│  │  FEE CALCULATION:                                                         │   │
│  │  - Uses stabilityRatio to determine fee brackets                         │   │
│  │  - Fees increase near stability mode boundaries                          │   │
│  │                                                                           │   │
│  │  VALUE CONVERSION:                                                        │   │
│  │  - getWrapppedValue(): Convert underlying ETH → wrapped eETH amount      │   │
│  │  - getUnderlyingValue(): Convert wrapped eETH → underlying ETH value     │   │
│  └──────────────────────────────────────────────────────────────────────────┘   │
│                                    │                                             │
│                                    │ calls Treasury functions                    │
│                                    ▼                                             │
└──────────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────────┐
│                           f(x) TREASURY LAYER                                    │
├─────────────────────────────────────────────────────────────────────────────────┤
│                                                                                  │
│  ┌──────────────────────────────────────────────────────────────────────────┐   │
│  │  WrappedTokenTreasuryV2 (extends TreasuryV2)                              │   │
│  │                                                                           │   │
│  │  KEY STATE:                                                               │   │
│  │  - totalBaseToken: Total deposited collateral (underlying value)         │   │
│  │  - referenceBaseTokenPrice: Settlement anchor price                      │   │
│  │  - priceOracle: IFxPriceOracleV2 for current prices                      │   │
│  │  - rateProvider: IFxRateProvider for eETH/ETH conversion                 │   │
│  │                                                                           │   │
│  │  CRITICAL FUNCTION - collateralRatio():                                   │   │
│  │  ```solidity                                                              │   │
│  │  function collateralRatio() public view returns (uint256) {              │   │
│  │      SwapState memory _state = _loadSwapState(Action.None);              │   │
│  │      return (_state.baseSupply * _state.baseNav) / _state.fSupply;       │   │
│  │  }                                                                        │   │
│  │  ```                                                                      │   │
│  │  Used by Gauge for liquidation threshold checks!                         │   │
│  │                                                                           │   │
│  │  PRICE ASYMMETRY (SECURITY FEATURE):                                      │   │
│  │  - MintFToken/RedeemXToken: uses minPrice                                │   │
│  │  - MintXToken/RedeemFToken: uses maxPrice                                │   │
│  │  → Prevents sandwich attacks but creates theoretical arbitrage           │   │
│  │                                                                           │   │
│  │  ROLE-PROTECTED:                                                          │   │
│  │  - mintFToken/mintXToken: [FX_MARKET_ROLE]                               │   │
│  │  - redeem: [FX_MARKET_ROLE]                                              │   │
│  │  - settle(): [SETTLE_WHITELIST_ROLE]                                     │   │
│  │  - initializeProtocol(): [PROTOCOL_INITIALIZER_ROLE]                     │   │
│  └──────────────────────────────────────────────────────────────────────────┘   │
│                                                                                  │
└──────────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    │ queries
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────────┐
│                           ORACLE LAYER                                           │
├─────────────────────────────────────────────────────────────────────────────────┤
│                                                                                  │
│  ┌──────────────────────────────────────────────────────────────────────────┐   │
│  │  IFxPriceOracleV2                                                         │   │
│  │                                                                           │   │
│  │  function getPrice() returns (                                            │   │
│  │      bool isValid,    // Price deviation within acceptable bounds         │   │
│  │      uint256 twap,    // Time-weighted average (manipulation resistant)   │   │
│  │      uint256 minPrice, // Minimum across all sources                      │   │
│  │      uint256 maxPrice  // Maximum across all sources                      │   │
│  │  );                                                                       │   │
│  │                                                                           │   │
│  │  PROTECTION: Reverts if twap == 0 (ErrorInvalidTwapPrice)                │   │
│  └──────────────────────────────────────────────────────────────────────────┘   │
│                                                                                  │
│  ┌──────────────────────────────────────────────────────────────────────────┐   │
│  │  IFxRateProvider (for wrapped tokens like eETH)                           │   │
│  │                                                                           │   │
│  │  function getRate() returns (uint256);                                    │   │
│  │  // Returns eETH/ETH conversion rate (e.g., 1.05e18 = 1 eETH = 1.05 ETH) │   │
│  └──────────────────────────────────────────────────────────────────────────┘   │
│                                                                                  │
└──────────────────────────────────────────────────────────────────────────────────┘
```

---

## Identified Attack Vectors

### H-005: Vote Sharing Manipulation via execute() [MEDIUM]

**Path**: StakingProxy.execute() → Gauge.acceptSharedVote()

```
Attacker Vault                          Victim
     │                                     │
     │  1. execute(gauge, acceptSharedVote(victim))
     │ ─────────────────────────────────────────►
     │                                     │
     │                              Check: isStakerAllowed[victim][attacker_vault]
     │                                     │
     │                              IF TRUE:
     │  2. getStakerVoteOwner[attacker_vault] = victim
     │ ◄───────────────────────────────────────
     │                                     │
     │  3. Attacker vault now uses victim's veFXN for boost
```

**Constraint**: Victim must have previously called `toggleVoteSharing(attacker_vault)` or be social-engineered to do so.

**Impact**: Boost rewards redirected from victim to attacker.

---

### H-006: Checkpoint Timing Optimization [LOW]

**Path**: Anyone → Gauge.checkpoint()

```
1. User locks large veFXN
2. Immediately call checkpoint(user)
3. High boost locked into time-weighted average
4. User unlocks veFXN later
5. Boost remains high until next checkpoint
```

**Impact**: Reward optimization, not extraction. More useful for legitimate users.

---

### H-007/H-008: Liquidation Attacks [LOW]

**Path**: LIQUIDATOR_ROLE → Gauge.liquidate() → Market.redeem() → Treasury.redeem()

```
1. Monitor collateralRatio approaching liquidatableCollateralRatio
2. JIT deposit into gauge (become major staker)
3. Trigger liquidation
4. Receive proportional share of liquidated eETH
5. Withdraw immediately
```

**Constraint**: Requires LIQUIDATOR_ROLE - attack is blocked by access control.

---

### H-009: Price Asymmetry Arbitrage [MEDIUM]

**Path**: Market.mintXToken() / Market.redeemXToken()

The Treasury uses different prices:
- `MintXToken`: uses `maxPrice`
- `RedeemXToken`: uses `minPrice`

When `maxPrice ≠ minPrice`, theoretical arbitrage exists:
```
Profit = (maxPrice/minPrice - 1) * position - fees
```

**Constraint**:
- Requires significant price divergence (> fee threshold)
- Oracle has multiple sources with deviation checks
- TWAP anchoring limits manipulation window

---

### H-004: earned() vs getReward() Asymmetry [LOW]

**Path**: Anyone → StakingProxy.earned() vs getReward()

```solidity
// earned() claims to VAULT (this contract)
IFxnGauge(gauge).claim(address(this), address(this));

// getReward() claims to OWNER
IFxnGauge(gauge).claim();  // Uses rewardReceiver → owner
```

**Impact**: Griefing only. Rewards stuck in vault but recoverable via `transferTokens()`.

---

## Cross-Contract State Dependencies

| Source Contract | Function | Depends On | Risk |
|----------------|----------|------------|------|
| Gauge | liquidate() | Treasury.collateralRatio() | Role-protected |
| Gauge | checkpoint() | veHelper.getAdjustedVeFXNBalance() | Permissionless but low impact |
| Market | mintFToken() | Treasury.maxMintableFToken() | Protected by FX_MARKET_ROLE |
| Market | redeemFToken() | Treasury.maxRedeemableFToken() | Protected by FX_MARKET_ROLE |
| Treasury | collateralRatio() | Oracle.getPrice() | Oracle trusted |
| Treasury | getWrapppedValue() | RateProvider.getRate() | Rate provider trusted |

---

## Reentrancy Analysis

### Protected Functions
- **StakingProxy**: `deposit()`, `withdraw()` have `nonReentrant`
- **Gauge**: `claim()` has `nonReentrant`
- **Treasury**: Uses `onlyRole(FX_MARKET_ROLE)` which prevents unauthorized calls

### Potentially Unprotected
- **StakingProxy.getReward()**: No explicit `nonReentrant`
  - However: External calls are to trusted contracts (gauge, minter)
  - State updates happen after external calls (CEI pattern in reward processing)
  - No exploit found

---

## Security Controls Summary

| Control | Implementation | Effectiveness |
|---------|---------------|---------------|
| Liquidation | LIQUIDATOR_ROLE required | Strong |
| Vote Sharing | VE_SHARING_ROLE + staker allowlist | Strong (requires victim action) |
| Oracle | Multi-source with TWAP + deviation checks | Strong |
| Market Access | FX_MARKET_ROLE for mints/redeems | Strong |
| Settlement | SETTLE_WHITELIST_ROLE | Strong |
| Reentrancy | nonReentrant on key functions | Adequate |

---

## Conclusion

The f(x) Protocol + Convex FXN integration demonstrates mature security design:

1. **Role-based access control** prevents direct exploitation of sensitive functions
2. **Oracle design** with multiple sources and TWAP prevents simple manipulation
3. **Price asymmetry** is intentional protection against sandwich attacks
4. **Permissionless functions** enable griefing but not value extraction

**No economically viable unprivileged exploit chains identified.**

The main residual risks are:
- Social engineering for vote sharing attacks (requires victim action)
- Oracle divergence arbitrage (requires rare conditions + may not exceed fees)
- Privileged role compromise (governance/multisig risk)

---

## Appendix: Key Function Selectors

| Contract | Function | Selector |
|----------|----------|----------|
| StakingProxy | deposit(uint256) | 0xb6b55f25 |
| StakingProxy | withdraw(uint256) | 0x2e1a7d4d |
| StakingProxy | getReward() | 0x3d18b912 |
| StakingProxy | earned() | 0x96c55175 |
| StakingProxy | execute(address,uint256,bytes) | 0xb61d27f6 |
| Gauge | claim() | 0x4e71d92d |
| Gauge | checkpoint(address) | 0xc2c4c5c1 |
| Gauge | liquidate(uint256,uint256) | 0x???? |
| Gauge | acceptSharedVote(address) | 0x???? |
| Treasury | collateralRatio() | 0x5d1ca631 |
| Treasury | settle() | 0x???? |
