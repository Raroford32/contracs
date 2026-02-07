#!/usr/bin/env python3
"""
Deep Vault Analysis - Per CLAUDE.md methodology
Focus on first depositor, donation, and share inflation attacks
"""
import json
import subprocess
import time
import re

RPC = "https://mainnet.infura.io/v3/bfc7283659224dd6b5124ebbc2b14e2c"
ETHERSCAN_API = "5UWN6DNT7UZCEJYNE3J6FCVAWH4QJW255K"

def rpc_call(method, params):
    payload = {"jsonrpc": "2.0", "method": method, "params": params, "id": 1}
    cmd = ["curl", "-s", "-X", "POST", "-H", "Content-Type: application/json",
           "-d", json.dumps(payload), RPC]
    result = subprocess.run(cmd, capture_output=True, text=True)
    try:
        return json.loads(result.stdout)
    except:
        return None

def eth_call(to, data, from_addr="0x0000000000000000000000000000000000000001"):
    result = rpc_call("eth_call", [{"to": to, "data": data, "from": from_addr}, "latest"])
    if result and 'result' in result:
        return result['result']
    return result.get('error', {}).get('message', '') if result else None

def estimate_gas(to, data, from_addr="0x0000000000000000000000000000000000000001", value="0x0"):
    result = rpc_call("eth_estimateGas", [{"to": to, "data": data, "from": from_addr, "value": value}])
    return result

def get_balance(addr):
    result = rpc_call("eth_getBalance", [addr, "latest"])
    if result and 'result' in result:
        return int(result['result'], 16) / 1e18
    return 0

def get_storage(addr, slot):
    result = rpc_call("eth_getStorageAt", [addr, slot, "latest"])
    if result and 'result' in result:
        return result['result']
    return None

def get_source(addr):
    url = f"https://api.etherscan.io/v2/api?chainid=1&module=contract&action=getsourcecode&address={addr}&apikey={ETHERSCAN_API}"
    result = subprocess.run(["curl", "-s", url], capture_output=True, text=True)
    try:
        data = json.loads(result.stdout)
        if data.get("status") == "1" and data.get("result"):
            return data["result"][0]
    except:
        pass
    return None

# High-priority targets from vault scan
targets = [
    {"address": "0xd48b633045af65ff636f3c6edd744748f39c5a39", "name": "Zethr", "balance": 280.8},
    {"address": "0xd619c8da0a64e06bdd5ee614ae43dc3fe31f2fa1", "name": "CycloneV2dot2", "balance": 200.0},
    {"address": "0xf944093004f847a7ad1222c937eb4e96d9e83ced", "name": "Vyper_contract", "balance": 72.2},
    {"address": "0xb9ab8eed48852de901c13543042204c6c569b811", "name": "Zethr2", "balance": 116.1},
    {"address": "0x899f9a0440face1397a1ee1e3f6bf3580a6633d1", "name": "RedemptionContract", "balance": 206.25},
    {"address": "0x5eee354e36ac51e9d3f7283005cab0c55f423b23", "name": "ArbitrageETHStaking", "balance": 216.3},
    {"address": "0x9b4ea303ca2d81e4cb1ce15846baaca8ba2ac8ef", "name": "auto_pool", "balance": 128.7},
]

print("=" * 80)
print("DEEP VAULT ANALYSIS - FIRST DEPOSITOR & DONATION ATTACKS")
print("=" * 80)

