# Discriminator Designs: Bridge Finality Gap

## D1: Across Slow Fill Pipeline Phantom Propagation (CHEAPEST — Do First)

**Question:** Can a phantom L2 deposit propagate through requestSlowFill → dataworker → root bundle → executeSlowRelayLeaf?

**Why this matters:** If yes, the SpokePool balance can be drained by executing slow fill leaves for deposits that never existed canonically.

**Experiment Design:**

### Step 1: Trace requestSlowFill behavior (on-chain only)
- `requestSlowFill(relayData)` is permissionless
- It checks: fillDeadline not expired, exclusivity not active, fillStatus is Unfilled
- It does NOT verify the deposit actually exists on the origin chain
- It simply sets fillStatuses[relayHash] = RequestedSlowFill and emits event
- **Conclusion:** requestSlowFill DOES NOT validate deposit existence. Anyone can call it with arbitrary relay data.

### Step 2: Trace dataworker validation (off-chain — key unknown)
- The dataworker reads RequestedSlowFill events from destination chain
- It then checks the origin chain for the corresponding FundsDeposited event
- **KEY QUESTION:** Does the dataworker check `finalized` blocks or `latest`?
- If `latest`: phantom deposit in reorged block → dataworker includes in root
- If `finalized`: phantom deposit must survive finality → much harder to exploit
- **How to determine:** Read Across relayer/dataworker source code (github.com/across-protocol/relayer)

### Step 3: Root bundle submission
- `relayRootBundle()` is onlyAdmin (cross-domain from HubPool)
- HubPool admin is UMA Optimistic Oracle proposer
- Proposer posts merkle roots → liveness period → anyone can dispute
- If nobody disputes during liveness: root is accepted
- **Attack window:** propose root containing phantom slow fill → nobody disputes → execute

### Step 4: Execution
- `executeSlowRelayLeaf()` verifies merkle proof against stored root
- If proof valid → SpokePool.safeTransfer(outputToken, recipient, amount)
- No additional deposit verification at execution time

**Discriminator Experiment (cheapest):**
```
1. Search Across relayer GitHub for "finalized" vs "latest" block tag usage in dataworker
2. If dataworker uses "latest": proceed to timing analysis
3. If dataworker uses "finalized": H1 is likely infeasible (but check for edge cases)
```

### Risk Assessment:
- If exploitable: SpokePool balances at risk (millions per token per chain)
- Defense layers: UMA OO dispute mechanism, dataworker validation, MIN_DEPOSIT_CONFIRMATIONS
- Attack cost: gas for phantom L2 tx + requestSlowFill call (~$1-50)

---

## D2: Across Relayer Fast Fill Timing Test (SECOND — Behavioral)

**Question:** How quickly do Across relayers fill deposits relative to source chain finality?

**Experiment Design:**
1. Execute a small real deposit on an L2 SpokePool (e.g., $1 USDC on Optimism)
2. Record wall-clock time of L2 deposit tx confirmation
3. Monitor destination chain for FilledRelay event
4. Record wall-clock time of fill tx
5. Compute: fill_latency = fill_time - deposit_time
6. Compare against L2 finality time (e.g., Optimism: 7 days full, ~2 min safe)
7. If fill_latency < finality_time: relayer is acting on unfinalized state

**Expected Result:** fill_latency of seconds-to-minutes (Across advertises <30s fills)
This would CONFIRM relayers read "latest" blocks (already documented by Across).

**What this proves:** Relayers are vulnerable to phantom deposits (their own capital at risk)
**What this doesn't prove:** Whether the slow fill pipeline is also vulnerable (D1 answers that)

---

## D3: Metis Messenger Finality Model (THIRD — Source Analysis)

**Question:** Does the Metis CrossDomainMessenger relay messages from unfinalized L2 state?

**Experiment Design:**
1. Fetch Metis CrossDomainMessenger contract source
2. Trace the message relay path: L2 message → L1 messenger → L1 bridge
3. Determine if messenger requires state proof / finality proof
4. If no finality proof: messenger blindly relays → phantom withdrawal possible
5. If finality proof required: standard Optimistic Rollup security → 7-day delay

---

## D4: Across HubPool → SpokePool Admin Trust Chain (FOURTH)

**Question:** Who controls `relayRootBundle` and how fast can a malicious root be posted?

**Experiment Design:**
1. Read HubPool contract to understand proposer/disputer mechanics
2. Trace the UMA OO integration: who can propose? what's the liveness period?
3. Can the proposer front-run the dispute window?
4. What's the collateral required for proposals?

---

## Priority Order:
1. **D1** — Cheapest (code review of dataworker) and highest impact (pool drain)
2. **D2** — Confirms relayer behavior but lower systemic impact (relayer loss only)
3. **D3** — Metis-specific; requires additional source fetching
4. **D4** — Trust chain analysis; depends on D1 results

## Immediate Next Action:
Search the Across Protocol relayer codebase (GitHub) for how the dataworker validates
deposits before including them in root bundles. Specifically look for:
- Block tag usage (latest vs finalized vs safe)
- Deposit validation logic
- MIN_DEPOSIT_CONFIRMATIONS implementation in dataworker
