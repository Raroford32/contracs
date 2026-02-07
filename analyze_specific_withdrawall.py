#!/usr/bin/env python3
"""
Analyze contracts with specific withdrawAll() function callable
These are NOT the Parity wallet echo pattern
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

def eth_call(to, data, from_addr="0x0000000000000000000000000000000000000001"):
    result = rpc_call("eth_call", [{"to": to, "data": data, "from": from_addr}, "latest"])
    return result

def estimate_gas(to, data, from_addr="0x0000000000000000000000000000000000000001"):
    result = rpc_call("eth_estimateGas", [{"to": to, "data": data, "from": from_addr}])
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

# Contracts with specific withdrawAll() only (not all functions like Parity wallets)
targets = [
    {"address": "0xdd637dda8a00e56968f9a9e8cffa74be2b35ce62", "balance": 138.3},
    {"address": "0xdc260a232c0a61b68abf6f70f15d0bdc6b36db0d", "balance": 93.8},
    {"address": "0x48c128eafc9caef8823add6af31dcb24d9dc2692", "balance": 98.5},
]

print("=" * 80)
print("SPECIFIC WITHDRAWALL() FUNCTION ANALYSIS")
print("=" * 80)

for target in targets:
    addr = target['address']
    print(f"\n{'='*70}")
    print(f"[CONTRACT] {addr}")
    print(f"[BALANCE] {get_balance(addr):.4f} ETH")
    print("=" * 70)

    # Get bytecode
    code = get_code(addr)
    print(f"Bytecode length: {len(code)} chars")

    # Check if it's a simple proxy or actual contract
    if len(code) < 200:
        print("[!] Very short bytecode - likely minimal proxy")
    elif len(code) < 1000:
        print("[!] Short bytecode - simple contract or proxy")
    else:
        print("[+] Substantial bytecode - likely full contract")

    # Get source
    source_data = get_source(addr)
    if source_data:
        name = source_data.get("ContractName", "Unknown")
        src = source_data.get("SourceCode", "")
        print(f"Contract Name: {name}")
        print(f"Source available: {len(src)} chars")

        if src:
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

            # Find withdrawAll function
            if "withdrawall" in src.lower():
                print("\n[withdrawAll Function Found]")
                lines = src.split('\n')
                for i, line in enumerate(lines):
                    if "withdrawall" in line.lower():
                        # Print context
                        start = max(0, i-2)
                        end = min(len(lines), i+10)
                        for j in range(start, end):
                            print(f"  {j+1}: {lines[j][:80]}")
                        print("  ---")
    else:
        print("No verified source")

    # Check storage slots
    print("\n[Storage Analysis]")
    for i in range(10):
        slot = get_storage(addr, hex(i))
        if slot and slot != "0x" + "0"*64:
            print(f"  Slot {i}: {slot}")
            if len(slot) == 66 and slot[2:26] == "0"*24:
                addr_val = "0x" + slot[26:]
                print(f"         -> address: {addr_val}")

    # Test withdrawAll specifically
    print("\n[withdrawAll() Test]")
    withdraw_all_sel = "0x853828b6"

    # Test with eth_call
    call_result = eth_call(addr, withdraw_all_sel)
    if call_result:
        if 'result' in call_result:
            print(f"  eth_call result: {call_result['result']}")
        elif 'error' in call_result:
            print(f"  eth_call error: {call_result['error'].get('message', '')[:80]}")

    # Test gas estimate
    gas_result = estimate_gas(addr, withdraw_all_sel)
    if gas_result:
        if 'result' in gas_result:
            gas = int(gas_result['result'], 16)
            print(f"  Gas estimate: {gas}")
            if gas > 21326:  # More than minimal proxy echo
                print(f"  [!!!] Gas > 21326 suggests REAL function!")
            else:
                print(f"  [!] Low gas suggests proxy echo behavior")
        elif 'error' in gas_result:
            print(f"  Gas estimate error: {gas_result['error'].get('message', '')[:80]}")

    # Test other common functions to see if it's a selective responder
    print("\n[Other Function Tests]")
    test_funcs = {
        "owner()": "0x8da5cb5b",
        "admin()": "0xf851a440",
        "withdraw()": "0x3ccfd60b",
        "balance()": "0xb69ef8a8",
        "totalBalance()": "0xad7a672f",
    }

    for func_name, sel in test_funcs.items():
        result = estimate_gas(addr, sel)
        if result and 'result' in result:
            gas = int(result['result'], 16)
            print(f"  {func_name}: gas {gas}")
        elif result and 'error' in result:
            err = result['error'].get('message', '')[:50]
            print(f"  {func_name}: {err}")

print("\n" + "=" * 80)
print("ANALYSIS COMPLETE")
print("=" * 80)
