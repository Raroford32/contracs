# L2 Finality Analysis: Cheapest Path to Phantom Deposit Creation

## Context

Across Protocol's dataworker queries L2 chain events using `provider.getBlockNumber()` which returns "latest" block. It applies `BUNDLE_END_BLOCK_BUFFERS` before including data. This analysis determines which L2 chain has the largest and most exploitable gap between "latest" and "truly final."

## Across Protocol BUNDLE_END_BLOCK_BUFFERS (from Constants.ts)

| Chain | Buffer (blocks) | Approx Block Time | Buffer Duration | Notes |
|-------|-----------------|-------------------|-----------------|-------|
| Ethereum Mainnet | 5 | 12s | ~60s | OUTLIER: 12.8x below 64-slot finality (768s) |
| Arbitrum One | 240 | 0.25s | ~60s | Orbit family default |
| OP Stack (all) | 60 | 2s | ~120s | Auto-populated default for Optimism/Base/Blast/Mode/Zora/etc |
| Polygon PoS | 128 | 2s | ~256s | "Historically reorg-prone" |
| zkSync Era | 120 | ~1s | ~120s | ZK_STACK family default |
| Linea | 40 | 3s | ~120s | |
| Scroll | 40 | 3s | ~120s | |
| BSC | 5 | 3s | ~15s | "2x average finality" |
| MegaETH | 300 | variable | variable | "Conservative for variable finality" |
| Monad | 150 | 0.4s | ~60s | "2 block finality" |
| Plasma | 180 | variable | variable | "Conservative due to uncertain finality" |
| HyperEVM | 120 | variable | ~60s | |

---

## Chain-by-Chain Finality Analysis

### 1. OP Stack Chains (Optimism, Base, Blast, Mode, Zora, Lisk, Ink, Soneium, Unichain, World Chain)

**Finality Model:**
- **Unsafe** (sequencer receipt): ~2 seconds. Sequencer includes tx, distributes via p2p. NO L1 backing.
- **Safe** (batch posted to L1): ~5-10 minutes. Batcher posts batch data to Ethereum as blobs/calldata.
- **Finalized** (L1 finalized): ~20-30 minutes. Ethereum block containing the batch is finalized.

**Sequencer:** Single centralized sequencer per chain.
- Optimism: OP Labs
- Base: Coinbase
- Blast: Blast team
- Mode/Zora/etc: respective teams

**Critical Facts:**
- Sequencer window: 12 hours maximum before unsafe blocks are reorged
- Batcher posts every few minutes on high-throughput chains (Base, Optimism), up to 5-6 hours on low-throughput chains
- **Unsafe blocks CAN be reorged** if the batch is not posted within the sequencing window
- Sequencer can reorder, delay, or deviate from promised soft confirmations
- Force inclusion available via L1 (but with up to 12h delay)

**Across Buffer vs True Finality:**
- Buffer: 60 blocks = ~120 seconds
- True finality (L1-posted + finalized): ~20-30 minutes
- **GAP: ~18-28 minutes of unfinalized data visible to the dataworker**
- During this window, deposit exists as "unsafe" -- sequencer has confirmed it but batch not yet on L1

**Phantom Deposit Window:**
- Deposit is created on L2, sequencer confirms it (~2s)
- Across buffer passes (120s later)
- Dataworker reads deposit as valid
- Batch must still be posted to L1 (~5-10 min for high-throughput chains)
- If sequencer fails to post batch, or deviates, deposit never materializes on L1
- **Window: ~3-28 minutes depending on batcher cadence**

