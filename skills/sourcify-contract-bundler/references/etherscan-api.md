# Etherscan API v2 (contract source and ABI)

Official docs:
- https://docs.etherscan.io/api-reference/endpoint/getsourcecode
- https://docs.etherscan.io/api-reference/endpoint/getabi

Base endpoint:
- `https://api.etherscan.io/v2/api`

Get contract source code:
- `module=contract&action=getsourcecode&chainid=<id>&address=<addr>&apikey=<key>`

Get contract ABI:
- `module=contract&action=getabi&chainid=<id>&address=<addr>&apikey=<key>`

Required query params:
- `apikey`: Etherscan API key
- `chainid`: chain ID (e.g., 1, 8453)
- `module=contract`
- `action=getsourcecode` or `getabi`
- `address`: contract address

Notes on responses:
- `getsourcecode` returns `result` array with fields like:
  - `SourceCode`, `ABI`, `ContractName`, `CompilerVersion`, `OptimizationUsed`, `Runs`,
    `ConstructorArguments`, `EVMVersion`, `Library`, `LicenseType`, `Proxy`, `Implementation`.
- `SourceCode` can be:
  - a single Solidity file string, or
  - a JSON string containing `sources` (multi-file standard JSON input).
- When `Proxy` is `1` and `Implementation` is set, treat the contract as a proxy and enqueue the implementation address.
