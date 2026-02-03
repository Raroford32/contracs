#!/usr/bin/env python3
"""
Analyze contract 0xaec2e87e0a235266d9c5adc9deb4b2e29b54d009
- 104.39 ETH
- deposit() callable at 21564 gas
"""
import json
import subprocess
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

def get_storage(addr, slot):
    result = rpc_call("eth_getStorageAt", [addr, slot, "latest"])
    if result and 'result' in result:
        return result['result']
    return None

def get_code(addr):
    result = rpc_call("eth_getCode", [addr, "latest"])
    if result and 'result' in result:
        return result['result']
    return "0x"

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

print("=" * 80)
print("CONTRACT ANALYSIS - 0xaec2e87e0...")
print("=" * 80)

TARGET = "0xaec2e87e0a235266d9c5adc9deb4b2e29b54d009"

print(f"\n[CONTRACT] {TARGET}")
print(f"[BALANCE] {get_balance(TARGET):.4f} ETH")

# Check bytecode length
code = get_code(TARGET)
print(f"[BYTECODE LENGTH] {len(code)} chars")

# Check for Parity pattern
test_selectors = [
    ("0x8da5cb5b", "owner()"),
    ("0x12345678", "random1()"),
    ("0x87654321", "random2()"),
    ("0xabcdef12", "random3()"),
]

print("\n[PARITY CHECK - Gas variance]")
gas_vals = []
for sel, name in test_selectors:
    result = estimate_gas(TARGET, sel)
    if result and 'result' in result:
        gas = int(result['result'], 16)
        gas_vals.append(gas)
        print(f"  {name}: {gas}")
    elif result and 'error' in result:
        gas_vals.append(-1)
        print(f"  {name}: ERROR")

positive = [g for g in gas_vals if g > 0]
if len(positive) >= 2:
    variance = max(positive) - min(positive)
    avg = sum(positive) / len(positive)
    pct = (variance / avg * 100) if avg > 0 else 0
    print(f"  Variance: {pct:.1f}%")
    if pct < 15:
        print("  [!] PARITY WALLET PATTERN")

# Get source
source_data = get_source(TARGET)
if source_data:
    src = source_data.get("SourceCode", "")
    contract_name = source_data.get("ContractName", "Unknown")
    abi = source_data.get("ABI", "")
    print(f"\n[CONTRACT NAME] {contract_name}")
    print(f"[SOURCE LENGTH] {len(src)} chars")

    if src.startswith("{{"):
        try:
            src_json = json.loads(src[1:-1])
            sources = src_json.get("sources", {})
            src = "\n".join([v.get("content", "") for v in sources.values()])
        except:
            pass

    if len(src) < 10000 and src:
        lines = src.split('\n')
        print("\n[FULL SOURCE]")
        for i, line in enumerate(lines):
            print(f"  {i+1:3}: {line}")

    # Parse ABI
    if abi:
        print("\n[ABI FUNCTIONS]")
        try:
            abi_json = json.loads(abi)
            for item in abi_json:
                if item.get("type") == "function":
                    name = item.get("name", "")
                    inputs = item.get("inputs", [])
                    stateMutability = item.get("stateMutability", "")
                    input_types = ",".join([i.get("type", "") for i in inputs])
                    print(f"  {name}({input_types}) - {stateMutability}")
        except:
            pass

# Storage
print("\n[STORAGE]")
for i in range(10):
    val = get_storage(TARGET, hex(i))
    if val and val != "0x" + "0"*64:
        print(f"  Slot {i}: {val}")

# Test specific functions
print("\n[FUNCTION TESTS]")
tests = [
    ("0xd0e30db0", "deposit()", "0xde0b6b3a7640000"),
    ("0x3ccfd60b", "withdraw()", "0x0"),
    ("0x18160ddd", "totalSupply()", "0x0"),
    ("0x8da5cb5b", "owner()", "0x0"),
]

for sel, name, value in tests:
    result = estimate_gas(TARGET, sel, value=value)
    if result:
        if 'result' in result:
            gas = int(result['result'], 16)
            print(f"  [+] {name} - gas: {gas}")

            # Get return value
            call_result = eth_call(TARGET, sel, value=value)
            if call_result and call_result.get('result'):
                print(f"      Return: {call_result['result'][:66]}")
        elif 'error' in result:
            err = result['error'].get('message', '')[:50]
            print(f"  [-] {name}: {err}")

print("\n" + "=" * 80)
