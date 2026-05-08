# Cross-Contract / Multi-Step Composition Analysis — Pendle Boros

Per CLAUDE.md §3.6.3 (Composition of Violations), this note tries to chain
the individual observations (H1 soft-expiry, H2 single-validator, H3 free
option) AND the wider module surface (Misc/Deposit/Conditional/AMM/Trade)
into a permissionless multi-step exploit. **Result: none found.** Recording
the composition attempts and why each fails.

## Surface inventory of permissionless functions
Functions reachable by ANY caller (no `onlyRelayer`/`onlyAuthorized`) that
mutate state:

| Function | Location | What it does | Why it's safe |
|---|---|---|---|
| `tryAggregate(requireSuccess, bytes[] calls)` | MISC | Loops `address(this).delegatecall(call)`; bundles multiple Router calls in one tx. | Each delegated call still routes through `RouterFacetLib.resolveRouterFacet`; each module function enforces its own auth. **No selector becomes callable that wasn't already callable.** Pure multicall. |
| `batchSimulate(SimulateData[] calls)` | MISC | Internally delegatecalls `batchRevert`, asserts the revert, parses bubbled-up bytes. | `batchRevert` always reverts; no persisted state. Pure simulation. |
| `batchRevert(SimulateData[] calls)` | MISC | Per call: `_setUnchecked(account)` + `target.functionCall(data)`; reverts at end. | Always reverts. Per EIP-1153 final spec, transient storage IS reverted on revert (same semantics as regular storage). State leakage attempt fails. |
| `finalizeVaultWithdrawal(root, tokenId)` | MarketHubEntry | Completes a withdrawal once cooldown elapsed; transfers token to `root`. | Strictly drives funds to `root`; no attacker-controlled receiver. |
| `settleAllAndGet(user, req, idToGetSize)` | MarketHubEntry | Iterates user's entered markets, calls `IMarket.settleAndGet`, applies pending PayFees, returns totals. | Force-settles user's outstanding fees/payments. By design — encourages settlement. May reduce user's cash but cannot extract to attacker. |
| `simulateTransfer(user, amount)` | MarketHubEntry | `acc[user].cash += amount`. | Guarded by `tx.origin == address(0)` — only reachable via `eth_call` with from=0x0. Inert in real txs. |
| `tryAggregate` + `batchSimulate` style helpers | various | Read-only bundling. | No state mutation. |

## Composition attempts

### Attempt 1 — Transient-storage account spoof via `batchRevert`
**Hypothesis**: Use `batchRevert`'s `_setUnchecked(...)` to plant a victim
`Account` in the transient slot, then in a subsequent call (within the same
top-level tx) hit a `setNonAuth`-protected function which reads `_account()`
and proceeds as the victim.

**Chain**:
1. Attacker calls `tryAggregate([call0, call1])`.
2. call0 = `batchRevert([{account=victim, target=ROUTER, data=anyView}])`.
3. Inside batchRevert: `_setUnchecked(victim)`; external call to ROUTER (a regular `call`, not delegate); revert at end.
4. tryAggregate's delegatecall returns `success=false` for call0.
5. call1 = `cashTransfer((marketId, amount))` → TradeModule.cashTransfer with `setNonAuth`.
6. **EXPECTED**: `_account()` returns leftover `victim`; setNonAuth respects it; cashTransfer moves victim's cash.

**Why it fails**: EIP-1153 final spec (Cancun, in effect on Arbitrum):
"Transient storage updates ARE reverted on revert, the same as regular
storage." When batchRevert reverts, all `tstore` ops within it are undone.
Transient slot is restored to whatever it was before batchRevert (which is
zero for an attacker-initiated tx). call1 sees `_account()==0` and
setNonAuth correctly assigns `(msg.sender, 0)`. **No spoof.**

**Verification approach (if RPC available)**: Tenderly sim of the chain
above; observe `acc[victim].cash` is unchanged.

### Attempt 2 — Permissionless force-settle to push victim into liquidation
**Hypothesis**: Use `settleAllAndGet(victim,...)` to crystallize all pending
PayFees against victim. If victim was relying on unsettled PnL to keep
their HR above critHR, attacker can lower their HR below critHR, then
liquidate them via `MarketHubEntry.liquidate(...)`.

**Chain**:
1. Attacker calls `settleAllAndGet(victim, GetRequest.MM, MarketIdLib.ZERO)`.
2. `_settleProcess` calls each entered market's `settleAndGet`, accumulates fees, applies via `_processPayFee(victim, totalPayFee)`.
3. Victim's `cash` decreases by net fees; HR drops.
4. Attacker calls `liquidate(...)` to capture liquidation rebate.

