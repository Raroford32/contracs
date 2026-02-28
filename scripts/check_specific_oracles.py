#!/usr/bin/env python3
"""Check specific oracle configurations for recently found interesting markets."""
import json
import os
from web3 import Web3

RPC = os.environ.get("RPC", "https://eth-mainnet.g.alchemy.com/v2/pLXdY7rYRY10SH_UTLBGH")
w3 = Web3(Web3.HTTPProvider(RPC))

ORACLE_V2_ABI = json.loads('''[
  {"inputs":[],"name":"BASE_VAULT","outputs":[{"internalType":"contract IERC4626","name":"","type":"address"}],"stateMutability":"view","type":"function"},
  {"inputs":[],"name":"QUOTE_VAULT","outputs":[{"internalType":"contract IERC4626","name":"","type":"address"}],"stateMutability":"view","type":"function"},
  {"inputs":[],"name":"BASE_FEED_1","outputs":[{"internalType":"contract AggregatorV3Interface","name":"","type":"address"}],"stateMutability":"view","type":"function"},
  {"inputs":[],"name":"BASE_FEED_2","outputs":[{"internalType":"contract AggregatorV3Interface","name":"","type":"address"}],"stateMutability":"view","type":"function"},
  {"inputs":[],"name":"QUOTE_FEED_1","outputs":[{"internalType":"contract AggregatorV3Interface","name":"","type":"address"}],"stateMutability":"view","type":"function"},
  {"inputs":[],"name":"QUOTE_FEED_2","outputs":[{"internalType":"contract AggregatorV3Interface","name":"","type":"address"}],"stateMutability":"view","type":"function"},
  {"inputs":[],"name":"SCALE_FACTOR","outputs":[{"internalType":"uint256","name":"","type":"uint256"}],"stateMutability":"view","type":"function"},
  {"inputs":[],"name":"price","outputs":[{"internalType":"uint256","name":"","type":"uint256"}],"stateMutability":"view","type":"function"},
  {"inputs":[],"name":"BASE_VAULT_CONVERSION_SAMPLE","outputs":[{"internalType":"uint256","name":"","type":"uint256"}],"stateMutability":"view","type":"function"},
  {"inputs":[],"name":"QUOTE_VAULT_CONVERSION_SAMPLE","outputs":[{"internalType":"uint256","name":"","type":"uint256"}],"stateMutability":"view","type":"function"}
]''')

ERC4626_ABI = json.loads('''[
  {"inputs":[],"name":"totalAssets","outputs":[{"internalType":"uint256","name":"","type":"uint256"}],"stateMutability":"view","type":"function"},
  {"inputs":[],"name":"totalSupply","outputs":[{"internalType":"uint256","name":"","type":"uint256"}],"stateMutability":"view","type":"function"},
  {"inputs":[{"internalType":"uint256","name":"shares","type":"uint256"}],"name":"convertToAssets","outputs":[{"internalType":"uint256","name":"","type":"uint256"}],"stateMutability":"view","type":"function"},
  {"inputs":[],"name":"asset","outputs":[{"internalType":"address","name":"","type":"address"}],"stateMutability":"view","type":"function"},
  {"inputs":[],"name":"name","outputs":[{"internalType":"string","name":"","type":"string"}],"stateMutability":"view","type":"function"},
  {"inputs":[],"name":"symbol","outputs":[{"internalType":"string","name":"","type":"string"}],"stateMutability":"view","type":"function"}
]''')

ERC20_ABI = json.loads('''[
  {"inputs":[],"name":"symbol","outputs":[{"internalType":"string","name":"","type":"string"}],"stateMutability":"view","type":"function"},
  {"inputs":[],"name":"decimals","outputs":[{"internalType":"uint8","name":"","type":"uint8"}],"stateMutability":"view","type":"function"},
  {"inputs":[{"internalType":"address","name":"","type":"address"}],"name":"balanceOf","outputs":[{"internalType":"uint256","name":"","type":"uint256"}],"stateMutability":"view","type":"function"},
  {"inputs":[],"name":"totalSupply","outputs":[{"internalType":"uint256","name":"","type":"uint256"}],"stateMutability":"view","type":"function"}
]''')

def safe_call(contract, func_name, *args):
    try:
        return getattr(contract.functions, func_name)(*args).call()
    except:
        return None

ZERO = "0x0000000000000000000000000000000000000000"

# Interesting oracles to check
targets = [
    ("srRoyUSDC/USDC ($31K)", "0x86A807dc5E689F78e280B18413001Ca0c2426Ab0"),
    ("srRoyUSDC/USDC ($1)", "0x62011dc01c0B9833C4E53e20456400e4EA4b8363"),
    ("xPRISM/USDC", "0x3ca09869054C1d5C4e38de06b505045cA3cED279"),
    ("WOUSD/USDC", "0x7c65985C35181d51EF7571fA40211B57659b7D80"),
    ("bbqUSDCturbo/USDC", "0xcEB6017685e28Ee3eB3650890fc5af932E910FA2"),
    ("siUSD/msUSD ($526K)", "0xC7bB5f34D645f3849a3091Ce4b6724631ee811Af"),
    ("savUSD/frxUSD ($402K)", "0x639499c2FDBbB91b814e76932414c3a9a964bcB6"),
    ("SPYx/USDC", "0x7961a27E1414569AD11B046FFE6cd41Fc6Fcd4d5"),
    ("stakedao-FrxMsUSD/frxUSD ($8K, 94.5% LLTV)", "0xC5860e9e6b6F6E9D79DCe5c5AB0F7A4b878Bd431"),
]

