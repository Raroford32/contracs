#!/usr/bin/env python3
"""Follow-up checks: gov contract, pricing interpretation, withdraw revert analysis."""

import os
import json
from web3 import Web3

RPC_URL = os.environ.get("MAINNET_ALCHEMY") or os.environ.get("RPC")
w3 = Web3(Web3.HTTPProvider(RPC_URL))

ONE_ETH = Web3.to_checksum_address("0x6fcBBb527fb2954bed2B224a5bb7c23c5AeEb6e1")
USDC = Web3.to_checksum_address("0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48")
GOV = Web3.to_checksum_address("0xfF7B5E167c9877f2b9f65D19d9c8c9aa651Fe19F")
STIMULUS_ORACLE = "0x0000000000000000000000000000000000000000"

print("="*80)
print("ANALYSIS: Why consultOneWithdraw returns 0")
print("="*80)
print()
print("Key facts:")
print(f"  chainLink = True")
print(f"  stimulusOracle = {STIMULUS_ORACLE} (address(0)!)")
print(f"  stimulus = 0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2 (WETH)")
print()
print("When chainLink=true, the withdraw path likely calls stimulusOracle")
print("to get the stimulus price. Since stimulusOracle is address(0),")
print("calling it will revert or return 0.")
print("consultOneWithdraw returns 0, meaning withdraw is effectively broken.")
print()

print("="*80)
print("PRICING INTERPRETATION")
print("="*80)
print()
print("getCollateralUsd(USDC) = 713682102")
print("  -> If 9 decimals: 0.713682102 USD per USDC (slightly off peg?)")
print("  -> If 6 decimals: 713.682102 USD per USDC (wrong)")
print("  -> If 8 decimals: 7.13682102 USD (wrong)")
print("  -> Most likely 9 decimal precision: ~$0.71 per USDC (stale/broken oracle?)")
print()
print("getOneTokenUsd() = 603551328")
print("  -> If 9 decimals: 0.603551328 USD per oneETH")
print("  -> oneETH is trading at ~$0.60 per its own oracle")
print()
print("reserveRatio = 99800000000")
print("  -> If percentage with 9 decimals: 99.8% reserve ratio")
print()
print("withdrawFee = 100000000000")
print("  -> If basis points with 9 decimals: 100% fee?? Or maybe 10% with different scaling")
print("  -> If percentage with 11 decimals: 100%")
print()
print("mintFee = 100000000000")
print("  -> Same as withdrawFee")
print()

# Check gov contract bytecode
print("="*80)
print("GOV CONTRACT ANALYSIS")
print("="*80)
gov_code = w3.eth.get_code(GOV)
print(f"Gov address: {GOV}")
print(f"Gov bytecode length: {len(gov_code)} bytes")
print(f"Gov bytecode: {gov_code.hex()}")
print()

# Try common governance/multisig function selectors on gov
GOV_ABI = json.loads("""[
    {"inputs":[],"name":"owner","outputs":[{"type":"address"}],"stateMutability":"view","type":"function"},
    {"inputs":[],"name":"getOwners","outputs":[{"type":"address[]"}],"stateMutability":"view","type":"function"},
    {"inputs":[],"name":"threshold","outputs":[{"type":"uint256"}],"stateMutability":"view","type":"function"},
    {"inputs":[],"name":"nonce","outputs":[{"type":"uint256"}],"stateMutability":"view","type":"function"},
    {"inputs":[],"name":"implementation","outputs":[{"type":"address"}],"stateMutability":"view","type":"function"}
]""")

gov_contract = w3.eth.contract(address=GOV, abi=GOV_ABI)
for fn_name in ["owner", "getOwners", "threshold", "nonce", "implementation"]:
    try:
        result = getattr(gov_contract.functions, fn_name)().call()
        print(f"  gov.{fn_name}(): {result}")
    except Exception as e:
        print(f"  gov.{fn_name}(): ERROR - {e}")

