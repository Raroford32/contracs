# Security Audit Report: Tokemak AutopoolETH (autoUSD)

**Target Contract:** `0xa7569A44f348d3D70d8ad5889e50F78E33d80D35` (Proxy)
**Implementation:** `0xfb2ebdedc38a7d19080e44ab1d621bc9afad0695` (AutopoolETH)
**Protocol:** Tokemak Foundation
**Base Asset:** USDC (`0xa0b86991c6218b36c1d19d4a2e9eb0ce3606eb48`)
**TVL:** ~$20.2 million USDC
**NAV/Share:** ~$1.066 USDC
**Audit Date:** 2026-02-04

---

## Executive Summary

This audit analyzes the Tokemak AutopoolETH (autoUSD) vault, a sophisticated yield aggregator that deploys USDC across multiple destination vaults. The contract implements complex debt tracking, flash rebalancing, and a hook system for extensibility.

### Key Findings Summary

| ID | Severity | Title | Status |
|----|----------|-------|--------|
| H-01 | High | Documented Attackable Price Function | Unconfirmed - Needs destination vault analysis |
| M-01 | Medium | Debt Reporting Continues with Unsafe Prices | Design Choice - Mitigated by min/max spread |
| M-02 | Medium | Flash Rebalance Callback Timing Window | Mitigated by price safety checks |
| L-01 | Low | 1-Day Staleness Window for Debt Reports | Accepted risk with conservative valuations |
| I-01 | Info | Hook System External Call Risk | Governance controlled |

---

## Architecture Analysis

### Contract Structure

```
TransparentUpgradeableProxy (0xa7569A44...)
         │
         └── AutopoolETH Implementation (0xfb2ebdedc...)
                  │
                  ├── AutopoolDebt (Library)
                  ├── AutopoolFees (Library)
                  ├── AutopoolToken (Library)
                  ├── Autopool4626 (Library)
                  ├── AutopoolDestinations (Library)
                  └── AutopoolStrategyHooks (Library)
```

### Value Flow

```
User USDC → AutopoolETH → Destination Vaults → LP Positions → Yield
            (totalIdle)     (totalDebt)
```

### Three-Tier Valuation System

The protocol uses different valuations based on operation type:

| Purpose | Calculation | Rationale |
|---------|-------------|-----------|
| **Global** | `totalIdle + totalDebt` | Average valuation |
| **Deposit** | `totalIdle + totalDebtMax` | Higher value = fewer shares for depositor |
| **Withdraw** | `totalIdle + totalDebtMin` | Lower value = fewer assets for withdrawer |

This design protects the protocol from manipulation by using conservative valuations on both sides.

---

## Detailed Findings

### H-01: Documented Attackable Price Function

**Location:** `IDestinationVault.sol` interface

**Code Comment:**
```solidity
/// @notice Get the current value of our held pool shares in terms of the base asset
/// @dev This price can be attacked is not validate to be in any range
/// @return price Value of 1 unit of the underlying LP token in terms of the base asset
function getUnderlyerCeilingPrice() external returns (uint256 price);
```

**Description:**
The `getUnderlyerCeilingPrice()` function is explicitly documented as attackable and "not validated to be in any range." This function is called by `totalAssetsTimeChecked()` when debt reports are stale (>1 day old) for calculating deposit share amounts.

**Analysis:**
- Called when: `lastReport + MAX_DEBT_REPORT_AGE_SECONDS > block.timestamp`
- Used for: Deposit valuations when debt is stale
- Protection: Uses max(staleDebt, newValue) to be conservative

**Mitigations Present:**
1. The function result is compared against cached `staleDebt` - the higher value is used
2. Deposits use ceiling price, which if manipulated higher would give depositors fewer shares (protecting existing holders)
3. Regular debt reporting (observed daily) keeps data fresh

**Recommendation:** Investigate the destination vault implementation to understand the attack surface of `getUnderlyerCeilingPrice()`.

---

### M-01: Debt Reporting Continues with Unsafe Prices

**Location:** `AutopoolDebt.sol:_recalculateDestInfo()`

**Code:**
```solidity
(uint256 spotPrice, uint256 safePrice, bool isSpotSafe) = destVault.getRangePricesLP();

// ...prices used to calculate debt...

result.pricesWereSafe = isSpotSafe;
// Note: Function continues even if isSpotSafe is false!
```

