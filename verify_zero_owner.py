#!/usr/bin/env python3
"""
Verify if zero-owner contracts are exploitable or Parity wallets
"""
import json
import subprocess

RPC = "https://mainnet.infura.io/v3/bfc7283659224dd6b5124ebbc2b14e2c"

def rpc_call(method, params):
    payload = {"jsonrpc": "2.0", "method": method, "params": params, "id": 1}
    cmd = ["curl", "-s", "-X", "POST", "-H", "Content-Type: application/json",
           "-d", json.dumps(payload), RPC]
    result = subprocess.run(cmd, capture_output=True, text=True)
    try:
        return json.loads(result.stdout)
    except:
        return None

def eth_call(to, data, from_addr="0x0000000000000000000000000000000000000001", value="0x0"):
    result = rpc_call("eth_call", [{"to": to, "data": data, "from": from_addr, "value": value}, "latest"])
    return result

def estimate_gas(to, data, from_addr="0x0000000000000000000000000000000000000001", value="0x0"):
    result = rpc_call("eth_estimateGas", [{"to": to, "data": data, "from": from_addr, "value": value}])
    return result

def get_balance(addr):
    result = rpc_call("eth_getBalance", [addr, "latest"])
    if result and 'result' in result:
        return int(result['result'], 16) / 1e18
    return 0

def get_code(addr):
    result = rpc_call("eth_getCode", [addr, "latest"])
    if result and 'result' in result:
        return result['result']
    return "0x"

print("=" * 80)
print("VERIFYING ZERO OWNER CONTRACTS")
print("=" * 80)

# Zero owner contracts found
targets = [
    "0xbd6ed4969d9e52032e4a8e88df46aadec6d60e4e",  # 301 ETH
    "0x3885b0c18e3c4ab0ca23abb2b4ec8cda40e05178",  # 250 ETH
    "0x4615cc10092b514258ba48a2bf44e1d8b09b9b8b",  # 232.6 ETH
    "0x5eee354e36ac51e9d3f7283005cab0c55f423b23",  # 216.3 ETH (ArbitrageETHStaking)
    "0xddf90e79af4e0ece885a0050f7c83e549b6a8b4b",  # 159.9 ETH
]

for addr in targets:
    print(f"\n{'='*70}")
    print(f"[CONTRACT] {addr}")
    print(f"[BALANCE] {get_balance(addr):.4f} ETH")
    print("=" * 70)

    # Get code
    code = get_code(addr)
    print(f"Code length: {len(code)} chars")

    # Check for Parity pattern
    if len(code) < 200:
        print("[!] SHORT CODE - Likely Parity wallet proxy")

    # Test various function selectors to see if they all return same gas (echo pattern)
    test_selectors = [
        ("0x8da5cb5b", "owner()"),
        ("0x3ccfd60b", "withdraw()"),
        ("0x12345678", "randomFunc1()"),
        ("0x87654321", "randomFunc2()"),
        ("0xabcdef12", "randomFunc3()"),
        ("0xb61d27f6", "execute(address,uint256,bytes)"),  # Parity execute
    ]

    gas_values = []
    print("\n[GAS ESTIMATES]")
    for selector, name in test_selectors:
        data = selector
        if "execute" in name:
            # Add params
            data += "0" * 64 + "0" * 64 + "0" * 64

        result = estimate_gas(addr, data)
        if result and 'result' in result:
            gas = int(result['result'], 16)
            gas_values.append(gas)
            print(f"  {name}: {gas}")
        elif result and 'error' in result:
            gas_values.append(-1)
            err = result['error'].get('message', '')[:40]
            print(f"  {name}: ERROR - {err}")

    # Check if echo pattern (all similar gas)
    positive_gas = [g for g in gas_values if g > 0]
    if len(positive_gas) >= 3:
        avg = sum(positive_gas) / len(positive_gas)
        variance = max(positive_gas) - min(positive_gas)
        variance_pct = (variance / avg * 100) if avg > 0 else 0

        print(f"\n[PATTERN ANALYSIS]")
        print(f"  Gas variance: {variance_pct:.1f}%")
        if variance_pct < 15:
            print("  [!] PARITY WALLET - Echo pattern detected")
        else:
            print("  [*] REAL CONTRACT - Different functions have different gas")

            # This could be exploitable! Test withdraw
            print("\n  [TESTING WITHDRAW]")
            withdraw_data = "0x3ccfd60b"
            result = eth_call(addr, withdraw_data)
            if result:
                print(f"    Result: {result}")

print("\n" + "=" * 80)
print("VERIFICATION COMPLETE")
print("=" * 80)
