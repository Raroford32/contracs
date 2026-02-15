#!/usr/bin/env python3
"""Final deep checks: Gnosis Safe details, fee interpretation, withdraw revert."""

import os
import json
from web3 import Web3

RPC_URL = os.environ.get("MAINNET_ALCHEMY") or os.environ.get("RPC")
w3 = Web3(Web3.HTTPProvider(RPC_URL))

ONE_ETH = Web3.to_checksum_address("0x6fcBBb527fb2954bed2B224a5bb7c23c5AeEb6e1")
USDC = Web3.to_checksum_address("0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48")
GOV = Web3.to_checksum_address("0xfF7B5E167c9877f2b9f65D19d9c8c9aa651Fe19F")
GNOSIS_IMPL = Web3.to_checksum_address("0xd9Db270c1B5E3Bd161E8c8503c55cEABeE709552")

# The gov is a Gnosis Safe with masterCopy 0xd9Db270c1B5E3Bd161E8c8503c55cEABeE709552
# This is the standard Gnosis Safe L1 v1.3.0

SAFE_ABI = json.loads("""[
    {"inputs":[],"name":"getOwners","outputs":[{"type":"address[]"}],"stateMutability":"view","type":"function"},
    {"inputs":[],"name":"getThreshold","outputs":[{"type":"uint256"}],"stateMutability":"view","type":"function"},
    {"inputs":[],"name":"nonce","outputs":[{"type":"uint256"}],"stateMutability":"view","type":"function"},
    {"inputs":[],"name":"VERSION","outputs":[{"type":"string"}],"stateMutability":"view","type":"function"}
]""")

safe = w3.eth.contract(address=GOV, abi=SAFE_ABI)

print("="*80)
print("GNOSIS SAFE (gov/lpGov) DETAILS")
print("="*80)
print(f"MasterCopy: {GNOSIS_IMPL} (Gnosis Safe L1 v1.3.0)")

try:
    version = safe.functions.VERSION().call()
    print(f"VERSION: {version}")
except Exception as e:
    print(f"VERSION: ERROR - {e}")

try:
    threshold = safe.functions.getThreshold().call()
    print(f"Threshold: {threshold}")
except Exception as e:
    print(f"Threshold: ERROR - {e}")

try:
    owners = safe.functions.getOwners().call()
    print(f"Owners ({len(owners)}):")
    for o in owners:
        code = w3.eth.get_code(Web3.to_checksum_address(o))
        bal = w3.eth.get_balance(Web3.to_checksum_address(o))
        print(f"  {o} - {'CONTRACT' if len(code) > 0 else 'EOA'} - {bal/10**18:.4f} ETH")
except Exception as e:
    print(f"Owners: ERROR - {e}")

try:
    nonce = safe.functions.nonce().call()
    print(f"Nonce: {nonce}")
except Exception as e:
    print(f"Nonce: ERROR - {e}")

# Now let's try to understand the fee scaling
print()
print("="*80)
print("FEE AND RATIO SCALING ANALYSIS")
print("="*80)
print()
print("oneETH decimals = 9")
print()
print("reserveRatio = 99800000000")
print("  If 1e11 = 100%: ratio = 99.8%")
print("  -> Means 99.8% collateral-backed, 0.2% algorithmic")
print()
print("withdrawFee = 100000000000 = 1e11")
print("  If 1e11 = 100%: fee = 100% (would take entire amount! likely wrong)")
print("  If 1e13 = 100%: fee = 1%")
print("  If fee is in basis points * 1e9: 100 bp = 1%")
print("  100000000000 / 1e9 = 100 -> 100 basis points = 1%")
print()
print("mintFee = 100000000000 = 1e11")
print("  Same scaling -> 1%")

# Try to simulate a withdraw via eth_call to see what happens
print()
print("="*80)
print("SIMULATING withdraw() via eth_call")
print("="*80)

WITHDRAW_ABI = json.loads("""[
    {"inputs":[{"type":"address"},{"type":"uint256"}],"name":"withdraw","outputs":[],"stateMutability":"nonpayable","type":"function"}
]""")

