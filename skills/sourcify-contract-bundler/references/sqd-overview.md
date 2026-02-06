# SQD / SubSquid overview (what to use, when)

SQD (formerly Subsquid) provides:

1) SQD Network (data lake + query engine)
- Free (currently) historical data extraction via public gateways.
- For EVM, includes logs, transactions/receipts, traces, and per-transaction state diffs.
- Best for: evidence bundles, protocol behavior mining, and high-volume historical extraction.

2) Squid SDK (Typescript indexing toolkit)
- Build custom indexers ("squids") with batch processors (e.g., `EvmBatchProcessor`).
- Best for: transforming raw chain data into custom datasets, DB tables, and audit-specific views.

3) SQD Cloud
- Hosted deployments for squids and (optional) GraphQL APIs.

4) Squid CLI (`sqd`)
- Scaffold and run squids locally, manage Cloud deployments.
- Useful here mainly for discovering gateways (`sqd gateways list`).

5) SQD Firehose (subgraphs adapter)
- Run subgraphs against SQD Network (historical via gateway + optional near-head RPC ingestion).

Key pages (official docs):
- Home: https://docs.sqd.ai/
- Public gateways list: https://docs.sqd.ai/subsquid-network/reference/networks/
- SQD Network EVM API: https://docs.sqd.ai/subsquid-network/reference/evm-api/
- Squid SDK overview (processors, stores, typegen): https://docs.sqd.ai/sdk/overview/
- SQD Cloud deployment workflow: https://docs.sqd.ai/cloud/overview/
- SQD Firehose (subgraphs support): https://docs.sqd.ai/subgraphs-support/
- EVM processor reference:
  - Logs: https://docs.sqd.ai/sdk/reference/processors/evm-batch/logs/
  - Transactions: https://docs.sqd.ai/sdk/reference/processors/evm-batch/transactions/
  - Traces: https://docs.sqd.ai/sdk/reference/processors/evm-batch/traces/
  - State diffs: https://docs.sqd.ai/sdk/reference/processors/evm-batch/state-diffs/
  - Field selection: https://docs.sqd.ai/sdk/reference/processors/evm-batch/field-selection/

Practical guidance for this skill:
- Use SQD Network API to fetch evidence quickly without running a full squid.
- Use Squid SDK when you need custom decoding/aggregation and reproducible ETL.
