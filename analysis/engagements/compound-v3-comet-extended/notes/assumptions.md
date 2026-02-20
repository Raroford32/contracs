# Assumptions — Compound V3 USDT Market (XAUt Upgrade)

## Upgrade-Specific Assumptions

### A1: XAUt is a standard ERC20
- EVIDENCE IN CODE: `doTransferIn/doTransferOut` uses IERC20NonStandard interface
- VIOLATION CONDITION: XAUt upgraded to add fee-on-transfer, non-standard behavior
- CONSEQUENCE: `doTransferIn` handles via balance-diff; `doTransferOut` would break if transfer sends less than requested (but OZ ERC20 guarantees exact amount unless upgraded)
- VIOLATION FEASIBILITY: Requires Tether admin action; not attacker-exploitable
- STATUS: HOLDS (standard OZ ERC20Upgradeable currently)

### A2: XAUt transfers don't revert unexpectedly
- EVIDENCE IN CODE: `doTransferOut` reverts the entire tx if transfer fails
- VIOLATION CONDITION: Tether blocks Comet contract address
- CONSEQUENCE: XAUt withdrawals fail; buyCollateral for XAUt fails; absorb still works (no transfer)
- VIOLATION FEASIBILITY: Requires Tether admin action
- STATUS: HOLDS but acknowledged dependency risk

### A3: XAU/USD Chainlink feed accurately reflects XAUt value
- EVIDENCE IN CODE: `getPrice(priceFeed)` → `latestRoundData()`; checks `price > 0`
- VIOLATION CONDITION: XAUt depegs from gold spot (secondary market discount)
- CONSEQUENCE: Over-collateralization: borrower gets credit for full gold value on discounted XAUt
- VIOLATION FEASIBILITY: Possible but XAUt is well-established ($3.5B mcap); supply cap limits exposure to ~$1M
- STATUS: ACKNOWLEDGED RISK (bounded by supply cap)

### A4: XAU/USD feed is fresh and not stale
- EVIDENCE IN CODE: No staleness check in `getPrice` (only `price > 0`)
- VIOLATION CONDITION: Chainlink feed stops updating (oracles go down, network issues)
- CONSEQUENCE: Stale gold price → incorrect collateral valuation → potential under/over-collateralization
- VIOLATION FEASIBILITY: Gold prices are relatively stable; Chainlink has redundant infrastructure
- STATUS: KNOWN DESIGN PATTERN (Compound V3 relies on Chainlink liveness for all assets)

### A5: assetsIn bitmap correctly tracks new asset
- EVIDENCE IN CODE: `isInAsset(assetsIn, 14, _reserved)` checks bit 14 of uint16 assetsIn
- VIOLATION CONDITION: Bit 14 was set before upgrade for a different purpose
- CONSEQUENCE: Phantom collateral attribution to XAUt
- VIOLATION FEASIBILITY: FALSIFIED — bit 14 was unused before upgrade (old numAssets=14, so only bits 0-13 used)
- STATUS: SAFE

### A6: Supply cap enforces maximum exposure
- EVIDENCE IN CODE: `if (totals.totalSupplyAsset > assetInfo.supplyCap) revert`
- VIOLATION CONDITION: Supply cap check is bypassed
- CONSEQUENCE: Unlimited XAUt collateral deposits
- VIOLATION FEASIBILITY: Check uses strict `>` on uint128; no bypass path found
- STATUS: SAFE

## General Compound V3 Assumptions (pre-existing, not upgrade-specific)

### G1: Oracle prices are accurate and timely
- All 15 assets depend on Chainlink feeds
- No staleness checks beyond `price > 0`

### G2: No re-entrancy via token transfers
- All state-modifying functions use `nonReentrant`
- XAUt: no hooks, standard ERC20

### G3: Interest index arithmetic doesn't overflow
- `baseSupplyIndex` and `baseBorrowIndex` are uint64
- Monotonically increasing; would take thousands of years to overflow at normal rates

### G4: Collateral factor gap (borrowCF < liquidateCF) provides safety margin
- XAUt: borrowCF=0.70, liquidateCF=0.75 → 5% gap
- This gap absorbs price movements between blocks without immediate liquidation

### G5: Liquidation is profitable and timely
- Absorbers earn points (no direct token reward currently)
- buyCollateral provides 6% discount for XAUt
- At $5039/XAUt and 200 XAUt cap, max liquidation value ~$1M → sufficient incentive
