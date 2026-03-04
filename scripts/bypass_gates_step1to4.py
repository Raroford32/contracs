#!/usr/bin/env python3
"""
STEP 1: Verify that BOTH primary and backup oracles read the SAME Pendle TWAP.

If true → the MetaOracleDeviationTimelock's deviation check is BLIND to TWAP manipulation.
The deviation check only catches underlying stablecoin depeg, NOT PT overvaluation via AMM manipulation.

STEP 2: Check if there's an UPSIDE cap on PT price.
The "max discount" parameter (1%) caps downward. But what about above par?
If PT TWAP shows 1.05, does the oracle report 1.05 uncapped?

STEP 3: Analyze the OracleRouter owner — who controls the backup oracle?

STEP 4: Check updatedAt=0 from PendleChainlinkOracle — does this bypass staleness checks?
"""

import os
import time
import json
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
        w3 = _w3
        print(f"Block: {bn}")
        break
    except:
        continue

now = w3.eth.get_block("latest")["timestamp"]
print(f"Time: {time.strftime('%Y-%m-%d %H:%M:%S UTC', time.gmtime(now))}\n")

def raw_call(addr, data_hex):
    try:
        return w3.eth.call({"to": Web3.to_checksum_address(addr), "data": data_hex})
    except Exception as e:
        return f"REVERT: {e}"

def u256(data, offset=0):
    if isinstance(data, str): return None
    if data and len(data) >= offset + 32:
        return int.from_bytes(data[offset:offset+32], 'big')
    return None

def addr_from(data, offset=0):
    if isinstance(data, str): return None
    if data and len(data) >= offset + 32:
        return "0x" + data[offset+12:offset+32].hex()
    return None

ZERO = "0x" + "0" * 40

# ============================================================================
# STEP 1: Do both oracles read the same TWAP?
# ============================================================================
print("=" * 100)
print("STEP 1: DO BOTH ORACLES READ THE SAME PENDLE TWAP?")
print("=" * 100)

# MetaOracleDeviationTimelock for PT-sNUSD
META_ORACLE = "0xe8465B52E106d98157d82b46cA566CB9d09482A9"

# Known selectors from previous probe
# Primary oracle (selector 0x2289445e AND 0xbd8f238e)
primary_oracle = addr_from(raw_call(META_ORACLE, "0x2289445e"))
# Backup oracle (selector 0x836efd31)
backup_oracle = addr_from(raw_call(META_ORACLE, "0x836efd31"))

print(f"  Primary oracle: {primary_oracle}")
print(f"  Backup oracle:  {backup_oracle}")

# Primary oracle is a MorphoChainlinkOracleV2 at 0xd25a93...
# Check its BASE_FEED_1 (the Pendle TWAP adapter)
PRIMARY = "0xd25a93399d82e1a08d9da61d21fdff7f3e65eb27"
# This is a 2598-byte contract. Let's check if it's MorphoChainlinkOracleV2
# by trying known selectors
# But earlier, standard CV2 selectors returned None for this address
# Let me try custom selectors from the bytecode

# Actually, the primary is NOT a standard MorphoChainlinkOracleV2 — it only responded to:
# 0xa035b1fe (price), 0xf50a4718 (some address), 0xce4b5bbe (1000000), 0x054f7ac0 (1), 0x461739d2 (1)
# The 0xf50a4718 address = 0xe488ee19e06eb9d5fef39b076682d959db87168b (PendleChainlinkOracle)

primary_feed = addr_from(raw_call(PRIMARY, "0xf50a4718"))
print(f"\n  Primary oracle's feed (0xf50a4718): {primary_feed}")

# Backup oracle is OracleRouter at 0x385ad6da...
BACKUP = "0x385ad6da207565bb232c0cc93602a3b785a16960"
# It has: 0x7dc0d1d0 => another address, 0x8da5cb5b => owner
backup_target = addr_from(raw_call(BACKUP, "0x7dc0d1d0"))
backup_owner = addr_from(raw_call(BACKUP, "0x8da5cb5b"))
print(f"  Backup oracle's target (0x7dc0d1d0): {backup_target}")
print(f"  Backup oracle's owner (0x8da5cb5b): {backup_owner}")

