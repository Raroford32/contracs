#!/usr/bin/env python3
import json
import subprocess
import sys

ETHERSCAN_KEY = "5UWN6DNT7UZCEJYNE3J6FCVAWH4QJW255K"
RPC_URL = "https://eth-mainnet.g.alchemy.com/v2/pLXdY7rYRY10SH_UTLBGH"
DEBANK_KEY = "e0f9f5b495ec8924d0ed905a0a68f78c050fdf54"

contracts = [
    {
        "impl": "0x927a83c679a5e1a6435d6bfaef7f20d4db23e2cc",
        "proxy": "0xe6d8d8ac54461b1c5ed15740eee322043f696c08",
        "throughput": "~21K ETH"
    },
    {
        "impl": "0x5e5b726c81f43b953a62ad87e2835c85c4d9dd3b",
        "proxy": "0x5c7bcd6e7de5423a257d81b442095a1a6ced35c5",
        "throughput": "~18K ETH"
    },
    {
        "impl": "0xf7aea2f093b29afd8a804191356bfdc6358696e1",
        "proxy": "0x604dd02d620633ae427888d41bfd15e38483736e",
        "throughput": "~17K ETH"
    },
    {
        "impl": "0x322b481088143d9ff74e4169fb7f12f7808690df",
        "proxy": "0xef4fb24ad0916217251f553c0596f8edc630eb66",
        "throughput": "~16K ETH"
    },
    {
        "impl": "0xd5b3be349ed0b7c82dbd9271ce3739a381fc7aa0",
        "proxy": "0x74a09653a083691711cf8215a6ab074bb4e99ef5",
        "throughput": "~13K ETH"
    },
]

def curl_json(url):
    result = subprocess.run(["curl", "-s", url], capture_output=True, text=True)
    return json.loads(result.stdout)

def rpc_call(to, data, from_addr="0x0000000000000000000000000000000000001234"):
    payload = json.dumps({
        "jsonrpc": "2.0",
        "id": 1,
        "method": "eth_call",
        "params": [{"from": from_addr, "to": to, "data": data}, "latest"]
    })
    result = subprocess.run(
        ["curl", "-s", "-X", "POST", RPC_URL, "-H", "Content-Type: application/json", "-d", payload],
        capture_output=True, text=True
    )
    return json.loads(result.stdout)

def check_debank(proxy_addr):
    result = subprocess.run(
        ["curl", "-s", f"https://pro-openapi.debank.com/v1/user/total_balance?id={proxy_addr}",
         "-H", f"AccessKey: {DEBANK_KEY}"],
        capture_output=True, text=True
    )
    try:
        data = json.loads(result.stdout)
        return data
    except:
        return {"error": result.stdout[:200]}

