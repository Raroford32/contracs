# Taint map — user-controlled inputs to dynamic dispatch / external call sites

| Strategy | Callsite | Target source | Calldata source | Value source | Safety checks |
|---|---|---|---|---|---|
| RFQ.fill | `spender.spendFromUser(takerAddr, takerAsset, amount)` | constant `spender` (operator-set, timelock) | (takerAddr, takerAsset, amount) ∈ Order — both sigs bound | n/a | maker+taker EIP712 sigs validated |
| RFQ.fill | `spender.spendFromUser(makerAddr, makerAsset, amount)` | constant | (makerAddr, makerAsset, amount) ∈ Order | n/a | maker+taker EIP712 sigs validated |
| RFQ._settle | `IERC20(makerAsset).safeTransfer(receiver, settle)` | makerAsset ∈ Order (taker-signed) | receiver ∈ Order (taker-signed) | n/a | typecheck via SafeERC20; receiver part of taker hash |
| RFQv2.fillRFQ | `_collect(takerToken, taker, maker, amount, takerPermit)` | TokenCollector enum chooses Spender / direct / permit / Permit2 | first byte of `takerTokenPermit` | depends on path | maker sig binds offerHash; if taker != msg.sender, taker sig binds rfqOrderHash |
| PMM.fill | `zeroExchange.executeTransaction(salt, this, data, "")` | constant (immutable) | `data` decoded from user payload, contains 0x v2 fillOrder | none | 0x v2 marks tx hash executed |
| PMM.fill | `IERC20(takerAsset).safeIncreaseAllowance(zxERC20Proxy, amount)` | constant | constant zxERC20Proxy | n/a | reset to 0 after zeroEx executeTransaction |
| LimitOrder.fillByTrader | `spender.spendFromUser(trader, takerToken, amount)` | constant | (trader, takerToken, amount) — trader signed | n/a | maker + taker + coordinator sigs |
| LimitOrder.fillByTrader | `spender.spendFromUser(maker, makerToken, amount)` | constant | (maker, makerToken, amount) — maker signed | n/a | maker + taker + coordinator sigs |
| LimitOrder.fillByProtocol | `protocolAddress.swap(...)` | UniV3 router OR Sushi router (only) — `_getProtocolAddress` whitelists | path / data — relayer chosen | n/a | post-swap `takerTokenOut >= takerTokenAmount` |
| AMMWrapper.trade | `weth.deposit{value: msg.value}()` | constant | n/a | msg.value (signed amount) | `require(msg.value == takerAssetAmount)` |
| AMMWrapper.trade | `spender.spendFromUser(userAddr, takerAsset, amount)` | constant | (userAddr, takerAsset, amount) — user signed | n/a | user EIP712 sig |
| AMMWrapper._tradeUniswapV2TokenToToken | `router.swapExactTokensForTokens(...)` | router == UNI_V2 / SUSHI (constants) | path[]: relayer chosen with endpoint constraints | n/a | path[0]==taker, path[-1]==maker |
| AMMWrapper._tradeUniswapV3TokenToToken | `router.exactInput(...) / exactInputSingle(...)` | router == UNI_V3 (constant) | path / single-pool data: relayer chosen | n/a | path validated endpoints |
| AMMWrapper._tradeCurveTokenToToken | `curve.exchange(i, j, amount, min)` or `exchange_underlying(...)` | `_order.makerAddr` (user-signed) | indices from `permStorage.getCurvePoolInfo(makerAddr, ...)`; pre-registered | msg.value if applicable | swap method must be 1 or 2; indices > 0 |
| Spender.spendFromUser | `allowanceTarget.executeCall(token, transferFrom)` | constant `allowanceTarget` | calldata built locally; `_user`, `msg.sender`, `_amount` | n/a | onlyAuthorized; balance delta == amount |
| AllowanceTarget.executeCall | `target.call(callData)` | UNCONSTRAINED — controlled by Spender | UNCONSTRAINED — controlled by Spender | n/a | onlySpender; Spender restricts to `IERC20.transferFrom` selector |

## Highest-blast-radius callsite: `AllowanceTarget.executeCall(target, callData)`

This is an arbitrary-call-as-AllowanceTarget primitive.  It is gated on
`onlySpender` and Spender constructs the calldata internally — the public
surface is `Spender.spendFromUser(user, token, amount)` which only
constructs `IERC20.transferFrom(user, msg.sender, amount)` data with
`target = token`.

If a future authorized strategy were added that constructs *arbitrary*
calldata to AllowanceTarget.executeCall, that strategy would be a
universal arbitrary-call primitive against any user approval.

**Watch:** `Spender.AuthorizeRequest` event for new authorizations.

## Spender approval inheritance

Every user who has ever interacted with Tokenlon has approved
`AllowanceTarget` (not Spender directly).  The set of authorized callers
on Spender effectively defines who can drain those approvals.  Currently:
`{RFQ, RFQv2 (disabled), PMM, LimitOrder, AMMWrapperWithPath}`.

If an attacker can find a flaw in *any* of those that lets them call
`spendFromUser` with arbitrary `(user, token, amount)`, the whole user
base becomes a drain target.  All five are audited above; no such flaw
found at this fork block.
