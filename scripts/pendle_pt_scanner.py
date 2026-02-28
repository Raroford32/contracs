#!/usr/bin/env python3
"""
Scan Morpho Blue markets for Pendle PT collateral tokens.
Check what oracle they use and how PT price is derived.
"""
import json
import os
from web3 import Web3

RPC = os.environ.get("RPC", "https://eth-mainnet.g.alchemy.com/v2/pLXdY7rYRY10SH_UTLBGH")
w3 = Web3(Web3.HTTPProvider(RPC))

# Known Pendle PT token addresses on Ethereum mainnet
# These are the most common PT tokens used as collateral
PENDLE_TOKENS = {
    # PT-sUSDe (various maturities)
    "0x3b3Da60C5e15fD06A5F3A4f16E72824a7bC0e5C4": "PT-sUSDe-27MAR2025",
    "0xE00bd3Df25fb187d6ABBB620b3dfd19839947b81": "PT-sUSDe-29MAY2025",
    "0xb7c0F8b99e36e97F3EE9d74C0843b0a9F67Bf8a9": "PT-sUSDe-26JUN2025",
    # PT-eETH
    "0x7c46d4FE9F4D83B88d1f1b0F7e5fD6Ee0E6C7B2B": "PT-eETH",
    # PT-weETH
    "0xc69Ad9baB1dEE23F4605a82b3354F8E40d665F49": "PT-weETH-26DEC2024",
    "0x6ee2b5e19ECBa773a352E5B21415Dc419A700d1D": "PT-weETH-26JUN2025",
    # PT-rsETH 
    "0xB05cAbCd99cf9a73b19805edefC5f67CA5d1895E": "PT-rsETH-26DEC2024",
    # PT-USDe
    "0xa0021EF8970104c2d008F38D92f115ad56a9B8e1": "PT-USDe-27MAR2025",
}

# Morpho Blue
MORPHO = "0xBBBBBbbBBb9cC5e90e3b3Af64bdAF62C37EEFFCb"

MORPHO_ABI = json.loads('''[
  {"inputs":[{"internalType":"Id","name":"id","type":"bytes32"}],"name":"idToMarketParams","outputs":[{"components":[{"internalType":"address","name":"loanToken","type":"address"},{"internalType":"address","name":"collateralToken","type":"address"},{"internalType":"address","name":"oracle","type":"address"},{"internalType":"address","name":"irm","type":"address"},{"internalType":"uint256","name":"lltv","type":"uint256"}],"internalType":"struct MarketParams","name":"","type":"tuple"}],"stateMutability":"view","type":"function"},
  {"inputs":[{"internalType":"Id","name":"id","type":"bytes32"}],"name":"market","outputs":[{"internalType":"uint128","name":"totalSupplyAssets","type":"uint128"},{"internalType":"uint128","name":"totalSupplyShares","type":"uint128"},{"internalType":"uint128","name":"totalBorrowAssets","type":"uint128"},{"internalType":"uint128","name":"totalBorrowShares","type":"uint128"},{"internalType":"uint128","name":"lastUpdate","type":"uint128"},{"internalType":"uint128","name":"fee","type":"uint128"}],"stateMutability":"view","type":"function"}
]''')

ORACLE_V2_ABI = json.loads('''[
  {"inputs":[],"name":"BASE_VAULT","outputs":[{"internalType":"contract IERC4626","name":"","type":"address"}],"stateMutability":"view","type":"function"},
  {"inputs":[],"name":"QUOTE_VAULT","outputs":[{"internalType":"contract IERC4626","name":"","type":"address"}],"stateMutability":"view","type":"function"},
  {"inputs":[],"name":"BASE_FEED_1","outputs":[{"internalType":"contract AggregatorV3Interface","name":"","type":"address"}],"stateMutability":"view","type":"function"},
  {"inputs":[],"name":"BASE_FEED_2","outputs":[{"internalType":"contract AggregatorV3Interface","name":"","type":"address"}],"stateMutability":"view","type":"function"},
  {"inputs":[],"name":"QUOTE_FEED_1","outputs":[{"internalType":"contract AggregatorV3Interface","name":"","type":"address"}],"stateMutability":"view","type":"function"},
  {"inputs":[],"name":"QUOTE_FEED_2","outputs":[{"internalType":"contract AggregatorV3Interface","name":"","type":"address"}],"stateMutability":"view","type":"function"},
  {"inputs":[],"name":"SCALE_FACTOR","outputs":[{"internalType":"uint256","name":"","type":"uint256"}],"stateMutability":"view","type":"function"},
  {"inputs":[],"name":"price","outputs":[{"internalType":"uint256","name":"","type":"uint256"}],"stateMutability":"view","type":"function"},
  {"inputs":[],"name":"BASE_VAULT_CONVERSION_SAMPLE","outputs":[{"internalType":"uint256","name":"","type":"uint256"}],"stateMutability":"view","type":"function"},
  {"inputs":[],"name":"QUOTE_VAULT_CONVERSION_SAMPLE","outputs":[{"internalType":"uint256","name":"","type":"uint256"}],"stateMutability":"view","type":"function"}
]''')

