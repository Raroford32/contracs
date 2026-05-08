# Memory (native-router-rfq → Pendle Boros, Arbitrum)

## Pinned Reality
- chain_id: 42161 (Arbitrum One)
- fork_block: NOT pinned (sandbox RPCs blocked; Etherscan v2 only)
- attacker_tier: public mempool (default; escalate with evidence)
- target (declared): Native Router @ 0x1080808080f145b14228443212e62447c112adad
- target (actual): **Pendle Boros MarketHub proxy**, Arbitrum.
  Native Protocol guess was wrong; this address on Arbitrum is Pendle's signed-order yield-perp system.

## Contract Universe (verified)
| Address | Role | Verification |
|---|---|---|
| `0x1080808080f145b14228443212e62447c112adad` | MarketHub TransparentUpgradeableProxy | verified |
| `0x63b53e49fca8cb315b0a4a2f598ca6943318635c` | MarketHubEntry impl (also a Proxy: fallback → RiskManagement) | verified |
| `0xe5d9735fe4fe391b4e1a0b42286da82e0650509b` | MarketHubRiskManagement (fallback impl for unknown selectors) | verified |
| `0x8080808080dab95efed788a9214e400ba552def6` | Router TransparentUpgradeableProxy | verified |
| `0x2348b91caeb1cb07dd0e8f0cc4216e921fa527e0` | Router impl (static-dispatch facet hub) | verified |
| `0x8c8436f76618be610a2e9b630b7687f13714e2d3` | AMM_MODULE | not yet bundled |
| `0xdb727ff30938790ebff0d7d3e2f28229d9273422` | AUTH_MODULE | verified |
| `0xcfc280444fcfa34ddbe7d2b58094823285422318` | CONDITIONAL_MODULE | not yet bundled |
| `0xbb64fe9396a1b62d1b7e7b74bfeb2a825f8b16fb` | DEPOSIT_MODULE | not yet bundled |
| `0xbad140a7a9ec22a016109fe8ee6fab343c30900a` | MISC_MODULE | not yet bundled |
| `0xc6f465f4173897ba7c6dd2ac0df9ef9b88b46d53` | **OTC_MODULE** (RFQ heart) | verified |
| `0x21bfd0f5502d8843d099f89d7424aceefaf6ad3f` | TRADE_MODULE | verified |
| `0x2080808080262c1706598c9dbdd3a0cd3601e5ea` | PermissionController proxy → 0xe6c43d22… | resolved |
| `0x3080808080ee6a795c1a6ff388195aa5f11ecee0` | MarketFactory proxy → 0x6bfc1a9c… | resolved |
| `0xbe6d2273477470fa96b11dcac47507c6be8ab652` | Treasury (Gnosis Safe) | resolved |
| `0xc381b67f0289d9c1015924a0c50bb32da5265d59` | TransparentProxy admin (hardcoded in proxy bytecode) | priv. role |

## Architecture Summary
```
User → Router (TransparentProxy) → Router impl (static-dispatch) → ModuleX (delegatecall)
                                  ↘ Module storage at deterministic ERC-7201 slots
ModuleX → MarketHub (TransparentProxy) → MarketHubEntry → fallback → RiskManagement
        (gates on msg.sender == ROUTER || PERM_CONTROLLER.canDirectCallMarketHub)
MarketHub → IMarket(CREATE2-derived) for per-market accounting
```
- **Storage**: ERC-7201 namespaced; `RouterAccountBase` uses **EIP-1153 transient storage** (`tload`/`tstore`) for the "currently authenticated account" context — preserved across delegatecalls within a tx.
- **OTC (RFQ) flow**: `executeOTCTrade(req)` requires (1) maker's agent signature, (2) taker's agent signature, (3) off-chain **validator's** EIP-712 co-signature over both side hashes. Replay key = `keccak256(OTCTradeReq typehash + body)`.

## Control Plane & Auth (RFQ-relevant)
| Gate | Where | Source of authority | Bypass attempts attempted |
|---|---|---|---|
| `onlyRelayer` | OTCModule, AuthModule | `_AMS().allowedRelayer[msg.sender]` (admin-managed) | None executed (no RPC). Relayer set via `setAllowedRelayer(addr,bool)` from MISC_MODULE. |
| Maker agent sig | `_verifyAgentSig` → `_verifyAgentSoft` | `agentExpiry[Account(maker, accountId)][agent] > 0` (NOT > block.timestamp) | Discussed below. |
| Taker agent sig | same | same | same |
| Validator sig | `_verifyValidatorSig` | `_OMS().validator` (single address; admin-set via `setOTCTradeValidator`) | Single point of failure. |
| Replay | `_markTradeExecuted` | `_OMS().isTradeExecuted[hash(OTCTradeReq)]` | Checked AFTER all execution; partial-revert ⇒ retryable (intended). |
| Direct MarketHub | `_checkOnlyRouter` | `msg.sender == ROUTER \|\| PERM_CONTROLLER.canDirectCallMarketHub(...)` | Sealed for permissionless callers. |
| Proxy admin | TransparentProxy hardcoded admin | `0xc381b67f...` (MarketHub) and similar for Router | Centralization risk; out of scope for permissionless attacker. |

