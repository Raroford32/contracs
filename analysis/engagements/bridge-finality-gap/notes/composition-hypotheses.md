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

**OFF-CHAIN DISCRIMINATOR RESULTS (2026-02-28): V2 CONFIRMED — "latest" block tag**

Source: `across-protocol/sdk` BaseAbstractClient.ts, SpokePoolClient → EVMSpokePoolClient

1. **Block tag: `provider.getBlockNumber()` → defaults to "latest" in ethers.js**
   - BaseAbstractClient.updateSearchConfig(): `to = await provider.getBlockNumber()`
   - No explicit "finalized" or "safe" block tag used anywhere in the query pipeline
   - Events are queried from `from` (last searched + 1) to `to` (latest block number)

2. **BUNDLE_END_BLOCK_BUFFERS (from `across-protocol/relayer/src/common/Constants.ts`):**
   - MAINNET: 5 blocks (~60 seconds)
   - Comment: "safely above the finalization period" — but this is FALSE for Ethereum
   - Ethereum finality = 64 slots = ~768 seconds (12.8 minutes)
   - **Buffer is 12.8x BELOW actual finality threshold**

3. **Other chain buffers for context:**
   - Polygon: 128 blocks (~256s) vs variable finality
   - Arbitrum: 240 blocks (~60s)
   - OP_STACK: 86400 blocks (~2 days) — these are conservative
   - Mainnet's 5-block buffer is an OUTLIER — all L2 buffers are much more conservative

4. **MIN_DEPOSIT_CONFIRMATIONS (separate from bundle buffer):**
   - $10K+: Mainnet=32 blocks (~6.4 min) — still below 12.8 min finality
   - $1K+: Mainnet=4 blocks (~48s) — massively below finality
   - $100+: Mainnet=2 blocks (~24s)
   - These apply to relayer FILL decisions (speed vs finality risk trade-off)
   - Dataworker bundle construction uses BUNDLE_END_BLOCK_BUFFERS, not these

5. **Implication for HC-1:**
   - V2 is CONFIRMED: Dataworker queries "latest" and applies only 5-block buffer
   - A deposit visible at "latest" but not yet finalized WILL be included in bundle data
   - If that deposit's block is reorged before finality, the dataworker has read phantom state
   - The window for phantom injection is ~12+ minutes (finality gap minus buffer)
   - **HC-1 kill chain V2 is live on current production code**

**UPDATED FEASIBILITY:**
- Attacker needs to create a deposit that exists at query time but reorgs away
- This requires either: (a) L2 sequencer collusion, (b) L2 reorg capability, or (c) RPC eclipse
- For Ethereum Mainnet itself: 64-slot finality makes reorgs extremely rare but not impossible
- For L2 chains (where most deposits originate): finality depends on L1 posting
- **Key insight: L2 deposits destined for L1 slow fill are the softest target**
  - L2 block can be published by sequencer but not yet posted to L1
  - Dataworker reads L2 "latest" block containing deposit
  - If sequencer fails to post or reorgs, deposit never existed canonically

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

**DISCRIMINATOR RESULT (2026-02-28): HC-2 FALSIFIED — BLOCKED at 3 layers**

Source: Across SDK (`across-protocol/sdk`) SpokePoolClient + relayer DataworkerUtils

1. **SpokePoolClient depositor match (Layer 1):** Speed-ups indexed by `[depositor][depositId]`.
   When applying, checks `deposit.depositor.eq(speedUp.depositor)` — cross-user matching blocked.

2. **Dataworker slow fill construction (Layer 2):** `buildV3SlowFillLeaf()` ignores speed-up data entirely.
   Uses original `deposit.recipient`, NOT `updatedRecipient`. Slow fill leaves never reference speed-ups.

3. **On-chain slow fill execution (Layer 3):** `executeSlowRelayLeaf()` hardcodes
   `updatedRecipient: relayData.recipient` (line 1174 SpokePool.sol). The contract has a @TODO
   comment noting speed-up data is intentionally NOT supported for slow fills yet.