**Description:**
When `_recalculateDestInfo()` is called during debt reporting, the function continues execution even when `isSpotSafe` returns false. This is in contrast to flash rebalance operations which revert on unsafe prices.

**Code Comment:**
```solidity
// Prices are per LP token and whether or not the prices are safe to use
// If they aren't safe then just continue and we'll get it on the next go around
```

**Analysis:**

| Operation | Unsafe Price Handling |
|-----------|----------------------|
| `flashRebalance()` | **Reverts** with `InvalidPrices()` |
| `updateDebtReporting()` | **Continues** - updates cached values |

**Mitigations Present:**
1. Both `spotPrice` and `safePrice` are used to calculate min/max bounds
2. The system uses `min(spotPrice, safePrice)` for minimum debt and `max(spotPrice, safePrice)` for maximum debt
3. This spread provides buffer against manipulation
4. Role-based access control limits who can trigger debt reporting

**Recommendation:** Consider adding a circuit breaker if prices deviate significantly between spot and safe, or if price changes exceed a threshold from previous report.

---

### M-02: Flash Rebalance Callback Timing Window

**Location:** `AutopoolDebt.sol:flashRebalance()`

**Flow:**
```
1. _handleRebalanceOut() - Withdraw from destinationOut, get prices
2. onFlashLoan callback - Solver has full control
3. _handleRebalanceIn() - Deposit to destinationIn, get NEW prices
```

**Description:**
Between `_handleRebalanceOut` and `_handleRebalanceIn`, the solver (via `IERC3156FlashBorrower.onFlashLoan`) has full execution control. If they can manipulate the destination vault's prices during this window, it could affect debt calculations.

**Mitigations Present:**
1. `_handleRebalanceIn` calls `getRangePricesLP()` AFTER the callback
2. `pricesWereSafe` is checked and reverts if false:
   ```solidity
   if (!inDebtResult.pricesWereSafe) {
       revert InvalidPrices();
   }
   ```
3. SOLVER role is required - trusted party
4. `nonReentrant` modifier prevents reentrancy
5. `trackNavOps` prevents concurrent nav-changing operations

**Recommendation:** The price safety check in `_handleRebalanceIn` is the primary protection. Ensure destination vault implementations properly detect manipulation in their `isSpotSafe` calculation.

---

### L-01: 1-Day Staleness Window

**Location:** `AutopoolDebt.sol`

**Code:**
```solidity
uint256 public constant MAX_DEBT_REPORT_AGE_SECONDS = 1 days;
```

**Description:**
Cached debt values are considered valid for 24 hours. If prices move significantly during this window, the cached values may not reflect reality.

**Mitigations Present:**
1. Regular debt reporting observed (multiple daily calls from `0x1a65e4844a3af0f1733ee9e1a474dc7db3c396a3`)
2. `totalAssetsTimeChecked()` performs live price queries when debt is stale
3. Conservative valuations (min for withdrawals, max for deposits) provide buffer

**Recommendation:** Monitor debt reporting frequency. Consider reducing staleness window for volatile market conditions.

---

### I-01: Hook System External Calls

**Location:** `AutopoolStrategyHooks.sol`

**Description:**
The protocol supports configurable hooks that are called during rebalance and debt reporting operations. These hooks are external contracts that could potentially:
- Revert to block operations
- Perform state manipulation during callbacks
- Introduce reentrancy vectors

**Mitigations Present:**
1. Hook registration requires `STRATEGY_HOOK_CONFIGURATION` role
2. Only trusted hooks should be added
3. Core operations protected by `nonReentrant`

**Recommendation:** Ensure strict governance over hook registration. Consider gas limits on hook calls.

---

## Cross-Contract Interactions

### External Dependencies

| Contract | Interaction | Risk |
|----------|-------------|------|
| Destination Vaults | `getRangePricesLP()`, `depositUnderlying()`, `withdrawUnderlying()` | Price accuracy, availability |
| Price Oracle (via DestVault) | `getUnderlyerCeilingPrice()`, `getUnderlyerFloorPrice()` | Oracle manipulation |
| USDC | `transfer`, `transferFrom`, `balanceOf` | Standard ERC20 risks |
| System Registry | Access control, security state | Centralization |

### Call Graph (Critical Paths)

```
flashRebalance()
├── validateRebalanceParams() - Access/param checks
├── _handleRebalanceOut()
│   └── destVault.getRangePricesLP() ← External call
│   └── destVault.withdrawUnderlying() ← External call
├── receiver.onFlashLoan() ← CALLBACK TO SOLVER
├── _handleRebalanceIn()
│   └── destVault.getRangePricesLP() ← External call, checked for safety
│   └── destVault.depositUnderlying() ← External call
└── executeHooks() ← External calls to registered hooks
```

