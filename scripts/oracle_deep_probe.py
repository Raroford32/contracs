#!/usr/bin/env python3
"""Deep probe of the sreUSD oracle contract - check storage slots and bytecode
to determine if it reads from the sreUSD vault's exchange rate."""

from web3 import Web3
from Crypto.Hash import keccak

RPC = "https://mainnet.infura.io/v3/bfc7283659224dd6b5124ebbc2b14e2c"
w3 = Web3(Web3.HTTPProvider(RPC))

ORACLE = '0x8535a120f6166959b124e156467d8caf41ca2887'
SREUSD = '0x557ab1e003951a73c12d16f0fea8490e39c33c35'
REUSD = '0x57ab1e0003f623289cd798b1824be09a793e4bec'

print(f"Block: {w3.eth.block_number}")

# Read first 20 storage slots of the oracle
print("=== ORACLE STORAGE SLOTS ===")
for i in range(20):
    try:
        slot = w3.eth.get_storage_at(Web3.to_checksum_address(ORACLE), i)
        val = int.from_bytes(slot, 'big')
        if val > 0:
            # Check if it looks like an address
            if val > 0 and val < 2**160:
                addr = '0x' + hex(val)[2:].zfill(40)
                print(f"  Slot {i}: {addr}")
                if addr.lower() == SREUSD.lower():
                    print(f"    >>> THIS IS THE sreUSD ADDRESS <<<")
                elif addr.lower() == REUSD.lower():
                    print(f"    >>> THIS IS THE reUSD ADDRESS <<<")
            elif val > 10**15 and val < 10**25:
                print(f"  Slot {i}: {val} ({val / 1e18:.6f})")
            else:
                print(f"  Slot {i}: {val} (0x{hex(val)})")
    except:
        pass

# Also check the oracle's bytecode for hardcoded addresses
print("\n=== ORACLE BYTECODE ANALYSIS ===")
code = w3.eth.get_code(Web3.to_checksum_address(ORACLE))
code_hex = code.hex()
print(f"Bytecode length: {len(code)} bytes")

# Search for address references in bytecode
# Addresses in EVM bytecode appear as PUSH20 (0x73) followed by 20 bytes
# or as PUSH32 with address padded
sreusd_hex = SREUSD[2:].lower()
reusd_hex = REUSD[2:].lower()

if sreusd_hex in code_hex:
    idx = code_hex.index(sreusd_hex)
    print(f"  Found sreUSD address at bytecode offset {idx//2}")
    print(f"    >>> ORACLE HARDCODES sreUSD ADDRESS <<<")
else:
    print(f"  sreUSD address NOT found in bytecode (may be in storage)")

if reusd_hex in code_hex:
    idx = code_hex.index(reusd_hex)
    print(f"  Found reUSD address at bytecode offset {idx//2}")

# Search for known function selectors in bytecode
def sel(sig):
    k = keccak.new(digest_bits=256)
    k.update(sig.encode())
    return k.digest()[:4].hex()

selectors = {
    'convertToAssets(uint256)': sel('convertToAssets(uint256)'),
    'totalAssets()': sel('totalAssets()'),
    'totalSupply()': sel('totalSupply()'),
    'balanceOf(address)': sel('balanceOf(address)'),
    'price()': sel('price()'),
    'price_w()': sel('price_w()'),
    'price_oracle()': sel('price_oracle()'),
    'get_virtual_price()': sel('get_virtual_price()'),
    'latestAnswer()': sel('latestAnswer()'),
    'latestRoundData()': sel('latestRoundData()'),
    'exchangeRate()': sel('exchangeRate()'),
    'getExchangeRate()': sel('getExchangeRate()'),
    'pricePerShare()': sel('pricePerShare()'),
    'convertToShares(uint256)': sel('convertToShares(uint256)'),
}

print("\nFunction selectors found in bytecode:")
for name, selector in selectors.items():
    if selector in code_hex:
        print(f"  {name}: 0x{selector} FOUND")

# Now let's try to figure out the oracle type from Etherscan
# Try getting as Vyper source
import requests

