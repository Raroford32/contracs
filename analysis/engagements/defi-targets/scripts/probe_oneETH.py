#!/usr/bin/env python3
"""
Probe on-chain state of the oneETH protocol at 0x6fcbbb527fb2954bed2b224a5bb7c23c5aeeb6e1
on Ethereum mainnet using raw JSON-RPC calls.
"""

import json
import time
import requests
import sys
from datetime import datetime, timezone

# ── Config ──────────────────────────────────────────────────────────────────
RPC_URL = "https://eth-mainnet.g.alchemy.com/v2/pLXdY7rYRY10SH_UTLBGH"
ONE_ETH = "0x6fcbbb527fb2954bed2b224a5bb7c23c5aeeb6e1"
WETH     = "0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2"
USDC     = "0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48"
ZERO_ADDR = "0x0000000000000000000000000000000000000000"

OUTPUT_PATH = "/home/user/contracs/analysis/engagements/defi-targets/notes/oneETH_state.md"

# ── Helpers ─────────────────────────────────────────────────────────────────
call_id = 0

def rpc_keccak(text):
    """Use web3_sha3 RPC method to compute keccak256."""
    global call_id
    call_id += 1
    hex_input = "0x" + text.encode().hex()
    resp = requests.post(RPC_URL, json={
        "jsonrpc": "2.0",
        "method": "web3_sha3",
        "params": [hex_input],
        "id": call_id
    }, timeout=30)
    return resp.json().get("result", "0x")

# Precompute selectors
print("Computing selectors via web3_sha3...")
sigs = [
    "totalSupply()",
    "reserveRatio()",
    "MIN_RESERVE_RATIO()",
    "withdrawFee()",
    "mintFee()",
    "stimulus()",
    "gov()",
    "lpGov()",
    "oneTokenOracle()",
    "stimulusOracle()",
    "chainLink()",
    "minimumRefreshTime()",
    "reserveStepSize()",
    "lastRefreshReserve()",
    "collateralArray(uint256)",
    "acceptedCollateral(address)",
    "collateralDecimals(address)",
    "collateralOracle(address)",
    "getCollateralUsd(address)",
    "getStimulusOracle()",
    "getOneTokenUsd()",
    "globalCollateralValue()",
    "balanceOf(address)",
    "pair()",
    "getReserves()",
    "token0()",
    "token1()",
    "name()",
    "symbol()",
    "decimals()",
    "consult(address,uint256)",
    "price0CumulativeLast()",
    "price1CumulativeLast()",
    "blockTimestampLast()",
    "lastUpdateTime()",
    "lastCumulativePrice()",
    "owner()",
    "paused()",
    "Transfer(address,address,uint256)",
]

SELECTORS = {}
# Batch the keccak calls
batch = []
for sig in sigs:
    call_id += 1
    hex_input = "0x" + sig.encode().hex()
    batch.append({
        "jsonrpc": "2.0",
        "method": "web3_sha3",
        "params": [hex_input],
        "id": call_id
    })

resp = requests.post(RPC_URL, json=batch, timeout=30)
hash_results = resp.json()
if isinstance(hash_results, list):
    hash_results.sort(key=lambda x: x.get("id", 0))
    for i, sig in enumerate(sigs):
        full_hash = hash_results[i].get("result", "0x")
        SELECTORS[sig] = full_hash[:10]  # 4-byte selector
        if sig == "Transfer(address,address,uint256)":
            SELECTORS[sig + "_full"] = full_hash  # full 32-byte topic
else:
    print("ERROR: batch keccak failed")
    sys.exit(1)

assert SELECTORS["totalSupply()"] == "0x18160ddd", f"Selector mismatch: {SELECTORS['totalSupply()']}"
print(f"  Selectors computed. totalSupply() = {SELECTORS['totalSupply()']} (verified)")

def eth_call(to, data, block="latest"):
    """Execute eth_call and return hex result."""
    global call_id
    call_id += 1
    resp = requests.post(RPC_URL, json={
        "jsonrpc": "2.0",
        "method": "eth_call",
        "params": [{"to": to, "data": data}, block],
        "id": call_id
    }, timeout=30)
    result = resp.json()
    if "error" in result:
        return None
    return result.get("result")

def eth_call_batch(calls):
    """Batch eth_call. Each call is (to, data, label). Returns list of hex results."""
    global call_id
    batch = []
    for (to, data, label) in calls:
        call_id += 1
        batch.append({
            "jsonrpc": "2.0",
            "method": "eth_call",
            "params": [{"to": to, "data": data}, "latest"],
            "id": call_id
        })
    resp = requests.post(RPC_URL, json=batch, timeout=60)
    results = resp.json()
    if isinstance(results, list):
        results.sort(key=lambda x: x.get("id", 0))
    else:
        results = [results]
    out = []
    for r in results:
        if "error" in r:
            out.append(None)
        else:
            out.append(r.get("result"))
    return out

