#!/usr/bin/env python3
"""
Complete analysis of ArbitrageETHStaking contract
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

def eth_call(to, data):
    return rpc_call("eth_call", [{"to": to, "data": data}, "latest"])

def get_source(addr):
    url = f"https://api.etherscan.io/v2/api?chainid=1&module=contract&action=getsourcecode&address={addr}&apikey={ETHERSCAN_API}"
    result = subprocess.run(["curl", "-s", url], capture_output=True, text=True)
    try:
        data = json.loads(result.stdout)
        if data.get("status") == "1" and data.get("result"):
            return data["result"][0]
        return None
    except:
        return None

ARBIT = "0x5eee354e36ac51e9d3f7283005cab0c55f423b23"

# Get full source and print withdraw functions
source = get_source(ARBIT)
if source:
    src = source.get("SourceCode", "")
    
    # Print the withdraw-related code
    lines = src.split('\n')
    print("=== WITHDRAW FUNCTIONS ===\n")
    
    in_func = False
    brace_count = 0
    for i, line in enumerate(lines):
        if 'function withdraw' in line.lower() or 'function withdrawAll' in line.lower():
            in_func = True
            brace_count = 0
        
        if in_func:
            print(f"{i:3d}: {line}")
            brace_count += line.count('{') - line.count('}')
            if brace_count <= 0 and '{' in src[sum(len(l)+1 for l in lines[:i]):]:
                if line.strip() == '}' or ('}' in line and brace_count == 0):
                    in_func = False
                    print("---")

print("\n=== CONTRACT STATE ANALYSIS ===\n")

# Check key state variables
# getBalance() - 0x12065fe0
bal_result = eth_call(ARBIT, "0x12065fe0")
if bal_result and "result" in bal_result:
    contract_bal = int(bal_result["result"], 16)
    print(f"getBalance(): {contract_bal / 1e18:.4f} ETH")

# Check actual balance
actual_bal = rpc_call("eth_getBalance", [ARBIT, "latest"])
if actual_bal and "result" in actual_bal:
    print(f"Actual ETH balance: {int(actual_bal['result'], 16) / 1e18:.4f} ETH")

# Storage analysis for globalFactor
# globalFactor is at slot 3 based on contract layout
# mapping personalFactorLedger_ - slot 0
# mapping balanceLedger_ - slot 1
# uint256 minBuyIn - slot 2
# uint256 stakingPrecent - slot 3
# uint256 globalFactor - slot 4

for slot in range(6):
    storage = rpc_call("eth_getStorageAt", [ARBIT, hex(slot), "latest"])
    if storage and "result" in storage:
        val = int(storage["result"], 16)
        if slot == 2:
            print(f"minBuyIn (slot 2): {val / 1e18:.6f} ETH")
        elif slot == 3:
            print(f"stakingPrecent (slot 3): {val}")
        elif slot == 4:
            print(f"globalFactor (slot 4): {val} ({val / 1e21:.4f} * 10e21)")
        elif val != 0:
            print(f"Slot {slot}: {val}")

# Check ethBalanceOf for a few addresses
# ethBalanceOf(address) - selector: need to compute
# Actually it's a view function, let me find it

print("\n=== CHECKING USER BALANCES ===")

# ethBalanceOf(address) - Keccak256("ethBalanceOf(address)")[:4]
# = 0xb7d9a0f4 (approximate, let me check)

# From the ABI, we need the correct selector
# Let me look at the full source for function signatures

print("\n=== LOOKING FOR EXPLOITS ===")
print("""
Analysis of ArbitrageETHStaking:

1. Owner is 0x0 (renounced) - no admin functions available
2. Users can only withdraw their own balance via withdraw(amount) or withdrawAll()
3. The 216 ETH represents user deposits that earn 2% from new deposits

POTENTIAL VULNERABILITIES:
- Division rounding: globalFactor math could have precision issues
- First depositor: If contract balance = 0, special behavior
- Reentrancy: Uses .transfer() which is safe (2300 gas limit)

Let me check if contract balance can go to 0...
""")

# The withdraw functions use ethBalanceOf which calculates based on:
# balanceLedger_[user] * globalFactor * constantFactor / personalFactorLedger_[user]

# If all users withdraw, contract would be empty
# Then first depositor could exploit... but users still have funds locked

