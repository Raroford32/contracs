#!/usr/bin/env python3
"""
Identify NUSD by tracing the PT token's SY (Standardized Yield) to its underlying.
Also check if the PendleChainlinkOracle is truly deterministic (not TWAP).
"""

import os
import time
import json
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
# Trace PT → SY → underlying
# ============================================================================
PT = "0x54Bf2659B5CdFd86b75920e93C0844c0364F5166"
print(f"PT-sNUSD: {PT}")
print(f"  symbol: {decode_string(raw_call(PT, '0x95d89b41'))}")
print(f"  decimals: {u256(raw_call(PT, '0x313ce567'))}")
print(f"  totalSupply: {u256(raw_call(PT, '0x18160ddd'))}")

# Find SY via factory or PT
factory = addr_from(raw_call(PT, "0xc45a0155"))
print(f"  factory: {factory}")

# Pendle V2 PT has SY() function - try selector
# SY() = 0xc54a44b6 but this didn't work earlier
# Let me scan PT bytecode for all selectors
code = w3.eth.get_code(Web3.to_checksum_address(PT))
print(f"  bytecode: {len(code)} bytes")

selectors = set()
for i in range(len(code) - 4):
    if code[i] == 0x63:
        sel = code[i+1:i+5].hex()
        selectors.add(sel)

print(f"  {len(selectors)} selectors found. Probing:")
for sel in sorted(selectors):
    result = raw_call(PT, "0x" + sel)
    if not result or len(result) < 32:
        continue
    val = u256(result)
    if val is None or val == 0:
        continue
    if val < 2**160 and val > 2**80:
        a = addr_from(result)
        sym = decode_string(raw_call(a, "0x95d89b41"))
        code_size = len(w3.eth.get_code(Web3.to_checksum_address(a)))
        print(f"    0x{sel} => {a} ({sym or '?'}, {code_size}b)")
    elif val > 1700000000 and val < 2000000000:
        ts = time.strftime('%Y-%m-%d %H:%M UTC', time.gmtime(val))
        print(f"    0x{sel} => {val} = {ts}")
    elif val < 10**30:
        print(f"    0x{sel} => {val}")

# ============================================================================
# Check the PendleChainlinkOracle implementation
# ============================================================================
print(f"\n{'='*80}")
print("PENDLECHAINLINKORACLE BYTECODE ANALYSIS")
print("=" * 80)

FEED = "0xe488ee19e06eb9d5fef39b076682d959db87168b"
feed_code = w3.eth.get_code(Web3.to_checksum_address(FEED))
print(f"  Address: {FEED}")
print(f"  Bytecode: {len(feed_code)} bytes")

# Check if it's a proxy
if len(feed_code) == 45:
    impl = "0x" + feed_code[10:30].hex()
    print(f"  EIP-1167 proxy → impl: {impl}")
elif len(feed_code) < 100:
    print(f"  Short bytecode. Checking for proxy storage...")
    impl_slot = "0x360894a13ba1a3210667c828492db98dca3e2076cc3735a920a3ca505d382bbc"
    storage = w3.eth.get_storage_at(Web3.to_checksum_address(FEED), impl_slot)
    impl = "0x" + storage.hex()[-40:]
    if impl != ZERO:
        print(f"  EIP-1967 implementation: {impl}")

# Check for SLOAD patterns in bytecode to understand what storage it reads
# Look for common opcodes:
# 0x54 = SLOAD, 0x55 = SSTORE, 0x3B = EXTCODESIZE, 0xFA = STATICCALL
sload_count = sum(1 for b in feed_code if b == 0x54)
sstore_count = sum(1 for b in feed_code if b == 0x55)
staticcall_count = sum(1 for b in feed_code if b == 0xFA)
call_count = sum(1 for b in feed_code if b == 0xF1)
timestamp_count = sum(1 for b in feed_code if b == 0x42)  # TIMESTAMP opcode

print(f"  SLOAD count: {sload_count}")
print(f"  SSTORE count: {sstore_count}")
print(f"  STATICCALL count: {staticcall_count}")
print(f"  CALL count: {call_count}")
print(f"  TIMESTAMP opcode count: {timestamp_count}")

if sstore_count == 0 and staticcall_count == 0:
    print(f"  >>> NO external calls, NO state writes")
    print(f"  >>> This is a PURE computation from immutables + block.timestamp")
    print(f"  >>> CONFIRMED: Deterministic oracle, NOT TWAP")
elif staticcall_count > 0:
    print(f"  >>> Makes external calls — might read from Pendle AMM/oracle")
    print(f"  >>> Need deeper analysis")

if timestamp_count > 0:
    print(f"  >>> Uses TIMESTAMP opcode — confirms time-dependent computation")

# Check storage slots for any state
print(f"\n  Storage scan (first 10 slots):")
for slot in range(10):
    storage = w3.eth.get_storage_at(Web3.to_checksum_address(FEED), slot)
    val = int.from_bytes(storage, 'big')
    if val > 0:
        print(f"    slot[{slot}]: {val}")

