---
name: ityfuzz-protocol-hunter
description: "Deep smart-contract fuzzing and exploit-sequence generation with ItyFuzz for EVM protocols (onchain forks from deployed addresses, offchain fuzzing from .abi/.bin or build commands, Foundry-style setup/invariant harnesses, detector/oracle tuning, replay/corpus triage, and Foundry PoC generation). Use when you need to hunt complex cross-contract chaining sequences, flashloan/price manipulation paths, reentrancy, fund-loss bugs, or deep protocol logic invariant violations in a protocol."
---

# ItyFuzz Protocol Hunter

## Overview

Use ItyFuzz to turn a protocol (onchain or local) into **reviewable, reproducible artifacts**:
- minimized exploit traces (replayable inputs)
- generated Foundry PoCs (`work_dir/vulnerabilities/*.t.sol`)
- evidence logs (`vuln_info.jsonl`, optional `relations.log`)

Hard rule: **do not guess CLI flags**. Always consult `references/cli-ityfuzz-evm-help.txt` and/or run `ityfuzz evm --help` in the target environment.

## Operating principles (2026, sequence-driven)

- Treat fuzzing as an **agentic loop**, not a one-shot command.
- Optimize for **multi-step, cross-contract sequences** (setup phase -> realization phase).
- Use ItyFuzz outputs as *evidence*, then widen/narrow the search based on what the evidence says.
- Reuse context from other skills when available:
  - `$sourcify-contract-bundler` for source/ABI/proxy mapping and onchain evidence
  - `$traverse-protocol-analysis` for call graphs + storage access maps (choose entrypoints/invariants)
  - `$tenderly-protocol-lab` for evidence-grade decoded traces/simulations (cheapest discriminators + E3 proof artifacts)
  - If available, prefer SQD evidence (logs/txs/traces/state diffs) to anchor fork blocks and prove value deltas.

## Sequence-driven hunt loop (prompting guide)

When the user asks to “find deep/novel protocol bugs”, follow this loop and keep outputs explicit.

### Loop 0: Build a protocol value model (before running ItyFuzz)

Produce (as text artifacts) the following:
- **Asset graph**: underlying assets, receipt/share tokens, debt tokens, reward tokens, oracles, AMM pairs.
- **Value equations** (the protocol *thinks* are true): totalAssets, totalSupply, exchangeRate, debt, collateral.
- **State machine gates**: epochs, cooldowns, delayed withdrawals, snapshots, hooks/callbacks, keeper-only steps.
- **External truth dependencies**: price feeds, TWAP windows, pool choice, decimals, inversion, staleness rules.

If you already ran `$traverse-protocol-analysis`, mine:
- storage writes (accounting vars, caches, indices) and
- reachable call chains around settlement/rebalance/liquidation.

### Loop 1: Generate hypotheses from the 2026 taxonomy

Read `references/sequence-driven-vuln-taxonomy-2026.md` and generate a **Hypothesis Matrix**.
For each hypothesis, fill:
- **Class**: one of the numbered taxonomy items
- **Invariant to break**: conservation/monotonicity/solvency/exchange-rate/TWAP sanity
- **Setup phase**: what state needs to be shaped (liquidity, oracle, debt, caches, approvals)
- **Realization phase**: the “harvest” call that crystallizes profit / breaks solvency
- **Minimal cross-contract set**: which contracts must be in the target set (`-t` multi-target)
- **Entry points**: candidate functions/selectors to allow (if using a harness)
- **Why fuzz might miss it**: rare boundary, requires repetition, needs specific caller, needs timing/order
- **Evidence to collect**: which events/storage deltas prove the break (and what a PoC must assert)

Then pick the top 3-10 hypotheses by:
- impact (fund-loss / solvency / share-price inflation),
- realism (permissionless), and
- “sequence depth” (needs >2 calls / cross-contract / boundary).

### Loop 2: Turn hypotheses into ItyFuzz campaigns (don’t over-constrain)

Pick the least constraining mode that still reproduces reality:

1) **Onchain fork (address mode)** for “real protocol in real state”:
   - multi-target addresses
   - fixed exploit window block
   - optional flashloan
2) **Offchain glob mode** for fast iteration when you can deploy dependencies.
3) **Foundry harness (setup mode)** only when you need:
   - complex initialization,
   - selector targeting (to keep search on the intended state machine),
   - custom invariants (`invariant_*()`).

Avoid prematurely writing bespoke configs unless forced.