# KEY QUESTION: Does the backup oracle point to the SAME primary oracle?
print(f"\n  >>> Primary oracle address: {PRIMARY}")
print(f"  >>> Backup target address:  {backup_target}")
if backup_target and backup_target.lower() == PRIMARY.lower():
    print(f"  >>> !!! BACKUP POINTS TO SAME PRIMARY ORACLE !!!")
    print(f"  >>> The deviation check monitors primary vs backup")
    print(f"  >>> But they're THE SAME ORACLE → deviation = 0 ALWAYS")
    print(f"  >>> MetaOracleDeviationTimelock is COMPLETELY BLIND to TWAP manipulation!")
else:
    print(f"  >>> Different targets. Checking if they share the same feed...")
    # Check if the backup target has a feed
    if backup_target:
        bt_feed = addr_from(raw_call(backup_target, "0xf50a4718"))
        bt_price = u256(raw_call(backup_target, "0xa035b1fe"))
        print(f"  >>> Backup target feed: {bt_feed}")
        print(f"  >>> Backup target price: {bt_price}")

        if bt_feed and primary_feed and bt_feed.lower() == primary_feed.lower():
            print(f"  >>> !!! SAME PENDLE FEED IN BOTH ORACLES !!!")
            print(f"  >>> TWAP manipulation affects BOTH equally")
            print(f"  >>> Deviation check won't fire for TWAP manipulation")

# Get prices from both
primary_price = u256(raw_call(PRIMARY, "0xa035b1fe"))
backup_price = u256(raw_call(BACKUP, "0xa035b1fe"))
meta_price = u256(raw_call(META_ORACLE, "0xa035b1fe"))

print(f"\n  Price comparison:")
print(f"    Primary:  {primary_price}")
print(f"    Backup:   {backup_price}")
print(f"    Meta:     {meta_price}")
if primary_price and backup_price:
    div = abs(primary_price - backup_price) / max(primary_price, backup_price) * 100
    print(f"    Divergence: {div:.8f}%")

# ============================================================================
# STEP 2: IS THERE AN UPSIDE CAP?
# ============================================================================
print(f"\n{'='*100}")
print("STEP 2: UPSIDE CAP CHECK")
print("=" * 100)

max_discount = u256(raw_call(META_ORACLE, "0xd94ad837"))
print(f"  Max discount (0xd94ad837): {max_discount} ({max_discount/1e18*100:.2f}%)")
print(f"  This caps DOWNWARD deviation. PT >= (1 - maxDiscount) * underlying")
print(f"  But what about UPWARD? If TWAP shows PT = 1.05 * underlying?")

# Check the PendleChainlinkOracle (the feed that returns TWAP)
PENDLE_FEED = "0xe488ee19e06eb9d5fef39b076682d959db87168b"
feed_answer = u256(raw_call(PENDLE_FEED, "0x50d25bcd"))  # latestAnswer()
print(f"\n  PendleChainlinkOracle latestAnswer: {feed_answer}")
if feed_answer:
    print(f"    = {feed_answer / 1e18:.8f} (if /1e18)")
    if feed_answer > 1e18:
        print(f"    >>> PT IS PRICED ABOVE PAR! ({(feed_answer/1e18 - 1)*100:.4f}% premium)")
    else:
        print(f"    >>> PT at {(1 - feed_answer/1e18)*100:.4f}% discount")

# Check all responding selectors on PendleChainlinkOracle to find any cap logic
print(f"\n  Full selector scan on PendleChainlinkOracle ({PENDLE_FEED}):")
code = w3.eth.get_code(Web3.to_checksum_address(PENDLE_FEED))
print(f"  Bytecode size: {len(code)} bytes")

selectors = set()
for i in range(len(code) - 4):
    if code[i] == 0x63:
        sel = code[i+1:i+5].hex()
        selectors.add(sel)

for sel in sorted(selectors):
    result = raw_call(PENDLE_FEED, "0x" + sel)
    if isinstance(result, bytes) and len(result) >= 32:
        val = u256(result)
        if val and val > 0:
            a = addr_from(result)
            if val < 2**160 and val > 2**80:
                print(f"    0x{sel} => {a}")
            else:
                print(f"    0x{sel} => {val}")

# ============================================================================
# STEP 3: ORACLE ROUTER OWNER ANALYSIS
# ============================================================================
print(f"\n{'='*100}")
print("STEP 3: ORACLEROUTER OWNER ANALYSIS")
print("=" * 100)

print(f"  OracleRouter: {BACKUP}")
print(f"  Owner: {backup_owner}")

