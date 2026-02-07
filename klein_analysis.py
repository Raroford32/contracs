#!/usr/bin/env python3
"""
Analyze Klein contract for reentrancy
- 128.5 ETH
- buy() has transfer BEFORE state updates
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
print("KLEIN CONTRACT REENTRANCY ANALYSIS")
print("=" * 80)

TARGET = "0x88ae96845e157558ef59e9ff90e766e22e480390"

print(f"\n[CONTRACT] {TARGET}")
print(f"[BALANCE] {get_balance(TARGET):.4f} ETH")

# Check bytecode for Parity pattern
code = get_code(TARGET)
print(f"[BYTECODE LENGTH] {len(code)} chars")

# Quick Parity check
test_selectors = [
    ("0x8da5cb5b", "owner()"),
    ("0x12345678", "random1()"),
    ("0x87654321", "random2()"),
]

print("\n[PARITY CHECK]")
gas_vals = []
for sel, name in test_selectors:
    result = estimate_gas(TARGET, sel)
    if result and 'result' in result:
        gas = int(result['result'], 16)
        gas_vals.append(gas)
        print(f"  {name}: {gas}")

positive = [g for g in gas_vals if g > 0]
if len(positive) >= 2:
    variance = max(positive) - min(positive)
    avg = sum(positive) / len(positive)
    pct = (variance / avg * 100) if avg > 0 else 0
    print(f"  Variance: {pct:.1f}%")
    if pct < 15:
        print("  [!] PARITY WALLET PATTERN - Not exploitable")

# Get source
source_data = get_source(TARGET)
if source_data:
    src = source_data.get("SourceCode", "")
    contract_name = source_data.get("ContractName", "Unknown")
    print(f"\n[CONTRACT NAME] {contract_name}")

    if src.startswith("{{"):
        try:
            src_json = json.loads(src[1:-1])
            sources = src_json.get("sources", {})
            src = "\n".join([v.get("content", "") for v in sources.values()])
        except:
            pass

    lines = src.split('\n')

    # Find buy function
    print("\n" + "=" * 60)
    print("[BUY FUNCTION]")
    print("=" * 60)

    for i, line in enumerate(lines):
        if re.search(r"function\s+buy\s*\(", line, re.IGNORECASE):
            print(f"\n  Found at line {i+1}:")
            for j in range(i, min(i+50, len(lines))):
                print(f"    {j+1}: {lines[j][:75]}")
                if lines[j].strip() == "}" and j > i + 2:
                    break

    # Look for withdraw
    print("\n" + "=" * 60)
    print("[WITHDRAW/SELL FUNCTIONS]")
    print("=" * 60)

    for i, line in enumerate(lines):
        if re.search(r"function\s+(withdraw|sell|claim)\s*\(", line, re.IGNORECASE):
            print(f"\n  Found at line {i+1}:")
            for j in range(i, min(i+30, len(lines))):
                print(f"    {j+1}: {lines[j][:75]}")
                if lines[j].strip() == "}" and j > i + 2:
                    break

# Test functions
print("\n" + "=" * 60)
print("[FUNCTION TESTS]")
print("=" * 60)

tests = [
    ("0xa6f2ae3a", "buy()", "0xde0b6b3a7640000"),
    ("0x3ccfd60b", "withdraw()", "0x0"),
    ("0xe4849b32", "sell(uint256)", "0x0"),
    ("0x8da5cb5b", "owner()", "0x0"),
    ("0x18160ddd", "totalSupply()", "0x0"),
]

for sel, name, value in tests:
    data = sel
    if "uint256" in name:
        data += "0000000000000000000000000000000000000000000000000000000000000001"

    result = estimate_gas(TARGET, data, value=value)
    if result:
        if 'result' in result:
            gas = int(result['result'], 16)
            print(f"  [+] {name} - gas: {gas}")
        elif 'error' in result:
            err = result['error'].get('message', '')[:60]
            print(f"  [-] {name}: {err}")

print("\n" + "=" * 80)
