#!/usr/bin/env python3
"""
Scan for RECENTLY DEPLOYED oracle-like contracts on Ethereum mainnet.
Fresh oracles are highest-risk for misconfigurations.

Approach: Search for contracts that were created in the last 14 days
and implement a price() or latestRoundData() function.
We detect these by looking for contract creation transactions
and then probing the deployed bytecode for oracle function selectors.
"""

import json
import os
from web3 import Web3

RPC = os.environ.get("RPC", "https://eth-mainnet.g.alchemy.com/v2/pLXdY7rYRY10SH_UTLBGH")
w3 = Web3(Web3.HTTPProvider(RPC))

print(f"Connected. Block: {w3.eth.block_number}")

# Oracle function selectors we're looking for in bytecode
ORACLE_SELECTORS = {
    "a035b1fe": "price()",               # Morpho oracle
    "feaf968c": "latestRoundData()",      # Chainlink
    "50d25bcd": "latestAnswer()",         # Chainlink
    "b4596f3b": "getExchangeRate()",      # Fluid oracle
    "07211ef7": "getPrice(address)",      # Various
    "9d1b464a": "oracle()",               # Various
    "fc57d4df": "getUnderlyingPrice(address)", # Compound
}

# Instead of scanning ALL blocks (too expensive), let's look at
# contracts that were deployed by known oracle deployer addresses
# or check the bytecode of recently created contracts on Morpho/Aave/Spark

# Most productive: check if any Morpho oracle was deployed in the last 14 days
# by scanning for contracts with the Morpho oracle ABI

# Actually, let's just check all the Morpho market oracles that were created
# in the last 14 days (from the market creation scan we did earlier)
# and verify their price makes sense

MORPHO = "0xBBBBBbbBBb9cC5e90e3b3Af64bdAF62C37EEFFCb"
CREATE_MARKET_TOPIC = "0xac4b2400f169220b0c0afdde7a0b32e775ba727ea1cb30b35f935cdaab8683ac"

MORPHO_ABI = json.loads('''[
  {"inputs":[{"internalType":"Id","name":"id","type":"bytes32"}],"name":"idToMarketParams","outputs":[{"components":[{"internalType":"address","name":"loanToken","type":"address"},{"internalType":"address","name":"collateralToken","type":"address"},{"internalType":"address","name":"oracle","type":"address"},{"internalType":"address","name":"irm","type":"address"},{"internalType":"uint256","name":"lltv","type":"uint256"}],"internalType":"struct MarketParams","name":"","type":"tuple"}],"stateMutability":"view","type":"function"},
  {"inputs":[{"internalType":"Id","name":"id","type":"bytes32"}],"name":"market","outputs":[{"internalType":"uint128","name":"totalSupplyAssets","type":"uint128"},{"internalType":"uint128","name":"totalSupplyShares","type":"uint128"},{"internalType":"uint128","name":"totalBorrowAssets","type":"uint128"},{"internalType":"uint128","name":"totalBorrowShares","type":"uint128"},{"internalType":"uint128","name":"lastUpdate","type":"uint128"},{"internalType":"uint128","name":"fee","type":"uint128"}],"stateMutability":"view","type":"function"}
]''')

MORPHO_ORACLE_V2_ABI = json.loads('''[
  {"inputs":[],"name":"price","outputs":[{"internalType":"uint256","name":"","type":"uint256"}],"stateMutability":"view","type":"function"},
  {"inputs":[],"name":"BASE_VAULT","outputs":[{"internalType":"contract IERC4626","name":"","type":"address"}],"stateMutability":"view","type":"function"},
  {"inputs":[],"name":"QUOTE_VAULT","outputs":[{"internalType":"contract IERC4626","name":"","type":"address"}],"stateMutability":"view","type":"function"},
  {"inputs":[],"name":"BASE_FEED_1","outputs":[{"internalType":"contract AggregatorV3Interface","name":"","type":"address"}],"stateMutability":"view","type":"function"},
  {"inputs":[],"name":"BASE_FEED_2","outputs":[{"internalType":"contract AggregatorV3Interface","name":"","type":"address"}],"stateMutability":"view","type":"function"},
  {"inputs":[],"name":"QUOTE_FEED_1","outputs":[{"internalType":"contract AggregatorV3Interface","name":"","type":"address"}],"stateMutability":"view","type":"function"},
  {"inputs":[],"name":"QUOTE_FEED_2","outputs":[{"internalType":"contract AggregatorV3Interface","name":"","type":"address"}],"stateMutability":"view","type":"function"},
  {"inputs":[],"name":"SCALE_FACTOR","outputs":[{"internalType":"uint256","name":"","type":"uint256"}],"stateMutability":"view","type":"function"}
]''')

