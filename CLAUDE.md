# CLAUDE.md v12.6 — Protocol Vuln Discovery OS (2026-02-06)
## bundle -> map -> hypothesize -> execute -> prove
## Evidence-first • Feasibility-first • Composition-first • Fork-grounded

This file is a **decision-complete runbook** for turning a protocol into **reviewable artifacts** (graphs, storage surfaces, source bundles, evidence) and then into **fork-grounded exploit proofs** (or falsified hypotheses) using the installed skills.

Key intent: integrate **bundle -> map -> hypothesize -> execute -> prove** using the workspace skills:
- `sourcify-contract-bundler` (address->universe mapping + sources + ABI + proxies + optional SQD evidence)
- `traverse-protocol-analysis` (full-surface static maps; do not miss callables)
- `ityfuzz-protocol-hunter` (dynamic, sequence-driven search + PoCs)
- `tenderly-protocol-lab` (forensics-grade traces + controlled simulations + Virtual TestNet labs + automation hooks)

Notation used throughout:
- `<workspace>`: repository root (current working directory)
- `<skills_dir>`: skill install root (defaults to `./skills` in the workspace)
- `<protocol_slug>`: short engagement name, e.g. `compound-v3`, `curve-stableswap`, `foo-vaults`
- `<engagements_dir>`: engagement artifact root (defaults to `analysis/engagements/`; configurable via `ENGAGEMENTS_DIR`)
- `<engagement_root>`: `<engagements_dir>/<protocol_slug>/` (all artifacts live here; path is relative to `<workspace>`)

---

# 1) Header: Guardrails, Mission, Non-Negotiables

## 1.1 Authorized + fork-only

- Work **only** on targets you are authorized to assess.
- Execution is **fork-only**. Never run "live" exploit attempts against real protocols.
- If `chain_id`, `fork_block`, or seed addresses are missing: **stop and ask**. No guessing.

## 1.2 No wrongdoing assistance

- Never provide guidance for evasion, laundering, or "covering tracks".
- Never generate payloads intended for harming real systems or users.

## 1.3 Evidence-first, no vibes

- If you can't point to fork-grounded evidence (trace/state-diff/balances), you **do not know**.
- "Interesting" without a measurable delta is not progress. Convert observations into discriminating experiments.

## 1.4 No user-facing vulnerability claims until E3

- You may explore and develop hypotheses (E1/E2), but you must **not** claim/report a vulnerability to the user until E3 gates pass.

## 1.5 E3 reporting gate (massive delta)

You may only present an E3 "finding" when all are true on the pinned fork:
- Reproducible sequence; any privileged effects are either not required or are obtained **permissionlessly within the sequence** (auth bypass/priv-esc is part of the exploit), not assumed.
- Costs are itemized (gas, protocol fees, MEV/bribes, market impact/slippage, flash fees, unwind costs).
- Net profit is materially large **after** costs. Prefer reporting deltas in native units (token amounts); optionally add a rough USD-equivalent at the fork block if it helps communicate magnitude.
- Robustness: still profitable under adverse-but-plausible perturbations:
  - gas +20%
  - liquidity depth -20%
  - timing shift +1 block where applicable
  - weaker ordering tier when possible (builder -> strong -> medium -> weak)

## 1.6 Source-of-truth hierarchy (anti-self-deception)

**Code is a map. Fork behavior is the territory.**
1) Fork execution (traces, state diffs, balance changes)
2) On-chain storage at `fork_block`
3) Verified source code (intent signal)
4) Bytecode / decompile
5) Docs / issues / deploy scripts (weakest)

---

# 2) Toolchain & Skill Orchestration (Mandatory)

## 2.0 Preflight: skills installed (hard stop)

Skills are located in the current workspace under `./skills/`. If any are missing, **stop**.

Defaults:
- `SKILLS_DIR="./skills"`
- `ENGAGEMENTS_DIR="${ENGAGEMENTS_DIR:-analysis/engagements}"`

Verify:
```bash
SKILLS_DIR="./skills"
ENGAGEMENTS_DIR="${ENGAGEMENTS_DIR:-analysis/engagements}"

for s in sourcify-contract-bundler traverse-protocol-analysis ityfuzz-protocol-hunter tenderly-protocol-lab \
  evm-bytecode-lab evm-dynamic-dispatch-lab offchain-control-plane-audit mev-ordering-lab bridge-message-path-lab evm-semantics-quirks-lab; do
  test -d "$SKILLS_DIR/$s" || { echo "Missing skill in workspace: $s"; exit 1; }
done
```

Optional but recommended runtime preflight (fail fast):
```bash
command -v python >/dev/null || exit 1
command -v rg >/dev/null || exit 1
command -v ityfuzz >/dev/null || echo "WARN: ityfuzz not in PATH"
command -v forge >/dev/null || echo "WARN: forge not in PATH (Traverse test-gen validation may be skipped)"
```

## 2.1 Skill map (When / Inputs / Outputs / Failure modes / Next step)

