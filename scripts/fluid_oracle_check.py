#!/usr/bin/env python3
"""
Check Fluid Protocol oracle architecture: does lending use DEX prices?
If yes, DEX manipulation could affect lending positions.
"""

import json
import os
from web3 import Web3

RPC = os.environ.get("RPC", "https://eth-mainnet.g.alchemy.com/v2/pLXdY7rYRY10SH_UTLBGH")
w3 = Web3(Web3.HTTPProvider(RPC))

print(f"Connected. Block: {w3.eth.block_number}")

# Fluid Vault T1 uses an oracle stored in its "constants"
# The vault's oracle address is embedded in the proxy's storage
# We need to read the vault's constants to find oracle addresses

# Approach: Read the first few vaults and extract their oracle addresses
# Fluid Vault stores constants in the implementation, accessible via constantsView
# But the ABI is complex. Let's try a different approach.

# The Fluid VaultResolver can give us structured data
VAULT_RESOLVER = "0x45f4ad57e300da55C33dea579A40FCeE000d7Cc9"
VAULT_FACTORY = "0x324c5Dc1fC42c7a4D43d92df1eBA58a54d13Bf2d"

# Try calling getVaultEntireData on the resolver
# But ABI might be wrong, so let's use raw calls with known selectors

# Alternative: Fluid has VaultResolver2 which is more recent
# Let's check if there's a resolver that returns token info

# From Fluid docs, vaults store their config in "constants" which includes:
# - supplyToken
# - borrowToken
# - oracle
# - liquidation threshold
# etc.

# The constants are embedded in the vault proxy's bytecode (immutable pattern)
# We can try to find oracle addresses by scanning the bytecode

# simpler: search for Fluid-related oracle contracts
# Fluid uses FluidOracle interface with getExchangeRate()

FLUID_ORACLE_ABI = json.loads('''[
  {"inputs":[],"name":"getExchangeRate","outputs":[{"internalType":"uint256","name":"exchangeRate_","type":"uint256"}],"stateMutability":"view","type":"function"},
  {"inputs":[],"name":"getExchangeRateOperate","outputs":[{"internalType":"uint256","name":"exchangeRate_","type":"uint256"}],"stateMutability":"view","type":"function"},
  {"inputs":[],"name":"getExchangeRateLiquidate","outputs":[{"internalType":"uint256","name":"exchangeRate_","type":"uint256"}],"stateMutability":"view","type":"function"}
]''')

# Known Fluid oracle implementations
# FluidOracle uses Chainlink + Redstone as primary/fallback
# WstETH oracle, weETH oracle, etc.

# Let's check the Fluid Vault Resolver for a few key vaults
# Using raw eth_call with function selectors

# getVaultAddress selector: getVaultAddress(uint256)
# 0x98ed9e9e
FACTORY_ABI = json.loads('''[
  {"inputs":[{"internalType":"uint256","name":"vaultId_","type":"uint256"}],"name":"getVaultAddress","outputs":[{"internalType":"address","name":"vault_","type":"address"}],"stateMutability":"view","type":"function"},
  {"inputs":[],"name":"totalVaults","outputs":[{"internalType":"uint256","name":"","type":"uint256"}],"stateMutability":"view","type":"function"}
]''')

factory = w3.eth.contract(address=Web3.to_checksum_address(VAULT_FACTORY), abi=FACTORY_ABI)
total = factory.functions.totalVaults().call()

ERC20_ABI = json.loads('''[
  {"inputs":[],"name":"symbol","outputs":[{"internalType":"string","name":"","type":"string"}],"stateMutability":"view","type":"function"},
  {"inputs":[],"name":"decimals","outputs":[{"internalType":"uint8","name":"","type":"uint8"}],"stateMutability":"view","type":"function"}
]''')

def safe_call(contract, func_name, *args):
    try:
        return getattr(contract.functions, func_name)(*args).call()
    except:
        return None

def get_sym(addr):
    if addr == "0x0000000000000000000000000000000000000000" or addr == "0xEeeeeEeeeEeEeeEeEeEeeEEEeeeeEeeeeeeeEEeE":
        return "ETH"
    c = w3.eth.contract(address=Web3.to_checksum_address(addr), abi=ERC20_ABI)
    return safe_call(c, "symbol") or "?"

# The vault's internal constants are stored in an efficient packed format
# Reading them requires understanding Fluid's VaultVariables storage layout
#
# Key insight: Fluid Vault T1 stores the oracle address in its constants
# which are read via `constantsView()` — returns packed struct
#
# But easier: each vault has a `readFromStorage(bytes32)` function
# or we can just try calling the oracle interface directly on addresses
# stored in the vault bytecode

# Let's try a different approach: read the vault bytecode and extract
# embedded addresses (oracles are typically immutable constructor args
# stored in the proxy code)

print("\n" + "="*80)
print("FLUID VAULT ORACLE EXTRACTION")
print("="*80)

# Fluid recently had a major exploit in March 2025
# Let's search for information about that

# For now, let's try calling getExchangeRate on known Fluid oracle addresses
# These are from Fluid's deployed contracts list

KNOWN_FLUID_ORACLES = {
    "Fluid ETH/USD Oracle": "0x2735F4906ABb0501E37bB7B4DaA3812d72536023",
    "Fluid wstETH/ETH Oracle": "0x67F2C5c230eB2Ac77A3C2bF06e8b1A14c15b7D80",
}

