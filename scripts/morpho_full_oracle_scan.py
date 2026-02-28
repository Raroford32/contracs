#!/usr/bin/env python3
"""
Efficient full Morpho Blue market scan: Check all 1216 markets for oracle anomalies.
Uses batch calls to minimize RPC overhead.
Focus: find markets where oracle price is wildly wrong (PAXG pattern).
"""

import json
import os
import sys
from web3 import Web3

RPC = os.environ.get("RPC", "https://eth-mainnet.g.alchemy.com/v2/pLXdY7rYRY10SH_UTLBGH")
w3 = Web3(Web3.HTTPProvider(RPC))

MORPHO = "0xBBBBBbbBBb9cC5e90e3b3Af64bdAF62C37EEFFCb"

# Minimal ABIs
MORPHO_ABI = json.loads('''[
  {"inputs":[{"internalType":"Id","name":"id","type":"bytes32"}],"name":"idToMarketParams","outputs":[{"components":[{"internalType":"address","name":"loanToken","type":"address"},{"internalType":"address","name":"collateralToken","type":"address"},{"internalType":"address","name":"oracle","type":"address"},{"internalType":"address","name":"irm","type":"address"},{"internalType":"uint256","name":"lltv","type":"uint256"}],"internalType":"struct MarketParams","name":"","type":"tuple"}],"stateMutability":"view","type":"function"},
  {"inputs":[{"internalType":"Id","name":"id","type":"bytes32"}],"name":"market","outputs":[{"internalType":"uint128","name":"totalSupplyAssets","type":"uint128"},{"internalType":"uint128","name":"totalSupplyShares","type":"uint128"},{"internalType":"uint128","name":"totalBorrowAssets","type":"uint128"},{"internalType":"uint128","name":"totalBorrowShares","type":"uint128"},{"internalType":"uint128","name":"lastUpdate","type":"uint128"},{"internalType":"uint128","name":"fee","type":"uint128"}],"stateMutability":"view","type":"function"}
]''')

ORACLE_ABI = json.loads('''[
  {"inputs":[],"name":"price","outputs":[{"internalType":"uint256","name":"","type":"uint256"}],"stateMutability":"view","type":"function"}
]''')

ERC20_ABI = json.loads('''[
  {"inputs":[],"name":"decimals","outputs":[{"internalType":"uint8","name":"","type":"uint8"}],"stateMutability":"view","type":"function"},
  {"inputs":[],"name":"symbol","outputs":[{"internalType":"string","name":"","type":"string"}],"stateMutability":"view","type":"function"}
]''')

morpho = w3.eth.contract(address=Web3.to_checksum_address(MORPHO), abi=MORPHO_ABI)

def safe_call(contract, func_name, *args):
    try:
        return getattr(contract.functions, func_name)(*args).call()
    except:
        return None

# Step 1: Get all market IDs from CreateMarket events
# Scan from Morpho deploy block
print(f"Connected. Block: {w3.eth.block_number}")
print("\n[1] Fetching all CreateMarket events...")

CREATE_MARKET_TOPIC = "0xac4b2400f169220b0c0afdde7a0b32e775ba727ea1cb30b35f935cdaab8683ac"

all_market_ids = []
start_block = 18883000  # Morpho Blue deploy
latest = w3.eth.block_number
chunk_size = 500000

for from_block in range(start_block, latest + 1, chunk_size):
    to_block = min(from_block + chunk_size - 1, latest)
    try:
        logs = w3.eth.get_logs({
            "address": Web3.to_checksum_address(MORPHO),
            "topics": [CREATE_MARKET_TOPIC],
            "fromBlock": from_block,
            "toBlock": to_block,
        })
        for log in logs:
            # topic[1] is the indexed market ID (bytes32)
            raw = log["topics"][1]
            # Convert HexBytes to bytes32
            market_id = bytes(raw)
            all_market_ids.append(market_id)
        if logs:
            print(f"  Blocks {from_block}-{to_block}: {len(logs)} markets")
    except Exception as e:
        # Try smaller chunks
        sub_chunk = 100000
        for sub_from in range(from_block, to_block + 1, sub_chunk):
            sub_to = min(sub_from + sub_chunk - 1, to_block)
            try:
                logs = w3.eth.get_logs({
                    "address": Web3.to_checksum_address(MORPHO),
                    "topics": [CREATE_MARKET_TOPIC],
                    "fromBlock": sub_from,
                    "toBlock": sub_to,
                })
                for log in logs:
                    raw = log["topics"][1]
                    market_id = bytes(raw)
                    all_market_ids.append(market_id)
            except:
                pass

print(f"\nTotal markets found: {len(all_market_ids)}")

# Step 2: For each market, check if it has supply > 0, then check oracle price
print("\n[2] Scanning markets for active ones with potential oracle anomalies...")

# Decimal cache
decimal_cache = {}
symbol_cache = {}

def get_decimals(addr):
    if addr in decimal_cache:
        return decimal_cache[addr]
    c = w3.eth.contract(address=Web3.to_checksum_address(addr), abi=ERC20_ABI)
    d = safe_call(c, "decimals")
    if d is None:
        d = 18
    decimal_cache[addr] = d
    return d

def get_symbol(addr):
    if addr in symbol_cache:
        return symbol_cache[addr]
    c = w3.eth.contract(address=Web3.to_checksum_address(addr), abi=ERC20_ABI)
    s = safe_call(c, "symbol")
    if s is None:
        s = "?"
    symbol_cache[addr] = s
    return s

