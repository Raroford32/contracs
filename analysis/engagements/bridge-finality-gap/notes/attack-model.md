# Concrete Attack Model: Across Slow Fill Phantom Injection

## Attack Vector Classification
- **Type**: Finality Gap + Off-chain Agent Trust Boundary
- **Target**: Across Protocol Slow Fill Pipeline
- **Chain**: L2 (Arbitrum/Base/Optimism) → L1 (Ethereum)
- **Attacker Tier**: Sequencer-level (on centralized-sequencer L2) OR RPC-eclipse capable

## Full Attack Chain (Step-by-Step)

### Phase 0: Prerequisites
- Attacker needs: ~$50 in gas (L2 deposit + L1 requestSlowFill)
- Attacker needs: RPC eclipse capability OR sequencer access on one L2
- NO flash loans needed, NO capital needed beyond gas

### Phase 1: Create Phantom Deposit on L2
**Target L2**: Arbitrum (centralized sequencer)
**Action**: Create a deposit via `depositV3()` on the L2 SpokePool

The deposit must:
- `originChainId`: 42161 (Arbitrum)
- `destinationChainId`: 1 (Ethereum)
- `inputToken`: WETH on Arbitrum
- `outputToken`: WETH on Ethereum (0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2)
- `inputAmount`: e.g., 75 WETH (maximum extractable from SpokePool)
- `outputAmount`: 74.5 WETH (with small fee)
- `recipient`: attacker-controlled address
- `fillDeadline`: current_time + 3600

**Critical**: This deposit exists in a block that will later be **reorged**.

Sequencer attack: The sequencer posts a batch that includes this deposit, but
the batch is later invalidated (sequencer fault/reorg/reorganization).

RPC eclipse: The deposit exists in a "ghost block" that the attacker's
controlled RPC node serves to the dataworker.

### Phase 2: Trigger requestSlowFill on L1
**Target**: Across SpokePool Ethereum (0x5c7BCd6E7De5423a257D81B442095A1a6ced35C5)
**Function**: `requestSlowFill(V3RelayData calldata relayData)` [line 1076]

This function:
1. Checks `fillDeadline > block.timestamp` ✓ (deadline in future)
2. Checks `exclusivityDeadline < block.timestamp` ✓ (no exclusivity)
3. Checks `fillStatuses[relayHash] == Unfilled` ✓ (never used before)
4. Sets `fillStatuses[relayHash] = RequestedSlowFill`
5. Emits `RequestedSlowFill` event

**DOES NOT**:
- Verify deposit exists on origin chain
- Verify deposit was finalized on origin chain
- Verify any cross-chain proof
- Check any origin chain state

**Cost**: Gas only (~50K gas = ~$5-10)

### Phase 3: Dataworker Reads RequestedSlowFill Event
**Actor**: Across dataworker (off-chain bot)
**Action**: Reads `RequestedSlowFill` events from L1 SpokePool

The dataworker must:
1. Read the RequestedSlowFill event from L1
2. Look up the corresponding deposit on the origin L2
3. If the deposit exists AND matches, include it in the slow fill root

**KEY QUESTION**: What block tag does the dataworker use when querying L2?
- If "latest": phantom deposit visible in unfinalized L2 blocks → included
- If "finalized": phantom deposit filtered out (L2 finality = 7+ days on Arbitrum)

### Phase 4: Root Bundle Proposal (if phantom passes dataworker)
**Actor**: Across dataworker (or any proposer — permissionless)
**Target**: HubPool (0xc186fA914353c44b2E33eBE05f21846F1048bEda)
**Function**: `proposeRootBundle()` [line 566]

Proposes merkle roots including:
- `slowRelayRoot`: contains the phantom slow fill leaf
- `poolRebalanceRoot`: includes rebalancing for phantom fill
- Bond: 0.45 ABT staked

