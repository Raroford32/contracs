#!/usr/bin/env python3
"""Check critical on-chain state for oneETH contract."""

import os
import json
import traceback
from web3 import Web3

RPC_URL = os.environ.get("MAINNET_ALCHEMY") or os.environ.get("RPC")
if not RPC_URL:
    raise RuntimeError("No RPC URL found in MAINNET_ALCHEMY or RPC env vars")

w3 = Web3(Web3.HTTPProvider(RPC_URL))
print(f"Connected: {w3.is_connected()}")
print(f"Block number: {w3.eth.block_number}")

ONE_ETH = "0x6fcBBb527fb2954bed2B224a5bb7c23c5AeEb6e1"
USDC = "0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48"
ONE_ETH_WETH_PAIR = "0x3bab83c78c30ac4c082b06bd62587f1e31172f8f"

# Minimal ABI for the calls we need
ONE_ETH_ABI = json.loads("""[
    {"inputs":[],"name":"chainLink","outputs":[{"type":"bool"}],"stateMutability":"view","type":"function"},
    {"inputs":[{"type":"uint256"},{"type":"address"}],"name":"consultOneWithdraw","outputs":[{"type":"uint256"}],"stateMutability":"view","type":"function"},
    {"inputs":[{"type":"uint256"},{"type":"address"}],"name":"consultOneDeposit","outputs":[{"type":"uint256"}],"stateMutability":"view","type":"function"},
    {"inputs":[],"name":"gov","outputs":[{"type":"address"}],"stateMutability":"view","type":"function"},
    {"inputs":[],"name":"lpGov","outputs":[{"type":"address"}],"stateMutability":"view","type":"function"},
    {"inputs":[{"type":"address"}],"name":"balanceOf","outputs":[{"type":"uint256"}],"stateMutability":"view","type":"function"},
    {"inputs":[],"name":"totalSupply","outputs":[{"type":"uint256"}],"stateMutability":"view","type":"function"},
    {"inputs":[{"type":"address"}],"name":"getCollateralUsd","outputs":[{"type":"uint256"}],"stateMutability":"view","type":"function"},
    {"inputs":[],"name":"getOneTokenUsd","outputs":[{"type":"uint256"}],"stateMutability":"view","type":"function"},
    {"inputs":[],"name":"stimulusOracle","outputs":[{"type":"address"}],"stateMutability":"view","type":"function"},
    {"inputs":[],"name":"stimulus","outputs":[{"type":"address"}],"stateMutability":"view","type":"function"},
    {"inputs":[],"name":"MIN_DELAY","outputs":[{"type":"uint256"}],"stateMutability":"view","type":"function"},
    {"inputs":[],"name":"withdrawFee","outputs":[{"type":"uint256"}],"stateMutability":"view","type":"function"},
    {"inputs":[],"name":"mintFee","outputs":[{"type":"uint256"}],"stateMutability":"view","type":"function"},
    {"inputs":[],"name":"MIN_RESERVE_RATIO","outputs":[{"type":"uint256"}],"stateMutability":"view","type":"function"},
    {"inputs":[],"name":"reserveRatio","outputs":[{"type":"uint256"}],"stateMutability":"view","type":"function"},
    {"inputs":[],"name":"decimals","outputs":[{"type":"uint8"}],"stateMutability":"view","type":"function"},
    {"inputs":[{"type":"address"}],"name":"acceptedCollateral","outputs":[{"type":"bool"}],"stateMutability":"view","type":"function"},
    {"inputs":[{"type":"address"}],"name":"collateralOracle","outputs":[{"type":"address"}],"stateMutability":"view","type":"function"},
    {"inputs":[],"name":"previouslyKnownCollateral","outputs":[{"type":"address[]"}],"stateMutability":"view","type":"function"},
    {"inputs":[],"name":"owner","outputs":[{"type":"address"}],"stateMutability":"view","type":"function"},
    {"inputs":[],"name":"name","outputs":[{"type":"string"}],"stateMutability":"view","type":"function"},
    {"inputs":[],"name":"symbol","outputs":[{"type":"string"}],"stateMutability":"view","type":"function"}
]""")

ERC20_ABI = json.loads("""[
    {"inputs":[{"type":"address"}],"name":"balanceOf","outputs":[{"type":"uint256"}],"stateMutability":"view","type":"function"},
    {"inputs":[],"name":"totalSupply","outputs":[{"type":"uint256"}],"stateMutability":"view","type":"function"},
    {"inputs":[],"name":"decimals","outputs":[{"type":"uint8"}],"stateMutability":"view","type":"function"}
]""")

contract = w3.eth.contract(address=Web3.to_checksum_address(ONE_ETH), abi=ONE_ETH_ABI)

