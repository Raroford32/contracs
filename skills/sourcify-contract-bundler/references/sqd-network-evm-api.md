# SQD Network EVM API (router/worker pattern)

Official reference:
- https://docs.sqd.ai/subsquid-network/reference/evm-api/

Concepts
- A gateway URL (router) distributes queries across workers.
- Router endpoints:
  - `GET /height` -> dataset height (highest available block)
  - `GET /<block>/worker` -> returns a worker URL that serves the range containing `<block>`
- Worker endpoint:
  - `POST /` (POST to the returned worker URL) with a JSON query.

Recommended fetch loop
1) `height = GET <gateway>/height`
2) `current = fromBlock`
3) While `current <= min(toBlock,height)`:
   - `worker = GET <gateway>/<current>/worker`
   - `resp = POST <worker> { ...query..., fromBlock: current, toBlock: desiredEnd }`
   - Parse `last = resp[-1].header.number` (always present even if no matches)
   - `current = last + 1`

Query shape (top-level keys)
- `fromBlock`: number (required)
- `toBlock`: number (optional but recommended to cap extraction)
- `includeAllBlocks`: boolean (optional)
- `fields`: selector object (optional)
- `logs`: array of log request objects (optional)
- `transactions`: array of transaction request objects (optional)
- `traces`: array of trace request objects (optional)
- `stateDiffs`: array of state diff request objects (optional)

Important semantics
- Addresses in requests must be lowercased.
- Empty arrays match *nothing*; omit the field (or request object) to match everything.

Evidence-oriented examples
- All txs directly calling a contract + emitted logs:
```json
{
  "fromBlock": 16000000,
  "transactions": [
    {
      "to": ["0xa0b86991c6218b36c1d19d4a2e9eb0ce3606eb48"],
      "logs": true
    }
  ],
  "fields": {
    "transaction": {"hash": true, "from": true, "to": true, "input": true, "value": true},
    "log": {"address": true, "topics": true, "data": true, "transactionHash": true}
  }
}
```

- All logs emitted by a contract:
```json
{
  "fromBlock": 16000000,
  "logs": [
    {
      "address": ["0xa0b86991c6218b36c1d19d4a2e9eb0ce3606eb48"],
      "transaction": true
    }
  ],
  "fields": {
    "log": {"address": true, "topics": true, "data": true, "transactionHash": true},
    "transaction": {"hash": true}
  }
}
```
