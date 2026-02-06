# Offchain Config Schema (`--offchain-config-file/url`)

ItyFuzz supports an advanced offchain deployment mode that pins:
- deterministic **deployment addresses**, and
- ABI-encoded **constructor args** (as hex)

This mode is driven by:

- `--offchain-config-file <path>` or `--offchain-config-url <url>`
- plus build artifacts (via `--builder-artifacts-*` or a `BUILD_COMMAND` like `-- forge build`)

## JSON shape (exact)

Top-level object:

- keys: **Solidity source filename** strings (as they appear in build artifacts)
- values: objects mapping **contract name** -> config object

Config object fields:

- `constructor_args`: string
  - hex **without** `0x` prefix is accepted
  - if you include `0x`, ItyFuzz strips it
  - this is the ABI-encoded constructor arguments *only* (no bytecode)
- `address`: string
  - hex address (e.g. `0x1234...`)

Example:

```json
{
  "src/MyProtocol.sol": {
    "MyProtocol": {
      "constructor_args": "0000000000000000000000000000000000000000000000000000000000000042",
      "address": "0x1000000000000000000000000000000000000001"
    }
  },
  "src/Token.sol": {
    "Token": {
      "constructor_args": "0x", 
      "address": "0x1000000000000000000000000000000000000002"
    }
  }
}
```

## When to use this

Use offchain config when:
- your protocol uses **hard-coded addresses** (registries, routers, proxies), and
- you need those addresses to match what the contracts expect, and/or
- you need constructor args that are difficult to express via `--constructor-args` (human-readable mode).

Avoid offchain config when:
- you can deploy in `glob` mode + `--constructor-args`, or
- you can use a Foundry `--deployment-script` harness to do setup in Solidity.

## Common failure modes

- Filename/contract name mismatch vs build artifacts:
  - The key must match what the artifacts use (often includes `src/` prefixes).
- Constructor args not ABI-encoded:
  - This file expects raw ABI encoding (hex bytes), not comma-separated values.
- Missing build artifacts:
  - Config mode requires artifacts so ItyFuzz can locate deploy bytecode + ABI per `(file, contract)`.

