# Hypotheses — Tokenlon RFQ stack

Hypotheses generated from the assumption-violation analysis on the RFQ
swap-proxy surface.  All falsified at fork_block 25,050,789.

---

## H1 — Maker-sig replay across orders due to missing receiver in RFQ orderHash

**Broken assumption (hypothesized):** the RFQ maker's signature does not
commit to the receiver, so an attacker who learns a maker signature can
fill the order with their own receiver.

**Reasoning chain:**
1. RFQ.ORDER_TYPEHASH includes: takerAddr, makerAddr, takerAssetAddr,
   makerAssetAddr, takerAssetAmount, makerAssetAmount, salt, deadline,
   feeFactor.  Note: **no `receiverAddr`**.
2. RFQ.FILL_WITH_PERMIT_TYPEHASH (signed by taker) DOES include receiverAddr.
3. The taker signature would still be required because `isValidSignature(takerAddr, fillDigest, ...)` is enforced.
4. So: even though maker did not bind receiver, the *taker* did.  The
   attacker would need to steal the taker's signature too.

**Failed because:** taker sig is required and binds receiver.  Maker sig
also binds takerAddr (so cannot be reused with a different taker).

**Insight:** the asymmetric receiver-commitment is intentional — the maker
delegates choice of receiver to the taker, whom the maker has agreed to
trade with by name.

---

## H2 — Cross-strategy replay via shared EIP712 domain (Tokenlon v5)

**Broken assumption:** all five Tokenlon strategies share the same EIP712
domain name+version, so a maker-signed RFQ.Order looks like a LimitOrder.Order.

**Reasoning chain:**
1. EIP712Domain = (name, version, chainId, verifyingContract).
2. name = "Tokenlon", version = "v5" — same in RFQ, RFQv2, PMM, LimitOrder, AMMWrapper.
3. **But** verifyingContract is set to `address(this)` in each constructor.
4. RFQ.address ≠ LimitOrder.address ≠ AMMWrapper.address ≠ RFQv2.address.
5. domain separator differs → digest differs → signatures don't cross.

**Failed because:** verifyingContract differs.

---

## H3 — AMMWrapper user-supplied path not signed → relayer drains user

**Broken assumption:** the user signs only takerAsset, makerAsset, amounts;
the relayer can pick a `_path` through any tokens.

**Reasoning chain:**
1. AMMWrapper.trade takes `address[] _path` as a separate parameter.
2. `_verify` hashes only the `tradeWithPermit` typehash fields — NO `_path`.
3. So a relayer could build a path that routes through a token whose
   transfer hook drains the AMMWrapper or charges absurd fees.
4. But: `_validatePath` enforces `_path[0] == takerAsset` and
   `_path[last] == makerAsset` (V2/Sushi); V3 path validated similarly.
5. Curve uses pre-registered pools indexed by maker addr; user signed maker addr.
6. Final guard: `receivedAmount = amounts[last]` from router; the user gets
   `>= makerAssetAmount * (10000 - subsidyFactor) / 10000`.
7. For a non-validated relayer, subsidy=0 → user gets >= makerAmount.
8. For a validated relayer, max subsidy is bounded by `subsidyFactor`.

**Failed because:** endpoints validated, output minimum enforced, subsidy
bounded.  A toxic mid-path token can only damage the user's gas — not steal
their tokens — because the swap reverts if the final output is too low.

**Residual concern:** middle hops via fee-on-transfer or
deflationary tokens could lower receivedAmount below minimum and
revert (just gas waste, not exploit).  Confirmed acceptable.

---

## H4 — RFQv2 `_offer.taker == msg.sender` skip lets attacker fill without taker sig

**Broken assumption:** if a maker sets `_offer.taker = userProxy_address`,
ANYONE can call fillRFQ via UserProxy and skip the taker-signature path.

**Reasoning chain:**
1. In RFQv2.fillRFQ: `if (_offer.taker != msg.sender) require(takerSig)`.
2. `msg.sender` is always the UserProxy address (because `onlyUserProxy`).
3. So setting `_offer.taker = userProxy_address` skips taker-sig requirement.
4. But the next step is `_collect(takerToken, _offer.taker, _offer.maker, takerAmount, takerTokenPermit)`
   — this pulls from `_offer.taker` = userProxy.
5. UserProxy holds no tokens and has no Spender approvals.

**Failed because:** the "no-taker-sig" branch tries to pull from a contract
(UserProxy) that has nothing to pull. Plus RFQv2 is currently disabled.