# Check if owner is a contract or EOA
if backup_owner:
    owner_code = w3.eth.get_code(Web3.to_checksum_address(backup_owner))
    print(f"  Owner bytecode size: {len(owner_code)} bytes")
    if len(owner_code) <= 2:
        print(f"  >>> OWNER IS AN EOA! Single key controls backup oracle!")
        print(f"  >>> Compromise this key → change backup oracle → force challenge → use malicious oracle")
    else:
        print(f"  >>> Owner is a contract. Checking type...")
        # Try common multisig/timelock selectors
        multisig_sels = {
            "0xaffed0e0": "nonce()",  # Gnosis Safe
            "0xa0e67e2b": "getOwners()", # Gnosis Safe
            "0xe75235b8": "getThreshold()", # Gnosis Safe
            "0x0d8e6e2c": "getModules()", # Gnosis Safe v1.1
            "0x8cff6355": "getDelay()", # Timelock
            "0x6a42b8f8": "delay()", # Timelock
            "0xf851a440": "admin()", # Proxy admin
        }
        for sel, name in multisig_sels.items():
            result = raw_call(backup_owner, sel)
            if isinstance(result, bytes) and len(result) >= 32:
                val = u256(result)
                if val is not None and val > 0:
                    if val < 2**160 and val > 2**80:
                        print(f"    {name}: {addr_from(result)}")
                    else:
                        print(f"    {name}: {val}")

# ============================================================================
# STEP 4: updatedAt=0 STALENESS BYPASS
# ============================================================================
print(f"\n{'='*100}")
print("STEP 4: updatedAt=0 STALENESS CHECK")
print("=" * 100)

# Check latestRoundData from the PendleChainlinkOracle
lrd = raw_call(PENDLE_FEED, "0xfeaf968c")  # latestRoundData()
if isinstance(lrd, bytes) and len(lrd) >= 160:
    roundId = u256(lrd, 0)
    answer = u256(lrd, 32)
    startedAt = u256(lrd, 64)
    updatedAt = u256(lrd, 96)
    answeredInRound = u256(lrd, 128)
    print(f"  PendleChainlinkOracle.latestRoundData():")
    print(f"    roundId: {roundId}")
    print(f"    answer: {answer} ({answer/1e18:.8f})")
    print(f"    startedAt: {startedAt}")
    print(f"    updatedAt: {updatedAt}")
    print(f"    answeredInRound: {answeredInRound}")

    if updatedAt == 0:
        print(f"\n  >>> updatedAt = 0 !!!")
        print(f"  >>> MorphoChainlinkOracleV2 does NOT check staleness (by design)")
        print(f"  >>> But MetaOracleDeviationTimelock has heartbeat = 43200 sec (12h)")
        print(f"  >>> Does MetaOracle check updatedAt from the feed?")
        print(f"  >>> If so, updatedAt=0 would make the feed appear infinitely stale")
        print(f"  >>> If the heartbeat check uses updatedAt from latestRoundData:")
        print(f"  >>>   block.timestamp - 0 = {now} seconds = {now/86400:.0f} days stale")
        print(f"  >>>   This would ALWAYS exceed the 12h heartbeat → oracle should revert")
        print(f"  >>>   But price() works fine → heartbeat check must NOT use feed's updatedAt")
        print(f"  >>>   OR the heartbeat is checked differently (MetaOracle's own state)")

# Check MetaOracle implementation for heartbeat-related storage
# The heartbeat selectors: 0xd83ed440 = 43200, 0x498e8b6e = 14400
# Let's check if there are additional state variables tracking last update time
print(f"\n  Checking MetaOracle state variables...")
# Try reading storage slots
for slot in range(20):
    storage = w3.eth.get_storage_at(Web3.to_checksum_address(META_ORACLE), slot)
    val = int.from_bytes(storage, 'big')
    if val > 0:
        if val < 2**160 and val > 2**80:
            print(f"    slot[{slot}]: {addr_from(storage)} (address)")
        elif val > now - 86400 * 365 and val < now + 86400:
            # Looks like a timestamp
            ts_str = time.strftime('%Y-%m-%d %H:%M:%S UTC', time.gmtime(val))
            age = (now - val) / 3600
            print(f"    slot[{slot}]: {val} = {ts_str} ({age:.1f} hours ago) *** TIMESTAMP ***")
        else:
            print(f"    slot[{slot}]: {val}")

