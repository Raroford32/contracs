#!/usr/bin/env python3
"""
The PT-sNUSD-5MAR2026 and PT-srUSDe-2APR2026 oracles are 45-byte contracts.
45 bytes = EIP-1167 minimal proxy (clone).
Extract the implementation address and probe it.

EIP-1167 bytecode pattern:
363d3d373d3d3d363d73<IMPL_ADDR>5af43d82803e903d91602b57fd5bf3
"""

import json
import os
import time
from web3 import Web3

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
        print(f"Connected to {rpc[:40]}... Block: {bn}")
        w3 = _w3
        break
    except Exception as e:
        print(f"Failed {rpc[:40]}...: {e}")

if not w3:
    print("No working RPC!")
    exit(1)

now = w3.eth.get_block("latest")["timestamp"]
print(f"Time: {time.strftime('%Y-%m-%d %H:%M:%S UTC', time.gmtime(now))}")

ZERO = "0x" + "0" * 40

# The 45-byte proxy oracles
PROXY_ORACLES = [
    ("PT-srUSDe-2APR2026", "0x8B417d1e0C08d8005B7Ca1d5ebbc72Ea877DB391", 12_068_119),
    ("PT-sNUSD-5MAR2026",  "0xe8465B52E106d98157d82b46cA566CB9d09482A9", 6_555_145),
    ("PT-srNUSD-28MAY2026", "0x0D07087b26b28995a66050f5bb7197D439221DE3", 1_116_632),
]

def safe_call(addr, abi, func_name, *args):
    try:
        c = w3.eth.contract(address=Web3.to_checksum_address(addr), abi=abi)
        return getattr(c.functions, func_name)(*args).call()
    except:
        return None

ERC20_ABI = json.loads('''[
  {"inputs":[],"name":"symbol","outputs":[{"type":"string"}],"stateMutability":"view","type":"function"},
  {"inputs":[],"name":"decimals","outputs":[{"type":"uint8"}],"stateMutability":"view","type":"function"}
]''')

for name, oracle_addr, borrow in PROXY_ORACLES:
    print(f"\n{'='*80}")
    print(f"  {name} | Borrow: ${borrow:,.0f}")
    print(f"  Oracle: {oracle_addr}")
    print(f"{'='*80}")

    # Get bytecode
    code = w3.eth.get_code(Web3.to_checksum_address(oracle_addr))
    print(f"  Bytecode ({len(code)} bytes): 0x{code.hex()}")

    # EIP-1167 extraction: bytes 10-30 contain the implementation address
    if len(code) == 45:
        impl_addr = "0x" + code[10:30].hex()
        print(f"  >>> EIP-1167 Minimal Proxy")
        print(f"  >>> Implementation: {impl_addr}")

        # Get implementation bytecode size
        impl_code = w3.eth.get_code(Web3.to_checksum_address(impl_addr))
        print(f"  >>> Implementation bytecode: {len(impl_code)} bytes")

        # Now probe the implementation with many selectors
        PROBES = {
            # Common oracle
            "0xa035b1fe": "price()",
            # SparkLinearDiscountOracle-like
            "0xfe10226d": "MATURITY()",
            "0x2b97bbc5": "DISCOUNT_RATE()",
            "0xd4b83992": "FEED()",
            "0xfbd0cfe4": "PT()",
            # Chainlink-like
            "0x50d25bcd": "latestAnswer()",
            "0xfeaf968c": "latestRoundData()",
            "0x313ce567": "decimals()",
            "0x7284e416": "description()",
            # Morpho oracle
            "0x07f8798d": "BASE_VAULT()",
            "0xe2e35209": "SCALE_FACTOR()",
            "0x7bfbf0d5": "BASE_FEED_1()",
            "0x2f9d31ad": "BASE_FEED_2()",
            "0x29f2ea6b": "QUOTE_FEED_1()",
            "0x1bf78780": "QUOTE_FEED_2()",
            "0x48bde20c": "QUOTE_VAULT()",
            # Pendle specific
            "0x7a51a3b6": "ORACLE()",
            "0x9d6b4a45": "TWAP_DURATION()",
            "0x48e5d9f8": "market()",
            "0x18160ddd": "totalSupply()",
            # Custom patterns
            "0x06fdde03": "name()",
            "0x95d89b41": "symbol()",
            "0xfc0c546a": "asset()",
            "0x38d52e0f": "asset()",  # ERC4626
        }

        print(f"\n  Probing implementation selectors via proxy:")
        for sel, fname in PROBES.items():
            try:
                result = w3.eth.call({
                    "to": Web3.to_checksum_address(oracle_addr),
                    "data": sel
                })
                if len(result) >= 32:
                    val = int.from_bytes(result[:32], 'big')
                    if val == 0:
                        continue
                    # Check if address
                    if val < 2**160:
                        addr_hex = "0x" + hex(val)[2:].zfill(40)
                        sym = safe_call(addr_hex, ERC20_ABI, "symbol")
                        print(f"    {fname:30s} => {addr_hex} ({sym or '?'})")
                    else:
                        print(f"    {fname:30s} => {val}")
            except:
                pass

        # Now try to enumerate ALL function selectors from the implementation bytecode
        # Look for PUSH4 opcodes (0x63) in the bytecode to find selectors
        print(f"\n  Extracting selectors from implementation bytecode:")
        selectors = set()
        for i in range(len(impl_code) - 4):
            # PUSH4 opcode
            if impl_code[i] == 0x63:
                sel = impl_code[i+1:i+5].hex()
                selectors.add(sel)

        print(f"  Found {len(selectors)} potential selectors")
        # Filter to likely function selectors (try calling each)
        for sel in sorted(selectors):
            try:
                result = w3.eth.call({
                    "to": Web3.to_checksum_address(oracle_addr),
                    "data": "0x" + sel
                })
                if len(result) >= 32:
                    val = int.from_bytes(result[:32], 'big')
                    if val == 0:
                        continue
                    if val < 2**160 and val > 2**80:  # Looks like address
                        addr_hex = "0x" + hex(val)[2:].zfill(40)
                        sym = safe_call(addr_hex, ERC20_ABI, "symbol")
                        print(f"    0x{sel} => {addr_hex} ({sym or '?'})")
                    elif val > 0:
                        print(f"    0x{sel} => {val}")
            except:
                pass

    elif len(code) < 100:
        # Might be a different proxy pattern
        print(f"  >>> Short bytecode, possibly UUPS or other proxy")
        # Try EIP-1967 storage slot for implementation
        impl_slot = "0x360894a13ba1a3210667c828492db98dca3e2076cc3735a920a3ca505d382bbc"
        try:
            storage = w3.eth.get_storage_at(Web3.to_checksum_address(oracle_addr), impl_slot)
            impl = "0x" + storage.hex()[-40:]
            if impl != ZERO:
                print(f"  >>> EIP-1967 implementation: {impl}")
        except:
            pass

print("\nDone.")
