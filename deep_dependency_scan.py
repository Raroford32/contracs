#!/usr/bin/env python3
"""
Deep dependency scan - find contracts that depend on:
1. External contracts that might be exploitable
2. Upgradeable components we can manipulate
3. Deprecated/dead contracts
4. Contracts with callable dangerous functions
"""
import json
import subprocess
import re
import time

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

def get_code(addr):
    result = rpc_call("eth_getCode", [addr, "latest"])
    if result and 'result' in result:
        return result['result']
    return "0x"

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
print("DEEP DEPENDENCY & INTERACTION SCANNER")
print("=" * 80)

# Load contracts
with open("contracts.txt", "r") as f:
    contracts = [line.strip() for line in f if line.strip().startswith("0x")]

findings = []

print("\n[1] SCANNING FOR EXTERNAL DEPENDENCIES")
print("-" * 50)

for i, addr in enumerate(contracts):
    if i % 30 == 0:
        print(f"Progress: {i}/{len(contracts)}...")

    balance = get_balance(addr)
    if balance < 50:
        continue

    time.sleep(0.25)
    source_data = get_source(addr)
    if not source_data:
        continue

    src = source_data.get("SourceCode", "")
    name = source_data.get("ContractName", "Unknown")

    if not src:
        continue

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

    src_lower = src.lower()
    lines = src.split('\n')

    vulnerabilities = []
    score = 0
    external_addrs = []

    # Extract hardcoded addresses from source
    addr_pattern = r'0x[a-fA-F0-9]{40}'
    found_addrs = re.findall(addr_pattern, src)
    unique_addrs = list(set([a.lower() for a in found_addrs if a.lower() != addr.lower()]))

    # Check if any hardcoded addresses have no code (dead contract)
    for ext_addr in unique_addrs[:10]:  # Check first 10
        code = get_code(ext_addr)
        if code == "0x" or len(code) < 10:
            score += 5
            vulnerabilities.append(f"DEAD_DEPENDENCY:{ext_addr[:16]}")
            external_addrs.append({"addr": ext_addr, "status": "NO_CODE"})

    # Check for settable external contract addresses
    settable_patterns = [
        r"function\s+set\w*\s*\([^)]*address",
        r"function\s+update\w*\s*\([^)]*address",
        r"function\s+change\w*\s*\([^)]*address",
    ]

    for pattern in settable_patterns:
        matches = re.findall(pattern, src, re.IGNORECASE)
        if matches:
            # Check if these are protected
            for match in matches[:3]:
                # Find the function and check for access control
                for j, line in enumerate(lines):
                    if match.lower() in line.lower():
                        context = "\n".join(lines[max(0,j-2):min(len(lines),j+10)])
                        if not any(p in context.lower() for p in ["onlyowner", "onlyadmin", "require(msg.sender"]):
                            score += 4
                            vulnerabilities.append(f"UNPROTECTED_SETTER:{match[:30]}")
                        break

    # Check for external calls to user-controlled addresses
    for j, line in enumerate(lines):
        # Look for calls to addresses from parameters
        if ".call" in line or "delegatecall" in line:
            context = "\n".join(lines[max(0,j-5):min(len(lines),j+5)])
            # Check if target address comes from user input
            if any(p in context for p in ["_to", "_target", "_recipient", "_addr"]):
                if "address(this)" not in context and "owner" not in context.lower():
                    score += 3
                    vulnerabilities.append("USER_CONTROLLED_CALL")
                    break

    # Check for callbacks that could be exploited
    callback_functions = [
        "onERC721Received",
        "onERC1155Received",
        "tokensReceived",
        "onFlashLoan",
        "fallback",
        "receive",
    ]

    for cb in callback_functions:
        if f"function {cb}" in src_lower or f"function {cb.lower()}" in src:
            # Check if this callback has state changes
            for j, line in enumerate(lines):
                if cb.lower() in line.lower() and "function" in line.lower():
                    func_body = "\n".join(lines[j:min(j+30, len(lines))])
                    if any(p in func_body for p in ["+=", "-=", "balances[", "totalSupply"]):
                        score += 2
                        vulnerabilities.append(f"CALLBACK_STATE:{cb}")
                    break

    # Check for time-dependent logic that could be exploited
    if "block.timestamp" in src_lower:
        # Look for comparisons that could be manipulated
        for j, line in enumerate(lines):
            if "block.timestamp" in line.lower():
                if any(p in line for p in ["<", ">", "==", "!="]):
                    # Check if this affects value transfer
                    context = "\n".join(lines[j:min(j+10, len(lines))])
                    if any(p in context.lower() for p in ["transfer", "withdraw", "mint", "redeem"]):
                        score += 2
                        vulnerabilities.append("TIMESTAMP_DEPENDENT_VALUE")
                        break

    if score >= 4:
        finding = {
            "address": addr,
            "name": name,
            "balance": balance,
            "score": score,
            "vulnerabilities": vulnerabilities,
            "external_deps": external_addrs[:5],
        }
        findings.append(finding)
        print(f"\n[!] {name} ({addr[:16]}...)")
        print(f"    Balance: {balance:.2f} ETH | Score: {score}")
        print(f"    Vulnerabilities: {vulnerabilities}")
        if external_addrs:
            print(f"    Dead dependencies: {[a['addr'][:16] for a in external_addrs]}")

# Sort by score and balance
findings.sort(key=lambda x: (x['score'], x['balance']), reverse=True)

print("\n" + "=" * 80)
print("TOP DEPENDENCY FINDINGS")
print("=" * 80)

for i, f in enumerate(findings[:15]):
    print(f"\n{i+1}. {f['name']} ({f['address']})")
    print(f"   Balance: {f['balance']:.2f} ETH | Score: {f['score']}")
    print(f"   Vulns: {f['vulnerabilities']}")

# Save findings
with open("dependency_findings.json", "w") as f:
    json.dump(findings, f, indent=2)

print(f"\n[*] Total findings with score >= 4: {len(findings)}")
print("[*] Saved to dependency_findings.json")
