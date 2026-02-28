#!/usr/bin/env python3
"""
Scan Curve Lending markets and Silo V2 for oracle misconfigurations.
Also check Morpho markets created in last 7 days (fresh misconfig window).
"""

import json
import os
from web3 import Web3

RPC = os.environ.get("RPC", "https://eth-mainnet.g.alchemy.com/v2/pLXdY7rYRY10SH_UTLBGH")
w3 = Web3(Web3.HTTPProvider(RPC))

print(f"Connected. Block: {w3.eth.block_number}")

ERC20_ABI = json.loads('''[
  {"inputs":[],"name":"symbol","outputs":[{"internalType":"string","name":"","type":"string"}],"stateMutability":"view","type":"function"},
  {"inputs":[],"name":"decimals","outputs":[{"internalType":"uint8","name":"","type":"uint8"}],"stateMutability":"view","type":"function"},
  {"inputs":[{"internalType":"address","name":"","type":"address"}],"name":"balanceOf","outputs":[{"internalType":"uint256","name":"","type":"uint256"}],"stateMutability":"view","type":"function"}
]''')

def safe_call(contract, func_name, *args):
    try:
        return getattr(contract.functions, func_name)(*args).call()
    except:
        return None

def get_sym(addr):
    if addr.lower() in ("0xeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeee", "0x0000000000000000000000000000000000000000"):
        return "ETH"
    c = w3.eth.contract(address=Web3.to_checksum_address(addr), abi=ERC20_ABI)
    return safe_call(c, "symbol") or "?"

def get_dec(addr):
    if addr.lower() in ("0xeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeee",):
        return 18
    c = w3.eth.contract(address=Web3.to_checksum_address(addr), abi=ERC20_ABI)
    return safe_call(c, "decimals") or 18

# ============================================================
# 1. CURVE LENDING FACTORY — Enumerate all markets
# ============================================================
print("="*80)
print("1. CURVE LENDING FACTORY MARKETS")
print("="*80)

CURVE_FACTORY = "0xeA6876DDE9e3467564acBeE1Ed5bac88783205E0"
CURVE_FACTORY_ABI = json.loads('''[
  {"inputs":[],"name":"market_count","outputs":[{"internalType":"uint256","name":"","type":"uint256"}],"stateMutability":"view","type":"function"},
  {"inputs":[{"internalType":"uint256","name":"n","type":"uint256"}],"name":"vaults","outputs":[{"internalType":"address","name":"","type":"address"}],"stateMutability":"view","type":"function"}
]''')

CURVE_VAULT_ABI = json.loads('''[
  {"inputs":[],"name":"asset","outputs":[{"internalType":"address","name":"","type":"address"}],"stateMutability":"view","type":"function"},
  {"inputs":[],"name":"totalAssets","outputs":[{"internalType":"uint256","name":"","type":"uint256"}],"stateMutability":"view","type":"function"},
  {"inputs":[],"name":"controller","outputs":[{"internalType":"address","name":"","type":"address"}],"stateMutability":"view","type":"function"},
  {"inputs":[],"name":"symbol","outputs":[{"internalType":"string","name":"","type":"string"}],"stateMutability":"view","type":"function"},
  {"inputs":[],"name":"priceOracle","outputs":[{"internalType":"address","name":"","type":"address"}],"stateMutability":"view","type":"function"}
]''')

CURVE_CONTROLLER_ABI = json.loads('''[
  {"inputs":[],"name":"collateral_token","outputs":[{"internalType":"address","name":"","type":"address"}],"stateMutability":"view","type":"function"},
  {"inputs":[],"name":"total_debt","outputs":[{"internalType":"uint256","name":"","type":"uint256"}],"stateMutability":"view","type":"function"},
  {"inputs":[],"name":"amm","outputs":[{"internalType":"address","name":"","type":"address"}],"stateMutability":"view","type":"function"},
  {"inputs":[],"name":"monetary_policy","outputs":[{"internalType":"address","name":"","type":"address"}],"stateMutability":"view","type":"function"}
]''')

CURVE_AMM_ABI = json.loads('''[
  {"inputs":[],"name":"price_oracle","outputs":[{"internalType":"uint256","name":"","type":"uint256"}],"stateMutability":"view","type":"function"},
  {"inputs":[],"name":"get_p","outputs":[{"internalType":"uint256","name":"","type":"uint256"}],"stateMutability":"view","type":"function"}
]''')

cf = w3.eth.contract(address=Web3.to_checksum_address(CURVE_FACTORY), abi=CURVE_FACTORY_ABI)
market_count = safe_call(cf, "market_count")
print(f"  Factory: {CURVE_FACTORY}")
print(f"  Total markets: {market_count}")

