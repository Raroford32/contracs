## understand the machine → derive what must be true → prove what isn't
## bundle -> map -> reason -> hypothesize -> execute -> prove
## Evidence-first • Feasibility-first • Composition-first • Fork-grounded • Reasoning-deep

This file is a **decision-complete runbook** for turning a protocol into **reviewable artifacts** (graphs, storage surfaces, source bundles, evidence) and then into **fork-grounded exploit proofs** (or falsified hypotheses) through **deep economic reasoning from first principles** using the installed skills.

Your targets are the vulnerabilities that survived multiple professional audits. They exist because they require understanding the protocol as a complete economic system, not as a collection of functions. No tool finds them. No checklist covers them. Only deep reasoning about the specific protocol's design reveals them.

Key intent: integrate **bundle -> map -> reason -> hypothesize -> execute -> prove** using the workspace skills:
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
- If all surface-level hypotheses are exhausted: re-enter Section 3.6.4 deep reasoning directives systematically — time, scale, emptiness/fullness, identity/confusion, information asymmetry, missing code, disagreement, incentive failure, reflexivity, ordering. Each directive is a new lens on the same protocol state. Record new hypotheses in `notes/hypotheses.md`.
- If composition opportunities exist (multiple protocols, shared state, token as both collateral and governance): apply Section 3.6.3 composition of violations — ask whether violation A enables violation B, whether cross-protocol state manipulation amplifies extraction.

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
  - <engagement_root>/notes/value-flows.md
  - <engagement_root>/notes/assumptions.md
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
- value flows (Section 3.6.1):
- assumptions (Section 3.6.2):
- hypotheses:

## Value Model Summary (custody vs entitlements)
- custody assets:
- entitlements:
- key measurements (prices/rates/indices/eligibility):
- key settlements (redeem/withdraw/liquidate/claim):
- solvency equation: [explicit mathematical relationship]

## Economic Model (Section 3.6)
- money entry points:
- money exit points:
- value transforms (where computation can err):
- fee extraction (from whom to whom):
- actor dual-roles identified:
- dependency gaps (guarantee vs assumption):
- top implicit assumptions (3-5 most dangerous):

## Top 3 Hypotheses (sequence archetypes)
1) <sequence hypothesis> (setup/distort/realize/unwind)
   - broken assumption:
   - reasoning chain depth: [N steps]
   - estimated extractable value:
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
- `notes/value-flows.md`: money entry→transform→exit chains, fee extraction points, actor model with dual-role analysis (Section 3.6.1).
- `notes/assumptions.md`: exhaustive assumption enumeration with violation conditions and consequences (Section 3.6.2).
- `notes/hypotheses.md`: active hypothesis set + backlog with reasoning chains and discriminator results.

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

# 3.6) Economic Reasoning Engine (FORGE-SENTINEL Core)

You have one process. You apply it with increasing depth until you find something or exhaust all avenues. There are no phases to skip, no shortcuts, no "check for known patterns" steps:

**Understand the machine → Derive what must be true → Prove what isn't.**

Everything in this section is about doing those three things at the deepest possible level of reasoning. This is the engine that drives Phase D hypothesis generation and Phase E campaign design. The toolchain (sections 2-3) produces the map. This section is how you THINK about the map.

## 3.6.1 Understand the Machine (Economic Modeling, Not Code Review)

Before you look for a single vulnerability, build the most complete possible understanding of what this protocol IS as an economic system.

### Money Flow Model

Trace every unit of value through the entire protocol. Not function calls — **value**.

Where does money enter? Not "the deposit function" — what economic action causes a human to send tokens to this contract? What do they expect in return? What promise is the protocol making them?

Where does money exit? Who can extract value and under what conditions? What determines how much they get? Is the amount they receive computed from the same information that was used when they entered, or has something changed?

What transforms happen between entry and exit? Value doesn't just sit in a contract — it gets lent, swapped, staked, split, merged, repriced, redenominated. Every transformation is an opportunity for the protocol to make an incorrect computation. Map every transformation.

Where does the protocol itself extract value? Fees, spreads, liquidation penalties, interest. Every fee is a redistribution — from whom to whom? Is the fee calculation correct in all edge cases? Does the fee extraction ever interfere with the core accounting?

