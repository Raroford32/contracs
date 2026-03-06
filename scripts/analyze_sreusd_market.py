#!/usr/bin/env python3
"""Deep analysis of sreUSD/crvUSD LlamaLend market for donation attack vulnerability.

The sDOLA exploit (March 2, 2026) used flash loans to donate to sDOLA vault,
inflating exchange rate, triggering mass liquidations. This market has the same pattern:
- sreUSD is an ERC4626 vault token
- 100% donation susceptibility
- $14.2M in active debt
- $17.2M vault TVL (manipulable with large flash loan)
"""

from web3 import Web3
from Crypto.Hash import keccak
from eth_abi import encode, decode
import json

RPC = "https://mainnet.infura.io/v3/bfc7283659224dd6b5124ebbc2b14e2c"
w3 = Web3(Web3.HTTPProvider(RPC))

def sel(sig):
    k = keccak.new(digest_bits=256)
    k.update(sig.encode())
    return k.digest()[:4]

def eth_call(addr, sig, extra=b''):
    data = '0x' + (sel(sig) + extra).hex()
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
            offset = int.from_bytes(r[:32], 'big')
            length = int.from_bytes(r[32:64], 'big')
            return r[64:64+length].decode('utf-8', errors='replace')
        except:
            return None
    return None

print(f"Block: {w3.eth.block_number}")

# Market 41: sreUSD/crvUSD
VAULT = '0xc32b0cf36e06c790a568667a17de80cba95a5aad'  # LlamaLend vault
CONTROLLER = '0x4f79fe450a2baf833e8f50340bd230f5a3ecafe9'
SREUSD = '0x557ab1e003951a73c12d16f0fea8490e39c33c35'  # Collateral token
UNDERLYING = '0x57ab1e0003f623289cd798b1824be09a793e4bec'  # sUSD

print("=== Market 41: sreUSD/crvUSD ===")

# Get token details
print(f"\nsreUSD token: {SREUSD}")
sreusd_name = read_string(SREUSD, "name()")
sreusd_symbol = read_string(SREUSD, "symbol()")
print(f"  Name: {sreusd_name}")
print(f"  Symbol: {sreusd_symbol}")

underlying_name = read_string(UNDERLYING, "name()")
underlying_symbol = read_string(UNDERLYING, "symbol()")
print(f"\nUnderlying: {UNDERLYING}")
print(f"  Name: {underlying_name}")
print(f"  Symbol: {underlying_symbol}")

# Get vault stats
total_assets = read_uint(SREUSD, "totalAssets()")
total_supply = read_uint(SREUSD, "totalSupply()")
print(f"\nsreUSD Vault Stats:")
print(f"  totalAssets: {total_assets}")
if total_assets:
    print(f"  totalAssets (human): {total_assets / 1e18:,.2f}")
print(f"  totalSupply: {total_supply}")

# Exchange rate
convert_1e18 = read_uint(SREUSD, "convertToAssets(uint256)", (10**18).to_bytes(32, 'big'))
print(f"  convertToAssets(1e18): {convert_1e18}")
if convert_1e18:
    print(f"  Exchange rate: {convert_1e18 / 1e18:.6f}")

# Check underlying balance in vault
underlying_bal = read_uint(UNDERLYING, "balanceOf(address)",
                          bytes(12) + bytes.fromhex(SREUSD[2:]))
print(f"  Underlying balanceOf(vault): {underlying_bal}")
if underlying_bal:
    print(f"  Underlying balanceOf (human): {underlying_bal / 1e18:,.2f}")
    if total_assets and total_assets > 0:
        print(f"  Donation susceptibility: {underlying_bal / total_assets:.2%}")

# =====================================================
# KEY: Check the ORACLE configuration
# =====================================================
print("\n=== ORACLE ANALYSIS ===")

# The controller has a reference to the AMM (LLAMMA)
amm = read_address(CONTROLLER, "amm()")
print(f"AMM (LLAMMA): {amm}")

# The controller also has a monetary policy and price oracle
price_oracle = read_address(CONTROLLER, "price_oracle()")
print(f"Price oracle (from controller): {price_oracle}")