CHAINLINK_ABI = json.loads('''[
  {"inputs":[],"name":"latestRoundData","outputs":[{"internalType":"uint80","name":"roundId","type":"uint80"},{"internalType":"int256","name":"answer","type":"int256"},{"internalType":"uint256","name":"startedAt","type":"uint256"},{"internalType":"uint256","name":"updatedAt","type":"uint256"},{"internalType":"uint80","name":"answeredInRound","type":"uint80"}],"stateMutability":"view","type":"function"},
  {"inputs":[],"name":"decimals","outputs":[{"internalType":"uint8","name":"","type":"uint8"}],"stateMutability":"view","type":"function"},
  {"inputs":[],"name":"description","outputs":[{"internalType":"string","name":"","type":"string"}],"stateMutability":"view","type":"function"}
]''')

ERC20_ABI = json.loads('''[
  {"inputs":[],"name":"symbol","outputs":[{"internalType":"string","name":"","type":"string"}],"stateMutability":"view","type":"function"},
  {"inputs":[],"name":"decimals","outputs":[{"internalType":"uint8","name":"","type":"uint8"}],"stateMutability":"view","type":"function"}
]''')

VAULT_ABI = json.loads('''[
  {"inputs":[],"name":"asset","outputs":[{"internalType":"address","name":"","type":"address"}],"stateMutability":"view","type":"function"},
  {"inputs":[],"name":"totalAssets","outputs":[{"internalType":"uint256","name":"","type":"uint256"}],"stateMutability":"view","type":"function"},
  {"inputs":[],"name":"totalSupply","outputs":[{"internalType":"uint256","name":"","type":"uint256"}],"stateMutability":"view","type":"function"},
  {"inputs":[{"internalType":"uint256","name":"assets","type":"uint256"}],"name":"convertToShares","outputs":[{"internalType":"uint256","name":"","type":"uint256"}],"stateMutability":"view","type":"function"}
]''')

def safe_call(contract, func_name, *args):
    try:
        return getattr(contract.functions, func_name)(*args).call()
    except:
        return None

def get_sym(addr):
    c = w3.eth.contract(address=Web3.to_checksum_address(addr), abi=ERC20_ABI)
    return safe_call(c, "symbol") or "?"

def get_dec(addr):
    c = w3.eth.contract(address=Web3.to_checksum_address(addr), abi=ERC20_ABI)
    return safe_call(c, "decimals") or 18

morpho = w3.eth.contract(address=Web3.to_checksum_address(MORPHO), abi=MORPHO_ABI)

# Get markets from last 14 days
latest = w3.eth.block_number
fourteen_days = 100800
start = latest - fourteen_days

print(f"Scanning Morpho markets from block {start} to {latest} (last ~14 days)")

logs = w3.eth.get_logs({
    "address": Web3.to_checksum_address(MORPHO),
    "topics": [CREATE_MARKET_TOPIC],
    "fromBlock": start,
    "toBlock": latest,
})

print(f"Markets created in last 14 days: {len(logs)}")

ZERO = "0x0000000000000000000000000000000000000000"

