#!/usr/bin/env python3
"""Identify what the sreUSD oracle depends on."""

from web3 import Web3
from Crypto.Hash import keccak
import requests, json

RPC = "https://mainnet.infura.io/v3/bfc7283659224dd6b5124ebbc2b14e2c"
w3 = Web3(Web3.HTTPProvider(RPC))

def sel(sig):
    k = keccak.new(digest_bits=256)
    k.update(sig.encode())
    return k.digest()[:4]

def eth_call(addr, sig_str, extra=b''):
    data = '0x' + (sel(sig_str) + extra).hex()
    try:
        return w3.eth.call({'to': Web3.to_checksum_address(addr), 'data': data})
    except:
        return None

def read_uint(addr, sig, extra=b''):
    r = eth_call(addr, sig, extra)
    return int.from_bytes(r[:32], 'big') if r and len(r) >= 32 else None

def read_address(addr, sig, extra=b''):
    r = eth_call(addr, sig, extra)
    return '0x' + r[12:32].hex() if r and len(r) >= 32 else None

def read_string(addr, sig):
    r = eth_call(addr, sig)
    if r and len(r) > 64:
        try:
            length = int.from_bytes(r[32:64], 'big')
            return r[64:64+length].decode('utf-8', errors='replace')
        except:
            return None
    return None

# The unknown address from oracle storage slot 1
UNKNOWN = '0x519b00d4685712930596b8e521106f5e020157a3'
ORACLE = '0x8535a120f6166959b124e156467d8caf41ca2887'

print(f"Block: {w3.eth.block_number}")
print(f"\n=== Identifying {UNKNOWN} ===")

# Check basic info
name = read_string(UNKNOWN, "name()")
symbol = read_string(UNKNOWN, "symbol()")
print(f"Name: {name}")
print(f"Symbol: {symbol}")

# Check if it's a pool
for getter in ["coins(uint256)", "balances(uint256)", "get_virtual_price()",
               "A()", "fee()", "price_oracle()", "price_oracle(uint256)",
               "last_prices()", "last_prices(uint256)", "price_scale()",
               "totalSupply()", "totalAssets()", "asset()",
               "token()", "lp_token()", "pool()"]:
    try:
        if "(uint256)" in getter:
            val = read_uint(UNKNOWN, getter, (0).to_bytes(32, 'big'))
        else:
            val = read_uint(UNKNOWN, getter)
        if val is not None:
            if val > 10**15 and val < 10**25:
                print(f"  {getter}: {val} ({val / 1e18:.6f})")
            elif val > 0 and val < 2**160:
                addr = '0x' + hex(val)[2:].zfill(40)
                n = read_string(addr, "symbol()")
                print(f"  {getter}: {addr} ({n})")
            else:
                print(f"  {getter}: {val}")
    except:
        pass

# Check coin addresses
for i in range(5):
    coin = read_address(UNKNOWN, "coins(uint256)", i.to_bytes(32, 'big'))
    if coin and coin != '0x0000000000000000000000000000000000000000':
        sym = read_string(coin, "symbol()")
        print(f"  coins({i}): {coin} ({sym})")

# Get the contract info from Etherscan
code = w3.eth.get_code(Web3.to_checksum_address(UNKNOWN))
print(f"\nBytecode size: {len(code)} bytes")

resp = requests.get(
    f"https://api.etherscan.io/api?module=contract&action=getsourcecode&address={UNKNOWN}&apikey=5UWN6DNT7UZCEJYNE3J6FCVAWH4QJW255K"
)
if resp.status_code == 200:
    data = resp.json()
    if data.get('status') == '1' and data.get('result'):
        result = data['result'][0]
        print(f"Contract name: {result.get('ContractName', '')}")
        print(f"Compiler: {result.get('CompilerVersion', '')}")
        print(f"Proxy: {result.get('Proxy', '')}")

        abi_str = result.get('ABI', '')
        if abi_str and abi_str != 'Contract source code not verified':
            try:
                abi = json.loads(abi_str)
                print(f"\nABI functions:")
                for item in abi:
                    if item.get('type') == 'function':
                        inputs = ', '.join([f"{inp['type']} {inp.get('name','')}" for inp in item.get('inputs', [])])
                        outputs = ', '.join([f"{out['type']}" for out in item.get('outputs', [])])
                        print(f"  {item['name']}({inputs}) -> ({outputs})")
            except:
                pass

        source = result.get('SourceCode', '')
        if source:
            print(f"\nSource ({len(source)} chars)")
            # Look for price-related code
            for line_num, line in enumerate(source.split('\n'), 1):
                ll = line.lower()
                if any(kw in ll for kw in ['price', 'oracle', 'rate', 'convert', 'exchange', 'vault']):
                    print(f"  L{line_num}: {line.strip()}")

