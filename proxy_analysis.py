#!/usr/bin/env python3
"""
Analyze AdminUpgradeabilityProxy contracts for:
1. Uninitialized implementations
2. Admin takeover possibilities
3. Storage collision attacks
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

def eth_call(to, data, from_addr="0x0000000000000000000000000000000000000001"):
    result = rpc_call("eth_call", [{"to": to, "data": data, "from": from_addr}, "latest"])
    return result

def estimate_gas(to, data, from_addr="0x0000000000000000000000000000000000000001"):
    result = rpc_call("eth_estimateGas", [{"to": to, "data": data, "from": from_addr}])
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

# Standard EIP-1967 storage slots
IMPLEMENTATION_SLOT = "0x360894a13ba1a3210667c828492db98dca3e2076cc3735a920a3ca505d382bbc"
ADMIN_SLOT = "0xb53127684a568b3173ae13b9f8a6016e243e63b6e8ee1178d6a717850b5d6103"
BEACON_SLOT = "0xa3f0ad74e5423aebfd80d3ef4346578335a9a72aeaee59ff6cb3582b35133d50"

# High-value proxy contracts
proxies = [
    {"address": "0xf74bf048138a2b8f825eccabed9e02e481a0f6c0", "name": "AdminUpgradeabilityProxy", "balance": 291.7},
    {"address": "0xb8ff313d33b0e841b6b83243f6e2935166de87c1", "name": "AdminUpgradeabilityProxy", "balance": 101.0},
    {"address": "0x0fa10d440522d4235c55811dc1adf4a875c16d00", "name": "TransparentUpgradeableProxy", "balance": 85.9},
    {"address": "0x27a94869341838d5783368a8503fda5fbcd7987c", "name": "AdminUpgradeabilityProxy", "balance": 84.3},
    {"address": "0x1a26ef6575b7bdb71d1c0c3bccc4c95375abbc1f", "name": "Proxy__L1LiquidityPoolArguments", "balance": 113.9},
]

print("=" * 80)
print("PROXY CONTRACT ANALYSIS")
print("=" * 80)

for proxy in proxies:
    addr = proxy['address']
    name = proxy['name']

    print(f"\n{'='*70}")
    print(f"[PROXY] {name} - {addr}")
    print(f"[BALANCE] {get_balance(addr):.4f} ETH")
    print("=" * 70)

    # 1. Check EIP-1967 slots
    print("\n[EIP-1967 Slots]")

    impl = get_storage(addr, IMPLEMENTATION_SLOT)
    if impl and impl != "0x" + "0"*64:
        impl_addr = "0x" + impl[26:]
        print(f"  Implementation: {impl_addr}")

        # Check if implementation has code
        impl_code = get_code(impl_addr)
        print(f"  Implementation code length: {len(impl_code)} chars")

        # Check if implementation is initialized
        impl_storage_0 = get_storage(impl_addr, "0x0")
        print(f"  Implementation slot 0: {impl_storage_0}")

        # Try calling initialize on implementation directly
        init_selectors = {
            "initialize()": "0x8129fc1c",
            "initialize(address)": "0xc4d66de8",
            "initialize(address,address)": "0x485cc955",
        }

        print("\n  [Implementation Initialization Tests]")
        for func, sel in init_selectors.items():
            data = sel
            if "address" in func:
                data = sel + "0000000000000000000000000000000000000000000000000000000000000001"
            if func.count("address") == 2:
                data = data[:10+64] + "0000000000000000000000000000000000000000000000000000000000000001"

            result = estimate_gas(impl_addr, data)
            if result:
                if 'result' in result:
                    gas = int(result['result'], 16)
                    print(f"    [!!!] {func} on impl callable - gas: {gas}")
                elif 'error' in result:
                    err = result['error'].get('message', '')[:50]
                    print(f"    [-] {func}: {err}")
    else:
        print("  Implementation: Not found at EIP-1967 slot")

    admin = get_storage(addr, ADMIN_SLOT)
    if admin and admin != "0x" + "0"*64:
        admin_addr = "0x" + admin[26:]
        print(f"\n  Admin: {admin_addr}")

        # Check if admin is EOA or contract
        admin_code = get_code(admin_addr)
        if len(admin_code) <= 2:
            print(f"  Admin is EOA (no code)")
        else:
            print(f"  Admin is contract ({len(admin_code)} chars)")

        # Check admin balance
        admin_bal = get_balance(admin_addr)
        print(f"  Admin ETH balance: {admin_bal:.4f} ETH")

    # 2. Check standard storage slots
    print("\n[Standard Storage]")
    for i in range(5):
        slot = get_storage(addr, hex(i))
        if slot and slot != "0x" + "0"*64:
            print(f"  Slot {i}: {slot}")

    # 3. Try admin functions via proxy
    print("\n[Proxy Admin Functions]")

    admin_funcs = {
        "admin()": "0xf851a440",
        "implementation()": "0x5c60da1b",
        "changeAdmin(address)": "0x8f283970",
        "upgradeTo(address)": "0x3659cfe6",
    }

    for func, sel in admin_funcs.items():
        data = sel
        if "address" in func:
            data = sel + "0000000000000000000000000000000000000000000000000000000000000001"

        result = estimate_gas(addr, data)
        if result:
            if 'result' in result:
                gas = int(result['result'], 16)
                print(f"  [+] {func} callable - gas: {gas}")
            elif 'error' in result:
                err = result['error'].get('message', '')[:50]
                if 'revert' in err.lower():
                    print(f"  [-] {func}: Protected")
                else:
                    print(f"  [?] {func}: {err}")

    # 4. Check for common vulnerable functions through proxy
    print("\n[Vulnerable Function Tests Through Proxy]")

    vuln_funcs = {
        "withdraw()": "0x3ccfd60b",
        "emergencyWithdraw()": "0xdb2e21bc",
        "initialize()": "0x8129fc1c",
        "transferOwnership(address)": "0xf2fde38b",
        "renounceOwnership()": "0x715018a6",
    }

    for func, sel in vuln_funcs.items():
        data = sel
        if "address" in func:
            data = sel + "0000000000000000000000000000000000000000000000000000000000000001"

        result = estimate_gas(addr, data)
        if result:
            if 'result' in result:
                gas = int(result['result'], 16)
                print(f"  [!!] {func} callable - gas: {gas}")
            elif 'error' in result:
                err = result['error'].get('message', '')[:50]

print("\n" + "=" * 80)
print("PROXY ANALYSIS COMPLETE")
print("=" * 80)
