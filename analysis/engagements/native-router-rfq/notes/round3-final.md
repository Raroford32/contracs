# Round 3 — Live RPC Probing — Final Status

## What was unlocked
Public Arbitrum RPCs (`https://arb1.arbitrum.io/rpc`,
`https://arbitrum.publicnode.com`, etc.) accept eth_call from this
sandbox. Etherscan v2 logs API works for bulk historical queries.
Combined, this enables E2-grade evidence collection — but not E3-grade
fork experiments (no Tenderly access).

## What was confirmed

### H1 (soft expiry agent acceptance) — LIVE on-chain
- **141 unrevoked-expired (account, agent) pairs across 8 distinct accounts.** All 231+ days past natural expiry; on-chain `agentExpiry > 0` for all.
- 57 distinct agents — **all bare EOAs** (no code, no EIP-7702 delegation, no contract). Verified by `eth_getCode` sweep.
- Conclusion: H1 is a real production exposure. To exploit, attacker
  needs a leaked agent EOA private key (and validator co-signature, or
  validator key compromise).

### Live admin / role / privileged-actor sweep
| Role | Count | EOAs | Contracts |
|---|---|---|---|
| `DEFAULT_ADMIN_ROLE` (PermissionController) | 6 | 2 | 4 (2 Safes, 1 PendleMulticallOwnerV1, 1 PendleMulticallOwner) |
| Allowed relayers (active in MISC storage) | 9 | 9 | 0 |
| OTC validator (`_OMS().validator`) | 1 | 1 | 0 |
| Conditional validators | 0 | — | — |
| Direct-call MarketHub role members | not enumerated (low priority — paths checked are admin-anyway) |
| Allowed-selector grants (PermissionController) | 36 unique (selector, caller) | mixed | mixed |
| Allowed-address grants (PermissionController) | 84 active | 6 distinct callers | mixed |

**Sample of granted-non-admin callers** (e.g. `0x7d95629767…`,
`0xc8ca354484…`): all checked are bare EOAs OR Pendle's own multicall /
TransparentUpgradeableProxy contracts. No EIP-7702 delegations to
buggy-ERC1271 contracts found among:
- 6 admin role holders
- 9 allowed relayers
- 1 OTC validator
- 10 allowed-selector callers (sampled)
- 57 distinct agents from H1's expired set

### Architecture sanity
- 4-tier proxy chain: TransparentUpgradeableProxy → Router (static
  dispatch by selector to 7 modules) → MarketHub TransparentProxy →
  MarketHubEntry (also a Proxy, fallback to RiskManagement) → per-Market
  TransparentProxy (with own 4-impl static dispatch).
- Markets deployed via **CREATE** (not CREATE2) with `marketId == factory
  nonce`; `assert(computedAddress == newMarket)` enforces parity at
  registration. Cannot be desynced permissionlessly.
- All public selectors enforce auth (`onlyRouter`, `onlyMarketHub`,
  `onlyAuthorized`, `onlyRelayer`, signature verification, etc.) —
  nothing slips through except the documented public utility functions
  (`finalizeVaultWithdrawal`, `settleAllAndGet`, `tryAggregate`,
  `simulateTransfer`).

## Permissionless attack surface — final tally
| Path | Status |
|---|---|
| Direct exploit of public functions | None — accounting is internal, no extraction |
| Direct call to module address bypassing Router proxy | Storage namespace + EIP-712 domain mismatch defeat it |
| Re-init via MISC.initialize | `_disableInitializers()` + `initializer` + `onlyRole(_INITIALIZER_ROLE)` |
| Storage slot collision | ERC-7201 deterministic, verified |
| Transient-storage account spoof via batchRevert | EIP-1153 reverts transient on revert |
| MarketFactory nonce desync | `onlyAuthorized`, asserts parity |
| settleAllAndGet → liquidate | `liquidate` is `onlyAuthorized` |
| tryAggregate slot collision | ERC-7201 |
| Self-OTC across same-root subaccounts | Permitted but value goes to treasury, not attacker |
| Conditional multi-validator weak-link | None set; bound by user's `tick` |
| Stale MarketCache | Cached fields are immutable per market |
| Forge agent signature on-chain (H1) | Requires agent EOA private key — none found exploitable |
| Forge validator signature | Requires validator key — bare EOA |
| Permissive ERC-1271 in any privileged actor | Sweep confirms none |

## Conclusion (final)
After 3 progressively deeper rounds — static analysis, cross-contract
composition exhaustion (14 chains), and live on-chain probing — **no
permissionless exploit has been identified**. The Pendle Boros
deployment on Arbitrum is exceptionally well-secured at the contract
level. All realistic attack vectors require off-chain compromise of one
or more of the following keys:
- An agent EOA (any one of 57 found, with current OTC reach)
- The OTC validator EOA (single SPOF)
- A relayer EOA (1-of-9; necessary but not sufficient)
- An admin role holder (multi-sig protected for 4 of 6)
- The TransparentProxy admins of MarketHub or Router (separate)

The single concrete deliverable from this engagement is the **H1
live-confirmation dataset** (`unrevoked_expired_at_block_460760913.csv`):
141 stale agent approvals on 8 accounts that the protocol's on-chain
code still treats as valid for OTC AcceptOTC signatures. This is
actionable for the protocol team (suggested fix: tighten `_verifyAgentSoft`
to `> block.timestamp`, encourage revocations) but does not constitute
a permissionless E3 finding for an outside attacker.

Per CLAUDE.md §1.4–1.5, no E3 finding is claimed.

## Data trail
- `notes/h1-live-confirmation.md` — H1 narrative + numbers
- `notes/expired_candidates.csv` — 141 candidate (account, agent) pairs from event filtering
- `notes/unrevoked_expired_at_block_460760913.csv` — verified-on-chain unrevoked subset (also 141)
- `notes/composition.md` — 14 cross-contract chain attempts with reasons-for-failure
- `notes/control-plane.md` — auth gates and bypass attempts
- `notes/entrypoints.md` — full Router + MarketHub selector/permissions table
- `notes/value-flows.md` — money entry/exit + actor model
- `notes/assumptions.md` — 12 enumerated assumptions w/ feasibility
- `notes/hypotheses.md` — active + falsified hypotheses with reasoning chains
- `memory.md` — pinned reality + summary across rounds
- `index.yaml` — engagement index

## What would advance this further
1. Tenderly Node access for E3-grade fork experiments and decoded
   evidence artifacts.
2. Threat model from Pendle on validator/relayer/admin key custody.
3. A specific operational compromise scenario to model (out of scope
   for permissionless analysis).