# ============================================================================
# STEP 5: POST-MATURITY PENDLE AMM STATE
# ============================================================================
print(f"\n{'='*100}")
print("STEP 5: PENDLE AMM POST-MATURITY BEHAVIOR")
print("=" * 100)

PT_SNUSD = "0x54Bf2659B5CdFd86b75920e93C0844c0364F5166"

# Check if PT has expired
is_expired = raw_call(PT_SNUSD, "0x2f13b60c")
if isinstance(is_expired, bytes):
    print(f"  PT-sNUSD isExpired(): {bool(u256(is_expired))}")

# The PT's factory
factory = addr_from(raw_call(PT_SNUSD, "0xc45a0155"))
print(f"  PT factory: {factory}")

# Try to get expiry from the factory or other sources
# Try different expiry() selectors
for sel_name, sel in [("0xd9548e53", "expiry()"), ("0xbfe10928", "maturity()"), ("0xb5d1c4a4", "MATURITY()"), ("0x204f83f9", "deadline()")]:
    result = raw_call(PT_SNUSD, sel_name)
    if isinstance(result, bytes) and len(result) >= 32:
        val = u256(result)
        if val and val > 1700000000 and val < 2000000000:
            exp_str = time.strftime('%Y-%m-%d %H:%M:%S UTC', time.gmtime(val))
            hours_to = (val - now) / 3600
            print(f"  {sel}: {val} = {exp_str} ({hours_to:.2f} hours)")

# Check PT totalSupply and if it's declining (LPs withdrawing)
pt_supply = u256(raw_call(PT_SNUSD, "0x18160ddd"))
print(f"\n  PT totalSupply: {pt_supply / 1e18:,.4f}" if pt_supply else "  PT totalSupply: None")

# Check the PendleChainlinkOracle to understand what Pendle market it reads from
print(f"\n  Scanning PendleChainlinkOracle for Pendle market/oracle references:")
# We already found selectors in PendleChainlinkOracle (951 bytes)
# Let me probe it more carefully
for sel in sorted(selectors):
    result = raw_call(PENDLE_FEED, "0x" + sel)
    if isinstance(result, bytes) and len(result) >= 32:
        val = u256(result)
        a = addr_from(result)
        if val and val > 0:
            if val < 2**160 and val > 2**80:
                # Check if this address is a Pendle market
                code_size = len(w3.eth.get_code(Web3.to_checksum_address(a)))
                print(f"    0x{sel} => {a} (code: {code_size} bytes)")
            elif val < 10**30:
                print(f"    0x{sel} => {val}")

# ============================================================================
# STEP 6: META-ORACLE IMPLEMENTATION BYTECODE ANALYSIS
# ============================================================================
print(f"\n{'='*100}")
print("STEP 6: META-ORACLE IMPLEMENTATION DEEP ANALYSIS")
print("=" * 100)

# The implementation is 0xcc319ef091bc520cf6835565826212024b2d25ec
IMPL = "0xcc319ef091bc520cf6835565826212024b2d25ec"
impl_code = w3.eth.get_code(Web3.to_checksum_address(IMPL))
print(f"  Implementation: {IMPL}")
print(f"  Bytecode: {len(impl_code)} bytes")

# Find ALL selectors and probe them via the proxy
all_impl_sels = set()
for i in range(len(impl_code) - 4):
    if impl_code[i] == 0x63:
        sel = impl_code[i+1:i+5].hex()
        all_impl_sels.add(sel)

print(f"  Found {len(all_impl_sels)} PUSH4 opcodes")
print(f"\n  All responding selectors:")

for sel in sorted(all_impl_sels):
    result = raw_call(META_ORACLE, "0x" + sel)
    if isinstance(result, bytes) and len(result) >= 32:
        val = u256(result)
        if val is not None and val > 0:
            if val < 2**160 and val > 2**80:
                a = addr_from(result)
                print(f"    0x{sel} => {a}")
            elif val > now - 86400 * 365 and val < now + 86400 and val > 1700000000:
                ts_str = time.strftime('%Y-%m-%d %H:%M:%S UTC', time.gmtime(val))
                age = (now - val) / 3600
                print(f"    0x{sel} => {val} = {ts_str} ({age:.1f}h ago) *** TIMESTAMP ***")
            else:
                print(f"    0x{sel} => {val}")

print("\nDone.")
