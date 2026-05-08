# Memory (tokenlon-rfq-2026-05-08)

## Pinned Reality
- chain_id: 1
- fork_block: 25,050,789  (2026-05-08 latest)
- attacker_tier: public mempool — anyone can call `UserProxy.toRFQ / toRFQv2 / toPMM / toAMM / toLimitOrder` from any EOA
- capital_model: irrelevant — no flaw found that requires capital

## Contract Map Summary

```
                          +-------------------------+
                          | UserProxy (TUP proxy)   |  0x03f34bE1...59659
                          | impl 0x0b9f13ff...675a  |
                          +---+---------+-----------+
                              |         |
            +-----------------+         +-----------------+
            v                 v                           v
+-----------+----+   +--------+--------+    +-------------+--+
| RFQ            |   | RFQv2 (DISABLED)|    | PMM (0x v2)    |
| 0xfd6c2d24...  |   | 0x91c98670...   |    | 0x8d901131...  |
+----+-----------+   +--------+--------+    +-------+--------+
     |                        |                     |
     |                        v                     v
     |              +-----------------+   +---------------------+
     |              | Permit2-supported|  | 0x v2 Exchange      |
     |              | TokenCollector   |  | + zxERC20Proxy      |
     |              +-----------------+   +---------------------+
     |
     v
+----+-----------+   +-----------------+   +-----------------+
| LimitOrder     |   | AMMWrapperWPath |   | Spender         |
| 0x623a6b34...  |   | 0x4a143470...   |   | 0x3c68dfc4...   |
+----+-----------+   +--+--------------+   +--------+--------+
     |                  |                           |
     |                  v                           v
     |    +-------------+--------+      +-----------+--------+
     |    | UniV2/V3/Sushi/Curve |      | AllowanceTarget    |
     |    +-------------+--------+      | 0x8a42d311...      |
     |                                  +-----------+--------+
     |                                              |
     v                                              v
+----+-----------+                    +-------------+--------+
| UniV3 router or |                   | User approvals (any  |
| Sushi router    |                   | ERC20 ever traded by |
| (settlement leg)|                   | a Tokenlon user)     |
+-----------------+                   +----------------------+

PermanentStorage (TUP proxy 0x6d9cc14a... -> impl 0x32c1f83d...) holds:
  - per-strategy {transactionSeen, allowFillSeen, filledOffer} replay sets
  - relayer validity
  - Curve pool index registrations
  - operator+role permissions (storageId based)
```

## Authority / Privileges (live)
- operator across all strategies = `0x63ef071b8a69c52a88dca4a844286aeff195129f` (Gnosis Safe multisig)
- isPMMEnabled = 1, isAMMEnabled = 1, isRFQEnabled = 1, isLimitOrderEnabled = 1, isRFQv2Enabled = 0
- Spender.isAuthorized(RFQ|PMM|AMM|RFQv2|LimitOrder) = true (all five)
- AllowanceTarget.spender = Spender
- coordinator (LimitOrder) = off-chain signer key controlled by Tokenlon backend

## Live token custody (latest block)
- RFQ: 0
- PMM: 2.17 ETH, 19.02 WETH, 84,244 USDT, 103,612 DAI, 2,877 USDC, 0.0073 WBTC  (~$120K accumulated fees)
- AMMWrapperWithPath: 0.017 ETH, 7.61 WETH, 51,490 USDT, 153,752 DAI, 1,889 USDC, 0.022 WBTC  (~$190K accumulated fees)
- LimitOrder: 0 (dust)
- Spender: 0
- AllowanceTarget: 953 USDT (residual)
- PermanentStorage: 0

The $300K+ in PMM+AMM are accumulated protocol fees, only extractable by the
operator multisig via `setAllowance` + an externally-owned spender.  No public
entry point sends those balances out except as part of legitimate maker-asset
settlement (i.e. the user must already have signed an order whose makerAsset
is exactly the token being drained).

## Signature surfaces audited (per strategy)

| Strategy | Maker sig | Taker sig | Coordinator sig | Replay anchor | Anti-replay store |
|---|---|---|---|---|---|
| RFQ | EIP712 over Order (no receiver) | EIP712 over fillWithPermit (incl receiver) | n/a | tx hash incl receiver | `setRFQTransactionSeen` |
| RFQv2 (off) | EIP712 over Offer | EIP712 over RFQOrder (incl recipient) | n/a | offer hash | `setRFQOfferFilled` |
| PMM (0x v2) | maker via 0x v2 fillOrder.signature | EIP712 over ZeroExTransaction | n/a | 0x v2 `transactions[hash].executed` | 0x v2 ZeroExchange |
| LimitOrder | EIP712 over Order | EIP712 over Fill (per-fill) | EIP712 over AllowFill | both fill+allowFill | `setLimitOrderTransactionSeen` + `setLimitOrderAllowFillSeen` |
| AMMWrapperWithPath | n/a (maker is Uni/Sushi/Curve) | EIP712 over tradeWithPermit (no path) | n/a | tx hash without path | `setAMMTransactionSeen` |

EIP712 domain separator per strategy = (`Tokenlon`, `v5`, chainId, address(this)).
No two strategies share both name+version+address, so no cross-strategy replay.

## Value Model Summary (custody vs entitlements)

custody:
- AllowanceTarget holds the *approval rights* to pull tokens from any user that
  has ever interacted with Tokenlon.  It does NOT hold tokens itself except
  whatever dust gets stuck.
- PMM and AMMWrapperWithPath accumulate FEE residuals as actual tokens.