Persist this model in `<engagement_root>/notes/value-flows.md` with explicit entry→transform→exit chains and fee extraction points.

### Actor Model

Who interacts with this protocol and why? For each actor: what do they want? What power do they have? What information do they have? What can they do that the protocol designer didn't fully consider?

Critical question: **can any actor play multiple roles simultaneously?** A user who is also a liquidator. A governance participant who is also a borrower. An oracle operator who is also a trader. Dual roles create conflicts of interest that the protocol may not defend against.

Can any actor's role be obtained temporarily via flash loans? If governance power comes from token holdings, it can be flash-borrowed. If liquidator priority comes from staked collateral, it can be flash-provided. If voting weight derives from LP positions, it can be flash-minted.

### Dependency Gap Analysis

For each external dependency: what exactly does the protocol expect from it? What interface does it call, what return values does it trust, what behavior does it assume?

Now: is that expectation guaranteed by the dependency, or merely typical? What's the difference between what the dependency **GUARANTEES** and what the protocol **ASSUMES**?

This gap — between guarantee and assumption — is where the most severe vulnerabilities live:
- A protocol that assumes an oracle is always fresh, when the oracle only guarantees updates above a deviation threshold.
- A protocol that assumes a token transfer always moves the exact amount specified, when the token only guarantees it won't revert.
- A protocol that assumes a DEX swap returns at least the minimum amount, when the DEX only guarantees it reverts below the minimum (but the minimum was computed from stale data).

The protocol treats the assumption as a guarantee, and the adversary exploits the gap.

### The Solvency Equation

Every protocol has one. Find it. Write it explicitly.

The solvency equation is the single mathematical relationship that, if violated, means the protocol cannot honor its obligations:
- Lending protocol: `total_collateral_value > total_debt_value`
- Vault: `sum(all_shares) * price_per_share <= total_assets`
- DEX: the invariant function (`xy=k`, StableSwap curve, concentrated liquidity position bounds)
- Insurance: `premium_pool + reserves >= max_outstanding_claims`
- Staking: `sum(user_stakes) + sum(pending_rewards) <= contract_balance + future_emissions`

Then ask: under what conditions can each term in this equation be manipulated independently of the others? If an adversary can increase the right side without increasing the left side (or decrease the left without decreasing the right), the protocol can be made insolvent.

Persist the solvency equation in `memory.md` under "Value Model Summary".

## 3.6.2 Derive What Must Be True (Assumption Enumeration)

From your understanding of the machine, derive every assumption the protocol depends on. Not known vulnerability categories — the specific, unique assumptions **THIS** protocol makes.

### Implicit Assumptions

The most dangerous assumptions are the ones nobody wrote down because they seemed obvious.

Read each function and ask: "What must be true about the state of the world for this function to produce a correct result?" Not just the `require` statements — those are the EXPLICIT assumptions. The implicit ones have no `require`. They're embedded in the math, in the order of operations, in the choice of which state variables to read.

A function that calculates `amount = balance * shares / totalShares` implicitly assumes:
- `totalShares > 0` (division by zero)
- `balance * shares` doesn't overflow (it might not revert in unchecked blocks)
- `balance` reflects reality (what if tokens were donated or rebased?)
- `shares` is a legitimate value (what if the share token has been manipulated?)
- the result represents a fair amount (what if the ratio was manipulated by a preceding action in the same block?)

That's five implicit assumptions in one line of arithmetic. Every function has dozens.

### Cross-Function Assumptions

Function A writes state. Function B reads state. The protocol assumes B will always see a consistent world left by A. But what if:

- A updates variable X but not Y, and B reads both?
- A is called by user 1, then B is called by user 2 in the same block, and A's state change makes B produce a wrong result for user 2?
- A has a require that ensures some property, but B can be called without going through A, so B lacks that guarantee?
- A was designed assuming B would be called next, but C can be called between them?

The space of cross-function assumption violations grows quadratically with the number of functions. For a protocol with 50 external functions, there are 2,450 ordered pairs. Each pair might have an assumption violation. This is why tools can't find these bugs — the search space is too large for anything except informed reasoning.

Cross-reference with `notes/entrypoints.md` to ensure no callable pair is missed.

