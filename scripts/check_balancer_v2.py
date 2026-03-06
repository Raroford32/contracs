#!/usr/bin/env python3
"""Check if Balancer V2 vault manageUserBalance is still callable."""

from web3 import Web3
from Crypto.Hash import keccak

RPC = "https://mainnet.infura.io/v3/bfc7283659224dd6b5124ebbc2b14e2c"
w3 = Web3(Web3.HTTPProvider(RPC))

VAULT = "0xBA12222222228d8Ba445958a75a0704d566BF2C8"

def sel(sig):
    k = keccak.new(digest_bits=256)
    k.update(sig.encode())
    return k.digest()[:4]

def eth_call(addr, data_hex, value=0):
    try:
        result = w3.eth.call({
            'to': Web3.to_checksum_address(addr),
            'data': data_hex,
            'from': '0x0000000000000000000000000000000000000001',
            'value': value
        })
        return result
    except Exception as e:
        return str(e)

print(f"Block: {w3.eth.block_number}")
print(f"Vault: {VAULT}")

# Check if vault is paused
# Balancer V2 Vault doesn't have a simple paused() getter
# Instead, let's check if functions are callable

# 1. Check getProtocolFeesCollector
r = eth_call(VAULT, '0x' + sel("getProtocolFeesCollector()").hex())
if isinstance(r, bytes):
    fee_collector = '0x' + r[12:32].hex()
    print(f"ProtocolFeesCollector: {fee_collector}")
else:
    print(f"getProtocolFeesCollector error: {r}")

# 2. Check WETH
r = eth_call(VAULT, '0x' + sel("WETH()").hex())
if isinstance(r, bytes):
    weth = '0x' + r[12:32].hex()
    print(f"WETH: {weth}")
else:
    print(f"WETH error: {r}")

# 3. Check getPausedState
r = eth_call(VAULT, '0x' + sel("getPausedState()").hex())
if isinstance(r, bytes) and len(r) >= 96:
    paused = int.from_bytes(r[:32], 'big')
    pause_window_end = int.from_bytes(r[32:64], 'big')
    buffer_period_end = int.from_bytes(r[64:96], 'big')
    print(f"Paused: {bool(paused)}")
    print(f"Pause window end: {pause_window_end}")
    print(f"Buffer period end: {buffer_period_end}")
else:
    print(f"getPausedState error: {r}")

# 4. Try to call manageUserBalance with WITHDRAW_INTERNAL
# UserBalanceOp: (uint8 kind, address asset, uint256 amount, address sender, address payable recipient)
# kind=1 is WITHDRAW_INTERNAL
# Let's try with zero amounts to see if it reverts

from eth_abi import encode

# Build a UserBalanceOp tuple
# kind = 1 (WITHDRAW_INTERNAL)
# asset = WETH (0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2)
# amount = 0
# sender = 0x0000000000000000000000000000000000000001 (our from address)
# recipient = 0x0000000000000000000000000000000000000001

# manageUserBalance((uint8,address,uint256,address,address)[])
# The selector for manageUserBalance
sig = "manageUserBalance((uint8,address,uint256,address,address)[])"
s = sel(sig)
print(f"\nmanageUserBalance selector: 0x{s.hex()}")

# Encode the ops array
# ops = [(1, WETH, 0, sender, recipient)]
weth_addr = "0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2"
sender_addr = "0x0000000000000000000000000000000000000001"

ops_data = encode(
    ['(uint8,address,uint256,address,address)[]'],
    [[(1, weth_addr, 0, sender_addr, sender_addr)]]
)

calldata = '0x' + s.hex() + ops_data.hex()
print(f"Calling manageUserBalance with WITHDRAW_INTERNAL (amount=0)...")

result = eth_call(VAULT, calldata)
if isinstance(result, bytes):
    print(f"SUCCESS! Return data: {result.hex()}")
    print("!!! manageUserBalance is still callable !!!")
elif isinstance(result, str):
    print(f"Reverted: {result}")
    # Check if it's paused, access control, or other
    if "PAUSED" in result.upper() or "HALT" in result.upper():
        print(">>> Vault appears PAUSED")
    elif "AUTH" in result.upper() or "SENDER" in result.upper() or "PERMISSION" in result.upper():
        print(">>> Access control active - possibly PATCHED")
    elif "BAL#" in result:
        # Balancer uses BAL# error codes
        print(f">>> Balancer error code detected")

# 5. Also check getInternalBalance to see if internal balances exist
print("\n=== Checking internal balances ===")
# getInternalBalance(address user, IERC20[] tokens) -> uint256[]
sig2 = sel("getInternalBalance(address,address[])")
# Check a whale address's internal balance for WETH
# Use the Balancer vault itself as test
test_addr = "0x0000000000000000000000000000000000000001"
encoded = encode(
    ['address', 'address[]'],
    [test_addr, [weth_addr]]
)
calldata2 = '0x' + sig2.hex() + encoded.hex()
r = eth_call(VAULT, calldata2)
if isinstance(r, bytes):
    print(f"getInternalBalance response length: {len(r)} bytes")
    if len(r) >= 64:
        # Array offset and length
        balance = int.from_bytes(r[-32:], 'big')
        print(f"Internal WETH balance for test addr: {balance}")
else:
    print(f"getInternalBalance error: {r}")

# 6. Check pool count/registered pools
print("\n=== Pool info ===")
# Let's check a known pool
# WETH/DAI pool or similar
r = eth_call(VAULT, '0x' + sel("getPoolTokenInfo(bytes32,address)").hex() +
    bytes.fromhex("5c6ee304399dbdb9c8ef030ab642b10820db8f56000200000000000000000014") +  # BAL/WETH 80/20 pool ID
    bytes(12) + bytes.fromhex("C02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2"))  # WETH
if isinstance(r, bytes) and len(r) >= 128:
    cash = int.from_bytes(r[:32], 'big')
    managed = int.from_bytes(r[32:64], 'big')
    print(f"BAL/WETH pool - WETH cash: {cash / 1e18:.4f} ETH")
    print(f"BAL/WETH pool - WETH managed: {managed / 1e18:.4f} ETH")
else:
    print(f"Pool query result: {r}")