## Value Model Summary
- Custody: ERC20 deposits sit in MarketHub (`vaultDeposit`); cash credited to MarketAcc records `acc[user].cash`.
- Entitlements: PnL accounting per-market via `IMarket.orderAndOtc` (from order book + OTC + funding).
- Solvency equation (per-token): `Σ acc[*].cash + Σ market_solvency >= treasury - bad_debt`. Strict accounting depends on per-market PnL settling at maturity.
- Measurement inputs: implied rates (per-market `MarketImpliedRate`), tick math, FIndex (floating index) for funding-like streams.

## Top 3 Hypotheses
See `notes/hypotheses.md` for full chains. Summary:

1. **H1 (Design risk, not exploit): soft agent expiry in OTC.** `_verifyAgentSoft` requires `agentExpiry > 0`, not `> block.timestamp`. A naturally-expired (but not explicitly revoked) agent's key, if leaked, can sign valid OTC AcceptOTCFullMessages; on-chain code accepts them as long as the validator co-signs. Documented as intentional ("loose check") — defence relies entirely on the off-chain validator.
   - Broken assumption: "expired agent ⇒ can no longer sign" (false on-chain; only revocation zeroes it).
   - Reasoning chain: 6 steps.
   - Discriminator: `agentExpiry(account, agent)` view call for any account whose agent's expiry < now and revocation not called → still > 0.
   - Severity: Low at code level; depends on validator integrity.

2. **H2 (Centralization): single OTC validator address controls all RFQ liveness/correctness.** `setOTCTradeValidator(address) onlyAuthorized` → if the role-holder or validator key is compromised, any OTC trade can be forged. **Not permissionlessly exploitable** without admin compromise.
   - Severity: Medium-High (operational).

3. **H3 (Free option): relayer execution timing.** Validator/relayer holds free option between maker's signing and on-chain execution within `expiry` window — known RFQ tradeoff.
   - Severity: Inherent.

## Last Experiment (round 3 — RPC unblocked via public arb1.arbitrum.io/rpc)
- Pinned: block ~460,760,913 (May 8 2026, Arbitrum One).
- Pulled 10,000 AgentApproved events from Router via Etherscan v2; filtered
  to expired (expiry < now) main-account approvals → 141 candidates;
  queried `agentExpiry(bytes21,address)` (sig 0xc9c437b3) on each.
- **Result: 141/141 are UNREVOKED** (storage value > 0) AND **231+ days
  past expiry**. Across 8 distinct accounts:
  - 0x904636b8…: 82 (largest exposure)
  - 0x0d198bc0…: 26 (EIP-7702 → MetaMask DeleGator)
  - 0x75e23ef6…: 19
  - 0x4626b191…: 5
  - 0x1eca053a…: 4 (EIP-7702 delegated)
  - 0x7d83e163…: 3
  - 0x5ebf929d…: 1
  - 0xc0faf4cb…: 1
- Validator: `0x862f53763a4cbb1bc74d605716342b53c6a84cc6` (EOA, no code).
- See `notes/h1-live-confirmation.md` and the CSV evidence for raw data.

## Next Cheapest Discriminator
- The on-chain side of H1 is fully verified — no further static call adds
  belief. To proceed to E3 needs either:
  1. A leaked or compromised agent private key (out of scope), or
  2. Validator key compromise (out of scope), or
  3. A bug in OZ ECDSA that doesn't exist (low priority to revisit), or
  4. Discovery that any of the 141 agents has EIP-7702 delegation to a
     buggy `isValidSignature` contract (5 sampled → bare EOAs; full sweep
     would take ~141 RPC calls but is viable if user wants).

## Open Unknowns
- Whether any of the 141 agents has EIP-7702 → permissive ERC-1271 (full
  sweep not yet done; sample of 5 are clean EOAs).
- Whether validator's key custody has any operational weakness (out of
  scope without protocol-internal information).

## Outcome (updated)
**Still no E3 finding** under permissionless threat model. **But H1 is
now LIVE-CONFIRMED with 141 concrete on-chain (account, agent, expiry)
tuples** — elevating it from "design smell" to "live operational
exposure". A protocol-side fix is recommended (`> block.timestamp` instead
of `> 0` in `_verifyAgentSoft`, plus encouraging revocations); a key-leak
incident would be immediately exploitable for the affected accounts.
