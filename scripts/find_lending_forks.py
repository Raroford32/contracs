#!/usr/bin/env python3
"""
Find ALL lending protocol forks on Ethereum mainnet by scanning for
distinctive contract creation patterns.

Compound V2 forks: look for Comptroller + cToken deployment patterns
Aave forks: look for Pool + aToken deployment patterns
Custom: look for contracts calling latestRoundData on Chainlink feeds

The serial attacker targets these — we should find them first.
"""

import json
import os
from web3 import Web3

RPC = os.environ.get("RPC", "https://eth-mainnet.g.alchemy.com/v2/pLXdY7rYRY10SH_UTLBGH")
w3 = Web3(Web3.HTTPProvider(RPC))

print(f"Connected. Block: {w3.eth.block_number}")

# Strategy: Search for contracts that emit specific events used by lending protocols
# Compound V2: MarketListed(address cToken)
# Aave: ReserveInitialized(address indexed asset, ...)

# MarketListed topic: keccak256("MarketListed(address)")
MARKET_LISTED_TOPIC = w3.keccak(text="MarketListed(address)").hex()
print(f"MarketListed topic: {MARKET_LISTED_TOPIC}")

# Also search for: NewPriceOracle(address, address)
NEW_ORACLE_TOPIC = w3.keccak(text="NewPriceOracle(address,address)").hex()
print(f"NewPriceOracle topic: {NEW_ORACLE_TOPIC}")

# ReserveInitialized topic
RESERVE_INIT_TOPIC = w3.keccak(text="ReserveInitialized(address,address,address,address,address)").hex()
print(f"ReserveInitialized topic: {RESERVE_INIT_TOPIC}")

ERC20_ABI = json.loads('''[
  {"inputs":[],"name":"symbol","outputs":[{"internalType":"string","name":"","type":"string"}],"stateMutability":"view","type":"function"},
  {"inputs":[],"name":"decimals","outputs":[{"internalType":"uint8","name":"","type":"uint8"}],"stateMutability":"view","type":"function"},
  {"inputs":[],"name":"totalSupply","outputs":[{"internalType":"uint256","name":"","type":"uint256"}],"stateMutability":"view","type":"function"},
  {"inputs":[{"internalType":"address","name":"","type":"address"}],"name":"balanceOf","outputs":[{"internalType":"uint256","name":"","type":"uint256"}],"stateMutability":"view","type":"function"}
]''')

def safe_call(contract, func_name, *args):
    try:
        return getattr(contract.functions, func_name)(*args).call()
    except:
        return None

# Search for MarketListed events (Compound V2 forks) in last 6 months
print("\n" + "="*80)
print("FINDING COMPOUND V2 FORKS (MarketListed events, last 6 months)")
print("="*80)

latest = w3.eth.block_number
six_months_blocks = 1300000  # ~6 months
start = latest - six_months_blocks

comptrollers = set()
chunk = 500000

for from_block in range(start, latest + 1, chunk):
    to_block = min(from_block + chunk - 1, latest)
    try:
        logs = w3.eth.get_logs({
            "topics": [MARKET_LISTED_TOPIC],
            "fromBlock": from_block,
            "toBlock": to_block,
        })
        for log in logs:
            comptrollers.add(log["address"])
        if logs:
            print(f"  Blocks {from_block}-{to_block}: {len(logs)} MarketListed events from {len(set(l['address'] for l in logs))} contracts")
    except Exception as e:
        # Smaller chunks
        sub = 100000
        for sf in range(from_block, to_block + 1, sub):
            st = min(sf + sub - 1, to_block)
            try:
                logs = w3.eth.get_logs({
                    "topics": [MARKET_LISTED_TOPIC],
                    "fromBlock": sf,
                    "toBlock": st,
                })
                for log in logs:
                    comptrollers.add(log["address"])
            except:
                pass

print(f"\nUnique Comptroller-like contracts: {len(comptrollers)}")
for addr in comptrollers:
    print(f"  {addr}")

# For each comptroller, try to get its oracle
COMPTROLLER_ABI = json.loads('''[
  {"inputs":[],"name":"oracle","outputs":[{"internalType":"contract PriceOracle","name":"","type":"address"}],"stateMutability":"view","type":"function"},
  {"inputs":[],"name":"getAllMarkets","outputs":[{"internalType":"contract CToken[]","name":"","type":"address[]"}],"stateMutability":"view","type":"function"},
  {"inputs":[],"name":"admin","outputs":[{"internalType":"address","name":"","type":"address"}],"stateMutability":"view","type":"function"}
]''')