---

## H5 — Permit2 SignatureTransfer replay across spenders

**Broken assumption:** a Permit2 signature given for one swap could be
replayed via a different spender contract.

**Reasoning chain:**
1. Permit2.permitTransferFrom (SignatureTransfer) binds permit hash to:
   `(token, amount, nonce, deadline, spender = msg.sender of permit2)`.
2. spender == RFQv2 (the contract calling permit2).
3. nonce is unordered (single-use); replaying the same nonce reverts.

**Failed because:** Permit2 binds spender.

---

## H6 — Wallet-mode (1271) signature bypass via empty-returndata wallet

**Broken assumption:** SignatureValidator.isValidWalletSignature with a
signer that's an EOA (no code) silently accepts any signature.

**Reasoning chain:**
1. Type 6 (Wallet) calls `isValidWalletSignature(hash, signerAddr, sig)`.
2. Inline assembly does:
   - `if iszero(extcodesize(walletAddress)) { revert WALLET_ERROR }`
   - `staticcall(...)` with 32-byte output buffer
   - `if iszero(eq(returndatasize(), 32)) { revert WALLET_ERROR }`
   - magic prefix check via 4-byte AND.
3. EOA signer fails extcodesize check.  Contract that returns wrong
   length fails returndatasize check.

**Failed because:** explicit guards.

---

## H7 — Cancel-order signature reuse (zero-amount fills)

**Broken assumption:** cancellation works by maker signing a copy with
`takerTokenAmount=0`; could that "cancellation" signature be replayed as
an actual fill?

**Reasoning chain:**
1. `cancelLimitOrder(order, sig)`: in-memory copy `cancelledOrder.takerTokenAmount = 0`,
   recompute orderHash on the modified copy, require maker sig matches.
2. The cancel hash differs from the original orderHash, so the cancel sig
   can't be used to fill the original order.
3. Conversely, the original-order maker-sig is invalid for the cancel hash.

**Failed because:** distinct orderHashes.

---

## H8 — LimitOrder protocol-fill drain via toxic UniV3 path

**Broken assumption:** `_params.data` (UniV3/Sushi swap path) is not
signed by the maker, so a malicious relayer can use a toxic path to
extract value from the LimitOrder contract.

**Reasoning chain:**
1. `fillLimitOrderByProtocol` accepts `ProtocolParams` with a free-form
   `data` field used as the swap path/data.
2. `_settleForProtocol`: `spender.spendFromUser(maker, makerToken, makerAmount)`
   places makerToken in the LimitOrder contract.
3. `_swapByProtocol(...)` swaps to takerToken; result `takerTokenOut`.
4. `require(takerTokenOut >= takerTokenAmount)` — must produce at least
   the maker's signed minimum.
5. Surplus → profitRecipient (chosen by relayer); makerAmount-minus-fee → maker.
6. LimitOrder contract balance after fill = 0.  No state retained.

**Failed because:** post-condition `takerTokenOut >= takerTokenAmount`
enforces maker's minimum; no balance accumulates that could be drained
in subsequent fills.

---

## H9 — AMMWrapper subsidy-reserve drain by a registered relayer

**Hypothesis:** a registered relayer EOA (validated in PermStorage) can
deliberately route a path that underperforms by exactly `subsidyFactor`,
and AMMWrapper subsidizes the shortfall from its own reserves
(currently $190K).

**Reasoning chain:**
1. Validated relayer: `subsidyFactor` applied; user gets makerAmount even
   if AMM swap returns less, with AMMWrapper paying the difference.
2. Per trade, max subsidy = `makerAmount * subsidyFactor / 10000`.
3. With `subsidyFactor` typically 100bp (1%), every trade can extract
   ~1% of makerAmount from AMMWrapper reserves.

**Status:** **NOT permissionless.** Requires a registered relayer EOA.
Operator controls the relayer set.  If the operator's keepers are
compromised, this is a slow drain bounded by user-signed orders.

**Action:** documented as feasibility concern; not E3.

---

## H10 (open) — 0x v4 OtcOrders (`0xDef1C0ded9bec7F1a1670819833240f027b25EfF`)

**Hypothesis:** ZeroExProxy's OtcOrdersFeature is a custom RFQ proxy
that has had historical signature-reuse issues (e.g. `expiry` and
`nonceBucket` packing edge cases).  Worth a separate engagement; out
of scope for this session because it is not a Tokenlon contract.

**Status:** parked for follow-up.