**Historical Reorgs:** No major L2 reorgs observed on OP Stack chains as of Feb 2026, but the 12-hour sequencing window expiration scenario has been documented (ethereum-optimism/optimism#11228).

**Exploitability Rating: MEDIUM-HIGH**
- Single sequencer = single point of trust
- Unsafe window (pre-batch-posting) is the largest gap on any major rollup relative to Across buffer
- Sequencer can technically produce blocks that never get batched
- Low-throughput OP Stack chains (Mode, Zora, Lisk) have LONGER batch posting intervals = LARGER windows

---

### 2. Arbitrum One

**Finality Model:**
- **Soft finality** (sequencer receipt): ~260ms. Fastest of all L2s. Trust-based.
- **Hard finality** (batch posted to L1 + L1 finality): ~10-20 minutes.
- **Full settlement** (challenge period): ~1 week.

**Sequencer:** Single centralized sequencer (Arbitrum Foundation / Offchain Labs).

**Critical Facts:**
- Sequencer posts batches to L1 every few minutes (typically 5-15 min on Arbitrum One)
- Sequencer CAN reorder or temporarily delay transactions between soft and hard finality
- Force inclusion via L1 with 24-hour delay
- Sequencer CANNOT forge transactions or propose invalid state

**Across Buffer vs True Finality:**
- Buffer: 240 blocks at ~0.25s/block = ~60 seconds
- True finality (batch posted + L1 finalized): ~10-20 minutes
- **GAP: ~9-19 minutes of unfinalized data**

**Phantom Deposit Window:**
- Deposit created, sequencer confirms in ~260ms
- Buffer passes (~60s)
- Dataworker reads deposit
- Batch posting: 5-15 minutes typical
- **Window: ~4-19 minutes**

**Historical Reorgs:** No Arbitrum One reorgs observed. Sequencer outage Dec 2023 (78 minutes) caused stale state but no reorg.

**Exploitability Rating: MEDIUM**
- Single sequencer but high posting frequency limits the window
- Sequencer is well-established (Offchain Labs)
- Lower batch latency than OP Stack reduces the gap

---

### 3. Arbitrum Nova

**Finality Model:** Same sequencer model as Arbitrum One, but uses AnyTrust DAC instead of full L1 data posting.

**Key Difference:** DAC provides a weaker data availability guarantee (trust 2-of-7 DAC members are honest). If DAC fails, falls back to full rollup mode.

**Across Buffer:** Same as Arbitrum One (240 blocks = ~60s)

**Exploitability Rating: MEDIUM**
- Same sequencer risks as Arbitrum One
- DAC adds a different trust surface but doesn't change the "latest" vs "finalized" gap meaningfully
- Lower TVL/volume means lower value at risk

---

### 4. Polygon PoS

**Finality Model (Post-Heimdall v2, July 2025):**
- **Latest** (Bor block): ~2 seconds
- **Safe/Finalized** (milestone-confirmed): ~2-5 seconds deterministic finality
- **Checkpoint** (L1-posted): every 256 blocks minimum

**Sequencer:** Decentralized validator set (100+ validators). NOT a single sequencer.

**Critical Historical Facts:**
- Pre-Delhi (Jan 2023): up to 128-block reorgs (~5 minutes)
- Post-Delhi: reorgs still common, up to 32 blocks (~1 minute)
- Nov 2023: 157-block reorg despite Delhi fix
- Post-Heimdall v2 (Jul 2025): reorgs capped at 2 blocks, finality ~5 seconds

**Across Buffer vs True Finality:**
- Buffer: 128 blocks at ~2s/block = ~256 seconds (~4.3 minutes)
- True finality (post-Heimdall v2): ~5 seconds
- **Post-Heimdall v2: Buffer EXCEEDS finality. GAP IS NEGATIVE (safe).**
- **Pre-Heimdall v2: GAP was ~1-4 minutes (reorg-prone)**

**Phantom Deposit Window (Post-Heimdall v2):**
- Effectively closed. 5-second finality < 256-second buffer.
- The 128-block buffer was calibrated for the OLD Polygon, which was reorg-heavy.

**Phantom Deposit Window (Pre-Heimdall v2, historical):**
- 32-block reorgs (~64s) were common
- 157-block reorg (Nov 2023) would have exceeded the 128-block buffer
- **Historical window: 0-5 minutes (highly variable)**

**Exploitability Rating: LOW (current) / HIGH (historical, pre-July 2025)**
- Heimdall v2 effectively eliminated the reorg-based phantom deposit vector
- Decentralized validator set makes sequencer manipulation much harder than L2s
- But if Across hasn't updated the buffer for post-Heimdall v2 reality, the buffer is now wastefully conservative

---

### 5. Polygon zkEVM

**Finality Model:**
- **Trusted State** (sequencer confirmation): 2-3 seconds
- **Virtual State** (L1 data availability): batch posted to L1
- **Consolidated State** (ZK proof verified on L1): varies, historically hours

**Sequencer:** Single centralized sequencer (Polygon Labs).

**Critical Facts:**
- Centralized sequencer with permissionless fallback for censorship resistance
- ZK proofs take significant time to generate
- Unproven batches can be deleted (unlike standard ZK rollup expectations)
- Each tx = one block (1:1 design for instant finality within the sequencer)

**Across Buffer:** Not explicitly listed (likely OP Stack default or custom)

**Exploitability Rating: MEDIUM-LOW**
- Single sequencer but relatively low volume/TVL on Across
- ZK proof requirement for true finality creates a large gap
- But Scroll-level proof times are improving

---

### 6. zkSync Era

**Finality Model:**
- **Soft confirmation** (sequencer): instant (sub-second)
- **Batch committed** to L1: minutes
- **Proof generated**: ~1 hour (historically), improving to 15 min-2 hours in 2025
- **Batch finalized** on L1: previously 21-24 hours (alpha delay), now 3 hours, targeting lower
- **Atlas upgrade**: targeting 1-second finality

**Sequencer:** Single centralized sequencer (Matter Labs).

**Critical Facts:**
- Centralized sequencer with force-inclusion via L1 priority queue
- 3-hour execution delay as security measure (down from 21 hours)
- No mechanism to force inclusion if sequencer is down (priority queue exists but delays)
- MEV extraction possible by centralized sequencer

**Across Buffer vs True Finality:**
- Buffer: 120 blocks at ~1s/block = ~120 seconds
- True finality (proof verified + delay): ~3 hours minimum
- **GAP: ~2 hours 58 minutes of unfinalized data**

**Phantom Deposit Window:**
- This is the LARGEST absolute gap of any chain
- But ZK proof requirement means the sequencer cannot post invalid state
- A deposit that exists in a committed-but-unproven batch could theoretically be in a batch that gets deleted
- **Window: theoretically up to 3+ hours**

**Exploitability Rating: MEDIUM**
- Largest absolute gap, but ZK proof provides stronger guarantee than optimistic rollups
- Batch deletion mechanism creates theoretical phantom deposit surface
- Single sequencer is the primary risk factor

---

### 7. Linea

**Finality Model:**
- **Soft finality** (sequencer): ~2 seconds
- **Hard finality** (ZK proof verified on L1 + 2 epochs): 8-32 hours typical
- **Upcoming improvement**: targeting ~15 minutes by constraining tx ordering to L1-posted data

**Sequencer:** Single centralized sequencer (Consensys/Linea team).

**Critical Facts:**
- NO mechanism for forced inclusion if sequencer is down or censoring (CRITICAL)
- Only after 6 months of no finalized blocks does the Operator role become public
- Funds can be frozen if sequencer refuses exit transactions
- MEV extraction possible

**Across Buffer vs True Finality:**
- Buffer: 40 blocks at ~3s/block = ~120 seconds
- True finality (proof verified): 8-32 hours
- **GAP: 8-32 HOURS of unfinalized data visible to Across dataworker**

**Phantom Deposit Window:**
- Extremely large theoretical window
- But Linea's volume on Across is relatively low
- No forced inclusion mechanism makes sequencer trust critical

**Exploitability Rating: MEDIUM-HIGH (theoretical) / LOW (practical)**
- Massive finality gap but low Across volume
- No anti-censorship mechanism is the most extreme centralization of any major L2
- A compromised Linea sequencer could produce phantom deposits that persist for hours

---

### 8. Scroll

**Finality Model:**
- **Sequencer confirmation**: sub-second
- **Batch committed to L1**: batch posting interval
- **ZK proof generated + verified**: historically hours, targeting under 30 seconds in 2025
- **Key risk**: Scroll can DELETE unproven batches. True finality requires proof verification.

**Sequencer:** Single centralized sequencer (Scroll team).

**Across Buffer vs True Finality:**
- Buffer: 40 blocks at ~3s/block = ~120 seconds
- True finality (proof verified): varies, potentially hours
- **GAP: potentially hours of unfinalized data**

**Phantom Deposit Window:**
- Similar to zkSync Era -- ZK proof requirement creates large gap
- Batch deletion mechanism is a specific risk: unproven batches CAN be removed
- **Window: minutes to hours depending on proof generation cadence**

**Exploitability Rating: MEDIUM**
- Batch deletion is a unique risk factor
- Single sequencer
- Improving proof times will close this gap

---

## Ranking: Cheapest Path to Phantom Deposit

### Tier 1: CHEAPEST (Highest risk-to-cost ratio)

**OP Stack low-throughput chains (Mode, Zora, Lisk, Ink, Soneium, World Chain)**
- Cost: ~$0.01-$0.10 gas for L2 deposit
- Window: potentially HOURS (low-throughput chains may not fill blobs for hours)
- Across buffer: only 60 blocks = 120 seconds
- Sequencer: single centralized operator
- Rationale: These chains have the same 120s Across buffer as Optimism/Base but dramatically lower batch posting frequency. A chain posting batches once every 1-6 hours has a massive window where deposits are "unsafe" but visible to the Across dataworker. The sequencer operator of these smaller chains may have less operational maturity.
- Attack: deposit on low-volume OP Stack chain, buffer passes in 120s, dataworker reads "latest", batch not posted for hours. If sequencer goes down or fails to post, deposit vanishes.

**Estimated window: 2 minutes (buffer) to 6+ hours (batch posting)**

### Tier 2: HIGH RISK

**Base / Optimism (high-throughput OP Stack)**
- Cost: ~$0.01-$0.10 gas
- Window: ~3-10 minutes (batches post every few minutes due to volume)
- Across buffer: 60 blocks = 120 seconds
- Sequencer: Coinbase (Base) / OP Labs (Optimism) -- well-resourced operators
- Rationale: Shorter window than Tier 1 due to frequent batch posting, but still a meaningful gap between buffer and L1 finality. Sequencer centralization remains the core risk.

**Estimated window: 2-10 minutes**

**Arbitrum One**
- Cost: ~$0.01-$0.10 gas
- Window: ~4-19 minutes
- Across buffer: 240 blocks = ~60 seconds
- Rationale: Frequent batch posting (5-15 min) but single sequencer. The 260ms soft confirmation creates an asymmetry -- deposit is "confirmed" almost instantly but not L1-final for 10-20 min.

**Estimated window: 1-19 minutes**

### Tier 3: LARGE GAP but HARDER TO EXPLOIT

**Linea**
- Window: 8-32 HOURS (ZK proof time)
- Across buffer: only 120 seconds
- But: low volume, fewer valuable deposits, harder to monetize

**zkSync Era**
- Window: ~3 hours (execution delay)
- Across buffer: 120 seconds
- But: ZK proof makes invalid state impossible (only batch deletion risk)

**Scroll**
- Window: minutes to hours (proof generation)
- Across buffer: 120 seconds
- But: batch deletion is a specific mechanism that could be exploited

### Tier 4: LOWEST RISK

**Polygon PoS (post-Heimdall v2)**
- Window: NEGATIVE (5s finality < 256s buffer)
- Effectively safe under current parameters

**Ethereum Mainnet**
- Buffer: 5 blocks = 60 seconds
- True finality: 64 slots = 768 seconds
- GAP: ~12 minutes
- But: reorgs on post-Merge Ethereum are extremely rare

---

## THE CHEAPEST PATH: Low-Throughput OP Stack Chain

### Winner: Mode, Zora, Lisk, Ink, or similar low-volume OP Stack chain

**Why this is cheapest:**

1. **Lowest gas cost**: OP Stack L2 deposits cost fractions of a cent
2. **Largest controllable window**: Low transaction volume means the batcher may not post for hours
3. **Same inadequate buffer**: Across applies the same 60-block (120s) buffer to ALL OP Stack chains, regardless of their batch posting frequency
4. **Single sequencer**: Each chain has a single operator
5. **Unsafe block reorg is documented behavior**: If the sequencing window expires (12h), all unsafe blocks are reorged. This is by design, not a bug.

**Attack scenario:**

```
T+0s:    Attacker deposits on low-volume OP Stack chain (e.g., Mode, chain_id 34443)
T+2s:    Sequencer confirms deposit (unsafe block)
T+120s:  Across BUNDLE_END_BLOCK_BUFFERS passes (60 blocks)
T+120s+: Across dataworker reads deposit as valid (queries "latest")
...      Batch has NOT been posted to L1 yet (low volume = infrequent batching)
T+??:    If sequencer goes down, fails, or batch is not posted within 12h window,
         the deposit block is reorged and the deposit never existed
T+32m:   Meanwhile, Across root bundle cycle completes, slow fill executed on L1
```

**Critical insight:** The Across dataworker does not distinguish between OP Stack chains with different batch posting frequencies. A deposit on Mode (batches every few hours) gets the same 120-second buffer as a deposit on Base (batches every few minutes). This creates a structural asymmetry: the tail risk of phantom persistence is dramatically higher on low-volume chains.

### Sequencer Failure Scenario (Not Just Malicious)

The cheapest path does not require a malicious sequencer. It requires:
1. A deposit on a low-volume OP Stack chain
2. A batcher failure (software bug, infra issue, gas spike on L1 preventing batch posting)
3. The deposit being visible at "latest" during the batcher downtime
4. Across dataworker reading and including this deposit before the situation resolves

This is particularly dangerous because:
- Sequencer outages account for ~60% of all L2 incidents
- Batcher issues are a subset of sequencer issues
- The 12-hour sequencing window means unsafe blocks can persist for up to 12 hours

### Time Window Summary

| Scenario | Time Available for Phantom |
|----------|--------------------------|
| Low-volume OP Stack, normal batcher | 120s (buffer) to ~1-6h (next batch) |
| Low-volume OP Stack, batcher failure | 120s (buffer) to ~12h (sequencing window) |
| High-volume OP Stack (Base), normal | 120s to ~5-10 min |
| Arbitrum One, normal | 60s to ~5-15 min |
| Linea, normal | 120s to ~8-32h |
| zkSync Era, normal | 120s to ~3h |
| Polygon PoS (post-Heimdall v2) | SAFE (finality < buffer) |

---

## Sources

### Official Documentation
- Arbitrum: https://docs.arbitrum.io/how-arbitrum-works/deep-dives/sequencer
- Arbitrum tx lifecycle: https://docs.arbitrum.io/tx-lifecycle
- OP Stack finality: https://docs.optimism.io/op-stack/transactions/transaction-finality
- OP Stack sequencer outages: https://docs.optimism.io/stack/rollup/outages
- OP Stack batcher config: https://docs.optimism.io/builders/chain-operators/configuration/batcher
- OP Stack derivation spec: https://specs.optimism.io/protocol/derivation.html
- Polygon finality: https://docs.polygon.technology/pos/concepts/finality/finality/
- zkSync finality: https://docs.zksync.io/zk-stack/concepts/finality
- Linea tx lifecycle: https://docs.linea.build/architecture/overview/transaction-lifecycle
- Scroll: https://l2beat.com/scaling/projects/scroll

### Research / Analysis
- Jump Crypto bridging & finality: https://jumpcrypto.com/resources/bridging-and-finality-optimism-and-arbitrum
- L2BEAT finality tracking: https://medium.com/l2beat/tracking-time-to-finality-of-l2-transactions-051d32f5d5ba
- L2 ethical risk analysis: https://arxiv.org/html/2512.12732v1
- Polygon reorg history: https://mplankton.substack.com/p/polygons-block-reorg-problem
- Polygon 157-block reorg: https://protos.com/polygon-hit-by-157-block-reorg-despite-hard-fork-to-reduce-reorgs/
- Linea L2BEAT risk: https://l2beat.com/scaling/projects/linea
- Chainlink CCIP finality: https://docs.chain.link/ccip/ccip-execution-latency

### Across Protocol
- Across supported chains: https://docs.across.to/reference/supported-chains
- Across SDK: https://github.com/across-protocol/sdk
- Across relayer: https://github.com/across-protocol/relayer
- Across Constants.ts: BUNDLE_END_BLOCK_BUFFERS values extracted from source

### Incident Data
- Sequencer window expiration: https://github.com/ethereum-optimism/optimism/issues/11228
- Flow exploit Dec 2025: https://x.com/benafisch/status/2005615542498132075
- Polygon Heimdall v2: https://cryptoapis.io/blog/350-polygon-heimdall-v2-hard-fork
