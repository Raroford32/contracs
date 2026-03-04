#!/usr/bin/env python3
"""
Deep probe of Pendle PT oracle contracts on Morpho Blue.

Phase 4 found 3 oracle types:
A. Aave PendlePriceCapAdapter - deterministic linear discount
B. Morpho SparkLinearDiscountOracle - baseDiscountPerYear, no market input
C. Pendle AMM 15-min TWAP - geometric mean in log-space

Previous scan used MorphoChainlinkOracleV2 ABI (BASE_VAULT etc.) which returned None.
This script probes with ALL known oracle ABIs to determine the actual type.

KEY QUESTION: What happens at maturity for the $7.3M PT-sNUSD-5MAR2026 market?
- SparkLinearDiscountOracle: discount → 0 smoothly, price → underlying. Safe.
- Pendle AMM TWAP: liquidity drains → manipulable. Dangerous.
- Custom: Unknown. Must investigate.
"""

import json
import os
import time
import requests
from web3 import Web3

RPCS = [
    os.environ.get("ETH_RPC", ""),
    "https://rpc.ankr.com/eth",
    "https://ethereum-rpc.publicnode.com",
    "https://eth.llamarpc.com",
    "https://1rpc.io/eth",
]
RPCS = [r for r in RPCS if r]

w3 = None
for rpc in RPCS:
    try:
        _w3 = Web3(Web3.HTTPProvider(rpc, request_kwargs={"timeout": 15}))
        bn = _w3.eth.block_number
        print(f"Connected to {rpc[:40]}... Block: {bn}")
        w3 = _w3
        break
    except Exception as e:
        print(f"Failed {rpc[:40]}...: {e}")
        continue

if not w3:
    print("No working RPC found!")
    exit(1)

now = w3.eth.get_block("latest")["timestamp"]
print(f"Current time: {time.strftime('%Y-%m-%d %H:%M:%S UTC', time.gmtime(now))}")

ZERO = "0x" + "0" * 40

# ============================================================================
# ABI sets for different oracle types
# ============================================================================

# Type A: MorphoChainlinkOracleV2 (standard)
CHAINLINK_ORACLE_V2_ABI = json.loads('''[
  {"inputs":[],"name":"BASE_VAULT","outputs":[{"type":"address"}],"stateMutability":"view","type":"function"},
  {"inputs":[],"name":"QUOTE_VAULT","outputs":[{"type":"address"}],"stateMutability":"view","type":"function"},
  {"inputs":[],"name":"BASE_FEED_1","outputs":[{"type":"address"}],"stateMutability":"view","type":"function"},
  {"inputs":[],"name":"BASE_FEED_2","outputs":[{"type":"address"}],"stateMutability":"view","type":"function"},
  {"inputs":[],"name":"QUOTE_FEED_1","outputs":[{"type":"address"}],"stateMutability":"view","type":"function"},
  {"inputs":[],"name":"QUOTE_FEED_2","outputs":[{"type":"address"}],"stateMutability":"view","type":"function"},
  {"inputs":[],"name":"SCALE_FACTOR","outputs":[{"type":"uint256"}],"stateMutability":"view","type":"function"},
  {"inputs":[],"name":"price","outputs":[{"type":"uint256"}],"stateMutability":"view","type":"function"}
]''')

# Type B: SparkLinearDiscountOracle (Spark/Morpho for PT)
SPARK_LINEAR_ABI = json.loads('''[
  {"inputs":[],"name":"price","outputs":[{"type":"uint256"}],"stateMutability":"view","type":"function"},
  {"inputs":[],"name":"PT","outputs":[{"type":"address"}],"stateMutability":"view","type":"function"},
  {"inputs":[],"name":"FEED","outputs":[{"type":"address"}],"stateMutability":"view","type":"function"},
  {"inputs":[],"name":"DISCOUNT_RATE","outputs":[{"type":"uint256"}],"stateMutability":"view","type":"function"},
  {"inputs":[],"name":"MATURITY","outputs":[{"type":"uint256"}],"stateMutability":"view","type":"function"},
  {"inputs":[],"name":"SCALE_FACTOR","outputs":[{"type":"uint256"}],"stateMutability":"view","type":"function"},
  {"inputs":[],"name":"baseDiscountPerYear","outputs":[{"type":"uint256"}],"stateMutability":"view","type":"function"},
  {"inputs":[],"name":"maturity","outputs":[{"type":"uint256"}],"stateMutability":"view","type":"function"},
  {"inputs":[],"name":"feed","outputs":[{"type":"address"}],"stateMutability":"view","type":"function"},
  {"inputs":[],"name":"discountRate","outputs":[{"type":"uint256"}],"stateMutability":"view","type":"function"}
]''')