# Try the non-standard source code endpoints
resp = requests.get(
    f"https://api.etherscan.io/api?module=contract&action=getsourcecode&address={ORACLE}&apikey=5UWN6DNT7UZCEJYNE3J6FCVAWH4QJW255K"
)
if resp.status_code == 200:
    data = resp.json()
    if data.get('status') == '1' and data.get('result'):
        result = data['result'][0]
        contract_name = result.get('ContractName', '')
        abi_str = result.get('ABI', '')
        source = result.get('SourceCode', '')
        compiler = result.get('CompilerVersion', '')

        print(f"\nEtherscan info:")
        print(f"  Contract name: {contract_name}")
        print(f"  Compiler: {compiler}")
        print(f"  ABI length: {len(abi_str)}")
        print(f"  Source length: {len(source)}")

        if abi_str and abi_str != 'Contract source code not verified':
            import json
            try:
                abi = json.loads(abi_str)
                print(f"\n  ABI functions:")
                for item in abi:
                    if item.get('type') == 'function':
                        inputs = ', '.join([f"{inp['type']} {inp.get('name','')}" for inp in item.get('inputs', [])])
                        outputs = ', '.join([f"{out['type']}" for out in item.get('outputs', [])])
                        print(f"    {item['name']}({inputs}) -> ({outputs})")
            except json.JSONDecodeError:
                print(f"  ABI not JSON parseable")

        if source and len(source) > 10:
            print(f"\n  Source code (first 2000 chars):")
            print(source[:2000])
            with open('/home/user/contracs/src_cache/sreusd_oracle_source.txt', 'w') as f:
                f.write(source)
            print(f"\n  Full source saved to src_cache/sreusd_oracle_source.txt")

# Try the oracle for the sDOLA market too (the one that was actually exploited)
print("\n\n=== sDOLA ORACLE COMPARISON ===")
SDOLA_ORACLE = '0x002688c4296a2c4d800f271fe6f01741111b09be'

resp2 = requests.get(
    f"https://api.etherscan.io/api?module=contract&action=getsourcecode&address={SDOLA_ORACLE}&apikey=5UWN6DNT7UZCEJYNE3J6FCVAWH4QJW255K"
)
if resp2.status_code == 200:
    data2 = resp2.json()
    if data2.get('status') == '1' and data2.get('result'):
        result2 = data2['result'][0]
        print(f"sDOLA oracle contract name: {result2.get('ContractName', '')}")
        print(f"sDOLA oracle compiler: {result2.get('CompilerVersion', '')}")

        abi_str2 = result2.get('ABI', '')
        if abi_str2 and abi_str2 != 'Contract source code not verified':
            try:
                abi2 = json.loads(abi_str2)
                print(f"\nsDOLA oracle ABI functions:")
                for item in abi2:
                    if item.get('type') == 'function':
                        inputs = ', '.join([f"{inp['type']} {inp.get('name','')}" for inp in item.get('inputs', [])])
                        outputs = ', '.join([f"{out['type']}" for out in item.get('outputs', [])])
                        print(f"  {item['name']}({inputs}) -> ({outputs})")
            except:
                pass

        source2 = result2.get('SourceCode', '')
        if source2 and len(source2) > 10:
            with open('/home/user/contracs/src_cache/sdola_oracle_source.txt', 'w') as f:
                f.write(source2)
            print(f"\nsDOLA oracle source saved ({len(source2)} chars)")
            print(f"\nsDOLA oracle source (first 2000 chars):")
            print(source2[:2000])

# Check the sDOLA oracle bytecode for the sDOLA vault address
SDOLA = '0xb45ad160634c528cc3d2926d9807104fa3157305'
sdola_code = w3.eth.get_code(Web3.to_checksum_address(SDOLA_ORACLE))
sdola_code_hex = sdola_code.hex()
sdola_hex = SDOLA[2:].lower()

if sdola_hex in sdola_code_hex:
    print(f"\n  sDOLA oracle hardcodes sDOLA vault address: YES")
else:
    print(f"\n  sDOLA oracle does NOT hardcode sDOLA vault address")

# Check sDOLA oracle storage
print(f"\n  sDOLA oracle storage slots:")
for i in range(10):
    try:
        slot = w3.eth.get_storage_at(Web3.to_checksum_address(SDOLA_ORACLE), i)
        val = int.from_bytes(slot, 'big')
        if val > 0:
            if val < 2**160:
                addr = '0x' + hex(val)[2:].zfill(40)
                print(f"    Slot {i}: {addr}")
                if addr.lower() == SDOLA.lower():
                    print(f"      >>> THIS IS sDOLA <<<")
            else:
                print(f"    Slot {i}: {val}")
    except:
        pass
