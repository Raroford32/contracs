#!/usr/bin/env python3
"""
Check if the same asset is priced differently across lending protocols.
Compare Morpho oracle prices vs Aave oracle prices for the same collateral/loan pairs.
Price disagreement could enable cross-protocol arbitrage.
"""
import json
import os
from web3 import Web3

RPC = os.environ.get("RPC", "https://eth-mainnet.g.alchemy.com/v2/pLXdY7rYRY10SH_UTLBGH")
w3 = Web3(Web3.HTTPProvider(RPC))

# Aave V3 Pool Data Provider
AAVE_POOL_DP = "0x7B4EB56E7CD4b454BA8ff71E4518426c7568d76D"

AAVE_DP_ABI = json.loads('''[
  {"inputs":[{"internalType":"address","name":"asset","type":"address"}],"name":"getReserveData","outputs":[{"internalType":"uint256","name":"unbacked","type":"uint256"},{"internalType":"uint256","name":"accruedToTreasuryScaled","type":"uint256"},{"internalType":"uint256","name":"totalAToken","type":"uint256"},{"internalType":"uint256","name":"totalStableDebt","type":"uint256"},{"internalType":"uint256","name":"totalVariableDebt","type":"uint256"},{"internalType":"uint256","name":"liquidityRate","type":"uint256"},{"internalType":"uint256","name":"variableBorrowRate","type":"uint256"},{"internalType":"uint256","name":"stableBorrowRate","type":"uint256"},{"internalType":"uint256","name":"averageStableBorrowRate","type":"uint256"},{"internalType":"uint256","name":"liquidityIndex","type":"uint256"},{"internalType":"uint256","name":"variableBorrowIndex","type":"uint256"},{"internalType":"uint256","name":"lastUpdateTimestamp","type":"uint256"}],"stateMutability":"view","type":"function"}
]''')

# Aave Oracle
AAVE_ORACLE = "0x54586bE62E3c3580375aE3723C145253060Ca0C2"
AAVE_ORACLE_ABI = json.loads('''[
  {"inputs":[{"internalType":"address","name":"asset","type":"address"}],"name":"getAssetPrice","outputs":[{"internalType":"uint256","name":"","type":"uint256"}],"stateMutability":"view","type":"function"},
  {"inputs":[],"name":"BASE_CURRENCY_UNIT","outputs":[{"internalType":"uint256","name":"","type":"uint256"}],"stateMutability":"view","type":"function"}
]''')

ERC20_ABI = json.loads('''[
  {"inputs":[],"name":"symbol","outputs":[{"internalType":"string","name":"","type":"string"}],"stateMutability":"view","type":"function"},
  {"inputs":[],"name":"decimals","outputs":[{"internalType":"uint8","name":"","type":"uint8"}],"stateMutability":"view","type":"function"}
]''')

def safe_call(contract, func_name, *args):
    try:
        return getattr(contract.functions, func_name)(*args).call()
    except:
        return None

print(f"Connected. Block: {w3.eth.block_number}")

# Key tokens listed on both Aave and Morpho
TOKENS = {
    "WETH": "0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2",
    "wstETH": "0x7f39C581F595B53c5cb19bD0b3f8dA6c935E2Ca0",
    "USDC": "0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48",
    "USDT": "0xdAC17F958D2ee523a2206206994597C13D831ec7",
    "DAI": "0x6B175474E89094C44Da98b954EedeAC495271d0F",
    "weETH": "0xCd5fE23C85820F7B72D0926FC9b05b43E359b7ee",
    "rsETH": "0xA1290d69c65A6Fe4DF752f95823fae25cB99e5A7",
    "sUSDe": "0x9D39A5DE30e57443BfF2A8307A4256c8797A3497",
    "WBTC": "0x2260FAC5E5542a773Aa44fBCfeDf7C193bc2C599",
    "cbBTC": "0xcbB7C0000aB88B473b1f5aFd9ef808440eed33Bf",
    "GHO": "0x40D16FC0246aD3160Ccc09B8D0D3A2cD28aE6C2f",
    "sUSDS": "0xa3931d71877C0E7a3148CB7Eb4463524FEc27fbD",
    "USDe": "0x4c9EDD5852cd905f086C759E8383e09bff1E68B3",
}

