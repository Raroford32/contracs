#!/usr/bin/env python3
"""Query Morpho Blue API for PT-srNUSD market."""

import json
import urllib.request

query = """
{
  markets(where: {
    collateralAsset_in: ["0x82b853DB31F025858792d8fA969f2a1Dc245C179"]
    chainId_in: [1]
  }) {
    items {
      uniqueKey
      lltv
      collateralAsset {
        address
        symbol
      }
      loanAsset {
        address
        symbol
        decimals
      }
      oracleAddress
      irmAddress
      state {
        supplyAssets
        borrowAssets
        liquidityAssets
        utilization
      }
    }
  }
}
"""

url = "https://blue-api.morpho.org/graphql"
data = json.dumps({"query": query}).encode()
req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"})

try:
    resp = urllib.request.urlopen(req, timeout=15)
    result = json.loads(resp.read().decode())
    print(json.dumps(result, indent=2))
except Exception as e:
    print(f"Error: {e}")

# Also try with lowercase address
query2 = """
{
  markets(where: {
    collateralAsset_in: ["0x82b853db31f025858792d8fa969f2a1dc245c179"]
    chainId_in: [1]
  }) {
    items {
      uniqueKey
      lltv
      collateralAsset {
        address
        symbol
      }
      loanAsset {
        address
        symbol
        decimals
      }
      oracleAddress
      irmAddress
      state {
        supplyAssets
        borrowAssets
        liquidityAssets
        utilization
      }
    }
  }
}
"""

data2 = json.dumps({"query": query2}).encode()
req2 = urllib.request.Request(url, data=data2, headers={"Content-Type": "application/json"})
try:
    resp2 = urllib.request.urlopen(req2, timeout=15)
    result2 = json.loads(resp2.read().decode())
    if result2 != result:
        print("\n--- Lowercase query result ---")
        print(json.dumps(result2, indent=2))
except Exception as e:
    print(f"Error2: {e}")

print("\nDone.")
