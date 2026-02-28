#!/usr/bin/env python3
"""
Morpho Blue Market Scanner: Find markets with ERC-4626 vault tokens as collateral
where the oracle reads live exchange rates (donation-attackable).

Key target: markets using MorphoChainlinkOracleV2 with BASE_VAULT != address(0)
and low-TVL vaults as collateral.
"""

import json
import os
import sys
from web3 import Web3

RPC = os.environ.get("RPC", "https://eth-mainnet.g.alchemy.com/v2/pLXdY7rYRY10SH_UTLBGH")
w3 = Web3(Web3.HTTPProvider(RPC))

# Morpho Blue singleton
MORPHO = "0xBBBBBbbBBb9cC5e90e3b3Af64bdAF62C37EEFFCb"

# MorphoChainlinkOracleV2 Factory
ORACLE_FACTORY = "0x3A7bB36Ee3f3eE32A60e9f2b33c1e5f2E83ad766"

# Known market IDs (from research)
# sUSDe/USDC: 0x85c7f4374f3a403b36d54cc284983b2b02bbd8581ee0f3c36494447b87d9fcab
# We'll also scan for oracle creation events

# ABIs
MORPHO_ABI = json.loads('''[
  {"inputs":[{"internalType":"Id","name":"id","type":"bytes32"}],"name":"idToMarketParams","outputs":[{"components":[{"internalType":"address","name":"loanToken","type":"address"},{"internalType":"address","name":"collateralToken","type":"address"},{"internalType":"address","name":"oracle","type":"address"},{"internalType":"address","name":"irm","type":"address"},{"internalType":"uint256","name":"lltv","type":"uint256"}],"internalType":"struct MarketParams","name":"","type":"tuple"}],"stateMutability":"view","type":"function"},
  {"inputs":[{"internalType":"Id","name":"id","type":"bytes32"}],"name":"market","outputs":[{"internalType":"uint128","name":"totalSupplyAssets","type":"uint128"},{"internalType":"uint128","name":"totalSupplyShares","type":"uint128"},{"internalType":"uint128","name":"totalBorrowAssets","type":"uint128"},{"internalType":"uint128","name":"totalBorrowShares","type":"uint128"},{"internalType":"uint128","name":"lastUpdate","type":"uint128"},{"internalType":"uint128","name":"fee","type":"uint128"}],"stateMutability":"view","type":"function"}
]''')

# MorphoChainlinkOracleV2 ABI for reading vault config
ORACLE_V2_ABI = json.loads('''[
  {"inputs":[],"name":"BASE_VAULT","outputs":[{"internalType":"contract IERC4626","name":"","type":"address"}],"stateMutability":"view","type":"function"},
  {"inputs":[],"name":"BASE_VAULT_CONVERSION_SAMPLE","outputs":[{"internalType":"uint256","name":"","type":"uint256"}],"stateMutability":"view","type":"function"},
  {"inputs":[],"name":"QUOTE_VAULT","outputs":[{"internalType":"contract IERC4626","name":"","type":"address"}],"stateMutability":"view","type":"function"},
  {"inputs":[],"name":"QUOTE_VAULT_CONVERSION_SAMPLE","outputs":[{"internalType":"uint256","name":"","type":"uint256"}],"stateMutability":"view","type":"function"},
  {"inputs":[],"name":"BASE_FEED_1","outputs":[{"internalType":"contract AggregatorV3Interface","name":"","type":"address"}],"stateMutability":"view","type":"function"},
  {"inputs":[],"name":"BASE_FEED_2","outputs":[{"internalType":"contract AggregatorV3Interface","name":"","type":"address"}],"stateMutability":"view","type":"function"},
  {"inputs":[],"name":"QUOTE_FEED_1","outputs":[{"internalType":"contract AggregatorV3Interface","name":"","type":"address"}],"stateMutability":"view","type":"function"},
  {"inputs":[],"name":"QUOTE_FEED_2","outputs":[{"internalType":"contract AggregatorV3Interface","name":"","type":"address"}],"stateMutability":"view","type":"function"},
  {"inputs":[],"name":"SCALE_FACTOR","outputs":[{"internalType":"uint256","name":"","type":"uint256"}],"stateMutability":"view","type":"function"},
  {"inputs":[],"name":"price","outputs":[{"internalType":"uint256","name":"","type":"uint256"}],"stateMutability":"view","type":"function"}
]''')

