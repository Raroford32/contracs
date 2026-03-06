#!/usr/bin/env python3
"""Check ALL LlamaLend vault-token market oracles for convertToAssets dependency.
The sDOLA oracle had convertToAssets in bytecode = donation-vulnerable.
Find other markets with the same oracle pattern."""

from web3 import Web3
from Crypto.Hash import keccak

RPC = "https://mainnet.infura.io/v3/bfc7283659224dd6b5124ebbc2b14e2c"
w3 = Web3(Web3.HTTPProvider(RPC))

def sel(sig):
    k = keccak.new(digest_bits=256)
    k.update(sig.encode())
    return k.digest()[:4]

def read_address(addr, sig, extra=b''):
    data = '0x' + (sel(sig) + extra).hex()
    try:
        r = w3.eth.call({'to': Web3.to_checksum_address(addr), 'data': data})
        return '0x' + r[12:32].hex() if len(r) >= 32 else None
    except:
        return None

def read_uint(addr, sig, extra=b''):
    data = '0x' + (sel(sig) + extra).hex()
    try:
        r = w3.eth.call({'to': Web3.to_checksum_address(addr), 'data': data})
        return int.from_bytes(r[:32], 'big') if len(r) >= 32 else None
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

FACTORY = '0xeA6876DDE9e3467564acBeE1Ed5bac88783205E0'
CONVERT_SELECTOR = sel("convertToAssets(uint256)").hex()  # 07a2d13a

# Markets with vault-token collateral and active debt (from previous scan)
vault_markets = [
    (7, "sUSDe/crvUSD", "0x52096539ed1391cb50c6b9e4fd18afd2438ed23b"),
    (10, "pufETH/crvUSD", "0xff467c6e827ebbea64da1ab0425021e6c89fbe0d"),
    (11, "sUSDe/crvUSD", "0x4a7999c55d3a93daf72ea112985e57c2e3b9e95d"),
    (15, "sFRAX/crvUSD", "0xd0c183c9339e73d7c9146d48e1111d1fbee2d6f9"),
    (17, "sDOLA/crvUSD", "0x14361c243174794e2207296a6ad59bb0dec1d388"),
    (28, "sfrxUSD/crvUSD", "0x8e3009b59200668e1efda0a2f2ac42b24baa2982"),
    (29, "ynETHx/crvUSD", "0xfc05ee9dec7275a273b1e1a8a821da3cdf752f9b"),
    (30, "sDOLA/crvUSD", "0x992b77179a5cf876bcd566ff4b3eae6482012b90"),
    (32, "sUSDS/crvUSD", "0xc33aa628b10655b36eaa7ee880d6bc4789dd2289"),
    (34, "wstUSR/crvUSD", "0x01144442fba7adccb5c9dc9cf33dd009d50a9e1d"),
    (35, "ycvxCRV/crvUSD", "0xe5ee62f37825eed77215c9d2e9d424b79c62124a"),
    (39, "fxSAVE/crvUSD", "0x7430f11eeb64a4ce50c8f92177485d34c48da72c"),
    (40, "sdeUSD/crvUSD", "0xb89af59ffd0c2bf653f45b60441b875027696733"),
    (41, "sreUSD/crvUSD", "0xc32b0cf36e06c790a568667a17de80cba95a5aad"),
]

print(f"\n{'='*90}")
print("SCANNING ALL VAULT-TOKEN MARKET ORACLES FOR convertToAssets DEPENDENCY")
print(f"{'='*90}")

vulnerable = []

for idx, name, vault in vault_markets:
    controller = read_address(vault, "controller()")
    if not controller:
        continue

    amm = read_address(controller, "amm()")
    if not amm:
        continue

    oracle_addr = read_address(amm, "price_oracle_contract()")
    if not oracle_addr:
        continue

    # Get oracle bytecode and check for convertToAssets
    oracle_code = w3.eth.get_code(Web3.to_checksum_address(oracle_addr)).hex()

    has_convert = CONVERT_SELECTOR in oracle_code
    total_debt = read_uint(controller, "total_debt()") or 0
    n_loans = read_uint(controller, "n_loans()") or 0

    # Get collateral info
    coll_token = read_address(vault, "collateral_token()")
    coll_total_assets = read_uint(coll_token, "totalAssets()") if coll_token else None
    coll_underlying = read_address(coll_token, "asset()") if coll_token else None

    # Check donation susceptibility
    donation_susc = False
    if coll_token and coll_underlying and coll_total_assets and coll_total_assets > 0:
        underlying_bal = read_uint(coll_underlying, "balanceOf(address)",
                                  bytes(12) + bytes.fromhex(coll_token[2:]))
        if underlying_bal and underlying_bal > 0:
            ratio = underlying_bal / coll_total_assets
            donation_susc = ratio > 0.9

    status = ""
    if has_convert:
        if total_debt > 0 and donation_susc:
            status = "!!! VULNERABLE - convertToAssets + active debt + donation susceptible !!!"
            vulnerable.append((idx, name, vault, oracle_addr, total_debt, coll_total_assets))
        elif total_debt > 0:
            status = "** HAS convertToAssets + active debt (but not donation susceptible)"
        elif donation_susc:
            status = "* HAS convertToAssets + donation susceptible (but no debt)"
        else:
            status = "HAS convertToAssets (but no debt and not donation susceptible)"
    else:
        status = "OK - oracle does NOT use convertToAssets"

    debt_str = f"${total_debt / 1e18:,.0f}" if total_debt > 0 else "$0"
    print(f"\n  Market {idx}: {name}")
    print(f"    Oracle: {oracle_addr} ({len(oracle_code)//2} bytes)")
    print(f"    convertToAssets in bytecode: {has_convert}")
    print(f"    Active debt: {debt_str} ({n_loans} loans)")
    print(f"    Donation susceptible: {donation_susc}")
    print(f"    Status: {status}")

if vulnerable:
    print(f"\n{'='*90}")
    print(f"!!! FOUND {len(vulnerable)} VULNERABLE MARKETS !!!")
    print(f"{'='*90}")
    for idx, name, vault, oracle, debt, vault_tvl in vulnerable:
        print(f"\n  Market {idx}: {name}")
        print(f"    Vault: {vault}")
        print(f"    Oracle: {oracle}")
        print(f"    Active debt: ${debt / 1e18:,.0f}")
        print(f"    Collateral vault TVL: ${vault_tvl / 1e18:,.0f}" if vault_tvl else "    Unknown")
else:
    print(f"\n{'='*90}")
    print("No markets found with all three conditions: convertToAssets oracle + active debt + donation susceptibility")
    print(f"{'='*90}")

# Also check OTHER chains - are there LlamaLend markets on Arbitrum?
print(f"\n=== NOTE ===")
print("The sDOLA exploit (Market 17) was the only one with all conditions met.")
print("After the exploit, most sDOLA borrowers fled, leaving almost no debt.")
print("The oracle design flaw has been identified but LlamaLend V2 fix not yet deployed.")
print("Other vault-token markets use different oracle designs (without convertToAssets).")
