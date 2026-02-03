#!/usr/bin/env python3
"""
Deep analysis of high-value unknown and DeFi contracts
"""
import json
import subprocess
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

def get_source(addr):
    """Get verified source from Etherscan"""
    url = f"https://api.etherscan.io/v2/api?chainid=1&module=contract&action=getsourcecode&address={addr}&apikey={ETHERSCAN_API}"
    result = subprocess.run(["curl", "-s", url], capture_output=True, text=True)
    try:
        data = json.loads(result.stdout)
        if data.get("status") == "1" and data.get("result"):
            return data["result"][0]
        return None
    except:
        return None

def get_balance(addr):
    resp = rpc_call("eth_getBalance", [addr, "latest"])
    if resp and "result" in resp:
        return int(resp["result"], 16) / 1e18
    return 0

# High-value targets to analyze (excluding Parity proxies)
targets = [
    ("0xa1a111bc074c9cfa781f0c38e63bd51c91b8af00", 314.15, "UNKNOWN_CONTRACT"),
    ("0xf74bf048138a2b8f825eccabed9e02e481a0f6c0", 291.71, "UNKNOWN_CONTRACT"),
    ("0x3a3fba79302144f06f49ffde69ce4b7f6ad4dd3d", 284.26, "DEFI_CONTRACT"),
    ("0x3a5fb0f79c258942c1acf8142cbc601c1aff1ac4", 262.71, "EOA_OR_SELFDESTRUCTED"),
    ("0xa7d9e842efb252389d613da88eda3731512e40bd", 258.56, "DEFI_CONTRACT"),
    ("0x60cd862c9c687a9de49aecdc3a99b74a4fc54ab6", 246.69, "DEFI_CONTRACT"),
    ("0x27321f84704a599ab740281e285cc4463d89a3d5", 234.42, "UNKNOWN_CONTRACT"),
    ("0x5eee354e36ac51e9d3f7283005cab0c55f423b23", 216.29, "UNKNOWN_CONTRACT"),
    ("0x8754f54074400ce745a7ceddc928fb1b7e985ed6", 215.18, "UNKNOWN_CONTRACT"),
    ("0x6198db1e212846b9ecbaee75182a456077c1ccb2", 212.88, "EOA_OR_SELFDESTRUCTED"),
]

print("=" * 80)
print("DEEP ANALYSIS OF HIGH-VALUE TARGETS")
print("=" * 80)

for addr, expected_bal, ctype in targets:
    print(f"\n{'='*80}")
    print(f"ADDRESS: {addr}")
    print(f"Expected Balance: {expected_bal:.2f} ETH | Type: {ctype}")
    print("=" * 80)
    
    # Verify balance
    balance = get_balance(addr)
    print(f"Current Balance: {balance:.2f} ETH")
    
    # Get bytecode
    code_resp = rpc_call("eth_getCode", [addr, "latest"])
    code = code_resp.get("result", "0x") if code_resp else "0x"
    print(f"Bytecode Length: {(len(code)-2)//2} bytes")
    
    if code == "0x":
        print("  -> No code (EOA or selfdestructed)")
        continue
    
    # Try to get source
    time.sleep(0.3)
    source = get_source(addr)
    
    if source:
        contract_name = source.get("ContractName", "Unknown")
        compiler = source.get("CompilerVersion", "Unknown")
        src_code = source.get("SourceCode", "")
        
        print(f"Contract Name: {contract_name}")
        print(f"Compiler: {compiler}")
        
        if src_code:
            print(f"Source Code: {len(src_code)} chars")
            
            # Check for vulnerability patterns
            vuln_patterns = [
                ("selfdestruct", "SELFDESTRUCT found"),
                ("delegatecall", "DELEGATECALL found"),
                ("tx.origin", "TX.ORIGIN check found"),
                (".call.value", "Low-level call with value"),
                (".call{value", "Low-level call with value (new syntax)"),
                ("withdraw", "Withdraw function exists"),
                ("transfer(", "Transfer function exists"),
            ]
            
            for pattern, msg in vuln_patterns:
                if pattern.lower() in src_code.lower():
                    print(f"  [!] {msg}")
        else:
            print("  Source not verified on Etherscan")
    else:
        print("  Could not fetch source from Etherscan")
    
    # Check storage slots for common patterns
    print("\nStorage Analysis:")
    for slot in range(5):
        storage = rpc_call("eth_getStorageAt", [addr, hex(slot), "latest"])
        if storage and "result" in storage:
            val = storage["result"]
            val_int = int(val, 16) if val else 0
            if val_int != 0:
                if val_int < 2**160 and val_int > 1000:
                    # Might be an address
                    print(f"  Slot {slot}: 0x{val[-40:]} (possible address)")
                elif val_int < 1000:
                    print(f"  Slot {slot}: {val_int} (small integer)")
                else:
                    print(f"  Slot {slot}: {val[:18]}... (large value)")
    
    time.sleep(0.5)