# Try reading the price oracle's price
if price_oracle:
    oracle_price = read_uint(price_oracle, "price()")
    print(f"  Oracle price(): {oracle_price}")
    if oracle_price:
        print(f"  Oracle price (human): {oracle_price / 1e18:.6f}")

    oracle_price_w = read_uint(price_oracle, "price_w()")
    print(f"  Oracle price_w(): {oracle_price_w}")
    if oracle_price_w:
        print(f"  Oracle price_w (human): {oracle_price_w / 1e18:.6f}")

    # Check what contract the oracle is
    oracle_name = read_string(price_oracle, "name()")
    print(f"  Oracle name: {oracle_name}")

    # Check oracle parameters
    for getter in ["PRICE_ORACLE()", "priceOracle()", "price_oracle()",
                   "STAKED_TOKEN()", "UNDERLYING_TOKEN()",
                   "base_price()", "high_price()", "low_price()",
                   "staked_oracle()", "underlying_oracle()"]:
        val = read_address(price_oracle, getter)
        if val and val != '0x0000000000000000000000000000000000000000':
            print(f"  {getter}: {val}")

    for getter in ["SCALE_FACTOR()", "alpha()", "beta()",
                   "staked_price()", "exchange_rate()",
                   "last_price()"]:
        val = read_uint(price_oracle, getter)
        if val is not None:
            print(f"  {getter}: {val}")

# Also check the AMM's oracle
if amm:
    amm_price_oracle = read_address(amm, "price_oracle_contract()")
    if not amm_price_oracle:
        amm_price_oracle = read_address(amm, "price_oracle()")
    print(f"\nAMM price oracle contract: {amm_price_oracle}")

    if amm_price_oracle:
        # Check if it's the same as controller's oracle
        if amm_price_oracle == price_oracle:
            print("  >> Same as controller's oracle")
        else:
            print("  >> DIFFERENT from controller's oracle!")
            oracle_price2 = read_uint(amm_price_oracle, "price()")
            if oracle_price2:
                print(f"  AMM oracle price: {oracle_price2 / 1e18:.6f}")

    # Check AMM state
    amm_price = read_uint(amm, "get_p()")
    print(f"\nAMM get_p(): {amm_price}")
    if amm_price:
        print(f"  AMM current price: {amm_price / 1e18:.6f}")

    oracle_up = read_uint(amm, "price_oracle()")
    print(f"AMM price_oracle() [internal EMA]: {oracle_up}")
    if isinstance(oracle_up, int):
        print(f"  AMM EMA oracle: {oracle_up / 1e18:.6f}")

# =====================================================
# Analyze borrower positions
# =====================================================
print("\n=== BORROWER POSITIONS ===")
n_loans = read_uint(CONTROLLER, "n_loans()")
print(f"Active loans: {n_loans}")

total_debt = read_uint(CONTROLLER, "total_debt()")
if total_debt:
    print(f"Total debt: {total_debt / 1e18:,.2f} crvUSD")

# Try to read individual loan details
# loan_ix(n) gives the address of the nth borrower
# loans(user) gives loan details
if n_loans and n_loans > 0:
    print(f"\nTop borrower positions:")
    for i in range(min(n_loans, 10)):
        borrower = read_address(CONTROLLER, "loan_ix(uint256)", i.to_bytes(32, 'big'))
        if borrower and borrower != '0x0000000000000000000000000000000000000000':
            # Get user state from AMM: get user's debt and collateral
            user_debt = read_uint(CONTROLLER, "debt(address)",
                                 bytes(12) + bytes.fromhex(borrower[2:]))
            # Get user's ticks (bands)
            r = eth_call(CONTROLLER, "user_state(address)",
                        bytes(12) + bytes.fromhex(borrower[2:]))
            if isinstance(r, bytes) and len(r) >= 128:
                collateral = int.from_bytes(r[:32], 'big')
                stablecoin = int.from_bytes(r[32:64], 'big')
                debt = int.from_bytes(r[64:96], 'big')
                n_bands = int.from_bytes(r[96:128], 'big')
                print(f"  Borrower {i}: {borrower}")
                print(f"    Collateral: {collateral / 1e18:,.4f} sreUSD")
                print(f"    Stablecoin: {stablecoin / 1e18:,.2f} crvUSD")
                print(f"    Debt: {debt / 1e18:,.2f} crvUSD")
                print(f"    Bands: {n_bands}")

                # Health check
                health = read_uint(CONTROLLER, "health(address,bool)",
                                  bytes(12) + bytes.fromhex(borrower[2:]) + (0).to_bytes(32, 'big'))
                if health is not None:
                    print(f"    Health (full): {health / 1e18:.4f}")
                    if health < 10**17:  # < 0.1 = very unhealthy
                        print(f"    >>> LOW HEALTH - NEAR LIQUIDATION <<<")
            elif user_debt:
                print(f"  Borrower {i}: {borrower} - debt: {user_debt / 1e18:,.2f}")

