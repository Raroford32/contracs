# SQD EVM data requests (logs/txs/traces/state diffs)

These shapes are used both in Squid SDK (`EvmBatchProcessor`) and the SQD Network EVM API query `logs/transactions/traces/stateDiffs` arrays.

## Logs
Request options (addLog):
```ts
{
  address?: string[]
  topic0?: string[]
  topic1?: string[]
  topic2?: string[]
  topic3?: string[]
  range?: {from: number, to?: number}

  transaction?: boolean
  transactionLogs?: boolean
  transactionTraces?: boolean
}
```
Notes:
- Topic filters match 32-byte topics. If you filter by an address topic (e.g. `topic1`/`topic2`), you must left-pad the 20-byte address to 32 bytes (66 chars including `0x`).

## Transactions
Request options (addTransaction):
```ts
{
  from?: string[]
  to?: string[]
  sighash?: string[]
  range?: {from: number, to?: number}

  logs?: boolean
  stateDiffs?: boolean
  traces?: boolean
}
```
Notes:
- `sighash` is the first 4 bytes of the keccak256(signature), e.g. `transfer(address,uint256)` -> `0xa9059cbb`.
- `addTransaction` only gets top-level calls (direct txs). Use traces to capture internal calls.

## Traces
Request options (addTrace):
```ts
{
  callTo?: string[]
  callFrom?: string[]
  callSighash?: string[]
  createFrom?: string[]
  rewardAuthor?: string[]
  suicideRefundAddress?: string[]
  type?: string[]
  range?: {from: number, to?: number}

  transaction?: boolean
  transactionLogs?: boolean
  subtraces?: boolean
  parents?: boolean
}
```
Allowed `type` values:
- `create`, `call`, `suicide`, `reward`
Notes:
- `subtraces=true` includes downstream traces.
- `parents=true` includes upstream traces.

## State diffs
Request options (addStateDiff):
```ts
{
  address?: string[]
  key?: string[]
  kind?: ('=' | '+' | '*' | '-')[]
  range?: {from: number, to?: number}

  transaction?: boolean
}
```
Notes:
- `key` can be a raw storage slot key, or special keys like `balance`, `code`, `nonce`.

## Field selection
Use a `fields` selector (SQD Network) / `setFields()` (SDK) to request only the needed fields.

Shape:
```ts
{
  log?: { /* booleans */ }
  transaction?: { /* booleans */ }
  stateDiff?: { /* booleans */ }
  trace?: { /* booleans */ }
  block?: { /* booleans */ }
}
```

Practical defaults for contract evidence:
- Logs: `topics`, `data`, `transactionHash`
- Transactions: `hash`, `from`, `to`, `input`, `value`
- Traces: `type` + call endpoints (`callFrom`, `callTo`, `callSighash`) or create address (`createResultAddress`)
