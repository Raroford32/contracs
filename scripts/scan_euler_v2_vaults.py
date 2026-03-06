#!/usr/bin/env python3
"""Scan Euler V2 for markets accepting ERC4626 vault tokens as collateral.
Check if any use direct convertToAssets for pricing (donation-vulnerable)."""

from web3 import Web3
from Crypto.Hash import keccak
from eth_abi import encode, decode

RPC = "https://mainnet.infura.io/v3/bfc7283659224dd6b5124ebbc2b14e2c"
w3 = Web3(Web3.HTTPProvider(RPC))

def sel(sig):
    k = keccak.new(digest_bits=256)
    k.update(sig.encode())
    return k.digest()[:4]

def read_uint(addr, sig, extra=b''):
    data = '0x' + (sel(sig) + extra).hex()
    try:
        r = w3.eth.call({'to': Web3.to_checksum_address(addr), 'data': data})
        return int.from_bytes(r[:32], 'big') if len(r) >= 32 else None
    except:
        return None

def read_address(addr, sig, extra=b''):
    data = '0x' + (sel(sig) + extra).hex()
    try:
        r = w3.eth.call({'to': Web3.to_checksum_address(addr), 'data': data})
        return '0x' + r[12:32].hex() if len(r) >= 32 else None
    except:
        return None

def read_string(addr, sig):
    data = '0x' + sel(sig).hex()
    try:
        r = w3.eth.call({'to': Web3.to_checksum_address(addr), 'data': data})
        if len(r) > 64:
            length = int.from_bytes(r[32:64], 'big')
            return r[64:64+length].decode('utf-8', errors='replace')
    except:
        return None

print(f"Block: {w3.eth.block_number}")

# Euler V2 uses EVaultFactory / EVault system
# Each vault is an independent lending market
# The EVC (Ethereum Vault Connector) coordinates between vaults

# Known Euler V2 addresses
EULER_FACTORY = '0x29a56a1b8ab8A55D68d7140C19F1d74c5dC06F8C'  # EVault Factory (Euler V2)

# Try to enumerate vaults from the factory
print("=== EULER V2 VAULT SCAN ===")

# Euler V2 uses a Lens contract to read vault data
# Let's try direct vault enumeration
# GenericFactory has getProxyListLength() and getProxyListSlice()

proxy_count = read_uint(EULER_FACTORY, "getProxyListLength()")
print(f"Total Euler V2 vaults: {proxy_count}")

if proxy_count and proxy_count > 0:
    # Read some vaults
    checked = 0
    vault_tokens = []

    for batch_start in range(0, min(proxy_count, 200), 10):
        batch_end = min(batch_start + 10, proxy_count)
        # getProxyListSlice(uint256,uint256)
        encoded = encode(['uint256', 'uint256'], [batch_start, batch_end])
        data = '0x' + sel("getProxyListSlice(uint256,uint256)").hex() + encoded.hex()
        try:
            r = w3.eth.call({'to': Web3.to_checksum_address(EULER_FACTORY), 'data': data})
            if len(r) >= 64:
                decoded = decode(['address[]'], r)
                for vault_addr in decoded[0]:
                    vault_hex = '0x' + vault_addr.hex() if isinstance(vault_addr, bytes) else vault_addr
                    if isinstance(vault_addr, str):
                        vault_hex = vault_addr
                    else:
                        vault_hex = Web3.to_checksum_address(vault_addr)

                    # Check if this vault's underlying asset is an ERC4626 vault
                    underlying = read_address(vault_hex, "asset()")
                    if not underlying:
                        continue

                    # Check if underlying is itself a vault (has totalAssets/convertToAssets)
                    inner_total_assets = read_uint(underlying, "totalAssets()")
                    inner_asset = read_address(underlying, "asset()")

                    if inner_total_assets is not None and inner_asset is not None:
                        # This is a vault-as-collateral situation!
                        sym = read_string(underlying, "symbol()") or "?"
                        vault_sym = read_string(vault_hex, "symbol()") or "?"
                        total_assets = read_uint(vault_hex, "totalAssets()")
                        total_borrows = read_uint(vault_hex, "totalBorrows()")

                        if total_assets and total_assets > 0:
                            vault_tokens.append({
                                'euler_vault': vault_hex,
                                'underlying': underlying,
                                'underlying_sym': sym,
                                'vault_sym': vault_sym,
                                'total_assets': total_assets,
                                'total_borrows': total_borrows,
                                'inner_total_assets': inner_total_assets,
                                'inner_asset': inner_asset,
                            })

                    checked += 1
        except Exception as e:
            continue

    print(f"Checked {checked} vaults")
    print(f"Found {len(vault_tokens)} vaults with ERC4626 underlying assets")

    for vt in vault_tokens:
        inner_sym = read_string(vt['inner_asset'], "symbol()") or "?"
        ta = vt['total_assets'] / 1e18 if vt['total_assets'] else 0
        tb = (vt['total_borrows'] / 1e18) if vt['total_borrows'] else 0
        ita = vt['inner_total_assets'] / 1e18 if vt['inner_total_assets'] else 0

        print(f"\n  Euler Vault: {vt['euler_vault']} ({vt['vault_sym']})")
        print(f"    Underlying: {vt['underlying']} ({vt['underlying_sym']})")
        print(f"    Inner asset: {vt['inner_asset']} ({inner_sym})")
        print(f"    Total deposited: {ta:,.2f}")
        print(f"    Total borrowed: {tb:,.2f}")
        print(f"    Inner vault TVL: {ita:,.2f}")

        # Check oracle for this vault
        oracle_addr = read_address(vt['euler_vault'], "oracle()")
        if oracle_addr:
            print(f"    Oracle: {oracle_addr}")
            # Check if oracle calls convertToAssets
            oracle_code = w3.eth.get_code(Web3.to_checksum_address(oracle_addr)).hex()
            has_convert = sel("convertToAssets(uint256)").hex() in oracle_code
            print(f"    Oracle uses convertToAssets: {has_convert}")

            if has_convert and tb > 0:
                # Check donation susceptibility
                underlying_bal = read_uint(vt['inner_asset'], "balanceOf(address)",
                                          bytes(12) + bytes.fromhex(vt['underlying'][2:]))
                if underlying_bal and vt['inner_total_assets'] > 0:
                    susc = underlying_bal / vt['inner_total_assets']
                    print(f"    Donation susceptibility: {susc:.2%}")
                    if susc > 0.9:
                        print(f"    >>> POTENTIALLY VULNERABLE <<<")
else:
    print("Could not enumerate Euler V2 vaults - factory might use different interface")

# Also check Silo V2
print("\n\n=== SILO V2 CHECK ===")
# Try known Silo addresses
SILO_FACTORY = '0x4D919CEcfD4793c0218c4e2d0DB18a43f40894B4'  # Silo V2 Factory (if exists)
silo_count = read_uint(SILO_FACTORY, "getMarketCount()")
if silo_count:
    print(f"Silo markets: {silo_count}")
else:
    print("Silo V2 factory not found at expected address")

# Try another common Silo address
SILO_REPO = '0xd998C35B7900b344bbBe6555cc11576942Cf309d'
silo_count2 = read_uint(SILO_REPO, "getSiloCount()")
if silo_count2:
    print(f"Silo repositories: {silo_count2}")