### Loop 3: Escalate search power based on evidence

Escalate in this order:
- Add `-f/--flashloan` for DeFi sequences.
- Add concolic (`--concolic --concolic-caller`) when conditions/timing gates block progress.
- Widen detectors (`--detectors ...`) when the bug is not “fund extraction” shaped.
- Run longer (`--run-forever`, vary `--seed`) once you have the right target set and the fuzzer is exploring the right call surface.

### Loop 4: Convert found traces into an auditor-grade deliverable

For each bug:
- Replay the minimized trace (`*_replayable`) and confirm determinism.
- Use the generated `.t.sol` as a base and add:
  - explicit assertions for the broken invariant, and
  - pre/post balance/value deltas that prove net-positive.
- Document the hypothesis class it matches and the smallest code-level root cause.

## Quick start

### 1) Onchain fuzzing (forked chain)

```bash
# Minimal onchain campaign (address mode)
ityfuzz evm \
  -t 0xTarget1,0xTarget2 \
  -c bsc -b 23695904 \
  -f \
  -k "$BSC_ETHERSCAN_API_KEY" \
  -w analysis/ityfuzz/onchain-run
```

### 2) Offchain fuzzing (local build artifacts)

```bash
# Requires *.abi + *.bin in ./build/
ityfuzz evm \
  -t './build/*' \
  --detectors high_confidence \
  -w analysis/ityfuzz/offchain-run
```

### 3) Foundry setup/invariant harness (deep protocol logic)

```bash
# Build the project via Foundry and deploy an ItyFuzz harness contract.
# The harness contract must implement setUp() + targetContracts/targetSelectors/etc.
ityfuzz evm \
  -m test/ItyFuzzHarness.sol:ItyFuzzHarness \
  -f \
  -w analysis/ityfuzz/foundry-harness \
  -- forge test
```

See `references/foundry-setup-harness.md` and `assets/ItyFuzzHarness.sol`.

## Workflow (maximum-coverage protocol hunting)

### 1) Collect inputs (ask before running)

Collect:
- **Mode**: onchain addresses vs offchain artifacts vs Foundry harness.
- **Chain + fork point** (onchain): `-c/--chain-type` and `-b/--onchain-block-number`.
- **Targets**:
  - onchain: comma-separated addresses for `-t`
  - offchain: a glob for `-t` (e.g. `./build/*`)
  - foundry/setup: `-m file.sol:ContractName`
- **RPC**:
  - set `ETH_RPC_URL` for performance/stability (archive RPC recommended for backtests)
- **Explorer key** (optional but recommended):
  - `-k/--onchain-etherscan-api-key` or `ETHERSCAN_API_KEY` env var
- **Goal**:
  - “find fund-loss exploit” (detectors + flashloan)
  - “find deep logic bug” (invariants + selector targeting)
  - “cross-contract sequence” (multi-target + harness)

If the user provides only a single core address, proactively request the likely dependency set (tokens/pairs/routers/oracles/proxies).

### 2) Choose target type (do not wing it)

Use `references/target-types-and-modes.md` to decide between:
- `glob` (offchain artifacts)
- `address` (onchain fork)
- `setup` (Foundry harness; complex initialization + selector targeting)
- `config` (advanced fixed-address + ABI-encoded constructor args)
- `anvil_fork` (onchain + build artifacts mapping)

### 3) Preflight (make runs reproducible)

Do:
- Confirm binary and flags:
  - run `ityfuzz --help` and `ityfuzz evm --help`
  - compare to `references/cli-ityfuzz-evm-help.txt` if needed
- Set a unique work dir per campaign:
  - `-w analysis/ityfuzz/<campaign-name>`
- Capture environment:
  - record `ETH_RPC_URL`, explorer keys, chain/block, and exact command (manifest)
- Prefer the wrapper for deterministic logging:

```bash
python skills/ityfuzz-protocol-hunter/scripts/ityfuzz_run_evm.py \
  -w analysis/ityfuzz/campaign-1 -- \
  <PASTE YOUR ityfuzz evm FLAGS HERE>
```

### 4) Build a “maximum complexity” target set (cross-contract sequences)

Onchain mode:
- Use multi-target `-t addr1,addr2,...` (see `official-tutorials-exp-known-working-hacks.md`).
- Include:
  - core protocol contract(s)
  - pool/pair contracts (AMMs)
  - key tokens (e.g., stablecoin + wrapped native)
  - routers/oracles/fee collectors/registries if the exploit touches them
