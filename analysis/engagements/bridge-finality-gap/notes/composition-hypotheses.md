# Composition Hypotheses: Multi-Vector Drain Scenarios

## Principle: Each vector alone is "low/medium." Combined = kill chain.

---

## HC-1: Across Layered Defense Collapse (Slow Fill Injection Chain)

**Composition of 5 individually-minor issues:**

| # | Individual Issue | Alone = | Combined Role |
|---|-----------------|---------|---------------|
| V1 | requestSlowFill has no origin validation | "By design, dataworker filters" | Creates permissionless on-chain entry point for phantom data |
| V2 | Dataworker uses "latest" not "finalized" (5-block buffer << 64-slot finality) | "Speed trade-off" | Dataworker validates phantom deposits that haven't finalized |
| V3 | Single EOA proposer (automated bot) | "Trusted operator" | Automated posting = no human review of root contents |
| V4 | Zero disputes ever, dormant mechanism | "No malicious proposals yet" | No safety net catches injection |
| V5 | amountToReturn not in balance check | "Edge case" | Excess funds from slow fill race create accounting slack |

**Kill chain:**
```
T0: Attacker creates deposit on L2 in block that will be reorged (or sequencer-fabricated)
T1: Attacker calls requestSlowFill(fabricatedRelayData) on L1/dest [V1: no validation]
T2: Dataworker reads RequestedSlowFill, queries L2 for deposit using "latest" [V2: reads unfinalized]
T3: Dataworker FINDS deposit (it's in an unfinalized block), validates it → includes in root
T4: L2 block reorged → deposit vanishes from canonical chain
T5: Automated proposer bot posts root bundle [V3: no human review]
T6: 30-min liveness, zero disputes [V4: dormant safety net]
T7: executeRootBundle → HubPool sends real tokens to SpokePool (netSendAmounts)
T8: executeSlowRelayLeaf → tokens sent to attacker's recipient address
T9: attacker-address receives tokens; original L2 deposit never existed canonically
```

**Value extraction:**
- SpokePool ETH balance: ~$380K per drain cycle
- HubPool sends MORE via netSendAmounts (refill for slow fill)
- Repeatable every root bundle cycle (~32 min)
- Total extractable: bounded by HubPool liquid reserves per token

**Why this survived audits:**
- Each issue was reviewed in isolation and deemed acceptable
- The COMPOSITION requires understanding the protocol as an economic system:
  - On-chain permissionlessness (V1) feeds into off-chain data pipeline (V2)
  - Off-chain pipeline feeds into single automated proposer (V3)
  - Proposer's output is uncontested due to dormant disputes (V4)
  - Result: permissionless on-chain action → real fund extraction
- Standard smart contract audits focus on on-chain logic; this exploit chain crosses the on-chain/off-chain boundary

**Feasibility constraints:**
- Requires L2 block reorg or sequencer-level manipulation (attacker tier: HIGH)
- OR: RPC eclipse on dataworker's L2 endpoint
- BUNDLE_END_BLOCK_BUFFERS: ETH=5 blocks (60s window) is the timing target

---

## HC-2: Across Speed-Up Replay + Slow Fill Redirect (Cross-Deposit Confusion)

**Composition of 3 issues:**

| # | Individual Issue | Alone = | Combined Role |
|---|-----------------|---------|---------------|
| V1 | unsafeDeposit allows depositId collision | "Acknowledged risk in NatSpec" | Creates key collision for speed-up signatures |
| V2 | Speed-up binds to (depositId, chainId) not relay hash | "Convenience trade-off" | Signature from deposit A valid for deposit B |
| V3 | Slow fill path uses dataworker-computed updatedRecipient | "Off-chain trust" | Redirected slow fill pays wrong recipient |

**Kill chain:**
```
Step 1: Legitimate deposit D1 created (safe deposit, depositId=X)
Step 2: D1's depositor signs speedUpV3Deposit(X, chain, newRecipient=ATTACKER_ADDR)
Step 3: D1 gets filled normally (speed-up event recorded but fill completed)
Step 4: Time passes. Attacker creates D2 via unsafeDeposit with depositNonce producing depositId=X
Step 5: D2 has different amounts/tokens but SAME depositId on same chain
Step 6: Attacker requests slow fill for D2
Step 7: Dataworker sees speed-up event for depositId=X → applies to D2 (if depositor check is weak)
Step 8: Slow fill leaf uses updatedRecipient=ATTACKER_ADDR
Step 9: executeSlowRelayLeaf sends D2's outputAmount to attacker instead of intended recipient
```

**Feasibility assessment:**
- CRITICAL QUESTION: Does the dataworker check speed-up signer == deposit depositor?
- If YES: Attacker must BE the depositor of both D1 and D2 → self-attack only, no drain
- If NO: Cross-user redirect possible → drain of D2's intended recipient's funds
- Scale: Limited to individual deposits with colliding IDs, not full pool drain
- Requires unsafeDeposit usage (less common path)

**Discriminator needed:** Review Across dataworker source for speed-up signature validation logic

---

## HC-3: Celer Signer Cascade + Volume Bypass (Full Pool Drain)

**Composition of 4 issues:**

| # | Individual Issue | Alone = | Combined Role |
|---|-----------------|---------|---------------|
| V1 | Signer quorum can update itself (updateSigners) | "Feature for rotation" | Compromised 2/3 → permanent 100% control |
| V2 | Epoch boundary volume doubling | "Inherent to epoch rate limiting" | Initial extraction exceeds expected limits |
| V3 | Governor can set epochLength=0 and delayPeriod=0 | "Admin flexibility" | All rate limits and delays disabled |
| V4 | No cancel mechanism for delayed transfers | "Design limitation" | Once queued, transfers execute regardless |