| Skill | When to run | Inputs | Outputs (persisted) | Common failure modes | Next step |
|---|---|---|---|---|---|
| `sourcify-contract-bundler` | First, unless you already have the full local repo | `chain_id`, seed addresses, RPC URL, explorer key (optional), SQD window (optional) | `<engagement_root>/contract-bundles/**/manifest.json`, `src/`, `abi/`, `metadata/`, `rpc/`, optional `sqd/` | Unverified sources; missing proxy impl; incomplete dependency tree; rate limits | Expand address set; merge sources into a Traverse input tree |
| `traverse-protocol-analysis` | After you have sources | Protocol source tree (repo OR merged bundle sources) | `<engagement_root>/traverse/**` (deep/external call graphs, storage analyzer, bindings, optional tests) | Import resolution gaps; dynamic dispatch under-approx; huge graphs | Enforce completeness checks; summarize callable surfaces into `memory.md` |
| `ityfuzz-protocol-hunter` | After static map and hypotheses exist | Target address set, chain, fork block, attacker tier constraints | `<engagement_root>/ityfuzz/<campaign>/**` (logs, crashes, repro traces, manifests) | Wrong fork block; missing RPC/explorer key; unstable repro; too-wide target set | Narrow hypotheses; iterate detectors; produce replay + Foundry PoC evidence |
| `tenderly-protocol-lab` | Whenever you need evidence-grade traces or controlled simulations (esp. for proof) | Tenderly Node RPC URL, optional API key + slugs, tx hashes, call data, VNet RPC/Admin RPC URLs | `<engagement_root>/tenderly/**` (saved JSON-RPC/API responses, links, notes) | Missing keys/URLs; unsupported network; rate limits; unverified contracts reduce decode quality | Use Tenderly to confirm deltas, debug sequences, and harden E3 proofs |
| `evm-bytecode-lab` | When sources/ABIs are missing or misleading | RPC URL, fork block, contract addresses | `<engagement_root>/notes/bytecode-surface.md` + updates to `entrypoints.md` / `taint-map.md` | Custom dispatch under-approx; signature DB noise | Pivot to dynamic dispatch lab + Tenderly runtime evidence |
| `evm-dynamic-dispatch-lab` | When dispatch is runtime-routed (diamonds/routers/plugins/proxies) | RPC URL, fork block, addresses, Traverse scan outputs | `<engagement_root>/notes/diamond-loupe.*` + manual edges in `taint-map.md` | Loupe missing; heavy assembly | Use Tenderly traces/sims to map runtime edges; expand universe |
| `offchain-control-plane-audit` | When offchain authority gates behavior (signers/keepers/forwarders/intents) | Sources + fork block + Tenderly sims | `control-plane.md` + `feasibility.md` updates + Tenderly evidence | Offchain artifact not onchain | Record as feasibility constraint; attempt bypass via discriminators |
| `mev-ordering-lab` | When ordering tier matters (sandwich/backrun/keeper races) | Hypothesis + pinned fork + Tenderly bundle/VNet | Bundle/VNet evidence under `<engagement_root>/tenderly/**` + `feasibility.md` | Cannot prove public mempool viability in sims | Bound requirements; record attacker tier explicitly |
| `bridge-message-path-lab` | When cross-domain messages/bridges exist | Sources + fork block + message tx templates | `message-path.md` + evidence under `<engagement_root>/tenderly/**` | Complex proof verifiers | Treat verifier as TCB; focus on acceptance predicates + replay + writers |
| `evm-semantics-quirks-lab` | When assembly/new semantics/system quirks may break assumptions | Source scans + fork lab | `evm-semantics.md` + falsifier evidence paths | Chain-specific behaviors | Re-run falsifiers on the exact chain/fork; do not generalize |

---

## 2.2 Capability Router (No Duplication)

Hard rule: **pick one primary tool per capability**. Use fallbacks only if the primary is unavailable or provably insufficient, and record that decision in `memory.md`.
Provider unification rule (avoid "cross-provider confusion"):
- Do not mix different tracers/simulators for the *same* evidence artifact unless forced. Prefer Tenderly artifacts for E3.
- If you must use a fallback tracer (archive `debug_traceTransaction`, SQD traces, etc.), record why and keep the artifact as a separate evidence line item.
This keeps comparisons consistent (decoded fields, state diffs, asset changes, and ordering assumptions vary by provider).

| Capability need | Primary | Why | Persisted evidence | Fallback |
|---|---|---|---|---|
| Sources + ABI + proxy/impl map (contract universe) | `sourcify-contract-bundler` | best coverage for verified source trees + proxy resolution | `<engagement_root>/contract-bundles/**` | manual + explorer + bytecode |
| Bulk historical evidence over ranges (logs/txs/traces/state diffs) | `sourcify-contract-bundler` (SQD) | scalable NDJSON evidence with provenance | `<engagement_root>/contract-bundles/**/sqd/**` | custom indexer / explorer exports |
| Evidence-grade decoded trace for a specific tx | `tenderly-protocol-lab` (`tenderly_traceTransaction`) | decoded call trace + state/asset/balance changes; easy JSON artifact | `<engagement_root>/tenderly/rpc/**` | archive node `debug_traceTransaction` |
| Controlled what-if (single tx) incl. state + block overrides | `tenderly-protocol-lab` (`tenderly_simulateTransaction`) | cheapest discriminator; deterministic; rich deltas | `<engagement_root>/tenderly/rpc/**` | local fork + scripts |
| Atomic multi-tx sequence (same block) | `tenderly-protocol-lab` (`tenderly_simulateBundle`) | built for chained sequences | `<engagement_root>/tenderly/rpc/**` | local fork (harder) |
| Multi-block/time/epoch lab + snapshots + cheatcodes | `tenderly-protocol-lab` (Virtual TestNets + Admin RPC) | fastest multi-block experimentation | `<engagement_root>/tenderly/rpc/**` | local anvil + time-warp |
| Static reachable surface + storage touch maps | `traverse-protocol-analysis` | prevents missed callables; maps reads/writes | `<engagement_root>/traverse/**` | manual review |
| Discover unknown cross-contract exploit sequences | `ityfuzz-protocol-hunter` | sequence search; produces PoCs | `<engagement_root>/ityfuzz/**` | hypothesis-driven manual sims |
| Unverified/partial ABI/source recovery | `evm-bytecode-lab` | recover selectors + proxy hints from bytecode | `<engagement_root>/notes/bytecode-surface.md` | manual + trace inference |
| Diamond/router/plugin dispatch mapping | `evm-dynamic-dispatch-lab` | convert runtime routing into explicit edges + writers | `<engagement_root>/notes/diamond-loupe.*` | trace-based mapping |
| Signature/keeper/forwarder control planes | `offchain-control-plane-audit` | map offchain authority into onchain anchors + bypass tests | `<engagement_root>/notes/control-plane.md` | treat as feasibility constraint |
| Ordering-tier (MEV) viability proofs | `mev-ordering-lab` | bundle/VNet evidence to bound attacker tiers | `<engagement_root>/notes/feasibility.md` | local fork labs |
| Cross-domain authenticity + replay model | `bridge-message-path-lab` | message acceptance predicate + replay + writers + falsifiers | `<engagement_root>/notes/message-path.md` | treat verifier as TCB |
| Assembly/new semantics falsifiers | `evm-semantics-quirks-lab` | fork experiments proving/falsifying semantics assumptions | `<engagement_root>/notes/evm-semantics.md` | bytecode-only inspection |

