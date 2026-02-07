#!/usr/bin/env python3
"""
Deep analysis of contracts with tx.origin authentication
These can be exploited via phishing attacks
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

targets = [
    {"address": "0xd48b633045af65ff636f3c6edd744748f39c5a39", "name": "Zethr", "balance": 280.8},
    {"address": "0xb9ab8eed48852de901c13543042204c6c569b811", "name": "Zethr2", "balance": 116.1},
    {"address": "0xe01e2a3cea58c1a77a31d6cfd30c52c7da2ca63d", "name": "EKS", "balance": 105.5},
    {"address": "0xd2bfceeab86c78884f88f4a31f04b1c9b9f1a3ff", "name": "DailyDivs", "balance": 109.8},
    {"address": "0xc618d56b6db0c8ac2da0ad1a899d3e18fd10f12a", "name": "LIQUID", "balance": 90.9},
]

print("=" * 80)
print("TX.ORIGIN AUTHENTICATION VULNERABILITY ANALYSIS")
print("=" * 80)

for target in targets:
    addr = target['address']
    name = target['name']

    print(f"\n{'='*70}")
    print(f"[CONTRACT] {name} - {addr}")
    print(f"[BALANCE] {get_balance(addr):.4f} ETH")
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

    # Find tx.origin usage
    print("\n[TX.ORIGIN Usage]")
    lines = src.split('\n')
    txorigin_functions = []

    for i, line in enumerate(lines):
        if "tx.origin" in line:
            print(f"  Line {i+1}: {line.strip()[:70]}")

            # Find the function containing this
            for j in range(i, -1, -1):
                if "function" in lines[j]:
                    func_match = re.search(r"function\s+(\w+)", lines[j])
                    if func_match:
                        func_name = func_match.group(1)
                        if func_name not in [f[0] for f in txorigin_functions]:
                            txorigin_functions.append((func_name, i+1, line.strip()[:50]))
                    break

    print("\n[Functions Using tx.origin]")
    for func_name, line_num, code in txorigin_functions:
        print(f"  {func_name}() at line {line_num}: {code}")

    # Find what tx.origin protects
    print("\n[What tx.origin Protects]")
    for func_name, _, _ in txorigin_functions:
        # Find the function body
        for i, line in enumerate(lines):
            if f"function {func_name}" in line:
                # Print function and body
                brace_count = 0
                started = False
                print(f"\n  {func_name}():")
                for j in range(i, min(i+30, len(lines))):
                    if '{' in lines[j]:
                        started = True
                    if started:
                        brace_count += lines[j].count('{') - lines[j].count('}')
                        print(f"    {j+1}: {lines[j][:60]}")
                        if brace_count <= 0:
                            break
                break

    # Check what value tx.origin controls
    print("\n[tx.origin Value Analysis]")

    # Look for admin/owner set with tx.origin
    for i, line in enumerate(lines):
        if "tx.origin" in line and ("admin" in line.lower() or "owner" in line.lower()):
            print(f"  Admin/Owner pattern at line {i+1}: {line.strip()[:60]}")

    # On-chain state
    print("\n[On-Chain State]")

    # admin/owner
    admin = eth_call(addr, "0xf851a440")  # admin()
    if admin and admin.get('result') and len(admin['result']) >= 66:
        print(f"  admin(): 0x{admin['result'][26:]}")

    owner = eth_call(addr, "0x8da5cb5b")  # owner()
    if owner and owner.get('result') and len(owner['result']) >= 66:
        print(f"  owner(): 0x{owner['result'][26:]}")

    # Check storage
    for slot in range(5):
        val = get_storage(addr, hex(slot))
        if val and val != "0x" + "0"*64:
            print(f"  Slot {slot}: {val}")

    # Check for withdraw functions
    print("\n[Value Extraction Functions]")
    value_funcs = ["withdraw", "transfer", "send", "exit", "claim"]
    for func in value_funcs:
        pattern = rf"function\s+{func}\w*\s*\([^)]*\)"
        matches = re.findall(pattern, src, re.IGNORECASE)
        for m in matches[:2]:
            print(f"  {m[:60]}")

print("\n" + "=" * 80)
print("ANALYSIS COMPLETE")
print("=" * 80)