def decode_uint(hex_val):
    if hex_val is None or hex_val == "0x" or len(hex_val) < 3:
        return None
    try:
        return int(hex_val, 16)
    except:
        return None

def decode_address(hex_val):
    if hex_val is None or hex_val == "0x" or len(hex_val) < 3:
        return None
    clean = hex_val.replace("0x", "").lower()
    if len(clean) >= 40:
        addr = "0x" + clean[-40:]
        return addr
    return None

def encode_address(addr):
    clean = addr.replace("0x", "").lower()
    return clean.zfill(64)

def encode_uint256(val):
    return hex(val)[2:].zfill(64)

def decode_string(hex_val):
    if hex_val is None or hex_val == "0x":
        return None
    try:
        raw = bytes.fromhex(hex_val[2:])
        if len(raw) >= 64:
            offset = int.from_bytes(raw[:32], 'big')
            length = int.from_bytes(raw[32:64], 'big')
            if length < 256 and 64 + length <= len(raw):
                return raw[64:64+length].decode('utf-8', errors='replace')
        return raw.rstrip(b'\x00').decode('utf-8', errors='replace')
    except:
        return hex_val

# ── Main Probe ──────────────────────────────────────────────────────────────
print("\n" + "="*80)
print("  oneETH Protocol State Probe")
print("="*80)

results = {}
report_lines = []

def report(line):
    print(line)
    report_lines.append(line)

# Get current block info
call_id += 1
resp = requests.post(RPC_URL, json={
    "jsonrpc": "2.0",
    "method": "eth_blockNumber",
    "params": [],
    "id": call_id
}, timeout=30)
current_block = int(resp.json().get("result", "0x0"), 16)

call_id += 1
resp = requests.post(RPC_URL, json={
    "jsonrpc": "2.0",
    "method": "eth_getBlockByNumber",
    "params": ["latest", False],
    "id": call_id
}, timeout=30)
block_data = resp.json().get("result", {})
current_ts = int(block_data.get("timestamp", "0x0"), 16)
current_time = datetime.fromtimestamp(current_ts, tz=timezone.utc)

report(f"## Block Info")
report(f"- Current block: {current_block}")
report(f"- Current timestamp: {current_ts} ({current_time.isoformat()})")

# ── 1. Basic oneETH state reads ─────────────────────────────────────────
print("\n--- Reading basic oneETH state ---")
basic_calls = [
    (ONE_ETH, SELECTORS["totalSupply()"], "totalSupply"),
    (ONE_ETH, SELECTORS["reserveRatio()"], "reserveRatio"),
    (ONE_ETH, SELECTORS["MIN_RESERVE_RATIO()"], "MIN_RESERVE_RATIO"),
    (ONE_ETH, SELECTORS["withdrawFee()"], "withdrawFee"),
    (ONE_ETH, SELECTORS["mintFee()"], "mintFee"),
    (ONE_ETH, SELECTORS["stimulus()"], "stimulus"),
    (ONE_ETH, SELECTORS["gov()"], "gov"),
    (ONE_ETH, SELECTORS["lpGov()"], "lpGov"),
    (ONE_ETH, SELECTORS["oneTokenOracle()"], "oneTokenOracle"),
    (ONE_ETH, SELECTORS["stimulusOracle()"], "stimulusOracle"),
    (ONE_ETH, SELECTORS["chainLink()"], "chainLink"),
    (ONE_ETH, SELECTORS["minimumRefreshTime()"], "minimumRefreshTime"),
    (ONE_ETH, SELECTORS["reserveStepSize()"], "reserveStepSize"),
    (ONE_ETH, SELECTORS["lastRefreshReserve()"], "lastRefreshReserve"),
    (ONE_ETH, SELECTORS["getStimulusOracle()"], "getStimulusOracle"),
    (ONE_ETH, SELECTORS["getOneTokenUsd()"], "getOneTokenUsd"),
    (ONE_ETH, SELECTORS["globalCollateralValue()"], "globalCollateralValue"),
    (ONE_ETH, SELECTORS["name()"], "name"),
    (ONE_ETH, SELECTORS["symbol()"], "symbol"),
    (ONE_ETH, SELECTORS["decimals()"], "decimals"),
    (ONE_ETH, SELECTORS["owner()"], "owner"),
    (ONE_ETH, SELECTORS["paused()"], "paused"),
]

