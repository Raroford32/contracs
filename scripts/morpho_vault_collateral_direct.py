#!/usr/bin/env python3
"""
Direct check of Morpho Blue markets on Ethereum mainnet for vault-as-collateral composition.
Instead of scanning events (slow), we use Morpho's API to get market IDs directly.

Key questions:
1. Which markets use ERC-4626 vault tokens as collateral?
2. Do any of those vaults' oracles read the vault's own exchange rate?
3. Are any MetaMorpho vault tokens used as collateral?
4. Is there a reflexive loop (vault lends into market where its own token is collateral)?
"""

import json
import os
import requests
from web3 import Web3

ETH_RPC = os.environ.get("ETH_RPC", "https://eth.llamarpc.com")
BASE_RPC = os.environ.get("BASE_RPC", "https://mainnet.base.org")

# Use Morpho's public GraphQL API to get market data
MORPHO_API = "https://blue-api.morpho.org/graphql"

def query_morpho_markets(chain_id=1):
    """Get all active Morpho Blue markets from the API"""
    query = """
    query {
      markets(
        where: { chainId_in: [%d], totalSupplyUsd_gte: 100000 }
        orderBy: TotalSupplyUsd
        orderDirection: Desc
        first: 200
      ) {
        items {
          uniqueKey
          loanAsset {
            address
            symbol
            decimals
          }
          collateralAsset {
            address
            symbol
            decimals
          }
          oracleAddress
          lltv
          state {
            totalSupplyUsd
            totalBorrowUsd
            supplyApy
            borrowApy
          }
        }
      }
    }
    """ % chain_id

    try:
        resp = requests.post(MORPHO_API, json={"query": query}, timeout=30)
        data = resp.json()
        return data.get("data", {}).get("markets", {}).get("items", [])
    except Exception as e:
        print(f"API error: {e}")
        return []


VAULT_ABI = json.loads('''[
  {"inputs":[],"name":"asset","outputs":[{"internalType":"address","name":"","type":"address"}],"stateMutability":"view","type":"function"},
  {"inputs":[],"name":"totalAssets","outputs":[{"internalType":"uint256","name":"","type":"uint256"}],"stateMutability":"view","type":"function"},
  {"inputs":[],"name":"totalSupply","outputs":[{"internalType":"uint256","name":"","type":"uint256"}],"stateMutability":"view","type":"function"},
  {"inputs":[],"name":"symbol","outputs":[{"internalType":"string","name":"","type":"string"}],"stateMutability":"view","type":"function"},
  {"inputs":[],"name":"curator","outputs":[{"internalType":"address","name":"","type":"address"}],"stateMutability":"view","type":"function"},
  {"inputs":[{"internalType":"uint256","name":"","type":"uint256"}],"name":"supplyQueue","outputs":[{"internalType":"Id","name":"","type":"bytes32"}],"stateMutability":"view","type":"function"},
  {"inputs":[],"name":"supplyQueueLength","outputs":[{"internalType":"uint256","name":"","type":"uint256"}],"stateMutability":"view","type":"function"}
]''')

ORACLE_ABI = json.loads('''[
  {"inputs":[],"name":"BASE_VAULT","outputs":[{"internalType":"contract IERC4626","name":"","type":"address"}],"stateMutability":"view","type":"function"},
  {"inputs":[],"name":"QUOTE_VAULT","outputs":[{"internalType":"contract IERC4626","name":"","type":"address"}],"stateMutability":"view","type":"function"},
  {"inputs":[],"name":"price","outputs":[{"internalType":"uint256","name":"","type":"uint256"}],"stateMutability":"view","type":"function"},
  {"inputs":[],"name":"BASE_FEED_1","outputs":[{"internalType":"contract AggregatorV3Interface","name":"","type":"address"}],"stateMutability":"view","type":"function"},
  {"inputs":[],"name":"SCALE_FACTOR","outputs":[{"internalType":"uint256","name":"","type":"uint256"}],"stateMutability":"view","type":"function"}
]''')

ZERO = "0x0000000000000000000000000000000000000000"

def safe_call(w3, addr, abi, func_name, *args):
    try:
        c = w3.eth.contract(address=Web3.to_checksum_address(addr), abi=abi)
        return getattr(c.functions, func_name)(*args).call()
    except:
        return None