for i, c in enumerate(contracts, 1):
    print(f"\n{'='*80}")
    print(f"CONTRACT {i}: {c['impl']}")
    print(f"Proxy: {c['proxy']}")
    print(f"Throughput: {c['throughput']}")
    print(f"{'='*80}")

    # Step 1: Etherscan source check
    url = f"https://api.etherscan.io/v2/api?chainid=1&module=contract&action=getsourcecode&address={c['impl']}&apikey={ETHERSCAN_KEY}"
    try:
        data = curl_json(url)
        r = data['result'][0]
        contract_name = r.get('ContractName', '')
        source = r.get('SourceCode', '')
        verified = bool(source)
        proxy_field = r.get('Proxy', '')
        impl_field = r.get('Implementation', '')
        abi_raw = r.get('ABI', '')

        print(f"  ContractName: {contract_name}")
        print(f"  Verified: {verified}")
        print(f"  Proxy field: {proxy_field}")
        print(f"  Implementation field: {impl_field}")

        has_initialize = False
        has_upgradeToAndCall = False
        has_upgradeTo = False
        init_signatures = []

        if abi_raw and abi_raw != 'Contract source code not verified':
            funcs = json.loads(abi_raw)
            names = [f.get('name', '') for f in funcs if f.get('type') == 'function']
            has_initialize = 'initialize' in names
            has_upgradeToAndCall = 'upgradeToAndCall' in names
            has_upgradeTo = 'upgradeTo' in names

            for f in funcs:
                if f.get('name') == 'initialize':
                    inputs = f.get('inputs', [])
                    sig = 'initialize(' + ','.join([inp['type'] for inp in inputs]) + ')'
                    init_signatures.append(sig)

            print(f"  Has initialize: {has_initialize}")
            print(f"  Has upgradeToAndCall: {has_upgradeToAndCall}")
            print(f"  Has upgradeTo: {has_upgradeTo}")
            if init_signatures:
                print(f"  Initialize signatures: {init_signatures}")
            print(f"  All functions: {names}")
        else:
            print(f"  ABI: Not verified / not available")

        c['contract_name'] = contract_name
        c['verified'] = verified
        c['has_initialize'] = has_initialize
        c['has_upgradeToAndCall'] = has_upgradeToAndCall
        c['has_upgradeTo'] = has_upgradeTo
        c['init_signatures'] = init_signatures

    except Exception as e:
        print(f"  Etherscan error: {e}")
        c['contract_name'] = 'ERROR'
        c['verified'] = False
        c['has_initialize'] = False
        c['has_upgradeToAndCall'] = False
        c['has_upgradeTo'] = False
        c['init_signatures'] = []

    # Step 2: Try initialize() calls on the implementation
    print(f"\n  --- Testing initialize() on IMPLEMENTATION {c['impl']} ---")

    # initialize() = 0x8129fc1c
    print(f"  Trying initialize() [0x8129fc1c]...")
    try:
        resp = rpc_call(c['impl'], "0x8129fc1c")
        if 'error' in resp:
            print(f"    Result: REVERTS - {resp['error'].get('message', str(resp['error']))[:120]}")
            c['init_no_args'] = 'REVERTS'
        elif 'result' in resp:
            print(f"    Result: SUCCESS - returned {resp['result'][:80]}")
            c['init_no_args'] = 'SUCCESS'
        else:
            print(f"    Result: {str(resp)[:120]}")
            c['init_no_args'] = 'UNKNOWN'
    except Exception as e:
        print(f"    Error: {e}")
        c['init_no_args'] = 'ERROR'

    # initialize(address) = 0xc4d66de8 + zero-padded attacker address
    attacker_padded = "0000000000000000000000000000000000000000000000000000000000001234"
    print(f"  Trying initialize(address) [0xc4d66de8]...")
    try:
        resp = rpc_call(c['impl'], "0xc4d66de8" + attacker_padded)
        if 'error' in resp:
            print(f"    Result: REVERTS - {resp['error'].get('message', str(resp['error']))[:120]}")
            c['init_addr'] = 'REVERTS'
        elif 'result' in resp:
            print(f"    Result: SUCCESS - returned {resp['result'][:80]}")
            c['init_addr'] = 'SUCCESS'
        else:
            print(f"    Result: {str(resp)[:120]}")
            c['init_addr'] = 'UNKNOWN'
    except Exception as e:
        print(f"    Error: {e}")
        c['init_addr'] = 'ERROR'

    # Step 3: Check DeBank TVL for the proxy
    print(f"\n  --- Checking DeBank TVL for proxy {c['proxy']} ---")
    try:
        debank = check_debank(c['proxy'])
        if 'total_usd_value' in debank:
            tvl = debank['total_usd_value']
            print(f"    TVL (USD): ${tvl:,.2f}")
            c['tvl'] = f"${tvl:,.2f}"
        else:
            print(f"    DeBank response: {str(debank)[:200]}")
            c['tvl'] = str(debank)[:80]
    except Exception as e:
        print(f"    DeBank error: {e}")
        c['tvl'] = 'ERROR'

# Summary table
print(f"\n\n{'='*140}")
print("SUMMARY TABLE")
print(f"{'='*140}")
header = f"{'#':<3} {'Impl Address':<44} {'Contract Name':<25} {'Verified':<9} {'has_init':<9} {'has_UUPS':<10} {'init() callable':<16} {'init(addr) callable':<20} {'TVL':<20}"
print(header)
print("-" * 140)
for i, c in enumerate(contracts, 1):
    row = f"{i:<3} {c['impl']:<44} {c.get('contract_name','?'):<25} {str(c.get('verified','?')):<9} {str(c.get('has_initialize','?')):<9} {str(c.get('has_upgradeToAndCall','?')):<10} {c.get('init_no_args','?'):<16} {c.get('init_addr','?'):<20} {c.get('tvl','?'):<20}"
    print(row)
