#!/usr/bin/env python3
"""
Verify if setOwner callable contracts are real vulnerabilities
Check if they're Parity wallets vs actual exploitable contracts
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

# Top findings from previous scan
targets = [
    ("0x2ccfa2acf69a016d3c1d88e0e7fa1bdb7c55ddd2", 514.6),
    ("0xc32050abac7dbfef4f4e73e9caa8938b1d75b15e", 340.2),
    ("0x7100c7ce94607ef689c016c3b03fed3b82f32945", 327.5),
    ("0xa08c1134cd73ad4189aa8b4749f5bbffbd70ba30", 325.2),
    ("0x2f9f02f2ba99ff5c755e286e0f76c8f8dc310c8a", 320.0),
    ("0xa1a111bc074c9cfa781f0c38e63bd51c91b8af00", 314.1),
]

# Parity multisig patterns
PARITY_PROXY_CODE = "0x60606040523615610020576000357c01000000000000000000000000000000000000000000000000000000009004806361"
PARITY_CODE_49BYTE = 49 * 2 + 2  # 100 chars including 0x prefix

print("=" * 80)
print("VERIFYING SETOWNER FINDINGS")
print("=" * 80)

for addr, balance in targets:
    print(f"\n{'='*70}")
    print(f"[CONTRACT] {addr}")
    print(f"[BALANCE] {get_balance(addr):.4f} ETH")
    print("=" * 70)

    # Get code
    code = get_code(addr)
    print(f"Code length: {len(code)} chars")

    # Check for Parity proxy pattern
    if len(code) < 200:
        print("[PATTERN] Short code - likely Parity wallet proxy")

    if code.startswith(PARITY_PROXY_CODE[:50]):
        print("[PATTERN] Matches Parity proxy code start")

    # Check for 49-byte minimal proxy
    if code.startswith("0x363d3d373d3d3d363d73"):
        print("[PATTERN] Minimal proxy (EIP-1167)")

    # Get source
    source = get_source(addr)
    if source:
        name = source.get("ContractName", "Unknown")
        src = source.get("SourceCode", "")
        print(f"Contract Name: {name}")
        print(f"Source length: {len(src)}")

        if "WalletLibrary" in name or "Wallet" in name:
            print("[PATTERN] Parity-style wallet name")

        if "delegatecall" in src.lower():
            print("[PATTERN] Contains delegatecall")
    else:
        print("No verified source")

    # Test multiple function selectors to see if they all return similar gas
    test_selectors = [
        ("setOwner(address)", "0x13af4035"),
        ("foo()", "0xc2985578"),
        ("randomFunc()", "0x12345678"),
        ("withdraw()", "0x3ccfd60b"),
        ("execute(address,uint256,bytes)", "0xb61d27f6"),
    ]

    print("\n[GAS ESTIMATES]")
    gas_values = []
    for name, sel in test_selectors:
        data = sel
        if "address" in name:
            data = sel + "0" * 64
        if "uint256" in name:
            data += "0" * 64
        if "bytes" in name:
            data += "0" * 64

        result = estimate_gas(addr, data)
        if result and 'result' in result:
            gas = int(result['result'], 16)
            gas_values.append(gas)
            print(f"  {name}: {gas}")
        elif result and 'error' in result:
            err = result['error'].get('message', '')[:40]
            print(f"  {name}: ERROR - {err}")
            gas_values.append(-1)

    # If all gas values are similar (within 10%), it's likely Parity proxy
    if len([g for g in gas_values if g > 0]) >= 3:
        positive_gas = [g for g in gas_values if g > 0]
        avg = sum(positive_gas) / len(positive_gas)
        variance = max(positive_gas) - min(positive_gas)
        variance_pct = variance / avg * 100

        print(f"\n[ANALYSIS]")
        print(f"  Gas variance: {variance_pct:.1f}%")
        if variance_pct < 20:
            print("  LIKELY PARITY WALLET - All functions have similar gas (echo pattern)")
        else:
            print("  POSSIBLE REAL CONTRACT - Functions have different gas costs")

print("\n" + "=" * 80)
print("VERIFICATION COMPLETE")
print("=" * 80)