ERC20_ABI = json.loads('''[
  {"inputs":[],"name":"name","outputs":[{"internalType":"string","name":"","type":"string"}],"stateMutability":"view","type":"function"},
  {"inputs":[],"name":"symbol","outputs":[{"internalType":"string","name":"","type":"string"}],"stateMutability":"view","type":"function"},
  {"inputs":[],"name":"decimals","outputs":[{"internalType":"uint8","name":"","type":"uint8"}],"stateMutability":"view","type":"function"},
  {"inputs":[{"internalType":"address","name":"","type":"address"}],"name":"balanceOf","outputs":[{"internalType":"uint256","name":"","type":"uint256"}],"stateMutability":"view","type":"function"},
  {"inputs":[],"name":"totalSupply","outputs":[{"internalType":"uint256","name":"","type":"uint256"}],"stateMutability":"view","type":"function"}
]''')

def safe_call(contract, func_name, *args):
    try:
        return getattr(contract.functions, func_name)(*args).call()
    except Exception:
        return None

print(f"Connected. Block: {w3.eth.block_number}")

# Step 1: Search for Pendle PT markets on Morpho using the Morpho API approach
# We know market IDs are keccak256(abi.encode(loanToken, collateralToken, oracle, irm, lltv))
# Let's search by checking known PT tokens

# Alternative: Query the Morpho subgraph or search events
# For now, let's check some known market IDs from the Morpho app

# Known PT market IDs from research (Morpho Blue)
KNOWN_PT_MARKETS = [
    # PT-sUSDe markets (from Morpho app)
    "0xb1f54084bdeb16eb3be6b2e50b47e88e1e7e4b4c4e497e5eb5a5e4c0e7d0c2a0",  # example
]

# Let's try a different approach - search for CreateMarket events
print("\n[1] Searching Morpho Blue CreateMarket events for Pendle PT collateral...")

# Morpho Blue CreateMarket event
MORPHO_EVENTS_ABI = json.loads('''[
  {"anonymous":false,"inputs":[{"indexed":true,"internalType":"Id","name":"id","type":"bytes32"},{"components":[{"internalType":"address","name":"loanToken","type":"address"},{"internalType":"address","name":"collateralToken","type":"address"},{"internalType":"address","name":"oracle","type":"address"},{"internalType":"address","name":"irm","type":"address"},{"internalType":"uint256","name":"lltv","type":"uint256"}],"indexed":false,"internalType":"struct MarketParams","name":"marketParams","type":"tuple"}],"name":"CreateMarket","type":"event"}
]''')

morpho = w3.eth.contract(address=Web3.to_checksum_address(MORPHO), abi=MORPHO_EVENTS_ABI + MORPHO_ABI)

# Scan CreateMarket events (Morpho deployed around block 18900000)
print("Scanning CreateMarket events...")
all_markets = []
start_block = 18900000
latest = w3.eth.block_number
chunk_size = 200000

for from_block in range(start_block, latest + 1, chunk_size):
    to_block = min(from_block + chunk_size - 1, latest)
    try:
        events = morpho.events.CreateMarket.get_logs(
            from_block=from_block,
            to_block=to_block
        )
        for evt in events:
            all_markets.append({
                "id": evt.args.id.hex(),
                "loanToken": evt.args.marketParams.loanToken,
                "collateralToken": evt.args.marketParams.collateralToken,
                "oracle": evt.args.marketParams.oracle,
                "irm": evt.args.marketParams.irm,
                "lltv": evt.args.marketParams.lltv,
            })
        if events:
            print(f"  Blocks {from_block}-{to_block}: {len(events)} markets")
    except Exception as e:
        print(f"  Blocks {from_block}-{to_block}: Error - {e}")
        # Try smaller chunks
        sub_chunk = 50000
        for sub_from in range(from_block, to_block + 1, sub_chunk):
            sub_to = min(sub_from + sub_chunk - 1, to_block)
            try:
                events = morpho.events.CreateMarket.get_logs(
                    from_block=sub_from, to_block=sub_to
                )
                for evt in events:
                    all_markets.append({
                        "id": evt.args.id.hex(),
                        "loanToken": evt.args.marketParams.loanToken,
                        "collateralToken": evt.args.marketParams.collateralToken,
                        "oracle": evt.args.marketParams.oracle,
                        "irm": evt.args.marketParams.irm,
                        "lltv": evt.args.marketParams.lltv,
                    })
                if events:
                    print(f"    Sub {sub_from}-{sub_to}: {len(events)} markets")
            except Exception as e2:
                print(f"    Sub {sub_from}-{sub_to}: Error - {e2}")