### Cross-Protocol Assumptions

Each integration point is built on assumptions about the other protocol's behavior:

- **Semantically wrong:** The protocol assumes "transfer returns true on success" but calls a token that returns nothing.
- **Temporally wrong:** The protocol assumes "the oracle price is current" but the oracle only updates when price deviates >1%, so it can be stale for hours.
- **Economically wrong:** The protocol assumes "liquidation will happen when positions are underwater" but doesn't ensure liquidation is profitable, so nobody liquidates and bad debt accumulates.
- **Compositionally wrong:** The protocol works correctly in isolation but breaks when another protocol interacts with the same underlying state. Two lending protocols sharing a collateral token. A vault built on top of another vault. A governance token used as collateral in a lending market.

### State Assumptions Explicitly

For each assumption, write it as a precise statement in `notes/assumptions.md`:

```
ASSUMPTION: [SPECIFIC THING] is true
EVIDENCE IN CODE: [where in code this is relied upon]
VIOLATION CONDITION: [what must happen for this to be false]
CONSEQUENCE: [what goes wrong economically if violated]
VIOLATION FEASIBILITY: [can the adversary cause this?]
```

You cannot reason about violating assumptions you haven't stated. Be exhaustive. The more assumptions you surface, the larger your attack surface for hypothesis generation.

## 3.6.3 Prove What Isn't (Adversarial Violation Analysis)

For each assumption, determine whether an adversary can violate it.

### Adversarial Capability Model

Your adversary has:
- Unlimited capital for one transaction (flash loans from every major provider on the chain)
- Ability to execute arbitrary sequences of contract calls atomically
- Ability to interact with every public contract on the chain
- Ability to time their transaction relative to other pending transactions
- Ability to see the mempool (for front/back-running) — constrained by attacker tier in `notes/feasibility.md`
- Ability to interact with the target protocol from multiple addresses simultaneously
- **NO** access to private keys, admin roles, or off-chain infrastructure (unless obtained permissionlessly within the sequence)

For each assumption: can this adversary violate it using these capabilities?

### Depth of Reasoning (Chain Length)

Surface-level reasoning finds surface-level bugs. Novel vulnerabilities require chains of reasoning with 5, 10, 15 steps.

Don't ask "can the price be manipulated?" Ask: "What is the full causal chain from the adversary's first action to the extraction of value, and at each link in that chain, what is the concrete mechanism?"

Don't stop at "this value could be wrong." Trace exactly what happens downstream when the value is wrong. Which functions read it? What decisions do they make? How do those decisions differ from what they would have made with the correct value? Where does the difference in decisions create extractable value?

Don't accept "this looks safe because there's a check." What EXACTLY does the check verify? Is that sufficient? Does the check use the same data source as the computation it's protecting? Could the check pass with one value while the computation uses a different value that changed in between?

### Composition of Violations

The most severe vulnerabilities combine multiple assumption violations. After identifying individual violations, ask:

- Can violation A create the conditions that enable violation B?
- Can I violate assumption X in protocol A to create a false state, then use that false state to violate assumption Y in protocol B (the target)?
- Can I combine a timing violation with an economic violation to amplify the impact?

Compose violations iteratively. If A alone extracts $100 and B alone extracts $50, maybe A→B extracts $10M because A breaks a safety check that limits B's extraction.

### Value Extraction Tracing

For every viable violation, trace the value flow explicitly:

1. Where does the extracted value come from? (Which pool, vault, user, insurance fund)
2. How much can be extracted in one transaction?
3. Can the extraction be repeated? How many times? What limits it?
4. What is the total extractable amount relative to the protocol's TVL?
5. After gas costs and flash loan fees, is the net profit positive?

If you can't trace the value flow to a positive profit, the violation is interesting but not exploitable. Move on, but record the insight in `notes/hypotheses.md` backlog.

## 3.6.4 Deep Reasoning Directives (Apply When Initial Analysis Finds Nothing)

These are instructions for HOW TO THINK HARDER about specific aspects of protocol design. When your initial assumption enumeration and violation analysis produce no viable hypotheses, systematically apply each directive below to push reasoning deeper.

### Think About Time

Most analysis is static — "what's true right now." But protocols exist over time, and time creates vulnerabilities that don't exist in any single snapshot.

