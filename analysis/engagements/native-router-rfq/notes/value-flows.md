# Value Flows — Pendle Boros (RFQ corridor)

## Money entry
- `vaultDeposit` (signed root msg or direct from msg.sender == root via TradeModule.vaultDeposit with `setNonAuth`):
  - ERC20.transferFrom(root → MarketHub)
  - `acc[(root, accountId, tokenId, marketId|CROSS)].cash += scaled(amount)`
- `depositFromBox(...)` (DEPOSIT_MODULE — not yet read in detail): mediated deposit with optional swap; signed by root.

## Money exit
- `requestVaultWithdrawal(tokenId, amount)` (signed root, then cooldown).
- `finalizeVaultWithdrawal(root, tokenId)` — permissionless; transfers ERC20 back to root.
- `cashInstantWithdraw(acc, unscaledAmount, receiver)` — `onlyRouter`, used for cash swaps.

## Value transformations (where compute can err)
1. `_toScaled / _toUnscaled` — multiply/divide by `scalingFactor` (per token). Used at deposit/withdraw boundary.
2. `IMarket.orderAndOtc` — order-book matching + OTC application; settles PnL via `MarketImpliedRate`, `FIndex`, fees.
3. `MarketHubEntry._processPayFee(user, payFee)` — applies (payment, fee) pairs to `acc[user].cash`; treasury accrues fee.
4. `OTCModule._otc` — packages a single OTC trade as `OTCTrade{counter: maker, trade: opposite, cashToCounter: 0}` and routes through `MarketHub.orderAndOtc(taker, [], [], [otc])`. Cash flows ONLY through PnL accounting; no premium leg.

## RFQ-specific entry → exit chain
```
1. Off-chain: maker quotes (rate, size) for marketId, signs AcceptOTCFullMessage(trade, accountId_M, cross_M, expiry_M).
2. Off-chain: taker accepts, signs AcceptOTCFullMessage(trade, accountId_T, cross_T, expiry_T).
3. Off-chain: validator co-signs ExecuteOTCTradeMessage(makerHash, takerHash, execMsgExpiry).
4. On-chain: relayer submits Router.executeOTCTrade(req).
5. OTCModule verifies (1)(2)(3) on-chain; checks data.expiry > now.
6. _enterMarket(maker, marketId); _enterMarket(taker, marketId).
7. MarketHub.orderAndOtc(marketId, taker, [], [], [{counter: maker, trade: opposite, cashToCounter: 0}]).
8. IMarket(market).orderAndOtc(...) computes PayFee for both sides; MarketHub applies via _processPayFee.
9. Margin checks: _processMarginCheck(taker), _processMarginCheck(maker).
10. _markTradeExecuted(trade) — keyed on hashOTCTradeReq(trade); blocks replay.
```

## Fee extraction
- OTC fee: maker and taker each pay `payment + settle` fees as returned by IMarket. The fees flow to treasury via `cashFeeData[tokenId]`.
- No protocol fee on the RFQ swap leg per se beyond market-internal fees.

## Actor model
| Actor | Wants | Power | Information |
|---|---|---|---|
| Maker | Earn quote spread | Sign (via agent) AcceptOTCFullMessage | Knows their inventory, market state |
| Taker | Get desired position at fair rate | Sign (via agent) AcceptOTCFullMessage | Sees maker's quote |
| Validator (off-chain) | Maintain RFQ integrity | Co-signs every OTC msg | Sees both sides' state |
| Relayer | Submit txs | `executeOTCTrade` calldata only after off-chain agreement | Same as validator (often same entity) |
| Agent | Act as either side's signer | Per-account, per-(account,agent) authorization | Whatever maker/taker delegate |
| Account manager (root by default) | Approve/revoke agents | Sign ApproveAgentMessage / RevokeAgentsMessage | Out-of-band |
| TransparentProxy admin | Upgrade impls | Single hardcoded address | Out-of-band |

### Dual roles
- **Validator + Relayer** typically the same operator. Free option discussed below.
- **Agent + Maker** — an agent could simultaneously be a maker on the same trade if approved on multiple accounts.

## Inherent free option (not a bug)
Between maker's signing and on-chain settlement (within `expiry`), the relayer/validator decides whether to execute. If markets move, they can selectively NOT execute trades that became unfavorable. Inherent to off-chain RFQ.

## Solvency equation (per token)
```
Σ acc[*].cash + Σ_market (per-market PnL accounting consistent) ≈ MarketHub_token_balance - treasury_dust
```
Strict equality holds only if every market's matured/unmatured state is internally consistent. The protocol relies on `_processMarginCheck` and `_isMarketMatured` to enforce that closed positions settle correctly.