print(f"\nTotal markets found: {len(all_markets)}")

# Step 2: Check each market's collateral token for Pendle PT characteristics
print("\n[2] Checking collateral tokens for Pendle PT tokens...")
pt_markets = []

for m in all_markets:
    ct = m["collateralToken"]
    c = w3.eth.contract(address=Web3.to_checksum_address(ct), abi=ERC20_ABI)
    name = safe_call(c, "name") or ""
    symbol = safe_call(c, "symbol") or ""
    
    # Check if it's a PT token (name contains "PT" or "Principal Token")
    is_pt = False
    if "PT" in symbol and ("Pendle" in name or "PT-" in symbol or "Principal" in name):
        is_pt = True
    elif symbol.startswith("PT-"):
        is_pt = True
    elif "Principal Token" in name:
        is_pt = True
    
    if is_pt:
        # Get market data
        try:
            market_data = morpho.functions.market(bytes.fromhex(m["id"])).call()
            total_supply = market_data[0]
            total_borrow = market_data[2]
        except:
            total_supply = 0
            total_borrow = 0
        
        pt_markets.append({
            **m,
            "name": name,
            "symbol": symbol,
            "totalSupply": total_supply,
            "totalBorrow": total_borrow,
        })
        
        # Get loan token info
        lt = w3.eth.contract(address=Web3.to_checksum_address(m["loanToken"]), abi=ERC20_ABI)
        lt_sym = safe_call(lt, "symbol") or "?"
        lt_dec = safe_call(lt, "decimals") or 18
        
        print(f"\n  FOUND PT MARKET:")
        print(f"    Collateral: {name} ({symbol}) @ {ct}")
        print(f"    Loan: {lt_sym} @ {m['loanToken']}")
        print(f"    Oracle: {m['oracle']}")
        print(f"    LLTV: {m['lltv'] / 1e18:.2%}")
        print(f"    Supply: {total_supply / 10**lt_dec:,.2f} {lt_sym}")
        print(f"    Borrow: {total_borrow / 10**lt_dec:,.2f} {lt_sym}")

print(f"\n\nTotal PT markets found: {len(pt_markets)}")

# Step 3: Analyze oracles for PT markets
if pt_markets:
    print("\n[3] Analyzing PT market oracles...")
    for m in pt_markets:
        oracle_addr = m["oracle"]
        print(f"\n  Oracle: {oracle_addr} (for {m['symbol']})")
        
        oc = w3.eth.contract(address=Web3.to_checksum_address(oracle_addr), abi=ORACLE_V2_ABI)
        
        base_vault = safe_call(oc, "BASE_VAULT")
        quote_vault = safe_call(oc, "QUOTE_VAULT")
        base_feed1 = safe_call(oc, "BASE_FEED_1")
        base_feed2 = safe_call(oc, "BASE_FEED_2")
        quote_feed1 = safe_call(oc, "QUOTE_FEED_1")
        quote_feed2 = safe_call(oc, "QUOTE_FEED_2")
        price = safe_call(oc, "price")
        scale = safe_call(oc, "SCALE_FACTOR")
        
        ZERO = "0x0000000000000000000000000000000000000000"
        
        print(f"    BASE_VAULT: {base_vault} {'(SET!)' if base_vault and base_vault != ZERO else '(none)'}")
        print(f"    QUOTE_VAULT: {quote_vault} {'(SET!)' if quote_vault and quote_vault != ZERO else '(none)'}")
        print(f"    BASE_FEED_1: {base_feed1} {'(SET)' if base_feed1 and base_feed1 != ZERO else '(none)'}")
        print(f"    BASE_FEED_2: {base_feed2} {'(SET)' if base_feed2 and base_feed2 != ZERO else '(none)'}")
        print(f"    QUOTE_FEED_1: {quote_feed1} {'(SET)' if quote_feed1 and quote_feed1 != ZERO else '(none)'}")
        print(f"    QUOTE_FEED_2: {quote_feed2} {'(SET)' if quote_feed2 and quote_feed2 != ZERO else '(none)'}")
        print(f"    Current price: {price}")
        print(f"    SCALE_FACTOR: {scale}")
        
        # If oracle is NOT MorphoChainlinkOracleV2, check if it's a custom oracle
        if base_vault is None and base_feed1 is None:
            print(f"    ** NOT a MorphoChainlinkOracleV2 — likely custom PT oracle!")
            # Try to get bytecode size
            code = w3.eth.get_code(Web3.to_checksum_address(oracle_addr))
            print(f"    Bytecode size: {len(code)} bytes")

