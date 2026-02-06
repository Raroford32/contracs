# Developer Explorer + Debugger (Human-Guided Introspection)

Sources of truth:
- Inspect Transaction: https://docs.tenderly.co/developer-explorer/inspect-transaction
- Transaction Overview + Advanced Trace Search: https://docs.tenderly.co/monitoring/contracts
- Evaluate Expressions: https://docs.tenderly.co/debugger/evaluate-expressions-with-advanced-debugger
- Dev Toolkit browser extension: https://docs.tenderly.co/debugger/dev-toolkit-browser-extension

## Inspect Transaction (what you get)
Inspect Transaction provides:
- decoded call trace (with opcode-level visibility; CALL/DELEGATECALL/STATICCALL/SLOAD/SSTORE/REVERT/etc.)
- toggles for "Full Trace", "Storage Access" (SLOAD/SSTORE + slot/value), and "Event Logs" (LOG0..LOG4)
- search inside the call trace (opcodes/functions/variables/addresses/files/contracts)
- tokens transferred / asset changes (with USD conversion)
- involved contracts (jump to source when verified)
- emitted events (decoded when verified; raw always)
- state changes with old->new values (decoded + raw)
- gas profiler flame chart (function/opcode breakdown)
- team workflows: comments and per-trace-line prioritization (useful for audit collaboration)

Security workflow tip:
- Use this UI when you need fast human understanding of "where value moved" and "what storage changed" before writing a hypothesis.
- Persist output evidence by exporting/capturing the JSON trace via Node RPC (`tenderly_traceTransaction`) and storing it on disk.

## Advanced Trace Search (jump to the needle)
Transaction Overview docs describe "Advanced Trace Search" categories:
- OpCode
- From
- To
- Function
- File
- Contract
- State Variable

Use this to quickly locate:
- the first external call
- the first state write to a critical variable
- the exact trace line where an invariant flips

## Evaluate Expressions (Debugger)
Evaluate Expression lets you evaluate expressions inside the execution trace (Solidity support per docs).
It can evaluate:
- state variables
- mappings
- dynamic arrays
- global and local variables
- function-level expressions

Security workflow tip:
- Use Evaluate to validate your "accounting model" assumptions at the exact trace step where measurement/settlement happens.
- Convert the evaluated facts into a single crisp invariant statement and then into a reproducible simulation or fuzz oracle.

## Dev Toolkit browser extension (speed boost)
Docs describe Dev Toolkit as a one-click bridge from any block explorer into Tenderly tooling:
- open a tx in Tenderly
- run on a Virtual TestNet
- simulate (including modifying inputs/params/code)
- debug trace-by-trace
- view trace/state changes/gas profiler

Security workflow tip:
- Use Dev Toolkit during rapid triage to minimize time spent copying tx hashes/URLs and to standardize evidence capture.
