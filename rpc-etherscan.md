# API Configuration (Local Only — Never Commit Secrets)

## Ethereum RPC Endpoints

```
MAINNET_INFURA: https://mainnet.infura.io/v3/bfc7283659224dd6b5124ebbc2b14e2c
MAINNET_ALCHEMY: https://eth-mainnet.g.alchemy.com/v2/pLXdY7rYRY10SH_UTLBGH
```

## Etherscan V2 API

```
BASE_URL: https://api.etherscan.io/v2/api
API_KEY: 5UWN6DNT7UZCEJYNE3J6FCVAWH4QJW255K

EXAMPLE (Source Code):
https://api.etherscan.io/v2/api?chainid=1&module=contract&action=getsourcecode&address=<addr>&apikey=5UWN6DNT7UZCEJYNE3J6FCVAWH4QJW255K

EXAMPLE (ABI):
https://api.etherscan.io/v2/api?chainid=1&module=contract&action=getabi&address=<addr>&apikey=5UWN6DNT7UZCEJYNE3J6FCVAWH4QJW255K

SUPPORTED CHAINS:
- chainid=1   (Ethereum Mainnet)
- chainid=56  (BNB Smart Chain)
- chainid=137 (Polygon)
- chainid=42161 (Arbitrum One)
- chainid=10  (Optimism)
```

## DeBank Cloud API

```
BASE_URL: https://pro-openapi.debank.com
ACCESS_KEY: e0f9f5b495ec8924d0ed905a0a68f78c050fdf54

ENDPOINTS:
- GET /v1/user/total_balance?id=<address>
- GET /v1/user/token_list?id=<address>
- GET /v1/user/protocol_list?id=<address>
- GET /v1/user/history_list?id=<address>
- GET /v1/protocol/list
- GET /v1/token?id=<address>&chain_id=eth

HEADERS:
AccessKey: e0f9f5b495ec8924d0ed905a0a68f78c050fdf54

EXAMPLE (Python):
import requests
headers = {"AccessKey": "e0f9f5b495ec8924d0ed905a0a68f78c050fdf54"}
response = requests.get(
    "https://pro-openapi.debank.com/v1/user/total_balance",
    params={"id": "0x..."},
    headers=headers
)
```

## Sourcify API (Preferred for Source Code)

```
BASE_URL: https://sourcify.dev/server

FULL MATCH:
GET /repository/contracts/full_match/1/<address>/

PARTIAL MATCH:
GET /repository/contracts/partial_match/1/<address>/

FILES:
GET /files/1/<address>
```

## External Tools

```
TRAVERSE.TOOLS:
URL: https://traverse.tools/
USE: Cross-contract relationship mapping, protocol topology

ITYFUZZ:
DOCS: https://docs.ityfuzz.rs/
USE: Coverage-guided fuzzing, invariant testing
```

## Usage Priority

1. **Source Code**: Sourcify first, Etherscan V2 fallback
2. **Protocol Context**: DeBank API
3. **Cross-Contract Mapping**: Traverse.tools
4. **Fuzzing**: ItyFuzz when parameter space is large
5. **RPC Queries**: Alchemy preferred (higher rate limit)