basic_results = eth_call_batch(basic_calls)

labels = [c[2] for c in basic_calls]
for i, label in enumerate(labels):
    results[label] = basic_results[i]

# Decode token info
token_name = decode_string(results.get("name"))
token_symbol = decode_string(results.get("symbol"))
token_decimals = decode_uint(results.get("decimals"))

report(f"\n## oneETH Contract: `{ONE_ETH}`")
report(f"\n### Token Info")
report(f"- Name: {token_name}")
report(f"- Symbol: {token_symbol}")
report(f"- Decimals: {token_decimals}")

total_supply_raw = decode_uint(results.get("totalSupply"))
decs = token_decimals if token_decimals is not None else 9
if total_supply_raw is not None:
    total_supply = total_supply_raw / (10 ** decs)
    report(f"- Total Supply (raw): {total_supply_raw}")
    report(f"- Total Supply: {total_supply:,.6f} {token_symbol or 'oneETH'}")
else:
    total_supply = None
    report(f"- Total Supply: FAILED TO READ")

report(f"\n### Protocol Parameters")

reserve_ratio_raw = decode_uint(results.get("reserveRatio"))
min_reserve_raw = decode_uint(results.get("MIN_RESERVE_RATIO"))
withdraw_fee_raw = decode_uint(results.get("withdrawFee"))
mint_fee_raw = decode_uint(results.get("mintFee"))
min_refresh_raw = decode_uint(results.get("minimumRefreshTime"))
reserve_step_raw = decode_uint(results.get("reserveStepSize"))
last_refresh_raw = decode_uint(results.get("lastRefreshReserve"))

report(f"- reserveRatio (raw): {reserve_ratio_raw}")
if reserve_ratio_raw is not None:
    # oneETH uses percentage * 100 or per-mille style
    # Common: 100 = 100%, or 10000 = 100%, or raw percent
    # Let's show multiple interpretations
    for label, div in [("if /1 = raw %", 1), ("if /100 = bps->%", 100), ("if /1e4", 1e4), ("if /1e6", 1e6)]:
        val = reserve_ratio_raw / div
        if 0.1 <= val <= 200:
            report(f"  - reserveRatio ({label}): {val:.4f}%")

report(f"- MIN_RESERVE_RATIO (raw): {min_reserve_raw}")
if min_reserve_raw is not None:
    for label, div in [("if /1 = raw %", 1), ("if /100 = bps->%", 100), ("if /1e4", 1e4), ("if /1e6", 1e6)]:
        val = min_reserve_raw / div
        if 0.1 <= val <= 200:
            report(f"  - MIN_RESERVE_RATIO ({label}): {val:.4f}%")

report(f"- withdrawFee (raw): {withdraw_fee_raw}")
if withdraw_fee_raw is not None:
    if withdraw_fee_raw < 10000:
        report(f"  - withdrawFee: {withdraw_fee_raw} (if bps: {withdraw_fee_raw/100:.2f}%)")
    if withdraw_fee_raw > 1e10:
        report(f"  - withdrawFee (1e18 scale): {withdraw_fee_raw / 1e18:.6f}")

report(f"- mintFee (raw): {mint_fee_raw}")
if mint_fee_raw is not None:
    if mint_fee_raw < 10000:
        report(f"  - mintFee: {mint_fee_raw} (if bps: {mint_fee_raw/100:.2f}%)")
    if mint_fee_raw > 1e10:
        report(f"  - mintFee (1e18 scale): {mint_fee_raw / 1e18:.6f}")

report(f"- minimumRefreshTime (raw): {min_refresh_raw}")
if min_refresh_raw is not None:
    report(f"  - minimumRefreshTime: {min_refresh_raw} seconds = {min_refresh_raw/3600:.2f} hours")

report(f"- reserveStepSize (raw): {reserve_step_raw}")
if reserve_step_raw is not None:
    for label, div in [("if /1", 1), ("if /100", 100), ("if /1e4", 1e4), ("if /1e6", 1e6)]:
        val = reserve_step_raw / div
        if 0.001 <= val <= 100:
            report(f"  - reserveStepSize ({label}): {val:.4f}")

report(f"- lastRefreshReserve (raw): {last_refresh_raw}")
if last_refresh_raw is not None:
    if last_refresh_raw > 1e9:  # timestamp
        try:
            lr_time = datetime.fromtimestamp(last_refresh_raw, tz=timezone.utc)
            age = current_ts - last_refresh_raw
            report(f"  - lastRefreshReserve (timestamp): {lr_time.isoformat()}")
            report(f"  - Time since last refresh: {age:,} seconds = {age/3600:.1f} hours = {age/86400:.1f} days")
        except:
            report(f"  - (could not parse as timestamp)")

