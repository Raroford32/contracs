# Numeric Boundaries — Compound V3 USDT Market

## Key Value Flows

### 1. Supply XAUt Collateral
- `supplyCollateral(from, dst, XAUt, amount)`
- Boundary: first depositor with 0 existing supply
- XAUt has 6 decimals, scale = 1e6
- Supply cap: 200,000,000 (200 XAUt = ~$1M at $5039/oz)
- No exchange rate / share mechanism for collateral (direct balance tracking)
- No donation/inflation attack vector (collateral is tracked 1:1, not via shares)

### 2. Withdraw XAUt Collateral
- `withdrawCollateral(src, to, XAUt, amount)`
- Boundary: withdrawing all collateral → `srcCollateralNew = 0`
- `updateAssetsIn` clears bit 14 in `assetsIn`
- `isBorrowCollateralized` check with newly reduced collateral

### 3. Liquidation (absorb) with XAUt
- `absorbInternal(absorber, account)` iterates all assets
- XAUt at index 14, liquidationFactor = 0.90
- Seized XAUt value = `seizeAmount * price / scale * 0.90`
- Protocol absorbs collateral; debt is reduced
- Boundary: account with only XAUt as collateral at liquidation threshold

### 4. buyCollateral for XAUt
- `quoteCollateral(XAUt, baseAmount)`
- `discountFactor = storeFrontPriceFactor * (1e18 - 0.90e18) = 0.6e18 * 0.1e18 / 1e18 = 0.06e18`
- `assetPriceDiscounted = XAUprice * (1e18 - 0.06e18) / 1e18 = XAUprice * 0.94`
- Buyers get XAUt at 6% discount to oracle price
- Division: `basePrice * baseAmount * 1e6 / assetPriceDiscounted / 1e6`
- At small baseAmount: potential rounding to 0 collateral (but minAmount protects buyer)

## Boundary Experiments

### A. Zero/Empty State
- XAUt `totalsCollateral.totalSupplyAsset` starts at 0 after upgrade
- First supply: `0 + amount`; no division, no exchange rate → SAFE
- `getCollateralReserves` = `balanceOf(this) - totalsCollateral` → starts at 0 → SAFE

### B. Supply Cap Edge
- Supply cap = 200,000,000 (200 XAUt)
- Check: `totals.totalSupplyAsset > assetInfo.supplyCap` → strict greater-than
- Edge: supply exactly 200 XAUt → `200e6 > 200e6` → FALSE → allowed
- Edge: supply 200 XAUt + 1 wei → `200000001 > 200000000` → TRUE → reverts
- CORRECT behavior

### C. Rounding in quoteCollateral
- Minimum meaningful purchase: `baseAmount` such that collateral >= 1 wei
- `collateralAmount = basePrice * baseAmount * 1e6 / assetPriceDiscounted / 1e6`
- With basePrice ~= 1e8 (USDT = $1), assetPriceDiscounted ~= 4736e8:
  - `1e8 * baseAmount * 1e6 / (4736e14) / 1e6 = baseAmount / 4736`
  - Minimum baseAmount for 1 wei XAUt: ~4736 USDT-wei = 0.004736 USDT
  - No meaningful rounding exploit at these scales

### D. Decimal Mismatch
- XAUt: 6 decimals (same as USDT base token)
- scale = 1e6
- Price feeds: both 8 decimals (PRICE_FEED_DECIMALS = 8)
- `mulPrice(n, price, fromScale)` = `n * price / fromScale`
- For XAUt: `seizeAmount * goldPrice / 1e6` → consistent units
- No decimal mismatch issues

## Conclusion
No numeric boundary vulnerabilities identified. The collateral-tracking model (direct balance, no shares/exchange rates) eliminates donation/inflation attack vectors. Rounding is within acceptable bounds given the token scales.
