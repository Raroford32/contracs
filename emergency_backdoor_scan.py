#!/usr/bin/env python3
"""
Scan for emergency functions, backdoors, and access control bypasses
Looking for:
1. Emergency withdraw functions that might be unprotected
2. Backdoor functions (arbitrary calls, code execution)
3. Access control bypasses
4. Timelock bypass patterns
"""
import json
import subprocess
import time
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

def get_balance(addr):
    result = rpc_call("eth_getBalance", [addr, "latest"])
    if result and 'result' in result:
        return int(result['result'], 16) / 1e18
    return 0

def estimate_gas(to, data, from_addr="0x0000000000000000000000000000000000000001", value="0x0"):
    result = rpc_call("eth_estimateGas", [{"to": to, "data": data, "from": from_addr, "value": value}])
    return result

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

# Load contracts
with open("contracts.txt", "r") as f:
    contracts = [line.strip() for line in f if line.strip().startswith("0x")]

print("=" * 80)
print("EMERGENCY/BACKDOOR FUNCTION SCAN")
print("=" * 80)

# Dangerous function selectors to test
dangerous_selectors = {
    # Withdraw functions
    "withdraw()": "0x3ccfd60b",
    "withdrawAll()": "0x853828b6",
    "emergencyWithdraw()": "0xdb2e21bc",
    "drain()": "0x9890220b",
    "sweep(address)": "0x01681a62",
    "rescueFunds(address,uint256)": "0x78e3214f",
    "recoverERC20(address,uint256)": "0x8980f11f",
    "recoverETH()": "0xe086e5ec",
    "claimTokens(address)": "0xdf8de3e7",
    "withdrawETH()": "0xf14210a6",
    "exit()": "0xe9fad8ee",

    # Dangerous admin functions
    "pause()": "0x8456cb59",
    "unpause()": "0x3f4ba83a",
    "kill()": "0x41c0e1b5",
    "destroy()": "0x83197ef0",
    "selfdestruct()": "0x9cb8a26a",

    # Arbitrary execution
    "execute(address,bytes)": "0x1cff79cd",
    "multicall(bytes[])": "0xac9650d8",
    "executeTransaction(address,uint256,string,bytes,uint256)": "0x0825f38f",

    # Access control
    "setOwner(address)": "0x13af4035",
    "changeOwner(address)": "0xa6f9dae1",
    "addMinter(address)": "0x983b2d56",
    "setAdmin(address)": "0x704b6c02",
    "grantRole(bytes32,address)": "0x2f2ff15d",
}

findings = []

for i, addr in enumerate(contracts):
    if i % 30 == 0:
        print(f"Scanning {i}/{len(contracts)}...")

    balance = get_balance(addr)
    if balance < 40:  # Focus on 40+ ETH
        continue

    contract_findings = []

    for func_name, selector in dangerous_selectors.items():
        # Build call data with dummy parameters
        data = selector
        if "address" in func_name:
            data = selector + "0000000000000000000000000000000000000000000000000000000000000001"
        if "uint256" in func_name:
            if "address" in func_name:
                data = data[:10+64] + "0000000000000000000000000000000000000000000000000000000000000001"
            else:
                data = selector + "0000000000000000000000000000000000000000000000000000000000000001"
        if "bytes" in func_name:
            # Complex encoding for bytes
            continue
        if "bytes32" in func_name:
            data = selector + "0000000000000000000000000000000000000000000000000000000000000001"
            if "address" in func_name:
                data = data[:10+64] + "0000000000000000000000000000000000000000000000000000000000000001"
        if "string" in func_name:
            continue

        result = estimate_gas(addr, data)
        if result and 'result' in result:
            gas = int(result['result'], 16)
            if gas < 500000:  # Reasonable gas = function exists
                contract_findings.append({
                    "function": func_name,
                    "gas": gas
                })

    if contract_findings:
        time.sleep(0.25)
        source_data = get_source(addr)
        name = "Unknown"
        has_access_control = False

        if source_data:
            src = source_data.get("SourceCode", "")
            name = source_data.get("ContractName", "Unknown")

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

            # Check for access control
            access_patterns = ["onlyOwner", "onlyAdmin", "require(msg.sender", "require(_msgSender"]
            has_access_control = any(p in src for p in access_patterns)

        # Score the findings
        score = 0
        dangerous_funcs = []

        for f in contract_findings:
            fn = f['function']
            # High-risk functions
            if any(p in fn for p in ["withdraw", "drain", "sweep", "rescue", "claim", "exit"]):
                score += 3
                dangerous_funcs.append(fn)
            elif any(p in fn for p in ["kill", "destroy", "selfdestruct"]):
                score += 5
                dangerous_funcs.append(fn)
            elif any(p in fn for p in ["execute", "multicall"]):
                score += 4
                dangerous_funcs.append(fn)
            elif any(p in fn for p in ["setOwner", "changeOwner", "setAdmin"]):
                score += 2

        # If no access control detected, increase score
        if not has_access_control:
            score += 3

        if score >= 3:
            finding = {
                "address": addr,
                "name": name,
                "balance": balance,
                "score": score,
                "dangerous_functions": dangerous_funcs,
                "all_functions": contract_findings,
                "has_access_control": has_access_control
            }
            findings.append(finding)
            print(f"\n[!!] {name} ({addr[:12]}...) - {balance:.1f} ETH - Score: {score}")
            print(f"     Dangerous: {dangerous_funcs}")
            print(f"     Access Control: {has_access_control}")

# Sort by score
findings.sort(key=lambda x: (x['score'], x['balance']), reverse=True)

print("\n" + "=" * 80)
print("TOP EMERGENCY/BACKDOOR FINDINGS")
print("=" * 80)

for i, f in enumerate(findings[:20]):
    print(f"\n{i+1}. {f['name']} ({f['address']})")
    print(f"   Balance: {f['balance']:.2f} ETH | Score: {f['score']}")
    print(f"   Dangerous Functions: {f['dangerous_functions']}")
    print(f"   Has Access Control: {f['has_access_control']}")
    print(f"   All Callable: {[x['function'] for x in f['all_functions']]}")

with open("emergency_findings.json", "w") as f:
    json.dump(findings, f, indent=2)

print(f"\n[*] Found {len(findings)} contracts with emergency/backdoor patterns")