# ERC4626 ABI
ERC4626_ABI = json.loads('''[
  {"inputs":[],"name":"totalAssets","outputs":[{"internalType":"uint256","name":"","type":"uint256"}],"stateMutability":"view","type":"function"},
  {"inputs":[],"name":"totalSupply","outputs":[{"internalType":"uint256","name":"","type":"uint256"}],"stateMutability":"view","type":"function"},
  {"inputs":[{"internalType":"uint256","name":"shares","type":"uint256"}],"name":"convertToAssets","outputs":[{"internalType":"uint256","name":"","type":"uint256"}],"stateMutability":"view","type":"function"},
  {"inputs":[],"name":"asset","outputs":[{"internalType":"address","name":"","type":"address"}],"stateMutability":"view","type":"function"},
  {"inputs":[],"name":"name","outputs":[{"internalType":"string","name":"","type":"string"}],"stateMutability":"view","type":"function"},
  {"inputs":[],"name":"symbol","outputs":[{"internalType":"string","name":"","type":"string"}],"stateMutability":"view","type":"function"},
  {"inputs":[],"name":"decimals","outputs":[{"internalType":"uint8","name":"","type":"uint8"}],"stateMutability":"view","type":"function"}
]''')

ERC20_ABI = json.loads('''[
  {"inputs":[],"name":"name","outputs":[{"internalType":"string","name":"","type":"string"}],"stateMutability":"view","type":"function"},
  {"inputs":[],"name":"symbol","outputs":[{"internalType":"string","name":"","type":"string"}],"stateMutability":"view","type":"function"},
  {"inputs":[],"name":"decimals","outputs":[{"internalType":"uint8","name":"","type":"uint8"}],"stateMutability":"view","type":"function"},
  {"inputs":[{"internalType":"address","name":"","type":"address"}],"name":"balanceOf","outputs":[{"internalType":"uint256","name":"","type":"uint256"}],"stateMutability":"view","type":"function"}
]''')

# Oracle factory CreateMorphoChainlinkOracleV2 event
FACTORY_ABI = json.loads('''[
  {"anonymous":false,"inputs":[{"indexed":false,"internalType":"address","name":"caller","type":"address"},{"indexed":false,"internalType":"address","name":"oracle","type":"address"}],"name":"CreateMorphoChainlinkOracleV2","type":"event"}
]''')


def safe_call(contract, func_name, *args):
    """Call a contract function safely, returning None on error."""
    try:
        return getattr(contract.functions, func_name)(*args).call()
    except Exception:
        return None


def get_token_info(addr):
    """Get token name, symbol, decimals."""
    c = w3.eth.contract(address=Web3.to_checksum_address(addr), abi=ERC20_ABI)
    name = safe_call(c, "name") or "?"
    symbol = safe_call(c, "symbol") or "?"
    decimals = safe_call(c, "decimals") or 18
    return name, symbol, decimals


def check_is_erc4626(addr):
    """Check if address implements ERC4626 (has totalAssets and asset functions)."""
    c = w3.eth.contract(address=Web3.to_checksum_address(addr), abi=ERC4626_ABI)
    ta = safe_call(c, "totalAssets")
    asset = safe_call(c, "asset")
    return ta is not None and asset is not None, ta, asset