---

## Security Controls Analysis

### Access Control

| Role | Permissions |
|------|-------------|
| `SOLVER` | Execute flash rebalance |
| `AUTO_POOL_REPORTING_EXECUTOR` | Update debt reporting |
| `AUTO_POOL_FEE_UPDATER` | Modify fee parameters |
| `AUTO_POOL_MANAGER` | Shutdown, profit unlock settings |
| `STRATEGY_HOOK_CONFIGURATION` | Add/remove hooks |
| `TOKEN_RECOVERY_MANAGER` | Recover stuck tokens |

### Reentrancy Protection

- `NonReentrantUpgradeable` modifier on state-changing functions
- `ensureNoNavOps` prevents concurrent nav-changing operations across system

### Price Protection

- Three-tier valuation (Deposit/Withdraw/Global)
- Min/Max debt tracking provides spread buffer
- `pricesWereSafe` check on flash rebalance
- TWAP-based safe prices in destination vaults (assumed)

---

## Economic Analysis

### Current State

- **TVL:** $20,224,182 USDC
- **Total Supply:** 18,965,072 shares
- **NAV/Share:** $1.0664 (6.64% profit)

### Attack Profitability Threshold

For an exploit to be economically viable:
- Must overcome min/max spread differential
- Must account for gas costs (~$10-50 per complex operation)
- Flash loan fees (~0.05-0.09%)
- Must net > $10,000 to be significant

### Price Manipulation Cost

To manipulate destination vault prices:
- Would require flash loan to move LP pools
- TWAP-based safe prices would require sustained manipulation
- Cost likely exceeds potential profit for most manipulation attempts

---

## Recommendations

### Immediate Actions

1. **Verify Destination Vault Price Functions:** Audit `getRangePricesLP()`, `getUnderlyerCeilingPrice()`, and `getUnderlyerFloorPrice()` implementations in all registered destination vaults.

2. **Monitor Debt Reporting:** Ensure regular debt reporting continues. Set up alerts if gaps exceed 12 hours.

3. **Hook Audit:** Review all registered hooks for potential security issues.

### Medium-Term Improvements

1. **Consider Price Deviation Circuit Breaker:** If spot/safe price divergence exceeds X%, pause or require additional verification.

2. **Reduce Staleness Window:** Consider reducing `MAX_DEBT_REPORT_AGE_SECONDS` from 1 day to 12 hours.

3. **Add Unsafe Price Logging:** Even if operations continue with unsafe prices, emit distinct events for monitoring.

### Long-Term Considerations

1. **Formal Verification:** The complex state machine with multiple valuations would benefit from formal verification of invariants.

2. **Invariant Testing:** Implement continuous invariant testing for:
   - NAV/share should never decrease during deposit
   - Total debt should equal sum of destination holdings
   - Profit unlock should never create shares from nothing

---

## Conclusion

The Tokemak AutopoolETH contract demonstrates sophisticated risk management through its three-tier valuation system and price safety checks. The most significant concern is the documented attackability of `getUnderlyerCeilingPrice()`, which requires investigation of the destination vault implementations to assess actual risk.

The protocol's defense-in-depth approach (role-based access, reentrancy guards, price safety checks, conservative valuations) provides meaningful protection against most attack vectors. However, the interaction between debt reporting (which continues on unsafe prices) and user operations (which use cached values) creates a potential timing window that warrants ongoing monitoring.

**Overall Risk Assessment:** MEDIUM - The $20M TVL warrants careful monitoring, but existing controls provide reasonable protection.

---

## Appendix: Key Code References

| Function | File | Line | Purpose |
|----------|------|------|---------|
| `flashRebalance` | AutopoolETH.sol | ~450 | Main rebalance entry point |
| `processRebalance` | AutopoolDebt.sol | ~200 | Core rebalance logic |
| `_recalculateDestInfo` | AutopoolDebt.sol | ~550 | Debt value calculation |
| `totalAssetsTimeChecked` | AutopoolDebt.sol | ~400 | Staleness-aware asset calculation |
| `updateDebtReporting` | AutopoolDebt.sol | ~300 | Periodic debt refresh |

---

*Report generated by security audit session 2026-02-04*