report(f"\n### Key Addresses")

address_fields = ["stimulus", "gov", "lpGov", "oneTokenOracle", "stimulusOracle", "chainLink", "owner"]
for field in address_fields:
    addr = decode_address(results.get(field))
    report(f"- {field}: `{addr}`")
    results[f"{field}_addr"] = addr

paused_val = decode_uint(results.get("paused"))
report(f"- paused: {paused_val} ({'**YES - PAUSED**' if paused_val else 'No (active)' if paused_val is not None else 'N/A (no such function)'})")

report(f"\n### Oracle Return Values")

stimulus_oracle_val = decode_uint(results.get("getStimulusOracle"))
report(f"- getStimulusOracle() (raw): {stimulus_oracle_val}")
if stimulus_oracle_val is not None and stimulus_oracle_val > 0:
    report(f"  - (1e18 interpretation): {stimulus_oracle_val / 1e18:.10f}")
    report(f"  - (1e9 interpretation):  {stimulus_oracle_val / 1e9:.10f}")
    report(f"  - (1e6 interpretation):  {stimulus_oracle_val / 1e6:.10f}")

one_token_usd = decode_uint(results.get("getOneTokenUsd"))
report(f"- getOneTokenUsd() (raw): {one_token_usd}")
if one_token_usd is not None and one_token_usd > 0:
    report(f"  - (1e18 interpretation): {one_token_usd / 1e18:.10f}")
    report(f"  - (1e9 interpretation):  {one_token_usd / 1e9:.10f}")
    report(f"  - (1e6 interpretation):  {one_token_usd / 1e6:.10f}")

global_collateral_val = decode_uint(results.get("globalCollateralValue"))
report(f"- globalCollateralValue() (raw): {global_collateral_val}")
if global_collateral_val is not None and global_collateral_val > 0:
    report(f"  - (1e18 interpretation): {global_collateral_val / 1e18:,.10f}")
    report(f"  - (1e9 interpretation):  {global_collateral_val / 1e9:,.10f}")
    report(f"  - (1e6 interpretation):  {global_collateral_val / 1e6:,.10f}")

# ── 2. Collateral Array ─────────────────────────────────────────────────
print("\n--- Reading collateral array ---")
collateral_calls = []
for i in range(6):
    data = SELECTORS["collateralArray(uint256)"] + encode_uint256(i)
    collateral_calls.append((ONE_ETH, data, f"collateralArray({i})"))

collateral_results = eth_call_batch(collateral_calls)

collaterals = []
report(f"\n### Collateral Array")
for i, res in enumerate(collateral_results):
    addr = decode_address(res)
    if addr and addr != ZERO_ADDR and res is not None:
        collaterals.append(addr)
        report(f"- collateralArray({i}): `{addr}`")
    else:
        if res is None:
            report(f"- collateralArray({i}): REVERTED (index out of bounds)")
        else:
            report(f"- collateralArray({i}): `{addr}` (zero/empty)")

# ── 3. Collateral details ───────────────────────────────────────────────
collateral_oracles = {}
collateral_info = {}