def analyze_oracle(oracle_addr):
    """Analyze a MorphoChainlinkOracleV2 oracle for vault references."""
    c = w3.eth.contract(address=Web3.to_checksum_address(oracle_addr), abi=ORACLE_V2_ABI)

    base_vault = safe_call(c, "BASE_VAULT")
    quote_vault = safe_call(c, "QUOTE_VAULT")
    base_sample = safe_call(c, "BASE_VAULT_CONVERSION_SAMPLE")
    quote_sample = safe_call(c, "QUOTE_VAULT_CONVERSION_SAMPLE")
    base_feed1 = safe_call(c, "BASE_FEED_1")
    base_feed2 = safe_call(c, "BASE_FEED_2")
    quote_feed1 = safe_call(c, "QUOTE_FEED_1")
    quote_feed2 = safe_call(c, "QUOTE_FEED_2")

    return {
        "base_vault": base_vault,
        "quote_vault": quote_vault,
        "base_sample": base_sample,
        "quote_sample": quote_sample,
        "base_feed1": base_feed1,
        "base_feed2": base_feed2,
        "quote_feed1": quote_feed1,
        "quote_feed2": quote_feed2,
    }


def scan_oracle_factory():
    """Get all oracles created by the factory."""
    factory = w3.eth.contract(address=Web3.to_checksum_address(ORACLE_FACTORY), abi=FACTORY_ABI)

    # Scan from factory deploy block to latest
    # Factory deployed around block 19300000 (early 2024)
    latest = w3.eth.block_number
    print(f"Latest block: {latest}")

    all_oracles = []
    # Scan in chunks of 100k blocks
    start_block = 19300000
    chunk_size = 100000

    for from_block in range(start_block, latest + 1, chunk_size):
        to_block = min(from_block + chunk_size - 1, latest)
        try:
            events = factory.events.CreateMorphoChainlinkOracleV2.get_logs(
                from_block=from_block,
                to_block=to_block
            )
            for evt in events:
                all_oracles.append(evt.args.oracle)
            if events:
                print(f"  Blocks {from_block}-{to_block}: Found {len(events)} oracles")
        except Exception as e:
            print(f"  Blocks {from_block}-{to_block}: Error - {e}")
            # Try smaller chunks
            sub_chunk = 20000
            for sub_from in range(from_block, to_block + 1, sub_chunk):
                sub_to = min(sub_from + sub_chunk - 1, to_block)
                try:
                    events = factory.events.CreateMorphoChainlinkOracleV2.get_logs(
                        from_block=sub_from, to_block=sub_to
                    )
                    for evt in events:
                        all_oracles.append(evt.args.oracle)
                    if events:
                        print(f"    Sub {sub_from}-{sub_to}: Found {len(events)} oracles")
                except Exception as e2:
                    print(f"    Sub {sub_from}-{sub_to}: Error - {e2}")

    return all_oracles