## 2.3 Skill Usage Contract (Self-evolving; keep this OS lean)

Hard rule: **do not duplicate full command blocks here**. Always read the skill's `SKILL.md` for exact commands, flags, and current best practices:
- `./skills/<skill>/SKILL.md`

How to interpret skill command templates:
- If a skill shows `python scripts/foo.py` or `scripts/foo.sh`, run it either by:
  - `cd "./skills/<skill>"` first, or
  - prefixing the path with `./skills/<skill>/...` from `<workspace>`.

Required output discipline (applies to every skill):
- Persist every run under `<engagement_root>` (never paste large outputs into chat).
- Record every artifact directory path in `index.yaml`.
- Summarize only belief-changing deltas into `memory.md`.

### `sourcify-contract-bundler`
- Responsibility: contract universe mapping (sources/ABIs/proxies) plus optional **bulk** SQD evidence.
- Non-dup rule: do **not** use SQD for single-tx "deep trace" work; use Tenderly for that.
- Self-evolving rule: any time a new address appears in traces/graphs/fuzzer logs, add it to the seed set and re-run the bundler.

### `traverse-protocol-analysis`
- Responsibility: static "do not miss callables" maps (deep call graph + storage surfaces) on the bundled sources or local repo.
- Completeness gate: treat the **deep** call graph as authoritative; explicitly account for dynamic dispatch (`delegatecall`, low-level calls, selector construction) by documenting "manual edges".

### `ityfuzz-protocol-hunter`
- Responsibility: sequence discovery and PoC generation on the pinned fork.
- Non-dup rule: don't "prove" with fuzz logs. When a candidate sequence appears, immediately export evidence-grade artifacts via Tenderly trace/simulate and store under `<engagement_root>/tenderly/**`.

### `tenderly-protocol-lab`
- Responsibility: forensics-grade evidence + controlled experiments (decoded traces/sims/bundles/VNets).
- Preferred interface: Node RPC (`tenderly_traceTransaction`, `tenderly_simulateTransaction`, `tenderly_simulateBundle`, gas/decode helpers) with JSON artifacts saved to `<engagement_root>/tenderly/**`.
- UI fast path (optional): Dev Toolkit + Simulator UI for human-speed iteration, but still export JSON evidence for E3.

### `evm-bytecode-lab`
- Responsibility: recover callable surfaces from runtime bytecode when ABI/source is missing or misleading; produce selector inventories and proxy hints.
- Non-dup rule: do not replace Tenderly proofs with signature-DB guesses. Use bytecode recovery to drive better discriminators and universe expansion.

### `evm-dynamic-dispatch-lab`
- Responsibility: convert runtime routing (diamonds/routers/plugins/proxies) into explicit manual edges and writer maps.
- Non-dup rule: do not assume static graphs are complete in the presence of dispatch. Require runtime evidence for high-impact edges.

### `offchain-control-plane-audit`
- Responsibility: map and falsify offchain authority assumptions (signers/keepers/forwarders/intents) via fork discriminators.
- Non-dup rule: do not treat "signed" or "keeper-only" as a filter. Treat it as a hypothesis and try to falsify.

### `mev-ordering-lab`
- Responsibility: bound ordering-tier feasibility with bundle/VNet evidence; keep attacker tier explicit.
- Non-dup rule: do not handwave "MEV needed" or "MEV impossible" without artifacts; record constraints in `notes/feasibility.md`.

### `bridge-message-path-lab`
- Responsibility: model cross-domain authenticity and replay; test message handler falsifiers on a fork; fill `notes/message-path.md`.
- Non-dup rule: do not assume bridge correctness; treat acceptance predicates and replay protection as primary evidence targets.

### `evm-semantics-quirks-lab`
- Responsibility: falsify assembly/new semantics assumptions (transient storage, selfdestruct changes, delegation, chain quirks) with fork experiments.
- Non-dup rule: do not generalize across chains/forks; run falsifiers on the pinned reality and record results.

---

## 2.4 Skill routing heuristics (symptoms -> action)