- What happens to this protocol over the next 1000 blocks? What accumulates? What drifts? What goes stale? Where do small errors compound into large ones?
- What happens if two operations that are supposed to happen together happen in different blocks? What state is the protocol in between them?
- What happens to time-dependent calculations at extreme durations? Interest that compounds for years. Rewards that accumulate for months. Vesting schedules that span epochs. Does the math still work at these timescales?
- What happens at time boundaries? Epoch transitions. Reward period rollovers. Oracle heartbeat intervals. Interest accrual boundaries. Governance voting periods. Every boundary is a potential discontinuity.

Use Tenderly Virtual TestNet time controls to test temporal hypotheses. Record temporal experiments in `notes/numeric-boundaries.md`.

### Think About Scale

- What happens when this operation is performed 10,000 times? Errors invisible at scale 1 become devastating at scale 10,000. Rounding that loses 0.01% per operation loses 63% over 10,000 operations.
- What happens when this value is 10^18 times larger than expected? Or 10^18 times smaller? Arithmetic that works for "normal" values may overflow, underflow, or lose all precision at extremes.
- What happens when there are 10,000 simultaneous users? State that seems isolated per-user might interact in unexpected ways when thousands of users act concurrently.

### Think About Emptiness and Fullness

- What happens when the pool is empty? First depositor, last withdrawer, zero liquidity. Protocols that work fine under normal conditions often have completely different code paths when a pool is empty or nearly empty.
- What happens when the pool is completely full? Maximum utilization, maximum leverage, all collateral slots taken.
- What happens at the transition between empty and non-empty, or between full and not-full? These transitions often have discontinuities that create extractable value.

Cross-reference with `notes/numeric-boundaries.md` — empty/full states are primary boundary experiment targets.

### Think About Identity and Confusion

- Can two different things be confused for each other by the protocol? Two tokens with the same symbol but different addresses. Two users who interact with the same pool in different roles. Two operations that modify overlapping state.
- Can the same thing appear to be two different things? A token that is both collateral in one market and debt in another. A user who has both a deposit and a borrow in the same pool. A contract that is both a price oracle and a liquidity pool.
- Can the absence of something be confused with a specific value? Uninitialized storage returning 0 vs an actual 0 balance. A mapping entry that was never set vs one that was explicitly set to the default. An enum value of 0 meaning "uninitialized" vs meaning the first valid state.

### Think About Information Asymmetry

- What does each actor know that other actors don't? A user who can see the mempool knows pending transactions. A keeper who monitors oracle updates knows when prices will change before the protocol does. A whale who controls significant liquidity knows the price impact of their own future trades.
- What information does the protocol REVEAL that it shouldn't? Do view functions expose values that could be used to optimize an attack? Can an attacker use the protocol's own getter functions to find the most profitable attack parameters?
- Does a failed transaction leak information about internal state?

### Think About What's Not There

The most important code to analyze is often code that DOESN'T EXIST.

- What check should be here but isn't? What validation is missing? What edge case has no handler? What error condition has no recovery path?
- What function SHOULD exist but doesn't? A way to handle accumulated dust. A way to recover from a bad oracle update. A way to pause a specific market without pausing the whole protocol.
- What state transition is missing? A position that can be opened but never closed under certain conditions. A reward that can be earned but never claimed. A deposit that can be made but never withdrawn.

### Think About Disagreement

Where do two parts of the protocol disagree about the same fact?

- Function A calculates a value one way. Function B calculates the "same" value a different way. Under normal conditions they agree. Under adversarial conditions they diverge. The protocol uses A's result for one decision and B's result for another, creating an inconsistency that can be exploited.
- The preview function says one thing. The execution function does another. Under normal conditions the difference is negligible. Under adversarial conditions the difference is enormous.
- The protocol's documentation says one thing. The code does another. Not a typo — a genuine semantic mismatch where the designer's mental model differs from what was implemented. These mismatches often survive audits because auditors check the code against the spec, and the spec itself is wrong.

### Think About Incentive Failure

Where does the protocol depend on someone doing something that isn't in their economic interest?