def main():
    print("=" * 80)
    print("MORPHO BLUE MARKET SCANNER: ERC-4626 Vault Donation Attack Surface")
    print("=" * 80)

    if not w3.is_connected():
        print("ERROR: Cannot connect to RPC")
        sys.exit(1)

    print(f"\nConnected to chain. Block: {w3.eth.block_number}")

    # Step 1: Get all oracle addresses from factory
    print("\n[1] Scanning oracle factory for all MorphoChainlinkOracleV2 deployments...")
    oracles = scan_oracle_factory()
    print(f"\nFound {len(oracles)} total oracle deployments")

    # Step 2: Check each oracle for vault references
    print("\n[2] Checking oracles for vault references (BASE_VAULT or QUOTE_VAULT != 0x0)...")
    vault_oracles = []
    ZERO = "0x0000000000000000000000000000000000000000"

    for i, oracle_addr in enumerate(oracles):
        if i % 50 == 0:
            print(f"  Checking oracle {i+1}/{len(oracles)}...")

        info = analyze_oracle(oracle_addr)

        has_base_vault = info["base_vault"] and info["base_vault"] != ZERO
        has_quote_vault = info["quote_vault"] and info["quote_vault"] != ZERO

        if has_base_vault or has_quote_vault:
            vault_oracles.append({
                "oracle": oracle_addr,
                "info": info,
                "has_base_vault": has_base_vault,
                "has_quote_vault": has_quote_vault,
            })

    print(f"\nFound {len(vault_oracles)} oracles with vault references")

    # Step 3: Analyze each vault-referencing oracle
    print("\n[3] Analyzing vault-referencing oracles...")
    results = []

    for vo in vault_oracles:
        oracle_addr = vo["oracle"]
        info = vo["info"]

        result = {"oracle": oracle_addr, "risks": []}

        # Check BASE_VAULT (collateral side)
        if vo["has_base_vault"]:
            bv = info["base_vault"]
            is_4626, total_assets, underlying = check_is_erc4626(bv)
            if is_4626:
                name, symbol, decimals = get_token_info(bv)
                und_name, und_sym, und_dec = get_token_info(underlying) if underlying else ("?", "?", 18)

                result["base_vault_addr"] = bv
                result["base_vault_name"] = f"{name} ({symbol})"
                result["base_vault_total_assets"] = total_assets
                result["base_vault_underlying"] = f"{und_name} ({und_sym}) @ {underlying}"
                result["base_vault_is_4626"] = True

                # Check if donation-sensitive (totalAssets uses balanceOf)
                # This is the case for most vaults
                result["risks"].append("BASE_VAULT is ERC-4626 — oracle reads live convertToAssets()")

                if total_assets and total_assets < 10**24:  # Less than ~$1M at 18 decimals
                    result["risks"].append(f"LOW TVL: totalAssets = {total_assets / 10**und_dec:.2f} {und_sym}")

        # Check QUOTE_VAULT (loan side) — MORE DANGEROUS
        if vo["has_quote_vault"]:
            qv = info["quote_vault"]
            is_4626, total_assets, underlying = check_is_erc4626(qv)
            if is_4626:
                name, symbol, decimals = get_token_info(qv)
                und_name, und_sym, und_dec = get_token_info(underlying) if underlying else ("?", "?", 18)

                result["quote_vault_addr"] = qv
                result["quote_vault_name"] = f"{name} ({symbol})"
                result["quote_vault_total_assets"] = total_assets
                result["quote_vault_underlying"] = f"{und_name} ({und_sym}) @ {underlying}"
                result["quote_vault_is_4626"] = True

                result["risks"].append("QUOTE_VAULT is ERC-4626 — DANGEROUS: loan-side vault manipulation!")

                if total_assets and total_assets < 10**24:
                    result["risks"].append(f"LOW TVL QUOTE VAULT: totalAssets = {total_assets / 10**und_dec:.2f} {und_sym}")

        if result["risks"]:
            results.append(result)

    # Step 4: Print findings
    print("\n" + "=" * 80)
    print("FINDINGS: Oracles with vault-based price feeds")
    print("=" * 80)

    for r in results:
        print(f"\nOracle: {r['oracle']}")
        if "base_vault_addr" in r:
            print(f"  BASE_VAULT: {r['base_vault_name']} @ {r['base_vault_addr']}")
            print(f"    Underlying: {r['base_vault_underlying']}")
            ta = r.get('base_vault_total_assets', 0)
            if ta:
                print(f"    Total Assets: {ta} ({ta/10**18:.2f} @ 18 dec)")
        if "quote_vault_addr" in r:
            print(f"  QUOTE_VAULT: {r['quote_vault_name']} @ {r['quote_vault_addr']}")
            print(f"    Underlying: {r['quote_vault_underlying']}")
            ta = r.get('quote_vault_total_assets', 0)
            if ta:
                print(f"    Total Assets: {ta} ({ta/10**18:.2f} @ 18 dec)")
        for risk in r["risks"]:
            print(f"  [RISK] {risk}")

    # Save results
    outpath = "analysis/engagements/bridge-finality-gap/notes/morpho-oracle-scan.json"
    os.makedirs(os.path.dirname(outpath), exist_ok=True)
    with open(outpath, "w") as f:
        # Convert to serializable
        serializable = []
        for r in results:
            sr = {}
            for k, v in r.items():
                if isinstance(v, int):
                    sr[k] = str(v)
                elif isinstance(v, list):
                    sr[k] = v
                else:
                    sr[k] = str(v) if v else None
            serializable.append(sr)
        json.dump(serializable, f, indent=2)
    print(f"\nResults saved to {outpath}")

    return results


if __name__ == "__main__":
    main()