# Check if gov is a minimal proxy (EIP-1167)
if gov_code.hex().startswith("363d3d373d3d3d363d73"):
    impl_addr = "0x" + gov_code.hex()[20:60]
    print(f"\n  GOV IS AN EIP-1167 MINIMAL PROXY -> implementation: {impl_addr}")
    impl_code = w3.eth.get_code(Web3.to_checksum_address(impl_addr))
    print(f"  Implementation bytecode length: {len(impl_code)} bytes")

print()

# Check collateral oracle
COLLATERAL_ORACLE = Web3.to_checksum_address("0x25D4Ba0b43Ce3B1805906060F8Bd74868D37388E")
print("="*80)
print(f"COLLATERAL ORACLE: {COLLATERAL_ORACLE}")
print("="*80)
oracle_code = w3.eth.get_code(COLLATERAL_ORACLE)
print(f"Code length: {len(oracle_code)} bytes -> {'CONTRACT' if len(oracle_code) > 0 else 'EOA/EMPTY'}")

# Try typical oracle functions
ORACLE_ABI = json.loads("""[
    {"inputs":[],"name":"latestAnswer","outputs":[{"type":"int256"}],"stateMutability":"view","type":"function"},
    {"inputs":[],"name":"latestRoundData","outputs":[{"type":"uint80"},{"type":"int256"},{"type":"uint256"},{"type":"uint256"},{"type":"uint80"}],"stateMutability":"view","type":"function"},
    {"inputs":[],"name":"decimals","outputs":[{"type":"uint8"}],"stateMutability":"view","type":"function"},
    {"inputs":[],"name":"description","outputs":[{"type":"string"}],"stateMutability":"view","type":"function"},
    {"inputs":[],"name":"consult","outputs":[{"type":"uint256"}],"stateMutability":"view","type":"function"}
]""")

if len(oracle_code) > 0:
    oracle = w3.eth.contract(address=COLLATERAL_ORACLE, abi=ORACLE_ABI)
    for fn_name in ["latestAnswer", "decimals", "description"]:
        try:
            result = getattr(oracle.functions, fn_name)().call()
            print(f"  oracle.{fn_name}(): {result}")
        except:
            pass
    try:
        result = oracle.functions.latestRoundData().call()
        print(f"  oracle.latestRoundData(): roundId={result[0]}, answer={result[1]}, startedAt={result[2]}, updatedAt={result[3]}, answeredInRound={result[4]}")
        import time
        staleness = int(time.time()) - result[3]
        print(f"  Oracle staleness: {staleness} seconds = {staleness/3600:.1f} hours = {staleness/86400:.1f} days")
    except Exception as e:
        print(f"  oracle.latestRoundData(): ERROR - {e}")

# Check owner of oneETH
print()
print("="*80)
print("OWNER ANALYSIS")
print("="*80)
owner = Web3.to_checksum_address("0x11111D16485aa71D2f2BfFBD294DCACbaE79c1d4")
print(f"Owner: {owner}")
owner_bal = w3.eth.get_balance(owner)
print(f"Owner ETH balance: {owner_bal / 10**18:.6f} ETH")
owner_nonce = w3.eth.get_transaction_count(owner)
print(f"Owner tx count: {owner_nonce}")

# Check if the contract is a Gnosis Safe
print()
print("="*80)
print("CHECKING IF GOV IS GNOSIS SAFE PROXY")
print("="*80)
# Gnosis Safe proxy stores master copy at slot 0
try:
    slot0 = w3.eth.get_storage_at(GOV, 0)
    print(f"  Gov storage slot 0: {slot0.hex()}")
    # Extract address from slot 0 (last 20 bytes)
    potential_impl = "0x" + slot0.hex()[-40:]
    print(f"  Potential implementation/masterCopy: {potential_impl}")
    impl_code_len = len(w3.eth.get_code(Web3.to_checksum_address(potential_impl)))
    print(f"  Implementation code length: {impl_code_len} bytes")
except Exception as e:
    print(f"  Error: {e}")

