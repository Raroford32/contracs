# SQD docs index (site map)

Use this file as a navigation index when you need "full vision" across SQD features.

Core products

1) SQD Network
- Overview: https://docs.sqd.ai/subsquid-network/overview/
- Public gateways list (find gateway URL for chainId): https://docs.sqd.ai/subsquid-network/reference/networks/
- Network APIs (router/worker pattern)
  - EVM API: https://docs.sqd.ai/subsquid-network/reference/evm-api/
  - Substrate API: https://docs.sqd.ai/subsquid-network/reference/substrate-api/
  - Starknet API: https://docs.sqd.ai/subsquid-network/reference/starknet-api/
  - Solana API: https://docs.sqd.ai/solana-indexing/network-api/solana-api/
  - Tron API: https://docs.sqd.ai/tron-indexing/network-api/tron-api/

2) Squid SDK (Indexing SDK)
- Home: https://docs.sqd.ai/sdk/
- Overview (processors, stores, typegen, GraphQL): https://docs.sqd.ai/sdk/overview/
- EVM processor reference: https://docs.sqd.ai/sdk/reference/processors/evm-batch/
- Substrate processor reference: https://docs.sqd.ai/sdk/reference/processors/substrate-batch/
- Stores (file/typeorm/bigquery): https://docs.sqd.ai/sdk/reference/store/
- Typegen tools: https://docs.sqd.ai/sdk/resources/tools/typegen/
- GraphQL serving / OpenReader: https://docs.sqd.ai/sdk/reference/openreader-server/

3) SQD Cloud
- Overview / deployment workflow: https://docs.sqd.ai/cloud/overview/
- Manifest reference (`squid.yaml`): https://docs.sqd.ai/cloud/reference/manifest/
- Addons (RPC, Postgres, etc): https://docs.sqd.ai/cloud/resources/
- Pricing: https://docs.sqd.ai/cloud/pricing/

4) Squid CLI (`sqd`)
- CLI reference: https://docs.sqd.ai/squid-cli/
- Installation: https://docs.sqd.ai/squid-cli/installation/
- Gateways discovery: https://docs.sqd.ai/squid-cli/gateways/
- Run locally: https://docs.sqd.ai/squid-cli/run/
- Deploy / logs / restart / tags: see sidebar under squid-cli.

5) SQD Firehose (subgraphs adapter)
- Tutorial: https://docs.sqd.ai/subgraphs-support/

Fast doc search technique (for agents)
- Use Firecrawl/web search with a site filter:
  - `site:docs.sqd.ai <feature>`
  - `site:docs.subsquid.io <feature>`
- Prefer the API reference pages when implementing code; prefer tutorials when writing workflows.
