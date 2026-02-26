# Feasibility Analysis: Bridge Finality Gap Attack

## Updated With Live On-Chain Evidence (Block 24,539,741)

### Confirmed Facts (On-Chain + Source Code Evidence)

| # | Fact | Evidence |
|---|------|----------|
| F1 | requestSlowFill() accepts fabricated deposits | eth_call simulation SUCCESS at block 24,539,741 |
| F2 | Zero origin-chain validation in requestSlowFill | SpokePool.sol:1076-1105 — only checks deadline, exclusivity, fill status |
| F3 | HubPool liveness = 1800s (30 min) | on-chain storage read: liveness() = 1800 |
| F4 | ABT proposer whitelist blocks unauthorized proposals | BondToken.sol:73-82 — transferFrom checks proposers mapping |
| F5 | Dataworker uses "latest" not "finalized" | GitHub: BaseAbstractClient.ts — provider.getBlockNumber() |
| F6 | BUNDLE_END_BLOCK_BUFFERS: ETH=5, Arb=240, OP=60 | GitHub: Constants.ts |
| F7 | Zero disputes in sampled 50K-block window | on-chain event query |
| F8 | SpokePool ETH balance ~$380K | on-chain balance query |
| F9 | ABT total supply = 39.96, HubPool holds 0.45 | on-chain queries |
| F10 | proposeRootBundle is permissionless (code) but ABT whitelist limits it (token) | HubPool.sol:566 + BondToken.sol:73-82 |

### Attack Variant Feasibility Matrix

#### Variant A: RPC Eclipse on Dataworker [MEDIUM-LOW Feasibility]
**Concept**: Feed phantom L2 blocks to the dataworker's RPC provider

**Requirements**:
- Must identify which RPC endpoint the Across dataworker uses
- Must intercept/spoof responses on that endpoint
- Phantom deposit must be within BUNDLE_END_BLOCK_BUFFERS range

**Assessment**:
- Dataworker infrastructure is private (Risk Labs operated)
- Multiple validators likely verify independently
- If dataworker uses multiple providers, eclipse requires multi-target compromise
- **VERDICT**: Infrastructure attack, NOT a protocol-level vulnerability

#### Variant B: Attacker Self-Proposes Malicious Root [BLOCKED]
**Why**: ABT BondToken.transferFrom() (line 78-80) blocks non-whitelisted proposers
- `proposers` mapping controls who can transfer ABT to HubPool
- Only `onlyOwner` can call `setProposer()`
- **VERDICT: INFEASIBLE** — cannot obtain proposer role permissionlessly

#### Variant C: L2 Sequencer Manipulation [LOW Feasibility]
**Why**: Requires compromising centralized L2 sequencer infrastructure
- **VERDICT**: Infrastructure attack, not protocol vulnerability

#### Variant D: Organic L2 Reorg + Dataworker Race [THEORETICAL]
**Scenario**: Natural L2 reorg causes deposit to appear then disappear while cached
- Requires reorg deeper than BUNDLE_END_BLOCK_BUFFERS (5-240 blocks)
- Never observed on any major L2 post-merge
- **VERDICT**: Theoretically possible, practically impossible

### Defense Layer Analysis

| Layer | Defense | Strength | Bypass Feasibility |
|-------|---------|----------|-------------------|
| 1 | requestSlowFill validation | **NONE** | N/A — intentionally permissionless |
| 2 | Dataworker deposit verification | **MODERATE** | Uses "latest" block tag |
| 3 | BUNDLE_END_BLOCK_BUFFERS | **MODERATE** | 5 blocks (ETH) << 64 slots finality |
| 4 | ABT proposer whitelist | **STRONG** | Requires owner compromise |
| 5 | UMA OO dispute (30 min) | **MODERATE** | Relies on active disputors |
| 6 | Independent validator infrastructure | **STRONG** | Single-entity risk |

### Economic Analysis

| Parameter | Value |
|-----------|-------|
| Attack cost (gas) | ~$50 |
| Extractable value (ETH SpokePool) | ~$380K |
| Required attacker tier | RPC eclipse OR sequencer compromise |
| ABT bond needed? | BLOCKED for self-proposal |
| Dispute window | 30 minutes |
| Capital needed | Zero (beyond gas) |

### H1 Final Status: PARTIALLY FALSIFIED

**On-chain component**: Confirmed vulnerable — requestSlowFill accepts anything.

**Off-chain component**: Defended by multiple layers:
1. ABT whitelist blocks self-proposal (strongest defense)
2. Dataworker validates deposits (moderate defense)
3. Dispute window provides safety net (moderate defense)

**Remaining attack surface**: Dataworker uses "latest" not "finalized", with insufficient BUNDLE_END_BLOCK_BUFFERS. This is a **design trade-off for speed**, not a bug.

**E3 qualification**: Cannot reach E3 without demonstrating actual phantom propagation through dataworker pipeline, which requires infrastructure-level compromise (RPC eclipse or similar).

### Novel Architectural Finding

The Across Protocol's security model has a **complete delegation of finality validation to off-chain infrastructure**:
- No on-chain finality check in any SpokePool function
- No origin-chain state verification in requestSlowFill
- No cross-chain proof requirement for slow fill requests
- ALL security depends on: (1) ABT whitelist, (2) dataworker correctness, (3) dispute monitoring

This is invisible to standard smart contract audits and represents a systemic architectural risk: **if the off-chain trust boundary fails, the on-chain contracts provide zero protection against phantom deposits**.

### Synapse FastBridge: H2 FALSIFIED
- On-chain state reverts with reorged blocks
- bridgeStatuses cannot persist phantom entries
- Risk limited to relayer capital only (self-funded fills)
- **VERDICT**: Protocol-level pool drain not feasible

### Across Fast Fill: H3 KNOWN RISK
- Relayer reads "latest" with MIN_DEPOSIT_CONFIRMATIONS
- Documented trade-off in Across docs
- Risk borne by relayer, not protocol
- **VERDICT**: Known and accepted, not novel
