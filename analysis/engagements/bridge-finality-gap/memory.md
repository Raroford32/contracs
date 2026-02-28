# Memory (bridge-finality-gap)

## Pinned Reality
- chain_id: 1 (Ethereum Mainnet; targets span L1↔L2 boundary)
- fork_block: 24539674 (pinned from live RPC query 2026-02-26)
- attacker_tier: sequencer-level OR RPC-eclipse capable
- capital_model: minimal (gas only ~$50; no flash loans needed)

## Contract Map Summary
**Across Protocol (PRIMARY TARGET):**
- HubPool: 0xc186fA914353c44b2E33eBE05f21846F1048bEda (NOT upgradeable)
  - Owner: 3/5 Gnosis Safe, Liveness: 1800s (30 min), Bond: 0.45 ABT
- SpokePool ETH: 0x5c7BCd6E7De5423a257D81B442095A1a6ced35C5 (UUPS upgradeable)
  - Balances: 75 WETH + $79K USDC + $111K USDT = ~$380K
- ABT: 0xee1dc6bcf1ee967a350e9ac6caaaa236109002ea (WETH9 + proposer whitelist)
  - 1 active proposer EOA: 0xf7bac63f...997c

**Celer cBridge V2:** 0x5427FEFA711Eff984124bfBB1AB6fbf5E3DA1820
- 2/3 stake-weighted signer quorum, separate Governor role
**Synapse FastBridge:** 0x5523D3c98809DdDB82C686E152F5C58B1B0fB59E
- RELAYER_ROLE + GUARD_ROLE gated, well-designed state machine
**Hop L1 ETH Bridge:** 0xb8901acB165ed027E32754E0FFe830802919727f
- Bonder + merkle proof, 1-day challenge period

## Deep Code Analysis Results (Phase C Extended)

### On-Chain Findings (Individual — all sub-E3 alone):
- SpokePool: fill status machine SOUND; reentrancy PROTECTED; relay hash COLLISION-FREE
- M1: speedUp signature replay with unsafeDeposit (acknowledged in NatSpec)
- M2: fee-on-transfer accounting mismatch (off-chain mitigated)
- M3: admin executeExternalCall arbitrary calls (admin trust)
- M4: HubPool _cancelBundle uses transfer() not safeTransfer()
- M5: ABT transfer() bypasses whitelist (but can't propose via this path)
- Celer: signature verification SOUND; M6: epoch boundary 2x volume; M7: fee-on-transfer LP mismatch
- Synapse/Hop: both well-designed for their trust models

### KEY INSIGHT: No critical on-chain vulnerability in isolation.

## Composition Hypotheses (Multi-Vector Chains)

### HC-1: Across Layered Defense Collapse [HIGHEST PRIORITY]
**5 individually-minor vectors compose into kill chain:**
1. requestSlowFill permissionless + no origin validation → entry point
2. Dataworker "latest" block tag + 5-block buffer << 64-slot finality → reads phantom
3. Single automated proposer → no human review of root contents
4. Zero disputes ever → no safety net
5. amountToReturn not in balance check → accounting slack

**Chain:** phantom L2 deposit → requestSlowFill → dataworker reads phantom → automated proposal → no dispute → executeSlowRelayLeaf → drain

**Status:** Sub-E3 — requires L2 reorg or RPC eclipse (infrastructure-level)
**Discriminator needed:** Can we demonstrate phantom propagation through full dataworker pipeline on fork?

### HC-2: Speed-Up Replay + Slow Fill Redirect [MEDIUM]
unsafeDeposit ID collision + speed-up signature → slow fill redirected to wrong recipient
**Discriminator needed:** Does dataworker check speed-up signer == deposit depositor?

### HC-3: Celer Signer Cascade + Volume Bypass [MEDIUM]
2/3 signer compromise → updateSigners → 100% control → governor takeover → disable limits → drain
**Discriminator needed:** Are Celer governor and signer set the same entity?

## Coverage Status
- entrypoints: notes/entrypoints.md
- control plane: notes/control-plane.md
- taint map: notes/taint-map.md
- tokens: notes/tokens.md
- feasibility: notes/feasibility.md
- message path: notes/message-path.md
- value flows: notes/value-flows.md
- assumptions: notes/assumptions.md
- hypotheses: notes/hypotheses.md + notes/composition-hypotheses.md
- on-chain analysis: notes/onchain-contract-analysis.md

## Solvency Equation
Across: sum(SpokePool_balances) + HubPool_liquidReserves >= sum(pending_fills) + sum(pending_refunds)
Violated when: phantom slow fills extract real tokens for non-existent deposits

## Last Experiment
- command: Deep source code analysis of SpokePool, HubPool, BondToken, Celer cBridge, Synapse, Hop
- evidence: notes/onchain-contract-analysis.md, notes/composition-hypotheses.md
- result: No critical on-chain vulnerability in isolation; 5 composition chains identified
- belief change: The vulnerability is NOT in any single contract — it's in the COMPOSITION of 5 defense layers each being "good enough" individually but failing together

## Next Discriminator
- Question: Can the full Across kill chain (HC-1) be demonstrated on a fork with actual dataworker code?
- Alternative: Check if Celer governor == signer set overlap (HC-3 cheapest test)
- Expected falsifier: If dataworker uses "finalized" for origin lookups, HC-1 is blocked
