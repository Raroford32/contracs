#!/usr/bin/env python3
"""Analyze the oracle contract for the sreUSD/crvUSD LlamaLend market.
Determine if the oracle price is affected by donations to the sreUSD vault."""

from web3 import Web3
from Crypto.Hash import keccak
from eth_abi import encode, decode

RPC = "https://mainnet.infura.io/v3/bfc7283659224dd6b5124ebbc2b14e2c"
w3 = Web3(Web3.HTTPProvider(RPC))

def sel(sig):
    k = keccak.new(digest_bits=256)
    k.update(sig.encode())
    return k.digest()[:4]

def eth_call(addr, sig_str, extra=b''):
    data = '0x' + (sel(sig_str) + extra).hex()
    try:
        r = w3.eth.call({'to': Web3.to_checksum_address(addr), 'data': data})
        return r
    except Exception as e:
        return str(e)

def read_uint(addr, sig, extra=b''):
    r = eth_call(addr, sig, extra)
    if isinstance(r, bytes) and len(r) >= 32:
        return int.from_bytes(r[:32], 'big')
    return None

def read_address(addr, sig, extra=b''):
    r = eth_call(addr, sig, extra)
    if isinstance(r, bytes) and len(r) >= 32:
        return '0x' + r[12:32].hex()
    return None

def read_string(addr, sig):
    r = eth_call(addr, sig)
    if isinstance(r, bytes) and len(r) > 64:
        try:
            length = int.from_bytes(r[32:64], 'big')
            return r[64:64+length].decode('utf-8', errors='replace')
        except:
            return None
    return None

print(f"Block: {w3.eth.block_number}")

ORACLE = '0x8535a120f6166959b124e156467d8caf41ca2887'
SREUSD = '0x557ab1e003951a73c12d16f0fea8490e39c33c35'
REUSD = '0x57ab1e0003f623289cd798b1824be09a793e4bec'
CONTROLLER = '0x4f79fe450a2baf833e8f50340bd230f5a3ecafe9'
AMM = '0x437722a015eefb96a6a2a882f3b27caf3c2bc41c'

print("=== ORACLE CONTRACT ANALYSIS ===")
print(f"Oracle: {ORACLE}")

# Get oracle bytecode size to understand what kind of contract it is
code = w3.eth.get_code(Web3.to_checksum_address(ORACLE))
print(f"Oracle bytecode size: {len(code)} bytes")

# Try many common oracle getter functions
oracle_getters = [
    "price()", "price_w()", "price_oracle()",
    "latestAnswer()", "latestRoundData()",
    "getPrice()", "get_price()",
    "stale_price()", "cached_price()",

    # LlamaLend specific
    "STAKED_TOKEN()", "UNDERLYING_TOKEN()",
    "VAULT()", "vault()",
    "ORACLE()", "oracle()",
    "PRICE_ORACLE()", "priceOracle()",
    "BASE_PRICE()", "base_price()",
    "SCALE()", "scale()",
    "DECIMALS()", "decimals()",

    # Curve specific
    "coins(uint256)", "balances(uint256)",
    "get_virtual_price()",
    "price_scale()", "price_oracle(uint256)",
    "last_prices()", "last_prices(uint256)",
    "pool()", "POOL()",

    # General
    "owner()", "admin()",
    "version()", "name()",

    # ERC4626 related
    "convertToAssets(uint256)",
    "totalAssets()", "totalSupply()",
    "asset()",

    # Chainlink-style
    "aggregator()", "description()",
    "latestTimestamp()",

    # Custom oracle getters
    "PEG_KEEPER()", "peg_keeper()",
    "raw_price()", "upper_price()", "lower_price()",
]

print("\nScanning oracle for known function signatures:")
for getter in oracle_getters:
    try:
        if getter in ["coins(uint256)", "balances(uint256)", "price_oracle(uint256)", "last_prices(uint256)"]:
            r = eth_call(ORACLE, getter, (0).to_bytes(32, 'big'))
        elif getter == "convertToAssets(uint256)":
            r = eth_call(ORACLE, getter, (10**18).to_bytes(32, 'big'))
        else:
            r = eth_call(ORACLE, getter)

        if isinstance(r, bytes) and len(r) >= 32:
            val = int.from_bytes(r[:32], 'big')
            # Try as address if looks like one
            if val > 0 and val < 2**160 and getter.lower().endswith("()") and any(x in getter.lower() for x in ["token", "vault", "oracle", "pool", "owner", "admin", "keeper", "asset", "aggregator"]):
                addr_str = '0x' + r[12:32].hex()
                name = read_string(addr_str, "name()")
                sym = read_string(addr_str, "symbol()")
                print(f"  {getter}: {addr_str} ({name or ''} {sym or ''})")
            elif val > 0:
                # Print as number
                if val > 10**15 and val < 10**21:
                    print(f"  {getter}: {val} ({val / 1e18:.6f})")
                elif val > 10**30:
                    print(f"  {getter}: {val} ({val / 1e36:.6f} in 36-dec)")
                else:
                    print(f"  {getter}: {val}")
    except:
        pass

