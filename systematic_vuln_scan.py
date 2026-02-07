#!/usr/bin/env python3
"""
Systematic vulnerability scan focusing on:
1. Zero owner addresses
2. Callable critical functions
3. Proxy implementation checks
"""
import json
import subprocess
import time

RPC = "https://mainnet.infura.io/v3/bfc7283659224dd6b5124ebbc2b14e2c"

def rpc_call(method, params):
    payload = {"jsonrpc": "2.0", "method": method, "params": params, "id": 1}
    cmd = ["curl", "-s", "-X", "POST", "-H", "Content-Type: application/json",
           "-d", json.dumps(payload), RPC]
    result = subprocess.run(cmd, capture_output=True, text=True)
    try:
        return json.loads(result.stdout)
    except:
        return None

def eth_call(to, data):
    return rpc_call("eth_call", [{"to": to, "data": data}, "latest"])

ATTACKER = "0xDeaDbeefdEAdbeefdEadbEEFdeadbeEFdEaDbeeF"

# Load contracts
with open("contracts.txt", "r") as f:
    contracts = [line.strip() for line in f if line.strip().startswith("0x")]

print("=" * 80)
print("SYSTEMATIC VULNERABILITY SCAN")
print("=" * 80)
print(f"Scanning {len(contracts)} contracts...")

# Skip already analyzed
skip = set([
    "0xbd6ed4969d9e52032ee3573e643f6a1bdc0a7e1e",
    "0x3885b0c18e3c4ab0ca2b8dc99771944404687628",
    # ... add more as needed
])

zero_owner = []
callable_critical = []

for i, addr in enumerate(contracts):
    if addr.lower() in [s.lower() for s in skip]:
        continue
    
    # Get balance
    bal = rpc_call("eth_getBalance", [addr, "latest"])
    balance = int(bal['result'], 16) / 1e18 if bal and 'result' in bal else 0
    
    if balance < 10:  # Skip low value
        continue
    
    # Check owner()
    owner_resp = eth_call(addr, "0x8da5cb5b")
    owner = None
    if owner_resp and "result" in owner_resp:
        result = owner_resp["result"]
        if result and len(result) >= 42:
            owner = "0x" + result[-40:]
            
            if owner == "0x0000000000000000000000000000000000000000":
                zero_owner.append((addr, balance))
                print(f"[ZERO OWNER] {addr}: {balance:.2f} ETH")
    
    # Check callable selfdestruct/upgrade functions
    critical_funcs = [
        ("0xff9913e8", "kill()"),
        ("0x41c0e1b5", "destroy()"),
        ("0x00f55d9d", "destroy(address)"),
        ("0xcbf0b0c0", "kill(address)"),
        ("0x3659cfe6", "upgradeTo(address)"),
    ]
    
    for sel, name in critical_funcs:
        gas_resp = rpc_call("eth_estimateGas", [{"from": ATTACKER, "to": addr, "data": sel}, "latest"])
        if gas_resp and "result" in gas_resp:
            gas = int(gas_resp["result"], 16)
            if gas > 21100:
                callable_critical.append((addr, balance, name, gas))
                print(f"[CRITICAL FUNC] {addr}: {balance:.2f} ETH - {name} callable (gas={gas})")
    
    if i % 50 == 0:
        print(f"Progress: {i}/{len(contracts)}")
    
    time.sleep(0.1)

print("\n" + "=" * 80)
print("SUMMARY")
print("=" * 80)

print(f"\nZero Owner Contracts: {len(zero_owner)}")
for addr, bal in zero_owner:
    print(f"  {addr}: {bal:.2f} ETH")

print(f"\nCallable Critical Functions: {len(callable_critical)}")
for addr, bal, func, gas in callable_critical:
    print(f"  {addr}: {bal:.2f} ETH - {func}")

