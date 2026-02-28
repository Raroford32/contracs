#!/usr/bin/env python3
"""
Scan Morpho Blue markets for oracle misconfigurations.
Key pattern: SCALE_FACTOR errors that over/undervalue collateral.
Inspired by the PAXG/USDC exploit ($230K, Oct 2024).
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

ORACLE_V2_ABI = json.loads('''[
  {"inputs":[],"name":"BASE_VAULT","outputs":[{"internalType":"contract IERC4626","name":"","type":"address"}],"stateMutability":"view","type":"function"},
  {"inputs":[],"name":"QUOTE_VAULT","outputs":[{"internalType":"contract IERC4626","name":"","type":"address"}],"stateMutability":"view","type":"function"},
  {"inputs":[],"name":"BASE_FEED_1","outputs":[{"internalType":"contract AggregatorV3Interface","name":"","type":"address"}],"stateMutability":"view","type":"function"},
  {"inputs":[],"name":"BASE_FEED_2","outputs":[{"internalType":"contract AggregatorV3Interface","name":"","type":"address"}],"stateMutability":"view","type":"function"},
  {"inputs":[],"name":"QUOTE_FEED_1","outputs":[{"internalType":"contract AggregatorV3Interface","name":"","type":"address"}],"stateMutability":"view","type":"function"},
  {"inputs":[],"name":"QUOTE_FEED_2","outputs":[{"internalType":"contract AggregatorV3Interface","name":"","type":"address"}],"stateMutability":"view","type":"function"},
  {"inputs":[],"name":"SCALE_FACTOR","outputs":[{"internalType":"uint256","name":"","type":"uint256"}],"stateMutability":"view","type":"function"},
  {"inputs":[],"name":"price","outputs":[{"internalType":"uint256","name":"","type":"uint256"}],"stateMutability":"view","type":"function"}
]''')

ERC20_ABI = json.loads('''[
  {"inputs":[],"name":"name","outputs":[{"internalType":"string","name":"","type":"string"}],"stateMutability":"view","type":"function"},
  {"inputs":[],"name":"symbol","outputs":[{"internalType":"string","name":"","type":"string"}],"stateMutability":"view","type":"function"},
  {"inputs":[],"name":"decimals","outputs":[{"internalType":"uint8","name":"","type":"uint8"}],"stateMutability":"view","type":"function"}
]''')

CHAINLINK_ABI = json.loads('''[
  {"inputs":[],"name":"latestRoundData","outputs":[{"internalType":"uint80","name":"roundId","type":"uint80"},{"internalType":"int256","name":"answer","type":"int256"},{"internalType":"uint256","name":"startedAt","type":"uint256"},{"internalType":"uint256","name":"updatedAt","type":"uint256"},{"internalType":"uint80","name":"answeredInRound","type":"uint80"}],"stateMutability":"view","type":"function"},
  {"inputs":[],"name":"decimals","outputs":[{"internalType":"uint8","name":"","type":"uint8"}],"stateMutability":"view","type":"function"},
  {"inputs":[],"name":"description","outputs":[{"internalType":"string","name":"","type":"string"}],"stateMutability":"view","type":"function"}
]''')

def safe_call(contract, func_name, *args):
    try:
        return getattr(contract.functions, func_name)(*args).call()
    except Exception:
        return None

print(f"Connected. Block: {w3.eth.block_number}")

# Scan ALL markets
morpho = w3.eth.contract(address=Web3.to_checksum_address(MORPHO), abi=MORPHO_EVENTS_ABI + MORPHO_ABI)

print("[1] Scanning CreateMarket events...")
all_markets = []
start_block = 18900000
latest = w3.eth.block_number
chunk_size = 200000

for from_block in range(start_block, latest + 1, chunk_size):
    to_block = min(from_block + chunk_size - 1, latest)
    try:
        events = morpho.events.CreateMarket.get_logs(from_block=from_block, to_block=to_block)
        for evt in events:
            all_markets.append({
                "id": evt.args.id.hex(),
                "loanToken": evt.args.marketParams.loanToken,
                "collateralToken": evt.args.marketParams.collateralToken,
                "oracle": evt.args.marketParams.oracle,
                "lltv": evt.args.marketParams.lltv,
                "block": evt.blockNumber,
            })
    except Exception as e:
        sub_chunk = 50000
        for sub_from in range(from_block, to_block + 1, sub_chunk):
            sub_to = min(sub_from + sub_chunk - 1, to_block)
            try:
                events = morpho.events.CreateMarket.get_logs(from_block=sub_from, to_block=sub_to)
                for evt in events:
                    all_markets.append({
                        "id": evt.args.id.hex(),
                        "loanToken": evt.args.marketParams.loanToken,
                        "collateralToken": evt.args.marketParams.collateralToken,
                        "oracle": evt.args.marketParams.oracle,
                        "lltv": evt.args.marketParams.lltv,
                        "block": evt.blockNumber,
                    })
            except:
                pass

print(f"Total markets: {len(all_markets)}")

# Filter to markets with supply (active markets worth checking)
print("\n[2] Checking market activity and oracle sanity...")
ZERO = "0x0000000000000000000000000000000000000000"

suspicious = []
checked = 0

for m in all_markets:
    # Get market data
    try:
        market_data = morpho.functions.market(bytes.fromhex(m["id"])).call()
        total_supply = market_data[0]
        total_borrow = market_data[2]
    except:
        continue
    
    # Only check markets with some supply
    if total_supply == 0 and total_borrow == 0:
        continue
    
    checked += 1
    
    # Get token info
    try:
        lt = w3.eth.contract(address=Web3.to_checksum_address(m["loanToken"]), abi=ERC20_ABI)
        ct = w3.eth.contract(address=Web3.to_checksum_address(m["collateralToken"]), abi=ERC20_ABI)
        lt_sym = safe_call(lt, "symbol") or "?"
        lt_dec = safe_call(lt, "decimals") or 18
        ct_sym = safe_call(ct, "symbol") or "?"
        ct_dec = safe_call(ct, "decimals") or 18
    except:
        lt_sym, lt_dec, ct_sym, ct_dec = "?", 18, "?", 18
    
    # Check oracle
    oracle_addr = m["oracle"]
    oc = w3.eth.contract(address=Web3.to_checksum_address(oracle_addr), abi=ORACLE_V2_ABI)
    
    oracle_price = safe_call(oc, "price")
    scale_factor = safe_call(oc, "SCALE_FACTOR")
    
    if oracle_price is None:
        # Not a MorphoChainlinkOracleV2 — custom oracle
        # Try to call price() anyway
        try:
            generic_abi = json.loads('[{"inputs":[],"name":"price","outputs":[{"internalType":"uint256","name":"","type":"uint256"}],"stateMutability":"view","type":"function"}]')
            gc = w3.eth.contract(address=Web3.to_checksum_address(oracle_addr), abi=generic_abi)
            oracle_price = gc.functions.price().call()
        except:
            oracle_price = None
    
    # Expected price normalization for Morpho Blue:
    # price is in 36 + loan_decimals - collateral_decimals decimal places
    # For ETH/ETH pairs: 36 + 18 - 18 = 36 decimals → ~1e36
    # For USDC/ETH pairs: 36 + 6 - 18 = 24 decimals → ~price_in_usd * 1e24
    # For USDT/USDC pairs: 36 + 6 - 6 = 36 decimals → ~1e36
    
    if oracle_price is not None and oracle_price > 0:
        expected_decimals = 36 + lt_dec - ct_dec
        
        # Check if the price is reasonable
        # For same-denomination pairs (ETH/ETH, USDC/USDC), price should be ~1e(expected_decimals)
        # For cross-denomination (ETH/USD), price should be ~2500 * 1e(expected_decimals - 18)
        
        price_magnitude = len(str(oracle_price))
        
        # Flag suspicious: price off by more than 6 orders of magnitude from expected
        # Expected: within a few orders of magnitude of 10^expected_decimals
        ratio_to_expected = oracle_price / (10 ** expected_decimals) if expected_decimals < 80 else 0
        
        is_suspicious = False
        reason = ""
        
        if ratio_to_expected > 1000:
            is_suspicious = True
            reason = f"Price {ratio_to_expected:.2e}x higher than expected 1e{expected_decimals}"
        elif ratio_to_expected < 0.001 and ratio_to_expected > 0:
            is_suspicious = True
            reason = f"Price {ratio_to_expected:.2e}x lower than expected 1e{expected_decimals}"
        elif ratio_to_expected == 0 and oracle_price > 0:
            is_suspicious = True
            reason = f"Price magnitude {price_magnitude} digits vs expected ~{expected_decimals} digits"
        
        # Also check for extreme LLTV values
        if m["lltv"] > 0.98e18:
            is_suspicious = True
            reason += f" | EXTREME LLTV: {m['lltv']/1e18:.4f}"
        
        supply_formatted = total_supply / (10 ** lt_dec) if lt_dec else total_supply
        borrow_formatted = total_borrow / (10 ** lt_dec) if lt_dec else total_borrow
        
        if is_suspicious:
            suspicious.append({
                "id": m["id"],
                "pair": f"{ct_sym}/{lt_sym}",
                "collateral": m["collateralToken"],
                "loan": m["loanToken"],
                "oracle": oracle_addr,
                "price": oracle_price,
                "scale_factor": scale_factor,
                "lt_dec": lt_dec,
                "ct_dec": ct_dec,
                "expected_dec": expected_decimals,
                "ratio": ratio_to_expected,
                "supply": supply_formatted,
                "borrow": borrow_formatted,
                "lltv": m["lltv"] / 1e18,
                "reason": reason,
                "block": m["block"],
            })

print(f"\nChecked {checked} active markets")
print(f"Found {len(suspicious)} suspicious markets")

# Print suspicious markets
print("\n" + "=" * 80)
print("SUSPICIOUS MARKETS (potential oracle misconfiguration)")
print("=" * 80)

for s in sorted(suspicious, key=lambda x: x["supply"], reverse=True):
    print(f"\n  Market: {s['pair']} (ID: 0x{s['id'][:16]}...)")
    print(f"  Created at block: {s['block']}")
    print(f"  Oracle: {s['oracle']}")
    print(f"  Oracle price: {s['price']} (magnitude: {len(str(s['price']))} digits)")
    print(f"  Expected: ~1e{s['expected_dec']} (loan_dec={s['lt_dec']}, coll_dec={s['ct_dec']})")
    print(f"  Ratio to expected: {s['ratio']:.6e}")
    print(f"  Scale factor: {s['scale_factor']}")
    print(f"  LLTV: {s['lltv']:.4f}")
    print(f"  Supply: {s['supply']:,.2f} {s['pair'].split('/')[1]}")
    print(f"  Borrow: {s['borrow']:,.2f}")
    print(f"  REASON: {s['reason']}")
    
    # For high-supply suspicious markets, deep dive into oracle
    if s["supply"] > 100:
        oc = w3.eth.contract(address=Web3.to_checksum_address(s["oracle"]), abi=ORACLE_V2_ABI)
        bf1 = safe_call(oc, "BASE_FEED_1")
        bf2 = safe_call(oc, "BASE_FEED_2")
        qf1 = safe_call(oc, "QUOTE_FEED_1")
        qf2 = safe_call(oc, "QUOTE_FEED_2")
        bv = safe_call(oc, "BASE_VAULT")
        qv = safe_call(oc, "QUOTE_VAULT")
        
        print(f"  BASE_VAULT: {bv}")
        print(f"  QUOTE_VAULT: {qv}")
        print(f"  BASE_FEED_1: {bf1}")
        print(f"  BASE_FEED_2: {bf2}")
        print(f"  QUOTE_FEED_1: {qf1}")
        print(f"  QUOTE_FEED_2: {qf2}")
        
        # Check feed descriptions
        for label, addr in [("BASE_FEED_1", bf1), ("BASE_FEED_2", bf2), ("QUOTE_FEED_1", qf1), ("QUOTE_FEED_2", qf2)]:
            if addr and addr != ZERO:
                fc = w3.eth.contract(address=Web3.to_checksum_address(addr), abi=CHAINLINK_ABI)
                desc = safe_call(fc, "description")
                dec = safe_call(fc, "decimals")
                rd = safe_call(fc, "latestRoundData")
                if rd:
                    print(f"    {label}: {desc} ({dec} dec) = {rd[1]}")

print("\n\nDone.")
