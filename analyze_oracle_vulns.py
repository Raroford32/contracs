#!/usr/bin/env python3
"""
Deep analysis of oracle manipulation candidates
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
    {"address": "0x0337184a497565a9bd8e300dad50270cd367f206", "name": "DynamicLiquidTokenConverter", "balance": 83.59},
    {"address": "0xd3d2b5643e506c6d9b7099e9116d7aaa941114fe", "name": "KyberFeeHandler", "balance": 88.93},
    {"address": "0x6f35a5e6a7301627a090822895e5e7209ed72f77", "name": "SavingAccount", "balance": 129.19},
]

print("=" * 80)
print("ORACLE MANIPULATION VULNERABILITY ANALYSIS")
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

    # Find price/oracle related code
    print("\n[Price/Oracle Logic]")
    lines = src.split('\n')
    for i, line in enumerate(lines):
        if any(p in line.lower() for p in ["price", "rate", "latestanswer", "getreserves", "exchange"]):
            if any(p in line for p in ['function', 'return', '=']):
                print(f"  Line {i+1}: {line.strip()[:70]}")

    # Find Chainlink usage
    print("\n[Chainlink Analysis]")
    for i, line in enumerate(lines):
        if "latestanswer" in line.lower() or "latestrounddata" in line.lower():
            context_start = max(0, i-3)
            context_end = min(len(lines), i+5)
            print(f"  Found at line {i+1}:")
            for j in range(context_start, context_end):
                print(f"    {j+1}: {lines[j][:65]}")
            print("  ---")

    # Find critical operations
    print("\n[Critical Operations]")
    critical_funcs = ["convert", "swap", "exchange", "liquidate", "borrow", "repay", "redeem"]
    for pattern in critical_funcs:
        func_pattern = rf"function\s+{pattern}[^{{]*\{{"
        matches = re.findall(func_pattern, src, re.IGNORECASE | re.DOTALL)
        for m in matches[:2]:
            print(f"  {m[:70]}...")

    # Check on-chain state
    print("\n[On-Chain State]")

    # owner
    owner = eth_call(addr, "0x8da5cb5b")
    if owner and owner.get('result') and len(owner['result']) >= 66:
        print(f"  owner(): 0x{owner['result'][26:]}")

    # Check for price/rate functions
    rate_funcs = {
        "rate()": "0x2c4e722e",
        "getRate()": "0x679aefce",
        "price()": "0xa035b1fe",
        "exchangeRate()": "0x3ba0b9a9",
        "getPrice()": "0x98d5fdca",
    }

    for func_name, sel in rate_funcs.items():
        result = eth_call(addr, sel)
        if result and result.get('result') and result['result'] != '0x':
            val = int(result['result'], 16)
            print(f"  {func_name}: {val}")

    # Check storage slots
    print("\n[Storage Slots]")
    for slot in range(5):
        val = get_storage(addr, hex(slot))
        if val and val != "0x" + "0"*64:
            print(f"  Slot {slot}: {val}")

    # Test function accessibility
    print("\n[Function Tests]")
    test_funcs = {
        "convert(uint256)": "0xa3908e1b",
        "swap(uint256,uint256)": "0xd004f0f7",
        "exchange(uint256)": "0x65e17c9d",
        "withdraw(uint256)": "0x2e1a7d4d",
    }

    for func_name, sel in test_funcs.items():
        data = sel
        # Add dummy parameters
        data = sel + "0000000000000000000000000000000000000000000000000000000000000001"
        if func_name.count("uint256") == 2:
            data = data + "0000000000000000000000000000000000000000000000000000000000000001"

        result = estimate_gas(addr, data)
        if result:
            if 'result' in result:
                gas = int(result['result'], 16)
                print(f"  [+] {func_name} callable - gas: {gas}")
            elif 'error' in result:
                err = result['error'].get('message', '')[:50]
                print(f"  [-] {func_name}: {err}")

print("\n" + "=" * 80)
print("ANALYSIS COMPLETE")
print("=" * 80)
