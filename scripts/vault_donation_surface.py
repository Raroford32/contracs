#!/usr/bin/env python3
"""
Check each ERC-4626 vault used as collateral in Morpho Blue (Ethereum mainnet)
for donation attack susceptibility:

1. Does the vault's totalAssets() increase when you directly transfer the underlying?
2. Does the oracle read the vault's exchange rate (BASE_VAULT)?
3. What is the vault's total supply and total assets ratio?
4. Is the vault low-liquidity (small totalSupply = easier to manipulate)?
5. Can you deposit and withdraw atomically (flash-style)?

KEY INSIGHT: If vault totalAssets = balance of underlying token,
then donating the underlying token inflates the exchange rate.
If the oracle reads this rate, collateral value is inflated.
"""

import json
import os
from web3 import Web3

ETH_RPC = os.environ.get("ETH_RPC", "https://eth.llamarpc.com")
w3 = Web3(Web3.HTTPProvider(ETH_RPC))

print(f"Connected to Ethereum. Block: {w3.eth.block_number}")

VAULT_ABI = json.loads('''[
  {"inputs":[],"name":"asset","outputs":[{"internalType":"address","name":"","type":"address"}],"stateMutability":"view","type":"function"},
  {"inputs":[],"name":"totalAssets","outputs":[{"internalType":"uint256","name":"","type":"uint256"}],"stateMutability":"view","type":"function"},
  {"inputs":[],"name":"totalSupply","outputs":[{"internalType":"uint256","name":"","type":"uint256"}],"stateMutability":"view","type":"function"},
  {"inputs":[{"internalType":"uint256","name":"shares","type":"uint256"}],
   "name":"convertToAssets","outputs":[{"internalType":"uint256","name":"","type":"uint256"}],"stateMutability":"view","type":"function"},
  {"inputs":[],"name":"symbol","outputs":[{"internalType":"string","name":"","type":"string"}],"stateMutability":"view","type":"function"},
  {"inputs":[],"name":"decimals","outputs":[{"internalType":"uint8","name":"","type":"uint8"}],"stateMutability":"view","type":"function"}
]''')

ERC20_ABI = json.loads('''[
  {"inputs":[],"name":"symbol","outputs":[{"internalType":"string","name":"","type":"string"}],"stateMutability":"view","type":"function"},
  {"inputs":[],"name":"decimals","outputs":[{"internalType":"uint8","name":"","type":"uint8"}],"stateMutability":"view","type":"function"},
  {"inputs":[{"internalType":"address","name":"","type":"address"}],"name":"balanceOf","outputs":[{"internalType":"uint256","name":"","type":"uint256"}],"stateMutability":"view","type":"function"},
  {"inputs":[],"name":"totalSupply","outputs":[{"internalType":"uint256","name":"","type":"uint256"}],"stateMutability":"view","type":"function"}
]''')

ORACLE_ABI = json.loads('''[
  {"inputs":[],"name":"BASE_VAULT","outputs":[{"internalType":"contract IERC4626","name":"","type":"address"}],"stateMutability":"view","type":"function"},
  {"inputs":[],"name":"QUOTE_VAULT","outputs":[{"internalType":"contract IERC4626","name":"","type":"address"}],"stateMutability":"view","type":"function"},
  {"inputs":[],"name":"price","outputs":[{"internalType":"uint256","name":"","type":"uint256"}],"stateMutability":"view","type":"function"},
  {"inputs":[],"name":"SCALE_FACTOR","outputs":[{"internalType":"uint256","name":"","type":"uint256"}],"stateMutability":"view","type":"function"}
]''')

ZERO = "0x0000000000000000000000000000000000000000"

def safe_call(addr, abi, func_name, *args):
    try:
        c = w3.eth.contract(address=Web3.to_checksum_address(addr), abi=abi)
        return getattr(c.functions, func_name)(*args).call()
    except:
        return None

# Top ERC-4626 vault collateral tokens from Morpho mainnet markets
VAULT_MARKETS = [
    {"sym": "sUSDS", "addr": "0xa3931d71877C0E7a3148CB7Eb4463524FEc27fbD", "oracle": "0x0C426d174FC8", "borrow_usd": 163_000_000, "loan": "USDT"},
    {"sym": "sUSDe", "addr": "0x9D39A5DE30e57443BfF2A8307A4256c8797A3497", "oracle": "0xE6212D05cB5a", "borrow_usd": 119_000_000, "loan": "PYUSD"},
    {"sym": "sdeUSD", "addr": "0x5C5b196aBE0d54485975D1Ec29617D42D9198326", "oracle": "0x65F9f6d537C2", "borrow_usd": 83_000_000, "loan": "USDC"},
    {"sym": "wsrUSD", "addr": "0xd3fD63209FA2D55B07A0f6db36C2f43900be3094", "oracle": "0x938D2eDb2042", "borrow_usd": 70_000_000, "loan": "USDC"},
    {"sym": "siUSD", "addr": "0xDBDC1Ef57537E34680B898E1FEBD3D68c7389bCB", "oracle": "0xd2cC46b9B2D7", "borrow_usd": 68_000_000, "loan": "USDC"},
    {"sym": "weETH", "addr": "0xCd5fE23C85820F7B72D0926FC9b05b43E359b7ee", "oracle": "0xbDd2F2D473E8", "borrow_usd": 43_000_000, "loan": "WETH"},
    {"sym": "syrupUSDC", "addr": "0x80ac24aA929eaF5013f6436cdA2a7ba190f5Cc0b", "oracle": "0x80032f4cb6E3", "borrow_usd": 38_000_000, "loan": "USDC"},
    {"sym": "stcUSD", "addr": "0x88887bE419578051FF9F4eb6C858A951921D8888", "oracle": "0x8E3386B2f608", "borrow_usd": 26_000_000, "loan": "USDC"},
    {"sym": "stUSDS", "addr": "0x99CD4Ec3f88A45940936F469E4bB72A2A701EEB9", "oracle": "0xba3D2Dc16707", "borrow_usd": 20_000_000, "loan": "USDC"},
    {"sym": "sUSDD", "addr": "0xC5d6A7B61d18AfA11435a889557b068BB9f29930", "oracle": "0x8c0a80C09aE8", "borrow_usd": 41_000_000, "loan": "USDT"},
    {"sym": "syrupUSDT", "addr": "0x356B8d89c1e1239Cbbb9dE4815c39A1474d5BA7D", "oracle": "0x34e50151c21c", "borrow_usd": 21_000_000, "loan": "USDT"},
    {"sym": "sNUSD", "addr": "0x08EFCC2F3e61185D0EA7F8830B3FEc9Bfa2EE313", "oracle": "0x28E82e7f25Db", "borrow_usd": 9_500_000, "loan": "USDC"},
    {"sym": "ETH+", "addr": "0xE72B141DF173b999AE7c1aDcbF60Cc9833Ce56a8", "oracle": "0x0705CDc1e56f", "borrow_usd": 9_400_000, "loan": "WETH"},
]

