# CLAUDE.md — Autonomous Counterexample Discovery for Smart Contract Systems
*(Composition‑first • solver‑driven • evidence‑only • **authorized testing only**)*

This document is a **build spec** for an agent system that discovers **multi‑step counterexamples** in EVM‑compatible smart contract systems.

The target reality is **heavily‑audited, high‑TVL, high‑composition protocols**, where failures are rarely “one bad function” and are more often:

- **kernel contradiction**: a subtle property discontinuity (rounding drift, accounting divergence, stale derived state, non‑commutativity),
- **precondition machine**: a complex sequence that reaches the one cursed state where the kernel flips sign,
- **solver requirement**: the exploitability boundary is numeric/temporal and must be *solved*, not guessed.

The system does **not** “prove safety.” It produces **minimal, executable reproductions** of violated properties in a sandbox.

> **Hard ethics gate:** This spec is for **authorized security testing and responsible disclosure** only.  
> Do not use it to target systems you do not have permission to test.

---

## 1) The only loop that scales: reason → solve → evidence → updated reason

In modern protocols, “smart reasoning” without solving is theater; “brute solving” without evidence is an expensive random walk.

This system enforces a scientific loop:

1. **Reasoning** outputs a *solvable object*  
   → a **ContradictionSpec** (variables, constraints, objective, instrumentation).

2. **Solving** searches for satisfying assignments  
   → sequences, parameters, time offsets, actor choices.

3. **Evidence** is compiled deterministically  
   → traces, state diffs, invariant deltas, sensitivity signals.

4. **Updated reasoning** consumes evidence  
   → refines specs, discovers macros, focuses search.

Everything else is vibes.

---

## 2) Non‑negotiables (hard gates)


### Gate B — Sandbox execution only
- All execution happens on a **local fork** / testnet / controlled environment.
- No live‑market interaction, no mempool games, no production private keys.

### Gate C — Evidence‑only findings
A “finding” is accepted only if it has:
- deterministic reproduction script/test,
- traces + state diffs,
- a minimized sequence (shrunk),
- a named violated property with a checkable predicate.

### Gate D — Composition‑first (complexity is default)
- The search prioritizes **multi‑function, multi‑contract, multi‑actor** sequences.
- Depth‑1 checks are treated as **degenerate** and never considered “done.”

### Gate E — Solver‑driven, not label‑driven
- No “reentrancy/oracle/arbitrage” labels as an objective.
- Objective is always: **maximize a property violation** under constraints.

### Gate F — Coverage transparency
Every report must include what was modeled, what wasn’t, and numeric coverage metrics (§12).

---

## 3) Threat model (explicit so the agent doesn’t hallucinate powers)

Default adversary model (customizable per ScopeSpec):

- **Unprivileged external actors** (EOA-like identities) with distinct balances.
- Can call any `public/external` function in scope.
- Can interact with external dependencies **only if included** in scope (e.g., a DEX used by the system).
- Can choose call ordering within a sequence and can span multiple blocks (within configured horizon).
- Cannot assume privileged roles, governance powers, or operator keys unless explicitly included.

---

## 4) Definitions (the minimal shared language)

**Action**  
A single sandbox interaction primitive:
- actor identity,
- target contract,
- function + arguments,
- msg.value (if any),
- block/time context.

**Sequence**  
An ordered list of Actions, possibly across blocks.

**Mode**  
A qualitative regime that changes behavior (e.g., supply=0 vs supply>0; empty pool; bootstrap; accrued vs not).

**Assumption**  
A condition a component implicitly relies on (often not checked).

**Invariant**  
A property that should hold across reachable states (global or mode‑scoped).

**Kernel contradiction**  
A small discontinuity in a property (often numeric) that can be amplified.

**Precondition machine**  
The multi‑step setup required to reach the kernel’s enabling state.

**ContradictionSpec**  
The contract between “reasoning” and “solving.” It must be machine‑readable.

---

## 5) Inputs / outputs (the repo’s public API)

### 5.1 ScopeSpec (required)
A run starts with `ScopeSpec`:

```json
{
  "chain": "evm-compatible",
  "fork": {
    "rpc_url": "${RPC_URL}",
    "block_number": 0
  },
  "targets": {
    "contracts": ["0x..."]
  },
  "dependencies": {
    "in_scope_contracts": ["0x..."],
    "out_of_scope_assumptions": ["oracle is honest", "dex behaves per interface"]
  },
  "assets": {
    "erc20": ["0x..."]
  },
  "adversary": {
    "actors": 3,
    "capital_limits": { "native": "0", "erc20": {} },
    "time_horizon_blocks": 500,
    "max_sequence_depth": 14
  },
  "constraints": {
    "no_out_of_scope_calls": true,
    "no_privileged_roles": true
  }
}
```

**Do not hardcode RPC keys** in this repo. Inject via environment.

### 5.2 FindingReport (required for any accepted hit)

```json
{
  "id": "FINDING-0001",
  "property_violated": "P-ACCOUNTING-CONSERVATION-01",
  "minimal_repro": {
    "sequence": ["A1", "A2", "A3"],
    "params": {"a1": "…"},
    "environment": {"block_number": 0}
  },
  "evidence": {
    "trace_refs": ["trace.json"],
    "state_diffs": ["diff.json"],
    "feature_vector": ["features.json"]
  },
  "impact": {
    "type": "property_violation",
    "notes": "Sandbox only. Real-world impact requires human review."
  },
  "mitigations": ["..."],
  "coverage": {
    "depth_max": 14,
    "modes_reached": ["supply=0", "supply>0"],
    "edges_hit": 431,
    "edges_total": 900
  },
  "limitations": ["..."]
}
```

---

## 6) World modeling (build a search space that matches reality)

### 6.1 Call‑Effect Graph (CEG)
For each target function `F`, build a deterministic effect summary:

- **reads/writes** (storage locations, mappings, packed vars),
- **external calls** (targets, value, callback surface),
- **asset movements** (ERC‑20 transfers, mint/burn, approvals),
- **dependency reads** (rates, prices, timestamps, accumulators),
- **permission gates** (requires/modifiers, state‑gated roles),
- **derived state** (cached indices, exchange rates, share price),
- **implicit assumptions** (what must be true for safe behavior).

Conceptual node:

```
CEG_NODE(F):
  reads: [...]
  writes: [...]
  external_calls: [...]
  assets: {in: [...], out: [...]}
  gates: [...]
  derived_state: [...]
  assumptions: [...]
```

### 6.2 Mode discovery (boundary states are first-class)
Infer mode predicates such as:
- supply == 0
- totalAssets == 0
- reserve == 0
- accruedIndex stale vs fresh
- paused flag
- liquidation threshold boundary
- “first time” flags

Modes become explicit dimensions in search.

### 6.3 Macro‑primitives (compress setup sequences)
Long sequences are expensive. We discover macros that reliably reach useful modes.

A **macro** is a verified mini-program with:
- goal (mode predicate),
- preconditions,
- sequence sketch,
- determinism check in sandbox.

Macros allow the solver to search at depth 14 “semantically,” not syntactically.

---

## 7) Property library (what we try to falsify)

Properties are checkable predicates. Examples (adapt as needed):

### 7.1 Conservation / accounting properties
- internal ledgers should not diverge from realizable balances beyond a small tolerance
- share conversions should be consistent forward/backward within rounding bounds
- sum of positions should track total assets within tolerance

### 7.2 Monotonicity properties
- indices and accumulators should be monotone (unless explicitly designed otherwise)
- “user credit” should not increase without paying the corresponding cost

### 7.3 Commutativity / interference properties
- for selected pairs (A,B), large differences between `A∘B` and `B∘A` require justification
- non-commutativity is a **signal**, not automatically a bug

### 7.4 Unit / precision properties
- quantities with different units/decimals must not mix without explicit scaling
- rounding bias must not be systematically extractable under repetition

### 7.5 Temporal properties
- time gates must not be bypassable via composition across blocks within configured horizon

---

## 8) Contradiction templates (where next‑gen failures concentrate)

These templates generate ContradictionSpecs.