contract = w3.eth.contract(address=ONE_ETH, abi=WITHDRAW_ABI)

# We need to simulate from an address that actually holds oneETH
# Let's find the pair which holds the most
ONE_ETH_WETH_PAIR = Web3.to_checksum_address("0x3bab83c78c30ac4c082b06bd62587f1e31172f8f")

# Try simulating withdraw from the pair (which holds 225k oneETH)
try:
    withdraw_data = contract.functions.withdraw(USDC, 1000000000).build_transaction({
        'from': ONE_ETH_WETH_PAIR,
        'gas': 1000000,
        'gasPrice': 0,
        'nonce': 0,
        'chainId': 1,
    })
    result = w3.eth.call({
        'from': ONE_ETH_WETH_PAIR,
        'to': ONE_ETH,
        'data': withdraw_data['data'],
        'gas': 1000000,
    })
    print(f"  withdraw(USDC, 1e9) from pair: SUCCESS - {result.hex()}")
except Exception as e:
    error_str = str(e)
    print(f"  withdraw(USDC, 1e9) from pair: REVERTED")
    print(f"  Error: {error_str[:500]}")

# Try simulate mint
print()
print("="*80)
print("SIMULATING mint() via eth_call")
print("="*80)

MINT_ABI = json.loads("""[
    {"inputs":[{"type":"address"},{"type":"uint256"}],"name":"mint","outputs":[],"stateMutability":"nonpayable","type":"function"}
]""")

mint_contract = w3.eth.contract(address=ONE_ETH, abi=MINT_ABI)

# Simulate minting from a USDC holder
try:
    mint_data = mint_contract.functions.mint(USDC, 1000000).build_transaction({
        'from': ONE_ETH_WETH_PAIR,
        'gas': 1000000,
        'gasPrice': 0,
        'nonce': 0,
        'chainId': 1,
    })
    result = w3.eth.call({
        'from': ONE_ETH_WETH_PAIR,
        'to': ONE_ETH,
        'data': mint_data['data'],
        'gas': 1000000,
    })
    print(f"  mint(USDC, 1e6) from pair: SUCCESS - {result.hex()}")
except Exception as e:
    error_str = str(e)
    print(f"  mint(USDC, 1e6) from pair: REVERTED")
    print(f"  Error: {error_str[:500]}")

# Check the collateral oracle more carefully
print()
print("="*80)
print("COLLATERAL ORACLE DEEP CHECK")
print("="*80)
COLLATERAL_ORACLE = Web3.to_checksum_address("0x25D4Ba0b43Ce3B1805906060F8Bd74868D37388E")

# Check if it's a TWAP/UniswapV2 oracle
TWAP_ABI = json.loads("""[
    {"inputs":[{"type":"address"},{"type":"uint256"}],"name":"consult","outputs":[{"type":"uint256"}],"stateMutability":"view","type":"function"},
    {"inputs":[],"name":"pair","outputs":[{"type":"address"}],"stateMutability":"view","type":"function"},
    {"inputs":[],"name":"token0","outputs":[{"type":"address"}],"stateMutability":"view","type":"function"},
    {"inputs":[],"name":"token1","outputs":[{"type":"address"}],"stateMutability":"view","type":"function"},
    {"inputs":[],"name":"price0CumulativeLast","outputs":[{"type":"uint256"}],"stateMutability":"view","type":"function"},
    {"inputs":[],"name":"price1CumulativeLast","outputs":[{"type":"uint256"}],"stateMutability":"view","type":"function"},
    {"inputs":[],"name":"blockTimestampLast","outputs":[{"type":"uint32"}],"stateMutability":"view","type":"function"},
    {"inputs":[],"name":"price0Average","outputs":[{"type":"uint224"},{"type":"uint32"}],"stateMutability":"view","type":"function"},
    {"inputs":[],"name":"price1Average","outputs":[{"type":"uint224"},{"type":"uint32"}],"stateMutability":"view","type":"function"},
    {"inputs":[],"name":"factory","outputs":[{"type":"address"}],"stateMutability":"view","type":"function"},
    {"inputs":[],"name":"PERIOD","outputs":[{"type":"uint256"}],"stateMutability":"view","type":"function"}
]""")

