# Assumptions: Finality Gap Attack Surface

## Assumption Enumeration (per Section 3.6.2)

### A1: L1 Contract Trusts Relayer Signature Means Finalized Event
```
ASSUMPTION: If the relayer signs a withdrawal message, the corresponding L2 event is finalized
EVIDENCE IN CODE: L1 bridge contracts verify ECDSA sig == trusted_signer, then release funds
VIOLATION CONDITION: Relayer signs based on unfinalized L2 state; L2 block is reorged
CONSEQUENCE: Phantom fund release on L1; L2 deposit never existed canonically
VIOLATION FEASIBILITY: HIGH - most fast bridges optimize for speed over finality
```

### A2: Cross-Domain Messenger Relays Only Finalized Messages
```
ASSUMPTION: CrossDomainMessenger.xDomainMessageSender() returns sender from finalized L2 tx
EVIDENCE IN CODE: onlyFromCrossDomainAccount modifier trusts messenger's report
VIOLATION CONDITION: Messenger relays message from unfinalized block
CONSEQUENCE: L1 bridge executes withdrawal for non-existent L2 action
VIOLATION FEASIBILITY: MEDIUM - canonical bridges usually wait for finality, but custom bridges may not
```

### A3: L2 Events Are Immutable Once Emitted
```
ASSUMPTION: Once an event is emitted on L2, it will persist in the canonical chain
EVIDENCE IN CODE: Off-chain agents treat event emission as the trigger for L1 action
VIOLATION CONDITION: L2 block containing the event is reorged/orphaned
CONSEQUENCE: Agent has already acted on phantom event; action is irreversible on L1
VIOLATION FEASIBILITY: HIGH - reorgs are inherent to blockchain consensus; "latest" != "finalized"
```

### A4: RPC Node Serves Canonical Chain State
```
ASSUMPTION: The RPC endpoint returns data from the canonical chain
EVIDENCE IN CODE: Off-chain agents query single RPC endpoint for state
VIOLATION CONDITION: RPC serves stale/orphaned blocks (eclipse attack, propagation delay, malicious node)
CONSEQUENCE: Agent's world model diverges from canonical chain; decisions based on phantom state
VIOLATION FEASIBILITY: MEDIUM - requires targeting specific RPC infrastructure
```

### A5: Nonce Protection Prevents Double-Spending
```
ASSUMPTION: Per-message nonces prevent the same withdrawal from executing twice
EVIDENCE IN CODE: withdrawn[hash] mapping or nonce tracking in L1 contracts
VIOLATION CONDITION: Nonce is derived from L2 tx data; if L2 tx is phantom, nonce is unique but illegitimate
CONSEQUENCE: Nonce protection works (prevents replay) but doesn't prevent initial phantom execution
VIOLATION FEASIBILITY: N/A - nonces don't protect against this vector (orthogonal defense)
```

### A6: Multi-Validator Consensus Prevents Single-Point Failure
```
ASSUMPTION: M-of-N validator threshold provides Byzantine fault tolerance
EVIDENCE IN CODE: Supermajority signature requirements (e.g., AdEx 2/3 validators)
VIOLATION CONDITION: All N validators share same data source (RPC); data source is eclipsed
CONSEQUENCE: All validators sign phantom message; threshold provides no protection
VIOLATION FEASIBILITY: LOW-MEDIUM - depends on validator infrastructure diversity
```

### A7: Settlement Timing Is Not Exploitable
```
ASSUMPTION: The time between L2 event and L1 settlement is operationally safe
EVIDENCE IN CODE: No explicit finality checks in off-chain agent code (typically)
VIOLATION CONDITION: Attacker controls block production/ordering during finality gap
CONSEQUENCE: Attacker can create phantom events that trigger real settlements
VIOLATION FEASIBILITY: HIGH on centralized-sequencer L2s; MEDIUM on decentralized L2s
```

### A8: Database State Reflects Blockchain State
```
ASSUMPTION: Off-chain database (Redis/MySQL) accurately mirrors on-chain state
EVIDENCE IN CODE: Agent writes DB records on event detection
VIOLATION CONDITION: Event was from unfinalized block; DB record persists after reorg
CONSEQUENCE: Persistent state corruption; downstream processes act on phantom data
VIOLATION FEASIBILITY: HIGH - DB writes are not blockchain-aware; no rollback mechanism
```

## Cross-Function Assumption Matrix

| L2 Action | Off-Chain Step | L1 Action | Assumption Chain |
|-----------|---------------|-----------|-----------------|
| User deposits on L2 | Agent reads event | Agent signs L1 release | A1 + A3 + A7 |
| User posts intent on L2 | Solver reads intent | Solver fills on L1 | A3 + A4 + A7 |
| Cross-domain message sent | Messenger relays | L1 bridge finalizes | A2 + A3 |
| OTC order created on L2 | Matcher reads order | Settlement on L1 | A3 + A4 + A8 |

## Violation Priority (by feasibility × impact)

1. **A1 + A3 + A7** (relayer trust + event impermanence + timing): CRITICAL PATH
2. **A4 + A8** (RPC eclipse + DB poisoning): HIGH IMPACT, MEDIUM FEASIBILITY
3. **A2** (messenger relay of unfinalized): VARIES BY BRIDGE IMPLEMENTATION
4. **A6** (shared RPC for validators): ARCHITECTURAL WEAKNESS, HARD TO PROVE
