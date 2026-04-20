#!/usr/bin/env python3
"""
CLAUDE.md Methodology - Deep Protocol Analysis
Focus on: Composition, Boundaries, Oracle, Flash Loan vectors
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

# Load contracts
with open("contracts.txt", "r") as f:
    contracts = [line.strip() for line in f if line.strip().startswith("0x")]

print("=" * 80)
print("CLAUDE.MD DEEP PROTOCOL ANALYSIS")
print("Focus: Composition, Boundaries, Oracle, Flash Loan Attack Surfaces")
print("=" * 80)

# Identify DeFi protocols with complex logic
defi_patterns = {
    "vault": ["deposit", "withdraw", "redeem", "mint", "convertToAssets", "convertToShares"],
    "lending": ["borrow", "repay", "liquidate", "collateral", "healthFactor"],
    "amm": ["swap", "addLiquidity", "removeLiquidity", "getAmountOut", "reserve"],
    "staking": ["stake", "unstake", "claim", "reward", "epoch"],
    "oracle": ["getPrice", "latestAnswer", "latestRoundData", "observe", "consult"],
}

interesting_contracts = []

for i, addr in enumerate(contracts):
    if i % 100 == 0:
        print(f"Scanning {i}/{len(contracts)}...")
    
    # Get balance
    bal = rpc_call("eth_getBalance", [addr, "latest"])
    balance = int(bal['result'], 16) / 1e18 if bal and 'result' in bal else 0
    
    if balance < 50:  # Focus on high value
        continue
    
    # Get source
    time.sleep(0.2)
    source = get_source(addr)
    if not source:
        continue
    
    src = source.get("SourceCode", "")
    name = source.get("ContractName", "")
    
    if not src:
        continue
    
    # Identify protocol type
    protocol_type = None
    for ptype, patterns in defi_patterns.items():
        matches = sum(1 for p in patterns if p.lower() in src.lower())
        if matches >= 2:
            protocol_type = ptype
            break
    
    if protocol_type:
        # Check for vulnerability indicators
        vuln_indicators = []
        
        # 1. Share/asset calculation (first depositor attack surface)
        if "totalSupply" in src and ("convertTo" in src or "previewDeposit" in src):
            vuln_indicators.append("SHARE_CALCULATION")
        
        # 2. Oracle dependency
        if "price" in src.lower() and ("chainlink" in src.lower() or "oracle" in src.lower()):
            vuln_indicators.append("ORACLE_DEPENDENT")
        
        # 3. External calls before state update (reentrancy surface)
        if ".call" in src and "nonReentrant" not in src:
            vuln_indicators.append("POTENTIAL_REENTRANCY")
        
        # 4. Flash loan callback
        if "flashLoan" in src or "onFlashLoan" in src or "executeOperation" in src:
            vuln_indicators.append("FLASH_LOAN_ENABLED")
        
        # 5. Unchecked arithmetic in older versions
        compiler = source.get("CompilerVersion", "")
        if ("0.6" in compiler or "0.7" in compiler) and "SafeMath" not in src:
            vuln_indicators.append("UNCHECKED_MATH")
        
        # 6. Price manipulation surface
        if "getReserves" in src or "slot0" in src:
            vuln_indicators.append("AMM_PRICE_SURFACE")
        
        if vuln_indicators:
            interesting_contracts.append({
                "address": addr,
                "name": name,
                "balance": balance,
                "type": protocol_type,
                "indicators": vuln_indicators
            })
            print(f"\n[INTERESTING] {addr}")
            print(f"  Name: {name}")
            print(f"  Balance: {balance:.2f} ETH")
            print(f"  Type: {protocol_type}")
            print(f"  Indicators: {vuln_indicators}")

print("\n" + "=" * 80)
print(f"Found {len(interesting_contracts)} contracts with potential attack surfaces")
print("=" * 80)

# Save for further analysis
with open("interesting_protocols.json", "w") as f:
    json.dump(interesting_contracts, f, indent=2)

