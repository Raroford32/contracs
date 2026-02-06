# Output layout (Traverse-friendly)

Default output structure:

out/
  manifest.json
  chain-<chainId>/
    <address>/
      info.json
      metadata/
        sourcify-contract.json
        etherscan-source.json
      abi/
        abi.json
      src/
        <source paths...>
      rpc/
        slots.json
      sqd/
        config.json
        queries/
          *.json
        results/
          *.ndjson

Guidelines:
- Preserve original source paths from `sources` so Solidity imports remain correct.
- For single-file source strings, write `src/<ContractName>.sol` (fallback to `Contract.sol`).
- Keep ABI as `abi/abi.json` for tooling compatibility.
- `manifest.json` maps addresses to their output directories and proxy relationships.
- SQD evidence outputs are optional; use NDJSON to stream large per-block responses.

Traverse usage:
- Run Traverse tools per address folder (input path = `chain-<id>/<address>/src`).
- For protocol-level graphs, group addresses from the same repo and merge only when file paths do not conflict.
