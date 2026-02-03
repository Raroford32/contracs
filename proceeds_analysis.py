#!/usr/bin/env python3
"""
Deep analysis of Proceeds contract (92 ETH)
Has DONATION_ATTACK_SURFACE and CEI_VIOLATION
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
print("PROCEEDS CONTRACT DEEP ANALYSIS")
print("=" * 80)

PROCEEDS = "0x68c4b7d05fae45bcb6192bb93e246c77e98360e1"

print(f"\n[CONTRACT] {PROCEEDS}")
print(f"[BALANCE] {get_balance(PROCEEDS):.4f} ETH")

source_data = get_source(PROCEEDS)
if source_data:
    src = source_data.get("SourceCode", "")
    contract_name = source_data.get("ContractName", "Unknown")
    print(f"[CONTRACT NAME] {contract_name}")

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

    print(f"[SOURCE LENGTH] {len(src)} chars")
    lines = src.split('\n')

    # Print entire source if short
    if len(src) < 10000:
        print("\n[FULL SOURCE]")
        for i, line in enumerate(lines):
            print(f"  {i+1}: {line}")
    else:
        # Find donation attack surface
        print("\n[DONATION ATTACK SURFACE]")
        for i, line in enumerate(lines):
            if "balanceof(address(this))" in line.lower() or "address(this).balance" in line.lower():
                print(f"\n  Line {i+1}: {line.strip()[:80]}")
                for j in range(max(0,i-3), min(len(lines), i+5)):
                    print(f"    {j+1}: {lines[j][:75]}")

        # Find CEI violations
        print("\n[CEI VIOLATIONS]")
        for i, line in enumerate(lines):
            if any(p in line for p in [".call{", ".transfer(", ".send("]):
                print(f"\n  External call at line {i+1}: {line.strip()[:70]}")
                for j in range(i+1, min(i+8, len(lines))):
                    if any(p in lines[j] for p in ["+=", "-=", "= "]):
                        if "return" not in lines[j].lower():
                            print(f"    State change at line {j+1}: {lines[j].strip()[:70]}")

        # Find withdraw/claim functions
        print("\n[WITHDRAW/CLAIM FUNCTIONS]")
        for i, line in enumerate(lines):
            if re.search(r"function\s+(withdraw|claim|getProceeds|collect)", line, re.IGNORECASE):
                print(f"\n  Found at line {i+1}:")
                for j in range(i, min(i+30, len(lines))):
                    print(f"    {j+1}: {lines[j][:75]}")
                    if lines[j].strip() == "}" and j > i + 1:
                        break

# On-chain state
print("\n" + "=" * 60)
print("[ON-CHAIN STATE]")
print("=" * 60)

selectors = {
    "owner()": "0x8da5cb5b",
    "admin()": "0xf851a440",
    "totalProceeds()": "0x78c9f869",
    "claimable()": "0x402914f5",
}

for name, sel in selectors.items():
    result = eth_call(PROCEEDS, sel)
    if result and result.get('result') and result['result'] != "0x":
        r = result['result']
        try:
            val = int(r, 16)
            if val > 10**38:
                print(f"  {name}: 0x{r[26:]}")
            else:
                print(f"  {name}: {val}")
        except:
            print(f"  {name}: {r[:66]}")

# Storage
print("\n[STORAGE SLOTS]")
for i in range(15):
    val = get_storage(PROCEEDS, hex(i))
    if val and val != "0x" + "0"*64:
        print(f"  Slot {i}: {val}")

# Test functions
print("\n" + "=" * 60)
print("[FUNCTION TESTS]")
print("=" * 60)

test_cases = [
    ("0x3ccfd60b", "withdraw()", "0x0"),
    ("0x4e71d92d", "claim()", "0x0"),
    ("0x5f4f932f", "getProceeds()", "0x0"),
    ("0xd0e30db0", "deposit()", "0xde0b6b3a7640000"),
    ("0x06fdde03", "name()", "0x0"),
]

for sel, name, value in test_cases:
    result = estimate_gas(PROCEEDS, sel, value=value)
    if result:
        if 'result' in result:
            gas = int(result['result'], 16)
            print(f"  [+] {name} - gas: {gas}")
        elif 'error' in result:
            err = result['error'].get('message', '')[:60]
            print(f"  [-] {name}: {err}")

print("\n" + "=" * 80)
print("ANALYSIS COMPLETE")
print("=" * 80)