print(f"\n{'='*100}")
print("VAULT DONATION ATTACK SURFACE — MORPHO BLUE ETHEREUM")
print(f"{'='*100}")

for vm in VAULT_MARKETS:
    addr = vm["addr"]
    sym = vm["sym"]

    # Get vault data
    asset_addr = safe_call(addr, VAULT_ABI, "asset")
    total_assets = safe_call(addr, VAULT_ABI, "totalAssets") or 0
    total_supply = safe_call(addr, VAULT_ABI, "totalSupply") or 0
    v_decimals = safe_call(addr, VAULT_ABI, "decimals") or 18

    if not asset_addr:
        print(f"\n  {sym}: NOT ERC-4626 (no asset())")
        continue

    # Get underlying asset data
    a_sym = safe_call(asset_addr, ERC20_ABI, "symbol") or "?"
    a_dec = safe_call(asset_addr, ERC20_ABI, "decimals") or 18

    # Get actual token balance of the vault (is totalAssets == balanceOf?)
    actual_balance = safe_call(asset_addr, ERC20_ABI, "balanceOf", Web3.to_checksum_address(addr)) or 0

    # Exchange rate
    rate = total_assets / total_supply if total_supply > 0 else 0
    convert = safe_call(addr, VAULT_ABI, "convertToAssets", 10 ** v_decimals)
    convert_rate = convert / (10 ** a_dec) if convert else 0

    # DONATION CHECK: Does totalAssets == balanceOf(vault)?
    # If yes, donating tokens to the vault increases totalAssets
    delta = abs(total_assets - actual_balance) if actual_balance > 0 else 0
    donation_vulnerable = (delta < total_assets * 0.01) if total_assets > 0 else False

    ta_human = total_assets / (10**a_dec) if a_dec else 0
    ts_human = total_supply / (10**v_decimals) if v_decimals else 0
    bal_human = actual_balance / (10**a_dec) if a_dec else 0

    flags = []
    if donation_vulnerable:
        flags.append("DONATION_VULNERABLE(totalAssets~=balanceOf)")
    if total_supply < 10 ** (v_decimals + 6):
        flags.append("LOW_SUPPLY")
    if rate > 2:
        flags.append(f"HIGH_RATE({rate:.4f})")

    flag_str = " | ".join(flags) if flags else "internal-tracking"

    print(f"\n  {sym} (asset: {a_sym}) — Borrow: ${vm['borrow_usd']/1e6:.0f}M in {vm['loan']}")
    print(f"    Total Assets: {ta_human:,.4f} {a_sym}")
    print(f"    Total Supply: {ts_human:,.4f} {sym}")
    print(f"    Actual Balance: {bal_human:,.4f} {a_sym}")
    print(f"    Rate (TA/TS): {rate:.8f}")
    print(f"    convertToAssets(1 share): {convert_rate:.8f}")
    print(f"    TA vs Balance delta: {delta / (10**a_dec) if a_dec else 0:,.4f}")
    print(f"    Flags: [{flag_str}]")

    if donation_vulnerable:
        # Calculate: how much would it cost to inflate the rate by X%
        # To inflate by 10%: need to donate 10% of totalAssets
        cost_10pct = total_assets * 0.10 / (10**a_dec)
        print(f"    >>> DONATABLE: totalAssets tracks balance directly")
        print(f"    >>> Cost to inflate rate 10%: {cost_10pct:,.0f} {a_sym}")
        print(f"    >>> With flash loan: inflate -> borrow against inflated collateral -> repay flash loan")
        print(f"    >>> Market borrow capacity: ${vm['borrow_usd']:,.0f}")
    else:
        print(f"    >>> Internal balance tracking detected (totalAssets != balanceOf)")
        print(f"    >>> Donation attack likely NOT feasible")

print(f"\n\n{'='*100}")
print("SUMMARY")
print(f"{'='*100}")

print("\nDone.")
