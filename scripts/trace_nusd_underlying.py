#!/usr/bin/env python3
"""
Trace: PT-sNUSD → SY-sNUSD → sNUSD → NUSD
Find what NUSD actually is, its liquidity, and depeg risk.
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
    if not data or isinstance(data, str) or len(data) < offset + 32: return None
    return int.from_bytes(data[offset:offset+32], 'big')

def addr_from(data, offset=0):
    if not data or isinstance(data, str) or len(data) < offset + 32: return None
    return "0x" + data[offset+12:offset+32].hex()

def decode_string(data):
    if not data or isinstance(data, str) or len(data) < 64: return None
    try:
        offset = u256(data, 0)
        length = u256(data, offset)
        return data[offset+32:offset+32+length].decode('utf-8', errors='replace')
    except:
        return None

ZERO = "0x" + "0" * 40

# ============================================================================
# SY-sNUSD
# ============================================================================
SY = "0x10c5e7711eaddc1b6b64e40ef1976fc462666409"
print(f"SY-sNUSD: {SY}")
print(f"  symbol: {decode_string(raw_call(SY, '0x95d89b41'))}")

# Common SY selectors
# asset() = 0x38d52e0f
# yieldToken() = selector varies
# underlying() = 0x6f307dc3
sels = {
    "0x38d52e0f": "asset()",
    "0x6f307dc3": "underlying()",
    "0xfc0c546a": "token()",
    "0xc45a0155": "factory()",
}

for sel, name in sels.items():
    result = raw_call(SY, sel)
    if result:
        a = addr_from(result)
        if a and a != ZERO:
            sym = decode_string(raw_call(a, "0x95d89b41"))
            dec = u256(raw_call(a, "0x313ce567"))
            supply = u256(raw_call(a, "0x18160ddd"))
            print(f"  {name}: {a} ({sym}, {dec} dec, supply: {supply})")

# Full selector scan
code = w3.eth.get_code(Web3.to_checksum_address(SY))
selectors = set()
for i in range(len(code) - 4):
    if code[i] == 0x63:
        sel = code[i+1:i+5].hex()
        selectors.add(sel)

print(f"\n  All responding selectors ({len(selectors)} candidates):")
for sel in sorted(selectors):
    result = raw_call(SY, "0x" + sel)
    if not result or len(result) < 32: continue
    val = u256(result)
    if val is None or val == 0: continue
    if val < 2**160 and val > 2**80:
        a = addr_from(result)
        sym = decode_string(raw_call(a, "0x95d89b41"))
        print(f"    0x{sel} => {a} ({sym or '?'})")
    elif val < 10**30:
        print(f"    0x{sel} => {val}")

# ============================================================================
# Trace deeper: find the underlying token
# ============================================================================
print(f"\n{'='*80}")
print("TRACING UNDERLYING TOKENS")
print("=" * 80)

# Check common ERC-4626 patterns
# convertToAssets(1e18), totalAssets(), etc.
# For SY: getTokensIn(), getTokensOut()
# Also: yieldToken, underlyingAsset

# Try Pendle SY-specific: getTokensIn() returns address[]
# selector: 0x24d81cbf
tokens_in = raw_call(SY, "0x24d81cbf")
if tokens_in and len(tokens_in) > 64:
    offset = u256(tokens_in, 0)
    count = u256(tokens_in, offset)
    print(f"\n  getTokensIn(): {count} tokens")
    for i in range(min(count, 5)):
        a = addr_from(tokens_in, offset + 32 + i * 32)
        if a and a != ZERO:
            sym = decode_string(raw_call(a, "0x95d89b41"))
            dec = u256(raw_call(a, "0x313ce567"))
            supply = u256(raw_call(a, "0x18160ddd"))
            supply_str = f"{supply/10**dec:,.2f}" if supply and dec else "?"

            # Check if it's an ERC-4626 vault
            vault_asset = addr_from(raw_call(a, "0x38d52e0f"))
            if vault_asset and vault_asset != ZERO:
                va_sym = decode_string(raw_call(vault_asset, "0x95d89b41"))
                print(f"    [{i}] {a} ({sym}, {dec} dec, supply: {supply_str})")
                print(f"         → vault underlying: {vault_asset} ({va_sym})")

                # Go one more level deep
                vault_asset2 = addr_from(raw_call(vault_asset, "0x38d52e0f"))
                if vault_asset2 and vault_asset2 != ZERO:
                    va2_sym = decode_string(raw_call(vault_asset2, "0x95d89b41"))
                    print(f"           → underlying of underlying: {vault_asset2} ({va2_sym})")
            else:
                print(f"    [{i}] {a} ({sym}, {dec} dec, supply: {supply_str})")

tokens_out = raw_call(SY, "0x4e48e02e")
if tokens_out and len(tokens_out) > 64:
    offset = u256(tokens_out, 0)
    count = u256(tokens_out, offset)
    print(f"\n  getTokensOut(): {count} tokens")
    for i in range(min(count, 5)):
        a = addr_from(tokens_out, offset + 32 + i * 32)
        if a and a != ZERO:
            sym = decode_string(raw_call(a, "0x95d89b41"))
            print(f"    [{i}] {a} ({sym})")

# ============================================================================
# Check NUSD-related tokens' liquidity and market data
# ============================================================================
print(f"\n{'='*80}")
print("NUSD TOKEN INVESTIGATION")
print("=" * 80)

# Look for NUSD token by checking known stablecoin addresses
# Noble USDN? nUSD? ethena nUSD?
# Let me try common naming patterns

# The SY is named SY-sNUSD, so the yield token is sNUSD and the underlying is NUSD
# Let me check what getTokensIn returns — that should show us NUSD

# Also check for exchange rate
# exchangeRate() = 0x3ba0b9a9
er = u256(raw_call(SY, "0x3ba0b9a9"))
if er:
    print(f"\n  SY exchangeRate(): {er} ({er/1e18:.8f})")

# ============================================================================
# Check the srNUSD feed (TWAP-based, 8679 bytes) — what does it read?
# ============================================================================
print(f"\n{'='*80}")
print("srNUSD TWAP FEED ANALYSIS")
print("=" * 80)

SRNUSD_FEED = "0x281e1699558157572ffa68685339fb5ffbd25310"
code2 = w3.eth.get_code(Web3.to_checksum_address(SRNUSD_FEED))
print(f"  Address: {SRNUSD_FEED}")
print(f"  Bytecode: {len(code2)} bytes")

# Full selector scan
sels2 = set()
for i in range(len(code2) - 4):
    if code2[i] == 0x63:
        sel = code2[i+1:i+5].hex()
        sels2.add(sel)

print(f"  {len(sels2)} selectors. Responding:")
for sel in sorted(sels2):
    result = raw_call(SRNUSD_FEED, "0x" + sel)
    if not result or len(result) < 32: continue
    val = u256(result)
    if val is None or val == 0: continue
    if val < 2**160 and val > 2**80:
        a = addr_from(result)
        sym = decode_string(raw_call(a, "0x95d89b41"))
        print(f"    0x{sel} => {a} ({sym or '?'})")
    elif val > 1700000000 and val < 2000000000:
        ts = time.strftime('%Y-%m-%d %H:%M UTC', time.gmtime(val))
        days = (val - now) / 86400
        print(f"    0x{sel} => {ts} ({days:.1f} days)")
    else:
        print(f"    0x{sel} => {val}")

print("\nDone.")
