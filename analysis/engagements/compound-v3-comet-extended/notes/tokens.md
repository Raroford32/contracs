# Token Semantics — Compound V3 USDT Market

## Base Token: USDT (0xdac17f958d2ee523a2206206994597c13d831ec7)
- Decimals: 6
- Fee-on-transfer: Has `basisPointsRate` (currently 0, but can be set by owner)
- Return value: Does NOT return bool on transfer/transferFrom (handled by IERC20NonStandard + assembly in Comet)
- Blocklist: Yes (isBlackListed)
- Pausable: Yes
- Upgradeable: No (legacy contract)
- Protocol assumption: `doTransferIn` uses balance-before/after (safe for fee-on-transfer)

## NEW ASSET — XAUt (Tether Gold) (0x68749665ff8d2d112fa859aa293f07a622782f38)
- Decimals: 6
- Fee-on-transfer: NO (standard OZ ERC20Upgradeable, no fee mechanism)
- Return value: Returns bool (standard)
- Blocklist: YES (`isBlocked[address]` — `WithBlockedList` mixin)
- Pausable: No explicit pause, but blocklist serves similar purpose
- Upgradeable: YES (TransparentUpgradeableProxy → TetherToken impl)
- Owner: `0xc6cde7c39eb2f0f0095f41570af89efc2c1ea828`
- Special: `destroyBlockedFunds` can burn tokens of blocked addresses
- Token total supply: ~712,747 XAUt
- Protocol supply cap: 200 XAUt (~$1M)
- Protocol assumption risks:
  1. If Comet contract gets blocked → XAUt withdrawals/buyCollateral fail (DoS on this asset only)
  2. If XAUt is upgraded to add fees → `doTransferIn` balance diff pattern handles this correctly
  3. `destroyBlockedFunds` on Comet → would break `getCollateralReserves` (underflow/revert)

## Collateral Assets (unchanged):

| # | Token | Addr | Decimals | Semantic Flags | Risk Notes |
|---|---|---|---|---|---|
| 0 | COMP | 0xc00e...6888 | 18 | Standard | Governance token |
| 1 | WETH | 0xc02a...6cc2 | 18 | Standard | Canonical wrapped ETH |
| 2 | WBTC | 0x2260...2c599 | 8 | Standard | High value collateral |
| 3 | UNI | 0x1f98...f984 | 18 | Standard | |
| 4 | LINK | 0x5149...86ca | 18 | Standard | |
| 5 | wstETH | 0x7f39...2ca0 | 18 | Exchange-rate bearing (stETH wrapper) | Rate conversion risk |
| 6 | cbBTC | 0xcbb7...33bf | 8 | Coinbase wrapped BTC | Centralized custodian |
| 7 | tBTC | 0x1808...d88 | 18 | Threshold Network BTC | Bridge/synthetic risk |
| 8 | (sunset) | 0x57f5...7812 | 18 | borrowCF=0, cap=0 | Winding down |
| 9 | sFRAX | 0xa663...c32 | 18 | Staked FRAX (yield-bearing) | Rate conversion |
| 10 | mETH | 0xd5f7...adfa | 18 | Mantle staked ETH | LST risk |
| 11 | weETH | 0xcd5f...b7ee | 18 | EtherFi wrapped eETH | LST + exchange rate |
| 12 | sdeUSD (sunset) | 0x5c5b...8326 | 18 | borrowCF=0, cap=0 | Winding down |
| 13 | (sunset) | 0x1570...5138 | 18 | borrowCF=0, cap=0 | Winding down |
| 14 | **XAUt** | 0x6874...2f38 | 6 | **NEW — blocklist, upgradeable** | **See above** |
