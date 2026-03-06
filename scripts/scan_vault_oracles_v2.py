#!/usr/bin/env python3
"""Scan Morpho Blue markets for low-TVL vault-backed oracles."""

from web3 import Web3
import requests, json, sys
from Crypto.Hash import keccak

RPC = "https://mainnet.infura.io/v3/bfc7283659224dd6b5124ebbc2b14e2c"
w3 = Web3(Web3.HTTPProvider(RPC))

def selector(sig):
    k = keccak.new(digest_bits=256)
    k.update(sig.encode())
    return k.digest()[:4]

def eth_call(addr, sig, extra_data=b''):
    sel = selector(sig)
    data = '0x' + (sel + extra_data).hex()
    try:
        result = w3.eth.call({'to': Web3.to_checksum_address(addr), 'data': data})
        return result
    except:
        return None

def read_address(addr, sig):
    r = eth_call(addr, sig)
    if r and len(r) >= 32:
        return '0x' + r[12:32].hex()
    return None

def read_uint(addr, sig, extra=b''):
    r = eth_call(addr, sig, extra)
    if r and len(r) >= 32:
        return int.from_bytes(r[:32], 'big')
    return None

def read_uint_with_addr(addr, sig, target_addr):
    padded = bytes(12) + bytes.fromhex(target_addr[2:].lower())
    return read_uint(addr, sig, padded)

print(f"Block: {w3.eth.block_number}")

# Get markets from Morpho API with correct schema
query = """{
  markets(first: 200, where: {totalSupplyUsd_gte: 100000}) {
    items {
      uniqueKey
      oracleAddress
      lltv
      loanAsset { symbol address decimals }
      collateralAsset { symbol address decimals }
      state {
        supplyAssetsUsd
        borrowAssetsUsd
      }
    }
  }
}"""

resp = requests.post('https://blue-api.morpho.org/graphql',
    json={'query': query},
    headers={'Content-Type': 'application/json'})

if resp.status_code != 200:
    # Try different field names
    query2 = """{
      markets(first: 200) {
        items {
          uniqueKey
          oracleAddress
          lltv
          loanAsset { symbol address decimals }
          collateralAsset { symbol address decimals }
        }
      }
    }"""
    resp = requests.post('https://blue-api.morpho.org/graphql',
        json={'query': query2},
        headers={'Content-Type': 'application/json'})

data = resp.json()
markets = data.get('data', {}).get('markets', {}).get('items', [])
print(f"Got {len(markets)} markets")

# Check each oracle for BASE_VAULT
results = []
checked = set()
for m in markets:
    oracle = m.get('oracleAddress', '')
    if not oracle or oracle in checked:
        continue
    checked.add(oracle)

    base_vault = read_address(oracle, "BASE_VAULT()")
    if not base_vault or base_vault in ['0x0000000000000000000000000000000000000001',
                                         '0x0000000000000000000000000000000000000000']:
        continue

    # This oracle uses a vault!
    total_assets = read_uint(base_vault, "totalAssets()")
    total_supply = read_uint(base_vault, "totalSupply()")
    asset_addr = read_address(base_vault, "asset()")

    if total_assets is None or asset_addr is None:
        continue

    decimals = read_uint(asset_addr, "decimals()") or 18
    underlying_bal = read_uint_with_addr(asset_addr, "balanceOf(address)", base_vault)
    symbol = m.get('collateralAsset', {}).get('symbol', '?')
    loan_symbol = m.get('loanAsset', {}).get('symbol', '?')

    # Get market state from API
    state = m.get('state', {}) or {}
    supply_usd = float(state.get('supplyAssetsUsd', 0) or 0)
    borrow_usd = float(state.get('borrowAssetsUsd', 0) or 0)
    lltv = int(m.get('lltv', 0) or 0)

    tvl_human = total_assets / (10 ** decimals) if decimals else 0
    donation_susceptible = (underlying_bal is not None and total_assets > 0 and
                           abs(underlying_bal - total_assets) < total_assets * 5 // 100)

    results.append({
        'oracle': oracle,
        'vault': base_vault,
        'symbol': symbol,
        'loan': loan_symbol,
        'supply_usd': supply_usd,
        'borrow_usd': borrow_usd,
        'lltv': lltv,
        'total_assets': total_assets,
        'total_supply': total_supply,
        'tvl_human': tvl_human,
        'underlying_bal': underlying_bal,
        'decimals': decimals,
        'donation_susceptible': donation_susceptible,
        'market_id': m.get('uniqueKey', ''),
    })

results.sort(key=lambda x: x['tvl_human'])

print(f"\n{'='*80}")
print(f"VAULT-BACKED ORACLE MARKETS: {len(results)} found")
print(f"{'='*80}\n")

for r in results:
    tvl = r['tvl_human']
    flag = ""
    if tvl < 1000:
        flag = " !!!! EXTREMELY LOW TVL !!!!"
    elif tvl < 100_000:
        flag = " *** LOW TVL ***"
    elif tvl < 1_000_000:
        flag = " * MODERATE TVL *"

    print(f"Collateral: {r['symbol']} -> Loan: {r['loan']}")
    print(f"  Oracle: {r['oracle']}")
    print(f"  BASE_VAULT: {r['vault']}")
    print(f"  Vault TVL: {tvl:,.2f} tokens ({r['total_assets']} raw){flag}")
    if r['total_supply']:
        rate = r['total_assets'] * 10**18 // r['total_supply'] if r['total_supply'] > 0 else 0
        print(f"  Exchange rate: {rate / 1e18:.6f}")
    if r['underlying_bal'] is not None:
        print(f"  Underlying balance: {r['underlying_bal'] / (10**r['decimals']):,.2f}")
    print(f"  Donation susceptible: {r['donation_susceptible']}")
    if r['supply_usd'] > 0:
        print(f"  Market supply: ${r['supply_usd']:,.0f} | Borrow: ${r['borrow_usd']:,.0f}")
    print(f"  LLTV: {r['lltv']/1e18:.2%}" if r['lltv'] > 1e15 else f"  LLTV: {r['lltv']}")

    # Check if this is a potential ResupplyFi-style target
    if tvl < 100_000 and r['supply_usd'] > 10_000 and r['donation_susceptible']:
        lltv_pct = r['lltv'] / 1e18 if r['lltv'] > 1e15 else r['lltv']
        donation_for_2x = tvl  # donate = total_assets to double the rate
        max_borrow_value = r['supply_usd']
        print(f"  >>> POTENTIAL TARGET <<<")
        print(f"  Donation to 2x rate: {donation_for_2x:,.2f} tokens")
        print(f"  Max borrowable from market: ${max_borrow_value:,.0f}")

    print()

# Also scan for QUOTE_VAULT usage
print(f"\n{'='*80}")
print("CHECKING QUOTE_VAULT USAGE")
print(f"{'='*80}\n")
for r in results[:10]:
    qv = read_address(r['oracle'], "QUOTE_VAULT()")
    if qv and qv not in ['0x0000000000000000000000000000000000000001',
                          '0x0000000000000000000000000000000000000000']:
        qv_assets = read_uint(qv, "totalAssets()")
        qv_supply = read_uint(qv, "totalSupply()")
        if qv_assets:
            print(f"Oracle {r['oracle']}: QUOTE_VAULT {qv}")
            print(f"  Quote vault TVL: {qv_assets}")
            print(f"  Quote vault supply: {qv_supply}")
            print()