CTOKEN_ABI = json.loads('''[
  {"inputs":[],"name":"symbol","outputs":[{"internalType":"string","name":"","type":"string"}],"stateMutability":"view","type":"function"},
  {"inputs":[],"name":"underlying","outputs":[{"internalType":"address","name":"","type":"address"}],"stateMutability":"view","type":"function"},
  {"inputs":[],"name":"totalSupply","outputs":[{"internalType":"uint256","name":"","type":"uint256"}],"stateMutability":"view","type":"function"},
  {"inputs":[],"name":"totalBorrows","outputs":[{"internalType":"uint256","name":"","type":"uint256"}],"stateMutability":"view","type":"function"},
  {"inputs":[],"name":"getCash","outputs":[{"internalType":"uint256","name":"","type":"uint256"}],"stateMutability":"view","type":"function"},
  {"inputs":[],"name":"exchangeRateStored","outputs":[{"internalType":"uint256","name":"","type":"uint256"}],"stateMutability":"view","type":"function"}
]''')

PRICE_ORACLE_ABI = json.loads('''[
  {"inputs":[{"internalType":"contract CToken","name":"cToken","type":"address"}],"name":"getUnderlyingPrice","outputs":[{"internalType":"uint256","name":"","type":"uint256"}],"stateMutability":"view","type":"function"}
]''')

print("\n" + "="*80)
print("ANALYZING COMPOUND FORKS — ORACLE CONFIGURATIONS")
print("="*80)

KNOWN_MAINNET_COMPOUND = {
    "0x3d9819210A31b4961b30EF54bE2aeD79B9c9Cd3B",  # Compound V2 original
}

for addr in comptrollers:
    comp = w3.eth.contract(address=Web3.to_checksum_address(addr), abi=COMPTROLLER_ABI)

    oracle_addr = safe_call(comp, "oracle")
    admin = safe_call(comp, "admin")
    markets = safe_call(comp, "getAllMarkets")

    is_known = addr in KNOWN_MAINNET_COMPOUND
    label = " (KNOWN: Compound V2)" if is_known else ""

    if markets:
        print(f"\n{'='*60}")
        print(f"Comptroller: {addr}{label}")
        print(f"  Admin: {admin}")
        print(f"  Oracle: {oracle_addr}")
        print(f"  Markets: {len(markets)}")

        if oracle_addr and not is_known:
            oracle = w3.eth.contract(address=Web3.to_checksum_address(oracle_addr), abi=PRICE_ORACLE_ABI)

            for i, market in enumerate(markets[:20]):  # cap at 20
                ct = w3.eth.contract(address=Web3.to_checksum_address(market), abi=CTOKEN_ABI)
                sym = safe_call(ct, "symbol") or "?"
                underlying = safe_call(ct, "underlying")
                cash = safe_call(ct, "getCash") or 0
                borrows = safe_call(ct, "totalBorrows") or 0

                # Get underlying info
                u_sym = "ETH"
                u_dec = 18
                if underlying:
                    uc = w3.eth.contract(address=Web3.to_checksum_address(underlying), abi=ERC20_ABI)
                    u_sym = safe_call(uc, "symbol") or "?"
                    u_dec = safe_call(uc, "decimals") or 18

                # Get oracle price
                price = safe_call(oracle, "getUnderlyingPrice", Web3.to_checksum_address(market))

                # Compound V2 oracle convention: price is scaled to 36 - underlying_decimals
                # For USDC (6 dec): price should be ~1e30
                # For WETH (18 dec): price should be ~1e18 * eth_price_usd
                # For DAI (18 dec): price should be ~1e18
                if price:
                    expected_scale = 36 - u_dec
                    normalized = price / (10 ** expected_scale)

                    # Check if price makes sense
                    suspicious = False
                    reason = ""

                    # Stablecoins should be ~$1
                    if u_sym in ("USDC", "USDT", "DAI", "FRAX", "LUSD", "crvUSD", "GHO", "USDe", "USDS", "PYUSD"):
                        if normalized > 10 or normalized < 0.1:
                            suspicious = True
                            reason = f"stablecoin priced at ${normalized:.4f}"
                    # ETH derivatives should be ~$1500-3500
                    elif u_sym in ("WETH", "stETH", "wstETH", "weETH", "cbETH", "rETH", "rsETH"):
                        if normalized > 100000 or normalized < 100:
                            suspicious = True
                            reason = f"ETH-like priced at ${normalized:.4f}"
                    # BTC derivatives should be ~$50000-200000
                    elif u_sym in ("WBTC", "cbBTC", "tBTC", "LBTC"):
                        if normalized > 1000000 or normalized < 10000:
                            suspicious = True
                            reason = f"BTC-like priced at ${normalized:.4f}"

                    cash_usd = cash / (10 ** u_dec) * normalized
                    borrow_usd = borrows / (10 ** u_dec) * normalized

                    status = "*** SUSPICIOUS ***" if suspicious else ""
                    if suspicious:
                        print(f"\n  !!! {sym} ({u_sym}): PRICE ANOMALY !!!")
                        print(f"      Oracle price raw: {price}")
                        print(f"      Normalized (USD): ${normalized:,.4f}")
                        print(f"      Reason: {reason}")
                        print(f"      Cash: ${cash_usd:,.0f}, Borrows: ${borrow_usd:,.0f}")
                    elif cash_usd > 10000 or borrow_usd > 10000:
                        print(f"  {sym} ({u_sym}): ${normalized:,.2f} | Cash: ${cash_usd:,.0f} | Borrows: ${borrow_usd:,.0f}")