if market_count:
    for i in range(market_count):
        vault_addr = safe_call(cf, "vaults", i)
        if vault_addr:
            vault = w3.eth.contract(address=Web3.to_checksum_address(vault_addr), abi=CURVE_VAULT_ABI)
            asset = safe_call(vault, "asset")
            total = safe_call(vault, "totalAssets") or 0
            controller = safe_call(vault, "controller")
            vault_sym = safe_call(vault, "symbol") or "?"
            oracle = safe_call(vault, "priceOracle")

            asset_sym = get_sym(asset) if asset else "?"
            asset_dec = get_dec(asset) if asset else 18
            total_amount = total / (10 ** asset_dec)

            # Get controller details
            coll_sym = "?"
            total_debt = 0
            amm_addr = None
            if controller:
                ctrl = w3.eth.contract(address=Web3.to_checksum_address(controller), abi=CURVE_CONTROLLER_ABI)
                coll = safe_call(ctrl, "collateral_token")
                if coll:
                    coll_sym = get_sym(coll)
                total_debt = (safe_call(ctrl, "total_debt") or 0) / 1e18
                amm_addr = safe_call(ctrl, "amm")

            # Get AMM oracle prices (LLAMMA)
            oracle_price = None
            spot_price = None
            if amm_addr:
                amm = w3.eth.contract(address=Web3.to_checksum_address(amm_addr), abi=CURVE_AMM_ABI)
                oracle_price = safe_call(amm, "price_oracle")
                spot_price = safe_call(amm, "get_p")

            # Determine rough USD TVL
            usd_tvl = total_amount
            if asset_sym in ("WETH", "ETH"):
                usd_tvl = total_amount * 1900
            elif asset_sym in ("WBTC", "cbBTC"):
                usd_tvl = total_amount * 90000

            if usd_tvl > 1000 or total_debt > 1000:
                print(f"\n  Market #{i}: {vault_sym}")
                print(f"    Vault: {vault_addr}")
                print(f"    Loan: {asset_sym} | Collateral: {coll_sym}")
                print(f"    Total Assets: {total_amount:,.2f} {asset_sym} (~${usd_tvl:,.0f})")
                print(f"    Total Debt: {total_debt:,.2f} crvUSD")
                print(f"    Oracle contract: {oracle}")
                if oracle_price:
                    print(f"    AMM oracle price: {oracle_price / 1e18:,.4f}")
                if spot_price:
                    print(f"    AMM spot price: {spot_price / 1e18:,.4f}")
                if oracle_price and spot_price:
                    dev = abs(oracle_price - spot_price) / oracle_price * 100
                    print(f"    Oracle-Spot deviation: {dev:.2f}%")
                    if dev > 5:
                        print(f"    *** LARGE DEVIATION ***")

# ============================================================
# 2. MORPHO — Markets created in last 7 DAYS (freshest misconfig window)
# ============================================================
print("\n\n" + "="*80)
print("2. MORPHO BLUE — MARKETS CREATED IN LAST 7 DAYS")
print("="*80)

MORPHO = "0xBBBBBbbBBb9cC5e90e3b3Af64bdAF62C37EEFFCb"
CREATE_MARKET_TOPIC = "0xac4b2400f169220b0c0afdde7a0b32e775ba727ea1cb30b35f935cdaab8683ac"

MORPHO_ABI = json.loads('''[
  {"inputs":[{"internalType":"Id","name":"id","type":"bytes32"}],"name":"idToMarketParams","outputs":[{"components":[{"internalType":"address","name":"loanToken","type":"address"},{"internalType":"address","name":"collateralToken","type":"address"},{"internalType":"address","name":"oracle","type":"address"},{"internalType":"address","name":"irm","type":"address"},{"internalType":"uint256","name":"lltv","type":"uint256"}],"internalType":"struct MarketParams","name":"","type":"tuple"}],"stateMutability":"view","type":"function"},
  {"inputs":[{"internalType":"Id","name":"id","type":"bytes32"}],"name":"market","outputs":[{"internalType":"uint128","name":"totalSupplyAssets","type":"uint128"},{"internalType":"uint128","name":"totalSupplyShares","type":"uint128"},{"internalType":"uint128","name":"totalBorrowAssets","type":"uint128"},{"internalType":"uint128","name":"totalBorrowShares","type":"uint128"},{"internalType":"uint128","name":"lastUpdate","type":"uint128"},{"internalType":"uint128","name":"fee","type":"uint128"}],"stateMutability":"view","type":"function"}
]''')

ORACLE_ABI = json.loads('''[
  {"inputs":[],"name":"price","outputs":[{"internalType":"uint256","name":"","type":"uint256"}],"stateMutability":"view","type":"function"}
]''')

morpho = w3.eth.contract(address=Web3.to_checksum_address(MORPHO), abi=MORPHO_ABI)

latest = w3.eth.block_number
seven_days = 50400  # ~7 days of blocks

logs = w3.eth.get_logs({
    "address": Web3.to_checksum_address(MORPHO),
    "topics": [CREATE_MARKET_TOPIC],
    "fromBlock": latest - seven_days,
    "toBlock": latest,
})

