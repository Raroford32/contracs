#!/usr/bin/env python3
"""
Pendle PT Maturity Oracle Discontinuity Check

PT-sNUSD-5MAR2026 matures TOMORROW (March 5, 2026).
$7.3M supply, $6.5M borrow on Morpho Blue.

Questions:
1. How does the Morpho oracle price this PT? (AMM TWAP, fixed rate, underlying?)
2. What happens to the oracle at/after maturity?
3. How thin is the Pendle AMM liquidity?
4. Can the PT be redeemed post-maturity?
5. Does the oracle price converge to underlying at maturity?
"""

import json
import os
import time
from web3 import Web3

ETH_RPC = os.environ.get("ETH_RPC", "https://eth.llamarpc.com")
w3 = Web3(Web3.HTTPProvider(ETH_RPC))

print(f"Connected to Ethereum. Block: {w3.eth.block_number}")
now = w3.eth.get_block("latest")["timestamp"]
print(f"Current time: {time.strftime('%Y-%m-%d %H:%M:%S UTC', time.gmtime(now))}")

# PT-sNUSD-5MAR2026 on Morpho
PT_SNUSD_ADDR = "0x54Bf2659B5CdFd86b75920e93C0844c0364F5166"
MORPHO_ORACLE = "0xe8465B52E106"  # Truncated — need full address

# Get from Morpho API
MARKET_KEY = None  # Will get from the query

# First, let's get the full oracle address from the API
import requests

MORPHO_API = "https://blue-api.morpho.org/graphql"
query = """
{
  markets(
    where: { chainId_in: [1] }
    first: 500
    orderBy: BorrowAssetsUsd
    orderDirection: Desc
  ) {
    items {
      uniqueKey
      loanAsset { address symbol }
      collateralAsset { address symbol }
      oracleAddress
      lltv
      state { supplyAssetsUsd borrowAssetsUsd }
    }
  }
}
"""

try:
    resp = requests.post(MORPHO_API, json={"query": query}, timeout=30)
    data = resp.json()
    markets = data.get("data", {}).get("markets", {}).get("items", [])

    # Find PT markets
    pt_markets = [m for m in markets if "PT" in m.get("collateralAsset", {}).get("symbol", "")]
    print(f"\nPendle PT markets on Morpho ({len(pt_markets)}):")
    for m in pt_markets:
        cs = m["collateralAsset"]["symbol"]
        ls = m["loanAsset"]["symbol"]
        s = m["state"]["supplyAssetsUsd"]
        b = m["state"]["borrowAssetsUsd"]
        oa = m["oracleAddress"]
        ca = m["collateralAsset"]["address"]
        print(f"  {cs}/{ls} | Supply: ${s:,.0f} | Borrow: ${b:,.0f}")
        print(f"    Collateral: {ca}")
        print(f"    Oracle: {oa}")
except Exception as e:
    print(f"API error: {e}")
    pt_markets = []

ZERO = "0x0000000000000000000000000000000000000000"

ERC20_ABI = json.loads('''[
  {"inputs":[],"name":"symbol","outputs":[{"internalType":"string","name":"","type":"string"}],"stateMutability":"view","type":"function"},
  {"inputs":[],"name":"decimals","outputs":[{"internalType":"uint8","name":"","type":"uint8"}],"stateMutability":"view","type":"function"},
  {"inputs":[{"internalType":"address","name":"","type":"address"}],"name":"balanceOf","outputs":[{"internalType":"uint256","name":"","type":"uint256"}],"stateMutability":"view","type":"function"},
  {"inputs":[],"name":"totalSupply","outputs":[{"internalType":"uint256","name":"","type":"uint256"}],"stateMutability":"view","type":"function"}
]''')

# Pendle PT interface
PT_ABI = json.loads('''[
  {"inputs":[],"name":"symbol","outputs":[{"internalType":"string","name":"","type":"string"}],"stateMutability":"view","type":"function"},
  {"inputs":[],"name":"expiry","outputs":[{"internalType":"uint256","name":"","type":"uint256"}],"stateMutability":"view","type":"function"},
  {"inputs":[],"name":"SY","outputs":[{"internalType":"address","name":"","type":"address"}],"stateMutability":"view","type":"function"},
  {"inputs":[],"name":"YT","outputs":[{"internalType":"address","name":"","type":"address"}],"stateMutability":"view","type":"function"},
  {"inputs":[],"name":"factory","outputs":[{"internalType":"address","name":"","type":"address"}],"stateMutability":"view","type":"function"},
  {"inputs":[],"name":"isExpired","outputs":[{"internalType":"bool","name":"","type":"bool"}],"stateMutability":"view","type":"function"},
  {"inputs":[],"name":"totalSupply","outputs":[{"internalType":"uint256","name":"","type":"uint256"}],"stateMutability":"view","type":"function"}
]''')

