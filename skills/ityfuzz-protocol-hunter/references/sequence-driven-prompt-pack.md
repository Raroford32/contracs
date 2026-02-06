# Sequence-Driven Prompt Pack (Protocol Logic Bugs)

This file is a **prompting guide** to keep the hunting process “high intelligence” and
sequence-driven. Use it with:
- `references/sequence-driven-vuln-taxonomy-2026.md` (hypothesis generator)
- `$sourcify-contract-bundler` (fetch sources/ABIs + proxy mapping + optional onchain evidence)
- `$traverse-protocol-analysis` (call graphs + storage read/write maps)
- ItyFuzz (to synthesize the actual exploit trace + PoC)

## Output contract (what to write down while working)

Always maintain 3 small artifacts (plain text / markdown):

1) **Protocol Value Model**
   - assets, shares, debts, oracles, pools/pairs, fee/reward flows
2) **Hypothesis Matrix**
   - 3-10 candidate discontinuities with explicit setup/realization sequences
3) **Campaign Log**
   - each ItyFuzz command + work_dir + what changed (targets/detectors/concolic/seed)

## Hypothesis Matrix template (copy/paste)

For each row, fill:

- ID:
- Taxonomy class (number + label):
- Target invariant / value equation:
- Where it lives (contracts, functions, storage vars):
- Boundary / discontinuity trigger:
- Setup phase (state shaping):
- Realization phase (harvest call):
- Required cross-contract set (`-t`):
- If using harness: allowed selectors:
- Evidence to prove break (pre/post deltas, events, storage):
- Expected minimal PoC assertions:
- Likely “why missed” (rare boundary, needs repetition, needs timing/order, needs caller switch):

## Sequence templates (turn ideas into fuzzable traces)

Use these templates to craft multi-step traces ItyFuzz can find.

### Template A: Shape -> Measure -> Redeem

1) Shape the measurement input (liquidity/oracle/index/caches)
2) Trigger a measurement snapshot (accrue/rebalance/settle/updateIndex)
3) Redeem/borrow/withdraw using the favorable measurement
4) Unwind shaping (sell back / repay) and check net-positive

Maps well to taxonomy items: 3, 11, 15, 16-23, 26, 28, 31-35.

### Template B: Empty boundary bootstrap

1) Force empty/near-empty state (zero supply, zero reserves, dust balances)
2) Perform the first action (first deposit / first borrow / first mint)
3) Exploit rounding/initialization/caching to inflate shares or misprice debt
4) Scale with repetition or flashloan

Maps: 5, 6, 7, 8, 9, 10, 13.

### Template C: Closed-loop positive cycle

1) Enter system A and receive receipt/share
2) Use receipt/share as input into system B (or back into A via alternate path)
3) Exit in a way that increases the original balance (net-positive)
4) Repeat until bounded by a limit (then attack the limit)

Maps: 1, 2, 3, 4, 40, 41.

### Template D: Non-atomic update interleaving

1) Trigger a partial update (global cache/index updated but per-user state not, or vice versa)
2) Interleave another action through an alternate path (hook, callback, reentrancy, external call)
3) Realize value using the inconsistent intermediate state

Maps: 24, 25, 28, 29, 30.

## Category prompts (ask these questions)

### Value/accounting discontinuities

Ask:
- Where are the *accounting totals* stored and updated?
- Are there multiple sources of “total assets / total debt / total supply” that must stay synchronized?
- Which functions write to accounting variables *after* making external calls?
- What happens at: `totalSupply == 0`, `totalAssets == 0`, `reserves == 0`, dust amounts?
- Which rounding direction is used (floor/ceil), and can it be repeated?

Convert to campaigns:
- Favor harness/offchain when you can add `invariant_*()` checks for conservation and monotonicity.
- Favor onchain when the accounting depends on real liquidity/oracles.

Evidence to collect:
- delta in (assets, shares, debt) over the trace
- exchangeRate/sharePrice before/after
- “free mint/burn” patterns (shares increase faster than assets)

### Oracle/valuation discontinuities

Ask:
- What is “truth”: spot price, TWAP, external oracle, internal AMM quote?
- Are there multiple oracles for the same asset (inconsistency)?
- Do decimals/inversion/normalization steps occur in more than one place?
- Are staleness/heartbeat/circuit-breakers enforced consistently?
- Can the attacker choose pool/path/reference (router input, poolId, oracle address)?

Convert to campaigns:
- Onchain + `-f` often best (real pools).
- Multi-target: include the pool/pair/router/oracle addresses, not just the protocol.

Evidence:
- show manipulated reference value and downstream eligibility/cap/limit decisions

### Sequencing/state machine discontinuities

Ask:
- Where are snapshots taken (solvency check, share conversion, debt accrual)?
- Are state transitions split across multiple calls/transactions/epochs?
- Are hooks/callbacks used as “authenticated context”?
- Are there alternate entrypoints that skip a state transition?

Convert to campaigns:
- Harness mode shines: restrict selectors to the state-machine entrypoints and add invariants that must hold across phases.
- Use `--concolic --concolic-caller` when reaching a gated state requires a specific caller or hidden condition.

Evidence:
- show state machine entering an invalid state (or skipping required steps)

### MEV / microstructure discontinuities (model as sequences)

ItyFuzz is not a mempool simulator, but you can still model MEV-style logic breaks as:
- attacker bracketing swaps within a flashloan-funded sequence, and/or
- multi-tx attacker sequences on a fork.

Ask:
- Is there a rebalance/settle/auction step that assumes “fair price” at execution time?
- Are there slippage margins that can be harvested by pre-shaping liquidity?

Convert:
- Include (router/pair/token) in `-t` and enable `-f`.

### Composability / programmability discontinuities

Ask:
- What “flexibility knobs” are attacker-controlled? (router calldata, module address, poolId, strategy params)
- Are approvals long-lived and reusable across contexts?
- Does receipt-token transferability create repeated side effects?

Convert:
- Expand the target set to include module/adapter contracts.
- Consider adding `typed_bug("...")` markers at “should never happen” internal branches if you can modify source.

### Cross-domain/chain-specific discontinuities

Ask:
- Is there chain-specific behavior (precompiles, L2 semantics, unusual gas/refund, native token handling)?
- Are message paths domain-separated (replay resistance)?

Convert:
- Prefer onchain campaigns on the relevant chain fork.
- Use explicit `--spec-id` if the EVM version matters.