- Liquidators are supposed to liquidate. But what if liquidation isn't profitable at current gas prices? Bad debt accumulates.
- Keepers are supposed to update prices or trigger actions. But what if the gas cost exceeds the reward? The protocol assumes timely maintenance, but nobody is economically motivated to provide it.
- Users are supposed to claim their rewards. But what if unclaimed rewards create accounting problems?
- Governance is supposed to act in the protocol's interest. But what if governance token holders have misaligned incentives? Short sellers who hold governance tokens have an incentive to damage the protocol.

### Think About Reflexivity

- Can the protocol's own state be used as an input to manipulate the protocol? A token whose price is determined by a pool that the protocol itself deposits into. A governance vote whose outcome changes the value of the tokens used to vote.
- Can an attacker create a feedback loop? Borrow asset A → deposit A to inflate collateral value → borrow more → repeat. Each iteration amplifies the previous one until a constraint binds or the protocol breaks.
- Can the protocol be forced into a state where its own defense mechanisms make things worse? A liquidation cascade where each liquidation pushes the price lower, triggering more liquidations. A bank run where each withdrawal increases the loss for remaining depositors.

### Think About Ordering Within a Block

- Given two transactions in the same block, does the result depend on their order?
- Can the adversary ensure their transaction executes before or after a specific other transaction?
- What state changes between the adversary's setup transaction and their extraction transaction?
- Can the adversary sandwich a victim's transaction to extract value from the state change?

Cross-reference ordering analysis with `notes/feasibility.md` attacker tier constraints.

## 3.6.5 Assumption → Hypothesis Bridge (Feeding Phase D)

After completing the reasoning engine analysis, translate findings into Phase D hypotheses:

For each viable assumption violation:
1. State the broken assumption precisely
2. Define the full attack sequence: `setup → distort → realize → unwind`
3. Identify the entry→exit value flow
4. Estimate extractable value (order of magnitude)
5. List feasibility constraints (attacker tier, capital, timing, ordering)
6. Design the cheapest discriminator to test on fork

Write each as a structured hypothesis in `notes/hypotheses.md` and rank the top 3 into `memory.md`.

The reasoning engine produces the raw material. Phase D structures it. Phase E tests it. Phase F proves it.

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
6) **Pivot rule**: if two iterations do not change beliefs, pivot to a different hypothesis corridor (e.g., auth bypass vs accounting vs oracle vs sequencing) and redesign the discriminator. If all corridors are exhausted, re-enter Section 3.6.4 deep reasoning directives with a fresh lens (time, scale, emptiness, identity, information, absence, disagreement, incentive failure, reflexivity, ordering).

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
- Value model: custody vs entitlements written; measurement inputs (oracles/indices/decimals) explicit; **solvency equation stated explicitly**.
- Runtime reconciliation: at least one evidence-grade decoded trace/simulation exists for each top flow you're reasoning about.
- Economic model: `notes/value-flows.md` exists with money entry→transform→exit chains and actor dual-role analysis (Section 3.6.1).
- Assumption enumeration: `notes/assumptions.md` exists with at least one assumption per external function and violation feasibility assessed (Section 3.6.2).
- Deep reasoning directives: at least one pass through each applicable directive in Section 3.6.4 completed and insights recorded.

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

## Phase D — Hypothesis matrix (reasoning-driven; open-world; no checklist limits)

**Pre-requisite:** Before generating hypotheses, ensure Section 3.6 reasoning engine analysis is complete:
- Money flow model written (`notes/value-flows.md`)
- Actor model with dual-role analysis completed
- Dependency gap analysis (guarantee vs assumption) for all external dependencies
- Solvency equation stated explicitly in `memory.md`
- Assumption enumeration completed (`notes/assumptions.md`)
- Adversarial violation analysis run against each assumption
- Deep reasoning directives applied (time, scale, emptiness/fullness, identity/confusion, information asymmetry, missing code, disagreement, incentive failure, reflexivity, ordering)

1) Generate 3-10 candidate sequences from the reasoning engine outputs AND any signal source:
   - **assumption violations** with viable adversarial paths (Section 3.6.3)
   - **deep reasoning directive outputs** (Section 3.6.4) — particularly composition of violations
   - **solvency equation manipulation paths** — each term that can be independently influenced
   - **dependency gap exploits** — where protocol assumption exceeds dependency guarantee
   - static maps (Traverse call graph + storage writes)
   - runtime evidence (Tenderly traces/sims)
   - fuzz evidence (ItyFuzz artifacts)