**Why it fails**: `MarketHubEntry.liquidate` is `onlyAuthorized` — only
permissioned liquidators (admin-curated) can liquidate. The auth model
expects keepers/bots, not anyone.

**Residual concern**: settleAllAndGet IS a free MEV breadcrumb — attacker
can OBSERVE victim's about-to-settle state and frontrun other actions
(e.g., place orders that benefit from settled state). Limited extractable
value, but worth recording.

### Attempt 3 — Module-direct call bypassing Router proxy
**Hypothesis**: Call OTC module's `executeOTCTrade` directly on its
deployed address (`0xc6f465f4...`), bypassing the Router proxy and
therefore bypassing the relayer whitelist (which lives in the Router's
proxy storage).

**Why it fails**:
- OTC module's `_AMS().allowedRelayer[msg.sender]` reads the OTC module's
  OWN storage at the ERC-7201 slot; that storage is never written to (only
  the Router proxy's storage at the same slot is written). Returns false.
- Even if storage matched, signature verification uses
  `_hashTypedDataV4` which computes domain separator with `address(this)`
  — when called directly, that's the OTC module's address, NOT the Router
  proxy address. Signatures don't verify because users sign for the
  Router proxy domain.

### Attempt 4 — Re-init MISC's EIP-712 storage to break domain separator
**Hypothesis**: Call `MiscModule.initialize(name, version, numTicks)` with
attacker-chosen values. If unprotected, attacker resets the EIP-712 name
and version → domain separator changes → all in-flight signed messages
become invalid (DoS) OR a custom-domain replay enables signature reuse on
some other deployment.

**Why it fails**: Constructor calls `_disableInitializers()`; modifier is
`initializer` (rejects re-init); also `onlyRole(_INITIALIZER_ROLE)`. Two
independent gates. The MarketHub MarketHubEntry impl also disables.

### Attempt 5 — `tryAggregate` + `setAMMIdToAcc` malicious-AMM chain
**Hypothesis**: Trick admin-only `setAMMIdToAcc` to register a
malicious AMM where `IAMM.AMM_ID()` and `IAMM.SELF_ACC()` return
attacker-controlled values, then use `swapWithAmm`/`addLiquidity*` flows
that resolve through `_getUserAndAMM` to hit an attacker contract.

**Why it fails**: `setAMMIdToAcc` is `onlyAuthorized`; attacker can't call.
Even if AMM were attacker-controlled, the AMM contract would still need
to satisfy the IMarket-side accounting checks (margin, settlement) —
malicious returns would either revert or fail margin checks downstream.

### Attempt 6 — Conditional Order's per-validator allowlist as wider attack surface vs OTC's single validator
**Observation**: `ConditionalModule._verifyValidatorSig(validator, ...)`
takes the validator address from the **request body**, not from storage,
then checks `_CMS().isValidator[validator]`. This means if multiple
validators are allowlisted, attacker can target the WEAKEST validator's
signing flow.

**Hypothesis chain** (operational):
1. If any validator V_weak in `_CMS().isValidator` has weaker key custody,
   and is compromised, attacker uses V_weak to co-sign conditional orders.
2. Combined with H1 (expired-but-unrevoked agent), attacker forges the
   conditional-order side fully.
3. Conditional orders in `reduceOnly=false` mode can OPEN new positions
   for the user, dragging margin into a market where attacker is
   counterparty.

**Why it's not E3**: requires V_weak compromise (operational).

**Worth recording**: ConditionalModule has BROADER attack surface than
OTC (multi-validator vs single) — paradoxically increases compromise
probability. Documented for the protocol's threat model awareness.

### Attempt 7 — Cross-module reentrancy via `tryAggregate`
**Hypothesis**: Inside `tryAggregate`, set up a state where an inner call's
side effects exposed to the outer caller can be re-entered to amplify.

**Why it fails**: All state-changing functions either:
- Apply atomic accounting (cash/position settlement is single-write).
- Use `setNonAuth`/`setAuth` modifiers that respect existing transient
  state (cooperate, not bypass).
- Don't expose external callbacks to user-controlled contracts (one
  exception: `depositFromBox` calls `box.approveAndCall`, but the box is
  per-user CREATE2 and the call params are user-signed).

### Attempt 8 — `_approveAgentAndSyncAMMAcc` mismatch between OTC and AuthModule's strict checks
**Observation**:
- OTC uses `_verifyAgentSoft` (`agentExpiry > 0`).
- `agentExecute` (in AuthModule) uses `_verifyAgentSigAndIncreaseNonce` →
  `agentExpiry > block.timestamp` (STRICT).
