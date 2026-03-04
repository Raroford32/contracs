#!/usr/bin/env python3
"""
Decode the full oracle chain for PT-sNUSD-5MAR2026.

Architecture discovered:
  Morpho reads: 0xe846... (45-byte EIP-1167 proxy)
    → impl 0xcc31... (6166-byte custom: TWAP+cap+heartbeat)
      → reads 0xd25a... (2598-byte, has price())
        → inner oracle, possibly ChainlinkOracleV2
      → reads 0x385a... (oracle reference)
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
        w3 = _w3
        print(f"Block: {bn}")
        break
    except:
        continue

now = w3.eth.get_block("latest")["timestamp"]
print(f"Time: {time.strftime('%Y-%m-%d %H:%M:%S UTC', time.gmtime(now))}")

def raw_call(addr, data_hex):
    try:
        return w3.eth.call({"to": Web3.to_checksum_address(addr), "data": data_hex})
    except:
        return None

def u256(data, offset=0):
    if data and len(data) >= offset + 32:
        return int.from_bytes(data[offset:offset+32], 'big')
    return None

def addr(data, offset=0):
    if data and len(data) >= offset + 32:
        return "0x" + data[offset+12:offset+32].hex()
    return None

# Standard MorphoChainlinkOracleV2 selectors
CV2 = {
    "price()": "0xa035b1fe",
    "BASE_VAULT()": "0x07f8798d",
    "QUOTE_VAULT()": "0x48bde20c",
    "BASE_FEED_1()": "0x7bfbf0d5",
    "BASE_FEED_2()": "0x2f9d31ad",
    "QUOTE_FEED_1()": "0x29f2ea6b",
    "QUOTE_FEED_2()": "0x1bf78780",
    "SCALE_FACTOR()": "0xe2e35209",
}

# Chainlink aggregator
CL = {
    "latestAnswer()": "0x50d25bcd",
    "decimals()": "0x313ce567",
    "description()": "0x7284e416",
}

ZERO = "0x" + "0" * 40

print("=" * 80)
print("LAYER 1: Inner oracle 0xd25a93... (behind PT-sNUSD TWAP adapter)")
print("=" * 80)

inner_oracle = "0xd25a93399d82e1a08d9da61d21fdff7f3e65eb27"

# Try MorphoChainlinkOracleV2 selectors
for name, sel in CV2.items():
    result = raw_call(inner_oracle, sel)
    if result:
        val = u256(result)
        a = addr(result)
        if name.endswith("VAULT()") or name.endswith("FEED_1()") or name.endswith("FEED_2()"):
            print(f"  {name}: {a}")
        elif name == "price()":
            print(f"  {name}: {val} ({val/1e24:.8f} if /1e24)")
        else:
            print(f"  {name}: {val}")

# Also try the custom selectors we found
custom = {
    "0xf50a4718": "unknown_addr",
    "0xce4b5bbe": "unknown_uint",
    "0x054f7ac0": "unknown_flag1",
    "0x461739d2": "unknown_flag2",
}
for sel, label in custom.items():
    result = raw_call(inner_oracle, sel)
    if result:
        val = u256(result)
        a = addr(result)
        if val and val < 2**160 and val > 2**80:
            print(f"  {sel} ({label}): {a}")
        else:
            print(f"  {sel} ({label}): {val}")

# Investigate the address pointed to by 0xf50a4718
feed_addr = "0xe488ee19e06eb9d5fef39b076682d959db87168b"
print(f"\n{'='*80}")
print(f"LAYER 2: Feed at {feed_addr}")
print(f"{'='*80}")

code = w3.eth.get_code(Web3.to_checksum_address(feed_addr))
print(f"  Bytecode size: {len(code)} bytes")

# Try Chainlink aggregator selectors
for name, sel in CL.items():
    result = raw_call(feed_addr, sel)
    if result:
        if name == "description()":
            try:
                offset = u256(result)
                length = u256(result, offset)
                s = result[offset+32:offset+32+length].decode('utf-8', errors='replace')
                print(f"  {name}: {s}")
            except:
                print(f"  {name}: (decode error)")
        elif name == "latestAnswer()":
            val = u256(result)
            print(f"  {name}: {val}")
        else:
            val = u256(result)
            print(f"  {name}: {val}")

# Try latestRoundData
lrd_sel = "0xfeaf968c"
result = raw_call(feed_addr, lrd_sel)
if result:
    round_id = u256(result, 0)
    answer = u256(result, 32)
    started = u256(result, 64)
    updated = u256(result, 96)
    print(f"  latestRoundData():")
    print(f"    roundId: {round_id}")
    print(f"    answer: {answer}")
    print(f"    updatedAt: {updated} ({time.strftime('%Y-%m-%d %H:%M:%S UTC', time.gmtime(updated)) if updated else '?'})")
    if updated:
        staleness = now - updated
        print(f"    staleness: {staleness/60:.0f} min ({staleness/3600:.1f} hours)")

# Now check the ORACLE REF address
oracle_ref = "0x385ad6da207565bb232c0cc93602a3b785a16960"
print(f"\n{'='*80}")
print(f"ORACLE REF: {oracle_ref}")
print(f"{'='*80}")

code = w3.eth.get_code(Web3.to_checksum_address(oracle_ref))
print(f"  Bytecode size: {len(code)} bytes")

# Try various oracle selectors
for name, sel in {**CL, **CV2}.items():
    result = raw_call(oracle_ref, sel)
    if result:
        val = u256(result)
        if name in ("latestAnswer()", "price()"):
            print(f"  {name}: {val}")
        elif name == "decimals()":
            print(f"  {name}: {val}")
        elif name == "description()":
            try:
                offset = u256(result)
                length = u256(result, offset)
                s = result[offset+32:offset+32+length].decode('utf-8', errors='replace')
                print(f"  {name}: {s}")
            except:
                pass

# Try Pendle oracle selectors
pendle_sels = {
    "0xc5ab3ba6": "getPtToAssetRate(address,uint32)",  # might not match
    "0x951e700d": "getPtToSyRate(address,uint32)",
    "0x5cd2a4c3": "getOracleState(address,uint32)",
}

# Also try some known Pendle PtOracle selectors
print(f"\n  Full selector scan on oracle ref:")
selectors = set()
for i in range(len(code) - 4):
    if code[i] == 0x63:
        sel = code[i+1:i+5].hex()
        selectors.add(sel)

for sel in sorted(selectors):
    result = raw_call(oracle_ref, "0x" + sel)
    if result and len(result) >= 32:
        val = u256(result)
        if val and val > 0 and val != u256(result):
            continue
        if val and val > 0:
            if val < 2**160 and val > 2**80:
                print(f"    0x{sel} => {addr(result)}")
            elif val < 10**30:
                print(f"    0x{sel} => {val}")

# ============================================================================
# PT token analysis
# ============================================================================
pt_addr = "0x54Bf2659B5CdFd86b75920e93C0844c0364F5166"
print(f"\n{'='*80}")
print(f"PT TOKEN: {pt_addr}")
print(f"{'='*80}")

# Check PT-specific selectors
pt_sels = {
    "SY()": "0xc54a44b6",
    "YT()": "0x5b22960d",
    "expiry()": "0xd9548e53",
    "isExpired()": "0x2f13b60c",
    "factory()": "0xc45a0155",
    "symbol()": "0x95d89b41",
    "decimals()": "0x313ce567",
    "totalSupply()": "0x18160ddd",
}

for name, sel in pt_sels.items():
    result = raw_call(pt_addr, sel)
    if result:
        val = u256(result)
        a = addr(result)
        if name in ("SY()", "YT()", "factory()"):
            print(f"  {name}: {a}")
        elif name == "symbol()":
            try:
                offset = u256(result)
                length = u256(result, offset)
                s = result[offset+32:offset+32+length].decode('utf-8', errors='replace')
                print(f"  {name}: {s}")
            except:
                pass
        elif name == "expiry()":
            if val:
                exp_str = time.strftime('%Y-%m-%d %H:%M:%S UTC', time.gmtime(val))
                hours_to = (val - now) / 3600
                print(f"  {name}: {val} = {exp_str} ({hours_to:.2f} hours to maturity)")
        elif name == "isExpired()":
            print(f"  {name}: {bool(val)}")
        elif name == "totalSupply()":
            print(f"  {name}: {val} ({val/1e18:,.4f})")
        else:
            print(f"  {name}: {val}")

print("\nDone.")
