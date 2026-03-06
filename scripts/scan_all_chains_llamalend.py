#!/usr/bin/env python3
"""Check for recently created LlamaLend markets AND check the second factory.
Also check if there's a TwoWayLending factory with different oracle patterns."""

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
CONVERT_SELECTOR = sel("convertToAssets(uint256)").hex()

# Check second factory (TwoWayLendingFactory)
# and any other factory addresses
FACTORIES = {
    'OneWayLendingFactory': '0xeA6876DDE9e3467564acBeE1Ed5bac88783205E0',
    'TwoWayFactory_v1': '0xc67a44D958eeF0ff316C3a7C9E14FB96f6DedAA0',
    'TwoWayFactory_v2': '0x36d3A6e2E4E7F4F2C8e0e1E0D8E0E3aE2B6C0F1',  # placeholder
}

for name, factory in FACTORIES.items():
    code = w3.eth.get_code(Web3.to_checksum_address(factory))
    if len(code) < 10:
        print(f"\n{name} ({factory}): No code")
        continue

    print(f"\n=== {name} ({factory}) ===")

    # Count vaults
    n = 0
    for i in range(200):
        v = read_address(factory, "vaults(uint256)", i.to_bytes(32, 'big'))
        if v and v != '0x0000000000000000000000000000000000000000':
            n = i + 1
        else:
            break

    print(f"  Markets: {n}")

    if n == 0:
        continue

    # For each market, check key properties
    for i in range(n):
        vault = read_address(factory, "vaults(uint256)", i.to_bytes(32, 'big'))
        if not vault or vault == '0x0000000000000000000000000000000000000000':
            continue

        controller = read_address(vault, "controller()")
        collateral_token = read_address(vault, "collateral_token()")
        borrowed_token = read_address(vault, "borrowed_token()")

        if not controller or not collateral_token:
            continue

        coll_symbol = read_string(collateral_token, "symbol()") or "?"
        borrow_symbol = read_string(borrowed_token, "symbol()") or "?"

        total_assets = read_uint(vault, "totalAssets()")
        total_debt = read_uint(controller, "total_debt()") or 0
        n_loans = read_uint(controller, "n_loans()") or 0

        # Check if collateral is ERC4626
        coll_total_assets = read_uint(collateral_token, "totalAssets()")
        coll_asset = read_address(collateral_token, "asset()")
        is_vault_token = coll_total_assets is not None and coll_asset is not None

        if not is_vault_token:
            continue  # Skip non-vault tokens

        if total_assets is None:
            continue

        decimals = read_uint(borrowed_token, "decimals()") or 18
        tvl = total_assets / (10 ** decimals) if total_assets else 0
        debt = total_debt / (10 ** decimals)

        # Check oracle for convertToAssets
        amm = read_address(controller, "amm()")
        oracle = read_address(amm, "price_oracle_contract()") if amm else None

        has_convert = False
        if oracle:
            oracle_code = w3.eth.get_code(Web3.to_checksum_address(oracle)).hex()
            has_convert = CONVERT_SELECTOR in oracle_code

        # Check donation susceptibility
        donation_susc = False
        coll_tvl = coll_total_assets / 1e18 if coll_total_assets else 0
        if coll_asset and coll_total_assets and coll_total_assets > 0:
            underlying_bal = read_uint(coll_asset, "balanceOf(address)",
                                      bytes(12) + bytes.fromhex(collateral_token[2:]))
            if underlying_bal:
                donation_susc = underlying_bal / coll_total_assets > 0.9

        vuln_flag = ""
        if has_convert and debt > 100 and donation_susc:
            vuln_flag = " >>> VULNERABLE <<<"
        elif has_convert and debt > 100:
            vuln_flag = " [convertToAssets oracle, has debt]"

        print(f"\n  Market {i}: {coll_symbol}/{borrow_symbol}")
        print(f"    TVL: ${tvl:,.0f} | Debt: ${debt:,.0f} | Loans: {n_loans}")
        print(f"    Vault TVL: ${coll_tvl:,.0f} | Donation: {donation_susc}")
        print(f"    Oracle: convertToAssets={has_convert}{vuln_flag}")