def safe_call(label, fn, *args):
    """Call a contract function safely, returning result or error."""
    try:
        result = fn(*args).call()
        print(f"  {label}: {result}")
        return result
    except Exception as e:
        print(f"  {label}: REVERTED/ERROR - {e}")
        return None

print("\n" + "="*80)
print("1. CRITICAL: chainLink boolean")
print("="*80)
chain_link = safe_call("chainLink()", contract.functions.chainLink)

print("\n" + "="*80)
print("1b. Related: stimulusOracle and stimulus addresses")
print("="*80)
stim_oracle = safe_call("stimulusOracle()", contract.functions.stimulusOracle)
stimulus = safe_call("stimulus()", contract.functions.stimulus)

print("\n" + "="*80)
print("2. consultOneWithdraw(1000000000, USDC) - simulate withdraw 1 oneETH for USDC")
print("   (1e9 = 1 oneETH assuming 9 decimals)")
print("="*80)
decimals = safe_call("decimals()", contract.functions.decimals)
# Try with 1e9 (if 9 decimals) and also 1e18 (if 18 decimals)
for amt_label, amt in [("1e9", 10**9), ("1e18", 10**18)]:
    safe_call(f"consultOneWithdraw({amt_label}, USDC)",
              contract.functions.consultOneWithdraw, amt, Web3.to_checksum_address(USDC))

print("\n" + "="*80)
print("3. consultOneDeposit(1000000000, USDC) - simulate minting 1 oneETH with USDC")
print("="*80)
for amt_label, amt in [("1e6 (1 USDC)", 10**6), ("1e9", 10**9), ("1e18", 10**18)]:
    safe_call(f"consultOneDeposit({amt_label}, USDC)",
              contract.functions.consultOneDeposit, amt, Web3.to_checksum_address(USDC))

print("\n" + "="*80)
print("4. gov() and lpGov() addresses")
print("="*80)
gov = safe_call("gov()", contract.functions.gov)
lp_gov = safe_call("lpGov()", contract.functions.lpGov)

# Check if they are EOAs or contracts
if gov:
    code = w3.eth.get_code(Web3.to_checksum_address(gov))
    print(f"  gov code length: {len(code)} bytes -> {'CONTRACT' if len(code) > 0 else 'EOA'}")
if lp_gov:
    code = w3.eth.get_code(Web3.to_checksum_address(lp_gov))
    print(f"  lpGov code length: {len(code)} bytes -> {'CONTRACT' if len(code) > 0 else 'EOA'}")

# Also check owner
try:
    owner = safe_call("owner()", contract.functions.owner)
    if owner:
        code = w3.eth.get_code(Web3.to_checksum_address(owner))
        print(f"  owner code length: {len(code)} bytes -> {'CONTRACT' if len(code) > 0 else 'EOA'}")
except:
    pass

print("\n" + "="*80)
print("5. oneETH balance of DEX pools")
print("="*80)
one_eth_erc20 = w3.eth.contract(address=Web3.to_checksum_address(ONE_ETH), abi=ERC20_ABI)

pairs_to_check = {
    "oneETH/WETH pair (0x3bab...)": ONE_ETH_WETH_PAIR,
}

for label, addr in pairs_to_check.items():
    try:
        bal = one_eth_erc20.functions.balanceOf(Web3.to_checksum_address(addr)).call()
        print(f"  {label}: {bal} raw = {bal / 10**9:.6f} oneETH (assuming 9 dec)")
        if decimals:
            print(f"  {label}: {bal / 10**decimals:.6f} oneETH (using actual {decimals} dec)")
    except Exception as e:
        print(f"  {label}: ERROR - {e}")

print("\n" + "="*80)
print("6. oneETH total supply and liquidity comparison")
print("="*80)
total_supply = safe_call("totalSupply()", one_eth_erc20.functions.totalSupply)
if total_supply and decimals:
    print(f"  Total supply in tokens: {total_supply / 10**decimals:.6f} oneETH")

# Check WETH balance in the pair too
WETH = "0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2"
weth_erc20 = w3.eth.contract(address=Web3.to_checksum_address(WETH), abi=ERC20_ABI)
try:
    weth_in_pair = weth_erc20.functions.balanceOf(Web3.to_checksum_address(ONE_ETH_WETH_PAIR)).call()
    print(f"  WETH in oneETH/WETH pair: {weth_in_pair} raw = {weth_in_pair / 10**18:.6f} WETH")
except Exception as e:
    print(f"  WETH in pair: ERROR - {e}")

# Check USDC balance in the oneETH contract (collateral)
usdc_erc20 = w3.eth.contract(address=Web3.to_checksum_address(USDC), abi=ERC20_ABI)
try:
    usdc_in_oneeth = usdc_erc20.functions.balanceOf(Web3.to_checksum_address(ONE_ETH)).call()
    print(f"  USDC held by oneETH contract: {usdc_in_oneeth} raw = {usdc_in_oneeth / 10**6:.2f} USDC")