**Kill chain (requires initial 2/3 signer compromise):**
```
Step 1: Compromise 2/3+ of signer stake weight (social engineering, key theft, etc.)
Step 2: Call updateSigners to install only attacker-controlled signers [V1: self-update]
Step 3: Now attacker has 100% signing power
Step 4: If attacker also controls governor OR can reach owner:
  - setEpochLength(0) → disable volume control [V3]
  - setDelayPeriod(0) → disable delays [V3]
Step 5: Sign relay messages draining entire pool balance
Step 6: Execute all relay messages in one block → full drain
```

**Without governor access:**
```
Step 3b: Sign relay messages up to volume cap
Step 3c: Time to epoch boundary → extract 2x cap [V2]
Step 3d: Repeat each epoch until pool drained or pauser reacts
```

**Value extraction:**
- With governor: entire pool balance in one block
- Without governor: 2x epochVolumeCap per epoch boundary, cap per normal epoch
- Pauser is the backstop (if different from compromised signers)

---

## HC-4: Across HubPool LP Rate Manipulation via Root Bundle (Slow Drain)

**Composition of 3 issues:**

| # | Individual Issue | Alone = | Combined Role |
|---|-----------------|---------|---------------|
| V1 | No semantic validation of root bundles on-chain | "Trust the liveness mechanism" | bundleLpFees can be inflated |
| V2 | undistributedLpFees smearing creates temporal rate changes | "Intended fee distribution" | Attacker can time LP entry/exit around fee events |
| V3 | Zero minimum LP deposit/supply | "Standard" | Precision exploitation at extreme values |

**Kill chain (requires proposer collusion):**
```
Step 1: Attacker deposits large LP amount just BEFORE a root bundle with inflated bundleLpFees
Step 2: Root bundle executes: _allocateLpAndProtocolFees adds to undistributedLpFees and utilizedReserves
Step 3: Over the smear duration, undistributedLpFees → 0, gradually increasing exchange rate
Step 4: Exchange rate = (liquidReserves + utilizedReserves - undistributedLpFees) / lpSupply
Step 5: As undistributedLpFees decreases, numerator increases → rate rises
Step 6: Attacker withdraws at higher rate → extracts portion of inflated fees

But: the fees are added to BOTH undistributedLpFees AND utilizedReserves equally.
Net immediate effect: utilizedReserves + X, undistributedLpFees + X → numerator change = 0.
Over time: undistributedLpFees decreases by fee distribution → numerator increases.
This is INTENDED behavior — LPs earn fees over time.
Inflated bundleLpFees would benefit ALL LPs proportionally, not just attacker.
```

**Assessment: WEAK composition. The intended fee mechanism distributes to all LPs proportionally. Attacker gets their proportional share, not a disproportionate extraction. Would need massive LP position relative to total supply to extract meaningfully. NOT a drain vector.**

---

## HC-5: Cross-Bridge Token Flow Confusion (Across + Celer/Synapse)

**Composition of cross-protocol interactions:**

| # | Individual Issue | Alone = | Combined Role |
|---|-----------------|---------|---------------|
| V1 | Across SpokePool holds funds for multiple tokens | "Shared pool" | Single drain affects all token holders |
| V2 | Fee-on-transfer accounting mismatch (both Across and Celer) | "Off-chain mitigated" | Gradual balance deficit in shared pools |
| V3 | No on-chain route validation in Across deposit | "Off-chain configured" | Can deposit non-standard tokens |

**Assessment: WEAK. Fee-on-transfer tokens are filtered off-chain. No mechanism to force protocol to accept them. Would require governance/admin to enable a malicious token route.**

---

## Ranking by Feasibility × Impact

| Rank | Hypothesis | Feasibility | Impact | Path to E3 |
|------|-----------|-------------|--------|------------|
| 1 | HC-1: Layered Defense Collapse | Medium (needs reorg/eclipse) | CRITICAL (pool drain) | Need to demonstrate phantom propagation through full pipeline |
| 2 | HC-3: Celer Signer Cascade | Medium (needs 2/3 signer compromise) | CRITICAL (pool drain) | Need to demonstrate signer → governor → drain chain |
| 3 | HC-2: Speed-Up Replay Redirect | Low-Medium (needs unsafeDeposit + weak dataworker check) | Medium (per-deposit redirect) | Need to review dataworker speed-up validation |
| 4 | HC-4: LP Rate Manipulation | Low (needs proposer collusion + minimal edge) | Low (proportional extraction) | Dead end — intended behavior |
| 5 | HC-5: Cross-Bridge Token | Very Low (needs admin/governance) | Low-Medium (gradual) | Dead end — off-chain mitigated |

---

## Next Discriminators

### For HC-1 (highest priority):
1. **Can we demonstrate a phantom deposit surviving long enough for dataworker to read it?**
   - Measure: time between L2 block broadcast and dataworker bundle construction
   - Evidence needed: dataworker timing logs or transaction timing analysis

2. **What EXACTLY does the dataworker do when it finds a RequestedSlowFill event?**
   - Review: Across dataworker source code for slow fill validation logic
   - Key question: does it use "latest" or "finalized" when looking up the origin deposit?

3. **Can we trigger the full chain on a fork?**
   - Setup: fork at pinned block, create a requestSlowFill, observe dataworker behavior
   - This would require running the actual dataworker code

### For HC-2:
1. **Does the dataworker check speed-up signer == deposit depositor?**
   - Review: Across dataworker source code for speed-up handling
   - If NO check: HC-2 becomes viable

### For HC-3:
1. **Are Celer governor and signer set the same entity?**
   - On-chain check: read governor address, compare to signer set
   - If same: signer compromise = governor compromise = full drain
