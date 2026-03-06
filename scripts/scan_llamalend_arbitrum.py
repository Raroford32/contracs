#!/usr/bin/env python3
"""Scan LlamaLend on Arbitrum for the same donation attack vulnerability."""

from web3 import Web3
from Crypto.Hash import keccak
from eth_abi import encode, decode

# Try multiple Arbitrum RPCs
RPCS = [
    "https://arb1.arbitrum.io/rpc",
    "https://arbitrum-one.publicnode.com",
]

w3 = None
for rpc in RPCS:
    try:
        _w3 = Web3(Web3.HTTPProvider(rpc, request_kwargs={'timeout': 10}))
        if _w3.is_connected():
            w3 = _w3
            print(f"Connected to: {rpc}")
            break
    except:
        continue

if not w3:
    print("Could not connect to Arbitrum RPC")
    exit(1)

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

CONVERT_SELECTOR = sel("convertToAssets(uint256)").hex()

# Known LlamaLend factories on Arbitrum
# The same factory pattern is used across chains
FACTORIES = [
    '0xcaEC110C784c9DF37240a8Ce096D352A75922DeA',  # One-Way Lending Factory Arbitrum
    '0xeA6876DDE9e3467564acBeE1Ed5bac88783205E0',  # Try mainnet address
    '0x98EE851a00abeE0d95D08cF4CA2BdCE32aeaAF7F',  # Another possible factory
]

for factory_addr in FACTORIES:
    print(f"\n=== Checking Factory: {factory_addr} ===")

    # Check if the factory exists
    code = w3.eth.get_code(Web3.to_checksum_address(factory_addr))
    if len(code) < 10:
        print("  No code at this address")
        continue

    n_vaults = 0
    for i in range(100):
        v = read_address(factory_addr, "vaults(uint256)", i.to_bytes(32, 'big'))
        if v and v != '0x0000000000000000000000000000000000000000':
            n_vaults = i + 1
        else:
            break

    if n_vaults == 0:
        print("  No vaults found")
        continue

    print(f"  Found {n_vaults} markets")

    for i in range(n_vaults):
        vault = read_address(factory_addr, "vaults(uint256)", i.to_bytes(32, 'big'))
        if not vault or vault == '0x0000000000000000000000000000000000000000':
            continue

        controller = read_address(vault, "controller()")
        collateral_token = read_address(vault, "collateral_token()")
        borrowed_token = read_address(vault, "borrowed_token()")

        coll_symbol = read_string(collateral_token, "symbol()") if collateral_token else "?"
        borrow_symbol = read_string(borrowed_token, "symbol()") if borrowed_token else "?"

        total_assets = read_uint(vault, "totalAssets()")
        total_debt = read_uint(controller, "total_debt()") if controller else None
        n_loans = read_uint(controller, "n_loans()") if controller else None

        # Check if collateral is ERC4626
        is_vault_token = False
        coll_total_assets = read_uint(collateral_token, "totalAssets()") if collateral_token else None
        coll_asset = read_address(collateral_token, "asset()") if collateral_token else None

        if coll_total_assets is not None and coll_asset is not None:
            is_vault_token = True

        if total_assets and total_assets > 0:
            decimals = read_uint(borrowed_token, "decimals()") if borrowed_token else 18
            if decimals is None:
                decimals = 18
            tvl = total_assets / (10 ** decimals)
            debt = (total_debt / (10 ** decimals)) if total_debt else 0

            if tvl > 100 or is_vault_token:  # Only show markets with some TVL or vault tokens
                print(f"\n  Market {i}: {coll_symbol}/{borrow_symbol}")
                print(f"    Vault: {vault}")
                print(f"    TVL: ${tvl:,.2f}")
                print(f"    Debt: ${debt:,.2f}")
                print(f"    Loans: {n_loans}")

                if is_vault_token:
                    print(f"    *** VAULT TOKEN COLLATERAL ***")
                    coll_tvl = coll_total_assets / (10 ** 18) if coll_total_assets else 0
                    print(f"    Vault TVL: ${coll_tvl:,.2f}")

                    # Check oracle
                    amm = read_address(controller, "amm()") if controller else None
                    if amm:
                        oracle = read_address(amm, "price_oracle_contract()")
                        if oracle:
                            oracle_code = w3.eth.get_code(Web3.to_checksum_address(oracle)).hex()
                            has_convert = CONVERT_SELECTOR in oracle_code
                            print(f"    Oracle: {oracle}")
                            print(f"    Oracle uses convertToAssets: {has_convert}")

                            if has_convert and debt > 0:
                                # Check donation susceptibility
                                underlying_bal = read_uint(coll_asset, "balanceOf(address)",
                                                          bytes(12) + bytes.fromhex(collateral_token[2:]))
                                if underlying_bal and coll_total_assets > 0:
                                    susc = underlying_bal / coll_total_assets
                                    print(f"    Donation susceptibility: {susc:.2%}")
                                    if susc > 0.9:
                                        print(f"    >>> POTENTIALLY EXPLOITABLE <<<")
                                        print(f"    Debt: ${debt:,.0f} | Vault TVL: ${coll_tvl:,.0f}")
                                        print(f"    Ratio (debt/vault_tvl): {debt/coll_tvl:.2%}" if coll_tvl > 0 else "")
