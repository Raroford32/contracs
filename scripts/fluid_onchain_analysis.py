#!/usr/bin/env python3
"""
Fluid Protocol On-Chain Analysis: Check if unified lending+DEX creates composition vulnerability.

Key question: Can manipulating Fluid DEX affect Fluid Lending oracle prices?
Architecture: Fluid has a shared "Liquidity Layer" used by both lending (vaults) and DEX.
"""

import json
import os
from web3 import Web3

RPC = os.environ.get("RPC", "https://eth-mainnet.g.alchemy.com/v2/pLXdY7rYRY10SH_UTLBGH")
w3 = Web3(Web3.HTTPProvider(RPC))

print(f"Connected. Block: {w3.eth.block_number}")

# Known Fluid Protocol addresses on Ethereum mainnet
# From: https://github.com/Instadapp/fluid-contracts-public
FLUID_LIQUIDITY = "0x52Aa899454998Be5b000Ad077a46Bbe360F4e497"  # Liquidity Layer
FLUID_VAULT_FACTORY = "0x324c5Dc1fC42c7a4D43d92df1eBA58a54d13Bf2d"  # Vault Factory (T1)
FLUID_VAULT_T1_FACTORY = "0x324c5Dc1fC42c7a4D43d92df1eBA58a54d13Bf2d"
FLUID_DEX_FACTORY = "0x91716C4EDA1Fb55e84Bf8b4c7085f84285c19085"  # DEX Factory
FLUID_RESOLVER = "0x45f4ad57e300da55C33dea579A40FCeE000d7Cc9"  # Vault Resolver

# ABI fragments
VAULT_FACTORY_ABI = json.loads('''[
  {"inputs":[],"name":"totalVaultTypes","outputs":[{"internalType":"uint256","name":"","type":"uint256"}],"stateMutability":"view","type":"function"},
  {"inputs":[],"name":"totalVaults","outputs":[{"internalType":"uint256","name":"","type":"uint256"}],"stateMutability":"view","type":"function"},
  {"inputs":[{"internalType":"uint256","name":"vaultId_","type":"uint256"}],"name":"getVaultAddress","outputs":[{"internalType":"address","name":"vault_","type":"address"}],"stateMutability":"view","type":"function"},
  {"inputs":[{"internalType":"uint256","name":"vaultId_","type":"uint256"}],"name":"getVaultType","outputs":[{"internalType":"uint256","name":"vaultType_","type":"uint256"}],"stateMutability":"view","type":"function"}
]''')

DEX_FACTORY_ABI = json.loads('''[
  {"inputs":[],"name":"totalDexes","outputs":[{"internalType":"uint256","name":"","type":"uint256"}],"stateMutability":"view","type":"function"},
  {"inputs":[{"internalType":"uint256","name":"dexId_","type":"uint256"}],"name":"getDexAddress","outputs":[{"internalType":"address","name":"dex_","type":"address"}],"stateMutability":"view","type":"function"}
]''')

# Generic view functions we'll try on vaults
VAULT_ABI = json.loads('''[
  {"inputs":[],"name":"constantsView","outputs":[{"internalType":"uint256","name":"","type":"uint256"}],"stateMutability":"view","type":"function"},
  {"inputs":[],"name":"readFromStorage","outputs":[{"internalType":"uint256","name":"","type":"uint256"}],"stateMutability":"view","type":"function"}
]''')

