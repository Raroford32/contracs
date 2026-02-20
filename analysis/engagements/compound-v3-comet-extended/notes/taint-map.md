# Taint Map — Compound V3 USDT Market

## External Callsites (Dynamic Targets)

### 1. `doTransferIn(asset, from, amount)` — line 659
- **Target**: `asset` parameter (caller-controlled via `supply*` asset param)
- **Calldata**: `transferFrom(from, address(this), amount)` — fixed pattern
- **Value**: 0
- **Safety checks**:
  - `getAssetInfoByAddress(asset)` validates asset is in the registered asset list
  - `nonReentrant` guard on all callers
  - Balance-before/after pattern catches fee-on-transfer
- **Risk**: LOW — asset is validated against immutable config

### 2. `doTransferOut(asset, to, amount)` — line 684
- **Target**: `asset` parameter (caller-controlled via `withdraw*` / `buyCollateral`)
- **Calldata**: `transfer(to, amount)` — fixed pattern
- **Value**: 0
- **Safety checks**:
  - `getAssetInfoByAddress(asset)` validates asset
  - `nonReentrant` guard
  - Return value check via assembly
- **Risk**: LOW — same validation

### 3. `getPrice(priceFeed)` — line 344
- **Target**: `priceFeed` from `AssetInfo` (immutable config) or `baseTokenPriceFeed` (immutable)
- **Calldata**: `latestRoundData()` — fixed
- **Value**: 0
- **Safety checks**: Validates `price > 0`; feed address is immutable
- **Risk**: LOW — oracle addresses are baked into bytecode via constructor

### 4. `fallback()` → delegatecall to `extensionDelegate` — line 1242
- **Target**: `extensionDelegate` (immutable)
- **Calldata**: Entire msg.data (caller-controlled)
- **Value**: msg.value
- **Safety checks**: extensionDelegate is immutable; cannot be changed
- **Risk**: MEDIUM — extensionDelegate executes in Comet's storage context; any bug in the delegate is a bug in Comet. However, delegate address is immutable and verified.

### 5. `IAssetList(assetList).getAssetInfo(i)` — line 226
- **Target**: `assetList` (immutable)
- **Calldata**: `getAssetInfo(uint8)` — index from parameter
- **Value**: 0
- **Safety checks**: assetList is immutable; index bounds checked by numAssets
- **Risk**: LOW

## Caller-Controlled Parameters Summary

| Parameter | Function | Taint Level | Validated? |
|---|---|---|---|
| `asset` | supply/withdraw/transfer/buy | User-controlled | Yes (getAssetInfoByAddress) |
| `amount` | all operations | User-controlled | Yes (balance checks, safe casts) |
| `from/src` | supplyFrom, withdrawFrom, transferFrom | User-controlled | Yes (hasPermission) |
| `dst/to` | supplyTo, withdrawTo, transferAsset | User-controlled | No restriction (any address) |
| `accounts[]` | absorb | User-controlled | Yes (isLiquidatable check) |
| `recipient` | buyCollateral | User-controlled | No restriction |

## Conclusion
No high-risk dynamic dispatch. All external call targets are either:
- Validated against immutable asset config (doTransferIn/Out, getPrice)
- Immutable addresses (extensionDelegate, assetList)
