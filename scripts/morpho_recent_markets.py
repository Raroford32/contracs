#!/usr/bin/env python3
"""
Find recently created Morpho Blue markets (last 30 days) with activity.
Recent markets are more likely to have:
1. Oracle misconfigurations (new market creators make mistakes)
2. Low TVL (easier to exploit)
3. Novel collateral types (less audited)
"""
import json
import os
from web3 import Web3

RPC = os.environ.get("RPC", "https://eth-mainnet.g.alchemy.com/v2/pLXdY7rYRY10SH_UTLBGH")
w3 = Web3(Web3.HTTPProvider(RPC))

MORPHO = "0xBBBBBbbBBb9cC5e90e3b3Af64bdAF62C37EEFFCb"

MORPHO_EVENTS_ABI = json.loads('''[
  {"anonymous":false,"inputs":[{"indexed":true,"internalType":"Id","name":"id","type":"bytes32"},{"components":[{"internalType":"address","name":"loanToken","type":"address"},{"internalType":"address","name":"collateralToken","type":"address"},{"internalType":"address","name":"oracle","type":"address"},{"internalType":"address","name":"irm","type":"address"},{"internalType":"uint256","name":"lltv","type":"uint256"}],"indexed":false,"internalType":"struct MarketParams","name":"marketParams","type":"tuple"}],"name":"CreateMarket","type":"event"}
]''')

MORPHO_ABI = json.loads('''[
  {"inputs":[{"internalType":"Id","name":"id","type":"bytes32"}],"name":"market","outputs":[{"internalType":"uint128","name":"totalSupplyAssets","type":"uint128"},{"internalType":"uint128","name":"totalSupplyShares","type":"uint128"},{"internalType":"uint128","name":"totalBorrowAssets","type":"uint128"},{"internalType":"uint128","name":"totalBorrowShares","type":"uint128"},{"internalType":"uint128","name":"lastUpdate","type":"uint128"},{"internalType":"uint128","name":"fee","type":"uint128"}],"stateMutability":"view","type":"function"}
]''')

ORACLE_ABI = json.loads('''[
  {"inputs":[],"name":"price","outputs":[{"internalType":"uint256","name":"","type":"uint256"}],"stateMutability":"view","type":"function"},
  {"inputs":[],"name":"SCALE_FACTOR","outputs":[{"internalType":"uint256","name":"","type":"uint256"}],"stateMutability":"view","type":"function"},
  {"inputs":[],"name":"BASE_VAULT","outputs":[{"internalType":"contract IERC4626","name":"","type":"address"}],"stateMutability":"view","type":"function"},
  {"inputs":[],"name":"QUOTE_VAULT","outputs":[{"internalType":"contract IERC4626","name":"","type":"address"}],"stateMutability":"view","type":"function"},
  {"inputs":[],"name":"BASE_FEED_1","outputs":[{"internalType":"contract AggregatorV3Interface","name":"","type":"address"}],"stateMutability":"view","type":"function"},
  {"inputs":[],"name":"BASE_FEED_2","outputs":[{"internalType":"contract AggregatorV3Interface","name":"","type":"address"}],"stateMutability":"view","type":"function"},
  {"inputs":[],"name":"QUOTE_FEED_1","outputs":[{"internalType":"contract AggregatorV3Interface","name":"","type":"address"}],"stateMutability":"view","type":"function"},
  {"inputs":[],"name":"QUOTE_FEED_2","outputs":[{"internalType":"contract AggregatorV3Interface","name":"","type":"address"}],"stateMutability":"view","type":"function"}
]''')

ERC20_ABI = json.loads('''[
  {"inputs":[],"name":"symbol","outputs":[{"internalType":"string","name":"","type":"string"}],"stateMutability":"view","type":"function"},
  {"inputs":[],"name":"decimals","outputs":[{"internalType":"uint8","name":"","type":"uint8"}],"stateMutability":"view","type":"function"},
  {"inputs":[],"name":"totalSupply","outputs":[{"internalType":"uint256","name":"","type":"uint256"}],"stateMutability":"view","type":"function"}
]''')

CHAINLINK_ABI = json.loads('''[
  {"inputs":[],"name":"latestRoundData","outputs":[{"internalType":"uint80","name":"roundId","type":"uint80"},{"internalType":"int256","name":"answer","type":"int256"},{"internalType":"uint256","name":"startedAt","type":"uint256"},{"internalType":"uint256","name":"updatedAt","type":"uint256"},{"internalType":"uint80","name":"answeredInRound","type":"uint80"}],"stateMutability":"view","type":"function"},
  {"inputs":[],"name":"decimals","outputs":[{"internalType":"uint8","name":"","type":"uint8"}],"stateMutability":"view","type":"function"},
  {"inputs":[],"name":"description","outputs":[{"internalType":"string","name":"","type":"string"}],"stateMutability":"view","type":"function"}
]''')

def safe_call(contract, func_name, *args):
    try:
        return getattr(contract.functions, func_name)(*args).call()
    except:
        return None

print(f"Connected. Block: {w3.eth.block_number}")

# Look at last 30 days of markets (roughly 200k blocks)
latest = w3.eth.block_number
start_block = latest - 200000  # ~30 days

morpho = w3.eth.contract(address=Web3.to_checksum_address(MORPHO), abi=MORPHO_EVENTS_ABI + MORPHO_ABI)

