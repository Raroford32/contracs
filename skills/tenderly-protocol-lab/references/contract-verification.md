# Contract Verification (Unlock Decoding + Debugging)

Source of truth:
- https://docs.tenderly.co/contract-verification

## Why verification matters for security work
Verified contracts unlock:
- decoded call traces/events/state changes
- better debugging and source mapping
- gas profiling by function/opcode
- Evaluate Expressions workflows

## Supported methods
Per docs, Tenderly supports multiple methods:
- Dashboard verification (quick, limited customization)
- Foundry verification
- Hardhat verification

## Etherscan-compatible verification API
Docs state Tenderly exposes an Etherscan-compliant verification API for:
- public networks accessible through Node RPC
- Virtual TestNets

## Virtual TestNets verifier URL
Docs describe a VNet verifier URL convention:
- append `/verify` to the VNet RPC URL

Example (from docs):
```
https://virtual.base.rpc.tenderly.co/<vnet-uuid>/verify
```

## Visibility modes
Docs describe:
- public verification (default on public networks)
- private verification (only visible in your org/project)

Practical note:
- use private verification when working on sensitive audit engagements.

