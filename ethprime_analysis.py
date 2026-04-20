#!/usr/bin/env python3
"""
Analyze EthPrime contract for reentrancy
- 106.88 ETH
- cashout() has external call before state update
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
print("ETHPRIME CONTRACT ANALYSIS")
print("=" * 80)

TARGET = "0xe40e1531a4b56fb65571ad2ca43dc0048a316a2d"

print(f"\n[CONTRACT] {TARGET}")
print(f"[BALANCE] {get_balance(TARGET):.4f} ETH")

code = get_code(TARGET)
print(f"[BYTECODE LENGTH] {len(code)} chars")

# Get source
source_data = get_source(TARGET)
if source_data:
    src = source_data.get("SourceCode", "")
    contract_name = source_data.get("ContractName", "Unknown")
    abi = source_data.get("ABI", "")
    print(f"[CONTRACT NAME] {contract_name}")

    if src.startswith("{{"):
        try:
            src_json = json.loads(src[1:-1])
            sources = src_json.get("sources", {})
            src = "\n".join([v.get("content", "") for v in sources.values()])
        except:
            pass

    lines = src.split('\n')

    # Find cashout function
    print("\n" + "=" * 60)
    print("[CASHOUT FUNCTION]")
    print("=" * 60)

    for i, line in enumerate(lines):
        if re.search(r"function\s+cashout", line, re.IGNORECASE):
            print(f"\n  Found at line {i+1}:")
            for j in range(i, min(i+50, len(lines))):
                print(f"    {j+1}: {lines[j][:75]}")
                if lines[j].strip() == "}" and j > i + 2:
                    break

    # Find claimDivsInternal
    print("\n" + "=" * 60)
    print("[CLAIMDIVSINTERNAL FUNCTION]")
    print("=" * 60)

    for i, line in enumerate(lines):
        if re.search(r"function\s+claimDivsInternal", line, re.IGNORECASE):
            print(f"\n  Found at line {i+1}:")
            for j in range(i, min(i+40, len(lines))):
                print(f"    {j+1}: {lines[j][:75]}")
                if lines[j].strip() == "}" and j > i + 2:
                    break

    # Find what 'dapp' is
    print("\n" + "=" * 60)
    print("[DAPP ADDRESS]")
    print("=" * 60)

    for i, line in enumerate(lines):
        if "dapp" in line.lower() and ("address" in line.lower() or "=" in line):
            print(f"  Line {i+1}: {line.strip()[:70]}")

# Parse ABI
print("\n" + "=" * 60)
print("[ABI FUNCTIONS]")
print("=" * 60)

if source_data and source_data.get("ABI"):
    try:
        abi_json = json.loads(source_data.get("ABI"))
        for item in abi_json:
            if item.get("type") == "function":
                name = item.get("name", "")
                inputs = item.get("inputs", [])
                stateMutability = item.get("stateMutability", "")
                input_types = ",".join([i.get("type", "") for i in inputs])
                print(f"  {name}({input_types}) - {stateMutability}")
    except:
        pass

# Test functions
print("\n" + "=" * 60)
print("[FUNCTION TESTS]")
print("=" * 60)

tests = [
    ("0x47681fca", "cashout()", "0x0"),
    ("0x3ccfd60b", "withdraw()", "0x0"),
    ("0xd0e30db0", "deposit()", "0xde0b6b3a7640000"),
    ("0x8da5cb5b", "owner()", "0x0"),
    ("0xc2bc2efc", "balances(address)", "0x0"),
]

for sel, name, value in tests:
    data = sel
    if "address" in name:
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