print(f"  Markets created in last 7 days: {len(logs)}")

for log in logs:
    market_id = bytes(log["topics"][1])
    block_num = log["blockNumber"]

    params = safe_call(morpho, "idToMarketParams", market_id)
    market_data = morpho.functions.market(market_id).call()

    if params:
        loan_token = params[0]
        coll_token = params[1]
        oracle_addr = params[2]
        lltv = params[4]

        supply = market_data[0]
        borrow = market_data[2]

        lt_sym = get_sym(loan_token)
        ct_sym = get_sym(coll_token)
        lt_dec = get_dec(loan_token)
        ct_dec = get_dec(coll_token)

        # Get oracle price
        oc = w3.eth.contract(address=Web3.to_checksum_address(oracle_addr), abi=ORACLE_ABI)
        oracle_price = safe_call(oc, "price")

        # Check price sanity
        price_flag = ""
        if oracle_price:
            expected_scale = 36 + lt_dec - ct_dec
            ratio = oracle_price / (10 ** expected_scale)
            if ratio > 10000000 or ratio < 0.0000001:
                price_flag = "*** EXTREME PRICE ***"
            elif ratio > 100000 or ratio < 0.00001:
                price_flag = "* UNUSUAL PRICE *"

        # Rough USD
        supply_usd = supply / (10 ** lt_dec)
        if lt_sym in ("WETH", "ETH"):
            supply_usd *= 1900
        elif lt_sym in ("WBTC", "cbBTC"):
            supply_usd *= 90000

        print(f"\n  Block {block_num} | {ct_sym}/{lt_sym} | LLTV: {lltv/1e18:.0%}")
        print(f"    Oracle: {oracle_addr}")
        if oracle_price:
            print(f"    Price: {oracle_price} (ratio: {ratio:.6e}) {price_flag}")
        else:
            print(f"    Price: FAILED TO READ")
        print(f"    Supply: {supply} (~${supply_usd:,.0f}) | Borrow: {borrow}")

        if price_flag:
            print(f"    !!! INVESTIGATE THIS MARKET !!!")

# ============================================================
# 3. SPARK PROTOCOL — Check all oracle prices
# ============================================================
print("\n\n" + "="*80)
print("3. SPARK PROTOCOL — ORACLE PRICE CHECK")
print("="*80)

SPARK_POOL = "0xC13e21B648A5Ee794902342038FF3aDAB66BE987"
SPARK_ORACLE = "0x8105f69D9C41644c6A0803fDA7D03Aa70996cFD2"

POOL_ABI = json.loads('''[
  {"inputs":[],"name":"getReservesList","outputs":[{"internalType":"address[]","name":"","type":"address[]"}],"stateMutability":"view","type":"function"}
]''')

ORACLE_V3_ABI = json.loads('''[
  {"inputs":[{"internalType":"address","name":"asset","type":"address"}],"name":"getAssetPrice","outputs":[{"internalType":"uint256","name":"","type":"uint256"}],"stateMutability":"view","type":"function"},
  {"inputs":[{"internalType":"address","name":"asset","type":"address"}],"name":"getSourceOfAsset","outputs":[{"internalType":"address","name":"","type":"address"}],"stateMutability":"view","type":"function"}
]''')

pool = w3.eth.contract(address=Web3.to_checksum_address(SPARK_POOL), abi=POOL_ABI)
spark_oracle = w3.eth.contract(address=Web3.to_checksum_address(SPARK_ORACLE), abi=ORACLE_V3_ABI)

reserves = safe_call(pool, "getReservesList") or []
print(f"  Reserves: {len(reserves)}")

# Compare Spark prices with Aave prices for the same assets
AAVE_ORACLE = "0x54586bE62E3c3580375aE3723C145253060Ca0C2"
aave_oracle = w3.eth.contract(address=Web3.to_checksum_address(AAVE_ORACLE), abi=ORACLE_V3_ABI)

for r in reserves:
    sym = get_sym(r)
    spark_price = safe_call(spark_oracle, "getAssetPrice", Web3.to_checksum_address(r))
    aave_price = safe_call(aave_oracle, "getAssetPrice", Web3.to_checksum_address(r))
    source = safe_call(spark_oracle, "getSourceOfAsset", Web3.to_checksum_address(r))

    if spark_price:
        usd = spark_price / 1e8
        flag = ""

        if aave_price and aave_price > 0:
            dev = abs(spark_price - aave_price) / aave_price * 100
            if dev > 1:
                flag = f"*** {dev:.1f}% DIVERGENCE vs Aave ***"

        print(f"  {sym:12s}: ${usd:>12,.2f} | Aave: ${(aave_price or 0)/1e8:>12,.2f} | source: {str(source)[:20]}... {flag}")

print("\n\nDone.")