# If no storage, confirm it's pure immutable computation
print(f"\n  All selectors with responses:")
feed_sels = set()
for i in range(len(feed_code) - 4):
    if feed_code[i] == 0x63:
        sel = feed_code[i+1:i+5].hex()
        feed_sels.add(sel)

for sel in sorted(feed_sels):
    result = raw_call(FEED, "0x" + sel)
    if result and len(result) >= 32:
        val = u256(result)
        if val is not None:
            print(f"    0x{sel} => {val}")

# ============================================================================
# Check the MetaOracle's stored implementation to understand what it reads
# ============================================================================
print(f"\n{'='*80}")
print("METAORACLE IMPLEMENTATION OPCODE ANALYSIS")
print("=" * 80)

IMPL = "0xcc319ef091bc520cf6835565826212024b2d25ec"
impl_code = w3.eth.get_code(Web3.to_checksum_address(IMPL))

sload_count = sum(1 for b in impl_code if b == 0x54)
sstore_count = sum(1 for b in impl_code if b == 0x55)
staticcall_count = sum(1 for b in impl_code if b == 0xFA)
call_count = sum(1 for b in impl_code if b == 0xF1)
timestamp_count = sum(1 for b in impl_code if b == 0x42)

print(f"  Implementation: {IMPL}")
print(f"  Bytecode: {len(impl_code)} bytes")
print(f"  SLOAD count: {sload_count}")
print(f"  SSTORE count: {sstore_count}")
print(f"  STATICCALL count: {staticcall_count}")
print(f"  CALL count: {call_count}")
print(f"  TIMESTAMP opcode count: {timestamp_count}")

if sstore_count > 0:
    print(f"  >>> Has state writes — can change internal state")
    print(f"  >>> The challenge/healing mechanism likely stores state")
if staticcall_count > 0:
    print(f"  >>> Makes external reads — reads from primary/backup oracles")

# Check MetaOracle storage more deeply
META_ORACLE = "0xe8465B52E106d98157d82b46cA566CB9d09482A9"
print(f"\n  MetaOracle storage (slots 0-20):")
for slot in range(21):
    storage = w3.eth.get_storage_at(Web3.to_checksum_address(META_ORACLE), slot)
    val = int.from_bytes(storage, 'big')
    if val > 0:
        if val < 2**160 and val > 2**80:
            print(f"    slot[{slot}]: {addr_from(storage)} (address)")
        elif val > now - 86400 * 365 and val < now + 86400 and val > 1700000000:
            ts = time.strftime('%Y-%m-%d %H:%M UTC', time.gmtime(val))
            age = (now - val) / 3600
            print(f"    slot[{slot}]: {ts} ({age:.1f}h ago) *** TIMESTAMP ***")
        else:
            print(f"    slot[{slot}]: {val}")

# ============================================================================
# Now check the second NUSD PT market (PT-srNUSD-28MAY2026) for similar pattern
# ============================================================================
print(f"\n{'='*80}")
print("PT-srNUSD-28MAY2026 ANALYSIS")
print("=" * 80)

META_SRNUSD = "0x0D07087b26b28995a66050f5bb7197D439221DE3"
primary_srnusd = addr_from(raw_call(META_SRNUSD, "0x2289445e"))
backup_srnusd = addr_from(raw_call(META_SRNUSD, "0x836efd31"))

print(f"  Primary: {primary_srnusd}")
print(f"  Backup:  {backup_srnusd}")

# Check backup target
if backup_srnusd:
    bt = addr_from(raw_call(backup_srnusd, "0x7dc0d1d0"))
    bo = addr_from(raw_call(backup_srnusd, "0x8da5cb5b"))
    print(f"  Backup target: {bt}")
    print(f"  Backup owner:  {bo}")
    if bt and primary_srnusd and bt.lower() == primary_srnusd.lower():
        print(f"  >>> CONFIRMED: BACKUP=PRIMARY ALSO ON srNUSD!")

# Check the srNUSD primary oracle's feed
if primary_srnusd:
    srnusd_feed = addr_from(raw_call(primary_srnusd, "0xf50a4718"))
    print(f"  Primary feed: {srnusd_feed}")
    if srnusd_feed:
        feed_code2 = w3.eth.get_code(Web3.to_checksum_address(srnusd_feed))
        print(f"  Feed bytecode: {len(feed_code2)} bytes")
        # Check expiry
        exp = u256(raw_call(srnusd_feed, "0x204f83f9"))
        if exp and exp > 1700000000:
            ts = time.strftime('%Y-%m-%d %H:%M UTC', time.gmtime(exp))
            days = (exp - now) / 86400
            print(f"  Feed expiry: {ts} ({days:.1f} days)")
        max_rate = u256(raw_call(srnusd_feed, "0x598e5451"))
        if max_rate:
            print(f"  Feed maxRate: {max_rate/1e18*100:.1f}%")

        # Check opcode pattern
        sc = sum(1 for b in feed_code2 if b == 0xFA)
        ts_count = sum(1 for b in feed_code2 if b == 0x42)
        print(f"  STATICCALL count: {sc}, TIMESTAMP count: {ts_count}")

print("\nDone.")
