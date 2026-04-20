#!/usr/bin/env python3
"""
Comprehensive vulnerability scan focusing on:
1. Uninitialized upgradeability proxies
2. Delegatecall to attacker-controlled addresses
3. Selfdestruct vulnerabilities
4. Signature replay issues
5. Access control gaps
"""
import json
import subprocess
import re
import time

RPC = "https://mainnet.infura.io/v3/bfc7283659224dd6b5124ebbc2b14e2c"
ETHERSCAN_API = "5UWN6DNT7UZCEJYNE3J6FCVAWH4QJW255K"

# Storage slots
IMPLEMENTATION_SLOT = "0x360894a13ba1a3210667c828492db98dca3e2076cc3735a920a3ca505d382bbc"
ADMIN_SLOT = "0xb53127684a568b3173ae13b9f8a6016e243e63b6e8ee1178d6a717850b5d6103"
BEACON_SLOT = "0xa3f0ad74e5423aebfd80d3ef4346578335a9a72aeaee59ff6cb3582b35133d50"

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

def is_parity_wallet(addr):
    """Quick check for Parity wallet echo pattern"""
    test_sels = ["0x8da5cb5b", "0x12345678", "0x87654321"]
    gases = []
    for sel in test_sels:
        result = estimate_gas(addr, sel)
        if result and 'result' in result:
            gases.append(int(result['result'], 16))
    if len(gases) >= 2:
        variance = max(gases) - min(gases)
        return variance < 500  # Echo pattern
    return False

print("=" * 80)
print("COMPREHENSIVE VULNERABILITY SCAN")
print("=" * 80)

# Load contracts
with open("contracts.txt", "r") as f:
    contracts = [line.strip() for line in f if line.strip().startswith("0x")]

findings = {
    "proxy_vulnerabilities": [],
    "access_control_issues": [],
    "dangerous_patterns": [],
}

print(f"\nScanning {len(contracts)} contracts...")

for i, addr in enumerate(contracts):
    if i % 50 == 0:
        print(f"Progress: {i}/{len(contracts)}")

    balance = get_balance(addr)
    if balance < 30:  # Focus on higher value
        continue

    code = get_code(addr)
    if len(code) < 200:  # Skip tiny contracts (Parity)
        continue

    # Skip if Parity pattern
    if is_parity_wallet(addr):
        continue

    # Check 1: Proxy with uninitialized implementation
    impl = get_storage(addr, IMPLEMENTATION_SLOT)
    if impl and impl != "0x" + "0"*64:
        impl_addr = "0x" + impl[26:]
        if impl_addr != "0x0000000000000000000000000000000000000000":
            # Test initialize on BOTH proxy and implementation
            init_tests = [
                ("initialize()", "0x8129fc1c"),
                ("initialize(address)", "0xc4d66de8"),
                ("__init__()", "0x9498bd71"),
            ]

            for name, sel in init_tests:
                data = sel
                if "address" in name:
                    data += "0000000000000000000000000000000000000000000000000000000000000001"

                # Test on implementation directly (bypassing proxy)
                impl_result = estimate_gas(impl_addr, data)
                if impl_result and 'result' in impl_result:
                    gas = int(impl_result['result'], 16)
                    if gas < 500000:
                        findings["proxy_vulnerabilities"].append({
                            "type": "UNINITIALIZED_IMPL",
                            "proxy": addr,
                            "implementation": impl_addr,
                            "balance": balance,
                            "callable_function": name,
                            "gas": gas
                        })
                        print(f"\n[PROXY VULN] {addr[:20]}...")
                        print(f"  Balance: {balance:.2f} ETH")
                        print(f"  Impl {name} callable with gas: {gas}")
                        break

    # Check 2: Access control - try calling privileged functions
    admin_funcs = [
        ("setOwner(address)", "0x13af4035"),
        ("transferOwnership(address)", "0xf2fde38b"),
        ("changeOwner(address)", "0xa6f9dae1"),
        ("setAdmin(address)", "0x704b6c02"),
        ("updateImplementation(address)", "0x025b22bc"),
        ("upgradeTo(address)", "0x3659cfe6"),
        ("upgradeToAndCall(address,bytes)", "0x4f1ef286"),
    ]

    for name, sel in admin_funcs:
        data = sel + "0000000000000000000000000000000000000000000000000000000000000001"
        if "bytes" in name:
            data += "00000000000000000000000000000000000000000000000000000000000000400000000000000000000000000000000000000000000000000000000000000000"

        result = estimate_gas(addr, data)
        if result and 'result' in result:
            gas = int(result['result'], 16)
            if gas > 21000 and gas < 200000:  # Real function, not just revert
                findings["access_control_issues"].append({
                    "type": "CALLABLE_ADMIN_FUNCTION",
                    "address": addr,
                    "balance": balance,
                    "function": name,
                    "gas": gas
                })
                print(f"\n[ACCESS] {addr[:20]}...")
                print(f"  Balance: {balance:.2f} ETH")
                print(f"  {name} callable with gas: {gas}")
                break

    # Check 3: Source code analysis for dangerous patterns
    source_data = get_source(addr)
    if source_data and source_data.get("SourceCode"):
        src = source_data.get("SourceCode", "")
        if src.startswith("{{"):
            try:
                src_json = json.loads(src[1:-1])
                sources = src_json.get("sources", {})
                src = "\n".join([v.get("content", "") for v in sources.values()])
            except:
                pass

        # Check for dangerous patterns
        patterns = [
            ("SELFDESTRUCT", r"selfdestruct\s*\("),
            ("DELEGATECALL_USER", r"\.delegatecall\s*\([^)]*msg\.sender"),
            ("DELEGATECALL_PARAM", r"\.delegatecall\s*\([^)]*_"),
            ("TX_ORIGIN", r"tx\.origin\s*=="),
            ("UNPROTECTED_ETH_SEND", r"\.call\{value:\s*[^}]+\}\s*\(\"\"\)"),
        ]

        for pattern_name, pattern in patterns:
            if re.search(pattern, src, re.IGNORECASE):
                findings["dangerous_patterns"].append({
                    "type": pattern_name,
                    "address": addr,
                    "balance": balance,
                    "contract_name": source_data.get("ContractName", "Unknown")
                })
                print(f"\n[PATTERN] {addr[:20]}...")
                print(f"  Balance: {balance:.2f} ETH | {pattern_name}")

    time.sleep(0.25)

# Summary
print("\n" + "=" * 80)
print("SCAN SUMMARY")
print("=" * 80)

print(f"\nProxy Vulnerabilities: {len(findings['proxy_vulnerabilities'])}")
for f in findings['proxy_vulnerabilities'][:5]:
    print(f"  {f['proxy'][:20]}... | {f['balance']:.2f} ETH | {f['type']}")

print(f"\nAccess Control Issues: {len(findings['access_control_issues'])}")
for f in findings['access_control_issues'][:5]:
    print(f"  {f['address'][:20]}... | {f['balance']:.2f} ETH | {f['function']}")

print(f"\nDangerous Patterns: {len(findings['dangerous_patterns'])}")
for f in findings['dangerous_patterns'][:5]:
    print(f"  {f['address'][:20]}... | {f['balance']:.2f} ETH | {f['type']}")

# Save
with open("comprehensive_findings.json", "w") as f:
    json.dump(findings, f, indent=2)

print(f"\n[*] Findings saved to comprehensive_findings.json")