for target in targets:
    addr = target['address']
    name = target['name']

    print(f"\n{'='*70}")
    print(f"[TARGET] {name} ({addr})")
    print(f"[BALANCE] {get_balance(addr):.2f} ETH")
    print("=" * 70)

    time.sleep(0.3)
    source_data = get_source(addr)

    if not source_data:
        print("  No verified source")
        continue

    src = source_data.get("SourceCode", "")

    # Parse multi-file
    if src.startswith("{{"):
        try:
            src_json = json.loads(src[1:-1])
            sources = src_json.get("sources", {})
            src = "\n".join([v.get("content", "") for v in sources.values()])
        except:
            pass
    elif src.startswith("{"):
        try:
            src_json = json.loads(src)
            sources = src_json.get("sources", {})
            src = "\n".join([v.get("content", "") for v in sources.values()])
        except:
            pass

    print(f"  Source length: {len(src)} chars")

    # 1. FIND DEPOSIT/MINT FUNCTIONS
    print("\n  [1] Deposit/Mint Functions:")

    deposit_patterns = [
        (r"function\s+deposit\s*\([^)]*\)", "deposit"),
        (r"function\s+mint\s*\([^)]*\)", "mint"),
        (r"function\s+stake\s*\([^)]*\)", "stake"),
        (r"function\s+buy\s*\([^)]*\)", "buy"),
    ]

    for pattern, func_type in deposit_patterns:
        matches = re.findall(pattern, src, re.IGNORECASE)
        if matches:
            for m in matches[:2]:
                print(f"      Found: {m[:60]}...")

    # 2. FIND SHARE CALCULATION
    print("\n  [2] Share Calculation Logic:")

    share_patterns = [
        r"shares\s*=\s*[^;]+",
        r"amount\s*\*\s*totalSupply[^;]*",
        r"amount\s*/\s*totalSupply[^;]*",
        r"convertToShares\s*\([^)]+\)",
        r"convertToAssets\s*\([^)]+\)",
    ]

    for pattern in share_patterns:
        matches = re.findall(pattern, src, re.IGNORECASE)
        if matches:
            for m in matches[:2]:
                print(f"      {m[:70].strip()}")

    # 3. CHECK FOR EMPTY STATE HANDLING
    print("\n  [3] Empty State Protection:")

    empty_checks = [
        "totalSupply == 0",
        "totalSupply() == 0",
        "_totalSupply == 0",
        "supply == 0",
        "totalSupply > 0",
    ]

    has_empty_check = False
    for check in empty_checks:
        if check in src:
            print(f"      Found: {check}")
            has_empty_check = True

    if not has_empty_check:
        print("      [!] NO EMPTY STATE CHECK FOUND")

    # 4. ANALYZE DIVISION OPERATIONS
    print("\n  [4] Division in Share Calculations:")

    lines = src.split('\n')
    for i, line in enumerate(lines):
        if ('/' in line and ('amount' in line.lower() or 'shares' in line.lower()
            or 'totalsupply' in line.lower() or 'totalassets' in line.lower())):
            # Check if it's inside a share calculation context
            if any(x in line.lower() for x in ['return', '=', '*']):
                print(f"      Line {i+1}: {line.strip()[:70]}")

    # 5. CHECK FOR DONATION PROTECTION
    print("\n  [5] Donation Attack Protection:")

    donation_protections = [
        "internal accounting",
        "_totalAssets",
        "storedBalance",
        "lastBalance",
        "balanceTracker",
    ]

    has_donation_protection = False
    for prot in donation_protections:
        if prot.lower() in src.lower():
            print(f"      Found protection: {prot}")
            has_donation_protection = True

    if not has_donation_protection:
        if "balanceof(address(this))" in src.lower():
            print("      [!] Uses balanceOf(address(this)) - DONATION VULNERABLE")

    # 6. TRY ACTUAL CALLS
    print("\n  [6] On-Chain State:")

    # totalSupply
    ts = eth_call(addr, "0x18160ddd")
    if ts and ts != "0x" and len(ts) >= 66:
        try:
            total_supply = int(ts, 16)
            print(f"      totalSupply: {total_supply}")
        except:
            pass

    # totalAssets (ERC4626)
    ta = eth_call(addr, "0x01e1d114")
    if ta and ta != "0x" and len(ta) >= 66:
        try:
            total_assets = int(ta, 16)
            print(f"      totalAssets: {total_assets}")
        except:
            pass

    # owner
    owner = eth_call(addr, "0x8da5cb5b")
    if owner and owner != "0x" and len(owner) == 66:
        owner_addr = "0x" + owner[26:]
        print(f"      owner: {owner_addr}")

    # Check storage slots
    for slot in range(5):
        slot_val = get_storage(addr, hex(slot))
        if slot_val and slot_val != "0x" + "0"*64:
            print(f"      Slot {slot}: {slot_val}")

    # 7. TEST FUNCTION ACCESSIBILITY
    print("\n  [7] Function Accessibility Tests:")

    test_selectors = {
        "deposit()": "0xd0e30db0",
        "withdraw()": "0x3ccfd60b",
        "redeem(uint256)": "0xdb006a75",
        "mint(uint256)": "0xa0712d68",
        "buy()": "0xa6f2ae3a",
        "sell(uint256)": "0xe4849b32",
    }

    for func_name, selector in test_selectors.items():
        # Pad with dummy data for functions with args
        data = selector
        if "uint256" in func_name:
            data = selector + "0000000000000000000000000000000000000000000000000000000000000001"

        result = estimate_gas(addr, data, value="0x1" if "deposit" in func_name or "buy" in func_name else "0x0")
        if result and 'result' in result:
            gas = int(result['result'], 16)
            if gas < 500000:
                print(f"      [+] {func_name} callable - gas: {gas}")
        elif result and 'error' in result:
            err = result['error'].get('message', '')[:50]
            if 'revert' not in err.lower():
                print(f"      {func_name}: {err}")

print("\n" + "=" * 80)
print("DEEP ANALYSIS COMPLETE")
print("=" * 80)
