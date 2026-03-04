#!/usr/bin/env python3
"""
Raw probe of Pendle V2 market contracts using known selectors.
The ABI-based calls failed, so we go selector-by-selector.
"""

import os
import time
from web3 import Web3

RPCS = [
    os.environ.get("ETH_RPC", ""),
    "https://ethereum-rpc.publicnode.com",
    "https://1rpc.io/eth",
]
RPCS = [r for r in RPCS if r]

w3 = None
for rpc in RPCS:
    try:
        _w3 = Web3(Web3.HTTPProvider(rpc, request_kwargs={"timeout": 15}))
        bn = _w3.eth.block_number
        print(f"Connected: {rpc[:40]}... Block: {bn}")
        w3 = _w3
        break
    except:
        continue

now = w3.eth.get_block("latest")["timestamp"]
print(f"Time: {time.strftime('%Y-%m-%d %H:%M:%S UTC', time.gmtime(now))}")

def raw_call(addr, data_hex):
    try:
        result = w3.eth.call({"to": Web3.to_checksum_address(addr), "data": data_hex})
        return result
    except Exception as e:
        return None

def decode_uint(data, offset=0):
    if data and len(data) >= offset + 32:
        return int.from_bytes(data[offset:offset+32], 'big')
    return None

def decode_addr(data, offset=0):
    if data and len(data) >= offset + 32:
        return "0x" + data[offset+12:offset+32].hex()
    return None

# Known Pendle V2 market selectors
MARKET_SELECTORS = {
    "readTokens()": "0xd3637567",
    "expiry()": "0xd9548e53",
    "isExpired()": "0x2f13b60c",
    "totalSupply()": "0x18160ddd",
    "factory()": "0xc45a0155",
    "symbol()": "0x95d89b41",
    "totalActiveSupply()": "0x28d1e6c0",
    "readState(address)": None,  # needs param
    # State reading
    "getReserves()": "0x0902f1ac",
    "observations(uint256)": None,  # needs param
    "observe(uint32[])": None,  # needs param
}

# Also try known Pendle PtYt selectors
PT_SELECTORS = {
    "SY()": "0xc54a44b6",
    "YT()": "0x5b22960d",
    "factory()": "0xc45a0155",
    "expiry()": "0xd9548e53",
    "isExpired()": "0x2f13b60c",
    "symbol()": "0x95d89b41",
    "decimals()": "0x313ce567",
    "totalSupply()": "0x18160ddd",
}

MARKETS = [
    ("PT-sNUSD-5MAR2026 Market", "0xd25a93399d82e1a08d9da61d21fdff7f3e65eb27"),
    ("PT-srUSDe-2APR2026 Market", "0x527c71f87ed3b65e14476f45db57bfbce56343b6"),
]

PT_ADDRS = [
    ("PT-sNUSD-5MAR2026", "0x54Bf2659B5CdFd86b75920e93C0844c0364F5166"),
]

for label, addr in MARKETS:
    print(f"\n{'='*80}")
    print(f"  {label}: {addr}")
    print(f"{'='*80}")

    # First check if it's a contract
    code = w3.eth.get_code(Web3.to_checksum_address(addr))
    print(f"  Bytecode size: {len(code)} bytes")

    if len(code) < 10:
        print(f"  >>> NOT A CONTRACT or EOA")
        continue

    for name, sel in MARKET_SELECTORS.items():
        if sel is None:
            continue
        result = raw_call(addr, sel)
        if result and len(result) > 0:
            if name == "readTokens()":
                sy = decode_addr(result, 0)
                pt = decode_addr(result, 32)
                yt = decode_addr(result, 64)
                print(f"  {name}: SY={sy}, PT={pt}, YT={yt}")
            elif name in ("symbol()",):
                # Dynamic string
                try:
                    offset = decode_uint(result, 0)
                    length = decode_uint(result, offset)
                    s = result[offset+32:offset+32+length].decode('utf-8', errors='replace')
                    print(f"  {name}: {s}")
                except:
                    print(f"  {name}: (decode error) 0x{result[:64].hex()}")
            elif name in ("isExpired()",):
                val = decode_uint(result)
                print(f"  {name}: {bool(val)}")
            elif name == "getReserves()":
                r0 = decode_uint(result, 0)
                r1 = decode_uint(result, 32)
                print(f"  {name}: reserve0={r0}, reserve1={r1}")
                if r0 and r1:
                    print(f"    reserve0: {r0/1e18:,.4f}")
                    print(f"    reserve1: {r1/1e18:,.4f}")
            else:
                val = decode_uint(result)
                if val is not None:
                    if name == "expiry()":
                        exp_str = time.strftime('%Y-%m-%d %H:%M:%S UTC', time.gmtime(val))
                        days_to = (val - now) / 86400
                        print(f"  {name}: {val} = {exp_str} ({days_to:.4f} days)")
                    elif name == "totalSupply()" or name == "totalActiveSupply()":
                        print(f"  {name}: {val} ({val/1e18:,.4f})")
                    else:
                        print(f"  {name}: {val}")
        else:
            print(f"  {name}: None")

    # Also do a full bytecode selector scan on the market
    print(f"\n  All responding selectors (PUSH4 scan):")
    selectors = set()
    for i in range(len(code) - 4):
        if code[i] == 0x63:
            sel = code[i+1:i+5].hex()
            selectors.add(sel)

    responding = []
    for sel in sorted(selectors):
        result = raw_call(addr, "0x" + sel)
        if result and len(result) >= 32:
            val = decode_uint(result)
            if val and val > 0:
                responding.append((sel, val, result))

    for sel, val, result in responding[:30]:
        if val < 2**160 and val > 2**80:
            addr_hex = "0x" + hex(val)[2:].zfill(40)
            print(f"    0x{sel} => {addr_hex}")
        elif val < 10**30:
            print(f"    0x{sel} => {val}")
        else:
            print(f"    0x{sel} => {val} ({val/1e18:.4f} if /1e18)")

# Also probe the PT token directly
for label, addr in PT_ADDRS:
    print(f"\n{'='*80}")
    print(f"  {label}: {addr}")
    print(f"{'='*80}")

    code = w3.eth.get_code(Web3.to_checksum_address(addr))
    print(f"  Bytecode size: {len(code)} bytes")

    for name, sel in PT_SELECTORS.items():
        result = raw_call(addr, sel)
        if result and len(result) > 0:
            if name in ("symbol()",):
                try:
                    offset = decode_uint(result, 0)
                    length = decode_uint(result, offset)
                    s = result[offset+32:offset+32+length].decode('utf-8', errors='replace')
                    print(f"  {name}: {s}")
                except:
                    print(f"  {name}: 0x{result[:64].hex()}")
            elif name in ("isExpired()",):
                val = decode_uint(result)
                print(f"  {name}: {bool(val)}")
            elif name in ("SY()", "YT()", "factory()"):
                val = decode_addr(result)
                print(f"  {name}: {val}")
            else:
                val = decode_uint(result)
                if name == "expiry()":
                    exp_str = time.strftime('%Y-%m-%d %H:%M:%S UTC', time.gmtime(val))
                    days_to = (val - now) / 86400
                    hours_to = (val - now) / 3600
                    print(f"  {name}: {val} = {exp_str} ({days_to:.4f} days, {hours_to:.2f} hours)")
                else:
                    print(f"  {name}: {val}")
        else:
            print(f"  {name}: None")

print("\nDone.")
