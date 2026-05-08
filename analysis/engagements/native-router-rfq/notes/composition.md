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

## Final conclusion
Cross-contract composition does not produce a permissionless exploit on
this codebase. The architecture's auth boundaries are well-isolated:
- Per-module ERC-7201 storage namespaces (no slot collisions).
- Per-module deterministic dispatch (no plugin-clobber).
- Transient-storage auth context that respects EIP-1153 revert semantics.
- Two-tier sig requirement for OTC (maker/taker agent + validator).
- Strict vs soft expiry split (soft only inside off-chain-validator-gated
  surfaces).

The realistic attack vectors all reduce to off-chain key compromise
(agent / validator / admin / proxy admin / relayer). Operating-model
risks; not on-chain code defects.