### Phase 5: Liveness Window (30 minutes)
**Defense**: UMA OO dispute mechanism
- Anyone can call `disputeRootBundle()` within 30 minutes
- **Observation**: Zero disputes in observed window → dormant mechanism
- Dispute requires: detecting phantom, obtaining ABT bond, calling dispute

### Phase 6: Root Execution (if no dispute)
**Actor**: Anyone (permissionless after liveness)
**Target**: HubPool
**Function**: `executeRootBundle()` [line 618]

This:
1. Checks `getCurrentTime() > challengePeriodEndTimestamp` ✓
2. Verifies merkle proof against poolRebalanceRoot ✓
3. Sends tokens to SpokePool via cross-chain adapter
4. Relays `relayRootBundle(relayerRefundRoot, slowRelayRoot)` to L1 SpokePool

### Phase 7: Slow Fill Execution
**Actor**: Anyone (permissionless)
**Target**: SpokePool Ethereum
**Function**: `executeSlowRelayLeaf()` [line 1159]

This:
1. Verifies merkle proof against slowRelayRoot ✓ (valid proof from posted root)
2. Checks `fillStatuses[relayHash]` is not Filled ✓
3. Sets `fillStatuses[relayHash] = Filled`
4. Calls `_fillRelayV3()` → `_transferTokensToRecipient()`
5. **Line 1666**: `IERC20(outputToken).safeTransfer(recipientToSend, amountToSend)`
   - Sends funds from SpokePool balance directly to attacker's recipient

## Value Extraction
- **SpokePool ETH balance**: ~$380K (75 WETH + $79K USDC + $111K USDT)
- **Per phantom deposit**: up to 75 WETH per token type
- **Repeatable**: Yes, once per root bundle cycle (~32 min)
- **Total extractable**: bounded by SpokePool balance per token

## Cost Model
- Gas: ~$50 total (L2 deposit + L1 requestSlowFill + executeSlowRelayLeaf)
- ABT Bond: NOT needed if using legitimate dataworker (phantom enters pipeline naturally)
  - OR: 0.45 ABT if attacker self-proposes root bundle
- **Net profit if successful**: ~$380K - $50 = ~$379,950

## Defense Analysis
1. **requestSlowFill validation**: NONE (permissionless, no origin check)
2. **Dataworker validation**: DEPENDS ON BLOCK TAG (key open question)
3. **UMA OO dispute**: 30 min window, ZERO disputes observed, may be dormant
4. **SpokePool balance**: Limited pool drains to current balance

## Attack Variants

### Variant A: RPC Eclipse on Dataworker
- Target the specific RPC endpoint the dataworker uses for L2 queries
- Serve phantom L2 blocks containing the fake deposit
- Dataworker includes phantom in root bundle naturally
- No need for attacker to propose bundle or obtain ABT

### Variant B: Self-Proposal with Custom Root
- Attacker obtains ABT (if traded on DEX)
- Constructs malicious merkle roots including phantom slow fill leaf
- Calls proposeRootBundle() directly
- Waits 30 min liveness
- Executes root bundle and slow fill

### Variant C: Sequencer Manipulation
- On centralized-sequencer L2 (Arbitrum, Base, Optimism)
- Sequencer includes phantom deposit in batch
- Dataworker reads batch, includes in root bundle
- Sequencer later reorgs/drops the batch
- Deposit is phantom but slow fill already in pipeline

## Critical Dependencies (Must Verify)
1. ✅ requestSlowFill accepts fabricated data (confirmed from code)
2. ❓ Dataworker block tag (pending — agent researching)
3. ❓ ABT token obtainability (pending — agent researching)
4. ❓ Dispute bot activity level (pending — agent researching)
5. ❓ Exact RPC infrastructure used by dataworker (affects RPC eclipse feasibility)

## Discriminators Needed
- D1: Does dataworker use "finalized" for L2 queries? → If yes, FALSIFIES H1
- D2: Is ABT traded on any DEX? → Determines Variant B feasibility
- D3: Are there active dispute bots? → Determines liveness window safety
- D4: What RPC endpoints does the dataworker use? → Determines Variant A feasibility