for name, addr in KNOWN_FLUID_ORACLES.items():
    code = w3.eth.get_code(Web3.to_checksum_address(addr))
    if len(code) > 0:
        oc = w3.eth.contract(address=Web3.to_checksum_address(addr), abi=FLUID_ORACLE_ABI)
        rate = safe_call(oc, "getExchangeRate")
        rate_op = safe_call(oc, "getExchangeRateOperate")
        rate_liq = safe_call(oc, "getExchangeRateLiquidate")
        print(f"\n{name} ({addr}):")
        print(f"  getExchangeRate: {rate}")
        print(f"  getExchangeRateOperate: {rate_op}")
        print(f"  getExchangeRateLiquidate: {rate_liq}")
    else:
        print(f"\n{name}: NO CODE at {addr}")

# Let's try to find the oracle addresses from vault bytecode
# Fluid vault proxies use a minimal proxy pattern with immutable args appended
print("\n\n" + "="*80)
print("FLUID VAULT BYTECODE ORACLE EXTRACTION (first 10 vaults)")
print("="*80)

for vid in range(1, 11):
    vault_addr = factory.functions.getVaultAddress(vid).call()
    bytecode = w3.eth.get_code(Web3.to_checksum_address(vault_addr)).hex()

    # Look for potential address patterns in the bytecode
    # Addresses are 20 bytes = 40 hex chars
    # In immutable storage, they appear after PUSH20 opcode (0x73)

    # Find all PUSH20 addresses in bytecode
    addresses = []
    i = 0
    bc = bytecode
    while i < len(bc) - 40:
        # PUSH20 = 73
        if bc[i:i+2] == '73':
            addr_hex = bc[i+2:i+42]
            try:
                addr = Web3.to_checksum_address('0x' + addr_hex)
                if addr != "0x0000000000000000000000000000000000000000":
                    addresses.append(addr)
            except:
                pass
        i += 2

    # Get unique addresses
    unique_addrs = list(set(addresses))

    # Try to identify which is the oracle by calling getExchangeRate
    oracle_addr = None
    for addr in unique_addrs:
        code = w3.eth.get_code(Web3.to_checksum_address(addr))
        if len(code) > 100:
            oc = w3.eth.contract(address=Web3.to_checksum_address(addr), abi=FLUID_ORACLE_ABI)
            rate = safe_call(oc, "getExchangeRate")
            if rate:
                oracle_addr = addr
                break

    # Also try to identify supply/borrow tokens
    token_addrs = []
    for addr in unique_addrs:
        sym = get_sym(addr)
        if sym != "?":
            token_addrs.append((addr, sym))

    tokens_str = ", ".join([f"{s}({a[:10]}...)" for a, s in token_addrs[:4]])

    print(f"\nVault #{vid}: {vault_addr}")
    print(f"  Tokens found: {tokens_str}")
    if oracle_addr:
        oc = w3.eth.contract(address=Web3.to_checksum_address(oracle_addr), abi=FLUID_ORACLE_ABI)
        rate = safe_call(oc, "getExchangeRate")
        rate_op = safe_call(oc, "getExchangeRateOperate")
        rate_liq = safe_call(oc, "getExchangeRateLiquidate")
        print(f"  Oracle: {oracle_addr}")
        print(f"    getExchangeRate: {rate}")
        print(f"    operate rate: {rate_op}, liquidate rate: {rate_liq}")

        # Check if the oracle references the Fluid DEX
        # Read oracle bytecode for DEX addresses
        oracle_bc = w3.eth.get_code(Web3.to_checksum_address(oracle_addr)).hex()
        # Check if Fluid DEX factory address appears in oracle bytecode
        DEX_FACTORY_LOWER = "91716c4eda1fb55e84bf8b4c7085f84285c19085"
        if DEX_FACTORY_LOWER in oracle_bc.lower():
            print(f"    *** ORACLE REFERENCES FLUID DEX FACTORY ***")

        # Check if any Fluid DEX address appears
        # DEX addresses from factory (check first 10)
        DEX_FACTORY_ADDR = "0x91716C4EDA1Fb55e84Bf8b4c7085f84285c19085"
        dex_factory = w3.eth.contract(address=Web3.to_checksum_address(DEX_FACTORY_ADDR), abi=json.loads('''[
          {"inputs":[],"name":"totalDexes","outputs":[{"internalType":"uint256","name":"","type":"uint256"}],"stateMutability":"view","type":"function"},
          {"inputs":[{"internalType":"uint256","name":"dexId_","type":"uint256"}],"name":"getDexAddress","outputs":[{"internalType":"address","name":"dex_","type":"address"}],"stateMutability":"view","type":"function"}
        ]'''))
        total_dexes = safe_call(dex_factory, "totalDexes") or 0

        for did in range(1, min(total_dexes + 1, 30)):
            dex_addr = safe_call(dex_factory, "getDexAddress", did)
            if dex_addr:
                dex_lower = dex_addr[2:].lower()
                if dex_lower in oracle_bc.lower():
                    print(f"    *** ORACLE REFERENCES FLUID DEX #{did}: {dex_addr} ***")
    else:
        print(f"  Oracle: not found via getExchangeRate probe")
        print(f"  Unique addresses in bytecode: {len(unique_addrs)}")

print("\n\n" + "="*80)
print("KEY QUESTION: Does any Fluid vault oracle read from a Fluid DEX pool?")
print("="*80)
print("If YES → DEX manipulation could affect lending oracle → potential exploit")
print("If NO → Oracle is independent, standard Chainlink/Redstone → same as other protocols")