if collaterals:
    print(f"\n--- Reading details for {len(collaterals)} collaterals ---")
    report(f"\n### Collateral Details")
    
    detail_calls = []
    for coll in collaterals:
        addr_enc = encode_address(coll)
        detail_calls.append((ONE_ETH, SELECTORS["acceptedCollateral(address)"] + addr_enc, f"accepted_{coll}"))
        detail_calls.append((ONE_ETH, SELECTORS["collateralDecimals(address)"] + addr_enc, f"decimals_{coll}"))
        detail_calls.append((ONE_ETH, SELECTORS["collateralOracle(address)"] + addr_enc, f"oracle_{coll}"))
        detail_calls.append((ONE_ETH, SELECTORS["getCollateralUsd(address)"] + addr_enc, f"usd_{coll}"))
        detail_calls.append((coll, SELECTORS["balanceOf(address)"] + encode_address(ONE_ETH), f"balance_{coll}"))
        detail_calls.append((coll, SELECTORS["symbol()"], f"symbol_{coll}"))
        detail_calls.append((coll, SELECTORS["decimals()"], f"token_decimals_{coll}"))
        detail_calls.append((coll, SELECTORS["name()"], f"name_{coll}"))
    
    detail_results = eth_call_batch(detail_calls)
    
    idx = 0
    for coll in collaterals:
        accepted = decode_uint(detail_results[idx])
        coll_decimals = decode_uint(detail_results[idx+1])
        oracle_addr = decode_address(detail_results[idx+2])
        usd_val = decode_uint(detail_results[idx+3])
        balance = decode_uint(detail_results[idx+4])
        sym = decode_string(detail_results[idx+5])
        tok_dec = decode_uint(detail_results[idx+6])
        tok_name = decode_string(detail_results[idx+7])
        
        if oracle_addr and oracle_addr != ZERO_ADDR:
            collateral_oracles[coll] = oracle_addr
        
        report(f"\n#### Collateral: `{coll}` ({sym or '?'})")
        report(f"  - Name: {tok_name}")
        report(f"  - Symbol: {sym}")
        report(f"  - Token Decimals: {tok_dec}")
        report(f"  - acceptedCollateral: {accepted} ({'YES' if accepted else 'NO'})")
        report(f"  - collateralDecimals (oneETH view): {coll_decimals}")
        report(f"  - collateralOracle: `{oracle_addr}`")
        report(f"  - getCollateralUsd (raw): {usd_val}")
        if usd_val is not None and usd_val > 0:
            report(f"    - (1e18): {usd_val / 1e18:,.10f}")
            report(f"    - (1e9):  {usd_val / 1e9:,.10f}")
            report(f"    - (1e6):  {usd_val / 1e6:,.10f}")
        report(f"  - Balance in oneETH contract (raw): {balance}")
        if balance is not None and tok_dec is not None and tok_dec > 0:
            bal_human = balance / (10 ** tok_dec)
            report(f"  - Balance in oneETH contract: {bal_human:,.6f} {sym or ''}")
        elif balance is not None:
            report(f"  - Balance in oneETH contract (raw units): {balance}")
        
        collateral_info[coll] = {
            "symbol": sym,
            "tok_decimals": tok_dec,
            "accepted": accepted,
            "coll_decimals": coll_decimals,
            "oracle": oracle_addr,
            "usd_val": usd_val,
            "balance": balance,
        }
        
        idx += 8

# ── 4. WETH and USDC balances ───────────────────────────────────────────
print("\n--- Reading WETH/USDC balances ---")
token_balance_calls = [
    (WETH, SELECTORS["balanceOf(address)"] + encode_address(ONE_ETH), "WETH_balance"),
    (USDC, SELECTORS["balanceOf(address)"] + encode_address(ONE_ETH), "USDC_balance"),
]
token_balance_results = eth_call_batch(token_balance_calls)

weth_balance = decode_uint(token_balance_results[0])
usdc_balance = decode_uint(token_balance_results[1])

report(f"\n### Key Token Balances in oneETH Contract")
report(f"- WETH (`{WETH}`):")
report(f"  - Raw: {weth_balance}")
if weth_balance is not None:
    report(f"  - Human: {weth_balance / 1e18:,.6f} WETH")

report(f"- USDC (`{USDC}`):")
report(f"  - Raw: {usdc_balance}")
if usdc_balance is not None:
    report(f"  - Human: {usdc_balance / 1e6:,.6f} USDC")

# ── 5. Oracle pair exploration ──────────────────────────────────────────
print("\n--- Exploring oracle pairs ---")
report(f"\n## Oracle Pair Analysis")

one_token_oracle = results.get("oneTokenOracle_addr")
stimulus_oracle_a = results.get("stimulusOracle_addr")

oracle_addresses = {}
if one_token_oracle and one_token_oracle != ZERO_ADDR:
    oracle_addresses["oneTokenOracle"] = one_token_oracle
if stimulus_oracle_a and stimulus_oracle_a != ZERO_ADDR:
    oracle_addresses["stimulusOracle"] = stimulus_oracle_a
for coll, oracle in collateral_oracles.items():
    if oracle and oracle != ZERO_ADDR:
        coll_sym = collateral_info.get(coll, {}).get("symbol", coll[:10])
        oracle_addresses[f"collateralOracle({coll_sym})"] = oracle