**Remaining narrow scenario:** Same depositor using `unsafeDeposit` can replay speed-up signatures
on colliding depositIds for the FAST fill path only. This is self-attack, acknowledged in NatSpec,
and requires a relayer to voluntarily use the stale speed-up data. NOT a drain vector.

**VERDICT: HC-2 is DEAD. Three independent defenses prevent the attack chain.**

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

**DISCRIMINATOR RESULTS (2026-02-28): HC-3 CASCADE PATH INVESTIGATED**

1. **Owner identity:** 0xF380166F is a custom governance/voting contract (NOT Gnosis Safe)
   - 6 voters: 5 with power=10000, 1 with power=1 (total: 50,001)
   - Pass threshold: 60% → needs 4 of 5 main voters
   - Active period: 1 day, MIN=1hr, MAX=28 days
   - 93 proposals created to date

2. **Owner can addGovernor():** Yes, `addGovernor(address)` is `onlyOwner` (line 1659)
   - Requires governance proposal with 60%+ vote (4/5 main voters)
   - Owner can also `resetSigners()`, `addPauser()`, `removePauser()`

3. **Signer-Voter overlap:** **ZERO OVERLAP**
   - 17 bridge signers (stake-weighted, top 3 = ~45.6%)
   - 6 governance voters (5 equal-power EOAs)
   - No addresses in common
   - Signer compromise does NOT cascade to governance

4. **Updated HC-3 chain:**
   - Signer compromise (2/3 stake-weight) → `updateSigners()` → 100% signing power
   - BUT: no governor access, no owner access
   - Max extraction: 2x epochVolumeCap per epoch boundary
   - USDC: min($2M, $1.478M pool) = $1.478M; USDT: min($2M, $1.687M) = $1.687M
   - **Total without governor: ~$3.38M** (capped by pool balances)
   - Pauser can freeze if they detect the attack

5. **Full drain requires:** 2/3 signer compromise + 4/5 governance voter compromise = VERY HIGH bar
   - This is 2 independent compromise operations against non-overlapping parties
   - NOT a composition vulnerability — just multi-entity compromise

**VERDICT: HC-3 without governor access = $3.38M max (significant but requires 2/3 signer compromise).
HC-3 with full cascade = blocked by 0 signer-voter overlap. Not a composition kill chain.**

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

## On-Chain Discriminator Results (block ~24553401)

### D1: requestSlowFill Permissionless Entry (HC-1 V1) — CONFIRMED
- fabricated relay hashes start as Unfilled (0)
- requestSlowFill would SUCCEED for any fabricated V3RelayData
- No on-chain origin validation exists
- SpokePool has ~500 root bundles, 3.7M safe deposits to date

### D2: HubPool Proposal State (HC-1 V3/V4) — PARTIAL
- ABI decoding error on `rootBundleProposal()` return tuple
- Raw bytes confirm proposer = 0xf7bAc63fc7CEaACf0589F25454Ecf5C2CE904997c (single EOA)
- Latest rootBundleId: 19645 (very active system)
- Latest slowRelayRoot = 0x00...00 (empty = no pending slow fills in latest bundle)
- 31 root bundles relayed in last 5000 blocks (~2.5 days)

### D3: ABT Transfer Bypass (standalone) — CONFIRMED but DEAD END
- ABT.transfer() bypasses whitelist (only transferFrom overridden)
- ABT ≠ WETH (different addresses) → ABT donations don't affect WETH LP rate
- proposeRootBundle uses safeTransferFrom → can't bypass whitelist for proposals
- **VERDICT: ABT transfer bypass is not composition-useful. Eliminating from kill chains.**

