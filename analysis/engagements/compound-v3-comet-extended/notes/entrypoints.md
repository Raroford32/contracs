# Entrypoints — Compound V3 USDT Market (CometWithExtendedAssetList)

Proxy: `0x3afdc9bca9213a35503b077a6072f3d0d5ab0840`
Implementation: `0xda54ede5a49cd61932d5507714d0a0e9d1f87eb5`

## External/Public Functions (Main Contract)

| Function | Selector | Callable By | Gating | State Writes | External Calls |
|---|---|---|---|---|---|
| `supply(asset, amount)` | | EOA/contracts | nonReentrant, notPaused | principal, totals, collateral | `doTransferIn` (transferFrom on asset) |
| `supplyTo(dst, asset, amount)` | | EOA/contracts | nonReentrant, notPaused | principal, totals, collateral | `doTransferIn` |
| `supplyFrom(from, dst, asset, amount)` | | EOA/contracts | nonReentrant, notPaused, hasPermission(from) | principal, totals, collateral | `doTransferIn` |
| `transfer(dst, amount)` | ERC20 | EOA/contracts | nonReentrant, notPaused | principal, totals | none (internal transfer) |
| `transferFrom(src, dst, amount)` | ERC20 | EOA/contracts | nonReentrant, notPaused, hasPermission(src) | principal, totals | none (internal transfer) |
| `transferAsset(dst, asset, amount)` | | EOA/contracts | nonReentrant, notPaused | principal, totals, collateral | none (collateral) or none (base) |
| `transferAssetFrom(src, dst, asset, amount)` | | EOA/contracts | nonReentrant, notPaused, hasPermission(src) | same | same |
| `withdraw(asset, amount)` | | EOA/contracts | nonReentrant, notPaused | principal, totals, collateral | `doTransferOut` |
| `withdrawTo(to, asset, amount)` | | EOA/contracts | nonReentrant, notPaused | same | `doTransferOut` |
| `withdrawFrom(src, to, asset, amount)` | | EOA/contracts | nonReentrant, notPaused, hasPermission(src) | same | `doTransferOut` |
| `absorb(absorber, accounts[])` | | EOA/contracts | notPaused | principal, totals, collateral, liquidatorPoints | oracle reads (getPrice) |
| `buyCollateral(asset, minAmount, baseAmount, recipient)` | | EOA/contracts | nonReentrant, notPaused | none (except token balances) | `doTransferIn(baseToken)`, `doTransferOut(asset)` |
| `pause(...)` | | governor OR pauseGuardian only | auth check | pauseFlags | none |
| `withdrawReserves(to, amount)` | | governor only | auth check | none | `doTransferOut(baseToken)` |
| `approveThis(manager, asset, amount)` | | governor only | auth check | none | `asset.approve()` |
| `accrueAccount(account)` | | EOA/contracts | none | principal, indices | none |
| `initializeStorage()` | | anyone (one-time) | `lastAccrualTime == 0` | indices, lastAccrualTime | none |

## View Functions

`getAssetInfo`, `getAssetInfoByAddress`, `getCollateralReserves`, `getReserves`, `getPrice`,
`isBorrowCollateralized`, `isLiquidatable`, `totalSupply`, `totalBorrow`, `balanceOf`, `borrowBalanceOf`,
`getSupplyRate`, `getBorrowRate`, `getUtilization`, `quoteCollateral`,
`isSupplyPaused`, `isTransferPaused`, `isWithdrawPaused`, `isAbsorbPaused`, `isBuyPaused`,
all config getters (governor, pauseGuardian, baseToken, extensionDelegate, numAssets, etc.)

## Fallback

`fallback()` → delegatecall to `extensionDelegate` (handles ERC20 metadata, allow/allowance, etc.)

## Notes
- All state-modifying supply/withdraw/transfer/buy operations are protected by `nonReentrant`
- `absorb` is NOT nonReentrant but only writes to internal state (no external transfers of collateral)
- `initializeStorage` is one-shot (guarded by `lastAccrualTime != 0`)