# Now check what the oracle is actually doing
# Try to disassemble the bytecode
print(f"\n=== ORACLE ({ORACLE}) BYTECODE DISASSEMBLY HINTS ===")
oracle_code = w3.eth.get_code(Web3.to_checksum_address(ORACLE))
oracle_hex = oracle_code.hex()

# Find all PUSH20 (hardcoded addresses)
import re
# PUSH20 = 0x73
i = 0
addresses_found = []
while i < len(oracle_hex):
    if oracle_hex[i:i+2] == '73':  # PUSH20
        addr_hex = oracle_hex[i+2:i+42]
        if len(addr_hex) == 40:
            addr = '0x' + addr_hex
            addresses_found.append(addr)
            sym = read_string(addr, "symbol()")
            n = read_string(addr, "name()")
            print(f"  PUSH20 at offset {i//2}: {addr} ({n or ''} {sym or ''})")
        i += 42
    else:
        i += 2

# Also check PUSH32 for addresses
i = 0
while i < len(oracle_hex):
    if oracle_hex[i:i+2] == '7f':  # PUSH32
        val_hex = oracle_hex[i+2:i+66]
        if len(val_hex) == 64:
            val = int(val_hex, 16)
            if val > 0 and val < 2**160:
                addr = '0x' + hex(val)[2:].zfill(40)
                sym = read_string(addr, "symbol()")
                if sym:
                    print(f"  PUSH32 address at offset {i//2}: {addr} ({sym})")
        i += 66
    else:
        i += 2

# Search for specific function selectors that might be STATICCALL'ed
# The oracle would STATICCALL external contracts to get prices
print(f"\n=== STATIC CALL TARGETS ===")
# price_oracle() selector: a035b1fe
# price_w() selector: ceb7f759
# convertToAssets: 07a2d13a
# totalAssets: 01e1d114
# totalSupply: 18160ddd
# get_virtual_price: bb7b8b80
# latestRoundData: feaf968c

ext_selectors = {
    '07a2d13a': 'convertToAssets(uint256)',
    '01e1d114': 'totalAssets()',
    '18160ddd': 'totalSupply()',
    'bb7b8b80': 'get_virtual_price()',
    'feaf968c': 'latestRoundData()',
    '50d25bcd': 'latestAnswer()',
    '668a0f02': 'latestRound()',
    'a035b1fe': 'price()',
    'ceb7f759': 'price_w()',
    '86fc88d3': 'price_oracle()',
    '70a08231': 'balanceOf(address)',
    'e6aa216c': 'get_p()',
    'b4b577ad': 'price_scale()',
    'f446c1d0': 'A()',
    '25e9d773': 'exchange_rate()',
    '99530b06': 'pricePerShare()',
}

for selector, name in ext_selectors.items():
    if selector in oracle_hex:
        print(f"  {name} (0x{selector}) FOUND in bytecode")

print(f"\n=== ALSO CHECK: Can we read all vault markets that use vault tokens? ===")
# Check which markets have the same issue as sDOLA

# Check the sDOLA oracle source more carefully
SDOLA_ORACLE = '0x002688c4296a2c4d800f271fe6f01741111b09be'
sdola_code_hex = w3.eth.get_code(Web3.to_checksum_address(SDOLA_ORACLE)).hex()

print(f"\nsDOLA oracle function selectors in bytecode:")
for selector, name in ext_selectors.items():
    if selector in sdola_code_hex:
        print(f"  {name} (0x{selector}) FOUND")