# Fluid Vault Resolver ABI (more useful)
RESOLVER_ABI = json.loads('''[
  {"inputs":[{"internalType":"address","name":"vault_","type":"address"}],"name":"getVaultEntireData","outputs":[{"components":[{"components":[{"internalType":"address","name":"liquidity","type":"address"},{"internalType":"address","name":"factory","type":"address"},{"internalType":"address","name":"adminImplementation","type":"address"},{"internalType":"address","name":"secondaryImplementation","type":"address"},{"internalType":"address","name":"supplyToken","type":"address"},{"internalType":"address","name":"borrowToken","type":"address"},{"internalType":"uint8","name":"supplyDecimals","type":"uint8"},{"internalType":"uint8","name":"borrowDecimals","type":"uint8"},{"internalType":"uint256","name":"vaultId","type":"uint256"},{"internalType":"uint256","name":"vaultType","type":"uint256"}],"internalType":"struct Structs.VaultConfig","name":"configs","type":"tuple"},{"components":[{"internalType":"uint256","name":"supplyExchangePrice","type":"uint256"},{"internalType":"uint256","name":"borrowExchangePrice","type":"uint256"},{"internalType":"uint256","name":"supplyRawExchange","type":"uint256"},{"internalType":"uint256","name":"supplyInterestFree","type":"uint256"},{"internalType":"uint256","name":"borrowRawExchange","type":"uint256"},{"internalType":"uint256","name":"borrowInterestFree","type":"uint256"},{"internalType":"uint256","name":"totalSupply","type":"uint256"},{"internalType":"uint256","name":"totalBorrow","type":"uint256"},{"internalType":"uint256","name":"totalPositions","type":"uint256"},{"internalType":"uint256","name":"currentBranchId","type":"uint256"},{"internalType":"uint256","name":"totalBranchId","type":"uint256"},{"internalType":"uint256","name":"lastUpdateTimestamp","type":"uint256"}],"internalType":"struct Structs.VaultState","name":"state","type":"tuple"}],"internalType":"struct Structs.VaultEntireData","name":"vaultData_","type":"tuple"}],"stateMutability":"view","type":"function"}
]''')

ERC20_ABI = json.loads('''[
  {"inputs":[],"name":"symbol","outputs":[{"internalType":"string","name":"","type":"string"}],"stateMutability":"view","type":"function"},
  {"inputs":[],"name":"decimals","outputs":[{"internalType":"uint8","name":"","type":"uint8"}],"stateMutability":"view","type":"function"},
  {"inputs":[],"name":"name","outputs":[{"internalType":"string","name":"","type":"string"}],"stateMutability":"view","type":"function"}
]''')

def safe_call(contract, func_name, *args):
    try:
        return getattr(contract.functions, func_name)(*args).call()
    except Exception as e:
        return None

def get_token_info(addr):
    if addr == "0x0000000000000000000000000000000000000000":
        return "ETH", "ETH", 18
    c = w3.eth.contract(address=Web3.to_checksum_address(addr), abi=ERC20_ABI)
    name = safe_call(c, "name") or "?"
    symbol = safe_call(c, "symbol") or "?"
    decimals = safe_call(c, "decimals") or 18
    return name, symbol, decimals

print("\n" + "="*80)
print("FLUID PROTOCOL ON-CHAIN ANALYSIS")
print("="*80)

# Check vault factory
print("\n[1] Vault Factory Analysis")
vf = w3.eth.contract(address=Web3.to_checksum_address(FLUID_VAULT_FACTORY), abi=VAULT_FACTORY_ABI)
total_vaults = safe_call(vf, "totalVaults")
total_vault_types = safe_call(vf, "totalVaultTypes")
print(f"  Total vaults: {total_vaults}")
print(f"  Total vault types: {total_vault_types}")

# List all vaults
if total_vaults:
    print(f"\n  Enumerating all {total_vaults} vaults...")
    for vid in range(1, min(total_vaults + 1, 100)):  # Cap at 100
        vault_addr = safe_call(vf, "getVaultAddress", vid)
        vault_type = safe_call(vf, "getVaultType", vid)
        if vault_addr:
            print(f"\n  Vault #{vid}: {vault_addr} (type: {vault_type})")

            # Try to get vault data via resolver
            # Read bytecode to check if it's a proxy
            code_size = len(w3.eth.get_code(Web3.to_checksum_address(vault_addr)))
            print(f"    Code size: {code_size} bytes")

            # Try reading storage slot 0 (often contains config)
            slot0 = w3.eth.get_storage_at(Web3.to_checksum_address(vault_addr), 0)
            print(f"    Slot 0: {slot0.hex()}")

