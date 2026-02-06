---
name: traverse-protocol-analysis
description: "End-to-end analysis of Solidity protocol codebases using the Traverse tool suite (sol2cg, sol2bnd, sol-storage-analyzer, storage-trace, sol2test). Use when you need call graphs, interface bindings, storage access maps, upgrade/refactor storage diffs, or Foundry test scaffolding for a full-protocol review."
---

# Traverse Protocol Analysis

## Overview
Use the Traverse tool suite to convert a Solidity protocol into readable artifacts: bindings, call graphs, storage access maps, storage diffs, and Foundry test scaffolds.

Coverage goal (important):
- Do not miss any **EOA-callable** or **contract-callable** surface:
  - all `public`/`external` functions (including proxy entrypoints where resolvable)
  - `fallback()` / `receive()` where present
  - internal/private functions reachable from those entrypoints
  - modifier bodies (they can hide external calls and state writes)

## Quick start (full pipeline)
1) Run `scripts/traverse_full_scan.sh` with `--project` and optional `--storage-pairs`.
2) Review outputs under `analysis/traverse/`.

Example:
```bash
scripts/traverse_full_scan.sh --project . --use-foundry --validate-compilation \
  --out <engagement_root>/traverse \
  --storage-pairs <engagement_root>/notes/storage-pairs.csv
```

## Workflow (maximum coverage)

### 1) Preflight
- Confirm Traverse tools are installed.
- Install Graphviz for DOT rendering (`dot`).
- Install Foundry if validating generated tests.
- Identify project root and primary source directory (`src/` or `contracts/`).

### 2) Interface resolution (sol2bnd)
- Generate `bindings.yaml` from NatSpec annotations.
- Pass `--bindings` (or `--manifest-file` if you have one) to all other tools.
- Consult `references/sol2bnd.md` for NatSpec formats and binding structure.

### 3) Call graphs and sequences (sol2cg)
- Run three passes: overview, deep (full surface), external-only focus.
- Treat `callgraph-deep.*` as the **authoritative** "don't miss anything" graph:
  - `max_depth` should be high enough to include multi-hop internal call chains
  - `include_internal=true`, `include_modifiers=true`, `show_external_calls=true`
- Output DOT + SVG and Mermaid (chunked for large diagrams).
- Consult `references/sol2cg.md` for config options and output formats.

Completeness sanity checks (recommended):
- Cross-check externally callable entrypoints against ABIs from `sourcify-contract-bundler` bundles (ABI is often the best "what can be called" ground truth onchain).
- Search the source tree for under-approximated edges:
  - `delegatecall`, low-level `.call(`, selector construction, inline `assembly`.
- If you have fork evidence (Tenderly traces/simulations), reconcile "contracts touched" with the call graph and expand your universe accordingly.

### 4) Storage access surface (sol-storage-analyzer)
- Produce a markdown report mapping reads/writes per function.
- Use this to isolate state mutation surfaces and high-risk paths.
- Consult `references/sol-storage-analyzer.md` for CLI details and report format.

### 5) Storage diffs (storage-trace)
- Compare function pairs that should be equivalent or upgrade-safe.
- Maintain a CSV of pairs and run them in batch.
- Consult `references/storage-trace.md` for required args and output format.

### 6) Test scaffolding (sol2test)
- Prefer project mode (`--project`) for Foundry repos.
- Enable `--use-foundry` and `--validate-compilation` when available.
- Tune `--config` for reverts/events/edge cases and use custom templates if needed.
- Consult `references/sol2test.md` for config options, templates, and CI hooks.

### 7) Evidence bundle
- Produce: call graphs (overview/deep/external), Mermaid sequences, storage report, storage-trace diffs, generated tests.
- Keep outputs under `analysis/traverse/` so they are easy to share or commit.
- Use `references/pipeline.md` as the canonical workflow checklist.

## Scripts
- `scripts/traverse_full_scan.sh`: Orchestrate the full pipeline with binding reuse, multi-pass graphs, storage reporting, optional storage-trace batches, and test generation.
- Use `--dry-run` to review generated commands before executing.

## References
- `references/pipeline.md`: end-to-end workflow and recommended deliverables.
- `references/sol2bnd.md`: bindings generation and NatSpec formats.
- `references/sol2cg.md`: call graph options and config table.
- `references/sol-storage-analyzer.md`: storage report structure and flags.
- `references/storage-trace.md`: function comparison usage and output.
- `references/sol2test.md`: test generation configuration, templates, and CI patterns.
