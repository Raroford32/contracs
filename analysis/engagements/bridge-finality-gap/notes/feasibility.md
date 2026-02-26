# Feasibility Assessment: Finality Gap Attack

## Per-Hypothesis Feasibility Ledger

### H1: Single Relayer Fast Bridge Phantom Payout

**Attacker Tier:** Sequencer-level (on centralized-sequencer L2s) OR builder-level (for reorg) OR network-level (for RPC eclipse)

**Ordering Requirement:**
- Must be able to produce or influence a block that will be orphaned
- On Optimistic Rollups: sequencer produces blocks; state root posted to L1 with delay
- On ZK Rollups: sequencer produces blocks; ZK proof generated later
- Key: the "fast path" agent acts BEFORE the proof/challenge period

**Finality Windows by L2 (as of 2026):**
| L2 | Sequencer Type | Block Time | Safe Finality | Full Finality | Fast Bridge Window |
|----|---------------|------------|---------------|---------------|-------------------|
| Optimism | Centralized | 2s | ~2min | 7 days | Hours (pre-proof) |
| Arbitrum One | Centralized | 250ms | ~10min | 7 days | Hours (pre-proof) |
| Base | Centralized | 2s | ~2min | 7 days | Hours (pre-proof) |
| zkSync Era | Centralized | 1s | Minutes | ~1hr (proof) | Minutes |
| Scroll | Centralized | 3s | Minutes | ~4hrs (proof) | Minutes-Hours |
| Polygon zkEVM | Centralized | 2s | Minutes | ~30min (proof) | Minutes |
| Starknet | Centralized | 6s | Minutes | Hours (proof) | Minutes-Hours |

**Reorg Feasibility by L2:**
- Centralized sequencer L2s: Sequencer CANNOT be reorged by external parties (sequencer is single entity)
- BUT: Sequencer itself can create conflicting blocks / soft-confirm then not include
- L2 reorgs primarily happen via: sequencer bugs, forced inclusion from L1, network partitions

**RPC Eclipse Feasibility:**
- If agent uses public RPC (e.g., Infura, Alchemy for L2): CDN-level manipulation is extremely hard
- If agent uses dedicated node: node-level attacks more feasible
- If agent uses sequencer's own endpoint: sequencer IS the source of truth pre-finality

**Capital Requirements:**
- Gas for phantom L2 tx: <$1 on most L2s
- Gas for L1 claim (if attacker submits): ~$5-50
- No flash loan needed (attacker doesn't need capital, just a phantom event)
- Total cost: ~$50 worst case

**Expected Value:**
- Bridge pool TVL typically $10M-$1B
- Single withdrawal may be capped (rate limits, per-tx limits)
- Net profit = min(bridge_balance, withdrawal_cap) - gas_costs

**Falsifier Experiment:**
- [ ] Identify specific fast bridge L1 contract
- [ ] Query relayer address and check if single signer
- [ ] Measure time from L2 event to L1 payout
- [ ] Compare against L2 finality time
- [ ] If payout_time < finality_time: assumption A1 violated

### H3: Intent/Solver Semantic Hallucination

**Attacker Tier:** Sequencer-level (to create phantom intent) + solver observation

**Key Protocols:**
- Across Protocol: Relayer-based; relayer fills then claims
- UniswapX: Solver-based; solver fills user orders
- Connext/Everclear: Router-based; routers provide liquidity

**Architecture-Specific Feasibility:**
| Protocol | Who Bears Loss? | Finality Check? | Rate Limits? |
|----------|----------------|-----------------|-------------|
| Across | Relayer (then reimbursed from pool) | Unknown - key question | Per-relayer limits |
| UniswapX | Solver directly | Dutch auction timing | Order expiry |
| Connext | Router (then pool) | Fast path has liquidity proof | Router capital limits |

**Falsifier Experiment:**
- [ ] Read Across SpokePool contract for finality handling
- [ ] Check if fill() function requires any finality proof
- [ ] Measure fill latency vs L2 finality

### On-Chain Discriminator Design

**Cheapest Test (Tenderly Simulation):**
1. Take a known fast bridge L1 contract
2. Craft a valid-looking relayer signature for a phantom withdrawal
3. Simulate the L1 release transaction
4. Observe: does the contract check anything beyond signature validity?
5. If NO additional finality proof check → vulnerable to phantom payout

**Timing Test (Behavioral):**
1. Execute small real L2→L1 withdrawal through target bridge
2. Measure wall-clock time from L2 tx confirmation to L1 fund release
3. Compare against L2 finality guarantee
4. If release_time < finality_time → agent reads unfinalized state