### D4: Celer Governor/Signer Overlap (HC-3) — KEY FINDING
- Owner: 0xF380166F8490F24AF32Bf47D1aA217FBA62B6575
- **Owner is NOT a governor** → signer cascade alone doesn't get governor powers
- epochLength: 1800s (30 min), delayPeriod: 1800s (30 min)
- Volume caps: USDC=$1M, USDT=$1M, WETH=400
- Delay thresholds: USDC=$500K, USDT=$500K, WETH=250
- Pool balances: USDC=$1.478M, USDT=$1.687M, WETH=218
- **IMPACT ON HC-3:**
  - Without governor: max extraction = 2x epochVolumeCap per epoch boundary
  - USDC: $2M per boundary → pool has $1.478M (drainable in ~1 boundary)
  - USDT: $2M per boundary → pool has $1.687M (drainable in ~1 boundary)
  - WETH: 800 WETH per boundary → pool has only 218 WETH
  - **Total extractable WITHOUT governor: ~$3.38M in one epoch boundary window**
  - With governor (owner compromise): disable all limits → full drain in one block
  - **QUESTION: Can owner add itself as governor? Is owner a multisig?** (investigating)

### D6: HubPool LP State (HC-1/HC-4) — CONFIRMED
- WETH: liquid=2,432 + utilized=3,638 - fees=2.3 = 6,068 WETH total ($~12M)
- WETH LP supply: 5,458 → exchange rate: 1.1116
- USDC: liquid=1.32M + utilized=720K = $2.04M total, LP supply near zero
- SpokePool ETH balance: only 21 WETH (much less than initial estimate of 75 WETH)
- **HubPool is the larger target** — $12M WETH + $2M USDC in reserves

### D7: Balance Analysis (HC-1 drain sizing)
- Across WETH: SpokePool=21 + HubPool=2,624 = 2,645 WETH total in protocol
- Across USDC: SpokePool=151K + HubPool=1.45M = $1.6M total in protocol
- **HC-1 drain per cycle: executeSlowRelayLeaf extracts from SpokePool (21 WETH currently)**
- **But netSendAmounts from HubPool refills SpokePool** → total extractable scales with HubPool reserves

---

## Final Ranking by Feasibility × Impact (post all discriminators)

| Rank | Hypothesis | Feasibility | Impact | Status |
|------|-----------|-------------|--------|--------|
| 1 | **HC-1: Layered Defense Collapse** | **Medium (needs L2 reorg/sequencer)** | **CRITICAL ($12M+ drain)** | **V1 + V2 CONFIRMED on-chain + off-chain. Full kill chain viable.** |
| 2 | HC-3: Celer Signer Cascade | High (needs 2/3 signer compromise) | Medium ($3.38M without governor) | No signer-voter overlap; caps at epoch boundary |
| 3 | HC-2: Speed-Up Replay Redirect | **DEAD** | **DEAD** | **Falsified: 3 independent defenses block the chain** |
| 4 | HC-4: LP Rate Manipulation | Dead | Dead | Intended behavior confirmed |
| 5 | HC-5: Cross-Bridge Token | Dead | Dead | Off-chain mitigated confirmed |

---

## HC-1 Evidence Summary (Strongest Composition Hypothesis)

### Confirmed vectors (5/5):
| Vector | Status | Evidence |
|--------|--------|----------|
| V1: requestSlowFill permissionless | **CONFIRMED** | D1: fabricated hashes → Unfilled(0); no auth gate on-chain |
| V2: Dataworker "latest" block tag | **CONFIRMED** | SDK BaseAbstractClient: `provider.getBlockNumber()` = latest; BUNDLE_END_BLOCK_BUFFERS ETH=5 |
| V3: Single automated proposer | **CONFIRMED** | D2: proposer=0xf7bac63f (single EOA); 19,645+ bundles |
| V4: Zero disputes historically | **CONFIRMED** | No dispute events found in protocol history |
| V5: amountToReturn gap | **CONFIRMED** | L2 in SpokePool.sol: balance check excludes amountToReturn |

### What remains for E3:
The ENTIRE kill chain is architecturally viable. The sole remaining question is:
**Can an attacker reliably cause an L2 deposit to exist at "latest" but never finalize?**

