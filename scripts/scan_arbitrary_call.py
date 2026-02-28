#!/usr/bin/env python3
"""
Scan for contracts with arbitrary-call vulnerabilities on Ethereum mainnet.
The Aperture/SwapNet pattern: contracts that allow calling arbitrary targets
with user-supplied calldata, enabling token drains via infinite approvals.

Also check: are there any protocols with governance tokens that can be
flash-borrowed for vote manipulation?
"""

import json
import os
from web3 import Web3

RPC = os.environ.get("RPC", "https://eth-mainnet.g.alchemy.com/v2/pLXdY7rYRY10SH_UTLBGH")
w3 = Web3(Web3.HTTPProvider(RPC))

print(f"Connected. Block: {w3.eth.block_number}")

# The Aperture/SwapNet pattern:
# 1. User approves contract for token spending
# 2. Contract has a function like: execute(address target, bytes calldata)
# 3. Attacker calls execute(token, transferFrom(victim, attacker, amount))
# 4. Since contract has approval, it transfers victim's tokens to attacker

# We can't easily scan ALL contracts for this pattern, but we CAN:
# 1. Check known aggregators/routers that have been flagged
# 2. Look for recently deployed contracts with high approval counts
# 3. Check if any known vulnerable versions are still live

# Known vulnerable contracts (past exploits):
VULNERABLE_CONTRACTS = {
    "Aperture V3 Router": "0x00000000Ede6d8D217c60f93191C060747324bca",
    "Aperture V4 Router": "0x0000000010E12F27022a41cBe5f0C0d90bF98",  # partial
    "SwapNet Aggregator": "0x0000000000000000000000000000000000000000",  # unknown
}

# Let's check which of these still have code and could be called
print("="*80)
print("CHECKING KNOWN VULNERABLE CONTRACTS")
print("="*80)

for name, addr in VULNERABLE_CONTRACTS.items():
    if addr == "0x0000000000000000000000000000000000000000":
        continue
    try:
        code = w3.eth.get_code(Web3.to_checksum_address(addr))
        if len(code) > 2:
            print(f"\n  [LIVE] {name}: {addr} ({len(code)} bytes)")
            # Check if there are any token balances
            # If yes, tokens could still be drained
        else:
            print(f"  [DEAD] {name}: no code")
    except:
        print(f"  [ERROR] {name}: invalid address")

# More productive: scan for recently deployed router/aggregator contracts
# by looking for Approval events to new contracts
print("\n\n" + "="*80)
print("CHECKING GOVERNANCE TOKEN FLASH LOAN ATTACK VECTORS")
print("="*80)

# Protocols where governance token can be flash-borrowed:
# 1. If the governance token is a standard ERC-20 available on Aave/Morpho/Euler
# 2. If the governance vote is executable in the same block as borrowing
# 3. If the vote can change protocol parameters (oracle, LTV, etc.)

GOVERNANCE_TOKENS = {
    "CRV": ("0xD533a949740bb3306d119CC777fa900bA034cd52", "Curve"),
    "AAVE": ("0x7Fc66500c84A76Ad7e9c93437bFc5Ac33E2DDaE9", "Aave"),
    "MKR": ("0x9f8F72aA9304c8B593d555F12eF6589cC3A579A2", "Maker"),
    "UNI": ("0x1f9840a85d5aF5bf1D1762F925BDADdC4201F984", "Uniswap"),
    "COMP": ("0xc00e94Cb662C3520282E6f5717214004A7f26888", "Compound"),
    "SUSHI": ("0x6B3595068778DD592e39A122f4f5a5cF09C90fE2", "Sushi"),
    "BAL": ("0xba100000625a3754423978a60c9317c58a424e3D", "Balancer"),
    "INST": ("0x6f40d4A6237C257fff2dB00FA0510DeEECd303eb", "Instadapp/Fluid"),
    "INV": ("0x41D5D79431A913C4aE7d69a668ecdfE5fF9DFB68", "Inverse"),
    "PRISMA": ("0xdA47862a83dac0c112BA89c6abC2159b95afd71C", "Prisma"),
    "GHO": ("0x40D16FC0246aD3160Ccc09B8D0D3A2cD28aE6C2f", "Aave GHO"),
    "CVX": ("0x4e3FBD56CD56c3e72c1403e103b45Db9da5B9D2B", "Convex"),
}

