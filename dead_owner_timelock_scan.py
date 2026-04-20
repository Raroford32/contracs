#!/usr/bin/env python3
"""
Scan for contracts with:
1. Zero address owner
2. Dead (no code) owner contract
3. Expired time locks
4. Abandoned contracts
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
print("DEAD OWNER / EXPIRED TIMELOCK SCANNER")
print("=" * 80)

# Load contracts
with open("contracts.txt", "r") as f:
    contracts = [line.strip() for line in f if line.strip().startswith("0x")]

findings = []

# Owner-related selectors
OWNER_SELECTORS = {
    "owner()": "0x8da5cb5b",
    "admin()": "0xf851a440",
    "governance()": "0x5aa6e675",
    "controller()": "0xf77c4791",
    "operator()": "0x570ca735",
}

print("\n[SCANNING FOR DEAD/ZERO OWNERS]")
print("-" * 50)

for i, addr in enumerate(contracts):
    if i % 30 == 0:
        print(f"Progress: {i}/{len(contracts)}...")

    balance = get_balance(addr)
    if balance < 40:
        continue

    time.sleep(0.15)

    # Check owner patterns
    for func_name, selector in OWNER_SELECTORS.items():
        result = eth_call(addr, selector)
        if result and result.get('result') and len(result['result']) >= 66:
            try:
                owner = "0x" + result['result'][26:66]
                owner_int = int(owner, 16)

                # Check for zero address
                if owner_int == 0:
                    findings.append({
                        "address": addr,
                        "balance": balance,
                        "issue": "ZERO_OWNER",
                        "owner_func": func_name,
                        "owner_addr": owner
                    })
                    print(f"\n[ZERO OWNER!] {addr[:20]}... ({balance:.1f} ETH)")
                    print(f"  {func_name} = {owner}")

                    # Test if admin functions are callable
                    test_funcs = [
                        ("0x3ccfd60b", "withdraw()"),
                        ("0x853828b6", "withdrawAll()"),
                        ("0xe9fad8ee", "exit()"),
                        ("0x2e1a7d4d", "withdraw(uint256)"),
                    ]
                    for sel, desc in test_funcs:
                        data = sel
                        if "uint256" in desc:
                            data += "0" * 64
                        gas_result = estimate_gas(addr, data)
                        if gas_result and 'result' in gas_result:
                            gas = int(gas_result['result'], 16)
                            if gas < 500000:
                                print(f"  [+] {desc} CALLABLE! Gas: {gas}")

                # Check for dead owner (contract with no code)
                elif owner_int > 0:
                    owner_code = get_code(owner)
                    if owner_code == "0x" or len(owner_code) < 10:
                        findings.append({
                            "address": addr,
                            "balance": balance,
                            "issue": "DEAD_OWNER",
                            "owner_func": func_name,
                            "owner_addr": owner
                        })
                        print(f"\n[DEAD OWNER!] {addr[:20]}... ({balance:.1f} ETH)")
                        print(f"  {func_name} = {owner} (NO CODE)")

            except:
                pass

    # Check for time-locked functions
    # Look for timelock/lock end timestamps
    timelock_selectors = [
        ("lockEndTime()", "0x16c38b3c"),
        ("endTime()", "0x3197cbb6"),
        ("unlockTime()", "0x251c1aa3"),
        ("releaseTime()", "0x0b97bc86"),
    ]

    for func_name, selector in timelock_selectors:
        result = eth_call(addr, selector)
        if result and result.get('result') and result['result'] != "0x" + "0"*64:
            try:
                timestamp = int(result['result'], 16)
                if timestamp > 0 and timestamp < 2000000000:  # Looks like a timestamp
                    current_time = int(time.time())
                    if timestamp < current_time:
                        # Lock has expired!
                        findings.append({
                            "address": addr,
                            "balance": balance,
                            "issue": "EXPIRED_LOCK",
                            "lock_func": func_name,
                            "lock_time": timestamp,
                            "expired_ago": current_time - timestamp
                        })
                        expired_days = (current_time - timestamp) / 86400
                        print(f"\n[EXPIRED LOCK!] {addr[:20]}... ({balance:.1f} ETH)")
                        print(f"  {func_name} = {timestamp}")
                        print(f"  Expired {expired_days:.0f} days ago")

                        # Test if withdraw is now possible
                        withdraw_funcs = [
                            ("0x3ccfd60b", "withdraw()"),
                            ("0x51cff8d9", "withdraw(address)"),
                            ("0x2e1a7d4d", "withdraw(uint256)"),
                        ]
                        for sel, desc in withdraw_funcs:
                            data = sel
                            if "address" in desc:
                                data += "0" * 56 + "0000000000000001"
                            if "uint256" in desc:
                                data += "0" * 64
                            gas_result = estimate_gas(addr, data)
                            if gas_result and 'result' in gas_result:
                                gas = int(gas_result['result'], 16)
                                print(f"  [+] {desc} CALLABLE! Gas: {gas}")
            except:
                pass

# Summary
print("\n" + "=" * 80)
print("SCAN SUMMARY")
print("=" * 80)

zero_owners = [f for f in findings if f['issue'] == 'ZERO_OWNER']
dead_owners = [f for f in findings if f['issue'] == 'DEAD_OWNER']
expired_locks = [f for f in findings if f['issue'] == 'EXPIRED_LOCK']

print(f"\n[ZERO OWNERS] {len(zero_owners)} contracts")
for f in zero_owners[:10]:
    print(f"  {f['address'][:20]}... - {f['balance']:.1f} ETH")

print(f"\n[DEAD OWNERS] {len(dead_owners)} contracts")
for f in dead_owners[:10]:
    print(f"  {f['address'][:20]}... - {f['balance']:.1f} ETH - Owner: {f['owner_addr'][:16]}...")

print(f"\n[EXPIRED LOCKS] {len(expired_locks)} contracts")
for f in expired_locks[:10]:
    print(f"  {f['address'][:20]}... - {f['balance']:.1f} ETH - Expired {f['expired_ago']/86400:.0f} days ago")

# Save
with open("dead_owner_findings.json", "w") as f:
    json.dump(findings, f, indent=2)

print("\n[*] Saved to dead_owner_findings.json")
