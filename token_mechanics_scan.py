#!/usr/bin/env python3
"""
Scan for token minting/burning vulnerabilities:
1. Unprotected mint functions
2. Burn without balance check
3. Approval manipulation
4. Permit signature vulnerabilities
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
print("TOKEN MECHANICS VULNERABILITY SCANNER")
print("=" * 80)

# Load contracts
with open("contracts.txt", "r") as f:
    contracts = [line.strip() for line in f if line.strip().startswith("0x")]

# Selectors
MINT_SELECTORS = {
    "mint()": "0x1249c58b",
    "mint(uint256)": "0xa0712d68",
    "mint(address,uint256)": "0x40c10f19",
    "mintTo(address)": "0x449a52f8",
    "issue(address,uint256)": "0x867904b4",
}

BURN_SELECTORS = {
    "burn(uint256)": "0x42966c68",
    "burn(address,uint256)": "0x9dc29fac",
    "burnFrom(address,uint256)": "0x79cc6790",
}

PERMIT_SELECTORS = {
    "permit(address,address,uint256,uint256,uint8,bytes32,bytes32)": "0xd505accf",
    "DOMAIN_SEPARATOR()": "0x3644e515",
    "nonces(address)": "0x7ecebe00",
}

findings = []

print(f"\nScanning {len(contracts)} contracts...")

for i, addr in enumerate(contracts):
    if i % 100 == 0:
        print(f"Progress: {i}/{len(contracts)}")

    balance = get_balance(addr)
    if balance < 20:
        continue

    code = get_code(addr)
    if len(code) < 200:  # Parity
        continue

    # Quick Parity check
    test1 = estimate_gas(addr, "0x12345678")
    test2 = estimate_gas(addr, "0x87654321")
    if test1 and test2 and 'result' in test1 and 'result' in test2:
        g1 = int(test1['result'], 16)
        g2 = int(test2['result'], 16)
        if abs(g1 - g2) < 500:
            continue  # Parity

    interesting = False
    contract_findings = {
        "address": addr,
        "balance": balance,
        "mint_callable": [],
        "burn_callable": [],
        "permit_available": False
    }

    # Test mint functions
    for name, sel in MINT_SELECTORS.items():
        data = sel
        if "uint256" in name:
            data += "0000000000000000000000000000000000000000000000000000000000000001"
        if "address" in name:
            data += "0000000000000000000000000000000000000000000000000000000000000001"
            if "uint256" in name:
                data += "0000000000000000000000000000000000000000000000000000000000000001"

        result = estimate_gas(addr, data)
        if result and 'result' in result:
            gas = int(result['result'], 16)
            if gas > 21000 and gas < 500000:
                contract_findings["mint_callable"].append({
                    "function": name,
                    "gas": gas
                })
                interesting = True

    # Test burn functions
    for name, sel in BURN_SELECTORS.items():
        data = sel
        if "address" in name:
            data += "0000000000000000000000000000000000000000000000000000000000000001"
        if "uint256" in name:
            data += "0000000000000000000000000000000000000000000000000000000000000001"

        result = estimate_gas(addr, data)
        if result and 'result' in result:
            gas = int(result['result'], 16)
            if gas > 21000 and gas < 500000:
                contract_findings["burn_callable"].append({
                    "function": name,
                    "gas": gas
                })
                interesting = True

    # Check for permit
    domain_sep = eth_call(addr, "0x3644e515")
    if domain_sep and domain_sep.get('result') and domain_sep['result'] != "0x":
        contract_findings["permit_available"] = True
        interesting = True

    if interesting:
        findings.append(contract_findings)
        print(f"\n[FOUND] {addr}")
        print(f"  Balance: {balance:.2f} ETH")
        if contract_findings["mint_callable"]:
            for m in contract_findings["mint_callable"]:
                print(f"  Mint: {m['function']} (gas: {m['gas']})")
        if contract_findings["burn_callable"]:
            for b in contract_findings["burn_callable"]:
                print(f"  Burn: {b['function']} (gas: {b['gas']})")
        if contract_findings["permit_available"]:
            print(f"  Has permit() function")

    time.sleep(0.2)

print("\n" + "=" * 80)
print(f"FOUND {len(findings)} CONTRACTS WITH TOKEN MECHANICS")
print("=" * 80)

# Deep analyze top findings
for finding in sorted(findings, key=lambda x: -x['balance'])[:5]:
    addr = finding['address']
    print(f"\n{'='*70}")
    print(f"[DEEP ANALYSIS] {addr}")
    print(f"Balance: {finding['balance']:.4f} ETH")
    print("=" * 70)

    source_data = get_source(addr)
    if source_data:
        contract_name = source_data.get("ContractName", "Unknown")
        print(f"Contract: {contract_name}")

        src = source_data.get("SourceCode", "")
        if src.startswith("{{"):
            try:
                src_json = json.loads(src[1:-1])
                sources = src_json.get("sources", {})
                src = "\n".join([v.get("content", "") for v in sources.values()])
            except:
                pass

        lines = src.split('\n')

        # Find mint functions
        if finding['mint_callable']:
            print("\n[MINT FUNCTIONS]")
            for i, line in enumerate(lines):
                if re.search(r"function\s+mint", line, re.IGNORECASE):
                    print(f"  Line {i+1}: {line.strip()[:70]}")
                    # Check for modifiers
                    if "only" in line.lower() or "require" in lines[min(i+1, len(lines)-1)].lower():
                        print(f"    [PROTECTED]")

        # Find burn functions
        if finding['burn_callable']:
            print("\n[BURN FUNCTIONS]")
            for i, line in enumerate(lines):
                if re.search(r"function\s+burn", line, re.IGNORECASE):
                    print(f"  Line {i+1}: {line.strip()[:70]}")

    time.sleep(0.5)

# Save findings
with open("token_mechanics_findings.json", "w") as f:
    json.dump(findings, f, indent=2)

print(f"\n[*] Findings saved to token_mechanics_findings.json")
