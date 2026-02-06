# End-to-End Traverse Pipeline (Maximum Coverage)

Use this workflow to turn a full Solidity protocol into readable artifacts.

0) Preflight
- Install Traverse tools (brew or binaries).
- Install Graphviz for DOT rendering (`dot` command).
- Install Foundry if you plan to validate generated tests.

1) Pick the analysis root
- Prefer `--project <root>` and pass the Solidity source roots as inputs.
- If the repo has both `src/` and `contracts/`, include **both** so you don't miss callable surfaces.
- Avoid passing huge dependency trees unless you need them (e.g., `node_modules/`), but do include any in-repo packages that contain deployable contracts.

2) Generate interface bindings (sol2bnd)
```bash
sol2bnd <PROJECT_ROOT> -o bindings.yaml
```
- Keep `bindings.yaml` for use in sol2cg, sol2test, sol-storage-analyzer, and storage-trace.

3) Call graphs (sol2cg)
- Produce multiple passes for different zoom levels.

Overview:
```bash
sol2cg --config "max_depth=2,include_internal=false,include_modifiers=true,show_external_calls=true" \
  --bindings bindings.yaml <INPUT_PATH> -o callgraph-overview.dot
```

Deep analysis (full surface: do not miss internal + modifiers + external calls):
```bash
sol2cg --config "max_depth=50,include_internal=true,include_modifiers=true,show_external_calls=true" \
  --bindings bindings.yaml <INPUT_PATH> -o callgraph-deep.dot
```

External calls only:
```bash
sol2cg --config "max_depth=50,include_internal=false,include_modifiers=true,show_external_calls=true" \
  --bindings bindings.yaml <INPUT_PATH> -o callgraph-external.dot
```

Render DOT:
```bash
dot -Tsvg callgraph-overview.dot -o callgraph-overview.svg
```

Mermaid sequences with chunking:
```bash
sol2cg -f mermaid --chunk-dir mermaid-chunks \
  --bindings bindings.yaml <INPUT_PATH> -o sequence.mmd
```

Completeness sanity checks (do this when "don't miss anything" matters):
- Confirm **every public/external entrypoint** is present as a node in `callgraph-deep.*`.
  - If something is missing, the usual causes are: wrong input roots, unparsed files, or missing bindings/manifest for interface-heavy code.
- Confirm `fallback()` / `receive()` appear when the protocol uses them (proxy dispatch, ETH entrypoints).
- Search for dynamic dispatch that static graphs may under-approximate:
  - `delegatecall`, low-level `.call(...)`, `assembly`, and selector construction.
  - Treat those as "manual edges" and document them alongside the graph outputs.

4) Storage access surface (sol-storage-analyzer)
```bash
sol-storage-analyzer --bindings bindings.yaml <INPUT_PATH> -o storage-report.md
```

5) Storage-trace diffs (storage-trace)
- Compare paired functions that should be equivalent or upgrade-safe.
- Use `Contract.function` format when there are name collisions.

Template for a pairs file:
```
# func1,func2,paths(optional; use ';' to separate multiple paths)
Vault.deposit,Vault.depositFor,src/Vault.sol
TokenV1.transfer,TokenV2.transfer,src/
Manager.stake,Manager.stakeFor,src/
```

Run:
```bash
storage-trace --func1 Vault.deposit --func2 Vault.depositFor src/ -o deposit-vs-depositFor.md
```

6) Test scaffolding (sol2test)
```bash
sol2test --project <PROJECT_ROOT> \
  --use-foundry --validate-compilation \
  --config "include_reverts=true,include_events=true,test_edge_cases=true" \
  -o test/
```

7) Evidence bundle (recommended outputs)
- Call graphs: overview + deep + external (DOT + SVG)
- Mermaid sequence diagrams (chunked when large)
- Storage access report (markdown)
- Storage trace comparisons (markdown)
- Generated tests (Foundry)

Tip: keep all outputs under `analysis/traverse/` so they can be checked into an audit bundle without polluting the main repo.