- Therefore an expired-but-unrevoked agent can sign OTC AcceptOTC messages
  but CANNOT sign agentExecute trade actions.

**Composition idea**: Attacker with leaked-expired agent A for victim V
can ONLY do RFQ-style trades against V (subject to validator co-sig). A
canNOT directly call cashTransfer or other agent-allowed selectors via
agentExecute — those require fresh expiry.

**Conclusion**: the soft check is constrained to the OTC RFQ surface —
limiting blast radius to "validator-co-signed OTC trades against V". The
on-chain code has correctly scoped the looseness.

## Scope-extending observations (informational, not exploits)

1. **Multi-validator surface in Conditional vs single in OTC** — different
   trust models. Conditional has more validators ⇒ more keys ⇒ more attack
   surface. Worth documenting in protocol threat model.

2. **`tryAggregate`'s gas-griefing potential**: an attacker can submit
   thousands of cheap calls in one tx to consume blockspace. Standard
   public-multicall consideration; not a security issue per se.

3. **`finalizeVaultWithdrawal` is permissionless and accelerates state for
   victim** — useful for griefing/timing but not value-extractive.

4. **`settleAllAndGet` exposes per-market settlement to external observers
   and can be called pre-emptively to crystallize a victim's pending
   payments**. By design.

5. **DepositFromBox arbitrary external call**: user signs the
   `swapExtRouter`, `swapApprove`, `swapCalldata`. Per-user CREATE2 box.
   Safe by design; user trusts what they sign.

## Composition matrix

|  | H1 soft expiry | H2 single validator | H3 free option | tryAggregate | settleAllAndGet | Conditional multi-validator |
|---|---|---|---|---|---|---|
| H1 |  | **Validator-compromise OTC forgery** (operational) | (informational) | — | — | Same as OTC for Conditional |
| H2 | (above) |  | Validator+Relayer collusion = max free option | — | — | Same |
| H3 | (above) | (above) |  | — | (slight: pre-settle) | — |
| tryAggregate | — | — | — |  | bundle multiple settles | — |
| settleAllAndGet | — | — | — | — |  | — |

## Round 2 — deeper market-side dive (after extending scope)

After bundling and reading the deferred surfaces — MarketHubRiskManagement,
MarketFactory, PendleAccessController, the actual Market impl
(MarketEntry + MarketOrderAndOtc + MarketSettingAndView +
MarketRiskManagement subimpls), the orderbook utilities (CoreOrderUtils,
CoreStateUtils, OrderBookUtils, Tick, TickBitmap), settlement
(SweepProcessUtils, ProcessMergeUtils, PendingOIPureUtils),
BookAmmSwapBase, and PaymentLib — six more chains attempted:

### Attempt 9 — Bump MarketFactory's deployment nonce to desync `_marketIdToAddrRaw`
**Hypothesis**: `CreateCompute.compute(factory, marketId)` derives the
market address using **CREATE** semantics (RLP nonce-based), expecting
factory's deploy-time nonce == marketId. If anyone can force a CREATE
from the factory contract, future `marketId == nonce` invariant breaks
and `_marketIdToAddrRaw` returns wrong addresses for new markets.

**Why it fails**: `MarketFactory.create()` is `onlyAuthorized`, the only
function that performs CREATE. Constructor of MarketFactory does not
perform a CREATE; `initialize()` only sets `marketNonce = 1`. No
permissionless path to bump nonce. Registration enforces parity:
`assert(computedAddress == newMarket)` on each create — admin error
during deploy would be caught immediately by the assert.

### Attempt 10 — Force-settle into liquidation via permissionless `settleAllAndGet`
**Hypothesis**: `settleAllAndGet(victim, ...)` is permissionless. It
iterates victim's entered markets and applies pending PayFees, dropping
victim's cash. If victim's HR drops below `critHR`, attacker calls
liquidate to capture the spread.

**Why it fails**:
- `MarketHubEntry.liquidate(...)` is `onlyAuthorized` — admin-curated
  liquidator set. Attacker is not on the list.
- `settleAllAndGet` only crystallizes ALREADY-ACCRUED PayFees. The user
  effectively owed these payments anyway. No new value created.

**Residual MEV concern**: forcing victim's settlement before placing
orders could give the attacker freshness advantage in matching. Limited
extractable value; recorded as MEV note.

