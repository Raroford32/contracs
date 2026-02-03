#!/usr/bin/env python3
"""
Deep analysis of HashesDAO - checking for governance/execution exploits
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

HASHES_DAO = "0xbd3af18e0b7ebb30d49b253ab00788b92604552c"

print("=" * 80)
print("HASHESDAO DEEP ANALYSIS")
print("=" * 80)

print(f"\nContract: {HASHES_DAO}")
print(f"Balance: {get_balance(HASHES_DAO):.4f} ETH")

# Get source
source_data = get_source(HASHES_DAO)
if source_data:
    src = source_data.get("SourceCode", "")
    name = source_data.get("ContractName", "")
    print(f"Contract Name: {name}")

    # Parse multi-file
    if src.startswith("{{"):
        try:
            src_json = json.loads(src[1:-1])
            sources = src_json.get("sources", {})
            src = "\n".join([v.get("content", "") for v in sources.values()])
        except:
            pass
    elif src.startswith("{"):
        try:
            src_json = json.loads(src)
            sources = src_json.get("sources", {})
            src = "\n".join([v.get("content", "") for v in sources.values()])
        except:
            pass

    print(f"Source length: {len(src)} chars")

    # Find governance functions
    print("\n[Governance Functions]")

    gov_funcs = [
        "propose", "queue", "execute", "cancel",
        "castVote", "getVotes", "state"
    ]

    for func in gov_funcs:
        if func in src:
            # Find the function definition
            import re
            pattern = rf"function\s+{func}\s*\([^)]*\)"
            matches = re.findall(pattern, src, re.IGNORECASE)
            for m in matches[:2]:
                print(f"  {m[:80]}")

    # Find key patterns
    print("\n[Key Code Patterns]")

    # Look for execution logic
    lines = src.split('\n')
    for i, line in enumerate(lines):
        if ".call{" in line and "value" in line:
            print(f"  Line {i+1}: {line.strip()[:80]}")

    # Find quorum and threshold logic
    print("\n[Quorum/Threshold Logic]")
    for i, line in enumerate(lines):
        if any(p in line.lower() for p in ["quorum", "threshold", "proposalthreshold"]):
            print(f"  Line {i+1}: {line.strip()[:80]}")

# On-chain state analysis
print("\n" + "=" * 60)
print("ON-CHAIN STATE")
print("=" * 60)

# Check governance token
print("\n[Governance State]")

# proposalThreshold()
threshold = eth_call(HASHES_DAO, "0xb58131b0")
if threshold and threshold.get('result'):
    val = threshold['result']
    if val != '0x':
        print(f"  proposalThreshold(): {int(val, 16)}")

# quorumVotes() or quorum()
quorum = eth_call(HASHES_DAO, "0x24bc1a64")
if quorum and quorum.get('result'):
    val = quorum['result']
    if val != '0x':
        print(f"  quorumVotes(): {int(val, 16)}")

# proposalCount()
count = eth_call(HASHES_DAO, "0xda35c664")
if count and count.get('result'):
    val = count['result']
    if val != '0x':
        print(f"  proposalCount(): {int(val, 16)}")

# Check storage slots
print("\n[Storage Slots]")
for i in range(10):
    slot = get_storage(HASHES_DAO, hex(i))
    if slot and slot != "0x" + "0"*64:
        print(f"  Slot {i}: {slot}")
        if len(slot) == 66 and slot[2:26] == "0"*24:
            addr = "0x" + slot[26:]
            print(f"         -> address: {addr}")

# Test accessibility of key functions
print("\n[Function Accessibility]")

test_funcs = {
    "execute(uint256)": "0xfe0d94c1",
    "queue(uint256)": "0xddf0b009",
    "propose(address[],uint256[],string[],bytes[],string)": "0xda95691a",
    "cancel(uint256)": "0x40e58ee5",
    "withdraw(uint256)": "0x2e1a7d4d",
    "withdrawETH()": "0xf14210a6",
}

for func, sel in test_funcs.items():
    data = sel
    if "uint256" in func:
        data = sel + "0000000000000000000000000000000000000000000000000000000000000001"

    result = estimate_gas(HASHES_DAO, data)
    if result:
        if 'result' in result:
            gas = int(result['result'], 16)
            print(f"  [+] {func} callable - gas: {gas}")
        elif 'error' in result:
            err = result['error'].get('message', '')[:60]
            print(f"  [-] {func}: {err}")

# Check for any low-threshold governance
print("\n[Governance Attack Vector Analysis]")
print("  Checking if governance can be captured...")

# Look for Hashes token
hashes_token = eth_call(HASHES_DAO, "0xfc0c546a")  # token()
if hashes_token and hashes_token.get('result'):
    token_addr = "0x" + hashes_token['result'][26:]
    if token_addr != "0x0000000000000000000000000000000000000000":
        print(f"  Governance Token: {token_addr}")

        # Check token total supply
        ts = eth_call(token_addr, "0x18160ddd")
        if ts and ts.get('result'):
            total = int(ts['result'], 16)
            print(f"  Token TotalSupply: {total}")

print("\n" + "=" * 80)
print("ANALYSIS COMPLETE")
print("=" * 80)
