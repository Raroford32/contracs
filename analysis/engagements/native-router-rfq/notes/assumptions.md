# Assumption Enumeration — Pendle Boros RFQ

Format per assumption:
```
A#: [statement]
EVIDENCE: [code location]
VIOLATION CONDITION: [what must be true for it to be false]
CONSEQUENCE: [what breaks economically]
VIOLATION FEASIBILITY: [permissionless / requires-key / requires-admin]
```

---

A1: An EOA with `agentExpiry[acc][agent] > 0` is a CURRENTLY-VALID signer for OTC AcceptOTCFullMessages on behalf of `acc`.
- EVIDENCE: `OTCModule._verifyAgentSig` → `AuthBase._verifyAgentSoft` (only `> 0` check, NOT `> block.timestamp`).
- VIOLATION CONDITION: agent's natural expiry has passed but `_revokeAgent` was not called; agent's private key is leaked.
- CONSEQUENCE: leaked agent's signature passes on-chain; if validator co-signs (e.g., due to off-chain validator misclassifying or being compromised), trade executes against `acc`.
- FEASIBILITY: requires (a) agent-key compromise + (b) validator co-signing. Not permissionless.

A2: The off-chain validator at `_OMS().validator` only co-signs OTC trades that both parties **currently and intentionally** agreed to.
- EVIDENCE: `_verifyValidatorSig` accepts whatever the validator signed.
- VIOLATION CONDITION: validator key compromise OR validator software bug (signs trades without verifying maker/taker intent).
- CONSEQUENCE: full RFQ integrity collapse — attacker can execute arbitrary OTC trades against any account whose agent has nonzero `agentExpiry`.
- FEASIBILITY: requires validator compromise. Not permissionless.

A3: Once an `OTCTradeReq` body is marked executed (`_OMS().isTradeExecuted[hash]`), it never re-executes.
- EVIDENCE: `_markTradeExecuted` requires not-yet-executed; sets to true.
- VIOLATION CONDITION: storage corruption (hash collision impossible at 2^256 security).
- CONSEQUENCE: same trade fills twice. Material economic damage.
- FEASIBILITY: not feasible.

A4: `_disableInitializers()` in MarketHubEntry's constructor prevents impl-side reinit.
- EVIDENCE: `MarketHubEntry` constructor.
- VIOLATION CONDITION: bypass via storage manipulation through proxy admin.
- CONSEQUENCE: re-init with malicious roles.
- FEASIBILITY: requires proxy admin.

A5: Domain separator (`name`, `version`, `chainid`, `address(this)`) of the Router proxy uniquely identifies signatures and prevents cross-domain replay.
- EVIDENCE: `EIP712Essential._buildDomainSeparator`.
- VIOLATION CONDITION: another deployment of the Router proxy on the same chain with the SAME contract address (CREATE2 collision) and SAME name/version. Or chain fork.
- CONSEQUENCE: signature replay across deployments / chain forks.
- FEASIBILITY: not feasible (CREATE2 with admin keys; chain forks rare).

A6: `address(this)` inside OTC/AUTH/TRADE module code is the Router PROXY address (not the module's own address).
- EVIDENCE: All module functions are reached via TransparentProxy → Router → delegatecall to module. `address(this)` is preserved as proxy address through delegatecalls.
- VIOLATION CONDITION: someone calls a module directly (not via proxy).
- CONSEQUENCE: domain separator computed against module address ≠ what users signed for. Signatures fail.
- FEASIBILITY: callers always go through proxy (intended). Even if direct calls happen, signature verification would fail safely.

A7: `_AMS()` (AuthModuleStorage) and `_OMS()` (OTCModuleStorage) read from STABLE deterministic ERC-7201 slots regardless of which module's bytecode runs.
- EVIDENCE: `GeneratedStorageSlots.AUTH_MODULE_STORAGE_LOCATION`, `ROUTER_OTC_MODULE_STORAGE_LOCATION` are constants.
- VIOLATION CONDITION: slot collision with another storage namespace, or slot constant changed in upgrade.
- CONSEQUENCE: state silently corrupted.
- FEASIBILITY: requires malicious upgrade. Out of scope.

A8: `_isAllowedRelayer(msg.sender)` correctly gates RFQ entry.
- EVIDENCE: `onlyRelayer` modifier in OTCModule, AuthModule.
- VIOLATION CONDITION: relayer set polluted (e.g., admin error) → attacker becomes relayer.
- CONSEQUENCE: attacker can submit OTC trades. Still needs valid agent + validator sigs to execute, so attacker can spam at most.
- FEASIBILITY: requires admin error.

A9: `EIP-1153 transient storage` (used in RouterAccountBase) correctly isolates the "current authenticated account" per top-level transaction.
- EVIDENCE: `tload`/`tstore` of `ROUTER_ACCOUNT_SLOT` in `setAuth` / `setNonAuth`.
- VIOLATION CONDITION: re-entrancy patterns where the inner call thinks it has different auth context than the outer set. Confirmed: `setAuth` cleans up at end; `setNonAuth` respects prior `setAuth` value.
- CONSEQUENCE: actions taken under wrong auth.
- FEASIBILITY: studied; intended behavior. No code-level bypass found.

A10: `_approveAgentAndSyncAMMAcc` correctly synchronizes agent approval between main account and AMM account.
- EVIDENCE: AuthModule._approveAgentAndSyncAMMAcc — when `acc.isMain()`, also approves for `(root, AMM_ACCOUNT_ID=255)`.
- VIOLATION CONDITION: agent could exercise authority on AMM account that user did not intend.
- CONSEQUENCE: agent acts on AMM account's funds.
- FEASIBILITY: signature for AMM account requires agent to sign a DIFFERENT message hash (with `accountId=255`). Existing main-account signature does not transfer. So no cross-account replay.

A11: Replay-protection key for OTC trades (`hashOTCTradeReq(trade)`) is unique per logical trade.
- EVIDENCE: includes `salt`, `maker`, `taker`, `marketId`, `signedSize`, `rate`.
- VIOLATION CONDITION: same hash for distinct logical trades.
- CONSEQUENCE: legitimate retry blocked, OR duplicate execution allowed.
- FEASIBILITY: cryptographic preimage attack — infeasible.

A12: Validator-co-signed message (`ExecuteOTCTradeMessage`) cannot be re-bundled across DIFFERENT trade bodies.
- EVIDENCE: `ExecuteOTCTradeMessage` contains `(makerMsgHash, takerMsgHash, expiry)`. Both inner hashes pin the trade body.
- VIOLATION CONDITION: collision in `(makerHash, takerHash)` for different trades.
- CONSEQUENCE: validator's signature reused for unrelated trades.
- FEASIBILITY: 2^-256 — infeasible.