oracle = w3.eth.contract(address=COLLATERAL_ORACLE, abi=TWAP_ABI)
for fn_name in ["pair", "token0", "token1", "factory", "PERIOD", "blockTimestampLast",
                 "price0CumulativeLast", "price1CumulativeLast"]:
    try:
        result = getattr(oracle.functions, fn_name)().call()
        print(f"  oracle.{fn_name}(): {result}")
    except Exception as e:
        print(f"  oracle.{fn_name}(): ERROR")

# Try consult for USDC
try:
    result = oracle.functions.consult(USDC, 10**6).call()
    print(f"  oracle.consult(USDC, 1e6): {result}")
except Exception as e:
    print(f"  oracle.consult(USDC, 1e6): ERROR - {e}")

# Summarize
print()
print("="*80)
print("COMPREHENSIVE STATE SUMMARY")
print("="*80)
print("""
CONTRACT: 0x6fcBBb527fb2954bed2B224a5bb7c23c5AeEb6e1 (oneETH)
CHAIN: Ethereum Mainnet
BLOCK: current (live query)

=== CRITICAL STATE ===

1. chainLink = TRUE
   - stimulusOracle = address(0) (ZERO ADDRESS!)
   - stimulus = WETH (0xC02...Cc2)
   - CONSEQUENCE: When chainLink=true, withdraw path uses stimulusOracle
     to price the stimulus token (WETH). Since stimulusOracle is address(0),
     the call to get stimulus price will fail/return 0.
   - consultOneWithdraw() returns 0 for ALL inputs -> withdraw is BROKEN.

2. consultOneWithdraw(any_amount, USDC) = 0
   - Confirmed: withdrawing any amount returns 0 collateral.
   - This means withdraw() is either reverting or giving users nothing.

3. consultOneDeposit(1e6 USDC, USDC) = 1398 raw oneETH
   - Minting works but gives very little oneETH per USDC.
   - 1 USDC -> 0.000001398 oneETH
   - Implied: 1 oneETH costs ~715,307 USDC via minting (!!!!)

4. gov() = lpGov() = 0xfF7B...Fe19F
   - Gnosis Safe v1.3.0 (proxy -> 0xd9Db270c)
   - 7 owners, threshold unknown (getThreshold may need different selector)
   - Owner EOAs listed above
   - Safe nonce: 2432

5. oneETH owner() = 0x11111D16...c1d4 (EOA, ~0.00008 ETH, 2224 txs)

=== COLLATERAL & SUPPLY ===

6. totalSupply = 228,706 oneETH (9 decimals)
7. USDC in contract = 228,872 USDC
8. ETH in contract = 11.96 ETH
9. reserveRatio = 99.8%

=== DEX LIQUIDITY ===

10. oneETH/WETH pair (0x3bab...): NOT on Uniswap V2 or SushiSwap
    - This pair is on some other DEX (maybe a custom pair)
    - Reserves: 225,123 oneETH / 65 WETH
    - Price: 1 oneETH = 0.000289 WETH (~$0.72 at $2500/ETH)
    - 98.4% of total supply is in this pair!

11. No Uniswap V2 or SushiSwap pairs exist.

=== PRICING ===

12. getOneTokenUsd() = 603551328 -> ~$0.604 (9 dec precision)
13. getCollateralUsd(USDC) = 713682102 -> ~$0.714 per USDC (stale/wrong oracle?)

=== IMPLICATIONS ===

- oneETH is essentially a dead/abandoned stablecoin project
- Withdraw is broken (stimulusOracle = address(0) while chainLink = true)
- ~228,872 USDC is locked in the contract as collateral
- The DEX pair prices oneETH at ~$0.72 (massively off its $1 peg)
- Minting via deposit still technically works but at absurd rates
- Anyone who can fix the stimulusOracle (gov/owner) could unlock withdrawals
  and drain the ~228k USDC collateral
""")
