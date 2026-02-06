# Node RPC (Official Docs Notes)

Source of truth:
- https://docs.tenderly.co/node
- https://docs.tenderly.co/node/rpc-reference

## Endpoint + auth
Node RPC is accessed via a unique HTTPS (and optional WS) URL created in the Tenderly dashboard.

Docs show an example URL shape for Ethereum mainnet:
- `https://mainnet.gateway.tenderly.co/$TENDERLY_NODE_ACCESS_KEY`

Treat the full URL as the secret-bearing endpoint. Prefer storing it in:
- `TENDERLY_NODE_RPC_URL`

## Custom RPC methods (security-relevant)
Per docs, Tenderly exposes custom methods in addition to standard EVM RPC:
- `tenderly_simulateTransaction`: simulate a tx with optional overrides
- `tenderly_simulateBundle`: simulate multiple txs sequentially in one block
- `tenderly_traceTransaction`: decoded trace of an existing tx
- `tenderly_estimateGas`: accurate gas usage for a given tx
- `tenderly_estimateGasBundle`: accurate gas usage for a bundle
- Decode helpers:
  - `tenderly_decodeInput`
  - `tenderly_decodeError`
  - `tenderly_decodeEvent`
  - `tenderly_functionSignatures`
  - `tenderly_errorSignatures`
  - `tenderly_eventSignature`

These methods typically return decoded:
- call traces
- logs/events
- state changes
- asset/balance changes

## JSON-RPC request skeleton
```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "method": "tenderly_traceTransaction",
  "params": ["0x<tx_hash>", "latest"]
}
```

Persist both request and response JSON as evidence artifacts (do not paste into chat).

## "Why Node RPC beats raw trace RPC for research"
- You get decoded artifacts (calls/logs/state/asset changes) without maintaining your own decode pipeline.
- You can simulate and trace from the same RPC URL (less infra glue).

## Related docs
- Node Extensions (custom `extension_*` methods executed through Node RPC): https://docs.tenderly.co/node/node-extensions

