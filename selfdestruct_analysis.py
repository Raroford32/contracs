#!/usr/bin/env python3
"""
Analyze contracts with SELFDESTRUCT pattern
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

def eth_call(to, data, from_addr="0x0000000000000000000000000000000000000001"):
    result = rpc_call("eth_call", [{"to": to, "data": data, "from": from_addr}, "latest"])
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
print("SELFDESTRUCT CONTRACT ANALYSIS")
print("=" * 80)

# Load findings
with open("comprehensive_findings.json", "r") as f:
    findings = json.load(f)

# Find SELFDESTRUCT patterns
selfdestruct_contracts = [f for f in findings["dangerous_patterns"] if f["type"] == "SELFDESTRUCT"]

for contract in selfdestruct_contracts:
    addr = contract["address"]
    balance = get_balance(addr)

    print(f"\n{'='*70}")
    print(f"[CONTRACT] {addr}")
    print(f"[BALANCE] {balance:.4f} ETH")
    print("=" * 70)

    code = get_code(addr)
    print(f"[BYTECODE LENGTH] {len(code)} chars")

    if len(code) < 200:
        print("[!] Short bytecode - Parity wallet")
        continue

    # Check for Parity pattern
    test_sels = ["0x8da5cb5b", "0x12345678", "0x87654321"]
    gases = []
    for sel in test_sels:
        result = estimate_gas(addr, sel)
        if result and 'result' in result:
            gases.append(int(result['result'], 16))

    if len(gases) >= 2 and max(gases) - min(gases) < 500:
        print("[!] PARITY PATTERN - Not exploitable")
        continue

    # Get source
    source_data = get_source(addr)
    if source_data:
        contract_name = source_data.get("ContractName", "Unknown")
        print(f"[CONTRACT NAME] {contract_name}")

        src = source_data.get("SourceCode", "")
        if src.startswith("{{"):
            try:
                src_json = json.loads(src[1:-1])
                sources = src_json.get("sources", {})
                src = "\n".join([v.get("content", "") for v in sources.values()])
            except:
                pass

        lines = src.split('\n')

        # Find selfdestruct
        print("\n[SELFDESTRUCT LOCATION]")
        for i, line in enumerate(lines):
            if "selfdestruct" in line.lower():
                print(f"\n  Line {i+1}: {line.strip()[:70]}")
                # Print context
                for j in range(max(0, i-5), min(len(lines), i+5)):
                    prefix = ">>>" if j == i else "   "
                    print(f"  {prefix} {j+1}: {lines[j][:70]}")

        # Find function containing selfdestruct
        print("\n[FUNCTION WITH SELFDESTRUCT]")
        in_function = False
        func_name = ""
        func_start = 0

        for i, line in enumerate(lines):
            func_match = re.search(r"function\s+(\w+)", line)
            if func_match:
                func_name = func_match.group(1)
                func_start = i

            if "selfdestruct" in line.lower() and func_name:
                print(f"\n  Function: {func_name}()")
                print(f"  Starting at line {func_start+1}")

                # Find modifiers on this function
                for k in range(func_start, min(func_start+3, len(lines))):
                    if "onlyowner" in lines[k].lower() or "only" in lines[k].lower():
                        print(f"    [PROTECTED] Has modifier at line {k+1}")

    # Test functions that might trigger selfdestruct
    print("\n[FUNCTION TESTS]")

    funcs_to_test = [
        ("destroy()", "0x83197ef0"),
        ("kill()", "0x41c0e1b5"),
        ("close()", "0x43d726d6"),
        ("terminate()", "0x0c08bf88"),
        ("suicide()", "0xbd5e3ddc"),
        ("selfDestruct()", "0xf2ca4d21"),
        ("destroyContract()", "0xa2b6c5c3"),
        ("withdraw()", "0x3ccfd60b"),
        ("owner()", "0x8da5cb5b"),
    ]

    for name, sel in funcs_to_test:
        result = estimate_gas(addr, sel)
        if result:
            if 'result' in result:
                gas = int(result['result'], 16)
                print(f"  [+] {name}: gas {gas}")

                if name == "owner()":
                    call_result = eth_call(addr, sel)
                    if call_result and call_result.get('result'):
                        owner = "0x" + call_result['result'][26:]
                        print(f"      Owner: {owner}")

            elif 'error' in result:
                err = result['error'].get('message', '')[:50]
                if "revert" not in err.lower():
                    print(f"  [-] {name}: {err}")

print("\n" + "=" * 80)
print("ANALYSIS COMPLETE")
print("=" * 80)
