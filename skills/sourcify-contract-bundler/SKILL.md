---
name: sourcify-contract-bundler
description: "Fetch and bundle Solidity contract sources, ABIs, and proxy/implementation mappings using Sourcify API v2, Etherscan API v2, and JSON-RPC, with optional SQD (SubSquid) Network evidence extraction (logs/txs/traces/state diffs). Use when you need to map protocol contracts (including proxies), download verified source trees, collect on-chain evidence, and store .sol files in Traverse-friendly layouts for graphing and analysis."
---

# Contract Bundler (Sourcify + Etherscan + RPC + SQD)

## Overview
Turn on-chain contract addresses into local, Traverse-ready bundles:
- Sources (`.sol`, single- or multi-file) + ABI
- Proxy/implementation mapping (Sourcify + Etherscan + EIP-1967 RPC)
- Optional evidence bundles from SQD Network (historical logs/txs/traces/state diffs)

Non-duplication note:
- Use this skill for **sources/ABIs/proxy mapping** and **bulk historical evidence** (SQD).
- For **per-transaction decoded traces, simulations, and bundled multi-tx experiments**, prefer `tenderly-protocol-lab` (Tenderly Node RPC / Virtual TestNets).

## Quick start
```bash
# Required: chain ID + address list
python scripts/fetch_contract_bundle.py \
  --chain-id 1 \
  --addresses 0x1234...,0xabcd... \
  --out analysis/contract-bundles \
  --etherscan-key $ETHERSCAN_API_KEY \
  --rpc-url $RPC_URL
```

Optional: also download SQD evidence (pick gateway by chain id using `sqd gateways list` or the public list):
```bash
python scripts/fetch_contract_bundle.py \
  --chain-id 1 \
  --addresses 0x1234... \
  --out analysis/contract-bundles \
  --sqd-network ethereum-mainnet \
  --sqd-types logs,transactions \
  --sqd-from-block 16000000
```

## Workflow (recommended)

### 1) Collect inputs
- Chain ID (e.g., `1`, `8453`).
- Seed addresses (protocol core contracts or a known registry).
- Etherscan API key if you want fallback coverage.
- RPC URL for proxy slot detection.
- SQD gateway URL or network slug (optional, for evidence extraction).

### 2) Run the bundler
Use `scripts/fetch_contract_bundle.py`.
- Query Sourcify first (`/v2/contract/...`) for sources + ABI.
- If missing, fall back to Etherscan for source + ABI.
- Resolve proxy implementations via Sourcify `proxyResolution`, Etherscan `Proxy/Implementation`, and EIP-1967 RPC slots.
- If SQD is configured, download evidence NDJSON under `chain-<id>/<addr>/sqd/`.

### 3) Review outputs
- `manifest.json` maps all discovered contracts and proxy relationships.
- Each contract is saved under `chain-<id>/<address>/` with:
  - `src/` (sources)
  - `abi/abi.json`
  - `metadata/` (raw API responses)
  - `rpc/slots.json` (proxy slot reads)
  - `sqd/` (optional evidence; queries + NDJSON results)

### 4) Run Traverse on bundles
- Use `chain-<id>/<address>/src` as Traverse input.
- For protocol-level graphs, only merge source trees when paths do not conflict.

## Script reference

### scripts/fetch_contract_bundle.py
Core options:
- `--chain-id` (required)
- `--addresses` or `--address-file` (required)
- `--out` (default: `analysis/contract-bundles`)
- `--sourcify-base` (default: `https://sourcify.dev/server`)
- `--sourcify-fields` (default: `all`)
- `--skip-sourcify`
- `--etherscan-base` (default: `https://api.etherscan.io/v2/api`)
- `--etherscan-key` (or `ETHERSCAN_API_KEY` env var)
- `--skip-etherscan`
- `--rpc-url` (or `RPC_URL` env var)
- `--skip-rpc`
- `--max-depth` (default: `2`) controls proxy-follow depth

SQD options (evidence):
- `--sqd-gateway <url>` or `--sqd-network <slug>`
- `--sqd-types logs,transactions,traces,stateDiffs`
- `--sqd-from-block <n>` / `--sqd-to-block <n>`
- `--sqd-evidence-depth <n>` (default `0` = only seed addresses)
- `--sqd-with-tx-logs` / `--sqd-with-tx-traces` / `--sqd-with-tx-state-diffs`

Examples:
```bash
# Address list file, no RPC
python scripts/fetch_contract_bundle.py \
  --chain-id 1 \
  --address-file analysis/addresses.txt \
  --etherscan-key $ETHERSCAN_API_KEY

# Sourcify only
python scripts/fetch_contract_bundle.py \
  --chain-id 1 \
  --addresses 0x1234... \
  --skip-etherscan --skip-rpc
```

### scripts/sqd_evm_dump.py
Use when you need a custom SQD Network EVM query beyond the bundler presets.

```bash
python scripts/sqd_evm_dump.py \
  --gateway https://v2.archive.subsquid.io/network/ethereum-mainnet \
  --query-file query.json \
  --out out.ndjson
```

## References
- `references/sourcify-api.md`: Sourcify API v2 endpoints and fields.
- `references/etherscan-api.md`: Etherscan getsourcecode/getabi parameters and responses.
- `references/rpc-proxy.md`: EIP-1967 slots and RPC methods.
- `references/output-layout.md`: output format and Traverse usage.
- `references/sqd-overview.md`: SQD ecosystem map (Network, SDK, Cloud, CLI).
- `references/sqd-cli.md`: install + `sqd gateways list`.
- `references/sqd-network-evm-api.md`: router/worker loop and query shape.
- `references/sqd-evm-requests.md`: logs/txs/traces/stateDiffs request shapes and field selection.
- `references/sqd-docs-index.md`: SQD docs navigation map for full feature coverage.