for name, oracle_addr in targets:
    print(f"\n{'='*70}")
    print(f"Market: {name}")
    print(f"Oracle: {oracle_addr}")
    
    oc = w3.eth.contract(address=Web3.to_checksum_address(oracle_addr), abi=ORACLE_V2_ABI)
    
    base_vault = safe_call(oc, "BASE_VAULT")
    quote_vault = safe_call(oc, "QUOTE_VAULT")
    bf1 = safe_call(oc, "BASE_FEED_1")
    bf2 = safe_call(oc, "BASE_FEED_2")
    qf1 = safe_call(oc, "QUOTE_FEED_1")
    qf2 = safe_call(oc, "QUOTE_FEED_2")
    scale = safe_call(oc, "SCALE_FACTOR")
    price = safe_call(oc, "price")
    bv_sample = safe_call(oc, "BASE_VAULT_CONVERSION_SAMPLE")
    qv_sample = safe_call(oc, "QUOTE_VAULT_CONVERSION_SAMPLE")
    
    is_v2 = scale is not None
    
    if is_v2:
        print(f"  Type: MorphoChainlinkOracleV2")
        print(f"  SCALE_FACTOR: {scale}")
        print(f"  Price: {price}")
        print(f"  BASE_VAULT: {base_vault} {'*** SET ***' if base_vault and base_vault != ZERO else '(none)'}")
        print(f"  QUOTE_VAULT: {quote_vault} {'*** QUOTE_VAULT SET! DANGEROUS! ***' if quote_vault and quote_vault != ZERO else '(none)'}")
        print(f"  BASE_FEED_1: {bf1} {'(set)' if bf1 and bf1 != ZERO else '(none)'}")
        print(f"  BASE_FEED_2: {bf2} {'(set)' if bf2 and bf2 != ZERO else '(none)'}")
        print(f"  QUOTE_FEED_1: {qf1} {'(set)' if qf1 and qf1 != ZERO else '(none)'}")
        print(f"  QUOTE_FEED_2: {qf2} {'(set)' if qf2 and qf2 != ZERO else '(none)'}")
        print(f"  BASE_VAULT_SAMPLE: {bv_sample}")
        print(f"  QUOTE_VAULT_SAMPLE: {qv_sample}")
        
        # Deep dive into any set vault
        for label, vault_addr in [("BASE_VAULT", base_vault), ("QUOTE_VAULT", quote_vault)]:
            if vault_addr and vault_addr != ZERO:
                vc = w3.eth.contract(address=Web3.to_checksum_address(vault_addr), abi=ERC4626_ABI)
                vname = safe_call(vc, "name") or "?"
                vsym = safe_call(vc, "symbol") or "?"
                ta = safe_call(vc, "totalAssets")
                ts = safe_call(vc, "totalSupply")
                asset_addr = safe_call(vc, "asset")
                
                print(f"\n  {label} Details:")
                print(f"    Name: {vname} ({vsym})")
                print(f"    Address: {vault_addr}")
                print(f"    totalAssets: {ta}")
                print(f"    totalSupply: {ts}")
                if ta and ts and ts > 0:
                    print(f"    Exchange rate: {ta/ts:.6f}")
                if asset_addr:
                    ac = w3.eth.contract(address=Web3.to_checksum_address(asset_addr), abi=ERC20_ABI)
                    asym = safe_call(ac, "symbol") or "?"
                    adec = safe_call(ac, "decimals") or 18
                    abal = safe_call(ac, "balanceOf", Web3.to_checksum_address(vault_addr))
                    print(f"    Underlying: {asym} @ {asset_addr}")
                    if ta and adec:
                        print(f"    totalAssets in underlying: {ta / 10**adec:,.4f} {asym}")
                    if abal:
                        print(f"    underlying.balanceOf(vault): {abal / 10**adec:,.4f} {asym}")
                        if ta:
                            diff = abs(abal - ta)
                            print(f"    balanceOf vs totalAssets diff: {diff} ({diff / 10**adec:,.6f} {asym})")
                            if diff < 1000:
                                print(f"    *** DONATION-SENSITIVE (balanceOf-based totalAssets) ***")
    else:
        print(f"  Type: CUSTOM ORACLE (not MorphoChainlinkOracleV2)")
        print(f"  Price: {price}")
        # Check bytecode size
        code = w3.eth.get_code(Web3.to_checksum_address(oracle_addr))
        print(f"  Bytecode size: {len(code)} bytes")

print("\n\nDone.")