for oracle_name, oracle_addr in oracle_addresses.items():
    report(f"\n### Oracle: {oracle_name} (`{oracle_addr}`)")
    
    # Read pair() and oracle state in one batch
    oracle_batch = [
        (oracle_addr, SELECTORS["pair()"], "pair"),
        (oracle_addr, SELECTORS["blockTimestampLast()"], "blockTimestampLast"),
        (oracle_addr, SELECTORS["price0CumulativeLast()"], "price0CumulativeLast"),
        (oracle_addr, SELECTORS["price1CumulativeLast()"], "price1CumulativeLast"),
        (oracle_addr, SELECTORS["lastUpdateTime()"], "lastUpdateTime"),
        (oracle_addr, SELECTORS["owner()"], "oracle_owner"),
    ]
    oracle_batch_results = eth_call_batch(oracle_batch)
    
    pair_addr = decode_address(oracle_batch_results[0])
    block_ts_last = decode_uint(oracle_batch_results[1])
    p0_cum = decode_uint(oracle_batch_results[2])
    p1_cum = decode_uint(oracle_batch_results[3])
    last_update = decode_uint(oracle_batch_results[4])
    oracle_owner = decode_address(oracle_batch_results[5])
    
    report(f"- pair(): `{pair_addr}`")
    if oracle_owner:
        report(f"- owner: `{oracle_owner}`")
    
    oracle_age = None
    if block_ts_last and block_ts_last > 1e9:
        oracle_age = current_ts - block_ts_last
        try:
            report(f"- blockTimestampLast: {block_ts_last} ({datetime.fromtimestamp(block_ts_last, tz=timezone.utc).isoformat()})")
            report(f"- Oracle data age: {oracle_age:,} sec = {oracle_age/3600:.1f} hrs = {oracle_age/86400:.1f} days")
        except:
            report(f"- blockTimestampLast: {block_ts_last}")
    
    if last_update and last_update > 1e9:
        age2 = current_ts - last_update
        try:
            report(f"- lastUpdateTime: {last_update} ({datetime.fromtimestamp(last_update, tz=timezone.utc).isoformat()})")
            report(f"- Since last update: {age2:,} sec = {age2/86400:.1f} days")
        except:
            report(f"- lastUpdateTime: {last_update}")
    
    if p0_cum is not None:
        report(f"- price0CumulativeLast: {p0_cum}")
    if p1_cum is not None:
        report(f"- price1CumulativeLast: {p1_cum}")
    
    if pair_addr and pair_addr != ZERO_ADDR:
        # Read pair details
        pair_calls = [
            (pair_addr, SELECTORS["getReserves()"], "reserves"),
            (pair_addr, SELECTORS["token0()"], "token0"),
            (pair_addr, SELECTORS["token1()"], "token1"),
        ]
        pair_results_data = eth_call_batch(pair_calls)
        
        reserves_hex = pair_results_data[0]
        token0 = decode_address(pair_results_data[1])
        token1 = decode_address(pair_results_data[2])
        
        report(f"\n  **Uniswap Pair: `{pair_addr}`**")
        report(f"  - token0: `{token0}`")
        report(f"  - token1: `{token1}`")
        
        if reserves_hex and len(reserves_hex) >= 130:
            raw = reserves_hex[2:]
            reserve0 = int(raw[0:64], 16)
            reserve1 = int(raw[64:128], 16)
            ts_last_pair = int(raw[128:192], 16) if len(raw) >= 192 else 0
            
            # Get token info
            tok_info_calls = [
                (token0, SELECTORS["symbol()"], "t0_sym"),
                (token0, SELECTORS["decimals()"], "t0_dec"),
                (token1, SELECTORS["symbol()"], "t1_sym"),
                (token1, SELECTORS["decimals()"], "t1_dec"),
            ]
            tok_info = eth_call_batch(tok_info_calls)
            
            t0_sym = decode_string(tok_info[0]) or "token0"
            t0_dec = decode_uint(tok_info[1]) or 18
            t1_sym = decode_string(tok_info[2]) or "token1"
            t1_dec = decode_uint(tok_info[3]) or 18
            
            r0_human = reserve0 / (10 ** t0_dec)
            r1_human = reserve1 / (10 ** t1_dec)
            
            report(f"  - reserve0 (raw): {reserve0}")
            report(f"  - reserve1 (raw): {reserve1}")
            report(f"  - reserve0: {r0_human:,.6f} {t0_sym}")
            report(f"  - reserve1: {r1_human:,.6f} {t1_sym}")
            
            if reserve0 > 0 and reserve1 > 0:
                price_0_in_1 = r1_human / r0_human
                price_1_in_0 = r0_human / r1_human
                report(f"  - Spot price {t0_sym}/{t1_sym}: {price_0_in_1:,.10f}")
                report(f"  - Spot price {t1_sym}/{t0_sym}: {price_1_in_0:,.10f}")
                
                k = reserve0 * reserve1
                report(f"  - k (constant product): {k:.2e}")
                report(f"  - sqrt(k): {k**0.5:,.2f}")
                
                # Liquidity depth: amount needed for 1% / 5% / 10% price impact
                import math
                for pct in [1, 5, 10]:
                    # To move price by p%, need to add dx such that new_price = (1+p%) * old_price
                    # In x*y=k AMM: to increase price by p%, add dx = x*(sqrt(1+p%)-1)
                    factor = math.sqrt(1 + pct/100) - 1
                    dx = r0_human * factor
                    dy = r1_human * factor
                    report(f"  - ~{pct}% price impact: ~{dx:,.4f} {t0_sym} or ~{dy:,.4f} {t1_sym}")
            
            if ts_last_pair > 1e9:
                age_pair = current_ts - ts_last_pair
                try:
                    report(f"  - Pair last trade: {datetime.fromtimestamp(ts_last_pair, tz=timezone.utc).isoformat()} ({age_pair:,} sec ago = {age_pair/86400:.1f} days)")
                except:
                    report(f"  - Pair last trade timestamp: {ts_last_pair}")
        else:
            report(f"  - getReserves(): {reserves_hex}")