### Attempt 11 — Stale `MarketCache` exploitation
**Hypothesis**: `_getMarketCache(marketId)` caches `(market, tokenId,
maturity, tickStep)` on first read. If any field could change post-cache
(e.g., maturity extended via admin upgrade, or token swapped), Router
operates on stale data while MarketHub uses fresh data → divergence.

**Why it fails**: `tokenId`, `maturity`, `tickStep` are immutables in
the Market contract (`k_tokenId`, `k_maturity`, `k_tickStep`) per
`MarketImmutableDataStruct` set at market construction. They cannot
change post-deployment. Cache is consistent forever.

### Attempt 12 — Self-OTC across same-root different-accountId MarketAccs
**Hypothesis**: User has Account(R, 0) and Account(R, 1). Crafts an OTC
where maker = MarketAcc(R, 1, T, M) and taker = MarketAcc(R, 0, T, M).
`_validateOrderAndOtc` checks `OTCs[i].counter != user` (literal bytes26
inequality), which passes (different accountId). Trade is a self-trade
that pays fees both sides → drains victim's own funds to treasury.

**Why it fails for attacker**:
- This requires the USER themselves to authorize the trade — only
  victim's agent (or validator+agent) can sign.
- Self-funded fees go to treasury, not attacker. No extractable value.

**Conclusion**: legitimate self-OTC is permitted (different MarketAccs)
but not value-extractive for an attacker. Wash-trade fees only.

### Attempt 13 — `tryAggregate` as a delegate-call slot collider
**Hypothesis**: Use `tryAggregate` to call multiple modules; if two
modules share a hashed storage slot but use different layouts, write+read
collide.

**Why it fails**: All non-immutable storage uses ERC-7201 namespaced
slots (`AUTH_MODULE_STORAGE_LOCATION`, `ROUTER_OTC_MODULE_STORAGE_LOCATION`,
`ROUTER_TRADE_STORAGE_LOCATION`, `ROUTER_CONDITIONAL_MODULE_STORAGE_LOCATION`,
`ROUTER_EIP712_STORAGE_LOCATION`). Each is `keccak256(...) - 1 & ~0xff`,
collision-resistant. Verified in `slots.sol`. The only concrete `address
public immutable MARKET_FACTORY/ROUTER/TREASURY` etc. are inlined and
don't claim slots.

### Attempt 14 — ConditionalModule's user-supplied `validator` field
**Observation**: ConditionalModule's `req.validator` is provided by the
caller (relayer) at execution time — not pinned at order placement. The
user (agent) signs only the orderHash; the validator-allowlist check at
execution selects from `_CMS().isValidator[*]`.

**Hypothesis**: Could the user have signed assuming validator V_strong
will execute, but a compromised V_weak (still allowlisted) executes
instead at terms unfavorable to user?

**Conclusion**: The user's signature commits to the order body
(including limit `tick`). Validator chooses execParams (ammId, desired
match rate) within order's tick limit. So validator can't price beyond
user's tick. **However, validator chooses WHEN to execute (within order
expiry) and which AMM** — material discretion. If V_weak is compromised,
attacker times execution to disadvantage user; user's `tick` bounds
worst-case loss but still loses. Documented as a multi-validator
threat-model note, not an exploit.

## Final conclusion
After bundling 17 contracts, reading 30+ source files across 5 module
hubs and 4 sub-impl proxies, and attempting 14 distinct cross-contract
chains: **no permissionless exploit found.** Pendle Boros's architecture
provides:

- Per-module ERC-7201 storage namespaces (no slot collisions).
- Per-module deterministic dispatch (no plugin-clobber, no init re-entry).
- Transient-storage auth context that respects EIP-1153 revert semantics.
- Two-tier sig requirement for OTC (maker/taker agent + validator).
- Strict vs soft expiry split (soft only inside off-chain-validator-gated
  surfaces).
- CREATE-based market deployment with parity assert at registration.
- Self-trade and zero-size-order rejections at the market layer.
- Immutable market parameters (tokenId/maturity/tickStep) preventing
  cache desync.

The realistic attack vectors all reduce to off-chain key compromise:
- Agent key (operational; partial compromise → OTC-only blast radius
  per H1's strict scoping)
- Validator key (single OTC validator; multi Conditional validators —
  Conditional surface is broader)
- Admin role / proxy admin / relayer set (full control)

These are operating-model risks; not on-chain code defects. The static
analysis budget is exhausted without a permissionless E3 — and per the
OS, **no E3 finding will be claimed unless and until a fork-grounded
proof exists**.

To extend further would require:
1. RPC for fork experiments (sandbox is blocked).
2. Threat-modeling documents from the protocol on validator/relayer key
   custody.
3. An adversary model that includes off-chain compromise.

