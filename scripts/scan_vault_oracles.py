#!/usr/bin/env python3
"""Scan Morpho Blue markets for low-TVL vault-backed oracles (ResupplyFi pattern)."""

from web3 import Web3
import json, sys

RPC = "https://mainnet.infura.io/v3/bfc7283659224dd6b5124ebbc2b14e2c"
w3 = Web3(Web3.HTTPProvider(RPC))

def call(addr, sig, types=None):
    """Call a contract function by signature."""
    from Crypto.Hash import keccak
    k = keccak.new(digest_bits=256)
    k.update(sig.encode())
    selector = k.digest()[:4]
    try:
        result = w3.eth.call({'to': Web3.to_checksum_address(addr), 'data': '0x' + selector.hex()})
        if types and len(result) >= 32:
            from eth_abi import decode
            return decode(types, result)
        return result
    except Exception as e:
        return None

def call_with_arg(addr, sig, arg_uint256):
    """Call function with uint256 arg."""
    from Crypto.Hash import keccak
    k = keccak.new(digest_bits=256)
    k.update(sig.encode())
    selector = k.digest()[:4]
    data = selector + arg_uint256.to_bytes(32, 'big')
    try:
        result = w3.eth.call({'to': Web3.to_checksum_address(addr), 'data': '0x' + data.hex()})
        return int.from_bytes(result, 'big')
    except:
        return None

def call_with_addr_arg(addr, sig, addr_arg):
    """Call function with address arg."""
    from Crypto.Hash import keccak
    k = keccak.new(digest_bits=256)
    k.update(sig.encode())
    selector = k.digest()[:4]
    data = selector + bytes(12) + bytes.fromhex(addr_arg[2:])
    try:
        result = w3.eth.call({'to': Web3.to_checksum_address(addr), 'data': '0x' + data.hex()})
        return int.from_bytes(result, 'big')
    except:
        return None

print(f"Connected to block: {w3.eth.block_number}")

# Use Morpho Blue GraphQL API to get markets with vault-backed oracles
import requests

# Query for markets with significant supply that use vault-backed oracles
query = """
{
  markets(
    first: 100
    orderBy: SupplyAssetsUsd
    orderDirection: Desc
    where: { supplyAssetsUsd_gte: 100000 }
  ) {
    items {
      uniqueKey
      loanAsset { symbol address decimals }
      collateralAsset { symbol address decimals }
      oracleAddress
      lltv
      state {
        supplyAssetsUsd
        supplyAssets
        borrowAssetsUsd
        borrowAssets
        collateralUsd
      }
    }
  }
}
"""

print("\n=== Querying Morpho Blue API for markets ===")
resp = requests.post(
    "https://blue-api.morpho.org/graphql",
    json={"query": query},
    headers={"Content-Type": "application/json"}
)

if resp.status_code != 200:
    print(f"API error: {resp.status_code}")
    sys.exit(1)

data = resp.json()
markets = data.get("data", {}).get("markets", {}).get("items", [])
print(f"Found {len(markets)} markets with >$100K supply")