# SY (Standardized Yield) interface
SY_ABI = json.loads('''[
  {"inputs":[],"name":"yieldToken","outputs":[{"internalType":"address","name":"","type":"address"}],"stateMutability":"view","type":"function"},
  {"inputs":[],"name":"exchangeRate","outputs":[{"internalType":"uint256","name":"","type":"uint256"}],"stateMutability":"view","type":"function"},
  {"inputs":[],"name":"asset","outputs":[{"internalType":"address","name":"","type":"address"}],"stateMutability":"view","type":"function"},
  {"inputs":[],"name":"totalSupply","outputs":[{"internalType":"uint256","name":"","type":"uint256"}],"stateMutability":"view","type":"function"}
]''')

# Morpho Oracle interface
ORACLE_ABI = json.loads('''[
  {"inputs":[],"name":"BASE_VAULT","outputs":[{"internalType":"contract IERC4626","name":"","type":"address"}],"stateMutability":"view","type":"function"},
  {"inputs":[],"name":"QUOTE_VAULT","outputs":[{"internalType":"contract IERC4626","name":"","type":"address"}],"stateMutability":"view","type":"function"},
  {"inputs":[],"name":"BASE_FEED_1","outputs":[{"internalType":"contract AggregatorV3Interface","name":"","type":"address"}],"stateMutability":"view","type":"function"},
  {"inputs":[],"name":"BASE_FEED_2","outputs":[{"internalType":"contract AggregatorV3Interface","name":"","type":"address"}],"stateMutability":"view","type":"function"},
  {"inputs":[],"name":"QUOTE_FEED_1","outputs":[{"internalType":"contract AggregatorV3Interface","name":"","type":"address"}],"stateMutability":"view","type":"function"},
  {"inputs":[],"name":"QUOTE_FEED_2","outputs":[{"internalType":"contract AggregatorV3Interface","name":"","type":"address"}],"stateMutability":"view","type":"function"},
  {"inputs":[],"name":"SCALE_FACTOR","outputs":[{"internalType":"uint256","name":"","type":"uint256"}],"stateMutability":"view","type":"function"},
  {"inputs":[],"name":"price","outputs":[{"internalType":"uint256","name":"","type":"uint256"}],"stateMutability":"view","type":"function"}
]''')

CHAINLINK_ABI = json.loads('''[
  {"inputs":[],"name":"latestRoundData","outputs":[{"internalType":"uint80","name":"roundId","type":"uint80"},{"internalType":"int256","name":"answer","type":"int256"},{"internalType":"uint256","name":"startedAt","type":"uint256"},{"internalType":"uint256","name":"updatedAt","type":"uint256"},{"internalType":"uint80","name":"answeredInRound","type":"uint80"}],"stateMutability":"view","type":"function"},
  {"inputs":[],"name":"decimals","outputs":[{"internalType":"uint8","name":"","type":"uint8"}],"stateMutability":"view","type":"function"},
  {"inputs":[],"name":"description","outputs":[{"internalType":"string","name":"","type":"string"}],"stateMutability":"view","type":"function"},
  {"inputs":[],"name":"latestAnswer","outputs":[{"internalType":"int256","name":"","type":"int256"}],"stateMutability":"view","type":"function"}
]''')

def safe_call(addr, abi, func_name, *args):
    try:
        c = w3.eth.contract(address=Web3.to_checksum_address(addr), abi=abi)
        return getattr(c.functions, func_name)(*args).call()
    except:
        return None

