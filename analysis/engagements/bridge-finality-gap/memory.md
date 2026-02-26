# Memory (bridge-finality-gap)

## Pinned Reality
- chain_id: 1 (Ethereum Mainnet; targets span L1↔L2 boundary)
- fork_block: TBD (will pin once specific target selected for proof)
- attacker_tier: sequencer-level (on centralized-sequencer L2s) OR RPC-eclipse capable
- capital_model: minimal (gas only; no flash loans needed for phantom event creation)

## Attack Vector: Finality Gap + Agentic Hijack
State-synchronization failure between Web3 consensus and Web2 infrastructure.
Off-chain agents read unfinalized L2 state → act on L1 → L2 block reorged → phantom payout persists.
This is NOT a standard smart contract bug. It targets the Web2/Web3 boundary.

## Contract Map Summary (Cached + Fetched)
- Metis L1 Bridge: 0x3980c9ed79d2c191a89e02fa3529c60ed6e9c04b (proxy+impl cached)
  - Uses CrossDomainMessenger trust model; finalizeETH/ERC20Withdrawal gated by onlyFromCrossDomainAccount
- Across SpokePool: 0x5c7BCd6E7De5423a257D81B442095A1a6ced35C5 (proxy→impl 0x5e5b)
  - Ethereum_SpokePool + SpokePool.sol fetched and extracted
  - fillRelay() is PERMISSIONLESS — any relayer can fill
  - Relayer fronts OWN capital (safeTransferFrom(msg.sender))
  - Reimbursement via HubPool merkle roots (relayRootBundle onlyAdmin)
  - slowFill path: SpokePool pays from own balance (executeSlowRelayLeaf)
- EtherDelta: 0x2a0c (cached) — admin-gated withdrawal with ecrecover
- AdEx: (cached) — 2/3 validator supermajority + ECDSA

## Critical Architecture Finding: Across Protocol
**Two distinct fill paths with different risk profiles:**
1. **Fast Fill**: Relayer calls fillRelay() → sends OWN tokens → gets reimbursed later via HubPool
   - Finality risk borne by RELAYER (not protocol pool)
   - Relayer explicitly reads "latest" blocks (confirmed by Across docs)
   - MIN_DEPOSIT_CONFIRMATIONS scales with deposit size (32 blocks for >$1K on ETH)
   - If source deposit reorged: relayer loses funds, no HubPool reimbursement
2. **Slow Fill**: requestSlowFill() → dataworker includes in merkle root → executeSlowRelayLeaf()
   - SpokePool pays from own balance (safeTransfer, not safeTransferFrom)
   - Gated by merkle proof against admin-submitted root bundle
   - Root bundles go through UMA Optimistic Oracle liveness period (~1hr)
   - THIS is the pool-drain vector if root bundles include phantom deposits

## Control Plane & Auth
- fillRelay(): NO auth gate (permissionless, anyone can call)
- relayRootBundle(): onlyAdmin (cross-domain admin from HubPool)
- executeSlowRelayLeaf(): no auth, but requires valid merkle proof against stored root
- requestSlowFill(): no auth (permissionless; emits event for dataworker to pick up)
- Key: admin = cross-domain admin; dataworker proposes bundles; UMA OO disputes

## Coverage Status
- entrypoints: analysis/engagements/bridge-finality-gap/notes/entrypoints.md
- control plane: analysis/engagements/bridge-finality-gap/notes/control-plane.md
- taint map: TBD
- tokens: TBD
- numeric boundaries: TBD
- feasibility: analysis/engagements/bridge-finality-gap/notes/feasibility.md
- message path: analysis/engagements/bridge-finality-gap/notes/message-path.md
- value flows: analysis/engagements/bridge-finality-gap/notes/value-flows.md
- assumptions: analysis/engagements/bridge-finality-gap/notes/assumptions.md
- hypotheses: analysis/engagements/bridge-finality-gap/notes/hypotheses.md

## Value Model Summary
- custody: SpokePool holds tokens for slow fills + relayer refunds
- entitlements: relayers owed refunds; users owed withdrawal amounts
- key measurements: relay hash (binds deposit params to fill), merkle proofs
- key settlements: fillRelay (fast), executeSlowRelayLeaf (slow), executeRelayerRefundLeaf
- solvency: sum(SpokePool_balance) >= sum(pending_slow_fills) + sum(pending_relayer_refunds)

## Economic Model
- money entry: users deposit on source chain SpokePool
- money exit: relayer fills on dest chain (fast) OR SpokePool pays (slow)
- value transform: relay hash computation, merkle proof verification
- fee extraction: relayer spread (fast fill); protocol fee (HubPool level)
- actor dual-roles: dataworker proposes + disputes bundles (conflict if malicious)
- dependency gaps: Across EXPLICITLY acknowledges finality gap risk for relayers
- top implicit assumptions: (1) relayers won't be exploited via phantom deposits, (2) dataworker won't include phantom deposits in root bundles, (3) UMA OO disputers will catch invalid bundles

## Top 3 Hypotheses
1) **Across Slow Fill Phantom Injection** — If a phantom deposit triggers requestSlowFill AND the dataworker includes it in a root bundle (before it's detected as phantom), the SpokePool pays from its own balance. The depositor never actually deposited.
   - broken assumption: dataworker validates deposits against finalized state
   - reasoning chain: 5 steps (phantom deposit → slow fill request → dataworker includes → root relayed → execute leaf → pool drained)
   - estimated extractable value: SpokePool balance per token (millions)
2) **Across Relayer Capital Drain** — Relayer fills phantom deposit with own capital, never gets reimbursed. Relayer loss, not protocol loss. Lower systemic impact.
   - broken assumption: relayer verifies deposit finality before filling
   - reasoning: relayer reads "latest" with MIN_DEPOSIT_CONFIRMATIONS; can be gamed during finality stall
   - estimated extractable value: individual relayer's capital at risk
3) **Metis Bridge Messenger Trust Chain** — If Metis cross-domain messenger relays message from unfinalized L2 state, L1 bridge releases funds
   - broken assumption: messenger only relays finalized messages
   - reasoning: onlyFromCrossDomainAccount check trusts messenger's report of sender
   - estimated extractable value: bridge balance

## Last Experiment
- command: Etherscan source fetch + code analysis of Across SpokePool
- evidence: src_cache/across_SpokePool.sol, across_Ethereum_SpokePool.sol
- result: Confirmed permissionless fillRelay, relayer-funded fast fills, pool-funded slow fills
- belief change: Across fast fill risk is RELAYER-borne, not pool. Slow fill path is the pool-drain vector.

## Next Discriminator
- question: Can a phantom L2 deposit propagate through the slow fill pipeline into a root bundle?
- experiment: Trace the full slow fill lifecycle — requestSlowFill() → dataworker processing → relayRootBundle() — determine if dataworker validates against finalized L2 state
- expected falsifier: If dataworker checks finalized blocks before including slow fills, H1 is infeasible

## Open Unknowns
- What block tag does the Across dataworker use to validate deposits?
- What is the UMA OO liveness period for root bundles? (docs say ~1hr)
- Can requestSlowFill be called for a deposit that only exists in unfinalized state?
- How does the Hop bonder verify source chain deposits before bonding?
- What finality guarantees does the Metis cross-domain messenger provide?
