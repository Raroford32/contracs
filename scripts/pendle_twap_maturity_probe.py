#!/usr/bin/env python3
"""
Deep probe of Pendle AMM TWAP oracle for PT-sNUSD-5MAR2026.

Key findings so far:
- Oracle is EIP-1167 proxy -> impl 0xcc319ef091bc520cf6835565826212024b2d25ec (6166 bytes)
- NOT SparkLinearDiscountOracle (too large, has TWAP params)
- Selector 0x498e8b6e => 14400 (4 hours = TWAP duration)
- Selector 0xd83ed440 => 43200 (12 hours = heartbeat?)
- Selector 0xd94ad837 => 1e16 (1% = max discount?)
- Market: 0xd25a93399d82e1a08d9da61d21fdff7f3e65eb27
- Oracle ref: 0x385ad6da207565bb232c0cc93602a3b785a16960

This script:
1. Checks the Pendle market state (liquidity, PT concentration)
2. Checks the Pendle oracle state (TWAP observations)
3. Analyzes maturity proximity risk
4. Estimates TWAP manipulation cost
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
    exit(1)

now = w3.eth.get_block("latest")["timestamp"]
print(f"Time: {time.strftime('%Y-%m-%d %H:%M:%S UTC', time.gmtime(now))}")

def safe_call(addr, abi_json, func_name, *args):
    try:
        c = w3.eth.contract(address=Web3.to_checksum_address(addr), abi=json.loads(abi_json) if isinstance(abi_json, str) else abi_json)
        return getattr(c.functions, func_name)(*args).call()
    except Exception as e:
        return None

def raw_call(addr, selector_hex, decode="uint256"):
    try:
        result = w3.eth.call({"to": Web3.to_checksum_address(addr), "data": selector_hex})
        if decode == "uint256":
            return int.from_bytes(result[:32], 'big')
        elif decode == "address":
            return "0x" + result[12:32].hex()
        elif decode == "bool":
            return int.from_bytes(result[:32], 'big') != 0
        return result.hex()
    except:
        return None

# ============================================================================
# Known addresses from previous probe
# ============================================================================

# PT-sNUSD-5MAR2026 oracle
ORACLE_SNUSD = "0xe8465B52E106d98157d82b46cA566CB9d09482A9"
MARKET_SNUSD = "0xd25a93399d82e1a08d9da61d21fdff7f3e65eb27"
ORACLE_REF_SNUSD = "0x385ad6da207565bb232c0cc93602a3b785a16960"
PT_SNUSD = "0x54Bf2659B5CdFd86b75920e93C0844c0364F5166"

# PT-srUSDe-2APR2026 oracle
ORACLE_SRUSDE = "0x8B417d1e0C08d8005B7Ca1d5ebbc72Ea877DB391"
MARKET_SRUSDE = "0x527c71f87ed3b65e14476f45db57bfbce56343b6"
ORACLE_REF_SRUSDE = "0xfbba40881e75fa48c32e0dad97edc0858c16aaa0"

ERC20_ABI = json.loads('''[
  {"inputs":[],"name":"symbol","outputs":[{"type":"string"}],"stateMutability":"view","type":"function"},
  {"inputs":[],"name":"decimals","outputs":[{"type":"uint8"}],"stateMutability":"view","type":"function"},
  {"inputs":[{"type":"address"}],"name":"balanceOf","outputs":[{"type":"uint256"}],"stateMutability":"view","type":"function"},
  {"inputs":[],"name":"totalSupply","outputs":[{"type":"uint256"}],"stateMutability":"view","type":"function"}
]''')

# Pendle market ABI (V2)
PENDLE_MARKET_ABI = json.loads('''[
  {"inputs":[],"name":"readTokens","outputs":[{"type":"address"},{"type":"address"},{"type":"address"}],"stateMutability":"view","type":"function"},
  {"inputs":[],"name":"expiry","outputs":[{"type":"uint256"}],"stateMutability":"view","type":"function"},
  {"inputs":[],"name":"isExpired","outputs":[{"type":"bool"}],"stateMutability":"view","type":"function"},
  {"inputs":[],"name":"totalActiveSupply","outputs":[{"type":"uint256"}],"stateMutability":"view","type":"function"},
  {"inputs":[],"name":"totalSy","outputs":[{"type":"uint256"}],"stateMutability":"view","type":"function"},
  {"inputs":[],"name":"totalPt","outputs":[{"type":"uint256"}],"stateMutability":"view","type":"function"},
  {"inputs":[],"name":"readState","outputs":[{"type":"tuple","components":[{"type":"uint256","name":"totalPt"},{"type":"uint256","name":"totalSy"},{"type":"uint80","name":"lastLnImpliedRate"},{"type":"uint16","name":"observationIndex"},{"type":"uint16","name":"observationCardinality"},{"type":"uint16","name":"observationCardinalityNext"}],"name":"state"}],"stateMutability":"view","type":"function"},
  {"inputs":[],"name":"getReserves","outputs":[{"type":"uint256"},{"type":"uint256"}],"stateMutability":"view","type":"function"},
  {"inputs":[],"name":"symbol","outputs":[{"type":"string"}],"stateMutability":"view","type":"function"},
  {"inputs":[],"name":"totalSupply","outputs":[{"type":"uint256"}],"stateMutability":"view","type":"function"}
]''')

# Pendle PT Oracle ABI (the core oracle that stores TWAP observations)
PENDLE_PT_ORACLE_ABI = json.loads('''[
  {"inputs":[{"type":"address","name":"market"},{"type":"uint32","name":"duration"}],"name":"getPtToAssetRate","outputs":[{"type":"uint256"}],"stateMutability":"view","type":"function"},
  {"inputs":[{"type":"address","name":"market"},{"type":"uint32","name":"duration"}],"name":"getPtToSyRate","outputs":[{"type":"uint256"}],"stateMutability":"view","type":"function"},
  {"inputs":[{"type":"address","name":"market"},{"type":"uint32","name":"duration"}],"name":"getOracleState","outputs":[{"type":"bool","name":"increaseCardinalityRequired"},{"type":"uint16","name":"cardinalityRequired"},{"type":"bool","name":"oldestObservationSatisfied"}],"stateMutability":"view","type":"function"}
]''')

# ============================================================================
# Analyze each market
# ============================================================================
for label, oracle_addr, market_addr, oracle_ref, pt_addr in [
    ("PT-sNUSD-5MAR2026 ($6.5M borrow)", ORACLE_SNUSD, MARKET_SNUSD, ORACLE_REF_SNUSD, PT_SNUSD),
    ("PT-srUSDe-2APR2026 ($12M borrow)", ORACLE_SRUSDE, MARKET_SRUSDE, ORACLE_REF_SRUSDE, None),
]:
    print(f"\n{'='*100}")
    print(f"  {label}")
    print(f"  Oracle: {oracle_addr}")
    print(f"  Pendle Market: {market_addr}")
    print(f"  Oracle Ref: {oracle_ref}")
    print(f"{'='*100}")

    # Get market info
    sym = safe_call(market_addr, ERC20_ABI, "symbol")
    expiry = safe_call(market_addr, PENDLE_MARKET_ABI, "expiry")
    is_expired = safe_call(market_addr, PENDLE_MARKET_ABI, "isExpired")
    lp_supply = safe_call(market_addr, ERC20_ABI, "totalSupply")

    print(f"\n  Market symbol: {sym}")
    if expiry:
        exp_str = time.strftime('%Y-%m-%d %H:%M:%S UTC', time.gmtime(expiry))
        days_to = (expiry - now) / 86400
        hours_to = (expiry - now) / 3600
        print(f"  Expiry: {exp_str}")
        print(f"  Time to expiry: {days_to:.4f} days ({hours_to:.2f} hours)")
    print(f"  Is expired: {is_expired}")
    print(f"  LP supply: {lp_supply}")

    # Get market reserves
    tokens = safe_call(market_addr, PENDLE_MARKET_ABI, "readTokens")
    if tokens:
        sy_addr, pt_in_market, yt_addr = tokens
        sy_sym = safe_call(sy_addr, ERC20_ABI, "symbol")
        pt_sym = safe_call(pt_in_market, ERC20_ABI, "symbol")
        print(f"\n  SY: {sy_sym} ({sy_addr})")
        print(f"  PT: {pt_sym} ({pt_in_market})")
        print(f"  YT: {yt_addr}")

    reserves = safe_call(market_addr, PENDLE_MARKET_ABI, "getReserves")
    if reserves:
        print(f"\n  AMM Reserves:")
        print(f"    Reserve 0 (SY): {reserves[0] / 1e18:,.4f}")
        print(f"    Reserve 1 (PT): {reserves[1] / 1e18:,.4f}")
        if reserves[0] > 0:
            pt_concentration = reserves[1] / (reserves[0] + reserves[1]) * 100
            print(f"    PT concentration: {pt_concentration:.2f}%")
            print(f"    >>> {'HIGH PT CONCENTRATION - thin liquidity!' if pt_concentration > 80 else 'Moderate'}")

    state = safe_call(market_addr, PENDLE_MARKET_ABI, "readState")
    if state:
        print(f"\n  Market State:")
        print(f"    totalPt: {state[0] / 1e18:,.4f}")
        print(f"    totalSy: {state[1] / 1e18:,.4f}")
        print(f"    lastLnImpliedRate: {state[2]}")
        print(f"    observationIndex: {state[3]}")
        print(f"    observationCardinality: {state[4]}")
        print(f"    observationCardinalityNext: {state[5]}")

    # Check Pendle oracle state
    print(f"\n  Pendle Oracle Ref: {oracle_ref}")

    # Try getPtToAssetRate with TWAP duration from oracle params
    twap_dur = raw_call(oracle_addr, "0x498e8b6e")  # TWAP duration
    heartbeat = raw_call(oracle_addr, "0xd83ed440")  # Heartbeat
    max_discount = raw_call(oracle_addr, "0xd94ad837")  # Max discount

    print(f"  TWAP duration: {twap_dur} sec ({twap_dur/3600:.1f} hours)" if twap_dur else "  TWAP duration: ?")
    print(f"  Heartbeat: {heartbeat} sec ({heartbeat/3600:.1f} hours)" if heartbeat else "  Heartbeat: ?")
    print(f"  Max discount: {max_discount} ({max_discount/1e18*100:.2f}%)" if max_discount else "  Max discount: ?")

    if oracle_ref and twap_dur:
        # Try to get PT-to-asset rate from the Pendle oracle
        pt_to_asset = safe_call(oracle_ref, PENDLE_PT_ORACLE_ABI, "getPtToAssetRate", Web3.to_checksum_address(market_addr), twap_dur)
        pt_to_sy = safe_call(oracle_ref, PENDLE_PT_ORACLE_ABI, "getPtToSyRate", Web3.to_checksum_address(market_addr), twap_dur)
        oracle_state = safe_call(oracle_ref, PENDLE_PT_ORACLE_ABI, "getOracleState", Web3.to_checksum_address(market_addr), twap_dur)

        print(f"\n  Pendle TWAP Oracle:")
        print(f"    getPtToAssetRate({twap_dur}s): {pt_to_asset}")
        if pt_to_asset:
            print(f"    = {pt_to_asset / 1e18:.8f}")
        print(f"    getPtToSyRate({twap_dur}s): {pt_to_sy}")
        if pt_to_sy:
            print(f"    = {pt_to_sy / 1e18:.8f}")
        if oracle_state:
            print(f"    Oracle state: increaseCardinality={oracle_state[0]}, required={oracle_state[1]}, oldestSatisfied={oracle_state[2]}")

    # Morpho oracle price
    morpho_price = raw_call(oracle_addr, "0xa035b1fe")
    raw_price_2 = raw_call(oracle_addr, "0x362a07ae")
    capped_price = raw_call(oracle_addr, "0xad891006")

    print(f"\n  Morpho Oracle Outputs:")
    print(f"    price() [0xa035b1fe]: {morpho_price}")
    if morpho_price:
        # Morpho price is scaled to 36 decimals for same-decimal assets
        print(f"    = {morpho_price / 1e24:.8f} (if /1e24)")
        print(f"    = {morpho_price / 1e18:.8f} (if /1e18)")
    print(f"    [0x362a07ae]: {raw_price_2}")
    print(f"    [0xad891006]: {capped_price}")

    if morpho_price and capped_price and morpho_price != capped_price:
        diff = abs(morpho_price - capped_price) / morpho_price * 100
        print(f"    >>> PRICE DIVERGENCE: {diff:.6f}% between two price outputs!")
        print(f"    >>> One may be capped/floored, the other raw TWAP")

    # MATURITY RISK ANALYSIS
    if expiry:
        days_to = (expiry - now) / 86400
        if days_to < 7:
            print(f"\n  {'!'*60}")
            print(f"  NEAR-MATURITY ANALYSIS")
            print(f"  {'!'*60}")
            print(f"  Days to expiry: {days_to:.4f}")

            if reserves:
                total_liq = reserves[0] + reserves[1]
                print(f"  Total AMM liquidity: {total_liq / 1e18:,.0f} tokens")
                print(f"  >>> With {twap_dur/3600:.0f}h TWAP, manipulation cost depends on liquidity depth")

                # Rough estimate: to move TWAP by X%, need to maintain position for TWAP duration
                # Cost = liquidity_moved * time_fraction * price_impact
                if reserves[0] > 0 and reserves[1] > 0:
                    # Simple constant-product estimate of manipulation cost
                    # To move spot price by 10%, need ~sqrt(1.1) - 1 ≈ 5% of reserves
                    cost_5pct = reserves[0] * 0.05 / 1e18
                    print(f"  >>> Rough cost to move spot 5%: ~{cost_5pct:,.0f} SY tokens")
                    print(f"  >>> But sustained for {twap_dur/3600:.0f}h TWAP window = much more expensive")

            if max_discount:
                print(f"\n  Max discount parameter: {max_discount/1e18*100:.2f}%")
                print(f"  >>> Oracle caps PT price to (1 - maxDiscount) of underlying")
                print(f"  >>> At maturity, discount should be ~0, so price ~= underlying")
                print(f"  >>> If TWAP shows > 1.0 (PT overpriced), max_discount floor might not protect")

            if days_to <= 1:
                print(f"\n  >>> CRITICAL: Less than 24 hours to maturity!")
                print(f"  >>> Pendle AMM behavior near/at maturity:")
                print(f"  >>>   - LPs typically withdraw (concentrated liquidity drains)")
                print(f"  >>>   - PT concentration increases")
                print(f"  >>>   - Implied rate becomes volatile")
                print(f"  >>>   - TWAP becomes less reliable with fewer trades")

print("\nDone.")