# Analyze each PT market
for m in pt_markets:
    coll_addr = m["collateralAsset"]["address"]
    oracle_addr = m["oracleAddress"]
    coll_sym = m["collateralAsset"]["symbol"]

    print(f"\n{'='*100}")
    print(f"  {coll_sym}")
    print(f"  Collateral: {coll_addr}")
    print(f"  Oracle: {oracle_addr}")
    print(f"{'='*100}")

    # PT details
    pt_sym = safe_call(coll_addr, PT_ABI, "symbol") or "?"
    expiry = safe_call(coll_addr, PT_ABI, "expiry")
    is_expired = safe_call(coll_addr, PT_ABI, "isExpired")
    sy_addr = safe_call(coll_addr, PT_ABI, "SY")
    yt_addr = safe_call(coll_addr, PT_ABI, "YT")
    pt_supply = safe_call(coll_addr, ERC20_ABI, "totalSupply") or 0
    pt_decimals = safe_call(coll_addr, ERC20_ABI, "decimals") or 18

    if expiry:
        expiry_str = time.strftime('%Y-%m-%d %H:%M:%S UTC', time.gmtime(expiry))
        time_to_expiry = expiry - now
        days_to = time_to_expiry / 86400
    else:
        expiry_str = "unknown"
        days_to = None

    print(f"\n  PT Symbol: {pt_sym}")
    print(f"  Expiry: {expiry_str}")
    print(f"  Is Expired: {is_expired}")
    print(f"  Time to expiry: {days_to:.2f} days" if days_to is not None else "  Time to expiry: unknown")
    print(f"  SY: {sy_addr}")
    print(f"  YT: {yt_addr}")
    print(f"  PT Supply: {pt_supply / (10**pt_decimals):,.4f}")

    # SY (Standardized Yield) details
    if sy_addr:
        yield_token = safe_call(sy_addr, SY_ABI, "yieldToken")
        sy_exchange_rate = safe_call(sy_addr, SY_ABI, "exchangeRate")
        sy_asset = safe_call(sy_addr, SY_ABI, "asset")
        sy_supply = safe_call(sy_addr, ERC20_ABI, "totalSupply") or 0

        if yield_token:
            yt_sym = safe_call(yield_token, ERC20_ABI, "symbol") or "?"
            print(f"\n  SY Details:")
            print(f"    Yield Token: {yt_sym} ({yield_token})")
            print(f"    Exchange Rate: {sy_exchange_rate}")
            print(f"    SY Asset: {sy_asset}")
            print(f"    SY Supply: {sy_supply / (10**18):,.4f}")

    # Oracle details
    print(f"\n  ORACLE ANALYSIS:")

    base_vault = safe_call(oracle_addr, ORACLE_ABI, "BASE_VAULT")
    quote_vault = safe_call(oracle_addr, ORACLE_ABI, "QUOTE_VAULT")
    base_feed_1 = safe_call(oracle_addr, ORACLE_ABI, "BASE_FEED_1")
    base_feed_2 = safe_call(oracle_addr, ORACLE_ABI, "BASE_FEED_2")
    quote_feed_1 = safe_call(oracle_addr, ORACLE_ABI, "QUOTE_FEED_1")
    quote_feed_2 = safe_call(oracle_addr, ORACLE_ABI, "QUOTE_FEED_2")
    scale_factor = safe_call(oracle_addr, ORACLE_ABI, "SCALE_FACTOR")
    oracle_price = safe_call(oracle_addr, ORACLE_ABI, "price")

    print(f"    BASE_VAULT: {base_vault}")
    print(f"    QUOTE_VAULT: {quote_vault}")
    print(f"    BASE_FEED_1: {base_feed_1}")
    print(f"    BASE_FEED_2: {base_feed_2}")
    print(f"    QUOTE_FEED_1: {quote_feed_1}")
    print(f"    QUOTE_FEED_2: {quote_feed_2}")
    print(f"    SCALE_FACTOR: {scale_factor}")
    print(f"    Current price(): {oracle_price}")

    # Check each feed
    for feed_name, feed_addr in [("BASE_FEED_1", base_feed_1), ("BASE_FEED_2", base_feed_2),
                                  ("QUOTE_FEED_1", quote_feed_1), ("QUOTE_FEED_2", quote_feed_2)]:
        if feed_addr and feed_addr != ZERO:
            desc = safe_call(feed_addr, CHAINLINK_ABI, "description")
            fdata = safe_call(feed_addr, CHAINLINK_ABI, "latestRoundData")
            fdec = safe_call(feed_addr, CHAINLINK_ABI, "decimals")
            if fdata:
                answer = fdata[1]
                updated = fdata[3]
                staleness = now - updated
                price_human = answer / (10**fdec) if fdec else answer
                print(f"    {feed_name}: {desc or '?'} = {price_human:,.8f} (staleness: {staleness/60:.0f} min)")
            else:
                print(f"    {feed_name}: {desc or '?'} — could not get latest data")

    # CRITICAL: Check if BASE_VAULT is the PT itself or the SY or the underlying
    if base_vault:
        bv_sym = safe_call(base_vault, ERC20_ABI, "symbol") or "?"
        print(f"\n    BASE_VAULT symbol: {bv_sym}")
        print(f"    BASE_VAULT address: {base_vault}")
        if base_vault.lower() == coll_addr.lower():
            print(f"    >>> ORACLE READS PT's OWN convertToAssets() !!!")
        elif sy_addr and base_vault.lower() == sy_addr.lower():
            print(f"    >>> ORACLE READS SY's convertToAssets()")
        else:
            print(f"    >>> ORACLE READS A DIFFERENT VAULT: {bv_sym}")

    # MATURITY RISK ANALYSIS
    if days_to is not None and days_to < 7:
        print(f"\n  !!! NEAR-MATURITY RISK ASSESSMENT !!!")
        print(f"  Days to expiry: {days_to:.2f}")
        print(f"  Is expired: {is_expired}")
        print(f"  Supply USD: ${m['state']['supplyAssetsUsd']:,.0f}")
        print(f"  Borrow USD: ${m['state']['borrowAssetsUsd']:,.0f}")
        print(f"  Questions:")
        print(f"    1. Does oracle_price() still work after expiry?")
        print(f"    2. What price does it return? (should converge to 1:1 with underlying)")
        print(f"    3. Can expired PT still be used as collateral?")
        print(f"    4. Is liquidation still possible for expired PT positions?")
        print(f"    5. How thin is AMM liquidity right now?")

print("\nDone.")
