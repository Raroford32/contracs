# Alerts, Web3 Actions, Node Extensions (Automation Layer)

Sources of truth:
- Alerts API: https://docs.tenderly.co/alerts/api
- Web3 Actions Node RPC access: https://docs.tenderly.co/web3-actions/references/web3-gateway-access
- Node Extensions: https://docs.tenderly.co/node/node-extensions

## When to use these (in vuln research)
Use these to:
- collect on-chain evidence when suspicious sequences occur
- automate invariant checks / triage over traces
- build protocol-specific analysis endpoints (Node Extensions) that return structured reports

Do not use these as your "primary discovery engine". Discovery is still ItyFuzz + hypothesis work.

## Alerts API (simple + complex)
Docs define:
- simple alert: one expression
- complex alert: multiple expressions; triggers only when all expressions match
- delivery channels are configured in the dashboard; can be fetched via API

Auth pattern in docs:
- API base: `https://api.tenderly.co/api/v1`
- header: `X-Access-Key: $TENDERLY_ACCESS_KEY`

Expression types (selection relevant to security; see docs for the full table):
- `method_call`: monitor a function call (line_number + call_position)
- `contract_address`: monitor interactions with a contract (direct/source/internal)
- `state_change`: monitor storage/parameter changes with conditions
- `emitted_log`: monitor specific events with parameter filtering
- `tx_status`: monitor success/failure
- `tx_error` / `tx_internal_error`: monitor errors
- `sandwich_transaction`: monitor sandwich patterns
- `no_action`: inactivity / dormancy detection

Research pattern:
1. encode a suspicious invariant as an alert condition
2. deliver to webhook (or Web3 Action trigger)
3. enrich alert evidence by tracing/simulating the tx and storing JSON artifacts

## Web3 Actions (serverless execution)
Docs show Node RPC access in Web3 Actions via:
- `context.gateways.getGateway(Network.MAINNET)` (Network enum in `@tenderly/actions`)
- use an ethers provider against that gateway URL inside the action function

Use Web3 Actions to:
- run a trace/simulate call after an alert triggers
- compute a lightweight invariant delta and store it as an artifact

## Node Extensions (custom `extension_*` RPC)
Docs define:
- Node Extensions run through Node RPC
- method names are prefixed with `extension_`
- you can build from scratch, repurpose a Web3 Action, deploy from a library, or deploy via CLI
- secrets can be retrieved via `await context.secrets.get('API_KEY')`

Security pattern (high leverage):
- implement a protocol-specific RPC method:
  - input: tx hash(s) or call bundle
  - body: trace/simulate -> compute deltas (custody vs entitlements) -> return JSON report
- call `extension_<name>` as part of the E3 proof pipeline so reporting is reproducible

