# Simulations (RPC + API) Notes

Sources of truth:
- Single simulations: https://docs.tenderly.co/simulations/single-simulations
- Bundled simulations: https://docs.tenderly.co/simulations/bundled-simulations
- State overrides: https://docs.tenderly.co/simulations/state-overrides
- RPC ref simulateTransaction: https://docs.tenderly.co/node/rpc-reference/ethereum-mainnet/tenderly_simulateTransaction
- RPC ref simulateBundle: https://docs.tenderly.co/node/rpc-reference/ethereum-mainnet/tenderly_simulateBundle

## A) Simulate via RPC (recommended default)
Pros:
- single endpoint (Node RPC URL)
- supports custom simulation methods
- good for evidence workflows (same JSON-RPC capture pattern)

### `tenderly_simulateTransaction`
Summary from RPC reference:
- simulates a tx as it would execute on a chosen block/tag
- supports state overrides (balances/storage/code/nonce) and block overrides
- returns decoded logs, decoded trace, assetChanges, stateChanges, balanceChanges, nonce change, and code change (when overriding code)

Parameters (conceptual):
1. Transaction call object:
   - `from`, `to`, `input` (or `data`), and optional gas fields
   - may include EIP-1559 fields (`maxFeePerGas`, `maxPriorityFeePerGas`) and access list
2. Block number or tag:
   - tag: `latest`, `earliest`, `pending`, `finalized`, `safe`
   - or hex quantity block number
3. State overrides map (optional):
   - keyed by address
   - fields may include: `balance`, `nonce`, `code`, `stateDiff` (slot->value)
4. Block overrides object (optional):
   - may include: `number`, `time`, `gasLimit`, `baseFee`, etc.

### `tenderly_simulateBundle`
Summary from RPC reference:
- simulates an array of tx calls sequentially in the same block
- returns an array of simulation results (per-tx), each with the same decoded evidence categories

Parameters (conceptual):
1. array of transaction call objects
2. block number/tag
3. state overrides map (optional)
4. block overrides object (optional)

## B) Simulate via API (when Node RPC is unavailable or when you need project-scoped saved sims)
Single simulation API endpoint (public network):
```
https://api.tenderly.co/api/v1/account/${TENDERLY_ACCOUNT_SLUG}/project/${TENDERLY_PROJECT_SLUG}/simulate
```

Single simulation API endpoint (Virtual TestNet):
```
https://api.tenderly.co/api/v1/account/${TENDERLY_ACCOUNT_SLUG}/project/${TENDERLY_PROJECT_SLUG}/vnets/{vnetId}/transactions/simulate
```

Auth header:
- `X-Access-Key: $TENDERLY_ACCESS_KEY`

Docs-required fields for single simulation payload:
- `network_id` (string)
- `block_number` (number or `latest`)
- `to` (string)
- `from` (string)
- `input` (string)
- `gas` (number)

Notes:
- simulations are unsigned; you can set arbitrary `from`.
- `simulation_type` can be `full`, `quick`, or `abi` (default: `full`).

Bundled simulation API endpoint:
```
https://api.tenderly.co/api/v1/account/${TENDERLY_ACCOUNT_SLUG}/project/${TENDERLY_PROJECT_SLUG}/simulate-bundle
```

Bundled payload shape:
- `simulations`: array of per-tx simulation objects (each has `network_id`, `from`, `to`, `input`, optional `state_objects`, plus save flags).

## C) State overrides (API terminology: `state_objects`)
Docs show overriding storage by specifying:
```json
{
  "state_objects": {
    "0x<contract>": {
      "storage": {
        "0x<slot>": "0x<value_32b>"
      }
    }
  }
}
```

Key operational note:
- storage slot calculation depends on Solidity layout rules (mapping keys, packed slots).
- Use Solidity storage layout docs for mapping/dynamic arrays.

## D) Gas estimation
Source of truth:
- https://docs.tenderly.co/simulations/gas-estimation

Docs describe two paths:
- Simulation API: set `estimate_gas: true` in the request payload to get gas estimates.
- Node RPC: use `tenderly_estimateGas` and `tenderly_estimateGasBundle` for 100% accurate estimates.

Security usage:
- Use accurate gas numbers for E3 cost accounting and gas-pressure edge cases (griefing paths).
