# Hypotheses: Finality Gap + Agentic Hijack

## Active Hypothesis Set

### H1: Fast Bridge Relayer Phantom Payout (Category A)
- **Broken assumption:** L1 contract assumes relayer only signs for finalized L2 events
- **Reality:** Relayer reads "latest" block tag for speed; L2 block can be reorged
- **Sequence:**
  1. Setup: Attacker identifies fast bridge with single-relayer ECDSA trust
  2. Distort: Submit large L2 withdrawal in a block that will be orphaned
  3. Realize: Relayer signs L1 payout based on unfinalized L2 event
  4. Unwind: L2 block reorged; L2 tx vanishes; L1 funds already released
- **Feasibility constraints:**
  - Attacker tier: builder/sequencer level OR RPC eclipse capability
  - Capital: only needs gas for L2 tx + L1 claim (no flash loan needed)
  - Timing: must occur within finality gap window
- **Discriminator:** Identify L1 contracts with relayer-signed withdrawal; time the payout latency vs finality

### H2: Shared RPC Eclipse on Multi-Signer Bridge (Category B)
- **Broken assumption:** M-of-N signers provide Byzantine tolerance
- **Reality:** If all N signers use the same RPC provider, eclipsing the provider eclipses all
- **Sequence:**
  1. Setup: Identify multi-sig bridge where all validators share RPC infra
  2. Distort: Eclipse/manipulate shared RPC to serve ghost block
  3. Realize: All M signers see same phantom event, produce valid multi-sig
  4. Unwind: Ghost block rejected by canonical chain; L1 release persists
- **Feasibility constraints:**
  - Requires knowledge of validator infra (may be opaque)
  - RPC eclipse is non-trivial but documented (provider-specific)
- **Discriminator:** Check if bridge documentation/code reveals shared RPC dependency

### H3: Intent/Solver Protocol Semantic Hallucination
- **Broken assumption:** Solver/filler observes a valid user intent on L2 and fills on L1
- **Reality:** If solver reads unfinalized state, user intent may be phantom
- **Sequence:**
  1. Setup: Create phantom intent on L2 (large cross-chain swap order)
  2. Distort: Solver's agent reads intent from unfinalized block
  3. Realize: Solver fills order on L1, sending tokens to attacker's L1 address
  4. Unwind: L2 intent reorged away; solver has sent real tokens for nothing
- **Feasibility constraints:**
  - Solver bears the loss (not protocol pool) in some architectures
  - Attacker must control both L2 intent creation and L2 reorg
- **Target protocols:** Across (relayer fills), Connext/Everclear (solver fills)
- **Discriminator:** Study solver fill-then-verify architecture; check finality handling

### H4: OTC Desk Database Poisoning
- **Broken assumption:** OTC matching engine's MySQL/Redis reflects canonical chain state
- **Reality:** If OTC agent writes to DB on "latest" events, DB can contain phantom orders
- **Sequence:**
  1. Setup: Identify OTC protocol with off-chain matching + on-chain settlement
  2. Distort: Create large phantom deposit on L2; agent writes to DB
  3. Realize: L1 settlement executes based on poisoned DB record
  4. Unwind: L2 deposit reorged; DB record is the only trace
- **Feasibility constraints:**
  - Requires OTC protocol with on-chain/off-chain hybrid architecture
  - DB poisoning is persistent (survives L2 reorg)
- **Discriminator:** Identify protocols with off-chain matching engines

## Backlog (Lower Priority)

### H5: Keeper/Liquidation Bot Finality Confusion
- Keeper bots reading unfinalized state may trigger premature liquidations
- Lower impact: liquidation is usually reversible or economically bounded

### H6: Oracle Relayer Finality Gap
- Oracle relayers (Chainlink CCIP, LayerZero DVNs) reading unfinalized state
- Lower feasibility: typically use finalized blocks + multi-layer verification

### H7: Sequencer-Induced Phantom (Appchain Specific)
- On sovereign appchains, the sequencer is often a single entity
- If compromised/malicious, can produce blocks that never finalize
- Lower relevance for Ethereum mainnet bridges to major L2s

## Hypothesis Ranking (by path-to-delta)

| Rank | Hypothesis | Expected Path | Feasibility | Impact |
|------|-----------|---------------|-------------|--------|
| 1 | H1: Single relayer fast bridge | Short - identifiable on L1 | Medium | High (pool drain) |
| 2 | H3: Intent/solver hallucination | Medium - need solver arch | Medium | High (solver loss) |
| 3 | H4: OTC database poisoning | Long - need off-chain arch | Low-Medium | Very High |
| 4 | H2: Shared RPC multi-sig | Long - need infra knowledge | Low | Very High |
