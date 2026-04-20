#!/usr/bin/env python3
"""
Deep analysis of NFT contracts with callback vulnerabilities
kleee002 and ProjectINK
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
    {"address": "0x63658cc84a5b2b969b8df9bea129a1c933e1439f", "name": "kleee002", "balance": 159.42},
    {"address": "0x5e8353930b557a524ff92eace9b87d82f9793124", "name": "ProjectINK", "balance": 95.55},
]

print("=" * 80)
print("NFT CALLBACK VULNERABILITY ANALYSIS")
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

    # Find mint/safeMint functions (attack entry point)
    print("\n[Mint Functions]")
    mint_patterns = [
        r"function\s+mint\s*\([^)]*\)",
        r"function\s+safeMint\s*\([^)]*\)",
        r"function\s+publicMint\s*\([^)]*\)",
        r"function\s+claim\s*\([^)]*\)",
    ]

    for pattern in mint_patterns:
        matches = re.findall(pattern, src, re.IGNORECASE)
        for m in matches[:2]:
            print(f"  {m[:70]}")

    # Find the _safeMint implementation and CEI violations
    print("\n[_safeMint Implementation]")
    lines = src.split('\n')
    for i, line in enumerate(lines):
        if "_safemint" in line.lower() or "safemint" in line.lower():
            # Print context
            start = max(0, i-2)
            end = min(len(lines), i+20)
            has_callback_context = False
            for j in range(start, end):
                if "onerc721received" in lines[j].lower() or "checkonerc721received" in lines[j].lower():
                    has_callback_context = True
                    break
            if has_callback_context:
                print(f"  Found at line {i+1}")
                for j in range(start, min(end, start+15)):
                    print(f"    {j+1}: {lines[j][:75]}")
                print("  ---")
                break

    # Check for state changes after safeMint
    print("\n[CEI Violation Analysis]")
    for i, line in enumerate(lines):
        if "_safemint" in line.lower():
            # Look at lines after this for state changes
            for j in range(i+1, min(i+15, len(lines))):
                next_line = lines[j]
                # Look for assignments or mappings updates
                if '=' in next_line and 'require' not in next_line.lower():
                    if any(p in next_line.lower() for p in ['total', 'count', 'balance', 'mint', '_']):
                        print(f"  [!] Line {j+1} (after safeMint): {next_line.strip()[:60]}")

    # Check pricing/payment logic
    print("\n[Payment Logic]")
    for i, line in enumerate(lines):
        if "msg.value" in line.lower() or "price" in line.lower():
            if "require" in line.lower() or ">=" in line or "==" in line:
                print(f"  Line {i+1}: {line.strip()[:70]}")

    # Check supply limits
    print("\n[Supply Limits]")
    for i, line in enumerate(lines):
        if "maxsupply" in line.lower() or "totalsupply" in line.lower() or "max_supply" in line.lower():
            print(f"  Line {i+1}: {line.strip()[:70]}")

    # Test on-chain state
    print("\n[On-Chain State]")

    # totalSupply()
    ts = eth_call(addr, "0x18160ddd")
    if ts and ts.get('result'):
        print(f"  totalSupply(): {int(ts['result'], 16)}")

    # owner()
    owner = eth_call(addr, "0x8da5cb5b")
    if owner and owner.get('result') and len(owner['result']) >= 66:
        print(f"  owner(): 0x{owner['result'][26:]}")

    # Check mint price
    price_funcs = {
        "price()": "0xa035b1fe",
        "mintPrice()": "0x6817c76c",
        "cost()": "0x13faede6",
    }

    for func_name, sel in price_funcs.items():
        result = eth_call(addr, sel)
        if result and result.get('result') and result['result'] != '0x':
            val = int(result['result'], 16)
            print(f"  {func_name}: {val} wei ({val/1e18:.4f} ETH)")

    # Test mint function accessibility
    print("\n[Mint Function Tests]")

    mint_selectors = {
        "mint()": "0x1249c58b",
        "mint(uint256)": "0xa0712d68",
        "publicMint()": "0x26092b83",
        "claim()": "0x4e71d92d",
    }

    for func_name, sel in mint_selectors.items():
        data = sel
        if "uint256" in func_name:
            data = sel + "0000000000000000000000000000000000000000000000000000000000000001"

        # Try with small value
        result = estimate_gas(addr, data, value="0x2386f26fc10000")  # 0.01 ETH
        if result:
            if 'result' in result:
                gas = int(result['result'], 16)
                print(f"  [+] {func_name} callable with 0.01 ETH - gas: {gas}")
            elif 'error' in result:
                err = result['error'].get('message', '')[:60]
                print(f"  [-] {func_name}: {err}")

print("\n" + "=" * 80)
print("ANALYSIS COMPLETE")
print("=" * 80)