Attack vectors for phantom deposit:
1. **L2 sequencer manipulation** — sequencer includes deposit tx in block, doesn't post to L1
2. **L2 reorg** — deposit block gets reorged (more likely on chains with fast blocks)
3. **RPC eclipse** — dataworker's RPC endpoint serves stale/fabricated L2 state
4. **L2-specific finality gap** — L2 blocks are "latest" before L1 posting; window varies by L2

---

## DEEP INVESTIGATION RESULTS (2026-02-28): Resolving All Remaining Paths

### Investigation 1: Dataworker Deposit Cross-Check — CONFIRMED REQUIRED

**Source:** Across SDK `BundleDataClient.loadData()` + `queryHistoricalDepositForFill()`

The dataworker performs a **13-field validation** against the origin chain:
1. Queries origin chain SpokePoolClient for matching `V3FundsDeposited` event
2. If not in memory, performs `findDeposit()` — on-chain historical event query
3. `validateFillForDeposit()` compares ALL 13 fields: depositId, originChainId, destinationChainId, depositor, recipient, exclusiveRelayer, inputToken, outputToken, inputAmount, outputAmount, fillDeadline, exclusivityDeadline, messageHash
4. Additional checks: `_canCreateSlowFillLeaf()` (token equivalence) + `_depositIsExpired()` + not already filled

**VERDICT: Pure fabrication (no real deposit) → BLOCKED by dataworker deposit matching.**
The attack REQUIRES a real deposit that exists when the dataworker queries it.

### Investigation 2: Race Condition Paths — ALL BLOCKED

**Path A: Fast fill + slow fill double-pay**
BLOCKED at SpokePool.sol line 1594: `if (fillStatuses[relayHash] == Filled) revert RelayFilled()`
Even if slow fill leaf is in the proposed root, on-chain execution reverts if fast fill already happened.

**Path B: fillDeadline expiry during liveness**
BLOCKED at SpokePool.sol line 1570: `if (relayData.fillDeadline < getCurrentTime()) revert ExpiredFillDeadline()`
On-chain check at execution time prevents expired slow fills.

**Path C: Deposit refund + slow fill double-spend**
BLOCKED by architecture: There is NO on-chain `refundDeposit()` function. Deposit refunds happen
through the SAME dataworker root bundle mechanism (via `RelayerRefundLeaf.refundAddresses`).
The dataworker builds slow fill root + refund root SIMULTANEOUSLY from consistent state.
A deposit that gets a slow fill leaf does NOT get a refund. Mutually exclusive by design.

Even across different bundles: if slow fill executes in Bundle N, the `FilledRelay` event with
`FillType.SlowFill` tells the dataworker in Bundle N+1 that the deposit was filled → no refund.

### Investigation 3: L2 Finality Gap Analysis — STRUCTURAL VULNERABILITY FOUND

**CHEAPEST PATH: Low-throughput OP Stack chains (Mode, Zora, Lisk, Ink, Soneium)**

Full analysis: `notes/l2-finality-analysis.md`

| Chain | Across Buffer | True Finality | GAP | Exploit Difficulty |
|-------|--------------|---------------|-----|-------------------|
| Mode/Zora/Lisk/Ink | 120s | Hours (batch posting) | **HOURS** | LOW (organic batcher delay) |
| Base/Optimism | 120s | 5-10 min | 3-8 min | MEDIUM |
| Arbitrum | 60s | 10-20 min | 9-19 min | MEDIUM |
| Linea | 120s | 8-32 hours | 8-32 hours | LOW but low value |
| zkSync | 120s | ~3 hours | ~3 hours | MEDIUM |
| Polygon PoS | 256s | 5 seconds | NEGATIVE | SAFE (Heimdall v2) |

**CRITICAL STRUCTURAL FLAW:**
Across applies **uniform 60-block buffer (120s)** to ALL OP Stack chains regardless of batch posting frequency. A deposit on Mode (batch every few hours) gets the same buffer as Base (batch every few minutes). On low-volume chains, deposits can exist for HOURS in purely sequencer-confirmed state with zero L1 backing, yet pass the Across dataworker's buffer check after just 120 seconds.

