# Value flows — Tokenlon RFQ stack

## Money entry points

| Entry | Asset | Source actor | Constraint |
|---|---|---|---|
| `UserProxy.toRFQ → RFQ.fill` | takerAsset | order.takerAddr (EOA, signed) | `spender.spendFromUser(takerAddr, takerAsset, amount)` |
| `UserProxy.toRFQ → RFQ.fill` | makerAsset | order.makerAddr (signed) | `spender.spendFromUser(makerAddr, makerAsset, amount)` |
| `UserProxy.toRFQ → RFQ.fill` (ETH leg) | ETH | msg.sender via UserProxy | `msg.value == takerAmount`, wrapped to WETH |
| `UserProxy.toPMM → PMM.fill` | takerAsset | tradeInfo.user (recovered from sig) | `spender.spendFromUser(user, takerAsset, takerAmount)` |
| `UserProxy.toPMM → PMM.fill` (ETH) | ETH | msg.sender via UserProxy | wrapped, `msg.value == takerAmount` |
| `UserProxy.toLimitOrder → fillLimitOrderByTrader` | takerAsset | _params.taker (signed) | `spender.spendFromUser(trader, takerToken, takerAmount)` |
| `UserProxy.toLimitOrder → fillLimitOrderByTrader` | makerAsset | order.maker (signed) | `spender.spendFromUser(maker, makerToken, makerAmount)` |
| `UserProxy.toLimitOrder → fillLimitOrderByProtocol` | makerAsset | order.maker (signed) | `spender.spendFromUser(maker, makerToken, makerAmount)`; takerToken comes from UniV3/Sushi swap |
| `UserProxy.toAMM → trade` | takerAsset | order.userAddr (signed, no path) | `spender.spendFromUser(userAddr, takerAsset, amount)` or wrap ETH |

## Value transforms (where computation can err)

1. **AMMWrapper `_settle`** — three branches:
   - `received == makerAmount`: pass through
   - `received > makerAmount`: collect fee on receivedAmount if `(surplus*10000) > feeFactor*received`, else give user makerAmount
   - `received < makerAmount`: requires `subsidyFactor > 0` AND
     `(deficit*10000) <= subsidy*received`; protocol pays from its own balance
   ⚠ Math reviewed; no precision loss exploitable.

2. **LimitOrder fee splitting**: `takerTokenFee = takerAmount * makerFeeFactor / 10000`,
   `makerTokenFee = makerAmount * takerFeeFactor / 10000`. Standard.

3. **RFQ `_settle`**: `settleAmount = makerAmount * (10000 - feeFactor)/10000` (>=)
   delivered to receiver; the `feeFactor` portion stays in the RFQ contract
   (which doesn't accumulate per current balance probe).

4. **PMM `_settle` (0x v2)**: same fee formula as RFQ. The 0x v2 fillOrder
   already moved the maker asset to PMM; `_settle` then deducts fee and
   forwards to `tradeInfo.receiver`.

## Money exit points

| Exit | Asset | Sink | Permission |
|---|---|---|---|
| `RFQ._settle` | makerAsset | order.receiverAddr | maker+taker both signed for this exact pair |
| `PMM._settle` | makerAsset | tradeInfo.receiver | user signed `(transactionHash, receiver)` |
| `LimitOrder._settleForTrader` | makerToken (- fee) | _settlement.recipient | maker+taker+coordinator signed |
| `LimitOrder._settleForProtocol` | takerToken (- fee) | order.maker | maker+coordinator signed |
| `LimitOrder._settleForProtocol` | takerToken surplus (- profitFee) | _settlement.profitRecipient | coordinator-signed AllowFill carries no profitRecipient → **profitRecipient is chosen by the relayer at fill time**; coordinator only authorizes the *executor* (tx.origin) |
| `AMMWrapper._settle` | makerAsset | order.receiverAddr | user signed `tradeWithPermit` digest |
| `*.setAllowance` (operator) | any | externally-owned spender | onlyOperator (multisig) |

### Note on LimitOrder profitRecipient

`fillLimitOrderByProtocol` lets the relayer set `_params.profitRecipient`
freely.  The coordinator sig binds to (executor=tx.origin, fillAmount,
salt, expiry) — it does NOT bind to profitRecipient.

So *if a coordinator AllowFill leaks*, a different EOA at the same tx.origin
position cannot replay it (because allowFill binds to a specific tx.origin),
but the **legitimate relayer EOA** can choose any profitRecipient including
their own multisig.  This is by design — relayers extract the spread.

## Fee extraction

| Strategy | Fee paid by | Fee paid in | Recipient | Notes |
|---|---|---|---|---|
| RFQ | taker | makerAsset | RFQ contract (then operator sweep via setAllowance) | feeFactor is in `order.salt` low 16 bits, capped <10000 |
| RFQv2 | recipient | makerToken | feeCollector | feeFactor in offer struct |
| PMM | taker | makerAsset | PMM contract | feeFactor in `order.salt` low 16 bits |
| LimitOrder (trader) | maker (charged in takerToken) and taker (charged in makerToken) | both | feeCollector | makerFeeFactor/takerFeeFactor |
| LimitOrder (protocol) | maker (in takerToken) + relayer (profitFeeFactor on surplus) | takerToken | feeCollector | profitFee = surplus * profitFeeFactor / 10000 |
| AMMWrapper | charged on surplus when received > makerAmount | receivedAsset | AMMWrapper contract | conditional on `(surplus*10000) > feeFactor*received` |

## Actor model

| Actor | Role | Power | Multi-role conflict? |
|---|---|---|---|
| Maker | Signs Order/Offer | Decides exchange ratio, deadline, taker | n/a |
| Taker / Trader | Signs Fill/transactionHash/tradeWithPermit | Decides receiver, fill amount | Can also be the relayer |
| Coordinator | Signs AllowFill (LimitOrder only) | Permits a specific tx.origin to fill | Tokenlon-controlled key (single point of trust) |
| Relayer (tx.origin) | Submits the fill tx | Pays gas; keeps protocol-fill profit; eligible for AMM subsidy if validated | Same EOA can post their own makerSig + their own takerSig |
| Operator | Multisig | Upgrades all strategies; mints new Spender authorities (timelocked); rotates roles | Can drain all approved tokens given 1-day timelock |
| Authorized strategies (RFQ/PMM/AMM/LO/RFQv2) | `Spender.authorize`d | Permissionlessly call `spendFromUser` | No conflict — each restricted to their own auth flows |

### Maker == Taker (self-fill)

Allowed; maker and taker may be the same EOA.  Just costs gas; no
privilege escalation.

### Maker == Relayer (LimitOrder protocol fill)

`fillLimitOrderByProtocol` requires `tx.origin == coordinator-signed executor`.
If the maker is also the executor, they are essentially crossing themselves
through Uniswap — bounded by `takerTokenOut >= takerTokenAmount` and
profitRecipient is their own choice.  No drain.
