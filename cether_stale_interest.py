#!/usr/bin/env python3
"""
Investigate stale interest in CEther - hasn't been accrued since 2020
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

def eth_call(to, data, from_addr="0x0000000000000000000000000000000000000001", value="0x0"):
    result = rpc_call("eth_call", [{"to": to, "data": data, "from": from_addr, "value": value}, "latest"])
    return result

def estimate_gas(to, data, from_addr="0x0000000000000000000000000000000000000001", value="0x0"):
    result = rpc_call("eth_estimateGas", [{"to": to, "data": data, "from": from_addr, "value": value}])
    return result

def get_block_number():
    result = rpc_call("eth_blockNumber", [])
    if result and 'result' in result:
        return int(result['result'], 16)
    return 0

print("=" * 80)
print("CETHER STALE INTEREST EXPLOIT ANALYSIS")
print("=" * 80)

CETHER = "0x7b4a7fd41c688a7cb116534e341e44126ef5a0fd"

# Get current block
current_block = get_block_number()
print(f"\nCurrent Block: {current_block}")

# Get last accrual block
accrual_result = eth_call(CETHER, "0x6c540baf")  # accrualBlockNumber()
if accrual_result and accrual_result.get('result'):
    last_accrual = int(accrual_result['result'], 16)
    print(f"Last Accrual Block: {last_accrual}")
    print(f"Blocks Since Last Accrual: {current_block - last_accrual:,}")
    # Roughly 12s per block, ~2,628,000 blocks per year
    years_stale = (current_block - last_accrual) / 2628000
    print(f"Approximate Time Stale: {years_stale:.2f} years")

# Get interest rate model
print("\n[INTEREST RATE MODEL]")
irm_result = eth_call(CETHER, "0xf3fdb15a")  # interestRateModel()
if irm_result and irm_result.get('result'):
    irm = "0x" + irm_result['result'][26:]
    print(f"Interest Rate Model: {irm}")

    # Get borrow rate
    # getBorrowRate(uint cash, uint borrows, uint reserves)
    # Let's use current values
    total_borrows = eth_call(CETHER, "0x47bd3718")  # totalBorrows()
    total_reserves = eth_call(CETHER, "0x8f840ddd")  # totalReserves()

    if total_borrows and total_reserves:
        borrows = total_borrows.get('result', '0x0')
        reserves = total_reserves.get('result', '0x0')

        # Estimate cash (313 ETH in wei)
        cash = hex(int(313.7 * 1e18))

        # Call getBorrowRate on IRM
        data = "0x15f24053" + cash[2:].zfill(64) + borrows[2:].zfill(64) + reserves[2:].zfill(64)
        rate_result = eth_call(irm, data)
        if rate_result and rate_result.get('result'):
            try:
                borrow_rate = int(rate_result['result'], 16)
                print(f"Borrow Rate Per Block: {borrow_rate}")
                # Annual rate = rate * blocks_per_year (~2628000)
                annual_rate = borrow_rate * 2628000 / 1e18
                print(f"Implied Annual Borrow Rate: {annual_rate:.4f}%")
            except:
                print(f"Borrow Rate: {rate_result['result']}")

# Test accrueInterest()
print("\n[ACCRUE INTEREST TEST]")
accrue_result = estimate_gas(CETHER, "0xa6afed95")  # accrueInterest()
if accrue_result:
    if 'result' in accrue_result:
        gas = int(accrue_result['result'], 16)
        print(f"[+] accrueInterest() callable - gas: {gas}")

        # Calculate potential interest
        # Interest = principal * rate * time
        borrows_result = eth_call(CETHER, "0x47bd3718")
        if borrows_result and borrows_result.get('result'):
            borrows = int(borrows_result['result'], 16) / 1e18
            print(f"\nCurrent Total Borrows: {borrows:.4f} ETH")

            # Very rough calculation
            # Assuming ~5% annual rate
            interest_years = (current_block - last_accrual) / 2628000
            potential_interest = borrows * 0.05 * interest_years
            print(f"Potential Unclaimed Interest (~5% annual): {potential_interest:.4f} ETH")
    elif 'error' in accrue_result:
        err = accrue_result['error'].get('message', '')
        print(f"[-] accrueInterest() error: {err}")

# Check if protocol is paused or deprecated
print("\n[PROTOCOL STATE CHECK]")

# Check if comptroller has this market listed
comptroller = "0xf47dd16553a934064509c40dc5466bbfb999528b"
cether_padded = CETHER[2:].lower().zfill(64)

# markets(address)
markets_data = "0x8e8f294b" + "000000000000000000000000" + cether_padded[24:]
markets_result = eth_call(comptroller, markets_data)
if markets_result and markets_result.get('result'):
    r = markets_result['result']
    if len(r) >= 130:
        is_listed = int(r[2:66], 16)
        collateral_factor = int(r[66:130], 16)
        print(f"Market Listed: {bool(is_listed)}")
        print(f"Collateral Factor: {collateral_factor / 1e18:.2f}")

# Check mintGuardianPaused
mint_paused_data = "0x731f0c2b" + "000000000000000000000000" + cether_padded[24:]
mint_paused_result = eth_call(comptroller, mint_paused_data)
if mint_paused_result and mint_paused_result.get('result'):
    is_paused = int(mint_paused_result['result'], 16)
    print(f"Mint Paused: {bool(is_paused)}")

# Try to simulate accruing and then minting
print("\n[SIMULATED EXPLOITATION PATH]")
print("""
If accrueInterest() is callable:
1. Call accrueInterest() to update the borrow index
2. This should cause interest to accrue on all borrows
3. Interest goes to:
   - Reserve (reserveFactor %)
   - Lenders (proportional to their cETH holdings)

Potential exploit vectors:
A) If we own cETH, accrue would increase our redemption value
B) If borrowers haven't repaid, they now owe more
C) Bad debt could exceed collateral if prices moved

Checking if this is actually exploitable...
""")

# Check exchange rate before/after accrue
print("\n[EXCHANGE RATE CHECK]")
exchange_rate = eth_call(CETHER, "0xbd6d894d")  # exchangeRateCurrent()
if exchange_rate and exchange_rate.get('result'):
    try:
        rate = int(exchange_rate['result'], 16)
        # Exchange rate is scaled by 1e18 * underlying decimals / cToken decimals
        # For ETH: 1e18 * 1e18 / 1e8 = 1e28
        normalized = rate / 1e28
        print(f"Current Exchange Rate: {rate} ({normalized:.6f} ETH per cETH)")

        total_supply = eth_call(CETHER, "0x18160ddd")
        if total_supply and total_supply.get('result'):
            supply = int(total_supply['result'], 16)
            # cETH has 8 decimals
            total_eth_redeemable = (supply / 1e8) * normalized
            print(f"Total cETH Supply: {supply/1e8:.4f}")
            print(f"Total ETH Redeemable: {total_eth_redeemable:.4f} ETH")
    except Exception as e:
        print(f"Error: {e}")

# Check who owns cETH
print("\n[CHECKING FOR FIRST DEPOSITOR/EMPTY VAULT]")
supply_result = eth_call(CETHER, "0x18160ddd")
if supply_result and supply_result.get('result'):
    total_supply = int(supply_result['result'], 16)
    if total_supply == 0:
        print("[!!!] TOTAL SUPPLY IS ZERO - First depositor vulnerability possible!")
    else:
        print(f"Total Supply: {total_supply/1e8:.4f} cETH (not zero, not first-depositor)")

print("\n" + "=" * 80)
print("ANALYSIS COMPLETE")
print("=" * 80)