entitlements:
- A Tokenlon user (maker or taker) is entitled to receive the assets specified
  in their EIP712-signed order, minus the fee factor encoded into that order.
- The operator multisig is entitled to sweep the fee residuals via setAllowance.

solvency equation (per fill):
  `taker_paid + maker_paid == taker_received + maker_received + fees_collected`

Each strategy preserves this invariant by atomic `_collect`+`_settle` pairs.

## Hypothesis matrix (status after deep audit)

| # | Hypothesis | Verdict | Evidence path |
|---|------------|---------|---------------|
| H1 | Maker-sig replay across orders due to missing receiver in RFQ orderHash | Falsified — receiver is in *transaction* hash + permStorage replay set, taker sig binds to recipient | notes/hypotheses.md H1 |
| H2 | Cross-strategy replay (RFQ ↔ LimitOrder ↔ AMM) via shared EIP712 name/version | Falsified — `verifyingContract` differs per strategy → different domain separator | notes/hypotheses.md H2 |
| H3 | AMMWrapperWithPath user-supplied `_path` not in signed tx-hash → relayer can drain user via toxic mid-path token | Falsified — `_path[0]==takerAsset`, `_path[last]==makerAsset` (V2/V3/Sushi); Curve uses pre-registered pools; user-protected by `receivedAmount >= makerAssetAmount * (10000-subsidy)/10000` | notes/hypotheses.md H3 |
| H4 | RFQv2 `if (_offer.taker != msg.sender)` lets attacker skip taker sig when taker == userProxy address | Falsified — userProxy holds no tokens, `_collect` from userProxy reverts on insufficient balance/allowance | notes/hypotheses.md H4 |
| H5 | Permit2 `Permit2SignatureTransfer` replay across spenders | Falsified — Permit2 binds permit to caller (RFQv2), single-use nonce | notes/hypotheses.md H5 |
| H6 | SignatureValidator wallet-mode (Type 6) extcodesize bypass via empty-returndata wallet | Falsified — explicit `iszero(extcodesize)` revert + `eq(returndatasize(), 32)` revert + magic prefix check | notes/hypotheses.md H6 |
| H7 | Cancel-order signature reuse: signed Order with takerTokenAmount=0 looks like a cancel, but maker-only fills with takerTokenAmount=0 might be filled too | Falsified — `_quoteOrder` requires `takerTokenAmount > 0` and order amount comparisons fail for cancellation copies | notes/hypotheses.md H7 |
| H8 | LimitOrder protocol-fill subsidy/profit drain via toxic UniV3 path (path is signed only by coordinator) | Falsified — `takerTokenOut >= takerTokenAmount` is required after swap; profit goes to `profitRecipient` (signed by coordinator); protocol holds no balance to drain | notes/hypotheses.md H8 |
| H9 | AMMWrapper subsidy reserve drain by malicious validated relayer | Conditional — possible only if a relayer EOA is compromised; bounded by `subsidyFactor * makerAssetAmount` per trade; not permissionless | notes/feasibility.md |

**Conclusion:** No permissionless E3 exploit found in the Tokenlon RFQ family
at fork_block 25,050,789.  The system is effectively a closed economic
sandbox where the only assets at risk per fill are exactly the assets the
maker and taker have *both* signed for, and replay is closed at the
PermanentStorage level per-strategy.

## Cross-protocol composition surface (residual interest)

Even with no single-contract flaw, the *shared Spender + AllowanceTarget* is
the largest blast-radius primitive.  Any future authorized strategy added
to Spender (`Spender.authorize(...)` is timelocked but not bounded in scope)
inherits the right to call `transferFrom` against every user approval ever
granted to AllowanceTarget.  This is the single watch-this-contract item
for ongoing monitoring:

```
WATCH: Spender.authorize(...)        — new strategy = expanded blast radius
WATCH: AllowanceTarget.setSpenderWith… — new spender = re-rooted approvals
WATCH: PermanentStorage.upgradeRFQ/PMM/AMM/LO/RFQv2 — strategy upgrade
WATCH: PMM/AMMWrapper.upgradeSpender — strategy redirected to a new spender
```

## Last Experiment (cheapest discriminator)
- Question: are there any non-fee tokens accumulating in any Tokenlon
  contract that could be permissionlessly drained by signing an RFQ
  matching the residual?
- Method: query balanceOf(WETH/USDT/DAI/USDC/WBTC) on every Tokenlon
  contract at latest block (above).
- Result: only AMMWrapper+PMM hold material balances (~$300K combined),
  and those are protected by the strategy's `_settle` accounting.
- Belief change: confirmed value-at-risk is bounded by maker+taker
  signature pair per fill; no public extraction primitive exists.

## Next Discriminator (if continued)
- Hypothesis to push next: 0x v4 OtcOrders / RfqOrders on `0xDef1C0ded9bec7F1a1670819833240f027b25EfF`
  — older 0x v4 RFQ paths have known signature-reuse foot-guns when
  combined with Settler routing.  Not Tokenlon, but a custom RFQ proxy
  surface used by 1inch / 0x API / Matcha.
- Also: monitor Spender.authorize events for any new strategy.

## Open Unknowns
- The off-chain `coordinator` signer (LimitOrder) — if its key leaks, an
  attacker can sign arbitrary AllowFill grants for `executor = victim_relayer`,
  but the maker/taker signatures are still required.  Risk is upstream.
- Tokenlon AMMWrapper depends on `permStorage.isRelayerValid(tx.origin)` —
  if PermStorage role permissions are misconfigured (e.g. operator lost or
  compromised), an attacker could mark themselves as a valid relayer and
  capture subsidy.  Currently sound.
