---
name: tenderly-protocol-lab
description: "Tenderly-powered tracing, debugging, simulation, bundled multi-transaction simulation, and Virtual TestNet experimentation for EVM protocol security research. Use when you need decoded call traces/state diffs/asset changes, fork-grounded what-if experiments (state and block overrides), multi-tx same-block sequences (simulateBundle), multi-block sequence labs (Virtual TestNets + Admin RPC), or when you want to automate evidence collection/triage with Alerts, Web3 Actions, or Node Extensions."
---

# Tenderly Protocol Lab

## Overview
Use Tenderly as the "forensics + controlled experiment" layer in a protocol vuln workflow:
- Trace and decode real transactions (calls, events, state changes, asset/balance changes).
- Re-simulate with controlled overrides to test hypotheses cheaply and deterministically.
- Simulate multi-transaction sequences in one block (bundle sim).
- Run multi-block/time-sensitive sequences on Virtual TestNets with snapshots and cheatcodes.
- Validate fixes against production state by editing contract source and compiler settings in Simulator UI.

Positioning (avoid duplication):
- Use `sourcify-contract-bundler` for **sources/ABIs/proxies** and local project layout.
- Use `traverse-protocol-analysis` for **static maps** (deep call graphs, storage surfaces).
- Use `ityfuzz-protocol-hunter` for **sequence discovery** (searching unknown exploit chains).
- Use **Tenderly** for **evidence-grade traces + controlled simulations + multi-tx/multi-block labs** and for turning "maybe" into "provable".

## Setup (env + inputs)
Prefer environment variables; never hardcode secrets in repo artifacts.

Node RPC (JSON-RPC, includes custom methods like `tenderly_traceTransaction`):
- `TENDERLY_NODE_RPC_URL` (recommended): full HTTPS URL from the Tenderly dashboard.
  - Example shape (from docs): `https://mainnet.gateway.tenderly.co/$TENDERLY_NODE_ACCESS_KEY`
- OR `TENDERLY_NODE_ACCESS_KEY` + known network gateway prefix (only if you explicitly build URLs yourself).

Simulation API (REST, requires account/project slugs):
- `TENDERLY_ACCESS_KEY` (used as `X-Access-Key` header)
- `TENDERLY_ACCOUNT_SLUG`
- `TENDERLY_PROJECT_SLUG`

Virtual TestNets:
- `TENDERLY_VNET_RPC_URL` (regular VNet RPC from dashboard)
- `TENDERLY_VNET_ADMIN_RPC_URL` (Admin RPC from dashboard; required for cheatcodes like `tenderly_setBalance`)

## Capability router (choose one best tool per job)
Use this to prevent duplicate/overlapping approaches:

| Job | Primary tool | Why | Fallback |
|---|---|---|---|
| Trace a specific tx with decoded calls/state/asset changes | Tenderly `tenderly_traceTransaction` | Deterministic, decoded, easy evidence export | `debug_traceTransaction` on your own archive node |
| “What if I change X?” on a pinned block (state/time overrides) | Tenderly `tenderly_simulateTransaction` / Simulation API | Fast what-if with overrides + rich deltas | Local fork (anvil/foundry) with custom harness |
| Simulate a multi-tx atomic sequence (same block) | Tenderly `tenderly_simulateBundle` | Built for chained sequences; per-tx deltas | Local fork scripting (Foundry scripts) |
| Multi-block/time/epoch sequences with snapshots | Tenderly Virtual TestNet + Admin RPC | Snapshots + time/block controls + optional State Sync | Local fork with time-warp + snapshot/revert |
| Bulk historical evidence (wide ranges) | SQD in `sourcify-contract-bundler` | NDJSON at scale; good provenance | Explorer exports / custom indexer |
| Static reachable surface + storage touch map | Traverse | Global source map; don’t miss callables | Manual reasoning |
| Discover unknown exploit sequences | ItyFuzz | Search/heuristics/concolic | Manual hypothesis tests |

## Evidence layout (disk-first)
Store all Tenderly artifacts under an engagement directory (example OS uses `<engagement_root>`):
- `<engagement_root>/tenderly/rpc/` (trace/simulate JSON-RPC responses)
- `<engagement_root>/tenderly/api/` (simulation API responses, alerts payloads)
- `<engagement_root>/tenderly/links.md` (permalink list, if using UI)

Never paste huge Tenderly traces into chat. Persist JSON + summarize into `memory.md`.

## Workflows (copy/paste friendly)

### 0) UI fast path (optional): Dev Toolkit + Simulator UI
Use this when you need human-speed iteration:
- Dev Toolkit browser extension opens any explorer tx directly in Tenderly tooling.
- Simulator UI supports: re-simulate existing txs, override state/block headers, and edit contract source to validate fixes.

Evidence discipline still applies:
- export the evidence as JSON artifacts (Node RPC trace/simulate) under `<engagement_root>/tenderly/**`
- summarize only deltas into `memory.md`

### 1) Forensics: trace an existing transaction (decoded evidence)
Use Node RPC custom method `tenderly_traceTransaction` to export a decoded trace/state/asset changes as JSON.

Option A: use the generic RPC evidence script:
```bash
python scripts/tenderly_rpc_call.py \
  --rpc-url "$TENDERLY_NODE_RPC_URL" \
  --method tenderly_traceTransaction \
  --params-json '["0x<tx_hash>", "latest"]' \
  --out-dir "<engagement_root>/tenderly/rpc" \
  --label "trace-<tx_hash>"
```

Option B: raw curl:
```bash
curl "$TENDERLY_NODE_RPC_URL" -X POST -H "Content-Type: application/json" -d '{
  "jsonrpc":"2.0",
  "id":1,
  "method":"tenderly_traceTransaction",
  "params":["0x<tx_hash>", "latest"]
}'
```