2) For each hypothesis, record:
   - **broken assumption** (precise statement from `notes/assumptions.md`)
   - **economic reasoning chain** (the full multi-step causal chain from adversary's first action to value extraction — this is the valuable part, not just the finding but HOW you found it)
   - **value extraction trace** (from which pool/vault/user, how much, repeatable?)
   - entrypoints used (reference `notes/entrypoints.md`)
   - callsites/dispatch used if relevant (reference `notes/taint-map.md`)
   - token assumptions if relevant (reference `notes/tokens.md`)
   - numeric boundary leveraged if relevant (reference `notes/numeric-boundaries.md`)
   - sequence description: `setup → distort → realize → unwind` (do not force-fit if it doesn't match)
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
7) Only then: write an E3 report using the structured format below.

### E3 Finding Format (mandatory structure)

```
FINDING: [what breaks, in plain economic language]

BROKEN ASSUMPTION:
  [precise statement of what the protocol assumes that isn't true]

ECONOMIC REASONING CHAIN:
  [the full chain of reasoning that led to discovery — this is the valuable
   part, not just the finding itself but HOW you found it, because the
   reasoning process should be reproducible on other protocols]
  Step 1: [observation about protocol design]
  Step 2: [derived assumption]
  ...
  Step N: [violation → value extraction]

ATTACK SEQUENCE:
  [step-by-step with contract addresses and function calls]
  Setup: [flash loan, position creation, state manipulation]
  Distort: [the core violation — what breaks the assumption]
  Realize: [extraction of value through the broken invariant]
  Unwind: [repayment of flash loans, closing of positions]

VALUE EXTRACTED:
  [how much, from whom, under what conditions]
  Gross: [total value moved to attacker]
  Costs: [gas + flash fees + slippage + MEV/bribes]
  Net: [profit in native units + optional USD-equivalent]
  Repeatability: [once / N times / unlimited until TVL drained]

PROOF OF CONCEPT:
  [Foundry fork-test path under <engagement_root>]
  [Tenderly evidence artifact paths]

ROBUSTNESS:
  [results of gas+20%, liquidity-20%, timing+1block, weaker ordering tier]

WHY THIS SURVIVED PRIOR AUDITS:
  [what reasoning was required that pattern-matching wouldn't produce —
   the depth of the chain, the cross-function/cross-protocol composition,
   the implicit assumption that seemed too obvious to check]

FIX:
  [minimal code change that eliminates the broken assumption]
```

### Unvalidated Hypothesis Format (record all failed attempts)

```
HYPOTHESIS: [what might break]
BROKEN ASSUMPTION (hypothesized): [what you thought wasn't true]
REASONING CHAIN: [the multi-step logic that led to this hypothesis]
FAILED BECAUSE: [what stopped the PoC — defense mechanism, wrong
  assumption about state, arithmetic didn't work out, etc.]
EVIDENCE: [artifact paths showing the failure]
INSIGHT: [what you learned that's useful for future analysis —
  which defense worked, which assumption held, what was surprising]
```

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
Phase C+: Economic reasoning engine (Section 3.6) -> money flows, actor model, dependency gaps, solvency equation, assumption enumeration, adversarial violation analysis, deep reasoning directives
Phase D: Hypothesize sequences (reasoning-driven + open-world; no checklist limits) -> rank by path-to-delta
Phase E: Run ityfuzz campaigns -> iterate with cheapest discriminators
Phase F: Prove (E3) -> replay, custody+entitlement deltas, costs, robustness -> structured finding format

SELF-EVALUATION LOOP (AFTER EACH PHASE/CAMPAIGN)
- What belief changed?
- What evidence was produced? (file paths)
- What is the single cheapest next discriminator?
- If no belief changes in 2 iterations: pivot to a different hypothesis corridor (auth bypass vs accounting vs oracle vs sequencing).
you can allways get help from guidebook.md !
OUTPUT DISCIPLINE
- If not E3: do not claim a vulnerability. Provide only: current hypothesis + evidence + next experiment.
```