- For proxy-heavy protocols:
  - add both proxy and implementation addresses if known
  - stabilize ABIs with `--force-abi address:path/to/abi.json` when decompilation is noisy

Offchain mode:
- Deploy *all* needed dependencies; offchain fuzzing starts from a clean chain.
- If constructor args matter, use:
  - `--constructor-args "Contract:arg1,arg2;Other:arg1;..."` (see `official-docs-evm-contract-constructor-for-offchain-fuzzing.md`)
  - or the `--fetch-tx-data` proxy-forwarding method for “deploy then fuzz” workflows.

Optional (recommended) mapping phase:
- Use `$sourcify-contract-bundler` to fetch sources/ABIs + proxy mappings for the protocol.
- Use `$traverse-protocol-analysis` to generate call graphs + storage access maps.
- Use those artifacts to pick:
  - high-impact entrypoints (writes + external calls)
  - invariant surfaces (accounting totals, share price, debt, reserves, oracle reads)

### 5) Encode deep protocol logic bugs (detectors + invariants)

Detectors:
- Start with `--detectors high_confidence` (default) and `-f` for DeFi.
- For custom mixes and invariant-heavy fuzzing, see `references/detectors-and-oracles.md`.

Invariants (offchain + harness mode is best):
- Add no-arg functions:
  - `invariant_*()` (ItyFuzz reports a bug when the call reverts)
  - `echidna_*()` (ItyFuzz reports a bug when returns false / reverts)
- Use `bug()` / `typed_bug(string)` markers (see `official-docs-evm-contract-writing-invariants.md`).
- Use Scribble by compiling with `scribble ... --no-assert` and fuzzing the compiled output (see the same doc).

### 6) Run campaigns in escalating passes

Pass A: baseline (fast)
- Onchain:
  - `-c/-b -k -f --detectors high_confidence`
- Offchain:
  - `-t './build/*' --detectors high_confidence`

Pass B: unlock hard conditions (concolic)
- Add:
  - `--concolic --concolic-caller`
  - optionally tune `--concolic-timeout` / `--concolic-num-threads`

Pass C: widen detector surface
- If default profile is too narrow, explicitly set `--detectors` (see reference).

Pass D: long-run bug harvest
- Add:
  - `--run-forever`
  - vary `--seed` across runs for diversity
  - enable `--write-relationship` to keep `relations.log`

### 7) Triage, replay, and produce evidence

Always check:
- `work_dir/vuln_info.jsonl` (machine-readable oracle outputs)
- `work_dir/vulnerabilities/*.t.sol` (Foundry PoCs)
- `work_dir/vulnerabilities/*_replayable` (replayable minimized traces)

Summarize a run:
```bash
python skills/ityfuzz-protocol-hunter/scripts/ityfuzz_summarize_workdir.py analysis/ityfuzz/campaign-1
```

Replay a minimized trace:
- use `--replay-file` with the `_replayable` file glob (see `references/replay-and-corpus.md`).

### 8) Output (what to deliver)

Deliver:
- Exact run command (including chain/block/targets) + env requirements (`ETH_RPC_URL`, explorer key).
- The `work_dir/` (or at minimum: `vuln_info.jsonl`, `vulnerabilities/*.t.sol`, `_replayable` traces, `stdout.log`, `stderr.log`).
- A Foundry PoC test and minimal explanation of the exploited invariant / accounting break.

## Scripts

- `scripts/ityfuzz_run_evm.py`: run `ityfuzz evm` with a manifest + stdout/stderr logs.
- `scripts/ityfuzz_summarize_workdir.py`: summarize `vuln_info.jsonl` + generated PoCs.

## References

- `references/ityfuzz-docs-index.md`: map of all vendored official docs + source-derived notes.
- `references/cli-ityfuzz-evm-help.txt`: authoritative EVM CLI flags and defaults.
- `references/sequence-driven-vuln-taxonomy-2026.md`: hypothesis generator for deep, multi-step bugs.
- `references/sequence-driven-prompt-pack.md`: advanced prompting guide for sequence-driven bug hunting.
- `references/target-types-and-modes.md`: pick the correct target type.
- `references/detectors-and-oracles.md`: `--detectors` values and selection guidance.
- `references/foundry-setup-harness.md`: write a harness for `--deployment-script`.
- `references/offchain-config-schema.md`: JSON schema for `--offchain-config-file/url`.
- `references/replay-and-corpus.md`: work dir layout + replay/resume workflows.