1) **Ordering sensitivity**  
Material difference between `A∘B` and `B∘A` on a watched property.

2) **Accounting divergence**  
Internal accounting vs realizable balance diverges under some path.

3) **Boundary discontinuity**  
Property holds in steady-state but fails at boundary modes.

4) **Cyclic amplification**  
A closed loop monotonically increases a watched metric (drift).

5) **Precision bias**  
Consistent rounding bias accumulates under repetition into a real violation.

6) **Temporal mismatch**  
Cooldowns/accrual windows can be stepped around by sequencing.

7) **Cross‑module semantic mismatch**  
Two modules interpret the same state differently (e.g., “assets” vs “shares”).

**Rule:** Templates are useless unless they compile into ContradictionSpec objects.

---

## 9) The critical object: ContradictionSpec

ContradictionSpec is what the LLM must output instead of storytelling.

```json
{
  "id": "CSPEC-0007",
  "template": "cyclic_amplification",
  "mode": "supply>0",
  "property": {
    "name": "P-CONSERVATION-01",
    "predicate": "metric_after <= metric_before + epsilon",
    "observation": ["metric_before", "metric_after", "epsilon"]
  },
  "variables": {
    "depth": {"min": 4, "max": 14},
    "actions": {"allowed": ["F1", "F2", "F3"]},
    "amounts": [{"name": "a1", "range": ["1", "1e30"]}],
    "actors": [{"name": "p1"}, {"name": "p2"}],
    "time_offsets_blocks": [{"name": "dt", "range": [0, 50]}],
    "discrete_choices": [{"name": "route", "options": ["R1", "R2"]}]
  },
  "constraints": [
    "all_calls_must_succeed",
    "no_out_of_scope_calls",
    "no_privileged_roles"
  ],
  "objective": {
    "type": "maximize_violation",
    "metric": "metric_after - metric_before"
  },
  "instrumentation": {
    "trace": true,
    "state_diff": true,
    "watch": {
      "balances": ["token:0x...", "native"],
      "storage_slots": ["..."],
      "events": ["..."]
    }
  }
}
```

**Hard rules**
- JSON only.
- Variables must have explicit ranges/options.
- Instrumentation must be explicit.
- No “attack” language; this is sandbox counterexample generation.

---

## 10) Solvers (portfolio, shared evidence)

No single solver wins. The system runs a portfolio and shares artifacts.

### 10.1 Discrete sequence search (structure)
Goal: propose action skeletons and macro compositions that satisfy constraints.

Signals used to prioritize expansions:
- high assumption density functions (many implicit assumptions),
- high interference potential (non-commutativity),
- boundary mode transitions,
- presence of derived/cached state,
- “conversion edges” (assets↔shares, debt↔collateral).

### 10.2 Parameter solving (numbers)
Goal: find amounts/ratios where the kernel flips sign.

Approach:
- treat it as black‑box optimization over sandbox execution,
- use learned priors from evidence (feature vectors),
- keep a “rounding bias detector” running during search.

### 10.3 Precondition synthesis (reach the enabling mode)
Goal: reliably reach the mode needed by the ContradictionSpec.

Method:
- solve sub-goals (“reach mode M”),
- compile into macros,
- reuse macros across runs.

### 10.4 Shrinking (make it minimal and real)
Shrink:
- depth,
- actor count,
- parameter magnitude,
- external assumptions.

If a hit disappears under shrinking, it wasn’t a hit.

---

## 11) Evidence compiler (deterministic, mandatory)

The evidence compiler converts raw traces into structured artifacts:

- `trace.json` (ordered call frames, gas, logs, revert reasons)
- `diff.json` (state diffs: balances + watched slots)
- `features.json` (signals for learning/triage)

Minimum feature set:
- per-step deltas of watched metrics,
- conservation error curve over time,
- rounding bias signature (consistent ±1 drift),
- commutativity distance for tested pairs,
- constraint tightness (which preconditions were nearly violated),
- sensitivity probes (small parameter perturbations).

Evidence feeds the next reasoning step.

---

## 12) Coverage (measurable, or it didn’t happen)

