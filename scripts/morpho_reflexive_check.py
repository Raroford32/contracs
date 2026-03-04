#!/usr/bin/env python3
"""
Morpho Reflexive Leverage Loop Discriminator

Checks: Can a MetaMorpho vault token be used as COLLATERAL in a Morpho Blue market
where the same vault LENDS INTO?

If yes → reflexive loop possible (vault token as collateral → borrow → deposit → more tokens)

Also checks: Are MetaMorpho vault tokens used as collateral ANYWHERE in Morpho Blue?
And: Does the oracle for such a market read the vault's own convertToAssets()?
"""

import json
import os
import time
from web3 import Web3

BASE_RPC = os.environ.get("BASE_RPC", "https://mainnet.base.org")
ETH_RPC = os.environ.get("ETH_RPC", "https://eth.llamarpc.com")

# Check both Base and Ethereum mainnet
for chain_name, rpc in [("Base", BASE_RPC), ("Ethereum", ETH_RPC)]:
    w3 = Web3(Web3.HTTPProvider(rpc))
    if not w3.is_connected():
        print(f"Cannot connect to {chain_name}")
        continue

    print(f"\n{'='*100}")
    print(f"CHAIN: {chain_name} | Block: {w3.eth.block_number}")
    print(f"{'='*100}")

    MORPHO = "0xBBBBBbbBBb9cC5e90e3b3Af64bdAF62C37EEFFCb"
    morpho_code = w3.eth.get_code(Web3.to_checksum_address(MORPHO))
    if len(morpho_code) < 10:
        print(f"  Morpho Blue not deployed on {chain_name}")
        continue

    MORPHO_ABI = json.loads('''[
      {"inputs":[{"internalType":"Id","name":"id","type":"bytes32"}],"name":"idToMarketParams","outputs":[{"components":[{"internalType":"address","name":"loanToken","type":"address"},{"internalType":"address","name":"collateralToken","type":"address"},{"internalType":"address","name":"oracle","type":"address"},{"internalType":"address","name":"irm","type":"address"},{"internalType":"uint256","name":"lltv","type":"uint256"}],"internalType":"struct MarketParams","name":"","type":"tuple"}],"stateMutability":"view","type":"function"},
      {"inputs":[{"internalType":"Id","name":"id","type":"bytes32"}],"name":"market","outputs":[{"internalType":"uint128","name":"totalSupplyAssets","type":"uint128"},{"internalType":"uint128","name":"totalSupplyShares","type":"uint128"},{"internalType":"uint128","name":"totalBorrowAssets","type":"uint128"},{"internalType":"uint128","name":"totalBorrowShares","type":"uint128"},{"internalType":"uint128","name":"lastUpdate","type":"uint128"},{"internalType":"uint128","name":"fee","type":"uint128"}],"stateMutability":"view","type":"function"}
    ]''')

    VAULT_ABI = json.loads('''[
      {"inputs":[],"name":"asset","outputs":[{"internalType":"address","name":"","type":"address"}],"stateMutability":"view","type":"function"},
      {"inputs":[],"name":"totalAssets","outputs":[{"internalType":"uint256","name":"","type":"uint256"}],"stateMutability":"view","type":"function"},
      {"inputs":[],"name":"totalSupply","outputs":[{"internalType":"uint256","name":"","type":"uint256"}],"stateMutability":"view","type":"function"},
      {"inputs":[{"internalType":"uint256","name":"shares","type":"uint256"}],
       "name":"convertToAssets","outputs":[{"internalType":"uint256","name":"","type":"uint256"}],"stateMutability":"view","type":"function"},
      {"inputs":[],"name":"symbol","outputs":[{"internalType":"string","name":"","type":"string"}],"stateMutability":"view","type":"function"},
      {"inputs":[],"name":"curator","outputs":[{"internalType":"address","name":"","type":"address"}],"stateMutability":"view","type":"function"},
      {"inputs":[{"internalType":"uint256","name":"","type":"uint256"}],"name":"supplyQueue","outputs":[{"internalType":"Id","name":"","type":"bytes32"}],"stateMutability":"view","type":"function"},
      {"inputs":[],"name":"supplyQueueLength","outputs":[{"internalType":"uint256","name":"","type":"uint256"}],"stateMutability":"view","type":"function"}
    ]''')

    ORACLE_ABI = json.loads('''[
      {"inputs":[],"name":"BASE_VAULT","outputs":[{"internalType":"contract IERC4626","name":"","type":"address"}],"stateMutability":"view","type":"function"},
      {"inputs":[],"name":"QUOTE_VAULT","outputs":[{"internalType":"contract IERC4626","name":"","type":"address"}],"stateMutability":"view","type":"function"},
      {"inputs":[],"name":"price","outputs":[{"internalType":"uint256","name":"","type":"uint256"}],"stateMutability":"view","type":"function"}
    ]''')

    ERC20_ABI = json.loads('''[
      {"inputs":[],"name":"symbol","outputs":[{"internalType":"string","name":"","type":"string"}],"stateMutability":"view","type":"function"},
      {"inputs":[],"name":"decimals","outputs":[{"internalType":"uint8","name":"","type":"uint8"}],"stateMutability":"view","type":"function"}
    ]''')

    morpho = w3.eth.contract(address=Web3.to_checksum_address(MORPHO), abi=MORPHO_ABI)
    ZERO = "0x0000000000000000000000000000000000000000"

    def safe_call(contract, func_name, *args):
        try:
            return getattr(contract.functions, func_name)(*args).call()
        except:
            return None

    def get_sym(addr):
        if addr == ZERO: return "ETH"
        c = w3.eth.contract(address=Web3.to_checksum_address(addr), abi=ERC20_ABI)
        return safe_call(c, "symbol") or "?"

    def is_metamorpho(addr):
        """Check if an address is a MetaMorpho vault by looking for curator() function"""
        vc = w3.eth.contract(address=Web3.to_checksum_address(addr), abi=VAULT_ABI)
        curator = safe_call(vc, "curator")
        return curator is not None

    def is_erc4626(addr):
        """Check if address implements ERC-4626 (has asset() function)"""
        vc = w3.eth.contract(address=Web3.to_checksum_address(addr), abi=VAULT_ABI)
        asset = safe_call(vc, "asset")
        return asset is not None, asset

    # Scan CreateMarket events to find all markets
    CREATE_MARKET_TOPIC = "0xac4b2400f169220b0c0afdde7a0b32e775ba727ea1cb30b35f935cdaab8683ac"

    latest = w3.eth.block_number
    # Scan last 90 days (~3.9M blocks on Base, ~648K blocks on Ethereum)
    blocks_90d = 3_888_000 if chain_name == "Base" else 648_000
    start = max(latest - blocks_90d, 0)

    print(f"\n  Scanning CreateMarket events from block {start} to {latest}...")

    all_market_ids = []
    chunk = 200_000 if chain_name == "Ethereum" else 100_000
    current = start
    retries = 0

    while current < latest:
        end = min(current + chunk - 1, latest)
        try:
            logs = w3.eth.get_logs({
                "address": Web3.to_checksum_address(MORPHO),
                "topics": [CREATE_MARKET_TOPIC],
                "fromBlock": current,
                "toBlock": end,
            })
            for log in logs:
                mid = bytes(log["topics"][1])
                all_market_ids.append({"id": mid, "block": log["blockNumber"]})
            retries = 0
        except Exception as e:
            retries += 1
            if retries <= 3:
                chunk = chunk // 2
                time.sleep(2 ** retries)
                continue
            retries = 0
        current = end + 1

    print(f"  Found {len(all_market_ids)} markets")

    # ============================================================================
    # CHECK EACH MARKET: Is collateral a vault? Is it a MetaMorpho vault?
    # ============================================================================
    vault_collateral_markets = []
    metamorpho_collateral_markets = []
    reflexive_markets = []

    for entry in all_market_ids:
        mid = entry["id"]
        params = safe_call(morpho, "idToMarketParams", mid)
        if not params:
            continue

        loan_token = params[0]
        coll_token = params[1]
        oracle_addr = params[2]
        lltv = params[4]

        market_data = safe_call(morpho, "market", mid)
        if not market_data:
            continue

        supply = market_data[0]
        borrow = market_data[2]

        # Skip empty markets
        if supply == 0 and borrow == 0:
            continue

        # Check if collateral is ERC-4626
        coll_is_vault, coll_vault_asset = is_erc4626(coll_token)
        if not coll_is_vault:
            continue

        # This market uses a VAULT TOKEN as collateral
        loan_sym = get_sym(loan_token)
        coll_sym = get_sym(coll_token)
        vault_asset_sym = get_sym(coll_vault_asset) if coll_vault_asset else "?"

        loan_dec = 18
        try:
            ldc = w3.eth.contract(address=Web3.to_checksum_address(loan_token), abi=ERC20_ABI)
            loan_dec = safe_call(ldc, "decimals") or 18
        except:
            pass

        supply_h = supply / (10**loan_dec)
        borrow_h = borrow / (10**loan_dec)

        vault_collateral_markets.append({
            "id": mid,
            "loan": loan_sym,
            "coll": coll_sym,
            "coll_addr": coll_token,
            "vault_asset": vault_asset_sym,
            "vault_asset_addr": coll_vault_asset,
            "supply": supply_h,
            "borrow": borrow_h,
            "lltv": lltv,
            "oracle": oracle_addr,
        })

        # Check if collateral is specifically a MetaMorpho vault
        if is_metamorpho(coll_token):
            metamorpho_collateral_markets.append(vault_collateral_markets[-1])

            # REFLEXIVE CHECK: Does this vault lend into THIS market?
            vc = w3.eth.contract(address=Web3.to_checksum_address(coll_token), abi=VAULT_ABI)
            sq_len = safe_call(vc, "supplyQueueLength") or 0
            for i in range(min(sq_len, 20)):
                queue_mid = safe_call(vc, "supplyQueue", i)
                if queue_mid and bytes(queue_mid) == mid:
                    reflexive_markets.append(vault_collateral_markets[-1])
                    break

        # Check if oracle reads the vault's exchange rate
        oc = w3.eth.contract(address=Web3.to_checksum_address(oracle_addr), abi=ORACLE_ABI)
        base_vault = safe_call(oc, "BASE_VAULT")
        if base_vault and base_vault.lower() == coll_token.lower():
            vault_collateral_markets[-1]["oracle_reads_self"] = True

    # ============================================================================
    # RESULTS
    # ============================================================================
    print(f"\n  {'='*80}")
    print(f"  VAULT COLLATERAL MARKETS (collateral is ERC-4626): {len(vault_collateral_markets)}")
    print(f"  {'='*80}")

    for m in vault_collateral_markets:
        print(f"\n    {m['coll']} (vault of {m['vault_asset']}) / {m['loan']} | LLTV: {m['lltv']/1e18:.0%}")
        print(f"      Supply: {m['supply']:,.0f} {m['loan']} | Borrow: {m['borrow']:,.0f} {m['loan']}")
        print(f"      Oracle: {m['oracle'][:14]}...")
        if m.get("oracle_reads_self"):
            print(f"      >>> ORACLE READS COLLATERAL VAULT'S OWN convertToAssets()")

    print(f"\n  {'='*80}")
    print(f"  METAMORPHO VAULT AS COLLATERAL: {len(metamorpho_collateral_markets)}")
    print(f"  {'='*80}")

    for m in metamorpho_collateral_markets:
        print(f"\n    !!! MetaMorpho vault {m['coll']} used as collateral !!!")
        print(f"      Loan: {m['loan']} | Supply: {m['supply']:,.0f} | Borrow: {m['borrow']:,.0f}")
        print(f"      Vault asset: {m['vault_asset']}")

    print(f"\n  {'='*80}")
    print(f"  REFLEXIVE LOOPS (vault lends into market where its own token is collateral): {len(reflexive_markets)}")
    print(f"  {'='*80}")

    if reflexive_markets:
        for m in reflexive_markets:
            print(f"\n    !!! REFLEXIVE LOOP DETECTED !!!")
            print(f"      Vault: {m['coll']} (asset: {m['vault_asset']})")
            print(f"      Market: {m['loan']} against {m['coll']}")
            print(f"      Supply: {m['supply']:,.0f} | Borrow: {m['borrow']:,.0f}")
            print(f"      >>> Vault deposits into this market AND its token is collateral here")
            print(f"      >>> This creates circular leverage amplification!")
    else:
        print(f"\n    No reflexive loops found")

print("\n\nDone.")