except Exception as e:
    print(f"  USDC in oneETH: ERROR - {e}")

# Check oneETH balance in the contract itself
try:
    oneeth_in_self = one_eth_erc20.functions.balanceOf(Web3.to_checksum_address(ONE_ETH)).call()
    print(f"  oneETH held by oneETH contract: {oneeth_in_self} raw")
except Exception as e:
    print(f"  oneETH in self: ERROR - {e}")

print("\n" + "="*80)
print("7. getCollateralUsd(USDC)")
print("="*80)
safe_call("getCollateralUsd(USDC)", contract.functions.getCollateralUsd, Web3.to_checksum_address(USDC))

print("\n" + "="*80)
print("8. getOneTokenUsd()")
print("="*80)
safe_call("getOneTokenUsd()", contract.functions.getOneTokenUsd)

print("\n" + "="*80)
print("EXTRA: Key protocol parameters")
print("="*80)
safe_call("name()", contract.functions.name)
safe_call("symbol()", contract.functions.symbol)
safe_call("reserveRatio()", contract.functions.reserveRatio)
safe_call("withdrawFee()", contract.functions.withdrawFee)
safe_call("mintFee()", contract.functions.mintFee)
safe_call("acceptedCollateral(USDC)", contract.functions.acceptedCollateral, Web3.to_checksum_address(USDC))
safe_call("collateralOracle(USDC)", contract.functions.collateralOracle, Web3.to_checksum_address(USDC))

# Try to get known collateral list
try:
    collaterals = contract.functions.previouslyKnownCollateral().call()
    print(f"  previouslyKnownCollateral(): {collaterals}")
except Exception as e:
    print(f"  previouslyKnownCollateral(): ERROR - {e}")

print("\n" + "="*80)
print("EXTRA: Check if oneETH/WETH pair has any reserves (Uniswap V2 style)")
print("="*80)
PAIR_ABI = json.loads("""[
    {"inputs":[],"name":"getReserves","outputs":[{"type":"uint112"},{"type":"uint112"},{"type":"uint32"}],"stateMutability":"view","type":"function"},
    {"inputs":[],"name":"token0","outputs":[{"type":"address"}],"stateMutability":"view","type":"function"},
    {"inputs":[],"name":"token1","outputs":[{"type":"address"}],"stateMutability":"view","type":"function"},
    {"inputs":[],"name":"totalSupply","outputs":[{"type":"uint256"}],"stateMutability":"view","type":"function"}
]""")
try:
    pair = w3.eth.contract(address=Web3.to_checksum_address(ONE_ETH_WETH_PAIR), abi=PAIR_ABI)
    token0 = pair.functions.token0().call()
    token1 = pair.functions.token1().call()
    reserves = pair.functions.getReserves().call()
    lp_supply = pair.functions.totalSupply().call()
    print(f"  token0: {token0}")
    print(f"  token1: {token1}")
    print(f"  reserve0: {reserves[0]}")
    print(f"  reserve1: {reserves[1]}")
    print(f"  LP totalSupply: {lp_supply}")

    # Identify which is oneETH and which is WETH
    if token0.lower() == ONE_ETH.lower():
        one_reserve, weth_reserve = reserves[0], reserves[1]
        print(f"  -> oneETH reserve: {one_reserve}")
        print(f"  -> WETH reserve: {weth_reserve} = {weth_reserve / 10**18:.6f} ETH")
    else:
        weth_reserve, one_reserve = reserves[0], reserves[1]
        print(f"  -> WETH reserve: {weth_reserve} = {weth_reserve / 10**18:.6f} ETH")
        print(f"  -> oneETH reserve: {one_reserve}")

    if decimals and one_reserve > 0:
        print(f"  -> oneETH reserve in tokens: {one_reserve / 10**decimals:.6f}")
    if one_reserve > 0 and weth_reserve > 0:
        # Price of 1 oneETH in WETH terms
        price = weth_reserve / one_reserve
        print(f"  -> Price: 1 raw oneETH = {price:.12f} raw WETH")
        if decimals:
            adjusted_price = (weth_reserve / 10**18) / (one_reserve / 10**decimals)
            print(f"  -> Adjusted price: 1 oneETH = {adjusted_price:.8f} WETH")
except Exception as e:
    print(f"  Pair query failed: {e}")
    traceback.print_exc()

print("\n" + "="*80)
print("EXTRA: Check contract ETH balance")
print("="*80)
eth_bal = w3.eth.get_balance(Web3.to_checksum_address(ONE_ETH))
print(f"  ETH balance of oneETH contract: {eth_bal} wei = {eth_bal / 10**18:.6f} ETH")

print("\n" + "="*80)
print("DONE")
print("="*80)