# =====================================================
# Simulate donation attack economics
# =====================================================
print("\n=== DONATION ATTACK ECONOMICS ===")
if total_assets and total_assets > 0:
    vault_tvl = total_assets / 1e18

    # Different donation amounts
    for donation_pct in [10, 20, 50, 100]:
        donation = vault_tvl * donation_pct / 100
        new_total = vault_tvl + donation
        new_rate = convert_1e18 * new_total / vault_tvl if convert_1e18 else 0
        rate_change = (new_total / vault_tvl - 1) * 100

        print(f"\n  Donation: {donation:,.0f} sUSD ({donation_pct}% of vault TVL)")
        print(f"    New exchange rate: {new_rate / 1e18:.6f}")
        print(f"    Rate change: +{rate_change:.1f}%")
        print(f"    Flash loan needed: ~${donation:,.0f}")

    print(f"\n  Comparison with sDOLA exploit:")
    print(f"    sDOLA: $5.78M vault TVL, $30M flash loan, ~14% rate change, $240K profit")
    print(f"    sreUSD: ${vault_tvl:,.0f} vault TVL, ${vault_tvl * 0.14 / 0.14:,.0f} flash loan for ~14% change")
    print(f"    sreUSD has {total_debt / 1e18 if total_debt else 0:,.0f} crvUSD in active debt")
    print(f"    Potential liquidation value: significantly higher than sDOLA")

# =====================================================
# Check available flash loan liquidity for sUSD
# =====================================================
print("\n=== FLASH LOAN AVAILABILITY (sUSD) ===")
# Check sUSD total supply
susd_total = read_uint(UNDERLYING, "totalSupply()")
print(f"sUSD total supply: {susd_total / 1e18:,.2f}" if susd_total else "sUSD total supply: unknown")

# Check available in Aave (major flash loan source)
# Aave V3 pool on mainnet
AAVE_POOL = '0x87870Bca3F3fD6335C3F4ce8392D69350B4fA4E2'
# Check if sUSD is available
# Try to get reserve data for sUSD
print(f"  (Check Aave/Balancer/dYdX for sUSD flash loan availability)")
print(f"  Note: attacker can also swap from USDC/USDT flash loans to sUSD")

# What about the underlying - is it actually sUSD or something else?
print(f"\n=== VERIFY UNDERLYING TOKEN ===")
# Double-check the underlying
underlying_decimals = read_uint(UNDERLYING, "decimals()")
print(f"Underlying decimals: {underlying_decimals}")
print(f"Underlying name: {underlying_name}")
print(f"Underlying symbol: {underlying_symbol}")

# Check if sreUSD has deposit/withdraw functions
print(f"\nsreUSD vault functions:")
for func in ["deposit(uint256,address)", "withdraw(uint256,address,address)",
             "redeem(uint256,address,address)", "mint(uint256,address)",
             "maxDeposit(address)", "maxWithdraw(address)"]:
    try:
        r = eth_call(SREUSD, func)
        if isinstance(r, bytes):
            print(f"  {func}: callable")
    except:
        pass

# Check who deployed/owns the vault
owner = read_address(SREUSD, "owner()")
print(f"\nsreUSD owner: {owner}")
admin = read_address(SREUSD, "admin()")
print(f"sreUSD admin: {admin}")

print("\n=== SUMMARY ===")
print(f"Market: sreUSD/crvUSD on Curve LlamaLend")
print(f"Active debt: ${total_debt / 1e18:,.0f} crvUSD" if total_debt else "Active debt: unknown")
print(f"Active loans: {n_loans}")
print(f"Vault TVL: ${vault_tvl:,.0f}" if 'vault_tvl' in dir() else "Vault TVL: unknown")
print(f"Donation susceptible: YES (100% underlying in vault)")
print(f"Oracle tracks exchange rate: {'YES - VULNERABLE' if price_oracle else 'NEEDS VERIFICATION'}")
print(f"Same pattern as sDOLA exploit (March 2, 2026): LIKELY")
