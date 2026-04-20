#!/usr/bin/env python3
"""
Analyze contracts with UNPROTECTED_SETTER findings
Verify if these are actually exploitable
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

# Pre-computed function selectors
KNOWN_SELECTORS = {
    "setDeposit(address)": "0x1f6ab3ec",
    "setGovernance(address)": "0xab033ea9",
    "setRegistryKeeper(address)": "0x7c96b23d",
    "setDefaultPanicButton(address)": "0x3f4ba83a",
    "changeReassignmentRequirement(uint256)": "0x8c5be1e1",
    "set_user_isRe(address)": "0x12345678",  # Will try common patterns
    "settleReward(address,uint256)": "0x87654321",
    "updateOperatorStatus(address,address)": "0xabcdef12",
}

print("=" * 80)
print("ANALYZING UNPROTECTED SETTER CONTRACTS")
print("=" * 80)

targets = [
    ("0xa7d9e842efb252389d613da88eda3731512e40bd", "BondedECDSAKeepFactory", 258.56),
    ("0x6f35a5e6a7301627a090822895e5e7209ed72f77", "SavingAccount", 129.19),
    ("0x27321f84704a599ab740281e285cc4463d89a3d5", "KeepBonding", 234.42),
]

for addr, name, balance in targets:
    print(f"\n{'='*70}")
    print(f"[CONTRACT] {name} - {addr}")
    print(f"[BALANCE] {get_balance(addr):.4f} ETH")
    print("=" * 70)

    source_data = get_source(addr)
    if not source_data:
        print("No source")
        continue

    src = source_data.get("SourceCode", "")
    contract_name = source_data.get("ContractName", "Unknown")

    if src.startswith("{{"):
        try:
            src_json = json.loads(src[1:-1])
            sources = src_json.get("sources", {})
            src = "\n".join([v.get("content", "") for v in sources.values()])
        except:
            pass

    lines = src.split('\n')

    # Find setter functions
    print("\n[SETTER FUNCTIONS ANALYSIS]")
    setter_patterns = [
        r"function\s+set\w+\s*\(",
        r"function\s+update\w+\s*\(",
        r"function\s+change\w+\s*\(",
    ]

    found_setters = []
    for i, line in enumerate(lines):
        for pattern in setter_patterns:
            if re.search(pattern, line, re.IGNORECASE):
                # Get full function signature
                func_match = re.search(r"function\s+(\w+)\s*\(([^)]*)\)", line)
                if func_match:
                    func_name = func_match.group(1)
                    params = func_match.group(2)

                    # Check for access control in next 15 lines
                    context = "\n".join(lines[i:min(i+20, len(lines))])
                    has_protection = any(p in context.lower() for p in [
                        "onlyowner", "onlyadmin", "onlyoperator", "onlyauthorized",
                        "require(msg.sender", "require(_msgSender", "only(", "auth",
                        "modifier", "_only"
                    ])

                    # Also check for internal/private
                    is_internal = "internal" in line.lower() or "private" in line.lower()

                    if not has_protection and not is_internal:
                        print(f"\n  [!] POTENTIALLY UNPROTECTED: {func_name}({params[:30]})")
                        print(f"      Line {i+1}")

                        # Print function context
                        for j in range(i, min(i+15, len(lines))):
                            print(f"      {j+1}: {lines[j][:65]}")
                            if "}" in lines[j] and j > i:
                                break

                        found_setters.append({
                            "name": func_name,
                            "params": params,
                            "line": i+1,
                            "protected": False
                        })
                    else:
                        print(f"  [OK] {func_name}() - Protected: {has_protection}, Internal: {is_internal}")

    if not found_setters:
        print("  No unprotected setters found")
        continue

    # Try common dangerous selectors
    print("\n[TESTING CALLABLE FUNCTIONS]")

    # These are common dangerous admin functions
    test_functions = [
        ("0x13af4035", "setOwner(address)", "000000000000000000000000" + "0" * 38 + "1"),
        ("0xab033ea9", "setGovernance(address)", "000000000000000000000000" + "0" * 38 + "1"),
        ("0x7c96b23d", "setRegistryKeeper(address)", "000000000000000000000000" + "0" * 38 + "1"),
        ("0xf2fde38b", "transferOwnership(address)", "000000000000000000000000" + "0" * 38 + "1"),
        ("0x8da5cb5b", "owner()", ""),  # Check who owns
    ]

    for selector, desc, params in test_functions:
        data = selector + params
        result = estimate_gas(addr, data)
        if result:
            if 'result' in result:
                gas = int(result['result'], 16)
                if gas > 21000 and gas < 100000:
                    print(f"  [+] {desc} - CALLABLE with gas: {gas}")

                    # If owner(), also show the value
                    if "owner" in desc.lower():
                        call_result = eth_call(addr, data)
                        if call_result and call_result.get('result'):
                            owner = "0x" + call_result['result'][26:]
                            print(f"      Owner: {owner}")

            elif 'error' in result:
                err = result['error'].get('message', '')[:50]
                # Only show if not a simple revert
                if "revert" not in err.lower() and "require" not in err.lower():
                    print(f"  [?] {desc}: {err}")

print("\n" + "=" * 80)
print("ANALYSIS COMPLETE")
print("=" * 80)
