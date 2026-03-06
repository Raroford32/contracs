#!/usr/bin/env python3
"""Scan Curve LlamaLend markets for donation attack vulnerability (sDOLA pattern).

The sDOLA exploit (March 2, 2026): attacker donated to ERC4626 vault, inflating
exchange rate, triggering liquidations in LlamaLend. Fix not yet deployed.

This script scans ALL active LlamaLend markets to find ones using vault/savings
tokens as collateral that might be vulnerable to the same attack.
"""

from web3 import Web3
from Crypto.Hash import keccak
from eth_abi import encode, decode

RPC = "https://mainnet.infura.io/v3/bfc7283659224dd6b5124ebbc2b14e2c"
w3 = Web3(Web3.HTTPProvider(RPC))

def sel(sig):
    k = keccak.new(digest_bits=256)
    k.update(sig.encode())
    return k.digest()[:4]

def eth_call(addr, sig, extra=b''):
    data = '0x' + (sel(sig) + extra).hex()
    try:
        r = w3.eth.call({'to': Web3.to_checksum_address(addr), 'data': data})
        return r
    except:
        return None

def read_uint(addr, sig, extra=b''):
    r = eth_call(addr, sig, extra)
    if r and len(r) >= 32:
        return int.from_bytes(r[:32], 'big')
    return None

def read_address(addr, sig, extra=b''):
    r = eth_call(addr, sig, extra)
    if r and len(r) >= 32:
        return '0x' + r[12:32].hex()
    return None

def read_string(addr, sig):
    r = eth_call(addr, sig)
    if r and len(r) > 64:
        try:
            offset = int.from_bytes(r[:32], 'big')
            length = int.from_bytes(r[32:64], 'big')
            return r[64:64+length].decode('utf-8', errors='replace')
        except:
            return None
    return None

print(f"Block: {w3.eth.block_number}")

# Known LlamaLend Factory addresses on Ethereum mainnet
# The OneWayLendingFactory is the main factory for LlamaLend markets
FACTORIES = [
    '0xeA6876DDE9e3467564acBeE1Ed5bac88783205E0',  # OneWayLendingFactory (main)
    '0xc67a44D958eeF0ff316C3a7C9E14FB96f6DedAA0',  # Possible second factory
]

