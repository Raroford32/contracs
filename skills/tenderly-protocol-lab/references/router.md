# Non-Duplicative Routing Matrix (Tenderly vs SQD vs Raw RPC vs Local Fork)

Goal: maintain one "best tool" per job, with explicit fallback order. This prevents drift into multiple overlapping pipelines.

## Primary selection rules
- Prefer **Tenderly** when you need **decoded** traces/sims and evidence artifacts quickly.
- Prefer **SQD** (via `sourcify-contract-bundler`) when you need **bulk historical** data over wide block ranges.
- Prefer **local forks** (anvil/foundry) when you need **tight integration with fuzzing/harnesses**, custom instrumentation, or offline determinism.
- Prefer **raw RPC** only as a fallback when Tenderly is unavailable or when you need a node-specific feature.

## Jobs -> tool

### A) Transaction evidence
- Single tx decoded trace + state changes + asset changes:
  - Primary: Tenderly `tenderly_traceTransaction`
  - Fallback: `debug_traceTransaction` on an archive node (Erigon/Geth) + manual decode

- Decode unknown selectors/errors/events (unverified contracts):
  - Primary: Tenderly decode helpers (`tenderly_decodeInput`, `tenderly_decodeError`, `tenderly_decodeEvent`, signature lookup)
  - Fallback: local signature DB (4byte) + ABI guess + manual inspection

### B) Controlled experiments
- Single-transaction what-if, including state overrides and block overrides:
  - Primary: Tenderly `tenderly_simulateTransaction` (RPC) or Simulation API
  - Fallback: local fork + `cast call`/Foundry script + custom storage writes

- Multi-transaction same-block sequence:
  - Primary: Tenderly `tenderly_simulateBundle`
  - Fallback: local fork script executing sequential txs in one block (harder; more plumbing)

- Multi-block/time/epoch experimentation:
  - Primary: Tenderly Virtual TestNet + Admin RPC (`evm_snapshot`, time controls, `tenderly_setBalance`, etc.)
  - Fallback: local anvil + snapshot/time-warp + custom state setup

### C) Bulk / historical
- Many txs, broad time windows, evidence provenance at scale:
  - Primary: SQD (Network) dumps under `sourcify-contract-bundler`
  - Fallback: custom indexer, explorer exports

### D) Codebase comprehension / surface completeness
- Static reachable surface, internal reachability, storage touch maps:
  - Primary: Traverse deep graphs + storage analyzer
  - Fallback: manual review + targeted greps + traces

### E) Discovery
- Find unknown cross-contract exploit sequences:
  - Primary: ItyFuzz campaigns on a pinned fork
  - Fallback: hypothesis-driven manual sequences + targeted simulations

## Evidence consistency contract (recommended)
If you use Tenderly for evidence:
- Save every trace/simulation response JSON under `<engagement_root>/tenderly/**`.
- Store the command used and the artifact path in `index.yaml`.
- Summarize only the belief-changing deltas in `memory.md`.

