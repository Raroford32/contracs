# PLANS.md — Minimal-Skill Solver Decision Engine

Purpose: a solver-first decision engine that prevents narrative loops. Every step must either (a) improve the semantic model, (b) produce a constraint program, or (c) run experiments that yield witnesses. It continues until E3.

---

## Core posture (non-negotiable)

1. **Never conclude safety.** Only E3 ends the run.
2. **No narrative progress.** If no experiment was run, the iteration does not count.
3. **Complexity-first.** Increase constraint hardness and multi-lever composition, not prose.
4. **Evidence-first.** Anything important is written to artifacts.
5. **No closed taxonomies.** All behavior fields are open vocabulary.

---

## Decision policy (autonomous; no user prompts)

When multiple valid options exist, decide automatically using this order:
1. **Convergence delta** (measurable move toward exploit feasibility or reachability).
2. **Evidence gain toward E3** (new experiments/witnesses).
3. **Novelty / dedup discipline** (avoid repeating the same dedupKey or solver corridor).
4. **Maximum impact potential** (largest extractable delta).
5. **Constraint hardness** (more independent levers fused).
6. **Permissionless feasibility** (fewer privileged assumptions).

If still tied, pick the option that expands the least-covered surface.

---

## Routing guarantees (non-negotiable)

- **PLANS.md is the canonical router.** Skills produce artifacts; PLANS chooses the next step.
- **Every gap maps to a skill.** Missing artifact or blocker must trigger a skill or be logged in `unknowns.md` with a resolution plan.
- **No autonomous termination except E3.** Checkpoints emit `resume_pack.md` and continue.
- **No drift allowed.** `focus.md` must always name the current goal + next skill; update it whenever you feel lost.
- **Continuous convergence is mandatory.** Any iteration without `convergence_delta > 0` is invalid and must trigger stall recovery.

---

## Skill routing table

| Gap/Need | Skill | Path | Output |
|----------|-------|------|--------|
| System integrity + rigor gate | system-governor | `/root/.codex/skills/system-governor/SKILL.md` | system_evaluation.md + lint results |
| Boundary + graphs + state machine | world-modeler | `/root/.codex/skills/world-modeler/SKILL.md` | boundary/graphs/state_machine + deployment_snapshot.md |
| Property portfolio + constraint programs | property-portfolio-compiler | `/root/.codex/skills/property-portfolio-compiler/SKILL.md` | properties/* + hypotheses/*.yaml |
| Experiments + witnesses | counterexample-solver | `/root/.codex/skills/counterexample-solver/SKILL.md` | experiments.jsonl + replay bundle candidates |
| Proof pack + E2/E3 | proofpack-builder | `/root/.codex/skills/proofpack-builder/SKILL.md` | replay bundles + Foundry falsifier + report |

---

## Decision engine (select next step)

Execute the first matching rule:

```
RULE 0: System integrity (global)
  IF starting a new investigation OR system files changed
  THEN invoke skill: system-governor
  THEN run mandatory rigor gate (must pass):
    - `python3 <workspace>/scripts/lint_skills_operations.py --root <workspace>`
    - `python3 <workspace>/scripts/lint_hypothesis_ledger.py --path <workspace>/hypothesis_ledger.md`
    - `python3 <workspace>/scripts/lint_constraint_programs.py --root <workspace> --strict-feasibility`
    - `python3 <workspace>/scripts/lint_trajectory.py --root <workspace>`
    - `python3 <workspace>/scripts/lint_replay_bundles.py --root <workspace>`
    - `python3 <workspace>/scripts/lint_experiments.py --root <workspace>`
    - `python3 <workspace>/scripts/lint_coverage_scoreboard.py --root <workspace>`
    - `python3 <workspace>/scripts/lint_focus_card.py --root <workspace>`
  OUTPUT: system_evaluation.md must be clean
  NOTE: Decisions and scores must be recorded to `memory/decision_trace.jsonl`.

RULE 1: Boundary / graphs / state machine missing?
  IF missing `boundary/manifest.json` OR missing any `graphs/*.json` OR missing `state_machine.md`
  THEN invoke skill: world-modeler
  OUTPUT: boundary/graphs/state_machine + deployment_snapshot.md

RULE 2: Property portfolio missing?
  IF missing `properties/portfolio.yaml` OR missing `properties/assumptions.yaml`
  THEN invoke skill: property-portfolio-compiler
  OUTPUT: properties/* + hypotheses/*.yaml + ledger updates

RULE 3: Constraint programs missing?
  IF any hypothesis row lacks a matching `hypotheses/<scenarioId>.yaml`
  THEN invoke skill: property-portfolio-compiler
  OUTPUT: hypotheses/*.yaml completed

RULE 4: Experiment gate (no narrative progress)
  IF experiments.jsonl has no entries for any active targetStateX OR last iteration produced only artifacts
  THEN invoke skill: counterexample-solver
  OUTPUT: experiments.jsonl + replay bundle candidates + ledger updates

RULE 4b: Convergence gate (no stagnant iterations)
  IF last experiment has no `convergence_delta` OR all deltas are 0
  THEN force constraint expansion + new experiment run
  OUTPUT: updated constraints + experiments.jsonl with convergence_delta>0

RULE 5: Witness exists?
  IF replay_bundles/candidates exists OR E1/E2 achieved
  THEN invoke skill: proofpack-builder
  OUTPUT: canonical replay bundles + Foundry falsifier; E2/E3 update

RULE 6: E3 achieved?
  IF any hypothesis is E3 with measurable delta
  THEN invoke skill: proofpack-builder
  OUTPUT: final_report.md
  STOP (success)

RULE 7: Stall detected?
  IF no evidence upgrade after N iterations
  THEN force constraint expansion:
    - add independent levers (state shaping + settlement/extraction)
    - add boundary crossing (module/external/ordering/control-plane)
    - widen variable set and re-run counterexample-solver
  OUTPUT: updated constraints + new experiments
```

---

## Quick start (do this immediately)

0) Hydrate a new workspace:
   ```bash
   python3 /root/.codex/skills/system-governor/scripts/init_investigation_workspace.py --path <workspace> --hydrate --verbose
   ```

1) Run the system evaluator:
   ```bash
   python3 /root/.codex/skills/system-governor/scripts/evaluate_system.py \
     --root <workspace> \
     --skills-root /root/.codex/skills \
     --out <workspace>/system_evaluation.md
   ```

2) Run the rigor gate lints:
   ```bash
   python3 <workspace>/scripts/lint_skills_operations.py --root <workspace>
   python3 <workspace>/scripts/lint_hypothesis_ledger.py --path <workspace>/hypothesis_ledger.md
   python3 <workspace>/scripts/lint_constraint_programs.py --root <workspace>
   python3 <workspace>/scripts/lint_trajectory.py --root <workspace>
   python3 <workspace>/scripts/lint_replay_bundles.py --root <workspace>
   python3 <workspace>/scripts/lint_experiments.py --root <workspace>
   python3 <workspace>/scripts/lint_coverage_scoreboard.py --root <workspace>
   python3 <workspace>/scripts/lint_focus_card.py --root <workspace>
   ```

3) Start the Decision Engine from RULE 1.

4) Continue until E3 (no user prompts).

---

## Stop conditions (autonomous termination)

SUCCESS only:
- An E3-promoted scenario exists with measurable economic delta.

Checkpoint behavior (non-terminating):
- Emit `resume_pack.md` and continue next session.

RPC policy: use `rpc-etherscan.md` for RPC endpoints. Source/ABI policy: prefer **Sourcify v2 first**; explorer APIs optional; never write secrets into artifacts.