# Type C: Pendle TWAP Oracle adapter
PENDLE_TWAP_ABI = json.loads('''[
  {"inputs":[],"name":"price","outputs":[{"type":"uint256"}],"stateMutability":"view","type":"function"},
  {"inputs":[],"name":"MARKET","outputs":[{"type":"address"}],"stateMutability":"view","type":"function"},
  {"inputs":[],"name":"TWAP_DURATION","outputs":[{"type":"uint32"}],"stateMutability":"view","type":"function"},
  {"inputs":[],"name":"market","outputs":[{"type":"address"}],"stateMutability":"view","type":"function"},
  {"inputs":[],"name":"twapDuration","outputs":[{"type":"uint32"}],"stateMutability":"view","type":"function"},
  {"inputs":[],"name":"PT","outputs":[{"type":"address"}],"stateMutability":"view","type":"function"},
  {"inputs":[],"name":"SY","outputs":[{"type":"address"}],"stateMutability":"view","type":"function"},
  {"inputs":[],"name":"ORACLE","outputs":[{"type":"address"}],"stateMutability":"view","type":"function"},
  {"inputs":[],"name":"oracle","outputs":[{"type":"address"}],"stateMutability":"view","type":"function"}
]''')

# Type D: Aave PendlePriceCapAdapter
AAVE_PENDLE_ABI = json.loads('''[
  {"inputs":[],"name":"price","outputs":[{"type":"uint256"}],"stateMutability":"view","type":"function"},
  {"inputs":[],"name":"UNDERLYING_PRICE_FEED","outputs":[{"type":"address"}],"stateMutability":"view","type":"function"},
  {"inputs":[],"name":"PENDLE_MARKET","outputs":[{"type":"address"}],"stateMutability":"view","type":"function"},
  {"inputs":[],"name":"DISCOUNT_RATE_PER_YEAR","outputs":[{"type":"uint256"}],"stateMutability":"view","type":"function"},
  {"inputs":[],"name":"PT_RATIO_TO_UNDERLYING","outputs":[{"type":"uint256"}],"stateMutability":"view","type":"function"}
]''')

# Generic ERC20
ERC20_ABI = json.loads('''[
  {"inputs":[],"name":"symbol","outputs":[{"type":"string"}],"stateMutability":"view","type":"function"},
  {"inputs":[],"name":"decimals","outputs":[{"type":"uint8"}],"stateMutability":"view","type":"function"}
]''')

def safe_call(addr, abi, func_name, *args):
    try:
        c = w3.eth.contract(address=Web3.to_checksum_address(addr), abi=abi)
        return getattr(c.functions, func_name)(*args).call()
    except Exception as e:
        return None

def get_bytecode_size(addr):
    try:
        code = w3.eth.get_code(Web3.to_checksum_address(addr))
        return len(code)
    except:
        return 0

# ============================================================================
# Get PT markets from Morpho API
# ============================================================================
MORPHO_API = "https://blue-api.morpho.org/graphql"
query = """{
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
}"""

resp = requests.post(MORPHO_API, json={"query": query}, timeout=30)
data = resp.json()
markets = data.get("data", {}).get("markets", {}).get("items", [])

# Filter PT markets with real size
pt_markets = []
for m in markets:
    cs = m.get("collateralAsset", {}).get("symbol", "")
    borrow = m.get("state", {}).get("borrowAssetsUsd", 0) or 0
    if "PT" in cs and borrow > 100_000:
        pt_markets.append(m)

pt_markets.sort(key=lambda x: x["state"]["borrowAssetsUsd"] or 0, reverse=True)
print(f"\nPT markets with >$100K borrow: {len(pt_markets)}")

for m in pt_markets[:15]:
    cs = m["collateralAsset"]["symbol"]
    b = m["state"]["borrowAssetsUsd"] or 0
    s = m["state"]["supplyAssetsUsd"] or 0
    print(f"  {cs} | Supply: ${s:,.0f} | Borrow: ${b:,.0f} | Oracle: {m['oracleAddress']}")