# Now try to get the oracle's source code via etherscan
print("\n=== ORACLE SOURCE CODE (fetching from Etherscan) ===")
import requests
resp = requests.get(
    f"https://api.etherscan.io/api?module=contract&action=getsourcecode&address={ORACLE}&apikey=5UWN6DNT7UZCEJYNE3J6FCVAWH4QJW255K"
)
if resp.status_code == 200:
    data = resp.json()
    if data.get('status') == '1' and data.get('result'):
        result = data['result'][0]
        name = result.get('ContractName', 'Unknown')
        compiler = result.get('CompilerVersion', 'Unknown')
        proxy = result.get('Proxy', '0')
        impl = result.get('Implementation', '')
        source = result.get('SourceCode', '')

        print(f"Contract name: {name}")
        print(f"Compiler: {compiler}")
        print(f"Is proxy: {proxy}")
        if impl:
            print(f"Implementation: {impl}")

        if source:
            # Save source code
            with open('/home/user/contracs/src_cache/sreusd_oracle.sol', 'w') as f:
                f.write(source)
            print(f"Source saved to src_cache/sreusd_oracle.sol ({len(source)} chars)")

            # Print key parts
            lines = source.split('\n')
            print(f"Source lines: {len(lines)}")

            # Search for price-related functions
            for i, line in enumerate(lines):
                line_lower = line.lower()
                if any(kw in line_lower for kw in ['def price', 'function price', 'converttoassets', 'exchange_rate', 'exchangerate', 'totalassets', 'donation']):
                    start = max(0, i-2)
                    end = min(len(lines), i+10)
                    print(f"\n--- Found at line {i+1}: ---")
                    for j in range(start, end):
                        print(f"  {j+1}: {lines[j]}")
        else:
            print("No source code available (unverified)")
else:
    print(f"Etherscan API error: {resp.status_code}")

# =====================================================
# Check the sDOLA market's oracle for comparison
# =====================================================
print("\n=== sDOLA MARKET ORACLE (for comparison) ===")
SDOLA_CONTROLLER = '0xcf3df6c1b4a6b38496661b31170de9508b867c8e'
SDOLA_AMM = read_address(SDOLA_CONTROLLER, "amm()")
print(f"sDOLA AMM: {SDOLA_AMM}")

if SDOLA_AMM:
    sdola_oracle = read_address(SDOLA_AMM, "price_oracle_contract()")
    if not sdola_oracle:
        sdola_oracle = read_address(SDOLA_AMM, "price_oracle()")
    print(f"sDOLA oracle contract: {sdola_oracle}")

    if sdola_oracle:
        # Check if same type as sreUSD oracle
        sdola_code = w3.eth.get_code(Web3.to_checksum_address(sdola_oracle))
        print(f"sDOLA oracle bytecode size: {len(sdola_code)} bytes")
        print(f"Same bytecode as sreUSD oracle: {code == sdola_code}")

        # Get sDOLA oracle contract name
        resp2 = requests.get(
            f"https://api.etherscan.io/api?module=contract&action=getsourcecode&address={sdola_oracle}&apikey=5UWN6DNT7UZCEJYNE3J6FCVAWH4QJW255K"
        )
        if resp2.status_code == 200:
            data2 = resp2.json()
            if data2.get('status') == '1' and data2.get('result'):
                print(f"sDOLA oracle contract name: {data2['result'][0].get('ContractName', 'Unknown')}")

# =====================================================
# Analyze the AMM more deeply
# =====================================================
print("\n=== AMM ANALYSIS ===")
# Check active band range
active_band = read_uint(AMM, "active_band()")
print(f"Active band: {active_band}")

min_band = read_uint(AMM, "min_band()")
max_band = read_uint(AMM, "max_band()")
print(f"Min band: {min_band}")
print(f"Max band: {max_band}")

# Get A (amplification)
A = read_uint(AMM, "A()")
print(f"A (amplification): {A}")

# Get fee
fee = read_uint(AMM, "fee()")
print(f"Fee: {fee}")
if fee:
    print(f"Fee rate: {fee / 1e18:.6f}")

# Check the LLAMMA base price
base_price = read_uint(AMM, "get_base_price()")
print(f"Base price: {base_price}")
if base_price:
    print(f"Base price (human): {base_price / 1e18:.6f}")

print("\n=== KEY QUESTION: Does oracle use sreUSD exchange rate? ===")
# The AMM oracle at 0x8535... is the price oracle.
# If it multiplies the underlying reUSD/crvUSD price by the vault's exchange rate,
# then donating to the vault will directly affect the oracle price.
#
# Current exchange rate: 1.029323
# Current oracle price: 1.023028
# These are close but different - the oracle likely includes the exchange rate
# but may also have EMA smoothing or other factors.
#
# The difference (1.029 vs 1.023) suggests the oracle's EMA hasn't fully
# caught up to the current exchange rate, which is expected.

oracle_price = read_uint(ORACLE, "price()")
if oracle_price:
    exchange_rate = read_uint(SREUSD, "convertToAssets(uint256)", (10**18).to_bytes(32, 'big'))
    print(f"Oracle price: {oracle_price / 1e18:.6f}")
    print(f"Exchange rate: {exchange_rate / 1e18:.6f}")
    print(f"Ratio (oracle/rate): {oracle_price / exchange_rate:.6f}")
    print(f"Implied reUSD/crvUSD price: {oracle_price / exchange_rate:.6f}")
    print(f"\nIf exchange rate doubles (via donation):")
    print(f"  New oracle price (immediate): {oracle_price * 2 / 1e18:.6f}")
    print(f"  New oracle price (after EMA): somewhere between current and 2x")
