# Squid CLI (`sqd`) essentials

Installation (official):
```bash
npm i -g @subsquid/cli@latest
sqd --version
```

Cloud auth (optional, only for deployments):
```bash
sqd auth -k <DEPLOYMENT_KEY>
```

Discover gateways by chain id (useful for this bundler):
```bash
# EVM gateways for chainId
sqd gateways list -t evm -c 1

# Filter by network name
sqd gateways list -t evm -n ethereum
```

Notes:
- `sqd gateways list` supports `--no-interactive`.
- The authoritative list of public gateways is also maintained in docs:
  https://docs.sqd.ai/subsquid-network/reference/networks/