# ============================================================================
# Deep probe each oracle
# ============================================================================
print(f"\n{'='*100}")
print("DEEP ORACLE PROBE — ALL ABI PATTERNS")
print(f"{'='*100}")

for m in pt_markets[:10]:
    oracle_addr = m["oracleAddress"]
    coll_addr = m["collateralAsset"]["address"]
    coll_sym = m["collateralAsset"]["symbol"]
    borrow = m["state"]["borrowAssetsUsd"] or 0

    print(f"\n{'='*80}")
    print(f"  {coll_sym} | Borrow: ${borrow:,.0f}")
    print(f"  Collateral: {coll_addr}")
    print(f"  Oracle: {oracle_addr}")
    print(f"{'='*80}")

    # Bytecode size
    bsize = get_bytecode_size(oracle_addr)
    print(f"  Bytecode size: {bsize} bytes")

    # Try price() first (common to all types)
    price = safe_call(oracle_addr, CHAINLINK_ORACLE_V2_ABI, "price")
    print(f"  price(): {price}")

    # === Type A: MorphoChainlinkOracleV2 ===
    base_vault = safe_call(oracle_addr, CHAINLINK_ORACLE_V2_ABI, "BASE_VAULT")
    scale_factor = safe_call(oracle_addr, CHAINLINK_ORACLE_V2_ABI, "SCALE_FACTOR")
    base_feed_1 = safe_call(oracle_addr, CHAINLINK_ORACLE_V2_ABI, "BASE_FEED_1")

    if base_vault is not None or scale_factor is not None:
        print(f"  >>> TYPE: MorphoChainlinkOracleV2")
        print(f"      BASE_VAULT: {base_vault}")
        print(f"      SCALE_FACTOR: {scale_factor}")
        print(f"      BASE_FEED_1: {base_feed_1}")
        base_feed_2 = safe_call(oracle_addr, CHAINLINK_ORACLE_V2_ABI, "BASE_FEED_2")
        quote_feed_1 = safe_call(oracle_addr, CHAINLINK_ORACLE_V2_ABI, "QUOTE_FEED_1")
        quote_vault = safe_call(oracle_addr, CHAINLINK_ORACLE_V2_ABI, "QUOTE_VAULT")
        print(f"      BASE_FEED_2: {base_feed_2}")
        print(f"      QUOTE_FEED_1: {quote_feed_1}")
        print(f"      QUOTE_VAULT: {quote_vault}")
        continue

    # === Type B: SparkLinearDiscountOracle ===
    discount_rate = safe_call(oracle_addr, SPARK_LINEAR_ABI, "DISCOUNT_RATE")
    maturity = safe_call(oracle_addr, SPARK_LINEAR_ABI, "MATURITY")
    pt_addr = safe_call(oracle_addr, SPARK_LINEAR_ABI, "PT")
    feed = safe_call(oracle_addr, SPARK_LINEAR_ABI, "FEED")

    # Also try lowercase variants
    if discount_rate is None:
        discount_rate = safe_call(oracle_addr, SPARK_LINEAR_ABI, "discountRate")
    if maturity is None:
        maturity = safe_call(oracle_addr, SPARK_LINEAR_ABI, "maturity")
    if feed is None:
        feed = safe_call(oracle_addr, SPARK_LINEAR_ABI, "feed")
    base_discount = safe_call(oracle_addr, SPARK_LINEAR_ABI, "baseDiscountPerYear")

    if discount_rate is not None or maturity is not None or base_discount is not None:
        print(f"  >>> TYPE: SparkLinearDiscountOracle")
        print(f"      PT: {pt_addr}")
        print(f"      FEED: {feed}")
        print(f"      DISCOUNT_RATE: {discount_rate}")
        print(f"      MATURITY: {maturity}")
        print(f"      baseDiscountPerYear: {base_discount}")

        if maturity:
            mat_str = time.strftime('%Y-%m-%d %H:%M:%S UTC', time.gmtime(maturity))
            days_to = (maturity - now) / 86400
            print(f"      Maturity date: {mat_str}")
            print(f"      Days to maturity: {days_to:.2f}")

            if days_to <= 0:
                print(f"      >>> EXPIRED! Oracle should return 1:1 with underlying")
            elif days_to < 2:
                print(f"      >>> NEAR MATURITY! Discount approaching zero")
                if discount_rate:
                    # Linear discount: price = underlying * (1 - discount_rate * time_to_maturity/year)
                    remaining_discount = discount_rate * (maturity - now) / (365.25 * 86400)
                    print(f"      >>> Remaining discount: {remaining_discount}")
        continue

    # === Type C: Pendle TWAP adapter ===
    twap_market = safe_call(oracle_addr, PENDLE_TWAP_ABI, "MARKET")
    twap_duration = safe_call(oracle_addr, PENDLE_TWAP_ABI, "TWAP_DURATION")
    pendle_oracle = safe_call(oracle_addr, PENDLE_TWAP_ABI, "ORACLE")
    sy = safe_call(oracle_addr, PENDLE_TWAP_ABI, "SY")
    pt_twap = safe_call(oracle_addr, PENDLE_TWAP_ABI, "PT")

    # lowercase variants
    if twap_market is None:
        twap_market = safe_call(oracle_addr, PENDLE_TWAP_ABI, "market")
    if twap_duration is None:
        twap_duration = safe_call(oracle_addr, PENDLE_TWAP_ABI, "twapDuration")
    if pendle_oracle is None:
        pendle_oracle = safe_call(oracle_addr, PENDLE_TWAP_ABI, "oracle")

    if twap_market is not None or twap_duration is not None or pendle_oracle is not None:
        print(f"  >>> TYPE: Pendle TWAP Oracle Adapter")
        print(f"      MARKET: {twap_market}")
        print(f"      TWAP_DURATION: {twap_duration}")
        print(f"      PT: {pt_twap}")
        print(f"      SY: {sy}")
        print(f"      ORACLE: {pendle_oracle}")

        if twap_duration:
            print(f"      TWAP window: {twap_duration} seconds ({twap_duration/60:.0f} min)")
            print(f"      >>> USES PENDLE AMM TWAP — liquidity-dependent!")
        continue

    # === Type D: Aave PendlePriceCapAdapter ===
    underlying_feed = safe_call(oracle_addr, AAVE_PENDLE_ABI, "UNDERLYING_PRICE_FEED")
    pendle_market = safe_call(oracle_addr, AAVE_PENDLE_ABI, "PENDLE_MARKET")
    discount_per_year = safe_call(oracle_addr, AAVE_PENDLE_ABI, "DISCOUNT_RATE_PER_YEAR")

    if underlying_feed is not None or pendle_market is not None:
        print(f"  >>> TYPE: Aave PendlePriceCapAdapter")
        print(f"      UNDERLYING_PRICE_FEED: {underlying_feed}")
        print(f"      PENDLE_MARKET: {pendle_market}")
        print(f"      DISCOUNT_RATE_PER_YEAR: {discount_per_year}")
        continue

    # === Unknown type ===
    print(f"  >>> TYPE: UNKNOWN (no known ABI matched)")
    print(f"  Trying raw 4-byte selector scan...")

    # Try common function selectors
    SELECTORS = {
        "0xa035b1fe": "price()",
        "0xfc0c546a": "asset()",
        "0x06fdde03": "name()",
        "0x95d89b41": "symbol()",
        "0xd4b83992": "FEED()",
        "0xfe10226d": "MATURITY()",
        "0x2b97bbc5": "DISCOUNT_RATE()",
        "0x48e5d9f8": "market()",
        "0xfbd0cfe4": "PT()",
    }

    for sel, name in SELECTORS.items():
        try:
            result = w3.eth.call({"to": Web3.to_checksum_address(oracle_addr), "data": sel})
            if len(result) > 0:
                val = int.from_bytes(result[:32], 'big') if len(result) >= 32 else result.hex()
                # Check if it's an address (top 12 bytes are 0)
                if isinstance(val, int) and val < 2**160 and val > 0:
                    addr_hex = "0x" + hex(val)[2:].zfill(40)
                    sym = safe_call(addr_hex, ERC20_ABI, "symbol")
                    print(f"    {name} => {addr_hex} ({sym or '?'})")
                elif isinstance(val, int):
                    print(f"    {name} => {val}")
                else:
                    print(f"    {name} => 0x{val[:32].hex()}...")
        except:
            pass

print("\nDone.")