anomalies = []
active_markets = 0
scanned = 0

for mid in all_market_ids:
    scanned += 1
    if scanned % 100 == 0:
        print(f"  Scanned {scanned}/{len(all_market_ids)}...")

    # Get market data first (cheapest call)
    try:
        market_data = morpho.functions.market(mid).call()
    except:
        continue

    total_supply = market_data[0]
    total_borrow = market_data[2]

    # Skip markets with no supply (no funds at risk)
    if total_supply == 0:
        continue

    active_markets += 1

    # Get market params
    try:
        params = morpho.functions.idToMarketParams(mid).call()
    except:
        continue

    loan_token = params[0]
    coll_token = params[1]
    oracle_addr = params[2]
    lltv = params[4]

    # Get oracle price
    oracle_c = w3.eth.contract(address=Web3.to_checksum_address(oracle_addr), abi=ORACLE_ABI)
    oracle_price = safe_call(oracle_c, "price")
    if oracle_price is None:
        continue

    # Get decimals
    lt_dec = get_decimals(loan_token)
    ct_dec = get_decimals(coll_token)

    # Expected price scale: 10^(36 + lt_dec - ct_dec)
    expected_exp = 36 + lt_dec - ct_dec
    expected_scale = 10 ** expected_exp

    # Price ratio to expected
    if expected_scale > 0 and oracle_price > 0:
        ratio = oracle_price / expected_scale

        # Flag if price seems wildly off (>100x or <0.01x)
        # For a 1:1 pair, ratio should be ~1
        # For ETH/USDC, ratio ~ 2500 (ETH price)
        # For USDC/ETH, ratio ~ 0.0004
        # Flag extreme outliers
        is_suspicious = False

        # These are expected ranges for different pair types
        # Stablecoin pairs: 0.5 to 2
        # Crypto/stablecoin: 0.001 to 200000
        # Any crypto pair: 0.00001 to 10000000

        # Flag truly extreme values (likely misconfigured)
        if ratio > 10000000 or ratio < 0.0000001:
            is_suspicious = True

        # Also check: supply > $1000 equivalent AND unusual ratio
        supply_usd_rough = 0
        lt_sym = get_symbol(loan_token)
        ct_sym = get_symbol(coll_token)

        # Rough USD estimate based on known stablecoins
        if lt_sym in ("USDC", "USDT", "DAI", "PYUSD", "USDS", "GHO", "FRAX", "LUSD", "crvUSD", "USDe"):
            supply_usd_rough = total_supply / (10 ** lt_dec)
        elif lt_sym in ("WETH", "ETH"):
            supply_usd_rough = total_supply / 1e18 * 2500
        elif lt_sym in ("WBTC", "cbBTC"):
            supply_usd_rough = total_supply / 1e8 * 90000

        if is_suspicious and supply_usd_rough > 1000:
            anomalies.append({
                "market_id": mid,
                "loan_token": f"{lt_sym} ({loan_token[:10]}...)",
                "coll_token": f"{ct_sym} ({coll_token[:10]}...)",
                "oracle": oracle_addr,
                "oracle_price": oracle_price,
                "expected_scale": expected_exp,
                "ratio": ratio,
                "supply": total_supply,
                "supply_usd_rough": supply_usd_rough,
                "borrow": total_borrow,
                "lltv": lltv / 1e18,
            })

        # Also flag: markets with very high LLTV (>98%) — these have thin liquidation margin
        if lltv > 0.98e18 and supply_usd_rough > 10000:
            anomalies.append({
                "market_id": mid,
                "loan_token": f"{lt_sym} ({loan_token[:10]}...)",
                "coll_token": f"{ct_sym} ({coll_token[:10]}...)",
                "oracle": oracle_addr,
                "oracle_price": oracle_price,
                "expected_scale": expected_exp,
                "ratio": ratio,
                "supply": total_supply,
                "supply_usd_rough": supply_usd_rough,
                "borrow": total_borrow,
                "lltv": lltv / 1e18,
                "flag": "HIGH_LLTV",
            })

print(f"\nActive markets (supply > 0): {active_markets}")
print(f"Anomalies found: {len(anomalies)}")

# Step 3: Report anomalies
if anomalies:
    print("\n" + "="*80)
    print("ANOMALOUS MARKETS")
    print("="*80)
    for a in anomalies:
        flag = a.get("flag", "PRICE_ANOMALY")
        print(f"\n[{flag}] Market: {a['market_id'][:18]}...")
        print(f"  {a['coll_token']} / {a['loan_token']}")
        print(f"  Oracle: {a['oracle']}")
        print(f"  Price: {a['oracle_price']} (expected ~10^{a['expected_scale']}, ratio: {a['ratio']:.6e})")
        print(f"  Supply: {a['supply']} (~${a['supply_usd_rough']:,.0f})")
        print(f"  Borrow: {a['borrow']}")
        print(f"  LLTV: {a['lltv']:.2%}")
else:
    print("\nNo anomalous markets found.")

# Save results
outpath = "analysis/engagements/bridge-finality-gap/notes/morpho-full-scan-results.json"
os.makedirs(os.path.dirname(outpath), exist_ok=True)
with open(outpath, "w") as f:
    serializable = []
    for a in anomalies:
        sa = {}
        for k, v in a.items():
            sa[k] = str(v) if isinstance(v, (int, float)) else v
        serializable.append(sa)
    json.dump(serializable, f, indent=2)
print(f"\nResults saved to {outpath}")
