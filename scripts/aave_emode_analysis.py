#!/usr/bin/env python3
"""
Aave V3 E-Mode Analysis: Check if e-mode oracle configurations create
arbitrage opportunities when combined with Morpho Blue.

E-mode allows higher LTV for correlated assets. If the e-mode oracle
prices assets differently than Morpho, there could be a cross-protocol
arbitrage (borrow on cheaper protocol, deposit on more expensive one).

Also check: are there any e-mode categories where the oracle could be
manipulated? E-mode uses a special "oracle" that can be set by governance.
"""

import json
import os
from web3 import Web3

RPC = os.environ.get("RPC", "https://eth-mainnet.g.alchemy.com/v2/pLXdY7rYRY10SH_UTLBGH")
w3 = Web3(Web3.HTTPProvider(RPC))

print(f"Connected. Block: {w3.eth.block_number}")

# Aave V3 Pool
AAVE_POOL = "0x87870Bca3F3fD6335C3F4ce8392D69350B4fA4E2"
AAVE_ORACLE = "0x54586bE62E3c3580375aE3723C145253060Ca0C2"

# Pool data provider for reserve info
AAVE_PDP = "0x7B4EB56E7CD4b454BA8ff71E4518426c7568d76D"

# ABI for getting e-mode categories
POOL_ABI = json.loads('''[
  {"inputs":[{"internalType":"uint8","name":"id","type":"uint8"}],"name":"getEModeCategoryData","outputs":[{"components":[{"internalType":"uint16","name":"ltv","type":"uint16"},{"internalType":"uint16","name":"liquidationThreshold","type":"uint16"},{"internalType":"uint16","name":"liquidationBonus","type":"uint16"},{"internalType":"address","name":"priceSource","type":"address"},{"internalType":"string","name":"label","type":"string"}],"internalType":"struct DataTypes.EModeCategory","name":"","type":"tuple"}],"stateMutability":"view","type":"function"},
  {"inputs":[{"internalType":"uint8","name":"id","type":"uint8"}],"name":"getEModeCategoryCollateralBitmap","outputs":[{"internalType":"uint128","name":"","type":"uint128"}],"stateMutability":"view","type":"function"},
  {"inputs":[{"internalType":"uint8","name":"id","type":"uint8"}],"name":"getEModeCategoryBorrowableBitmap","outputs":[{"internalType":"uint128","name":"","type":"uint128"}],"stateMutability":"view","type":"function"}
]''')

ORACLE_ABI = json.loads('''[
  {"inputs":[{"internalType":"address","name":"asset","type":"address"}],"name":"getAssetPrice","outputs":[{"internalType":"uint256","name":"","type":"uint256"}],"stateMutability":"view","type":"function"},
  {"inputs":[{"internalType":"address","name":"asset","type":"address"}],"name":"getSourceOfAsset","outputs":[{"internalType":"address","name":"","type":"address"}],"stateMutability":"view","type":"function"}
]''')

def safe_call(contract, func_name, *args):
    try:
        return getattr(contract.functions, func_name)(*args).call()
    except:
        return None

pool = w3.eth.contract(address=Web3.to_checksum_address(AAVE_POOL), abi=POOL_ABI)
oracle = w3.eth.contract(address=Web3.to_checksum_address(AAVE_ORACLE), abi=ORACLE_ABI)

print("\n" + "="*80)
print("AAVE V3 E-MODE CATEGORY ANALYSIS")
print("="*80)

# Scan all e-mode categories (0-255, but most are empty)
for emode_id in range(0, 20):  # Most deployments have <20 categories
    data = safe_call(pool, "getEModeCategoryData", emode_id)
    if data and data[0] > 0:  # ltv > 0 means active category
        ltv = data[0]
        liq_threshold = data[1]
        liq_bonus = data[2]
        price_source = data[3]
        label = data[4]

        print(f"\nE-Mode #{emode_id}: {label}")
        print(f"  LTV: {ltv/100:.1f}%")
        print(f"  Liquidation Threshold: {liq_threshold/100:.1f}%")
        print(f"  Liquidation Bonus: {liq_bonus/100:.1f}%")
        print(f"  Price Source: {price_source}")

        # Check if price source is non-zero (custom oracle for e-mode)
        if price_source != "0x0000000000000000000000000000000000000000":
            print(f"  *** CUSTOM E-MODE ORACLE ***")
            # Check what kind of oracle this is
            code_size = len(w3.eth.get_code(Web3.to_checksum_address(price_source)))
            print(f"  Oracle code size: {code_size}")

        # Get collateral bitmap
        coll_bitmap = safe_call(pool, "getEModeCategoryCollateralBitmap", emode_id)
        borrow_bitmap = safe_call(pool, "getEModeCategoryBorrowableBitmap", emode_id)

        if coll_bitmap:
            print(f"  Collateral bitmap: {bin(coll_bitmap)}")
        if borrow_bitmap:
            print(f"  Borrowable bitmap: {bin(borrow_bitmap)}")

# Also check: Aave V3.1 introduced liquid e-modes (Aave 3.2+)
# Where users can enter e-mode without changing their full portfolio
print("\n\n" + "="*80)
print("KEY FINDINGS")
print("="*80)
print("""
E-mode analysis for cross-protocol arbitrage:
1. If e-mode has a CUSTOM price source (not 0x0), it uses a special oracle
   that might price assets at 1:1 (e.g., ETH/stETH at par)
2. Meanwhile, Morpho prices the same assets using market rates
3. If Aave e-mode says stETH = ETH (1:1), but Morpho says stETH = 0.999 ETH:
   → Deposit stETH on Aave at 1:1 value
   → Borrow ETH at e-mode's higher LTV
   → Use ETH to buy more stETH on market at 0.999
   → Deposit again... loop for profit
   → But profit per loop = (1-0.999) * LTV - gas
   → With LTV=93%, profit = 0.001 * 0.93 = 0.093% per loop
   → This is standard LST looping, not an exploit

The real question: can the e-mode oracle be manipulated to create a
larger deviation? Or can a market event (depeg) be exploited before
the e-mode oracle updates?
""")

# Check oracle sources for key LST tokens
KEY_TOKENS = {
    "wstETH": "0x7f39C581F595B53c5cb19bD0b3f8dA6c935E2Ca0",
    "weETH": "0xCd5fE23C85820F7B72D0926FC9b05b43E359b7ee",
    "rsETH": "0xA1290d69c65A6Fe4DF752f95823fae25cB99e5A7",
    "osETH": "0xf1C9acDc66974dFB6dEcB12aA385b9cD01190E38",
    "rETH": "0xae78736Cd615f374D3085123A210448E74Fc6393",
    "cbETH": "0xBe9895146f7AF43049ca1c1AE358B0541Ea49704",
    "sUSDe": "0x9D39A5DE30e57443BfF2A8307A4256c8797A3497",
    "USDS": "0xdC035D45d973E3EC169d2276DDab16f1e407384F",
    "sUSDS": "0xa3931d71877C0E7a3148CB7Eb4463524FEc27fbD",
}

print("\n\nORACLE SOURCES FOR KEY TOKENS:")
for name, addr in KEY_TOKENS.items():
    source = safe_call(oracle, "getSourceOfAsset", Web3.to_checksum_address(addr))
    price = safe_call(oracle, "getAssetPrice", Web3.to_checksum_address(addr))
    if source:
        code_size = len(w3.eth.get_code(Web3.to_checksum_address(source)))
        print(f"  {name}: price=${price/1e8:,.2f}, source={source} ({code_size} bytes)")
    else:
        print(f"  {name}: not listed")