# Now check Base chain
print(f"\n\n{'='*80}")
print("=== BASE CHAIN ===")
print(f"{'='*80}")

BASE_RPCS = [
    "https://mainnet.base.org",
    "https://base.publicnode.com",
]

w3_base = None
for rpc in BASE_RPCS:
    try:
        _w3 = Web3(Web3.HTTPProvider(rpc, request_kwargs={'timeout': 10}))
        if _w3.is_connected():
            w3_base = _w3
            print(f"Connected to Base: {rpc}")
            break
    except:
        continue

if w3_base:
    print(f"Base block: {w3_base.eth.block_number}")

    # Try known LlamaLend factory addresses on Base
    BASE_FACTORIES = [
        '0xeA6876DDE9e3467564acBeE1Ed5bac88783205E0',
        '0xcaEC110C784c9DF37240a8Ce096D352A75922DeA',
    ]

    for factory in BASE_FACTORIES:
        code = w3_base.eth.get_code(Web3.to_checksum_address(factory))
        if len(code) < 10:
            continue

        print(f"\nFound factory on Base: {factory}")

        n = 0
        for i in range(100):
            data = '0x' + sel("vaults(uint256)").hex() + i.to_bytes(32, 'big').hex()
            try:
                r = w3_base.eth.call({'to': Web3.to_checksum_address(factory), 'data': data})
                v = '0x' + r[12:32].hex()
                if v != '0x0000000000000000000000000000000000000000':
                    n = i + 1
                else:
                    break
            except:
                break

        print(f"  Markets: {n}")

        for i in range(n):
            data = '0x' + sel("vaults(uint256)").hex() + i.to_bytes(32, 'big').hex()
            try:
                r = w3_base.eth.call({'to': Web3.to_checksum_address(factory), 'data': data})
                vault = '0x' + r[12:32].hex()
            except:
                continue

            # Get basic info
            data2 = '0x' + sel("collateral_token()").hex()
            try:
                r2 = w3_base.eth.call({'to': Web3.to_checksum_address(vault), 'data': data2})
                coll = '0x' + r2[12:32].hex()
            except:
                continue

            data3 = '0x' + sel("symbol()").hex()
            try:
                r3 = w3_base.eth.call({'to': Web3.to_checksum_address(coll), 'data': data3})
                if len(r3) > 64:
                    sym = r3[64:64+int.from_bytes(r3[32:64], 'big')].decode('utf-8', errors='replace')
                else:
                    sym = "?"
            except:
                sym = "?"

            # Check totalAssets
            data4 = '0x' + sel("totalAssets()").hex()
            try:
                r4 = w3_base.eth.call({'to': Web3.to_checksum_address(vault), 'data': data4})
                ta = int.from_bytes(r4[:32], 'big')
            except:
                ta = 0

            # Check if collateral is ERC4626
            try:
                r5 = w3_base.eth.call({'to': Web3.to_checksum_address(coll), 'data': data4})
                coll_ta = int.from_bytes(r5[:32], 'big')
            except:
                coll_ta = None

            data6 = '0x' + sel("asset()").hex()
            try:
                r6 = w3_base.eth.call({'to': Web3.to_checksum_address(coll), 'data': data6})
                coll_asset = '0x' + r6[12:32].hex()
            except:
                coll_asset = None

            is_vault = coll_ta is not None and coll_asset is not None

            if ta > 0 or is_vault:
                print(f"\n  Market {i}: {sym}")
                print(f"    Vault: {vault}")
                print(f"    Collateral: {coll}")
                print(f"    TVL: {ta / 1e18:,.2f}")
                print(f"    Is ERC4626: {is_vault}")
                if is_vault:
                    print(f"    Vault TVL: {coll_ta / 1e18:,.2f}")
else:
    print("Could not connect to Base")