for chain_name, chain_id, rpc in [("Ethereum", 1, ETH_RPC), ("Base", 8453, BASE_RPC)]:
    w3 = Web3(Web3.HTTPProvider(rpc))
    if not w3.is_connected():
        print(f"Cannot connect to {chain_name}")
        continue

    print(f"\n{'='*100}")
    print(f"CHAIN: {chain_name} (ID: {chain_id}) | Block: {w3.eth.block_number}")
    print(f"{'='*100}")

    markets = query_morpho_markets(chain_id)
    print(f"Markets with >$100K supply from API: {len(markets)}")

    vault_collateral = []
    metamorpho_collateral = []

    for m in markets:
        coll = m.get("collateralAsset", {})
        loan = m.get("loanAsset", {})
        oracle_addr = m.get("oracleAddress", "")
        state = m.get("state", {})
        lltv = m.get("lltv")

        coll_addr = coll.get("address", "")
        coll_sym = coll.get("symbol", "?")
        loan_sym = loan.get("symbol", "?")
        supply_usd = state.get("totalSupplyUsd", 0) or 0
        borrow_usd = state.get("totalBorrowUsd", 0) or 0

        if not coll_addr:
            continue

        # Check if collateral is ERC-4626 vault
        vault_asset = safe_call(w3, coll_addr, VAULT_ABI, "asset")
        if not vault_asset:
            continue

        # It IS a vault token!
        vault_sym = safe_call(w3, coll_addr, VAULT_ABI, "symbol") or coll_sym
        vault_asset_sym = safe_call(w3, vault_asset, VAULT_ABI, "symbol") or "?"

        # Check vault stats
        vault_ta = safe_call(w3, coll_addr, VAULT_ABI, "totalAssets") or 0
        vault_ts = safe_call(w3, coll_addr, VAULT_ABI, "totalSupply") or 1
        rate = vault_ta / vault_ts if vault_ts > 0 else 0

        # Check if MetaMorpho (has curator())
        curator = safe_call(w3, coll_addr, VAULT_ABI, "curator")
        is_metamorpho = curator is not None

        # Check oracle — does it read vault's exchange rate?
        base_vault = safe_call(w3, oracle_addr, ORACLE_ABI, "BASE_VAULT") if oracle_addr else None
        quote_vault = safe_call(w3, oracle_addr, ORACLE_ABI, "QUOTE_VAULT") if oracle_addr else None
        oracle_reads_coll = base_vault and base_vault.lower() == coll_addr.lower()

        entry = {
            "coll_sym": vault_sym,
            "coll_addr": coll_addr,
            "vault_asset": vault_asset_sym,
            "vault_asset_addr": vault_asset,
            "loan_sym": loan_sym,
            "supply_usd": supply_usd,
            "borrow_usd": borrow_usd,
            "lltv": lltv,
            "rate": rate,
            "oracle_reads_coll": oracle_reads_coll,
            "base_vault": base_vault,
            "quote_vault": quote_vault,
            "is_metamorpho": is_metamorpho,
            "curator": curator,
            "oracle_addr": oracle_addr,
            "market_key": m.get("uniqueKey", ""),
        }

        vault_collateral.append(entry)
        if is_metamorpho:
            metamorpho_collateral.append(entry)

    # ========================================================================
    # RESULTS
    # ========================================================================
    print(f"\n  VAULT TOKEN COLLATERAL MARKETS: {len(vault_collateral)}")
    print(f"  MetaMorpho vault collateral: {len(metamorpho_collateral)}")

    print(f"\n  {'='*80}")
    print(f"  ALL VAULT COLLATERAL MARKETS (sorted by supply)")
    print(f"  {'='*80}")

    for e in sorted(vault_collateral, key=lambda x: x["supply_usd"], reverse=True):
        flags = []
        if e["is_metamorpho"]:
            flags.append("METAMORPHO")
        if e["oracle_reads_coll"]:
            flags.append("ORACLE_READS_VAULT_RATE")
        if e["base_vault"] and e["base_vault"] != ZERO:
            flags.append(f"BASE_VAULT={e['base_vault'][:10]}...")
        if e["quote_vault"] and e["quote_vault"] != ZERO:
            flags.append(f"QUOTE_VAULT={e['quote_vault'][:10]}...")

        flag_str = " | ".join(flags) if flags else "clean"

        print(f"\n    {e['coll_sym']} (vault of {e['vault_asset']}) / {e['loan_sym']}")
        print(f"      Supply: ${e['supply_usd']:,.0f} | Borrow: ${e['borrow_usd']:,.0f} | LLTV: {float(e['lltv'] or 0)*100:.0f}%")
        print(f"      Vault rate: {e['rate']:.8f}")
        print(f"      Oracle: {e['oracle_addr'][:14]}...")
        print(f"      Flags: [{flag_str}]")

        if e["is_metamorpho"]:
            print(f"      >>> MetaMorpho vault used as COLLATERAL!")
            print(f"      >>> Curator: {e['curator']}")

            # REFLEXIVE CHECK: Does this vault lend into the market where it's collateral?
            sq_len = safe_call(w3, e["coll_addr"], VAULT_ABI, "supplyQueueLength") or 0
            print(f"      >>> Supply queue length: {sq_len}")
            for i in range(min(sq_len, 20)):
                queue_mid = safe_call(w3, e["coll_addr"], VAULT_ABI, "supplyQueue", i)
                if queue_mid:
                    queue_hex = "0x" + bytes(queue_mid).hex()
                    if queue_hex == e["market_key"]:
                        print(f"      >>> !!! REFLEXIVE LOOP: Vault lends into THIS market !!!")
                        print(f"      >>> The vault deposits here AND its token is collateral here")

        if e["oracle_reads_coll"]:
            print(f"      >>> Oracle directly reads vault's convertToAssets()")
            print(f"      >>> DONATION ATTACK VECTOR: donate to vault → inflate rate → borrow more")

    print()

print("\nDone.")
