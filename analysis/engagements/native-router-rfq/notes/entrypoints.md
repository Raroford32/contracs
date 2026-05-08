# Entrypoints — Pendle Boros (Arbitrum)

All user-reachable selectors live on the **Router proxy** `0x8080808080dab95efed788a9214e400ba552def6`. Static dispatch via `RouterFacetLib.resolveRouterFacet(sig)` routes to one of 7 immutable module addresses.

## RFQ-relevant selectors (OTC_MODULE @ 0xc6f465f4...)
| Selector | Function | Notes |
|---|---|---|
| `0xd5c4ecff` | `executeOTCTrade(ExecuteOTCTradeReq)` | **The RFQ entry.** `onlyRelayer`. Verifies maker+taker agent sigs + validator co-sig; calls MarketHub.orderAndOtc. |
| `0xdd1de2f8` | `setOTCTradeValidator(address)` | `onlyAuthorized` (`PERM_CONTROLLER.canCall`). Replaces the SINGLE validator address. |
| `0x5aa537dd` | `otcTradeValidator()` | view |
| `0x000cf1df` | `isOTCTradeExecuted(bytes32)` | view (replay-protection inspection) |

## Auth/identity (AUTH_MODULE @ 0xdb727ff3...)
| Selector | Function | Notes |
|---|---|---|
| `0xb06620b1` | `approveAgent((address,uint8,address,uint64))` | accManager direct call |
| `0xffe6fb25` | `approveAgent((address,uint8,address,uint64,uint64),bytes)` | relayer + signed |
| `0x24218484` | `revokeAgent((address,uint8,address[]))` | accManager direct call |
| `0x5896bd48` | `revokeAgent((address,uint8,address[],uint64),bytes)` | relayer + signed |
| `0x158404db` | `systemRevokeAgent(bytes21[],address[])` | `onlyAuthorized` — admin force-revoke |
| `0xc32025a0` | `agentExecute(address,(bytes21,bytes32,uint64),bytes,bytes)` | `onlyRelayer`. Delegatecalls into `_checkAgentAllowedToCall`-whitelisted selectors with `setAuth(message.account)`. |
| `0xc9c437b3` | `agentExpiry(bytes21,address)` | view |
| `0x22f0e36f` | `signerNonce(address)` | view |
| `0xfa980fb1` | `accountManager(bytes21)` | view |

### Selectors agentExecute is allowed to delegatecall (whitelist)
TradeModule: `cashTransfer`, `ammCashTransfer`, `payTreasury`, `placeSingleOrder`, `bulkOrders`, `bulkCancels`, `enterExitMarkets`.
AMMModule: `swapWithAmm`, `addLiquidityDualToAmm`, `addLiquiditySingleCashToAmm`, `removeLiquidityDualFromAmm`, `removeLiquiditySingleCashFromAmm`.
**NOT in whitelist**: `executeOTCTrade`, `vaultDeposit/withdrawal`, `subaccountTransfer` — these require root signatures via dedicated AuthModule entrypoints.

## Trade (TRADE_MODULE @ 0x21bfd0f5...)
- `placeSingleOrder`, `bulkOrders`, `bulkCancels`, `enterExitMarkets`, `cashTransfer`, `ammCashTransfer`, `payTreasury`, `vaultDeposit`, `vaultPayTreasury`, `requestVaultWithdrawal`, `cancelVaultWithdrawal`, `subaccountTransfer`. All use `setNonAuth` modifier (cooperate with AuthModule's `setAuth`).

## MarketHub-side entrypoints (callable via Router only — `onlyRouter`)
- `enterMarket`, `exitMarket`, `vaultDeposit`, `vaultPayTreasury`, `requestVaultWithdrawal`, `cancelVaultWithdrawal`, `cashInstantWithdraw`, `cashTransfer`, `cashTransferAll`, `payTreasury`, `orderAndOtc`, `bulkOrders`, `cancel`, `liquidate`.
- Permissionless (anyone can call): `finalizeVaultWithdrawal`, `settleAllAndGet`.
- Simulation-only (`require tx.origin == 0`): `simulateTransfer`.

## Fallback dispatch
- MarketHubEntry's `_implementation()` returns `_MARKET_HUB_RISK_MANAGEMENT = 0xe5d9735f...` — any selector NOT defined on MarketHubEntry is delegatecalled there. Includes `delevAndDelist`, force-cancel, and other RM functions.
