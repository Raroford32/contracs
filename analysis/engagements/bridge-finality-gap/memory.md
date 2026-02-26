# Memory (bridge-finality-gap)

## Pinned Reality
- chain_id: 1 (Ethereum Mainnet; targets span L1↔L2 boundary)
- fork_block: 24539674 (pinned from live RPC query 2026-02-26)
- attacker_tier: sequencer-level OR RPC-eclipse capable
- capital_model: minimal (gas only ~$50; no flash loans needed)

## Attack Vector: Finality Gap + Agentic Hijack
Off-chain agents read unfinalized L2 state → act on L1 → L2 block reorged → phantom payout.
Targets the Web2/Web3 boundary — NOT a standard smart contract bug.

## Contract Map Summary
**Across Protocol (PRIMARY TARGET):**
- HubPool: 0xc186fA914353c44b2E33eBE05f21846F1048bEda
  - Owner: 3/5 Gnosis Safe (0xb524735...dff03715)
  - Liveness: 1800s (30 min), Bond: 0.45 ABT
- SpokePool ETH: 0x5c7BCd6E7De5423a257D81B442095A1a6ced35C5
  - Balances: 75 WETH + $79K USDC + $111K USDT = ~$380K
- ABT: 0xee1dc6bcf1ee967a350e9ac6caaaa236109002ea
  - **Proposer whitelist** — only 1 active: 0xf7bac63f...997c (EOA)
  - Mintable permissionlessly (deposit ETH → ABT, WETH9 pattern)

## CONFIRMED FINDINGS (All on-chain evidence)

### F1: requestSlowFill() ACCEPTS FABRICATED DEPOSITS
- eth_call simulation at block 24,539,741: SUCCESS (no revert)
- Zero origin-chain validation — only checks deadline, exclusivity, fillStatus
- Selector: 0x2e63e59a, Gas: ~69K

### F2: Dataworker uses "latest" NOT "finalized"
- GitHub: BaseAbstractClient.ts → provider.getBlockNumber()
- BUNDLE_END_BLOCK_BUFFERS: ETH=5 blocks (60s) << 64-slot finality (12.8 min)

### F3: ABT Whitelist BLOCKS Self-Proposal
- BondToken.transferFrom() checks proposers mapping
- ONLY 1 whitelisted proposer: 0xf7bac63f...997c (EOA, 14.7 ABT, 8.2 ETH)
- 33 proposals in 5K blocks, 100% from this single EOA

### F4: ZERO Disputes EVER
- RootBundleDisputed events: 0 in last 50K blocks
- No evidence of ANY dispute in contract history
- 30-min window with no active independent monitors confirmed

### F5: UMA OO Does NOT Auto-Validate
- Purely optimistic — assumes correct unless challenged
- Dispute reward: 0.225 ABT (~$562) vs risk: 0.45 ABT (~$1,125) = 2:1 against
- Manual `yarn dispute` tool, not automated daemon

### F6: Slow Fill Payout Path (SpokePool.sol:1666)
- executeSlowRelayLeaf → _fillRelayV3 → safeTransfer(recipient, amount)
- Pays from SpokePool balance directly to recipient

## Hypothesis Status (FINAL)

### H1: Across Slow Fill Phantom Injection [DESIGN RISK — NOT E3]
**On-chain**: VULNERABLE (requestSlowFill accepts anything)
**Off-chain defenses**:
1. ABT whitelist → STRONG (blocks self-proposal)
2. Dataworker validation → MODERATE (uses "latest" not "finalized")
3. UMA dispute → WEAK (dormant, no active monitors)
**Cannot reach E3**: Requires infrastructure compromise (RPC eclipse or key theft)

### H2: Synapse FastBridge Phantom Prove [FALSIFIED]
On-chain state reverts with reorged blocks. Pool drain not feasible.

### H3: Across Fast Fill Relayer Risk [KNOWN / NOT NOVEL]
Documented trade-off. Relayer bears risk, not protocol.

## Novel Architectural Finding (Sub-E3)

**Complete delegation of finality validation to off-chain infrastructure:**
1. No on-chain finality check in ANY SpokePool function
2. No origin-chain state verification in requestSlowFill
3. ALL security depends on: (a) single EOA proposer whitelist, (b) dataworker correctness, (c) dormant dispute mechanism
4. If proposer EOA key compromised: ~$380K+ extractable with no on-chain defense
5. Dataworker's 5-block ETH buffer << 64-slot finality gap

**This is invisible to standard smart contract audits.**

## Last Experiment
- command: eth_call simulation of requestSlowFill + ABT analysis + proposer identification
- evidence: notes/feasibility.md, notes/control-plane.md, notes/attack-model.md
- result: All defenses mapped; H1 partially falsified; design risk identified
- belief change: ABT whitelist is primary defense; dispute mechanism is dormant

## Self-Evaluation
- What belief changed: ABT whitelist kills self-proposal (strongest defense)
- Single EOA proposer is a single point of failure
- Zero disputes ever = untested safety net
- Cannot reach E3 without infrastructure compromise

## Next Steps
- Record as sub-E3 design risk finding
- Commit and push all evidence
