# Sourcify API v2 (contract lookup and verification)

Official docs:
- https://docs.sourcify.dev/docs/api/
- Swagger: https://sourcify.dev/server/api-docs/swagger.json

Primary endpoints used by this skill:

Contract lookup
- `GET /v2/contract/{chainId}/{address}`
  - Use `?fields=all` to retrieve full details including `sources`, `abi`, `metadata`, `stdJsonInput`, `proxyResolution`.
  - Use `fields=abi` or other comma-separated paths to limit payload.
  - Use `omit=` to exclude fields.
- `GET /v2/contract/all-chains/{address}`: same address across chains.
- `GET /v2/contracts/{chainId}`: list verified contracts (supports `limit`, `sort`, `afterMatchId`).

Verification (optional, when needed)
- `POST /v2/verify/{chainId}/{address}` (standard JSON input)
- `POST /v2/verify/metadata/{chainId}/{address}` (metadata.json)
- `POST /v2/verify/etherscan/{chainId}/{address}` (import from Etherscan)
- `POST /v2/verify/similarity/{chainId}/{address}` (similarity search)
- `GET /v2/verify/{verificationId}` (poll verification job)

Useful response fields for bundling:
- `sources`: map of file paths to `{ content }` entries
- `abi`: array ABI
- `metadata`: Solidity metadata.json
- `stdJsonInput`: standard JSON input (includes `sources` + `settings`)
- `compilation`: compiler version, language, fully qualified name
- `proxyResolution`: `isProxy`, `proxyType`, `implementations[]`

Notes:
- `proxyResolution` is computed on-the-fly using bytecode analysis; use it to enqueue implementation addresses.
- When `sources` are present, write each file to disk using its path to preserve imports.
