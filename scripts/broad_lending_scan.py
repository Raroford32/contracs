#!/usr/bin/env python3
"""
Broad on-chain scan: Find ALL lending/vault contracts on Ethereum mainnet
that use Chainlink oracles and check for misconfigurations.

The serial attacker pattern: scan for lending protocols where oracle feed
returns price in wrong denomination (e.g., ETH-denominated feed used as USD price).

Approach:
1. Scan recent contract deployments that call Chainlink aggregators
2. Look for Compound V2/V3 forks, Aave forks, custom lending protocols
3. Check if oracle price makes sense for the token pair
"""

import json
import os
from web3 import Web3

RPC = os.environ.get("RPC", "https://eth-mainnet.g.alchemy.com/v2/pLXdY7rYRY10SH_UTLBGH")
w3 = Web3(Web3.HTTPProvider(RPC))

print(f"Connected. Block: {w3.eth.block_number}")

# Strategy 1: Find lending protocols by scanning for common oracle patterns
# Most lending protocols call latestRoundData() on Chainlink aggregators
# We can find these by looking at who calls popular Chainlink feeds

# Strategy 2: Scan for known fork factory patterns
# Compound V2 forks use Comptroller + cToken pattern
# Compound V3 forks use Comet pattern
# Aave forks use Pool + aToken pattern

# Let's start with a direct approach: find protocols by their oracle usage
# Known Chainlink feeds that lending protocols commonly use

# ETH/USD: 0x5f4eC3Df9cbd43714FE2740f5E3616155c5b8419
# BTC/USD: 0xF4030086522a5bEEa4988F8cA5B36dbC97BeE88c
# USDC/USD: 0x8fFfFfd4AfB6115b954Bd326cbe7B4BA576818f6
# USDT/USD: 0x3E7d1eAB13ad0104d2750B8863b489D65364e32D

# Instead of looking backward, let's scan for RECENTLY CREATED lending contracts
# by checking for contracts that implement key lending interfaces

# Approach: Search for recently deployed contracts that:
# 1. Have supply/deposit functions
# 2. Reference oracle/price feed addresses
# 3. Have borrow/withdraw functions
# 4. Hold significant token balances

# Let's look at known smaller lending protocols on Ethereum mainnet
# These are the ones that get exploited because they have fewer audits

SMALL_LENDING_PROTOCOLS = {
    # Known Compound V2 forks on Ethereum mainnet
    "Silo Finance V1": {
        "type": "custom",
        "router": "0x8658047e48CC09161f4152c79155Dac1d710Ff0a",
    },
    "Silo Finance V2": {
        "type": "custom",
        "factory": "0x2c0fA05d3AE7F90FfE9F06080294c18C12223D4a",
    },
    "Sturdy Finance": {
        "type": "aave_fork",
        "pool": "0xd784927Ff2f95ba542BfC824c8a8a98F3495f6b5",
    },
    "Radiant Capital": {
        "type": "aave_fork",
        "pool": "0x0000000000000000000000000000000000000000",  # check if deployed on mainnet
    },
    "Benqi": {
        "type": "compound_fork",
        "note": "Avalanche only",
    },
    "Venus": {
        "type": "compound_fork",
        "note": "BSC only, but has Ethereum deployment?",
    },
    "Exactly Protocol": {
        "type": "custom",
        "market_factory": "0x0000000000000000000000000000000000000000",
    },
    "Notional Finance": {
        "type": "custom",
        "proxy": "0x6e7058c91F85E0F6db4fc9da2CA886530F220C4E",
    },
    "Gearbox V3": {
        "type": "custom",
        "address_provider": "0x9ea7b04Da02a5373317D745c1571c84aaD03321D",
    },
    "Spark (MakerDAO)": {
        "type": "aave_fork",
        "pool": "0xC13e21B648A5Ee794902342038FF3aDAB66BE987",
    },
    "Zerolend": {
        "type": "aave_fork",
        "note": "zkSync/Linea primarily, check Ethereum",
    },
    "f(x) Protocol": {
        "type": "custom",
        "treasury": "0x0e5CAA5c889Bdf053c9A76395f62f1723f863627",
    },
    "Raft": {
        "type": "custom",
        "position_manager": "0x5f59b322eB44C45F4B0ae8E70eC9c99e6b10Ace4",
    },
    "Prisma Finance": {
        "type": "custom",
        "factory": "0x70b66E20766b775B2E9cE5B718bbD285Af59b7E1",
    },
    "Gravita Protocol": {
        "type": "custom",
        "borrower_ops": "0x2bCA0300c2aa65de6F19c2d241B54a445C9990E2",
    },
    "crvUSD (Curve Lending)": {
        "type": "custom",
        "controller_factory": "0xC9332fdCB1C4b38bFAc67bA03C1E11B043aB4950",
    },
    "Inverse Finance (FiRM)": {
        "type": "custom",
        "dbr": "0xAD038Eb671c44b853887A7E32528FaB35dC5D710",
    },
    "Sentiment V2": {
        "type": "custom",
        "note": "Check if deployed on Ethereum mainnet",
    },
    "Term Finance": {
        "type": "custom",
        "note": "Auction-based lending",
    },
    "Idle Finance": {
        "type": "custom",
        "note": "Yield optimizer with lending exposure",
    },
}

ERC20_ABI = json.loads('''[
  {"inputs":[{"internalType":"address","name":"","type":"address"}],"name":"balanceOf","outputs":[{"internalType":"uint256","name":"","type":"uint256"}],"stateMutability":"view","type":"function"},
  {"inputs":[],"name":"symbol","outputs":[{"internalType":"string","name":"","type":"string"}],"stateMutability":"view","type":"function"},
  {"inputs":[],"name":"decimals","outputs":[{"internalType":"uint8","name":"","type":"uint8"}],"stateMutability":"view","type":"function"},
  {"inputs":[],"name":"totalSupply","outputs":[{"internalType":"uint256","name":"","type":"uint256"}],"stateMutability":"view","type":"function"}
]''')

