# Memory (bridge-finality-gap)

## Pinned Reality
- chain_id: 1 (Ethereum Mainnet; targets span L1↔L2 boundary)
- fork_block: 24539674 (pinned 2026-02-26)
- discriminator_block: ~24553401 (live 2026-02-28)
- attacker_tier: sequencer-level OR DA-DoS capable
- capital_model: <$0.10 L2 gas for deposit + $100K+ for DA DoS (if needed)

## Contract Map Summary
**Across Protocol (PRIMARY TARGET):**
- HubPool: 0xc186fA914353c44b2E33eBE05f21846F1048bEda — $12M WETH + $2M USDC
- SpokePool ETH: 0x5c7BCd6E7De5423a257D81B442095A1a6ced35C5 — 21 WETH + $151K USDC
- ABT: 0xee1dc6bcf1ee967a350e9ac6caaaa236109002ea (ABT≠WETH)

**Celer cBridge V2:** $3.38M total. HC-3 capped at epoch boundary, no signer-voter overlap.
**Synapse/Hop:** deprioritized (well-designed)

## HC-1: Across Layered Defense Collapse — COMPLETE ANALYSIS

**ALL 5 ON-CHAIN/OFF-CHAIN VECTORS CONFIRMED. EVERY ALTERNATIVE PATH INVESTIGATED.**

### Confirmed vectors:
| V# | Vector | Evidence |
|----|--------|----------|
| V1 | requestSlowFill permissionless | Fabricated hash → Unfilled(0), no auth gate |
| V2 | Dataworker "latest" block tag | `provider.getBlockNumber()` = latest; buffer ETH=5, OP=60 |
| V3 | Single automated proposer | 0xf7bac63f EOA, 19,645+ bundles |
| V4 | Zero disputes | No dispute events ever |
| V5 | amountToReturn gap | SpokePool.sol line 1406 |

### Investigated + closed paths:
- Pure fabrication (no real deposit): BLOCKED by 13-field dataworker cross-check
- Fast fill + slow fill double-pay: BLOCKED at line 1594 (fillStatuses)
- fillDeadline expiry during liveness: BLOCKED at line 1570
- Deposit refund double-spend: BLOCKED by same-pipeline mutual exclusion
- HC-2 speed-up replay: BLOCKED by 3 independent defenses
- HC-3 Celer cascade: WEAKENED by 0 signer-voter overlap

### Remaining viable path: L2 finality gap exploitation
- Low-volume OP Stack chains: 120s buffer vs hours between batch posts
- Deposit exists at "latest" but has no L1 backing for hours
- If batcher fails/reorgs → phantom deposit → drain
- See notes/l2-finality-analysis.md for per-chain analysis

### Status: DESIGN RISK — sub-E3 at permissionless tier
- Can't reliably CAUSE batcher failure without infrastructure access
- Organic batcher failures DO happen but are unpredictable
- DA DoS attack (Sep 2025 disclosure) costs $100K+ post-patch
- If batcher failure coincides with deposit → $12M+ drain

## Coverage Status
- notes/entrypoints.md, control-plane.md, taint-map.md, tokens.md
- notes/feasibility.md, message-path.md, value-flows.md, assumptions.md
- notes/hypotheses.md + composition-hypotheses.md
- notes/onchain-contract-analysis.md
- notes/l2-finality-analysis.md
- scripts/onchain_discriminators.py

## Solvency Equation
sum(SpokePool_balances) + HubPool_liquidReserves >= sum(pending_fills) + sum(pending_refunds)
Violated when: phantom slow fills extract real tokens for non-existent deposits

## Last Experiment
- Deep investigation of ALL remaining paths to E3
- evidence: composition-hypotheses.md (deep investigation section), l2-finality-analysis.md
- result: All pure on-chain paths BLOCKED. L2 finality gap is the ONLY remaining vector.
- belief change: HC-1 is a confirmed design risk but NOT immediately actionable without infrastructure compromise or organic batcher failure

## Next Discriminator
- Measure actual batch posting frequency on Mode/Zora/Lisk via L1 BatchInbox
- If batches are hours apart → confirms multi-hour exploitation window exists organically
- Fork Mode, create deposit, wait past buffer, verify dataworker reads it