# Check if governance tokens are available on lending markets (flash-borrowable)
AAVE_POOL = "0x87870Bca3F3fD6335C3F4ce8392D69350B4fA4E2"
AAVE_POOL_ABI = json.loads('''[
  {"inputs":[{"internalType":"address","name":"asset","type":"address"}],"name":"getReserveData","outputs":[{"components":[{"components":[{"internalType":"uint256","name":"data","type":"uint256"}],"internalType":"struct DataTypes.ReserveConfigurationMap","name":"configuration","type":"tuple"},{"internalType":"uint128","name":"liquidityIndex","type":"uint128"},{"internalType":"uint128","name":"currentLiquidityRate","type":"uint128"},{"internalType":"uint128","name":"variableBorrowIndex","type":"uint128"},{"internalType":"uint128","name":"currentVariableBorrowRate","type":"uint128"},{"internalType":"uint128","name":"currentStableBorrowRate","type":"uint128"},{"internalType":"uint40","name":"lastUpdateTimestamp","type":"uint40"},{"internalType":"uint16","name":"id","type":"uint16"},{"internalType":"address","name":"aTokenAddress","type":"address"},{"internalType":"address","name":"stableDebtTokenAddress","type":"address"},{"internalType":"address","name":"variableDebtTokenAddress","type":"address"},{"internalType":"address","name":"interestRateStrategyAddress","type":"address"},{"internalType":"uint128","name":"accruedToTreasury","type":"uint128"},{"internalType":"uint128","name":"unbacked","type":"uint128"},{"internalType":"uint128","name":"isolationModeTotalDebt","type":"uint128"}],"internalType":"struct DataTypes.ReserveDataLegacy","name":"","type":"tuple"}],"stateMutability":"view","type":"function"}
]''')

ERC20_ABI = json.loads('''[
  {"inputs":[],"name":"symbol","outputs":[{"internalType":"string","name":"","type":"string"}],"stateMutability":"view","type":"function"},
  {"inputs":[{"internalType":"address","name":"","type":"address"}],"name":"balanceOf","outputs":[{"internalType":"uint256","name":"","type":"uint256"}],"stateMutability":"view","type":"function"},
  {"inputs":[],"name":"totalSupply","outputs":[{"internalType":"uint256","name":"","type":"uint256"}],"stateMutability":"view","type":"function"}
]''')

def safe_call(contract, func_name, *args):
    try:
        return getattr(contract.functions, func_name)(*args).call()
    except:
        return None

aave_pool = w3.eth.contract(address=Web3.to_checksum_address(AAVE_POOL), abi=AAVE_POOL_ABI)

print("\nGovernance tokens available for flash borrowing on Aave V3:")
for name, (addr, protocol) in GOVERNANCE_TOKENS.items():
    reserve = safe_call(aave_pool, "getReserveData", Web3.to_checksum_address(addr))
    if reserve and reserve[0][0] > 0:  # configuration data > 0 means listed
        atoken = reserve[8]
        # Get aToken balance to estimate available liquidity
        token = w3.eth.contract(address=Web3.to_checksum_address(addr), abi=ERC20_ABI)
        atoken_bal = safe_call(token, "balanceOf", Web3.to_checksum_address(atoken))
        total_supply = safe_call(token, "totalSupply") or 1

        if atoken_bal:
            pct = atoken_bal / total_supply * 100
            print(f"  {name} ({protocol}): {atoken_bal / 1e18:,.0f} available on Aave ({pct:.1f}% of supply)")
            if pct > 10:
                print(f"    *** >10% of supply flash-borrowable — governance attack surface ***")
    else:
        # Check if available on Morpho (0% fee flash loans)
        pass

# Also check which are on Uniswap V3 (flash loan source)
print("\n\nGovernance tokens available via Uniswap V3 flash:")
USDC = "0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48"
WETH = "0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2"
# Uni V3 flash loans are available from any pool holding the token
# Just need to check if significant pools exist

# Key question: For flash-borrowable governance tokens,
# can the borrowed amount influence a vote that executes SAME BLOCK?
print("""
GOVERNANCE FLASH LOAN ATTACK ANALYSIS:

For a governance token flash loan attack to work:
1. Token must be flash-borrowable (available on Aave/Morpho/Uni)
2. Governance must allow vote + execute in same transaction
3. The vote must be able to change something valuable (oracle, params, treasury)

Protections that block this:
- Timelock: Most established protocols (Compound, Aave, Uniswap) have timelocks
- Voting period: Multi-day voting periods prevent same-block execution
- Snapshot-based voting: Uses balance at prior block (can't flash in)
- veToken locking: CRV requires locking for veCRV, BAL requires veBAL

Protocols MOST at risk (no timelock + token-weighted voting):
- Small DAOs with onchain token-weighted voting
- New protocols that didn't implement timelocks
- Protocols where governance parameters can be changed by simple token-holder vote
""")

# Check if any small protocol has a flash-loan-vulnerable governance
# by looking at well-known small DAO contracts
print("="*80)
print("CHECKING SPECIFIC SMALLER PROTOCOL GOVERNANCE")
print("="*80)

# Inverse Finance - known for governance issues
INV = "0x41D5D79431A913C4aE7d69a668ecdfE5fF9DFB68"
inv_token = w3.eth.contract(address=Web3.to_checksum_address(INV), abi=ERC20_ABI)
inv_supply = safe_call(inv_token, "totalSupply")
print(f"\nINV (Inverse Finance): Total supply = {(inv_supply or 0) / 1e18:,.0f}")

# Check if INV is on Aave
inv_reserve = safe_call(aave_pool, "getReserveData", Web3.to_checksum_address(INV))
if inv_reserve and inv_reserve[0][0] > 0:
    print("  Available on Aave V3: YES")
else:
    print("  Available on Aave V3: NO")

print("\n\nDone.")