Use this to keep the agent's decision-making correct under real-world time pressure:
- If you start with *addresses* (typical onchain target): run `sourcify-contract-bundler` first. Everything else depends on a stable contract universe.
- If you start with a *local repo* (you already have sources): run `traverse-protocol-analysis` first, then reconcile with onchain ABIs once addresses are known.
- If you cannot enumerate "what can be called": generate `notes/entrypoints.md` from bundler ABIs and reconcile against Traverse deep graphs; if selectors exist on bytecode but not ABIs, treat as a red flag until resolved.
- If ABIs/sources are missing or selectors are unexplained: route to `evm-bytecode-lab` to recover selectors and proxy hints from runtime bytecode (and update `notes/entrypoints.md` with evidence links).
- If dispatch is runtime-routed (diamonds/routers/plugins/proxies): route to `evm-dynamic-dispatch-lab` to build manual edges and map routing writers (and update `notes/taint-map.md` / `notes/control-plane.md`).
- If a path is gated: do not filter it out. Route to control-plane mapping (and run at least one Tenderly discriminator attempt per high-impact gate).
- If a high-impact action is signature/keeper/forwarder controlled: route to `offchain-control-plane-audit` and attempt falsifiers (invalid sig, replay, forwarder confusion) on the pinned fork.
- If you need to change a belief cheaply: use `tenderly-protocol-lab` simulation (single tx) before running wide fuzzing.
- If you need to test an atomic multi-step sequence: use Tenderly bundle simulation before writing complicated local scripts.
- If the exploit needs time/epochs/multi-block setup: use Tenderly Virtual TestNet (snapshots + time controls) or fall back to a local fork only if Tenderly is unavailable.
- If ordering tier (MEV) is a key constraint: route to `mev-ordering-lab` to produce bundle/VNet evidence and bound attacker tiers.
- If bridges/messengers/proof verifiers exist: route to `bridge-message-path-lab` and fill `notes/message-path.md` with acceptance predicates + replay model + evidence.
- If assembly/new semantics/system quirks are present: route to `evm-semantics-quirks-lab` and require falsifier experiments recorded in `notes/evm-semantics.md`.
- If the bug is "unknown sequence, cross-contract chaining": route to `ityfuzz-protocol-hunter`, but only after Phase C coverage gates exist (entrypoints, control plane, taint map, tokens, numeric boundaries, feasibility).
- If evidence needs scale over wide block ranges (forensics, provenance, "what happened across a window"): use SQD via `sourcify-contract-bundler` and treat it as bulk evidence, not as your per-tx debugger.
- If two iterations do not change beliefs: pivot corridors (auth bypass vs accounting vs oracle vs sequencing), and redesign the next cheapest discriminator (do not just re-run the same fuzzer config longer).

# 3) Hybrid Memory & Context Management (Mandatory)

Objective: never "forget" protocol facts while keeping chat/context small.

## 3.1 Engagement workspace (one deterministic root)

For each protocol, use exactly one engagement root:
- `<engagement_root> = <engagements_dir>/<protocol_slug>/` (relative to `<workspace>`)

Required files inside `<engagement_root>`:
- `memory.md` (hard cap: <= ~200 lines; update every iteration)
- `index.yaml` (artifact pointers + fork pin + commands)

Recommended subdirs (do not over-invent):
- `contract-bundles/` (bundler outputs)
- `traverse/` (Traverse outputs)
- `ityfuzz/` (campaign workdirs)
- `tenderly/` (Tenderly RPC/API evidence artifacts)
- `notes/` (required: coverage artifacts; plus optional hypothesis matrix, asset maps, diagrams)

## 3.2 `index.yaml` schema (small, stable)

Create and maintain `<engagement_root>/index.yaml` with these keys:
```yaml
protocol: <protocol_slug>
chain_id: <CHAIN_ID>
fork_block: <FORK_BLOCK>
seed_addresses:
  - <ADDR1>
  - <ADDR2>

# Evidence/provenance sources used
rpc_url: <RPC_URL_USED>
explorer: <EXPLORER_BASE_OR_NAME>
etherscan_key_env: <ENV_VAR_NAME_FOR_KEY>

# Artifacts (paths are relative to <workspace>)
bundler_manifest_path: <engagement_root>/contract-bundles/manifest.json
traverse_out_dir: <engagement_root>/traverse
ityfuzz_workdirs:
  - <engagement_root>/ityfuzz/<campaign1>
  - <engagement_root>/ityfuzz/<campaign2>
sqd_evidence_paths:
  - <engagement_root>/contract-bundles/chain-<id>/<addr>/sqd
tenderly_node_rpc_url_env: TENDERLY_NODE_RPC_URL
tenderly_access_key_env: TENDERLY_ACCESS_KEY
tenderly_account_slug: <TENDERLY_ACCOUNT_SLUG>
tenderly_project_slug: <TENDERLY_PROJECT_SLUG>
tenderly_vnet_rpc_url_env: TENDERLY_VNET_RPC_URL
tenderly_vnet_admin_rpc_url_env: TENDERLY_VNET_ADMIN_RPC_URL
tenderly_evidence_paths:
  - <engagement_root>/tenderly/rpc
notes_paths:
  - <engagement_root>/notes/entrypoints.md
  - <engagement_root>/notes/control-plane.md
  - <engagement_root>/notes/taint-map.md
  - <engagement_root>/notes/tokens.md
  - <engagement_root>/notes/numeric-boundaries.md
  - <engagement_root>/notes/feasibility.md
  - <engagement_root>/notes/evm-semantics.md
  - <engagement_root>/notes/message-path.md
  - <engagement_root>/notes/hypotheses.md
```

Rules:
- Never store secrets (keys) in `index.yaml`; only store env var names.
- Every tool run must append its output path to `index.yaml` (or update the single pointer).

## 3.3 `memory.md` template (strict, compact)

Create and maintain `<engagement_root>/memory.md` using this template:
```md
# Memory (<protocol_slug>)

## Pinned Reality
- chain_id:
- fork_block:
- attacker_tier: (public mempool | private relay | builder)
- capital_model: (flash allowed? max size? constraints?)

## Contract Map Summary
- core:
- proxies -> implementations:
- oracles / rate providers:
- routers / aggregators:
- DEX pools / pairs touched:
- privileged control plane (roles/owners/signers/upgrade authority) & where stored:

## Control Plane & Auth (what is supposed to be privileged)
- auth mechanisms: (Ownable/roles/custom/sigs/hooks/forwarders/upgrades)
- auth state locations: (where stored)
- auth writers: (who can change what)
- bypass hypotheses: (1-3 short chains)
- bypass attempts + evidence: (paths only)

## Coverage Status (paths only; keep compact)
- entrypoints:
- control plane:
- taint map:
- tokens:
- numeric boundaries:
- feasibility:
- evm semantics (if needed):
- message path (if needed):

## Value Model Summary (custody vs entitlements)
- custody assets:
- entitlements:
- key measurements (prices/rates/indices/eligibility):
- key settlements (redeem/withdraw/liquidate/claim):

## Top 3 Hypotheses (sequence archetypes)
1) <sequence hypothesis> (optionally: setup/distort/realize/unwind)
2) ...
3) ...

## Last Experiment (cheapest discriminator)
- command:
- evidence paths (from index.yaml):
- result:
- belief change:

## Next Discriminator (single cheapest question)
- question:
- experiment design:
- expected falsifier:

## Open Unknowns
- ...
```

