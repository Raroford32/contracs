#!/usr/bin/env python3
"""Find the exact Morpho Blue market for PT-srNUSD."""

import os
from web3 import Web3
from eth_abi import encode

RPCS = [
    os.environ.get("ETH_RPC", ""),
    "https://ethereum-rpc.publicnode.com",
    "https://1rpc.io/eth",
    "https://eth.llamarpc.com",
]
RPCS = [r for r in RPCS if r]

w3 = None
for rpc in RPCS:
    try:
        _w3 = Web3(Web3.HTTPProvider(rpc, request_kwargs={"timeout": 15}))
        bn = _w3.eth.block_number
        w3 = _w3
        print(f"Block: {bn}")
        break
    except:
        continue

def raw_call(addr, data_hex):
    try:
        return w3.eth.call({"to": Web3.to_checksum_address(addr), "data": data_hex})
    except Exception as e:
        return f"REVERT: {str(e)[:120]}"

def u256(data, offset=0):
    if not data or isinstance(data, str) or len(data) < offset + 32: return None
    return int.from_bytes(data[offset:offset+32], 'big')

def addr_from(data, offset=0):
    if not data or isinstance(data, str) or len(data) < offset + 32: return None
    return "0x" + data[offset+12:offset+32].hex()

MORPHO = "0xBBBBBbbBBb9cC5e90e3b3Af64bdAF62C37EEFFCb"
PT_SRNUSD = "0x82b853DB31F025858792d8fA969f2a1Dc245C179"
META_ORACLE = "0x0D07087b26b28995a66050f5bb7197D439221DE3"

# Known Morpho IRMs
IRMS = [
    "0x870aC11D48B15DB9a138Cf899d20F13F79Ba00BC",  # AdaptiveCurveIrm
    "0x46415998764C29aB2a25CbeA6254146D50D22687",  # Another IRM
]

# Loan tokens to try
LOAN_TOKENS = [
    ("USDC", "0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48"),
    ("USDT", "0xdAC17F958D2ee523a2206206994597C13D831ec7"),
    ("DAI", "0x6B175474E89094C44Da98b954EedeAC495271d0F"),
    ("USDS", "0xdC035D45d973E3EC169d2276DDab16f1e407384F"),
]

# LLTV values to try
LLTVS = [
    915000000000000000,   # 91.5%
    860000000000000000,   # 86%
    770000000000000000,   # 77%
    945000000000000000,   # 94.5%
    900000000000000000,   # 90%
    980000000000000000,   # 98%
]

# Also try different MetaOracle addresses
ORACLES = [
    META_ORACLE,
    "0x2b28bf17c7bb004dbbf002b2482da267dbe06c60",  # Primary oracle directly
]

found = False
for loan_name, loan_token in LOAN_TOKENS:
    for irm in IRMS:
        for oracle in ORACLES:
            for lltv in LLTVS:
                market_params = encode(
                    ['address', 'address', 'address', 'address', 'uint256'],
                    [
                        Web3.to_checksum_address(loan_token),
                        Web3.to_checksum_address(PT_SRNUSD),
                        Web3.to_checksum_address(oracle),
                        Web3.to_checksum_address(irm),
                        lltv
                    ]
                )
                market_id = Web3.keccak(market_params)
                data = "0x44de2e1c" + market_id.hex()
                result = raw_call(MORPHO, data)
                if isinstance(result, bytes) and len(result) >= 160:
                    total_supply = u256(result, 0)
                    if total_supply and total_supply > 0:
                        total_borrow = u256(result, 64)
                        available = total_supply - total_borrow
                        print(f"\nFOUND MARKET!")
                        print(f"  ID: 0x{market_id.hex()}")
                        print(f"  Loan: {loan_name} ({loan_token})")
                        print(f"  Collateral: PT-srNUSD ({PT_SRNUSD})")
                        print(f"  Oracle: {oracle}")
                        print(f"  IRM: {irm}")
                        print(f"  LLTV: {lltv/1e18*100:.1f}%")
                        dec = 6 if loan_name in ["USDC", "USDT"] else 18
                        print(f"  Supply: {total_supply/10**dec:,.2f} {loan_name}")
                        print(f"  Borrow: {total_borrow/10**dec:,.2f} {loan_name}")
                        print(f"  Available: {available/10**dec:,.2f} {loan_name}")
                        found = True

if not found:
    print("Market not found with standard params. Trying idToMarketParams...")
    # Alternative: scan recent events or use a known market ID
    # Let's try to find the market by looking at position data

    # Check if PT-srNUSD has approved Morpho
    allowance = u256(raw_call(PT_SRNUSD, "0xdd62ed3e" +
        "0000000000000000000000000000000000000000000000000000000000000000" +
        MORPHO.lower().replace("0x", "").zfill(64)))
    print(f"  PT-srNUSD allowance to Morpho: {allowance}")

    # Check balance of PT in Morpho (already found: 1,296,509 tokens)
    bal = u256(raw_call(PT_SRNUSD, "0x70a08231" + MORPHO.lower().replace("0x", "").zfill(64)))
    print(f"  PT-srNUSD balance in Morpho: {bal/1e18:,.2f}")

    # Try to find the market via the Morpho API
    # Actually, let's try with USDS as loan token (Morpho has many USDS markets)
    USDS = "0xdC035D45d973E3EC169d2276DDab16f1e407384F"
    for irm in IRMS:
        for oracle in ORACLES:
            for lltv in LLTVS:
                market_params = encode(
                    ['address', 'address', 'address', 'address', 'uint256'],
                    [
                        Web3.to_checksum_address(USDS),
                        Web3.to_checksum_address(PT_SRNUSD),
                        Web3.to_checksum_address(oracle),
                        Web3.to_checksum_address(irm),
                        lltv
                    ]
                )
                market_id = Web3.keccak(market_params)
                data = "0x44de2e1c" + market_id.hex()
                result = raw_call(MORPHO, data)
                if isinstance(result, bytes) and len(result) >= 160:
                    total_supply = u256(result, 0)
                    if total_supply and total_supply > 0:
                        total_borrow = u256(result, 64)
                        print(f"\nFOUND MARKET (USDS)!")
                        print(f"  ID: 0x{market_id.hex()}")
                        print(f"  Oracle: {oracle}")
                        print(f"  IRM: {irm}")
                        print(f"  LLTV: {lltv/1e18*100:.1f}%")
                        print(f"  Supply: {total_supply/1e18:,.2f} USDS")
                        print(f"  Borrow: {total_borrow/1e18:,.2f} USDS")

print("\nDone.")