# ── 6. Solvency Analysis ────────────────────────────────────────────────
print("\n--- Computing solvency analysis ---")
report(f"\n## Solvency Analysis")

if total_supply_raw is not None:
    report(f"\n### Supply")
    report(f"- Total Supply (raw): {total_supply_raw}")
    report(f"- Total Supply ({decs} decimals): {total_supply_raw / (10**decs):,.6f} oneETH")

if global_collateral_val is not None:
    report(f"\n### Collateral Value")
    report(f"- globalCollateralValue (raw): {global_collateral_val}")
    for d in [6, 9, 18]:
        report(f"  - {d}-decimal interpretation: {global_collateral_val / (10**d):,.6f}")

if global_collateral_val is not None and total_supply_raw is not None and total_supply_raw > 0:
    report(f"\n### Solvency Ratio")
    ratio = (global_collateral_val / total_supply_raw) * 100
    report(f"- Collateral / Supply ratio (raw): {ratio:.4f}%")
    report(f"  - This means: for every 1 oneETH of supply, there is {global_collateral_val / total_supply_raw:.6f} units of collateral value")
    
    if ratio < 100:
        report(f"- **UNDERCOLLATERALIZED**: Only {ratio:.2f}% backed")
    else:
        report(f"- OVERCOLLATERALIZED: {ratio:.2f}% backed")

# Reserve ratio
report(f"\n### Reserve Ratio Status")
if reserve_ratio_raw is not None and min_reserve_raw is not None:
    report(f"- Current reserve ratio: {reserve_ratio_raw}")
    report(f"- Minimum reserve ratio: {min_reserve_raw}")
    if reserve_ratio_raw == min_reserve_raw:
        report(f"- Status: **AT MINIMUM** - protocol has reduced collateral ratio to the floor")
    elif reserve_ratio_raw > min_reserve_raw:
        pct_above = ((reserve_ratio_raw - min_reserve_raw) / min_reserve_raw) * 100
        report(f"- Status: ABOVE MINIMUM by {reserve_ratio_raw - min_reserve_raw} ({pct_above:.2f}% above floor)")
    else:
        report(f"- Status: **BELOW MINIMUM** - anomalous state!")

# ── 7. Activity Check ───────────────────────────────────────────────────
print("\n--- Checking recent activity ---")
report(f"\n## Activity Check")

transfer_topic_full = SELECTORS.get("Transfer(address,address,uint256)_full")
if not transfer_topic_full:
    # Recompute
    transfer_topic_full = rpc_keccak("Transfer(address,address,uint256)")