# Check SushiSwap / other routers for oneETH pairs
print()
print("="*80)
print("SUSHISWAP / ADDITIONAL DEX CHECK")
print("="*80)
# Sushi V2 Factory
SUSHI_FACTORY = Web3.to_checksum_address("0xC0AEe478e3658e2610c5F7A4A2E1777cE9e4f2Ac")
WETH = Web3.to_checksum_address("0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2")
SUSHI_ABI = json.loads("""[
    {"inputs":[{"type":"address"},{"type":"address"}],"name":"getPair","outputs":[{"type":"address"}],"stateMutability":"view","type":"function"}
]""")
sushi = w3.eth.contract(address=SUSHI_FACTORY, abi=SUSHI_ABI)

# Uniswap V2 Factory
UNI_FACTORY = Web3.to_checksum_address("0x5C69bEe701ef814a2B6a3EDD4B1652CB9cc5aA6f")
uni = w3.eth.contract(address=UNI_FACTORY, abi=SUSHI_ABI)

for dex_name, factory in [("Uniswap V2", uni), ("SushiSwap", sushi)]:
    try:
        pair = factory.functions.getPair(ONE_ETH, WETH).call()
        print(f"  {dex_name} oneETH/WETH pair: {pair}")
        if pair != "0x0000000000000000000000000000000000000000":
            pair_contract = w3.eth.contract(address=Web3.to_checksum_address(pair), abi=json.loads("""[
                {"inputs":[],"name":"getReserves","outputs":[{"type":"uint112"},{"type":"uint112"},{"type":"uint32"}],"stateMutability":"view","type":"function"},
                {"inputs":[],"name":"token0","outputs":[{"type":"address"}],"stateMutability":"view","type":"function"}
            ]"""))
            t0 = pair_contract.functions.token0().call()
            reserves = pair_contract.functions.getReserves().call()
            print(f"    token0: {t0}")
            print(f"    reserves: {reserves[0]}, {reserves[1]}")
    except Exception as e:
        print(f"  {dex_name}: ERROR - {e}")

    # Also check oneETH/USDC
    try:
        pair = factory.functions.getPair(ONE_ETH, USDC).call()
        print(f"  {dex_name} oneETH/USDC pair: {pair}")
    except Exception as e:
        print(f"  {dex_name} oneETH/USDC: ERROR - {e}")

print()
print("="*80)
print("SUMMARY OF CRITICAL FINDINGS")
print("="*80)
print("""
1. chainLink = True BUT stimulusOracle = address(0)
   -> This is a critical inconsistency. When chainLink is true, the contract
      likely tries to use stimulusOracle for pricing. But it's address(0).
   -> consultOneWithdraw returns 0 for any amount, confirming withdraw is broken.

2. consultOneDeposit WORKS:
   -> 1 USDC (1e6) -> 1398 oneETH (raw, 9 dec) = 0.000001398 oneETH
   -> 1e9 USDC -> ~1398381 raw = ~0.001398 oneETH
   -> Minting still functions, but the exchange rate seems odd.

3. Collateral situation:
   -> USDC held by contract: ~228,872 USDC
   -> oneETH total supply: ~228,706 oneETH
   -> Reserve ratio ~99.8% (as reported by the contract)

4. DEX liquidity:
   -> Uniswap V2 oneETH/WETH pair has:
      ~225,123 oneETH and ~65 WETH
   -> Price: 1 oneETH ~ 0.000289 WETH
   -> At ~$2,500/ETH: 1 oneETH ~ $0.72
   -> oneETH is supposed to be pegged to 1 ETH but trades at ~0.03% of ETH price!

5. Gov/lpGov = same address (0xfF7B...) which is a contract (170 bytes = likely proxy)
   Owner = EOA (0x11111D16...)

6. getOneTokenUsd() = 603551328 -> ~$0.60 per oneETH (9 dec precision)
   getCollateralUsd(USDC) = 713682102 -> ~$0.71 per USDC (9 dec precision)
""")