### 12.1 Required coverage metrics
- **CEG edge coverage:** executed edges / total edges
- **Assumption coverage:** assumptions touched by at least one sequence
- **Mode coverage:** which boundary modes were reached
- **Depth coverage:** histogram of tested depths (up to max)
- **Macro coverage:** macros instantiated/expanded
- **Interference coverage:** tested A/B commutativity pairs

### 12.2 Stopping criteria (per run)
Stop only if:
- budget exhausted, OR
- coverage thresholds met AND all contradiction templates were instantiated across relevant modes.

---

## 13) Roles (LLM + deterministic parts, strict I/O)

LLMs are used to propose structured specs and candidates. Deterministic components enforce correctness.

### 13.1 Orchestrator (deterministic)
- enforces gates,
- schedules roles,
- manages budgets,
- de-duplicates specs,
- persists artifacts.

### 13.2 Cartographer (LLM → CEG candidates)
Input: ABI/source/bytecode summaries.  
Output: JSON describing:
- external dependencies,
- derived/cached state suspects,
- conversion edges,
- mode predicates,
- hotspots for interference.

### 13.3 Assumption Miner (LLM → assumptions)
Output: JSON array of assumption objects, each tied to concrete reads/writes.

### 13.4 Invariant Engineer (LLM → predicates)
Output: JSON array of checkable invariants (predicates) scoped by mode.

### 13.5 ContradictionSpec Writer (LLM → ContradictionSpec)
Takes templates + assumptions + invariants + modes and outputs ContradictionSpec JSON.

### 13.6 Macro Synthesizer (LLM → macro candidates)
Proposes macros as goal predicates + abstract action sketches (verified deterministically).

### 13.7 Simulator / Evaluator (deterministic)
Executes sequences in sandbox, collects traces, computes invariant deltas.

### 13.8 Shrinker (deterministic + optional LLM assist)
Minimizes sequences while preserving violation.

### 13.9 Report Writer (LLM → FindingReport draft)
Consumes evidence artifacts and writes a clear report with mitigations + coverage.

---

## 14) Prompt contracts (templates)

These are *contracts* for structured outputs. Each role must output JSON only.

### 14.1 Cartographer prompt
> Output JSON only with:  
> - mode_predicates[]  
> - conversion_edges[] (e.g., assets↔shares)  
> - derived_state_fields[] (cached indices/rates)  
> - interference_candidates[] (pairs of functions likely non-commutative)  
> - external_dependencies[] (readpoints/writepoints)  
> Constraints: no narrative, no exploit instructions, no out-of-scope calls.

### 14.2 Assumption Miner prompt
> Output JSON array:  
> [{ "function": "...", "assumption": "...", "evidence": { "reads": [...], "writes": [...], "why": "..." } }]  
> Assumptions must be falsifiable and tied to concrete state usage.

### 14.3 Invariant Engineer prompt
> Output JSON array:  
> [{ "name": "...", "mode": "...|any", "predicate": "...", "tolerance": "...", "notes": "..." }]  
> Predicates must be checkable in the sandbox (no vague language).

### 14.4 ContradictionSpec Writer prompt
> Generate a ContradictionSpec JSON.  
> Must include: template, mode, property(predicate+observations), variables(ranges/options), constraints, objective, instrumentation(watch lists).  
> No narrative. No attack language. Authorized sandbox only.

### 14.5 Macro Synthesizer prompt
> Propose macros as JSON array:  
> [{ "goal_mode": "...", "preconditions": [...], "abstract_sequence": ["F?","F?"], "why_it_helps": "..." }]  
> The abstract_sequence must be verified deterministically before use.

---

## 15) Hygiene (don’t kneecap your own research)
- Never commit RPC URLs with embedded keys (use env vars).
- Close every markdown code fence (CI lint).
- Store traces/state diffs deterministically and version them.
- Always include limitations + coverage. “Trust me” is not evidence.

---

## 16) Success criteria (what “done” means)
A successful run produces:
- a minimal counterexample sequence in sandbox,
- a violated property with a checkable predicate,
- traces + state diffs + features,
- a clear report with mitigations and coverage.

Anything else is noise.