def safe_call(contract, func_name, *args):
    try:
        return getattr(contract.functions, func_name)(*args).call()
    except:
        return None

def check_has_code(addr):
    if addr == "0x0000000000000000000000000000000000000000":
        return False
    try:
        code = w3.eth.get_code(Web3.to_checksum_address(addr))
        return len(code) > 2
    except:
        return False

# Check which of these protocols are live on Ethereum mainnet
print("\n" + "="*80)
print("SCANNING SMALLER LENDING PROTOCOLS ON ETHEREUM MAINNET")
print("="*80)

live_protocols = {}
for name, info in SMALL_LENDING_PROTOCOLS.items():
    # Get the main address
    main_addr = None
    for key in ["pool", "router", "factory", "proxy", "address_provider", "treasury",
                 "position_manager", "borrower_ops", "controller_factory", "dbr", "market_factory"]:
        if key in info:
            main_addr = info[key]
            break

    if main_addr and main_addr != "0x0000000000000000000000000000000000000000":
        has_code = check_has_code(main_addr)
        if has_code:
            code_size = len(w3.eth.get_code(Web3.to_checksum_address(main_addr)))
            print(f"\n  [LIVE] {name}: {main_addr} ({code_size} bytes)")
            live_protocols[name] = info
        else:
            print(f"  [DEAD] {name}: no code at {main_addr}")
    else:
        note = info.get("note", "no address specified")
        print(f"  [SKIP] {name}: {note}")

print(f"\n\nLive protocols found: {len(live_protocols)}")

# Now let's do a broader approach: scan for recently created contracts
# that look like lending protocols (have oracle dependencies)
print("\n\n" + "="*80)
print("SCANNING FOR RECENTLY DEPLOYED LENDING-LIKE CONTRACTS")
print("="*80)

# Find contracts created in the last 7 days that reference Chainlink interfaces
# We look for contracts that call latestRoundData or latestAnswer
# by searching for the function selector in deployed bytecode

# latestRoundData() selector: 0xfeaf968c
# latestAnswer() selector: 0x50d25bcd
# getPrice() / price() selector: varies

# More efficient: look at recent transactions creating contracts
# that immediately read from Chainlink feeds

# Alternative broader approach: scan for contracts holding >$100K in common tokens
# that were deployed recently

STABLES = {
    "USDC": ("0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48", 6),
    "USDT": ("0xdAC17F958D2ee523a2206206994597C13D831ec7", 6),
    "DAI": ("0x6B175474E89094C44Da98b954EedeAC495271d0F", 18),
    "USDS": ("0xdC035D45d973E3EC169d2276DDab16f1e407384F", 18),
    "GHO": ("0x40D16FC0246aD3160Ccc09B8D0D3A2cD28aE6C2f", 18),
    "crvUSD": ("0xf939E0A03FB07F59A73314E73794Be0E57ac1b4E", 18),
    "FRAX": ("0x853d955aCEf822Db058eb8505911ED77F175b99e", 18),
    "USDe": ("0x4c9EDD5852cd905f086C759E8383e09bff1E68B3", 18),
    "PYUSD": ("0x6c3ea9036406852006290770BEdFcAbA0e23A0e8", 6),
}

ETH_ASSETS = {
    "WETH": ("0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2", 18),
    "wstETH": ("0x7f39C581F595B53c5cb19bD0b3f8dA6c935E2Ca0", 18),
    "weETH": ("0xCd5fE23C85820F7B72D0926FC9b05b43E359b7ee", 18),
    "cbETH": ("0xBe9895146f7AF43049ca1c1AE358B0541Ea49704", 18),
    "rETH": ("0xae78736Cd615f374D3085123A210448E74Fc6393", 18),
}

BTC_ASSETS = {
    "WBTC": ("0x2260FAC5E5542a773Aa44fBCfeDf7C193bc2C599", 8),
    "cbBTC": ("0xcbB7C0000aB88B473b1f5aFd9ef808440eed33Bf", 8),
}

# Check balances of live lending protocols
print("\nChecking TVL of live smaller lending protocols...")
for name, info in live_protocols.items():
    main_addr = None
    for key in ["pool", "router", "factory", "proxy", "address_provider", "treasury",
                 "position_manager", "borrower_ops", "controller_factory", "dbr", "market_factory"]:
        if key in info:
            main_addr = info[key]
            break

    if not main_addr:
        continue

    total_usd = 0
    balances = {}

    # Check stablecoin balances
    for token_name, (token_addr, dec) in {**STABLES, **ETH_ASSETS, **BTC_ASSETS}.items():
        c = w3.eth.contract(address=Web3.to_checksum_address(token_addr), abi=ERC20_ABI)
        bal = safe_call(c, "balanceOf", Web3.to_checksum_address(main_addr))
        if bal and bal > 0:
            amount = bal / (10 ** dec)
            usd = amount
            if token_name in ETH_ASSETS:
                usd = amount * 1900  # rough ETH price
            elif token_name in BTC_ASSETS:
                usd = amount * 90000  # rough BTC price

            if usd > 100:
                balances[token_name] = (amount, usd)
                total_usd += usd

    if total_usd > 1000:
        print(f"\n  {name} ({main_addr}):")
        print(f"    Total TVL (rough): ${total_usd:,.0f}")
        for token_name, (amount, usd) in sorted(balances.items(), key=lambda x: -x[1][1]):
            print(f"      {token_name}: {amount:,.2f} (~${usd:,.0f})")

print("\n\nDone with initial scan.")