# Search for NewPriceOracle events (oracle updates — fresh misconfig opportunity)
print("\n\n" + "="*80)
print("FINDING RECENT ORACLE UPDATES (NewPriceOracle events, last 30 days)")
print("="*80)

thirty_days_blocks = 216000
start_recent = latest - thirty_days_blocks

for from_block in range(start_recent, latest + 1, chunk):
    to_block = min(from_block + chunk - 1, latest)
    try:
        logs = w3.eth.get_logs({
            "topics": [NEW_ORACLE_TOPIC],
            "fromBlock": from_block,
            "toBlock": to_block,
        })
        if logs:
            print(f"  Blocks {from_block}-{to_block}: {len(logs)} NewPriceOracle events")
            for log in logs:
                print(f"    From: {log['address']}")
                print(f"    Block: {log['blockNumber']}")
                # Decode old and new oracle addresses from data
                data = log['data'].hex()
                if len(data) >= 128:
                    old_oracle = "0x" + data[26:66]
                    new_oracle = "0x" + data[90:130]
                    print(f"    Old oracle: {old_oracle}")
                    print(f"    New oracle: {new_oracle}")
    except:
        pass

# Also search for recently deployed lending protocols via Aave-like patterns
print("\n\n" + "="*80)
print("FINDING AAVE FORKS (ReserveInitialized events, last 6 months)")
print("="*80)

aave_pools = set()
for from_block in range(start, latest + 1, chunk):
    to_block = min(from_block + chunk - 1, latest)
    try:
        logs = w3.eth.get_logs({
            "topics": [RESERVE_INIT_TOPIC],
            "fromBlock": from_block,
            "toBlock": to_block,
        })
        for log in logs:
            aave_pools.add(log["address"])
        if logs:
            print(f"  Blocks {from_block}-{to_block}: {len(logs)} ReserveInitialized from {len(set(l['address'] for l in logs))} contracts")
    except Exception as e:
        sub = 100000
        for sf in range(from_block, to_block + 1, sub):
            st = min(sf + sub - 1, to_block)
            try:
                logs = w3.eth.get_logs({
                    "topics": [RESERVE_INIT_TOPIC],
                    "fromBlock": sf,
                    "toBlock": st,
                })
                for log in logs:
                    aave_pools.add(log["address"])
            except:
                pass

print(f"\nUnique Aave-like Pool contracts: {len(aave_pools)}")
for addr in aave_pools:
    code_size = len(w3.eth.get_code(Web3.to_checksum_address(addr)))
    print(f"  {addr} ({code_size} bytes)")

# Known Aave pools
KNOWN_AAVE = {
    "0x87870Bca3F3fD6335C3F4ce8392D69350B4fA4E2": "Aave V3 Main",
    "0x4e033931ad43597d96D6bcc25c280717730B58B1": "Aave V3 Lido",
    "0xC13e21B648A5Ee794902342038FF3aDAB66BE987": "Spark Protocol",
    "0x7d2768dE32b0b80b7a3454c06BdAc94A69DDc7A9": "Aave V2",
}

for addr in aave_pools:
    known = KNOWN_AAVE.get(addr, None)
    if not known:
        print(f"\n  *** UNKNOWN AAVE FORK: {addr} ***")
        # This needs investigation!

print("\n\nDone.")