What to extract into `memory.md`:
- Which contracts were touched (addresses + roles).
- Which storage variables changed (by address, slot, decoded if available).
- Where value moved (assetChanges/balanceChanges).
- The first “belief-changing” anomaly (invariant break, unexpected write ordering, etc.).

### 2) Controlled what-if: simulate a single tx (state + block overrides)
Use `tenderly_simulateTransaction` (RPC) or the Simulation API.

RPC (fastest path, one URL):
```bash
python scripts/tenderly_rpc_call.py \
  --rpc-url "$TENDERLY_NODE_RPC_URL" \
  --method tenderly_simulateTransaction \
  --params-file "<engagement_root>/notes/tenderly/simulate_single_params.json" \
  --out-dir "<engagement_root>/tenderly/rpc" \
  --label "sim-single"
```

Write `<engagement_root>/notes/tenderly/simulate_single_params.json` as a JSON array:
1) tx call object (`from`, `to`, `input`/`data`, optional gas fields)
2) block tag/number (`latest` or hex block)
3) (optional) state overrides map
4) (optional) block overrides object (timestamp, baseFee, etc.)

If you need mapping slot overrides: compute slots using Solidity layout rules (see references).

### 3) Atomic sequence: simulate a bundle (multi-tx, same block)
Use `tenderly_simulateBundle` via Node RPC (or `simulate-bundle` API).

```bash
python scripts/tenderly_rpc_call.py \
  --rpc-url "$TENDERLY_NODE_RPC_URL" \
  --method tenderly_simulateBundle \
  --params-file "<engagement_root>/notes/tenderly/simulate_bundle_params.json" \
  --out-dir "<engagement_root>/tenderly/rpc" \
  --label "sim-bundle"
```

Bundle params are a JSON array:
1) array of tx call objects (simulated sequentially)
2) block tag/number
3) (optional) state overrides map
4) (optional) block overrides object

Use this for:
- setup -> distort measurement -> realize -> unwind sequences in one block
- “tight loop” proofs where the measurement and redemption happen atomically

### 4) Multi-block lab: Virtual TestNet + Admin RPC cheatcodes
Use Virtual TestNets for sequences spanning blocks/time/epochs or requiring repeated fast setup.

Admin RPC methods (examples from docs):
- time and blocks: `evm_increaseTime`, `evm_setNextBlockTimestamp`, `tenderly_setNextBlockTimestamp`, `evm_increaseBlocks`, `evm_mine`
- snapshots: `evm_snapshot`, `evm_revert`
- balances/storage/code: `tenderly_setBalance`, `tenderly_addBalance`, `tenderly_setErc20Balance`, `tenderly_setStorageAt`, `tenderly_setCode`

Example: snapshot -> modify -> run tx -> revert:
```bash
# Take snapshot
python scripts/tenderly_rpc_call.py \
  --rpc-url "$TENDERLY_VNET_ADMIN_RPC_URL" \
  --method evm_snapshot \
  --params-json '[]' \
  --out-dir "<engagement_root>/tenderly/rpc" \
  --label "vnet-snapshot"

# Change ETH balance (cheatcode)
python scripts/tenderly_rpc_call.py \
  --rpc-url "$TENDERLY_VNET_ADMIN_RPC_URL" \
  --method tenderly_setBalance \
  --params-json '["0x<addr>", "0xDE0B6B3A7640000"]' \
  --out-dir "<engagement_root>/tenderly/rpc" \
  --label "vnet-set-balance"
```

State Sync rule (important): if you enable it, reads track parent chain until you write; written slots detach.

### 5) Precision helpers: decode inputs/errors/events when source is missing
Use Node RPC decode helpers when contracts aren’t verified:
- `tenderly_decodeInput`
- `tenderly_decodeError`
- `tenderly_decodeEvent`
- `tenderly_functionSignatures` / `tenderly_errorSignatures` / `tenderly_eventSignature`

Persist decode evidence the same way as traces (JSON-RPC responses under `<engagement_root>/tenderly/rpc`).

### 6) Unlock better decoding: verify contracts on Tenderly (optional)
Verification enables richer decoding, debugging, and Evaluate Expressions.
Use the verification method that matches your build system (Dashboard/Foundry/Hardhat).
On Virtual TestNets, the verifier URL is the VNet RPC URL with `/verify` appended (see references).

### 7) Automation: Alerts, Web3 Actions, Node Extensions (advanced)
Use these for:
- collecting evidence when a pattern happens on-chain
- automated triage / invariant checks / structured reporting

Rules:
- Treat these as evidence collectors and automation helpers, not “bug finders”.
- Keep outputs as saved JSON artifacts; summarize only deltas and decisions in `memory.md`.

## References (load only what you need)
- `references/tenderly-docs-index.md`: navigation map (official docs)
- `references/router.md`: non-duplicative routing matrix across providers and skills
- `references/node-rpc.md`: Node RPC URL/auth + custom methods + evidence fields
- `references/simulations.md`: single/bundle simulation payloads + overrides
- `references/virtual-testnets.md`: VNet workflow + Admin RPC methods + State Sync caveats
- `references/explorer-debugger.md`: Inspect Tx, Advanced Trace Search, Evaluate Expressions, Gas Profiler
- `references/simulator-ui-and-sandbox.md`: Simulator UI code editing + Sandbox prototyping workflows
- `references/alerts-actions-extensions.md`: Alerts API, Web3 Actions gateway access, Node Extensions patterns
- `references/contract-verification.md`: verification modes and endpoints
