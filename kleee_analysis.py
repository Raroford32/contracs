#!/usr/bin/env python3
"""
Deep analysis of kleee002 contract
- 159.42 ETH balance
- totalSupply = 360
- deposit() callable
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
print("KLEEE002 CONTRACT DEEP ANALYSIS")
print("=" * 80)

TARGET = "0x63658cc84a5b2b969b8df9bea129a1c933e1439f"

print(f"\n[CONTRACT] {TARGET}")
print(f"[BALANCE] {get_balance(TARGET):.4f} ETH")

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
    elif src.startswith("{"):
        try:
            src_json = json.loads(src)
            sources = src_json.get("sources", {})
            src = "\n".join([v.get("content", "") for v in sources.values()])
        except:
            pass

    print(f"[SOURCE LENGTH] {len(src)} chars")

    if src:
        lines = src.split('\n')
        # Print full source if small
        if len(src) < 5000:
            print("\n[FULL SOURCE]")
            for i, line in enumerate(lines):
                print(f"  {i+1:3}: {line}")
        else:
            # Find key functions
            print("\n[KEY FUNCTIONS]")
            for i, line in enumerate(lines):
                if re.search(r"function\s+(deposit|withdraw|mint|burn|stake|claim)", line, re.IGNORECASE):
                    print(f"\n  Found at line {i+1}:")
                    for j in range(i, min(i+25, len(lines))):
                        print(f"    {j+1}: {lines[j][:75]}")
                        if lines[j].strip() == "}" and j > i + 2:
                            break

    # Parse ABI
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
        print("  Could not parse ABI")

# State checks
print("\n[STATE VARIABLES]")

selectors = {
    "totalSupply()": "0x18160ddd",
    "owner()": "0x8da5cb5b",
    "name()": "0x06fdde03",
    "symbol()": "0x95d89b41",
    "decimals()": "0x313ce567",
    "price()": "0xa035b1fe",
    "rate()": "0x2c4e722e",
    "pool()": "0x16f0115b",
}

for name, sel in selectors.items():
    result = eth_call(TARGET, sel)
    if result and result.get('result') and result['result'] not in ["0x", ""]:
        r = result['result']
        try:
            if len(r) > 66:  # Likely string
                print(f"  {name}: (complex)")
            else:
                val = int(r, 16)
                if val > 10**38:
                    print(f"  {name}: 0x{r[26:]}")
                elif val > 10**15:
                    print(f"  {name}: {val/1e18:.4f}")
                else:
                    print(f"  {name}: {val}")
        except:
            print(f"  {name}: {r[:40]}...")
    else:
        print(f"  {name}: (not found)")

# Storage
print("\n[STORAGE]")
for i in range(15):
    val = get_storage(TARGET, hex(i))
    if val and val != "0x" + "0"*64:
        print(f"  Slot {i}: {val}")

# Test functions
print("\n[FUNCTION TESTS]")

tests = [
    ("0xd0e30db0", "deposit()", "0xde0b6b3a7640000"),  # 1 ETH
    ("0x3ccfd60b", "withdraw()", "0x0"),
    ("0x1249c58b", "mint()", "0xde0b6b3a7640000"),
    ("0xa0712d68", "mint(uint256)", "0x0"),  # mint(1)
    ("0x2e1a7d4d", "withdraw(uint256)", "0x0"),  # withdraw(1)
    ("0x70a08231", "balanceOf(address)", "0x0"),  # balanceOf(0x1)
]

for sel, name, value in tests:
    data = sel
    if "uint256" in name:
        data += "0000000000000000000000000000000000000000000000000000000000000001"
    if "address" in name:
        data += "0000000000000000000000000000000000000000000000000000000000000001"

    result = estimate_gas(TARGET, data, value=value)
    if result:
        if 'result' in result:
            gas = int(result['result'], 16)
            print(f"  [+] {name} - CALLABLE gas: {gas}")
        elif 'error' in result:
            err = result['error'].get('message', '')[:50]
            print(f"  [-] {name}: {err}")

# Check balanceOf for us
print("\n[BALANCE CHECK]")
test_addr = "0000000000000000000000000000000000000000000000000000000000000001"
balance_data = "0x70a08231" + test_addr
result = eth_call(TARGET, balance_data)
if result and result.get('result'):
    bal = int(result['result'], 16)
    print(f"  balanceOf(0x1): {bal}")

# If totalSupply is 360, check how much 1 share is worth
print("\n[SHARE VALUE ANALYSIS]")
total_supply = 360
contract_balance = get_balance(TARGET)
if total_supply > 0:
    share_value = contract_balance / total_supply
    print(f"  Contract balance: {contract_balance:.4f} ETH")
    print(f"  Total supply: {total_supply}")
    print(f"  Value per share: {share_value:.6f} ETH")
    print(f"  If we can get 1 share, it's worth: {share_value:.6f} ETH")

print("\n" + "=" * 80)
print("ANALYSIS COMPLETE")
print("=" * 80)