**September 2025 OP Stack DA DoS Attack (Conduit disclosure):**
- Demonstrated that OP Stack chains can be forced to reorg via DA spam
- Patched in op-batcher v1.15.0 (September 2025)
- Chains NOT running patched batcher are still vulnerable
- Low-volume chains may have longer windows for organic batcher failures

### Investigation 4: Dispute Mechanism — ROBUST BUT NOT PERFECT

- Dispute cost: 0.45 ETH (low, accessible to any honest observer)
- ABT whitelist does NOT block disputers (only blocks unauthorized proposers)
- Liveness: 30 minutes
- Can't replace proposal during liveness (`noActiveRequests` modifier)

**The dispute mechanism assumes honest watchers are running the dataworker independently.**
If the attacker targets a low-volume L2 chain that most independent dataworkers don't monitor,
the dispute window becomes a "no one is watching" problem.

---

## FINAL ASSESSMENT: HC-1 Kill Chain Viability

### Refined Kill Chain (Low-Volume OP Stack Target)

```
T+0s:    Attacker deposits on Mode (chain 34443) — cost: <$0.10
T+2s:    Mode sequencer confirms (unsafe block, NO L1 backing)
T+120s:  Across 60-block buffer passes
T+120s+: Dataworker queries Mode "latest", finds real deposit, validates 13 fields ✓
T+120s+: requestSlowFill on destination chain (fabricated relay data matching deposit)
T+~32m:  Dataworker includes slow fill in root bundle proposal
T+~62m:  30-min liveness passes, no dispute (if no one monitors Mode independently)
T+~62m+: executeRootBundle → HubPool sends tokens via netSendAmounts
T+~62m+: executeSlowRelayLeaf → real tokens sent to attacker's recipient
T+???:   Mode batcher posts batch hours later (deposit is real)
         OR batcher fails → deposit block reorged → deposit never existed
```

### Three Scenarios After Execution:

**Scenario A: Batcher posts normally (deposit is real)**
- Slow fill executed for a real deposit → LEGITIMATE fill
- No drain — this is normal protocol operation
- Attacker got their deposit filled, nothing stolen

**Scenario B: Batcher fails / DA DoS attack (deposit reorgs)**
- Slow fill executed for a phantom deposit → DRAIN
- HubPool sent real tokens for a deposit that no longer exists
- Attacker extracted real value for phantom deposit
- Solvency equation violated

**Scenario C: Attacker also gets refund (double-spend)**
- BLOCKED: deposit refund mechanism is in the SAME dataworker pipeline
- If deposit reorgs, dataworker can't find it for refund either
- If deposit survives, slow fill was legitimate (no issue)

### STATUS: DESIGN RISK — Sub-E3 at permissionless attacker tier

**What makes this NOT E3:**
1. Scenario A (batcher posts normally) is the likely outcome — no drain
2. Scenario B requires batcher failure — either organic (unpredictable) or DA DoS (patched, $100K+ cost)
3. The attacker can't RELIABLY cause Scenario B without infrastructure access
4. Independent dispute bots may catch the invalid bundle during 30-min liveness

**What makes this a REAL design risk:**
1. ALL 5 defense layers have confirmed weaknesses
2. The structural buffer asymmetry is a real misconfiguration (120s buffer on hours-between-batches chains)
3. Organic batcher failures DO happen (~60% of L2 incidents are sequencer-related per L2BEAT data)
4. Low-volume chain monitoring may be insufficient for dispute-based security
5. If the September 2025 DA DoS attack is not patched on all chains, it becomes cheaper
6. The economic incentive is massive: $12M+ extractable from HubPool reserves

### RECOMMENDED FIX (if reporting to Across team):
1. Use "safe" or "finalized" block tag instead of "latest" for deposit queries
2. Per-chain buffer calibration based on ACTUAL batch posting frequency, not uniform default
3. Independent dispute bot for ALL supported L2 chains, not just high-volume ones
4. Consider requiring N L1 confirmations for origin chain deposits before slow fill eligibility