## 3.4 Context governor rules (do this every session)

- Never paste large graphs / tool outputs into chat. Store artifacts under `<engagement_root>` and cite file paths.
- Start every session by reading `memory.md`, then use `index.yaml` to jump to artifacts.
- Use `rg` and targeted file reads; summarize only the minimum into `memory.md`.
- If you learn a new protocol fact: it must be written into `memory.md` within the same iteration.

## 3.5 Coverage artifacts (disk-first; forcing functions, not filters)

Goal: prevent "missed surfaces" and "missed primitives" without turning the OS into a rigid checklist.

Hard rules:
- Keep `memory.md` compact; store exhaustive inventories under `<engagement_root>/notes/`.
- Do not paste massive lists into chat. Persist files and cite paths.
- Every top hypothesis in `memory.md` must reference at least one coverage artifact path (so you can audit what you did not miss).

Required `notes/` files (create empty stubs early; fill as you learn):
- `notes/entrypoints.md`: complete callable surface inventory (selectors + fallback/receive + hooks).
- `notes/control-plane.md`: auth gates + auth-state storage + writers + bypass-attempt matrix + evidence paths.
- `notes/taint-map.md`: user-controlled inputs -> dynamic dispatch/external callsites (target+calldata) + discriminators.
- `notes/tokens.md`: adversarial token semantics classification for every value-moving token.
- `notes/numeric-boundaries.md`: numeric/accounting boundary experiments (empty/zero/tiny supply, donation, rounding loops, scale drift).
- `notes/feasibility.md`: attacker-tier feasibility ledger for each top hypothesis (ordering/oracle/liquidity/capital constraints).
- `notes/evm-semantics.md`: assembly/new-EVM-semantics scan (transient storage, delegation features, chain-specific quirks) and "footgun until falsified" experiments.
- `notes/message-path.md`: cross-domain / bridge message model (only if the universe includes bridges/messengers/proofs).

Optional bootstrap helpers (keep OS command-light; see skill `SKILL.md` for exact usage):
- `./skills/traverse-protocol-analysis/scripts/init_coverage_notes.py` (create note stubs)
- `./skills/sourcify-contract-bundler/scripts/generate_entrypoints_md.py` (ABI-grounded `entrypoints.md`, optional selector scan)
- `./skills/traverse-protocol-analysis/scripts/scan_solidity_callsites.py` (seed `taint-map.md` / `evm-semantics.md`)
- `./skills/traverse-protocol-analysis/scripts/scan_solidity_control_plane.py` (seed `control-plane.md`)
- `./skills/evm-bytecode-lab/scripts/extract_selectors_md.py` (bytecode-first selector recovery when ABI/source is missing)
- `./skills/evm-dynamic-dispatch-lab/scripts/diamond_loupe_dump.py` (diamond loupe selector->facet mapping when supported)

Optional integrity check (non-mutating):
- `./scripts/validate_engagement.py` (verify required files/notes exist; warn on missing pointers and oversized memory; run from `<workspace>`)

Minimal templates (keep each file small; link to raw artifacts instead of duplicating them):

`notes/entrypoints.md` (canonical surface inventory):
- For each contract address (proxy + impl), list:
  - function signature + selector (or "fallback/receive")
  - callable by (EOA | contracts | hooks/callbacks)
  - gating summary (none | gated | gated but bypass attempted; link to `notes/control-plane.md`)
  - external-call behavior (none | fixed targets | dynamic targets; link to `notes/taint-map.md`)
  - state writes (high level; link to Traverse storage analyzer output)

`notes/taint-map.md` (arbitrary-call corridor):
- For each low-level callsite / dynamic dispatch:
  - where (file:line or function name)
  - target source (constant | config | caller-controlled | storage-controlled)
  - calldata source (constant | config | caller-controlled | derived)
  - value source (fixed | caller-controlled)
  - safety checks (allowlist? signature? nonce? reentrancy? length checks?)
  - cheapest discriminator (Tenderly simulate) + evidence path

`notes/tokens.md` (token semantics corridor):
- For each token (asset/receipt/debt/reward):
  - semantics flags: fee-on-transfer, rebasing, ERC777 hooks, nonstandard return values, nonstandard decimals, pausable/blacklist, upgradeable
  - protocol assumptions that break if nonstandard
  - cheapest discriminator (simulate transfer in/out; observe deltas)

`notes/numeric-boundaries.md` (numeric corridor):
- Boundary experiments to attempt against top value flows:
  - empty/zero-supply and tiny-supply edges (ERC4626-like exchange rate, pool virtual balances)
  - donation/inflation before deposit/mint; repeated round-trip loops (rounding drift)
  - scale normalization (decimals) applied twice or skipped once
  - index/rate provider mismeasurement; cached measurement invalidation at boundaries
  - stable-math solver vs implementation mismatch (if relevant)
  - extreme-input discontinuities (wrap/truncate -> near-free pricing)

`notes/feasibility.md` (feasibility-first enforcement):
- For each top hypothesis:
  - attacker_tier constraint (public mempool | private relay | builder)
  - ordering requirement (none | sandwich | backrun | multi-block)
  - oracle requirement (spot/TWAP/staleness/heartbeats; manipulation feasibility)
  - liquidity requirement (depth, slippage tolerances; can setup+unwind?)
  - cheapest falsifier experiment and evidence path

---

# 4) Operating Loop (Self-evolving, self-evaluating)

Run phases A-F in order. Do not skip a phase unless you explicitly record why in `memory.md`.

## Meta-loop — Cheapest Discriminator Engine (run continuously)

This OS is self-evolving only if it **changes beliefs based on evidence**. Before and after every phase (and after every experiment), force this loop:

1) **Name the current bottleneck** to E3 (one sentence).
2) **Diverge briefly (timebox) without losing the thread**:
   - Generate multiple plausible pathways to reach the goal (including bypasses, weird edges, and cross-contract composition).
   - Write them as 1-liners into `<engagement_root>/notes/hypotheses.md` (active set + backlog). No prose.
   - Hard anti-distraction rule: you may brainstorm widely, but you must keep exactly one "active thread" at a time until its discriminator is executed.
3) **Converge to the single cheapest discriminator** that could change your belief.
   - Prefer: Tenderly simulation/trace (cheap, controlled) -> Traverse map updates -> ItyFuzz campaigns (expensive search).
4) **Run + persist artifacts** under `<engagement_root>` and update `index.yaml`.
5) **Update `memory.md` immediately** with:
   - what belief changed
   - what evidence was produced (file paths)
   - what the next cheapest discriminator is
6) **Pivot rule**: if two iterations do not change beliefs, pivot to a different hypothesis corridor (e.g., auth bypass vs accounting vs oracle vs sequencing) and redesign the discriminator.

Consistency guardrails (do not self-sabotage):
- Pinned reality (`chain_id`, `fork_block`, attacker tier) is a hard anchor for an iteration. Do not quietly drift it.
- If you must change fork block to test freshness, record it explicitly as a new pin in `memory.md` and keep the original pin for reproducibility.
- Never "believe" a new theory unless it is attached to at least one concrete artifact path.

Coverage gates (do not proceed to long fuzzing if these are unknown):
Definition: an "auth gate" is any condition that attempts to restrict action by caller/context (owners/roles/allowlists, signature-based permissions, callback/hook "trusted caller" assumptions, meta-tx forwarders, upgrade/admin paths, timelocks/guards).
- Contract universe: proxy->impl map complete; oracles/routers/pairs/tokens included.
- Callable surface: `notes/entrypoints.md` exists and covers all ABI-exposed selectors plus `fallback/receive` and implemented hooks/callbacks.
- Control plane: `notes/control-plane.md` exists; all auth gates + auth-state storage + writers mapped; at least 1 discriminator attempt executed for each high-impact gate.
- Arbitrary-call corridor: `notes/taint-map.md` exists for every dynamic external callsite / dynamic dispatch; at least 1 discriminator executed for each high-risk callsite.
- Token semantics: `notes/tokens.md` exists for every token that moves value in top flows (assets, receipts, debt, rewards).
- Numeric boundaries: `notes/numeric-boundaries.md` exists and contains at least one boundary experiment result for each top value flow.
- Feasibility: `notes/feasibility.md` exists for each top hypothesis (ordering/oracle/liquidity/capital constraints) and includes at least one executed discriminator.
- EVM semantics: if inline `assembly` / new semantics are present, `notes/evm-semantics.md` exists and includes at least one falsifier experiment per suspected footgun.
- Message path: if bridges/messengers/proof verifiers exist, `notes/message-path.md` exists and includes at least one discriminator attempt.
- Value model: custody vs entitlements written; measurement inputs (oracles/indices/decimals) explicit.
- Runtime reconciliation: at least one evidence-grade decoded trace/simulation exists for each top flow you're reasoning about.

## Phase A — Pin reality (no floating facts)

1) Create `<engagement_root>` and initialize `index.yaml` + `memory.md`.
2) Record:
   - `protocol_slug`
   - `chain_id`
   - `fork_block` (absolute number)
   - seed addresses (core entrypoints, registries, routers)
   - attacker tier + capital model assumptions
3) Hard stop if any are missing.

## Phase B — Build the contract universe (Bundler)

1) Run `sourcify-contract-bundler` with `--max-depth 4` (or higher if nested proxies exist).
2) Expand address set to all protocol-relevant dependencies:
   - implementations for every proxy
   - oracles/rate providers used for any measurement
   - routers/aggregators/pools used for swaps and liquidation legs
   - tokens (including receipts/debt)
3) Update:
   - `index.yaml`: `bundler_manifest_path`, seed list, SQD paths if used
   - `memory.md`: proxy->impl mapping and any missing/unverified contracts
4) Universe expansion loop (do not freeze the map too early):
   - Mine additional addresses from: (a) Traverse graphs (external calls), (b) Tenderly traces of representative txs, (c) protocol constants/config.
   - If new addresses appear: add them to seeds and re-run the bundler until the universe stabilizes.

## Phase C — Static map (Traverse) + completeness enforcement

1) Run `traverse-protocol-analysis` full scan and produce deep/external call graphs and storage maps.
   - If the protocol has function variants that should be equivalent (or an upgrade/refactor boundary), populate `<engagement_root>/notes/storage-pairs.csv` and run `storage-trace` in batch to catch silent drift (commands live in the Traverse skill).
2) Mandatory "Do not miss callables" checks:
   - Confirm deep graphs exist in `<traverse_out_dir>` (DOT/SVG/MD).
   - Build and persist the canonical entrypoint inventory:
     - write `<engagement_root>/notes/entrypoints.md` from (a) bundled ABIs, (b) source-level entrypoints, and (c) selector/bytecode scan for missing ABIs.
     - include proxy + implementation surfaces; include `fallback/receive`; include implemented hooks/callback entrypoints.
   - Run the dynamic dispatch search (`delegatecall`, low-level calls, `assembly`, selector construction).
