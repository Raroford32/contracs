#!/usr/bin/env python3
"""
Scanner for Vault Inflation / First Depositor attacks
Looking for:
1. Vaults with totalSupply == 0 or very small
2. Contracts using balanceOf(this) in share calculations
3. Empty vaults with deposit functions
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
print("VAULT INFLATION / FIRST DEPOSITOR ATTACK SCANNER")
print("=" * 80)

# Load contracts
with open("contracts.txt", "r") as f:
    contracts = [line.strip() for line in f if line.strip().startswith("0x")]

# Function selectors
TOTAL_SUPPLY = "0x18160ddd"
TOTAL_ASSETS = "0x01e1d114"  # ERC4626
CONVERT_TO_SHARES = "0xc6e6f592"  # ERC4626 convertToShares(uint256)
CONVERT_TO_ASSETS = "0x07a2d13a"  # ERC4626 convertToAssets(uint256)
DEPOSIT = "0x6e553f65"  # ERC4626 deposit(uint256,address)
DEPOSIT_ETH = "0xd0e30db0"  # deposit()
MINT = "0x1249c58b"  # mint()
PREVIEW_DEPOSIT = "0xef8b30f7"  # previewDeposit(uint256)

vulnerable_vaults = []

print(f"\nScanning {len(contracts)} contracts...")

for i, addr in enumerate(contracts):
    if i % 100 == 0:
        print(f"Progress: {i}/{len(contracts)}")

    balance = get_balance(addr)
    if balance < 5:  # Skip low value contracts
        continue

    code = get_code(addr)
    if len(code) < 200:  # Skip Parity wallets
        continue

    # Check totalSupply
    ts_result = eth_call(addr, TOTAL_SUPPLY)
    total_supply = None
    if ts_result and ts_result.get('result') and ts_result['result'] not in ["0x", ""]:
        try:
            total_supply = int(ts_result['result'], 16)
        except:
            pass

    # Check totalAssets (ERC4626)
    ta_result = eth_call(addr, TOTAL_ASSETS)
    total_assets = None
    if ta_result and ta_result.get('result') and ta_result['result'] not in ["0x", ""]:
        try:
            total_assets = int(ta_result['result'], 16)
        except:
            pass

    # Check if deposit/mint is callable
    deposit_callable = False
    deposit_gas = 0
    mint_callable = False
    mint_gas = 0

    # Test deposit with 1 ETH
    dep_result = estimate_gas(addr, DEPOSIT_ETH, value="0xde0b6b3a7640000")
    if dep_result and 'result' in dep_result:
        gas = int(dep_result['result'], 16)
        if gas > 21000 and gas < 500000:
            deposit_callable = True
            deposit_gas = gas

    # Test mint
    mint_result = estimate_gas(addr, MINT, value="0xde0b6b3a7640000")
    if mint_result and 'result' in mint_result:
        gas = int(mint_result['result'], 16)
        if gas > 21000 and gas < 500000:
            mint_callable = True
            mint_gas = gas

    # Flag interesting cases
    interesting = False
    reason = []

    # Case 1: totalSupply is 0 and deposit is callable
    if total_supply == 0 and (deposit_callable or mint_callable):
        interesting = True
        reason.append("EMPTY_VAULT: totalSupply=0, deposit callable")

    # Case 2: totalSupply very small (< 1000)
    if total_supply is not None and 0 < total_supply < 1000:
        interesting = True
        reason.append(f"TINY_SUPPLY: totalSupply={total_supply}")

    # Case 3: Has totalAssets function (ERC4626)
    if total_assets is not None:
        interesting = True
        reason.append(f"ERC4626: totalAssets={total_assets/1e18:.4f}")

    # Case 4: Large balance with no/tiny totalSupply
    if balance > 50 and (total_supply == 0 or (total_supply is not None and total_supply < 10**15)):
        interesting = True
        reason.append(f"LARGE_BALANCE_EMPTY: {balance:.2f} ETH but low supply")

    if interesting:
        finding = {
            "address": addr,
            "balance": balance,
            "total_supply": total_supply,
            "total_assets": total_assets,
            "deposit_callable": deposit_callable,
            "deposit_gas": deposit_gas,
            "mint_callable": mint_callable,
            "mint_gas": mint_gas,
            "reasons": reason
        }
        vulnerable_vaults.append(finding)
        print(f"\n[POTENTIAL] {addr}")
        print(f"  Balance: {balance:.2f} ETH")
        print(f"  TotalSupply: {total_supply}")
        print(f"  TotalAssets: {total_assets}")
        print(f"  Deposit: {'YES' if deposit_callable else 'NO'} (gas: {deposit_gas})")
        print(f"  Reasons: {', '.join(reason)}")

    time.sleep(0.15)

print("\n" + "=" * 80)
print(f"FOUND {len(vulnerable_vaults)} POTENTIAL TARGETS")
print("=" * 80)

# Deep analysis of top candidates
for finding in sorted(vulnerable_vaults, key=lambda x: -x['balance'])[:5]:
    addr = finding['address']
    print(f"\n{'='*70}")
    print(f"[DEEP ANALYSIS] {addr}")
    print(f"Balance: {finding['balance']:.4f} ETH")
    print("=" * 70)

    source_data = get_source(addr)
    if source_data:
        src = source_data.get("SourceCode", "")
        contract_name = source_data.get("ContractName", "Unknown")
        print(f"Contract: {contract_name}")

        if src.startswith("{{"):
            try:
                src_json = json.loads(src[1:-1])
                sources = src_json.get("sources", {})
                src = "\n".join([v.get("content", "") for v in sources.values()])
            except:
                pass

        # Look for vulnerable patterns
        patterns = [
            "balanceOf(address(this))",
            "address(this).balance",
            "totalSupply == 0",
            "_totalSupply == 0",
            "shares * balance",
            "amount * totalSupply / totalAssets",
            "assets * totalSupply",
        ]

        print("\n[VULNERABLE PATTERNS]")
        lines = src.split('\n')
        for i, line in enumerate(lines):
            for pattern in patterns:
                if pattern.lower() in line.lower():
                    print(f"  Line {i+1}: {line.strip()[:70]}")

    time.sleep(0.5)

# Save findings
with open("vault_inflation_findings.json", "w") as f:
    json.dump(vulnerable_vaults, f, indent=2)

print(f"\n[*] Findings saved to vault_inflation_findings.json")
