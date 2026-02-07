#!/usr/bin/env python3
"""
Deep analysis of boundary condition vulnerabilities
Focus on: MSGVALUE_BALANCE_INTERACTION, MISSING_EMPTY_SUPPLY_CHECK
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

# Targets with MSGVALUE_BALANCE_INTERACTION or interesting patterns
targets = [
    {"address": "0xae28714390aca0a14e5f4c6183126de590ee0fea", "name": "EulerBeats", "balance": 215.6, "vulns": ["MSGVALUE_BALANCE_INTERACTION", "MISSING_EMPTY_SUPPLY_CHECK"]},
    {"address": "0xbdaf6b3e5e0c5a46cce3a75b8f4c46c8d6668b39", "name": "HashesDAO", "balance": 205.9, "vulns": ["MSGVALUE_BALANCE_INTERACTION", "HIGH_EXTERNAL_CALLS:6"]},
    {"address": "0xdeface1e0afe1f8b8a0e5c5afe5c7e8c0e5c1adb", "name": "Unknown", "balance": 0, "vulns": []},  # placeholder
]

# Load actual findings from boundary scan
try:
    with open("boundary_findings.json", "r") as f:
        boundary_findings = json.load(f)
        # Focus on MSGVALUE_BALANCE_INTERACTION
        targets = [t for t in boundary_findings if "MSGVALUE_BALANCE_INTERACTION" in t.get('vulnerabilities', [])]
        if not targets:
            targets = boundary_findings[:5]
except:
    pass

print("=" * 80)
print("DEEP BOUNDARY VULNERABILITY ANALYSIS")
print("=" * 80)

for target in targets[:10]:
    addr = target['address']
    name = target.get('name', 'Unknown')

    print(f"\n{'='*70}")
    print(f"[CONTRACT] {name} - {addr}")
    print(f"[BALANCE] {get_balance(addr):.4f} ETH")
    print(f"[VULNS] {target.get('vulnerabilities', [])}")
    print("=" * 70)

    # Get source
    source_data = get_source(addr)
    if not source_data:
        print("No verified source")
        continue

    src = source_data.get("SourceCode", "")
    contract_name = source_data.get("ContractName", "Unknown")
    print(f"Contract Name: {contract_name}")

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

    print(f"Source length: {len(src)} chars")

    # ANALYSIS 1: msg.value and address(this).balance interaction
    print("\n[MSG.VALUE + BALANCE ANALYSIS]")

    lines = src.split('\n')
    for i, line in enumerate(lines):
        # Look for dangerous patterns
        if "msg.value" in line and ("balance" in line.lower() or "this" in line):
            print(f"  Line {i+1}: {line.strip()[:80]}")
        elif "address(this).balance" in line:
            print(f"  Line {i+1}: {line.strip()[:80]}")

    # Find payable functions
    print("\n[PAYABLE FUNCTIONS]")
    payable_funcs = []
    for i, line in enumerate(lines):
        if "function" in line and "payable" in line:
            match = re.search(r"function\s+(\w+)", line)
            if match:
                func_name = match.group(1)
                payable_funcs.append((func_name, i+1))
                print(f"  {func_name}() at line {i+1}")

    # Look for refund patterns (potential reentrancy or calculation issues)
    print("\n[REFUND/RETURN PATTERNS]")
    for i, line in enumerate(lines):
        if any(p in line.lower() for p in ["refund", "excess", "return", "remainder"]):
            if "msg.value" in line or "balance" in line.lower() or ".call" in line or ".transfer" in line:
                print(f"  Line {i+1}: {line.strip()[:80]}")

    # ANALYSIS 2: Check for price calculation with balance
    print("\n[PRICE/RATE CALCULATION]")
    for i, line in enumerate(lines):
        if "/" in line:  # Division
            if "balance" in line.lower() or "supply" in line.lower():
                print(f"  Line {i+1}: {line.strip()[:80]}")

    # ANALYSIS 3: Look for functions that could drain via msg.value mismatch
    print("\n[POTENTIAL DRAIN FUNCTIONS]")

    # Common patterns
    drain_patterns = [
        r"msg\.value\s*-",  # msg.value minus something
        r"address\(this\)\.balance\s*-",  # balance minus
        r"\.call\{value:",  # call with value
        r"\.transfer\(",  # transfer
        r"\.send\(",  # send
    ]

    for i, line in enumerate(lines):
        for pattern in drain_patterns:
            if re.search(pattern, line):
                # Get function context
                func_context = ""
                for j in range(i, max(0, i-20), -1):
                    if "function" in lines[j]:
                        match = re.search(r"function\s+(\w+)", lines[j])
                        if match:
                            func_context = match.group(1)
                        break
                print(f"  [{func_context}] Line {i+1}: {line.strip()[:70]}")

    # ANALYSIS 4: Check storage for current state
    print("\n[ON-CHAIN STATE]")

    # Common selectors
    selectors = {
        "totalSupply()": "0x18160ddd",
        "owner()": "0x8da5cb5b",
        "paused()": "0x5c975abb",
    }

    for name_sel, sel in selectors.items():
        result = eth_call(addr, sel)
        if result and result.get('result') and result['result'] != "0x":
            try:
                val = int(result['result'], 16)
                print(f"  {name_sel}: {val}")
            except:
                print(f"  {name_sel}: {result['result'][:66]}")

    # Check first few storage slots
    for i in range(5):
        val = get_storage(addr, hex(i))
        if val and val != "0x" + "0"*64:
            print(f"  Storage[{i}]: {val}")

    # ANALYSIS 5: Try calling payable functions
    print("\n[FUNCTION EXPLOITABILITY TESTS]")

    # Test specific vulnerable patterns
    test_selectors = {
        "mint()": "0x1249c58b",
        "buy()": "0xa6f2ae3a",
        "deposit()": "0xd0e30db0",
        "claim()": "0x4e71d92d",
        "withdraw()": "0x3ccfd60b",
        "withdrawAll()": "0x853828b6",
        "emergencyWithdraw()": "0xdb2e21bc",
    }

    for func, sel in test_selectors.items():
        # Try with 0 ETH first
        result = estimate_gas(addr, sel, value="0x0")
        if result and 'result' in result:
            gas = int(result['result'], 16)
            print(f"  [+] {func} callable (0 ETH) - gas: {gas}")

            # Try with 1 ETH
            result_eth = estimate_gas(addr, sel, value="0xde0b6b3a7640000")  # 1 ETH
            if result_eth and 'result' in result_eth:
                gas_eth = int(result_eth['result'], 16)
                print(f"  [+] {func} callable (1 ETH) - gas: {gas_eth}")

print("\n" + "=" * 80)
print("DEEP ANALYSIS COMPLETE")
print("=" * 80)