3) Phase C.1 — Control Plane & Auth-Bypass Map (mandatory)
   Hard rule: **Do not mark an entrypoint "out of scope" just because it is gated.** Treat gating as a hypothesis and attempt to falsify it. If falsified, that surface becomes permissionless.
   - Inventory auth gates across *all* external/public entrypoints:
     - modifiers + inline checks + "trusted caller" patterns (hooks/callbacks, forwarders, routers)
   - Locate auth state in storage:
     - owner/admin slots, role membership mappings, guardians, operator allowlists
     - signers/validators, forwarder config, upgrade authority, timelock/guard config
   - Map auth-state writers and their reachability:
     - every function that can change auth state
     - whether attacker-reachable directly or via another path
   - Exhaustive bypass-family forcing function (do not handwave):
     - init/reinit paths (`initialize` variants, constructors replaced by init, module init)
     - proxy/impl confusion (call impl directly; uninitialized impl; UUPS/Beacon admin confusion)
     - upgrade authority drift (upgradeTo/upgradeToAndCall/changeAdmin/setBeacon/diamond cut paths)
     - signature/permit/forwarder issues (EIP-712 domain separation, nonce/replay, meta-tx sender parsing)
     - callback/hook trust confusion (onlyPool/onlyRouter assumptions, forged callback context)
     - delegatecall/plugin clobber (user-controlled library/module addresses; selector routing)
     - boolean/logic slips in access checks (`||` vs `&&`, inverted conditions, role constant mismatch)
     - timelock/guard miswires (guarded path vs unguarded alternate path)
   - Design and run cheapest discriminators (fork-only evidence, no key assumptions):
     - attempt the privileged action from an attacker-controlled sender via Tenderly simulation/trace to capture the exact guard/revert
     - attempt any attacker-reachable writer path that changes auth state, then re-attempt the privileged action
   - Record results:
     - persist the matrix in `<engagement_root>/notes/control-plane.md` (gates, state locations, writers, bypass families attempted, evidence paths)
     - summarize control plane + bypass status in `memory.md` (1-5 bullets)
     - add evidence artifact paths to `index.yaml` (prefer Tenderly JSON artifacts under `<engagement_root>/tenderly/**`)
4) Phase C.2 — Arbitrary-call and parameter-taint map (mandatory)
   - Build `<engagement_root>/notes/taint-map.md`:
     - enumerate every external callsite that can send value or change state outside the contract set
     - classify each callsite by whether target/calldata/value are caller-controlled vs config-controlled
     - for each high-risk callsite, run at least one Tenderly discriminator simulation and store evidence
5) Phase C.3 — Token semantics classification (mandatory)
   - Build `<engagement_root>/notes/tokens.md` for all value-moving tokens discovered so far.
   - If any token is nonstandard (fee-on-transfer, rebasing, ERC777, nonstandard return values, etc.):
     - add a targeted discriminator (Tenderly simulate a minimal in/out flow) and record evidence paths.
6) Phase C.4 — Numeric boundary and accounting semantics forcing function (mandatory)
   - Build `<engagement_root>/notes/numeric-boundaries.md`:
     - identify top value flows (deposit/mint, withdraw/redeem, borrow/repay, liquidate, claim, swap legs)
     - for each flow, choose at least one boundary discriminator (empty/zero/tiny supply, donation, rounding loop, scale drift) and execute it on the fork (Tenderly sim preferred)
     - store evidence artifacts under `<engagement_root>/tenderly/**` and reference them in `notes/numeric-boundaries.md`
7) Phase C.5 — EVM semantics scan (conditional but strict)
   - If the codebase uses inline `assembly`, low-level opcodes, or newly introduced semantics (e.g., transient storage, delegation features):
     - write `<engagement_root>/notes/evm-semantics.md` and run at least one falsifier experiment per suspected semantic footgun.
8) Phase C.6 — Cross-domain/message-path model (only if relevant)
   - If the universe includes bridges/messengers/proof verifiers:
     - build `<engagement_root>/notes/message-path.md` (domain separation, nonces, replay protection, verifier trust assumptions) and add a cheapest discriminator attempt.
9) If dynamic dispatch exists:
   - Document "manual edges" (source->target reachability) in `memory.md`.
   - Treat graphs as under-approx and compensate in hypotheses and fuzz targets.
10) Update:
   - `index.yaml`: `traverse_out_dir`
   - `memory.md`: "callable surface summary" + "manual edges / blind spots"
11) Runtime reconciliation (cheap correctness check):
   - For each top flow you're reasoning about, obtain at least one evidence-grade decoded trace/simulation via Tenderly.
   - Compare "addresses touched" vs your contract universe; if new contracts appear, return to Phase B/C.

## Phase D — Hypothesis matrix (open-world; no checklist limits)

1) Generate 3-10 candidate sequences from *any* signal source:
   - static maps (Traverse call graph + storage writes)
   - runtime evidence (Tenderly traces/sims)
   - fuzz evidence (ItyFuzz artifacts)
2) For each hypothesis, record:
   - entrypoints used (reference `notes/entrypoints.md`)
   - callsites/dispatch used if relevant (reference `notes/taint-map.md`)
   - token assumptions if relevant (reference `notes/tokens.md`)
   - numeric boundary leveraged if relevant (reference `notes/numeric-boundaries.md`)
   - sequence description (optionally: setup -> distort -> realize -> unwind; do not force-fit if it doesn't match)
   - cross-contract set required
   - any assumed privilege (and if privileged, the **permissionless privilege-acquisition chain** to test)
   - invariant/evidence that proves value delta
   - feasibility constraints (attacker tier, ordering, oracle/liquidity assumptions; link `notes/feasibility.md`)
3) Enforce feasibility-first:
   - Create/update `<engagement_root>/notes/feasibility.md` for each top hypothesis before long fuzzing.
4) Rank by:
   - expected path-to-delta (how quickly can a fork experiment falsify?)
   - feasibility under attacker tier constraints
5) Write top hypotheses into `memory.md`.

## Phase E — Execute campaigns (ItyFuzz)

1) Choose campaign type:
   - fork-first if reality-dependent (oracles/liquidity/MEV)
   - harness/offchain if you must encode invariants/initialization
2) Iterate:
   - baseline run (narrow targets) -> widen only when stuck
   - adjust detectors based on hypothesis (profit delta, invariant violation, solvency flip)
3) Store every campaign under:
   - `<engagement_root>/ityfuzz/<campaign>/`
