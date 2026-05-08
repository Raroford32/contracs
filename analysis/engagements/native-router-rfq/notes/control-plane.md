# Control Plane & Auth-Bypass Map — Pendle Boros RFQ

## Auth gates inventory

### A. Relayer whitelist (`onlyRelayer`)
- Storage: `_AMS().allowedRelayer[address] : bool`
- Writers: `setAllowedRelayer(address,bool)` on MISC_MODULE — gated by `onlyAuthorized` (PERM_CONTROLLER admin).
- Reach: every RFQ + signed-message entry on Router (`executeOTCTrade`, `agentExecute`, `vaultDeposit(message,sig)`, ...).
- Bypass attempts:
  - Direct call to OTC module address (bypassing Router) — fails because `_AMS()` storage of the module-as-callee is empty (storage namespacing means OTC's own storage has no relayers). ✗
  - Storage clobber via initializer reuse — MarketHub uses `_disableInitializers()` in constructor; not attempted on Router (would need similar check). Not yet verified.

### B. Maker/Taker agent signature (`_verifyAgentSig` → `_verifyAgentSoft`)
- Storage: `_AMS().agentExpiry[Account][address] : uint256`
- Set by: `_approveAgent` (validates `expiry > block.timestamp`); zeroed only by `_revokeAgent` (delete).
- **On-chain check during OTC: `agentExpiry > 0` (LOOSE — does NOT compare to block.timestamp).**
- Auto-sync rule: `_approveAgentAndSyncAMMAcc` — approving for main account ALSO approves for AMM account `(root, 255)`.
- Bypass attempts:
  - Forge sig without key — blocked by ECDSA + ERC-1271 verification. ✗
  - Submit OTC with naturally-expired but unrevoked agent — would PASS on-chain (loose check). Requires validator co-signature. **Confirmed by code reading; no on-chain test executed.**
  - Confuse `accountId=0` (main) and `accountId=255` (AMM) by leveraging auto-sync — agent's signature is bound to the specific (accountId, cross, expiry) it signed for; a different accountId would change the message hash, requiring a new signature. ✗

### C. Validator signature (`_verifyValidatorSig`)
- Storage: `_OMS().validator : address`
- Single-address. Set by `setOTCTradeValidator(address)` — `onlyAuthorized`.
- Replay: validator sig has `expiry` but no nonce — relies on `_markTradeExecuted(trade)` keyed on the OTCTradeReq hash for replay.
- Critical observation: validator is **single point of failure**. Compromise ⇒ attacker forges validator sigs ⇒ executes ANY OTC trade for accounts whose agents have nonzero `agentExpiry`.

### D. Direct MarketHub call (`onlyRouter`)
- `_checkOnlyRouter`: `msg.sender == ROUTER || _PERM_CONTROLLER.canDirectCallMarketHub(msg.sender)`
- `ROUTER` is immutable per MarketHub deployment.
- Bypass: requires PERM_CONTROLLER to whitelist attacker via `canDirectCallMarketHub`. Admin-only; not permissionlessly reachable.

### E. INITIALIZER_ROLE
- `MarketHubEntry.initialize(globalCooldown, globalMaxEnteredMarkets) external initializer onlyRole(_INITIALIZER_ROLE)`
- Constructor calls `_disableInitializers()` on impl. Proxy storage holds the initialization state.
- If proxy was already initialized (it is, since the system is operational), re-initialization is blocked.

### F. Proxy admins (TransparentUpgradeableProxy)
- MarketHub proxy admin: `0xc381b67f0289d9c1015924a0c50bb32da5265d59` (hardcoded in proxy bytecode at construction).
- Router proxy admin: `0x927ec9918e2ee4929c10b0d9f18f11452d3c25be`.
- Powers: `upgradeToAndCall` — full impl swap.
- Centralization risk recorded; not permissionlessly reachable.

## Bypass-family forcing function (results)

| Bypass family | Attempted | Result |
|---|---|---|
| init/reinit | Code-read | Blocked: `_disableInitializers()` in MarketHubEntry constructor. Router has no init that I've seen yet. |
| proxy/impl confusion | Code-read | Both Router and MarketHub use TransparentUpgradeableProxy with hardcoded admin in deploy bytecode. Standard. |
| upgrade authority drift | Not attempted | Off-scope (admin-controlled). |
| EIP-712 / signature | Code-read | Domain separator includes chainid + `address(this) = router proxy`. Type encoding correct (primary + alphabetically sorted referenced struct). No malleability (OZ ECDSA.tryRecover rejects high-s). |
| forwarder / callback | Code-read | None — relayer is the only meta-tx forwarder; whitelisted. |
| delegatecall plugin | Code-read | Router static-dispatch via `RouterFacetLib.resolveRouterFacet(sig)`; module addresses are immutable in Router impl. No plugin-clobber path. |
| bool/logic slips | Code-read | Modifiers cleanly composed: `onlyRelayer`, `onlyAuthorized`, `onlyRole(_INITIALIZER_ROLE)` — each does a single explicit `require`. |
| timelock / guard | Not in this surface | N/A on Router/MarketHub directly. |

## Conclusion
The on-chain control plane is tight for permissionless callers. Three operational concentrations of trust:
1. **Validator address** (single-key gate over all RFQ correctness)
2. **Relayer set** (liveness gate; not security gate per se)
3. **Proxy admins** (full upgrade)

No code-level bypass identified.
