#!/usr/bin/env python3
"""
Deep analysis of contracts with CEI violations
EthPrime and TweetMarket
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
    {"address": "0xe40e1531a4b56fb65571ad2ca43dc0048a316a2d", "name": "EthPrime", "balance": 106.89},
    {"address": "0xe14ab3ee81abe340b45bb26b1b166a7d2df22585", "name": "TweetMarket", "balance": 105.51},
    {"address": "0x2af47a65da8cd66729b4209c22017d6a5c2d2400", "name": "StandardBounties", "balance": 90.37},
]

print("=" * 80)
print("CEI VIOLATION ANALYSIS")
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

    # Find external calls and analyze CEI pattern
    print("\n[External Call Analysis]")
    lines = src.split('\n')

    for i, line in enumerate(lines):
        # Look for external calls
        if any(p in line.lower() for p in ['.call{', '.call(', 'transfer(', '.send(']):
            # Check for CEI violation - state changes after call
            print(f"\n  External call at line {i+1}:")
            print(f"    {line.strip()[:70]}")

            # Look at context before and after
            for j in range(i+1, min(i+10, len(lines))):
                next_line = lines[j]
                # Look for state changes
                if '=' in next_line and 'require' not in next_line.lower():
                    stripped = next_line.strip()
                    if stripped and not stripped.startswith('//'):
                        if any(p in next_line.lower() for p in ['balance', 'total', 'amount', 'mapping', '[']):
                            print(f"    [!] State change after call - Line {j+1}: {stripped[:60]}")

    # Look for withdraw functions
    print("\n[Withdraw Functions]")
    withdraw_pattern = r"function\s+withdraw\s*\([^)]*\)\s*[^{]*\{"
    matches = re.findall(withdraw_pattern, src, re.IGNORECASE | re.DOTALL)
    for m in matches[:3]:
        print(f"  {m[:80]}")

    # Find the actual withdraw implementation
    for i, line in enumerate(lines):
        if "function withdraw" in line.lower():
            start = i
            # Find function body
            brace_count = 0
            end = i
            for j in range(i, min(i+50, len(lines))):
                brace_count += lines[j].count('{') - lines[j].count('}')
                if brace_count <= 0 and j > i:
                    end = j
                    break

            print(f"\n  Withdraw function at line {start+1}-{end+1}:")
            for j in range(start, min(end+1, start+20)):
                print(f"    {j+1}: {lines[j][:70]}")

    # Check on-chain state
    print("\n[On-Chain State]")

    # owner
    owner = eth_call(addr, "0x8da5cb5b")
    if owner and owner.get('result') and len(owner['result']) >= 66:
        print(f"  owner(): 0x{owner['result'][26:]}")

    # Check storage slots
    for slot in range(5):
        val = get_storage(addr, hex(slot))
        if val and val != "0x" + "0"*64:
            print(f"  Slot {slot}: {val}")

    # Test function accessibility
    print("\n[Function Tests]")
    test_funcs = {
        "withdraw()": "0x3ccfd60b",
        "withdraw(uint256)": "0x2e1a7d4d",
        "claimReward()": "0xb88a802f",
        "getBalance()": "0x12065fe0",
    }

    for func_name, sel in test_funcs.items():
        data = sel
        if "uint256" in func_name:
            data = sel + "0000000000000000000000000000000000000000000000000000000000000001"

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
