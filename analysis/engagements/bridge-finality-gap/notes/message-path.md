# Bridge Message Path Analysis: Finality Gap + Agentic Hijack

## Attack Vector Model

### Architecture of Vulnerable Systems

```
L2 Chain                  Off-Chain Agent (Web2)              L1 Chain
─────────                 ──────────────────────              ────────

User initiates            Agent polls L2 RPC
withdrawal/OTC order  ->  (reads "latest" block)
                              |
Event emitted             Agent parses event
(e.g. OrderFilled,        writes to Redis/MySQL
 DepositLocked)               |
                          Worker reads queue
                          signs ECDSA payload
                              |
                          Submits L1 tx          ->    L1 contract verifies
                                                       ECDSA sig from trusted
                                                       signer, releases funds
                              |
         <--- Ghost Block reorged away --->
         L2 tx vanishes from canonical chain
         L1 payout already executed
```

### Key Components

1. **L1 Settlement Contract**
   - Accepts ECDSA signatures from trusted relayer/signer
   - Releases funds (ETH/ERC20) to recipient
   - Typically uses `onlyRelayer` modifier OR `ecrecover`/`ECDSA.recover` verification
   - MAY use nonce tracking (but nonce is per-message, not per-finality)

2. **Off-Chain Agent (The Target)**
   - Listens to L2 RPC for events
   - Critical question: which block tag? `latest` vs `safe` vs `finalized`
   - Writes state to fast data store (Redis) and persistent DB (MySQL/Postgres)
   - Separate worker signs and submits L1 tx

3. **The Finality Gap**
   - Window between L2 block broadcast and L2 finality
   - Optimistic rollups: 7-day challenge period
   - ZK rollups: proof generation time (minutes to hours)
   - High-throughput L2s/appchains: even shorter finality = higher reorg risk

### Acceptance Predicates (What L1 contract checks)

For each target bridge, map:
- [ ] Signature validity (ECDSA recover == trusted signer)
- [ ] Nonce/message uniqueness
- [ ] Amount bounds / rate limits
- [ ] Timeout/expiry
- [ ] Chain ID binding
- [ ] Message hash binding (does it bind to L2 tx hash? block hash? state root?)

### Replay Protection Model

- [ ] Is the nonce derived from L2 tx data or independently generated?
- [ ] If L2 tx is reorged, can the same nonce be reused with different data?
- [ ] Does the L1 contract check L2 finality proofs, or trust the relayer?
- [ ] Is there a challenge/dispute mechanism?

## Target Protocol Classification

### Category A: Pure Relayer Trust (Highest Risk)
L1 contract trusts a single ECDSA signer. No on-chain finality verification.
- Typical in: fast bridges, OTC desks, intent-based protocols
- The off-chain agent IS the security model
- Attack: poison the agent's view of L2 -> phantom payout on L1

### Category B: Threshold/Multi-sig Relayer
L1 requires M-of-N signatures. Agent corruption requires compromising M signers.
- Lower risk but still vulnerable if all signers read same RPC
- Attack: eclipse the shared RPC endpoint -> all signers sign the phantom

### Category C: On-chain Finality Proof
L1 verifies a state/storage proof against a finalized L2 state root.
- Canonical bridges (Optimism, Arbitrum) wait for finality
- NOT vulnerable to this attack (by design, at cost of latency)

### Category D: Hybrid (Fast Path + Slow Verification)
Fast path uses relayer (Category A/B). Slow path verifies on-chain.
- If fast path has independent liquidity pool: relayer's funds at risk
- If fast path draws from shared pool: all depositors at risk
- Key question: who bears the loss if relayer is wrong?

## Discrimination Methodology

### Step 1: Identify Trusted Relayer on L1
```
Search L1 contracts for:
- ecrecover / ECDSA.recover in withdrawal/settle/release functions
- onlyRelayer / onlyMessenger / onlyOracle modifiers
- Single address stored as `relayer` / `signer` / `messenger` / `keeper`
- External function that: (a) verifies signature, (b) transfers tokens/ETH
```

### Step 2: Determine Agent Finality Threshold
```
Timing test:
- Submit small legitimate L2 tx
- Measure time to L1 payout execution
- Compare against L2 finality time
- If payout_time << finality_time -> reading unfinalized state
```

### Step 3: Map RPC Dependency
```
- Can the agent's RPC endpoint be identified? (public infra, specific provider)
- Is the agent using a single RPC or multiple with consensus?
- Does the agent verify block finality tags?
```

### Step 4: Assess Reorg/Eclipse Feasibility
```
For the target L2:
- What is the cost to produce an orphaned block?
- Can RPC eclipse be achieved (CDN/provider-specific)?
- What is the maximum reorg depth observed historically?
- On appchains: what is sequencer trust model?
```

## Evidence Requirements for E3

To promote a finding to E3, ALL must hold:
1. L1 contract verified to accept relayer-only ECDSA signatures
2. Off-chain agent confirmed reading unfinalized blocks (timing evidence)
3. L2 reorg or RPC eclipse demonstrated feasible (cost bounded)
4. Funds release on L1 confirmed for phantom L2 tx
5. Net profit positive after gas + setup costs
6. Robustness under perturbations
