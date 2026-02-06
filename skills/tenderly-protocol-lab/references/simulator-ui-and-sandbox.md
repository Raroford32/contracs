# Simulator UI + Sandbox (Rapid Experimentation)

Sources of truth:
- Simulator UI overview: https://docs.tenderly.co/simulator-ui
- Editing contract source: https://docs.tenderly.co/simulator-ui/editing-contract-source
- Gas estimation (Simulation API): https://docs.tenderly.co/simulations/gas-estimation
- Tenderly Sandbox: https://docs.tenderly.co/tenderly-sandbox

## Simulator UI (interactive what-if)
Docs describe Simulator UI as an IDE-like experience for simulations:
- build a tx from scratch OR load an existing tx and "Re-Simulate"
- access decoded trace, accurate gas overview, asset/balance changes, and storage modifications
- override:
  - tx params (from/to/input, gas/gasPrice, etc.)
  - state variables (state overrides)
  - contract code (edit source)
  - block header values (block.number, block.timestamp)
  - sender (arbitrary `from` since sim is unsigned)
  - choose latest or historical block

Security workflow usage:
1. Start from a real tx (or a minimal tx that triggers a suspected bug).
2. Edit inputs until you can isolate the minimal trigger.
3. Apply state/block overrides to test boundary conditions quickly.
4. If you have a patch idea: edit the contract source and re-simulate against production state.
5. Once the behavior is pinned: move to a reproducible artifact (Node RPC simulation JSON + Foundry regression test).

## Editing contract source (patch validation against production state)
Docs explicitly call out:
- edit contract source "on the fly" while simulating/re-simulating
- change compiler parameters for simulation execution:
  - compiler version
  - optimization used
  - optimization count
  - EVM version
- add a custom contract source to any address (attach source to an address)
- type custom source from scratch for any address

Security workflow usage:
- use this to validate fixes and add temporary instrumentation (events/asserts) while keeping the chain state real.

## Gas estimation
Docs for Simulation API show:
- set `estimate_gas: true` in the simulation request to get gas estimates
- or use Node RPC methods:
  - `tenderly_estimateGas`
  - `tenderly_estimateGasBundle`

Security workflow usage:
- use accurate gas numbers for E3 cost accounting, griefing analysis, and gas-pressure edge cases.

## Tenderly Sandbox (rapid local-free prototyping)
Docs describe Sandbox as:
- browser-based Solidity + JavaScript environment
- execution uses Tenderly Forks in the background
- each run creates a temporary fork and 10 accounts funded with ETH
- you can load any resulting tx into Tenderly tooling (Debugger, trace, state changes, gas)
- includes environment configuration (network, block, compiler version, optimizations)
- supports dynamic imports from scoped npm packages (example: OpenZeppelin)

Security workflow usage:
- build tiny repro harnesses for a suspected accounting bug
- demonstrate an exploit skeleton without setting up a full repo
- share a minimal reproducer with collaborators (but keep engagement data private)