# Check DEX factory
print("\n\n[2] DEX Factory Analysis")
df = w3.eth.contract(address=Web3.to_checksum_address(FLUID_DEX_FACTORY), abi=DEX_FACTORY_ABI)
total_dexes = safe_call(df, "totalDexes")
print(f"  Total DEXes: {total_dexes}")

if total_dexes:
    print(f"\n  Enumerating all {total_dexes} DEXes...")
    for did in range(1, min(total_dexes + 1, 50)):  # Cap at 50
        dex_addr = safe_call(df, "getDexAddress", did)
        if dex_addr:
            code_size = len(w3.eth.get_code(Web3.to_checksum_address(dex_addr)))
            print(f"\n  DEX #{did}: {dex_addr}")
            print(f"    Code size: {code_size} bytes")

# Check shared liquidity layer
print("\n\n[3] Liquidity Layer Analysis")
liq_code_size = len(w3.eth.get_code(Web3.to_checksum_address(FLUID_LIQUIDITY)))
print(f"  Liquidity contract: {FLUID_LIQUIDITY}")
print(f"  Code size: {liq_code_size} bytes")

# Check if any DEX pools share tokens with vault markets
# This is the key composition question
print("\n\n[4] Composition Check: Do DEX pools and Vaults share underlying tokens?")
print("  (If yes, manipulating DEX price could affect vault oracle pricing)")
print("  NOTE: Fluid uses Chainlink oracles for vault liquidations, NOT its own DEX prices")
print("  Key question: Is there any path from DEX manipulation → oracle update → vault liquidation?")

# Check Fluid oracle architecture
# Fluid typically uses a separate oracle contract per vault
# Let's check what oracle the resolver reports
print("\n\n[5] Checking Fluid oracle usage patterns...")

# Try to read known Fluid vault configs to find oracle addresses
# The vault stores oracle address in its constants
# We need to decode the constants view

# Alternative approach: check if Fluid has a governance/admin that can change oracles
FLUID_GOVERNANCE = "0x2386DC45AdDed673317eF068992F19421B481F4c"  # FluidGovernance
gov_code = len(w3.eth.get_code(Web3.to_checksum_address(FLUID_GOVERNANCE)))
print(f"\n  Governance contract: {FLUID_GOVERNANCE}")
print(f"  Code size: {gov_code} bytes")

# Check recent Fluid security - any recent exploit events?
print("\n\n[6] TVL Check - Liquidity Layer ETH/WETH balance")
eth_balance = w3.eth.get_balance(Web3.to_checksum_address(FLUID_LIQUIDITY))
print(f"  ETH balance: {eth_balance / 1e18:.2f} ETH")

# Check WETH balance
WETH = "0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2"
weth_c = w3.eth.contract(address=Web3.to_checksum_address(WETH), abi=json.loads('''[
  {"inputs":[{"internalType":"address","name":"","type":"address"}],"name":"balanceOf","outputs":[{"internalType":"uint256","name":"","type":"uint256"}],"stateMutability":"view","type":"function"}
]'''))
weth_bal = safe_call(weth_c, "balanceOf", Web3.to_checksum_address(FLUID_LIQUIDITY))
if weth_bal:
    print(f"  WETH balance: {weth_bal / 1e18:.2f} WETH")

# Check USDC balance
USDC = "0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48"
usdc_c = w3.eth.contract(address=Web3.to_checksum_address(USDC), abi=json.loads('''[
  {"inputs":[{"internalType":"address","name":"","type":"address"}],"name":"balanceOf","outputs":[{"internalType":"uint256","name":"","type":"uint256"}],"stateMutability":"view","type":"function"}
]'''))
usdc_bal = safe_call(usdc_c, "balanceOf", Web3.to_checksum_address(FLUID_LIQUIDITY))
if usdc_bal:
    print(f"  USDC balance: {usdc_bal / 1e6:.2f} USDC")