# Get Aave prices
aave_oracle = w3.eth.contract(address=Web3.to_checksum_address(AAVE_ORACLE), abi=AAVE_ORACLE_ABI)
base_unit = safe_call(aave_oracle, "BASE_CURRENCY_UNIT")
print(f"Aave base currency unit: {base_unit}")

print("\n{'='*70}")
print("AAVE V3 ORACLE PRICES (USD, 8 decimals)")
print("{'='*70}")

aave_prices = {}
for name, addr in TOKENS.items():
    price = safe_call(aave_oracle, "getAssetPrice", Web3.to_checksum_address(addr))
    if price:
        aave_prices[name] = price
        print(f"  {name}: ${price / 1e8:,.4f}")
    else:
        print(f"  {name}: not listed on Aave")

# Now check known Morpho markets that overlap with Aave
# For overlapping pairs, compare oracle-implied exchange rates
print("\n{'='*70}")
print("CROSS-PROTOCOL ORACLE COMPARISON")
print("{'='*70}")

# Morpho oracle for sUSDe/USDC — compare effective rate
MORPHO_ORACLE_ABI = json.loads('''[
  {"inputs":[],"name":"price","outputs":[{"internalType":"uint256","name":"","type":"uint256"}],"stateMutability":"view","type":"function"}
]''')

# Known Morpho market oracles for key pairs
morpho_oracles = {
    # sUSDe collateral markets
    "sUSDe/USDC (sUSDe/DAI oracle)": "0x5D916980D5Ae1737a8330Bf24dF812b2911Aae25",
    "wstETH/USDC": "0x48F7E36EB6B826B2dF4B2E630B62Cd25e89E40e2",
    "weETH/USDC": None,  # Need to find
    "sUSDS/USDC": None,
}

for pair, oracle_addr in morpho_oracles.items():
    if oracle_addr:
        oc = w3.eth.contract(address=Web3.to_checksum_address(oracle_addr), abi=MORPHO_ORACLE_ABI)
        morpho_price = safe_call(oc, "price")
        if morpho_price:
            # Morpho price is in 36 + loan_dec - coll_dec decimal units
            # For X/USDC: 36 + 6 - 18 = 24 decimal places
            # Price represents: how many loan tokens per 1 collateral token
            print(f"\n  {pair}")
            print(f"    Morpho oracle raw: {morpho_price}")
            
            # Extract collateral and loan names
            coll_name = pair.split("/")[0].strip()
            loan_name = pair.split("/")[1].split(" ")[0].strip()
            
            if coll_name in aave_prices and loan_name in aave_prices:
                # Aave implied exchange rate
                aave_rate = aave_prices[coll_name] / aave_prices[loan_name]
                
                # Morpho rate depends on decimals
                coll_addr = TOKENS.get(coll_name)
                loan_addr = TOKENS.get(loan_name)
                if coll_addr and loan_addr:
                    ct = w3.eth.contract(address=Web3.to_checksum_address(coll_addr), abi=ERC20_ABI)
                    lt = w3.eth.contract(address=Web3.to_checksum_address(loan_addr), abi=ERC20_ABI)
                    ct_dec = safe_call(ct, "decimals") or 18
                    lt_dec = safe_call(lt, "decimals") or 18
                    
                    # Morpho price normalization: price * 10^coll_dec / 10^(36 + lt_dec)
                    morpho_rate = morpho_price / (10 ** (36 + lt_dec - ct_dec))
                    
                    divergence = abs(morpho_rate - aave_rate) / aave_rate * 100
                    
                    print(f"    Aave rate ({coll_name}/{loan_name}): {aave_rate:.6f}")
                    print(f"    Morpho rate ({coll_name}/{loan_name}): {morpho_rate:.6f}")
                    print(f"    Divergence: {divergence:.4f}%")
                    
                    if divergence > 1:
                        print(f"    *** SIGNIFICANT DIVERGENCE: {divergence:.2f}% ***")
                        print(f"    If can deposit on cheaper protocol and borrow on more expensive:")
                        print(f"    Potential profit per $1M: ${divergence/100 * 1e6:,.0f}")

print("\n\nDone.")