for factory_addr in FACTORIES:
    print(f"\n=== Checking Factory: {factory_addr} ===")

    # Get market count
    n_vaults = read_uint(factory_addr, "market_count()")
    if n_vaults is None:
        # Try alternative names
        n_vaults = read_uint(factory_addr, "n_vaults()")
    if n_vaults is None:
        print(f"  Could not read market count, trying vaults_index...")
        # Try reading individual vaults
        n_vaults = 0
        for i in range(100):
            v = read_address(factory_addr, "vaults(uint256)", i.to_bytes(32, 'big'))
            if v and v != '0x0000000000000000000000000000000000000000':
                n_vaults = i + 1
            else:
                break
        if n_vaults == 0:
            print(f"  No vaults found, skipping factory")
            continue

    print(f"  Found {n_vaults} markets")

    vulnerable_markets = []

    for i in range(n_vaults):
        vault = read_address(factory_addr, "vaults(uint256)", i.to_bytes(32, 'big'))
        if not vault or vault == '0x0000000000000000000000000000000000000000':
            continue

        # Get vault details
        controller = read_address(vault, "controller()")
        collateral_token = read_address(vault, "collateral_token()")
        if not collateral_token:
            # Try alternative name
            collateral_token = read_address(vault, "collateralToken()")

        borrowed_token = read_address(vault, "borrowed_token()")
        if not borrowed_token:
            borrowed_token = read_address(vault, "borrowedToken()")

        # Get token info
        coll_symbol = read_string(collateral_token, "symbol()") if collateral_token else "?"
        borrow_symbol = read_string(borrowed_token, "symbol()") if borrowed_token else "?"

        # Get market stats
        total_assets = read_uint(vault, "totalAssets()")
        total_supply_vault = read_uint(vault, "totalSupply()")

        # Check if collateral is an ERC4626 vault or similar
        is_vault_token = False
        coll_total_assets = None
        coll_total_supply = None
        coll_asset = None
        coll_convert = None

        if collateral_token:
            coll_total_assets = read_uint(collateral_token, "totalAssets()")
            coll_total_supply = read_uint(collateral_token, "totalSupply()")
            coll_asset = read_address(collateral_token, "asset()")

            if coll_total_assets is not None and coll_asset is not None:
                is_vault_token = True
                # Check convertToAssets(1e18)
                sample = 10**18
                coll_convert = read_uint(collateral_token, "convertToAssets(uint256)",
                                        sample.to_bytes(32, 'big'))

        # Get number of loans / total debt
        total_debt = None
        n_loans = None
        if controller:
            total_debt = read_uint(controller, "total_debt()")
            n_loans = read_uint(controller, "n_loans()")

        # Print info
        if total_assets and total_assets > 0:
            asset_decimals = read_uint(borrowed_token, "decimals()") if borrowed_token else 18
            if asset_decimals is None:
                asset_decimals = 18
            tvl = total_assets / (10 ** asset_decimals)

            print(f"\n  Market {i}: {coll_symbol}/{borrow_symbol}")
            print(f"    Vault: {vault}")
            print(f"    Controller: {controller}")
            print(f"    Collateral: {collateral_token} ({coll_symbol})")
            print(f"    TVL (lent): {tvl:,.2f} {borrow_symbol}")

            if total_debt:
                debt_human = total_debt / (10 ** asset_decimals)
                print(f"    Total debt: {debt_human:,.2f} {borrow_symbol}")
            if n_loans:
                print(f"    Active loans: {n_loans}")

            if is_vault_token:
                print(f"    *** COLLATERAL IS VAULT TOKEN ***")
                print(f"    Underlying asset: {coll_asset}")
                if coll_total_assets:
                    coll_decimals = read_uint(coll_asset, "decimals()") if coll_asset else 18
                    if coll_decimals is None:
                        coll_decimals = 18
                    coll_tvl = coll_total_assets / (10 ** coll_decimals)
                    print(f"    Vault TVL: {coll_tvl:,.2f}")
                if coll_total_supply:
                    print(f"    Vault total supply: {coll_total_supply}")
                if coll_convert:
                    print(f"    convertToAssets(1e18): {coll_convert}")
                    rate = coll_convert / 1e18
                    print(f"    Exchange rate: {rate:.6f}")

                # Check if underlying is held directly in vault (donation susceptible)
                if coll_asset and coll_asset != '0x0000000000000000000000000000000000000000':
                    underlying_bal = read_uint(coll_asset, "balanceOf(address)",
                                              bytes(12) + bytes.fromhex(collateral_token[2:]))
                    if underlying_bal is not None:
                        underlying_human = underlying_bal / (10 ** (coll_decimals if 'coll_decimals' in dir() else 18))
                        print(f"    Underlying balanceOf(vault): {underlying_human:,.2f}")
                        if coll_total_assets and coll_total_assets > 0:
                            donation_susceptibility = underlying_bal / coll_total_assets
                            print(f"    Donation susceptibility: {donation_susceptibility:.2%}")

                # Record as potentially vulnerable
                if total_debt and total_debt > 0:
                    vulnerable_markets.append({
                        'index': i,
                        'vault': vault,
                        'coll_symbol': coll_symbol,
                        'borrow_symbol': borrow_symbol,
                        'coll_token': collateral_token,
                        'tvl': tvl,
                        'total_debt': total_debt / (10 ** asset_decimals) if asset_decimals else 0,
                        'n_loans': n_loans,
                        'coll_tvl': coll_tvl if 'coll_tvl' in dir() else 0,
                        'exchange_rate': coll_convert / 1e18 if coll_convert else 0,
                    })
        elif total_assets == 0:
            # Empty market, skip silently
            pass
        else:
            # Could not read totalAssets, might be different interface
            print(f"\n  Market {i}: {coll_symbol}/{borrow_symbol}")
            print(f"    Vault: {vault} (could not read totalAssets)")

    if vulnerable_markets:
        print(f"\n{'='*80}")
        print(f"POTENTIALLY VULNERABLE MARKETS (vault token as collateral + active debt):")
        print(f"{'='*80}")
        for vm in vulnerable_markets:
            print(f"\n  Market {vm['index']}: {vm['coll_symbol']}/{vm['borrow_symbol']}")
            print(f"    Active debt: {vm['total_debt']:,.2f} {vm['borrow_symbol']}")
            print(f"    Active loans: {vm['n_loans']}")
            print(f"    Collateral vault TVL: {vm['coll_tvl']:,.2f}")
            print(f"    >>> DONATION ATTACK PATTERN APPLICABLE <<<")
    else:
        print(f"\n  No markets found with vault-token collateral + active debt")