# Try last 10000 blocks first
for window_name, window_size in [("~10K blocks (~1.5 days)", 10000), ("~100K blocks (~15 days)", 100000), ("~1M blocks (~150 days)", 1000000)]:
    call_id += 1
    from_block = hex(max(0, current_block - window_size))
    try:
        resp = requests.post(RPC_URL, json={
            "jsonrpc": "2.0",
            "method": "eth_getLogs",
            "params": [{
                "address": ONE_ETH,
                "fromBlock": from_block,
                "toBlock": "latest",
                "topics": [transfer_topic_full]
            }],
            "id": call_id
        }, timeout=30)
        log_result = resp.json()
        
        if "result" in log_result:
            logs = log_result["result"]
            report(f"- Transfer events in {window_name}: {len(logs)}")
            if logs:
                last_log = logs[-1]
                last_block = int(last_log["blockNumber"], 16)
                blocks_ago = current_block - last_block
                days_ago = blocks_ago * 12 / 86400
                report(f"  - Most recent Transfer at block {last_block} ({blocks_ago} blocks / ~{days_ago:.1f} days ago)")
                if len(logs) <= 5:
                    for j, lg in enumerate(logs[-5:]):
                        lb = int(lg["blockNumber"], 16)
                        ba = current_block - lb
                        da = ba * 12 / 86400
                        val_raw = decode_uint(lg.get("data", "0x"))
                        val_str = f" | value(raw)={val_raw}" if val_raw else ""
                        report(f"    - Event {j}: block {lb} (~{da:.1f} days ago){val_str}")
                break  # Found events, stop searching
            else:
                if window_size >= 1000000:
                    report(f"- **NO Transfer events found in last {window_name}** -- protocol appears INACTIVE")
                # continue to wider window
        else:
            err_msg = log_result.get("error", {}).get("message", "unknown")
            report(f"- Log query ({window_name}) error: {err_msg}")
            if "range" in err_msg.lower() or "limit" in err_msg.lower():
                report(f"  - (range too wide for provider, trying smaller)")
                continue
            break
    except Exception as e:
        report(f"- Log query ({window_name}) exception: {e}")
        break

# ── 8. Summary & Interpretation ─────────────────────────────────────────
report(f"\n## Summary & Interpretation")

report(f"\n### Key Findings")

# 1. Protocol liveness
report(f"\n**1. Protocol Liveness:**")
if paused_val:
    report(f"   - Protocol is PAUSED. No minting/withdrawing possible.")
elif paused_val == 0:
    report(f"   - Protocol is NOT paused (contract-level).")
else:
    report(f"   - Pause status unknown (no paused() function or reverted).")

# 2. Supply analysis
report(f"\n**2. Supply:**")
if total_supply_raw is not None:
    if total_supply_raw == 0:
        report(f"   - Total supply is ZERO. Protocol has been fully redeemed or never used.")
    else:
        report(f"   - Total supply: {total_supply_raw / (10**decs):,.6f} oneETH")

# 3. Collateral backing
report(f"\n**3. Collateral Backing:**")
if global_collateral_val is not None:
    if global_collateral_val == 0:
        report(f"   - Global collateral value is ZERO.")
    else:
        report(f"   - Global collateral value (raw): {global_collateral_val}")

# 4. Reserve ratio
report(f"\n**4. Reserve Ratio:**")
if reserve_ratio_raw is not None:
    report(f"   - Current: {reserve_ratio_raw} | Min: {min_reserve_raw}")
    if reserve_ratio_raw == min_reserve_raw:
        report(f"   - AT MINIMUM: The protocol has algorithmically reduced collateral backing to the floor.")
        report(f"   - This means maximum stimulus token exposure / minimum USDC/ETH backing.")

# 5. Fees
report(f"\n**5. Fees:**")
report(f"   - Withdraw fee: {withdraw_fee_raw}")
report(f"   - Mint fee: {mint_fee_raw}")

# 6. Oracle freshness warning
report(f"\n**6. Oracle Freshness:**")
report(f"   - If TWAP oracles have not been updated in days/weeks, prices are severely stale.")
report(f"   - Stale TWAP = current spot has outsized influence or price is frozen.")
report(f"   - This is a critical manipulation vector if liquidity in oracle pairs is low.")

# 7. Manipulation feasibility
report(f"\n**7. Oracle Manipulation Feasibility:**")
report(f"   - Assess by checking oracle pair reserves above.")
report(f"   - Low reserves (< $10K equivalent) = trivially manipulable with flash loans.")
report(f"   - If the oracle pair has not traded in days, the TWAP is frozen at an old price.")
report(f"   - If stimulus token liquidity is near zero, stimulus oracle can be moved to any price.")

report(f"\n---")
report(f"*Probe completed at {datetime.now(tz=timezone.utc).isoformat()}*")
report(f"*Total RPC calls: {call_id}*")

# ── Write report ────────────────────────────────────────────────────────
print(f"\n--- Writing report to {OUTPUT_PATH} ---")

with open(OUTPUT_PATH, "w") as f:
    f.write(f"# oneETH Protocol On-Chain State Probe\n\n")
    f.write(f"**Generated:** {current_time.isoformat()}  \n")
    f.write(f"**Contract:** `{ONE_ETH}`  \n")
    f.write(f"**Chain:** Ethereum Mainnet (chain_id=1)  \n")
    f.write(f"**Block:** {current_block}  \n\n")
    f.write(f"---\n\n")
    for line in report_lines:
        f.write(line + "\n")

print(f"\nDone! Report saved to: {OUTPUT_PATH}")
print(f"Total RPC calls: {call_id}")