print(f"[1] Scanning blocks {start_block} to {latest} for recent markets...")
recent_markets = []
chunk_size = 50000

for from_block in range(start_block, latest + 1, chunk_size):
    to_block = min(from_block + chunk_size - 1, latest)
    try:
        events = morpho.events.CreateMarket.get_logs(from_block=from_block, to_block=to_block)
        for evt in events:
            recent_markets.append({
                "id": evt.args.id.hex(),
                "loanToken": evt.args.marketParams.loanToken,
                "collateralToken": evt.args.marketParams.collateralToken,
                "oracle": evt.args.marketParams.oracle,
                "lltv": evt.args.marketParams.lltv,
                "block": evt.blockNumber,
            })
    except:
        pass

print(f"Found {len(recent_markets)} recently created markets")

# Check each for activity and oracle config
print("\n[2] Analyzing recent markets with supply...")
ZERO = "0x0000000000000000000000000000000000000000"

active_recent = []
for m in recent_markets:
    try:
        market_data = morpho.functions.market(bytes.fromhex(m["id"])).call()
        total_supply = market_data[0]
        total_borrow = market_data[2]
    except:
        continue
    
    if total_supply == 0:
        continue
    
    lt = w3.eth.contract(address=Web3.to_checksum_address(m["loanToken"]), abi=ERC20_ABI)
    ct = w3.eth.contract(address=Web3.to_checksum_address(m["collateralToken"]), abi=ERC20_ABI)
    lt_sym = safe_call(lt, "symbol") or "?"
    lt_dec = safe_call(lt, "decimals") or 18
    ct_sym = safe_call(ct, "symbol") or "?"
    ct_dec = safe_call(ct, "decimals") or 18
    
    supply_usd_approx = total_supply / (10 ** lt_dec)
    borrow_usd_approx = total_borrow / (10 ** lt_dec)
    
    # Get oracle price
    oc = w3.eth.contract(address=Web3.to_checksum_address(m["oracle"]), abi=ORACLE_ABI)
    oracle_price = safe_call(oc, "price")
    scale_factor = safe_call(oc, "SCALE_FACTOR")
    
    # Check oracle type
    base_vault = safe_call(oc, "BASE_VAULT")
    quote_vault = safe_call(oc, "QUOTE_VAULT")
    bf1 = safe_call(oc, "BASE_FEED_1")
    bf2 = safe_call(oc, "BASE_FEED_2")
    qf1 = safe_call(oc, "QUOTE_FEED_1")
    qf2 = safe_call(oc, "QUOTE_FEED_2")
    
    is_chainlink_v2 = scale_factor is not None
    has_vault = (base_vault and base_vault != ZERO) or (quote_vault and quote_vault != ZERO)
    has_no_feeds = (not bf1 or bf1 == ZERO) and (not bf2 or bf2 == ZERO) and (not qf1 or qf1 == ZERO) and (not qf2 or qf2 == ZERO)
    
    # Flag interesting markets
    flags = []
    if has_vault:
        flags.append("HAS_VAULT")
    if has_no_feeds and is_chainlink_v2:
        flags.append("NO_CHAINLINK_FEEDS")
    if not is_chainlink_v2:
        flags.append("CUSTOM_ORACLE")
    if m["lltv"] > 0.95e18:
        flags.append(f"HIGH_LLTV({m['lltv']/1e18:.2%})")
    
    # Check for novel collateral tokens (not well-known)
    well_known = ["WETH", "USDC", "USDT", "DAI", "WBTC", "wstETH", "weETH", "sUSDe", "USDe",
                   "cbBTC", "sUSDS", "stUSDS", "PYUSD", "USDS", "GHO", "FRAX", "cbETH",
                   "rETH", "ezETH", "rsETH", "LBTC", "pufETH", "sDAI", "sFRAX"]
    if ct_sym not in well_known:
        flags.append(f"NOVEL_COLLATERAL({ct_sym})")
    
    if flags or supply_usd_approx > 10:
        active_recent.append({
            "id": m["id"],
            "pair": f"{ct_sym}/{lt_sym}",
            "ct_addr": m["collateralToken"],
            "lt_addr": m["loanToken"],
            "oracle": m["oracle"],
            "price": oracle_price,
            "scale_factor": scale_factor,
            "supply": supply_usd_approx,
            "borrow": borrow_usd_approx,
            "lltv": m["lltv"] / 1e18,
            "block": m["block"],
            "flags": flags,
            "lt_dec": lt_dec,
            "ct_dec": ct_dec,
            "base_vault": base_vault,
            "bf1": bf1,
        })

# Sort by supply and print
active_recent.sort(key=lambda x: x["supply"], reverse=True)

print(f"\n{'='*80}")
print(f"RECENT ACTIVE MARKETS ({len(active_recent)} with supply > 0)")
print(f"{'='*80}")

for m in active_recent[:50]:  # Top 50
    flag_str = " | ".join(m["flags"]) if m["flags"] else "standard"
    print(f"\n  {m['pair']} | Supply: {m['supply']:,.2f} | Borrow: {m['borrow']:,.2f} | LLTV: {m['lltv']:.2%}")
    print(f"    Block: {m['block']} | Oracle: {m['oracle']}")
    print(f"    Price: {m['price']}")
    print(f"    Flags: {flag_str}")