# Now check each market's oracle for BASE_VAULT usage
vault_markets = []
for m in markets:
    oracle = m.get("oracleAddress")
    if not oracle:
        continue

    # Check if oracle has BASE_VAULT
    result = call(oracle, "BASE_VAULT()", ['address'])
    if result is None:
        continue

    base_vault = result[0]
    if base_vault == "0x0000000000000000000000000000000000000001" or base_vault == "0x0000000000000000000000000000000000000000":
        continue

    # This oracle uses a BASE_VAULT!
    collateral = m.get("collateralAsset", {})
    loan = m.get("loanAsset", {})
    state = m.get("state", {}) or {}
    supply_usd = float(state.get("supplyAssetsUsd", 0) or 0)
    borrow_usd = float(state.get("borrowAssetsUsd", 0) or 0)
    lltv = int(m.get("lltv", 0) or 0)

    # Get vault TVL
    vault_total_assets = call(base_vault, "totalAssets()", ['uint256'])
    vault_total_supply = call(base_vault, "totalSupply()", ['uint256'])
    vault_asset = call(base_vault, "asset()", ['address'])

    if vault_total_assets is None:
        continue

    total_assets = vault_total_assets[0]
    total_supply = vault_total_supply[0] if vault_total_supply else 0
    asset_addr = vault_asset[0] if vault_asset else "unknown"

    # Get underlying balance in vault (donation susceptibility)
    underlying_balance = call_with_addr_arg(asset_addr, "balanceOf(address)", base_vault) if asset_addr != "unknown" else None

    # Get decimals
    decimals_result = call(asset_addr, "decimals()", ['uint8']) if asset_addr != "unknown" else None
    decimals = decimals_result[0] if decimals_result else 18

    # Calculate TVL in human-readable terms
    tvl = total_assets / (10 ** decimals) if decimals else total_assets

    vault_markets.append({
        'oracle': oracle,
        'base_vault': base_vault,
        'collateral': collateral.get('symbol', '?'),
        'loan': loan.get('symbol', '?'),
        'supply_usd': supply_usd,
        'borrow_usd': borrow_usd,
        'lltv': lltv / 1e18 if lltv > 1e15 else lltv,
        'vault_total_assets': total_assets,
        'vault_total_supply': total_supply,
        'vault_tvl': tvl,
        'underlying_balance': underlying_balance,
        'decimals': decimals,
        'donation_susceptible': underlying_balance is not None and total_assets > 0 and abs(underlying_balance - total_assets) < total_assets * 0.05
    })

# Sort by vault TVL (lowest first - most vulnerable)
vault_markets.sort(key=lambda x: x['vault_tvl'])

print(f"\n=== {len(vault_markets)} markets with vault-backed oracles ===\n")

for vm in vault_markets:
    flag = ""
    if vm['vault_tvl'] < 1_000_000:
        flag = " *** LOW TVL ***"
    if vm['vault_tvl'] < 10_000:
        flag = " !!!! VERY LOW TVL - POTENTIAL TARGET !!!!"

    print(f"Oracle: {vm['oracle']}")
    print(f"  Collateral: {vm['collateral']} | Loan: {vm['loan']}")
    print(f"  Market supply: ${vm['supply_usd']:,.0f} | Borrow: ${vm['borrow_usd']:,.0f}")
    print(f"  LLTV: {vm['lltv']:.2%}")
    print(f"  BASE_VAULT: {vm['base_vault']}")
    print(f"  Vault TVL: {vm['vault_tvl']:,.2f} tokens{flag}")
    if vm['underlying_balance'] is not None:
        print(f"  Underlying balance: {vm['underlying_balance'] / (10**vm['decimals']):,.2f}")
    print(f"  Donation susceptible: {vm['donation_susceptible']}")

    # If very low TVL vault with significant market supply, this is a potential target
    if vm['vault_tvl'] < 100_000 and vm['supply_usd'] > 10_000:
        print(f"  !!!!! POTENTIAL RESUPPLYFI-STYLE ATTACK !!!!!")
        print(f"  Attack economics: donate to vault -> inflate exchange rate -> borrow against inflated collateral")
        print(f"  Vault TVL: {vm['vault_tvl']:,.2f} | Market supply: ${vm['supply_usd']:,.0f}")
        # Calculate donation needed
        if vm['vault_total_assets'] > 0:
            # To double the exchange rate, need to donate = totalAssets
            donation_needed = vm['vault_total_assets'] / (10 ** vm['decimals'])
            max_borrow = vm['supply_usd'] * vm['lltv']
            print(f"  Donation to 2x rate: {donation_needed:,.2f} tokens")
            print(f"  Max borrowable: ${max_borrow:,.0f}")
            if max_borrow > donation_needed * 2:  # rough profitability check
                print(f"  $$$ POTENTIALLY PROFITABLE $$$")

    print()

# Also check for QUOTE_VAULT (inverse direction)
print("\n=== Checking QUOTE_VAULT usage ===")
for vm in vault_markets[:5]:  # Check top 5
    result = call(vm['oracle'], "QUOTE_VAULT()", ['address'])
    if result and result[0] not in ["0x0000000000000000000000000000000000000001", "0x0000000000000000000000000000000000000000"]:
        print(f"Oracle {vm['oracle']} also has QUOTE_VAULT: {result[0]}")