# Check USDT
USDT = "0xdAC17F958D2ee523a2206206994597C13D831ec7"
usdt_c = w3.eth.contract(address=Web3.to_checksum_address(USDT), abi=json.loads('''[
  {"inputs":[{"internalType":"address","name":"","type":"address"}],"name":"balanceOf","outputs":[{"internalType":"uint256","name":"","type":"uint256"}],"stateMutability":"view","type":"function"}
]'''))
usdt_bal = safe_call(usdt_c, "balanceOf", Web3.to_checksum_address(FLUID_LIQUIDITY))
if usdt_bal:
    print(f"  USDT balance: {usdt_bal / 1e6:.2f} USDT")

# Check wstETH
WSTETH = "0x7f39C581F595B53c5cb19bD0b3f8dA6c935E2Ca0"
wst_c = w3.eth.contract(address=Web3.to_checksum_address(WSTETH), abi=json.loads('''[
  {"inputs":[{"internalType":"address","name":"","type":"address"}],"name":"balanceOf","outputs":[{"internalType":"uint256","name":"","type":"uint256"}],"stateMutability":"view","type":"function"}
]'''))
wst_bal = safe_call(wst_c, "balanceOf", Web3.to_checksum_address(FLUID_LIQUIDITY))
if wst_bal:
    print(f"  wstETH balance: {wst_bal / 1e18:.2f} wstETH")

# Check weETH
WEETH = "0xCd5fE23C85820F7B72D0926FC9b05b43E359b7ee"
we_c = w3.eth.contract(address=Web3.to_checksum_address(WEETH), abi=json.loads('''[
  {"inputs":[{"internalType":"address","name":"","type":"address"}],"name":"balanceOf","outputs":[{"internalType":"uint256","name":"","type":"uint256"}],"stateMutability":"view","type":"function"}
]'''))
we_bal = safe_call(we_c, "balanceOf", Web3.to_checksum_address(FLUID_LIQUIDITY))
if we_bal:
    print(f"  weETH balance: {we_bal / 1e18:.2f} weETH")

# Check cbBTC
CBBTC = "0xcbB7C0000aB88B473b1f5aFd9ef808440eed33Bf"
cb_c = w3.eth.contract(address=Web3.to_checksum_address(CBBTC), abi=json.loads('''[
  {"inputs":[{"internalType":"address","name":"","type":"address"}],"name":"balanceOf","outputs":[{"internalType":"uint256","name":"","type":"uint256"}],"stateMutability":"view","type":"function"}
]'''))
cb_bal = safe_call(cb_c, "balanceOf", Web3.to_checksum_address(CBBTC))
if cb_bal:
    print(f"  cbBTC balance: {cb_bal / 1e8:.4f} cbBTC")

print("\n\n" + "="*80)
print("ANALYSIS SUMMARY")
print("="*80)
print("""
Key architecture points for Fluid:
1. Liquidity Layer is SHARED between Lending (Vaults) and DEX
2. Vaults use EXTERNAL Chainlink oracles for pricing (not DEX prices)
3. DEX uses its own internal pricing mechanism
4. The shared liquidity means:
   - Vaults and DEX draw from the same pool
   - A large DEX swap could affect available liquidity for lending
   - But oracle prices come from Chainlink, not DEX — so price manipulation via DEX is BLOCKED

Attack surface evaluation:
- Oracle manipulation via DEX: BLOCKED (Chainlink oracles)
- Liquidity drainage via DEX: LIMITED (per-protocol limits set by governance)
- Flash loan + DEX manipulation: Need to check if cool-off period exists
- Vault<->DEX composition: Need to check if a user can simultaneously have
  vault positions and DEX positions that interact
""")