4) Summarize each campaign into `memory.md`:
   - what happened
   - what belief changed
   - the cheapest next discriminator
5) When a candidate sequence emerges, immediately produce evidence-grade artifacts:
   - export decoded traces with Tenderly (`tenderly_traceTransaction`) and/or confirm the atomic chain with `tenderly_simulateBundle`
   - store artifacts under `<engagement_root>/tenderly/**` and record paths in `index.yaml`

## Phase F — Proof & reporting gate (E3)

Only if you have a candidate exploit:
1) Replay and confirm determinism on the pinned fork.
2) If the exploit uses privilege escalation/auth bypass, include the exact privilege-acquisition chain as part of the proof (same evidence standard as value delta).
3) Export evidence artifacts for every tx in the sequence:
   - preferred: Tenderly `tenderly_traceTransaction` (decoded calls/state/asset changes) saved under `<engagement_root>/tenderly/rpc`
   - fallback: SQD evidence dumps (tx/traces/stateDiffs) under `<engagement_root>/contract-bundles/**/sqd`
4) Produce custody + entitlement deltas (before/after) and itemize costs.
5) Run robustness perturbations (gas/liquidity/timing/ordering).
6) Freshness check (recommended): re-run the minimal proof sequence on a more recent block (new pinned fork), and record whether it still holds.
   - Keep the original E3 proof pinned to its original `fork_block` for reproducibility.
7) Only then: write an E3 report (minimal sequence, root cause, regression test idea).

## Self-evaluation rule (after every phase and every campaign)

Answer in `memory.md`:
- What belief changed?
- What evidence was produced? (file paths)
- What is the single cheapest next discriminator?

Pivot rule:
- If no belief changes in 2 iterations: pivot to a different hypothesis corridor (e.g., auth bypass vs accounting vs oracle vs sequencing) and design a new discriminator.

## Done checks (acceptance criteria)

You are "done" with the OS workflow for an engagement only when:
1) `index.yaml` exists and points to:
   - bundler manifest
   - traverse output dir
   - at least one ityfuzz workdir
2) `memory.md` remains compact (<~200 lines) and always contains:
   - pinned reality
   - contract map summary (including proxies/impls)
   - top hypotheses + last experiment + next discriminator
3) Traverse completeness is enforced:
   - deep graph is treated as authoritative
   - dynamic dispatch/proxy caveats and manual edges are documented
4) Control plane coverage is enforced:
   - auth gates + auth-state storage + writers are mapped
   - at least 1 discriminator attempt exists for each high-impact gate (evidence paths recorded)
5) Coverage artifacts exist under `<engagement_root>/notes/`:
   - `entrypoints.md`, `control-plane.md`, `taint-map.md`, `tokens.md`, `numeric-boundaries.md`, `feasibility.md`
   - conditional: `evm-semantics.md` if assembly/new semantics exist; `message-path.md` if bridges exist

## Dogfood scenario (non-destructive)

Purpose: validate the OS end-to-end on a known example (from ItyFuzz tutorials / known exploits) without touching any live systems.

Checklist:
1) Create `<engagement_root>` for a known tutorial target.
2) Bundle seed addresses -> generate `manifest.json`.
3) Run Traverse full scan on the bundled sources or a local repo.
4) Run an ItyFuzz campaign on a pinned fork block.
5) Export at least one Tenderly evidence artifact (trace or simulation) under `<engagement_root>/tenderly/**`.
6) Confirm `index.yaml` points to:
   - `contract-bundles/**/manifest.json`
   - `traverse/`
   - `ityfuzz/<campaign>/`
7) Confirm `memory.md` stays compact and tracks: hypothesis -> discriminator -> result.
8) Confirm `notes/` contains the coverage artifacts required by section 3.5 and the meta-loop coverage gates.

---

# 5) Appendices (Reference-Only; do not start here)
## Appendix A — Master Prompt (run the OS phases; keep outputs evidence-linked)

```text
MISSION
- Construct a sequence (often multi-contract, multi-tx) that violates protocol meaning (invariants over time) for profit.
- Integrate bundle -> map -> hypothesize -> execute -> prove.

HARD GUARDRAILS (DO NOT BEND)
- authorized targets only; fork-only execution; never run live exploit attempts.
- no evasion/laundering/cover-tracks guidance.
- if chain_id / fork_block / seed addresses are missing: ask for them, then stop.
- do not claim/report a vulnerability until E3 proof passes:
  - reproducible on the pinned fork
  - any privileged effects are either not required or obtained permissionlessly within the sequence (not assumed)
  - net profit is materially large after itemized costs (report native units; optional USD-equivalent)
  - profitable under robustness perturbations (gas, liquidity, timing, ordering)

GROUNDING
- Code is a map. Fork behavior is the territory. When sources disagree, trust traces/state/balances.
- Never paste huge outputs in chat; store artifacts under <engagement_root> and cite paths.
- Keep memory compact: update <engagement_root>/memory.md every iteration.

OPERATING SYSTEM (PHASES A-F)
Phase A: Pin reality -> write index.yaml + memory.md
Phase B: Bundle address universe -> sources/ABI/proxies/evidence
Phase C: Traverse static maps -> deep graphs + storage surfaces + completeness checks
Phase D: Hypothesize sequences (open-world; no checklist limits) -> rank by path-to-delta
Phase E: Run ityfuzz campaigns -> iterate with cheapest discriminators
Phase F: Prove (E3) -> replay, custody+entitlement deltas, costs, robustness

SELF-EVALUATION LOOP (AFTER EACH PHASE/CAMPAIGN)
- What belief changed?
- What evidence was produced? (file paths)
- What is the single cheapest next discriminator?
- If no belief changes in 2 iterations: pivot to a different hypothesis corridor (auth bypass vs accounting vs oracle vs sequencing).

OUTPUT DISCIPLINE
- If not E3: do not claim a vulnerability. Provide only: current hypothesis + evidence + next experiment.
```