for log in logs:
    market_id = bytes(log["topics"][1])
    block_num = log["blockNumber"]

    params = safe_call(morpho, "idToMarketParams", market_id)
    if not params:
        continue

    loan_token = params[0]
    coll_token = params[1]
    oracle_addr = params[2]
    lltv = params[4]

    market_data = morpho.functions.market(market_id).call()
    supply = market_data[0]
    borrow = market_data[2]

    lt_sym = get_sym(loan_token)
    ct_sym = get_sym(coll_token)
    lt_dec = get_dec(loan_token)
    ct_dec = get_dec(coll_token)

    # Deep-check the oracle
    oc = w3.eth.contract(address=Web3.to_checksum_address(oracle_addr), abi=MORPHO_ORACLE_V2_ABI)
    price = safe_call(oc, "price")
    base_vault = safe_call(oc, "BASE_VAULT")
    quote_vault = safe_call(oc, "QUOTE_VAULT")
    base_feed1 = safe_call(oc, "BASE_FEED_1")
    base_feed2 = safe_call(oc, "BASE_FEED_2")
    quote_feed1 = safe_call(oc, "QUOTE_FEED_1")
    quote_feed2 = safe_call(oc, "QUOTE_FEED_2")
    scale_factor = safe_call(oc, "SCALE_FACTOR")

    # Skip if no supply (no money at risk)
    supply_usd_rough = supply / (10 ** lt_dec)
    if lt_sym in ("WETH", "ETH"):
        supply_usd_rough *= 1900
    elif lt_sym in ("WBTC", "cbBTC"):
        supply_usd_rough *= 90000

    flags = []

    # Check for QUOTE_VAULT (loan-side manipulation vector)
    if quote_vault and quote_vault != ZERO:
        flags.append("HAS_QUOTE_VAULT")

    # Check for BASE_VAULT (collateral-side vault oracle)
    if base_vault and base_vault != ZERO:
        # Check vault health
        vault = w3.eth.contract(address=Web3.to_checksum_address(base_vault), abi=VAULT_ABI)
        vault_total_assets = safe_call(vault, "totalAssets") or 0
        vault_total_supply = safe_call(vault, "totalSupply") or 1

        # Check if vault has extremely low supply (first-depositor attack)
        if vault_total_supply < 1e6:  # Very low supply
            flags.append("VAULT_LOW_SUPPLY")
        if vault_total_supply > 0 and vault_total_assets > 0:
            rate = vault_total_assets / vault_total_supply
            if rate > 10:
                flags.append(f"VAULT_HIGH_RATE({rate:.2f})")

    # Check feeds
    if base_feed1 and base_feed1 != ZERO:
        feed = w3.eth.contract(address=Web3.to_checksum_address(base_feed1), abi=CHAINLINK_ABI)
        desc = safe_call(feed, "description")
        feed_dec = safe_call(feed, "decimals")
        latest_data = safe_call(feed, "latestRoundData")
        if latest_data:
            feed_price = latest_data[1]
            updated_at = latest_data[3]
            now = w3.eth.get_block("latest")["timestamp"]
            staleness = now - updated_at
            if staleness > 86400:
                flags.append(f"STALE_BASE_FEED1({staleness/3600:.0f}h)")
            # Check if feed name matches expected token
            if desc:
                # Flag if the feed description doesn't match the collateral token
                desc_lower = desc.lower()
                ct_lower = ct_sym.lower()
                if ct_lower not in desc_lower and "usd" not in desc_lower:
                    flags.append(f"FEED_MISMATCH(coll={ct_sym},feed={desc})")

    # Only print markets with supply > $100 OR with flags
    if supply_usd_rough > 100 or flags:
        flag_str = " | ".join(flags) if flags else "clean"
        print(f"\n  Block {block_num} | {ct_sym}/{lt_sym} | LLTV: {lltv/1e18:.0%} | Supply: ~${supply_usd_rough:,.0f}")
        print(f"    Oracle: {oracle_addr}")
        if price:
            expected_scale = 36 + lt_dec - ct_dec
            ratio = price / (10 ** expected_scale)
            print(f"    Price ratio: {ratio:.6e}")
        if base_vault and base_vault != ZERO:
            print(f"    BASE_VAULT: {base_vault}")
        if quote_vault and quote_vault != ZERO:
            print(f"    QUOTE_VAULT: {quote_vault}")
        if base_feed1 and base_feed1 != ZERO:
            feed = w3.eth.contract(address=Web3.to_checksum_address(base_feed1), abi=CHAINLINK_ABI)
            desc = safe_call(feed, "description")
            print(f"    BASE_FEED_1: {base_feed1} ({desc})")
        if scale_factor:
            print(f"    SCALE_FACTOR: {scale_factor}")
        print(f"    Flags: [{flag_str}]")

        if "HAS_QUOTE_VAULT" in flag_str:
            print(f"    !!! QUOTE_VAULT SET — LOAN-SIDE MANIPULATION POSSIBLE !!!")
        if "FEED_MISMATCH" in flag_str:
            print(f"    !!! FEED NAME DOESN'T MATCH COLLATERAL TOKEN !!!")
        if "STALE" in flag_str:
            print(f"    !!! STALE ORACLE FEED !!!")
        if "VAULT_LOW_SUPPLY" in flag_str:
            print(f"    !!! VAULT HAS VERY LOW SUPPLY — FIRST DEPOSITOR RISK !!!")

print("\n\nDone.")
