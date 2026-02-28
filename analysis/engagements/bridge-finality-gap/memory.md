# Memory (bridge-finality-gap)

## Pinned Reality
- chain_id: 1 (Ethereum Mainnet; targets span L1↔L2 boundary)
- fork_block: 24539674 (pinned from live RPC query 2026-02-26)
- discriminator_block: ~24553401 (live RPC query 2026-02-28)
- attacker_tier: sequencer-level OR RPC-eclipse capable
- capital_model: minimal (gas only ~$50; no flash loans needed)

## Contract Map Summary
**Across Protocol (PRIMARY TARGET):**
- HubPool: 0xc186fA914353c44b2E33eBE05f21846F1048bEda (NOT upgradeable)
  - Owner: 3/5 Gnosis Safe, Liveness: 1800s, Bond: 0.45 ABT
  - WETH reserves: liquid=2,432 + utilized=3,638 = 6,068 WETH (~$12M)
  - USDC reserves: liquid=1.32M + utilized=720K = $2.04M
- SpokePool ETH: 0x5c7BCd6E7De5423a257D81B442095A1a6ced35C5 (UUPS)
  - Balances: 21 WETH + $151K USDC
- ABT: 0xee1dc6bcf1ee967a350e9ac6caaaa236109002ea (WETH9 + proposer whitelist, ABT≠WETH)

**Celer cBridge V2:** 0x5427FEFA711Eff984124bfBB1AB6fbf5E3DA1820
- 17 stake-weighted signers, Governor SEPARATE from Owner, Owner SEPARATE from signers
- Owner: 0xF380166F (governance contract, 6 voters, 60% threshold, 0 signer overlap)
- Pool: USDC=$1.478M, USDT=$1.687M, WETH=218 (total ~$3.38M)

## HC-1: Across Layered Defense Collapse — ALL 5 VECTORS CONFIRMED

**This is the primary finding. All vectors confirmed, sub-E3 only because infrastructure tier required.**

| # | Vector | Status | Evidence |
|---|--------|--------|----------|
| V1 | requestSlowFill permissionless | CONFIRMED | D1: fabricated hash → Unfilled(0) |
| V2 | Dataworker "latest" block tag (5-block buffer << 64-slot finality) | CONFIRMED | SDK: `provider.getBlockNumber()` = latest; Constants: ETH=5 |
| V3 | Single automated proposer | CONFIRMED | proposer=0xf7bac63f (EOA), 19,645+ bundles |
| V4 | Zero disputes ever | CONFIRMED | no dispute events in history |
| V5 | amountToReturn not in balance check | CONFIRMED | SpokePool.sol line 1406 |

**Kill chain:** phantom L2 deposit → requestSlowFill → dataworker reads "latest" → automated proposal → no dispute → executeSlowRelayLeaf → drain
**Impact:** Up to 6,068 WETH (~$12M) + $2M USDC per drain cycle (bounded by HubPool reserves)

## Falsified Hypotheses

**HC-2 (Speed-Up Replay): DEAD — blocked by 3 independent defenses**
1. SpokePoolClient: `deposit.depositor.eq(speedUp.depositor)` check
2. Dataworker: `buildV3SlowFillLeaf` ignores speed-up data entirely
3. On-chain: `executeSlowRelayLeaf` hardcodes `updatedRecipient=relayData.recipient`

**HC-3 (Celer Signer Cascade): WEAKENED — no signer-voter overlap**
- 17 signers vs 6 governance voters = ZERO overlap
- Without governor: max $3.38M at epoch boundary (requires 2/3 signer compromise)
- Full drain requires 2/3 signers + 4/5 governance voters = 2 independent compromises

**HC-4, HC-5: DEAD** — intended behavior / off-chain mitigated

## Coverage Status
- entrypoints: notes/entrypoints.md
- control plane: notes/control-plane.md
- taint map: notes/taint-map.md
- tokens: notes/tokens.md
- feasibility: notes/feasibility.md
- message path: notes/message-path.md
- value flows: notes/value-flows.md
- assumptions: notes/assumptions.md
- hypotheses: notes/hypotheses.md + notes/composition-hypotheses.md
- on-chain analysis: notes/onchain-contract-analysis.md
- discriminator script: scripts/onchain_discriminators.py

## Solvency Equation
Across: sum(SpokePool_balances) + HubPool_liquidReserves >= sum(pending_fills) + sum(pending_refunds)
Violated when: phantom slow fills extract real tokens for non-existent deposits

## Last Experiment
- command: Off-chain code review of Across SDK + relayer dataworker source
- evidence: notes/composition-hypotheses.md (off-chain discriminator section)
- result: V2 CONFIRMED (provider.getBlockNumber() = "latest"), HC-2 FALSIFIED (3 defenses), HC-3 WEAKENED (0 overlap)
- belief change: HC-1 is architecturally complete — ALL 5 vectors confirmed. Only infrastructure tier (L2 reorg/sequencer) prevents E3.

## Next Discriminator
- Question: Can phantom deposit propagation be demonstrated on a fork with actual dataworker logic?
- Design: Fork L2, create deposit in unfinalized block, run dataworker read pipeline
- Expected falsifier: If dataworker has additional finality checks not visible in base client code
- Alternative: Analyze L2-specific finality gaps (which L2 has cheapest reorg/sequencer path?)
