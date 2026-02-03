#!/usr/bin/env python3
"""
Deep analysis of WolkExchange (107 ETH)
Has LENDING_INTEGRATION and PRICE_DEPENDENT_TRANSFER patterns
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
print("WOLK EXCHANGE DEEP ANALYSIS")
print("=" * 80)

WOLK = "0x728781e75735dc0962df3a51d7ef47e798a7107e"

print(f"\n[CONTRACT] {WOLK}")
print(f"[BALANCE] {get_balance(WOLK):.4f} ETH")

source_data = get_source(WOLK)
if source_data:
    src = source_data.get("SourceCode", "")
    contract_name = source_data.get("ContractName", "Unknown")
    print(f"[CONTRACT NAME] {contract_name}")

    # Parse multi-file
    if src.startswith("{{"):
        try:
            src_json = json.loads(src[1:-1])
            sources = src_json.get("sources", {})
            src = "\n".join([v.get("content", "") for v in sources.values()])
        except:
            pass

    print(f"[SOURCE LENGTH] {len(src)} chars")
    lines = src.split('\n')

    # Find price-dependent patterns
    print("\n[PRICE-DEPENDENT PATTERNS]")
    for i, line in enumerate(lines):
        line_lower = line.lower()
        if any(p in line_lower for p in ["price", "rate", "exchange"]):
            if any(p in line_lower for p in ["transfer", "send", ".call"]):
                print(f"  Line {i+1}: {line.strip()[:80]}")

    # Find all external calls
    print("\n[EXTERNAL CALLS WITH VALUE]")
    for i, line in enumerate(lines):
        if ".call{" in line or ".transfer(" in line or ".send(" in line:
            # Get function context
            func_name = "unknown"
            for j in range(i, max(0, i-30), -1):
                if "function " in lines[j]:
                    match = re.search(r"function\s+(\w+)", lines[j])
                    if match:
                        func_name = match.group(1)
                    break
            print(f"  [{func_name}] Line {i+1}: {line.strip()[:70]}")

    # Find payable functions
    print("\n[PAYABLE FUNCTIONS]")
    for i, line in enumerate(lines):
        if "function" in line and "payable" in line:
            match = re.search(r"function\s+(\w+)", line)
            if match:
                func_name = match.group(1)
                print(f"  {func_name}() at line {i+1}")
                # Print function body
                for j in range(i, min(i+20, len(lines))):
                    print(f"    {j+1}: {lines[j][:75]}")
                    if lines[j].strip() == "}" and j > i:
                        break
                print()

    # Find lending/borrow patterns
    print("\n[LENDING PATTERNS]")
    for i, line in enumerate(lines):
        if any(p in line.lower() for p in ["borrow", "repay", "loan", "credit"]):
            print(f"  Line {i+1}: {line.strip()[:80]}")

    # Find state variables
    print("\n[STATE VARIABLES]")
    for i, line in enumerate(lines):
        if any(p in line for p in ["mapping", "uint256 public", "address public"]):
            if ";" in line:
                print(f"  {line.strip()[:80]}")

    # Find owner/admin patterns
    print("\n[OWNER/ADMIN PATTERNS]")
    for i, line in enumerate(lines):
        if any(p in line.lower() for p in ["onlyowner", "owner()", "admin", "operator"]):
            print(f"  Line {i+1}: {line.strip()[:80]}")

# On-chain state
print("\n" + "=" * 60)
print("[ON-CHAIN STATE]")
print("=" * 60)

selectors = {
    "owner()": "0x8da5cb5b",
    "paused()": "0x5c975abb",
    "rate()": "0x2c4e722e",
    "exchangeRate()": "0x3ba0b9a9",
    "totalSupply()": "0x18160ddd",
}

for name, sel in selectors.items():
    result = eth_call(WOLK, sel)
    if result and result.get('result') and result['result'] != "0x":
        r = result['result']
        try:
            val = int(r, 16)
            if val > 10**38:
                print(f"  {name}: 0x{r[26:]}")
            else:
                print(f"  {name}: {val}")
        except:
            print(f"  {name}: {r[:66]}")

# Storage slots
print("\n[STORAGE SLOTS]")
for i in range(10):
    val = get_storage(WOLK, hex(i))
    if val and val != "0x" + "0"*64:
        print(f"  Slot {i}: {val}")

# Test callable functions
print("\n" + "=" * 60)
print("[FUNCTION CALL TESTS]")
print("=" * 60)

test_selectors = [
    ("0x3ccfd60b", "withdraw()"),
    ("0xd0e30db0", "deposit()"),
    ("0xa6f2ae3a", "buy()"),
    ("0x4e71d92d", "claim()"),
    ("0xe8078d94", "addLiquidity()"),
    ("0xbaa2abde", "removeLiquidity()"),
    ("0x1249c58b", "mint()"),
    ("0x6a627842", "mint(address)"),
]

for sel, name in test_selectors:
    data = sel
    if "address" in name:
        data = sel + "0000000000000000000000000000000000000000000000000000000000000001"

    # Test with 0 ETH
    result = estimate_gas(WOLK, data, value="0x0")
    if result and 'result' in result:
        gas = int(result['result'], 16)
        print(f"  [+] {name} (0 ETH) - gas: {gas}")

    # Test with 1 ETH
    result = estimate_gas(WOLK, data, value="0xde0b6b3a7640000")
    if result and 'result' in result:
        gas = int(result['result'], 16)
        print(f"  [+] {name} (1 ETH) - gas: {gas}")

print("\n" + "=" * 80)
print("ANALYSIS COMPLETE")
print("=" * 80)
