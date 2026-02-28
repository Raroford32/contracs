#!/usr/bin/env python3
"""
Deep dive into Curve Lending markets with large oracle-spot deviations.
Check if the deviation creates an exploitable arbitrage or liquidation opportunity.

Key question: Can we deposit collateral at spot, borrow at oracle rate, and profit?
Or: Can we trigger incorrect liquidations using the deviation?

Curve LLAMMA AMM uses an internal oracle (EMA) that's designed to lag spot.
Large deviations might be NORMAL for LLAMMA or might indicate a manipulation opportunity.
"""

import json
import os
from web3 import Web3

RPC = os.environ.get("RPC", "https://eth-mainnet.g.alchemy.com/v2/pLXdY7rYRY10SH_UTLBGH")
w3 = Web3(Web3.HTTPProvider(RPC))

print(f"Connected. Block: {w3.eth.block_number}")

ERC20_ABI = json.loads('''[
  {"inputs":[],"name":"symbol","outputs":[{"internalType":"string","name":"","type":"string"}],"stateMutability":"view","type":"function"},
  {"inputs":[],"name":"decimals","outputs":[{"internalType":"uint8","name":"","type":"uint8"}],"stateMutability":"view","type":"function"},
  {"inputs":[{"internalType":"address","name":"","type":"address"}],"name":"balanceOf","outputs":[{"internalType":"uint256","name":"","type":"uint256"}],"stateMutability":"view","type":"function"}
]''')

def safe_call(contract, func_name, *args):
    try:
        return getattr(contract.functions, func_name)(*args).call()
    except:
        return None

def get_sym(addr):
    c = w3.eth.contract(address=Web3.to_checksum_address(addr), abi=ERC20_ABI)
    return safe_call(c, "symbol") or "?"

# ============================================================
# Suspicious Curve Lending markets with large deviations
# ============================================================

CURVE_FACTORY = "0xeA6876DDE9e3467564acBeE1Ed5bac88783205E0"
CURVE_FACTORY_ABI = json.loads('''[
  {"inputs":[{"internalType":"uint256","name":"n","type":"uint256"}],"name":"vaults","outputs":[{"internalType":"address","name":"","type":"address"}],"stateMutability":"view","type":"function"}
]''')

CURVE_VAULT_ABI = json.loads('''[
  {"inputs":[],"name":"asset","outputs":[{"internalType":"address","name":"","type":"address"}],"stateMutability":"view","type":"function"},
  {"inputs":[],"name":"totalAssets","outputs":[{"internalType":"uint256","name":"","type":"uint256"}],"stateMutability":"view","type":"function"},
  {"inputs":[],"name":"controller","outputs":[{"internalType":"address","name":"","type":"address"}],"stateMutability":"view","type":"function"},
  {"inputs":[],"name":"symbol","outputs":[{"internalType":"string","name":"","type":"string"}],"stateMutability":"view","type":"function"}
]''')

CURVE_CONTROLLER_ABI = json.loads('''[
  {"inputs":[],"name":"collateral_token","outputs":[{"internalType":"address","name":"","type":"address"}],"stateMutability":"view","type":"function"},
  {"inputs":[],"name":"total_debt","outputs":[{"internalType":"uint256","name":"","type":"uint256"}],"stateMutability":"view","type":"function"},
  {"inputs":[],"name":"amm","outputs":[{"internalType":"address","name":"","type":"address"}],"stateMutability":"view","type":"function"},
  {"inputs":[],"name":"n_loans","outputs":[{"internalType":"uint256","name":"","type":"uint256"}],"stateMutability":"view","type":"function"},
  {"inputs":[],"name":"liquidation_discount","outputs":[{"internalType":"uint256","name":"","type":"uint256"}],"stateMutability":"view","type":"function"},
  {"inputs":[],"name":"loan_discount","outputs":[{"internalType":"uint256","name":"","type":"uint256"}],"stateMutability":"view","type":"function"},
  {"inputs":[{"internalType":"address","name":"user","type":"address"}],"name":"health","outputs":[{"internalType":"int256","name":"","type":"int256"}],"stateMutability":"view","type":"function"}
]''')

CURVE_AMM_ABI = json.loads('''[
  {"inputs":[],"name":"price_oracle","outputs":[{"internalType":"uint256","name":"","type":"uint256"}],"stateMutability":"view","type":"function"},
  {"inputs":[],"name":"get_p","outputs":[{"internalType":"uint256","name":"","type":"uint256"}],"stateMutability":"view","type":"function"},
  {"inputs":[{"internalType":"uint256","name":"i","type":"uint256"}],"name":"bands_x","outputs":[{"internalType":"uint256","name":"","type":"uint256"}],"stateMutability":"view","type":"function"},
  {"inputs":[{"internalType":"uint256","name":"i","type":"uint256"}],"name":"bands_y","outputs":[{"internalType":"uint256","name":"","type":"uint256"}],"stateMutability":"view","type":"function"},
  {"inputs":[],"name":"active_band","outputs":[{"internalType":"int256","name":"","type":"int256"}],"stateMutability":"view","type":"function"},
  {"inputs":[],"name":"min_band","outputs":[{"internalType":"int256","name":"","type":"int256"}],"stateMutability":"view","type":"function"},
  {"inputs":[],"name":"max_band","outputs":[{"internalType":"int256","name":"","type":"int256"}],"stateMutability":"view","type":"function"},
  {"inputs":[],"name":"A","outputs":[{"internalType":"uint256","name":"","type":"uint256"}],"stateMutability":"view","type":"function"},
  {"inputs":[{"internalType":"uint256","name":"i","type":"uint256"}],"name":"coins","outputs":[{"internalType":"address","name":"","type":"address"}],"stateMutability":"view","type":"function"}
]''')

cf = w3.eth.contract(address=Web3.to_checksum_address(CURVE_FACTORY), abi=CURVE_FACTORY_ABI)

# Focus on high-deviation markets
SUSPICIOUS_MARKETS = [4, 8, 29, 31, 26, 1, 13, 10]

for market_id in SUSPICIOUS_MARKETS:
    vault_addr = safe_call(cf, "vaults", market_id)
    if not vault_addr:
        continue

    vault = w3.eth.contract(address=Web3.to_checksum_address(vault_addr), abi=CURVE_VAULT_ABI)
    asset = safe_call(vault, "asset")
    total_assets = safe_call(vault, "totalAssets") or 0
    controller_addr = safe_call(vault, "controller")
    sym = safe_call(vault, "symbol") or "?"

    if not controller_addr:
        continue

    ctrl = w3.eth.contract(address=Web3.to_checksum_address(controller_addr), abi=CURVE_CONTROLLER_ABI)
    coll = safe_call(ctrl, "collateral_token")
    total_debt = safe_call(ctrl, "total_debt") or 0
    amm_addr = safe_call(ctrl, "amm")
    n_loans = safe_call(ctrl, "n_loans") or 0
    liq_discount = safe_call(ctrl, "liquidation_discount")
    loan_discount = safe_call(ctrl, "loan_discount")

    coll_sym = get_sym(coll) if coll else "?"
    asset_sym = get_sym(asset) if asset else "?"

    amm = w3.eth.contract(address=Web3.to_checksum_address(amm_addr), abi=CURVE_AMM_ABI)
    oracle_price = safe_call(amm, "price_oracle") or 0
    spot_price = safe_call(amm, "get_p") or 0
    active_band = safe_call(amm, "active_band")
    min_band = safe_call(amm, "min_band")
    max_band = safe_call(amm, "max_band")
    A = safe_call(amm, "A")

    if oracle_price > 0:
        dev = abs(oracle_price - spot_price) / oracle_price * 100
    else:
        dev = 0

    # Get AMM balances (how much is in the LLAMMA pool)
    coin0 = safe_call(amm, "coins", 0)
    coin1 = safe_call(amm, "coins", 1)
    coin0_sym = get_sym(coin0) if coin0 else "?"
    coin1_sym = get_sym(coin1) if coin1 else "?"

    if coin0:
        bal0c = w3.eth.contract(address=Web3.to_checksum_address(coin0), abi=ERC20_ABI)
        bal0 = safe_call(bal0c, "balanceOf", Web3.to_checksum_address(amm_addr)) or 0
    else:
        bal0 = 0
    if coin1:
        bal1c = w3.eth.contract(address=Web3.to_checksum_address(coin1), abi=ERC20_ABI)
        bal1 = safe_call(bal1c, "balanceOf", Web3.to_checksum_address(amm_addr)) or 0
    else:
        bal1 = 0

    c0_dec = safe_call(w3.eth.contract(address=Web3.to_checksum_address(coin0), abi=ERC20_ABI), "decimals") if coin0 else 18
    c1_dec = safe_call(w3.eth.contract(address=Web3.to_checksum_address(coin1), abi=ERC20_ABI), "decimals") if coin1 else 18

    print(f"\n{'='*70}")
    print(f"MARKET #{market_id}: {coll_sym}/{asset_sym} — {dev:.1f}% deviation")
    print(f"{'='*70}")
    print(f"  Vault: {vault_addr}")
    print(f"  Controller: {controller_addr}")
    print(f"  AMM: {amm_addr}")
    print(f"  Total Assets: {total_assets / 1e18:,.2f} {asset_sym}")
    print(f"  Total Debt: {total_debt / 1e18:,.2f} crvUSD")
    print(f"  Active Loans: {n_loans}")
    print(f"  Loan Discount: {(loan_discount or 0) / 1e18:.2%}")
    print(f"  Liquidation Discount: {(liq_discount or 0) / 1e18:.2%}")
    print(f"  Oracle Price: {oracle_price / 1e18:,.6f}")
    print(f"  Spot Price: {spot_price / 1e18:,.6f}")
    print(f"  Deviation: {dev:.2f}%")
    print(f"  AMM A: {A}")
    print(f"  Bands: active={active_band}, min={min_band}, max={max_band}")
    print(f"  AMM {coin0_sym} balance: {bal0 / (10**c0_dec):,.4f}")
    print(f"  AMM {coin1_sym} balance: {bal1 / (10**c1_dec):,.4f}")

    # Analysis
    if dev > 10 and total_debt / 1e18 > 10000:
        print(f"\n  *** HIGH DEVIATION + SIGNIFICANT DEBT ***")
        print(f"  Potential exploitation vectors:")
        print(f"  1. If oracle > spot: collateral is OVERVALUED by oracle")
        print(f"     -> Users can borrow more than they should")
        print(f"     -> But LLAMMA oracle is EMA, designed to lag")
        print(f"  2. If oracle < spot: collateral is UNDERVALUED by oracle")
        print(f"     -> Liquidations triggered earlier than market warrants")
        print(f"     -> Could force-liquidate healthy positions")

        if oracle_price > spot_price:
            direction = "ORACLE > SPOT (collateral overvalued)"
            overvalue_pct = (oracle_price - spot_price) / spot_price * 100
            # Can we deposit cheap collateral and borrow against overvalued price?
            print(f"\n  Direction: {direction}")
            print(f"  Overvaluation: {overvalue_pct:.1f}%")
            if liq_discount:
                margin = overvalue_pct - (liq_discount / 1e18 * 100)
                print(f"  After liquidation discount: {margin:.1f}% margin")
                if margin > 5:
                    print(f"  !!! POTENTIAL PROFIT MARGIN > 5% !!!")
        else:
            direction = "SPOT > ORACLE (collateral undervalued)"
            undervalue_pct = (spot_price - oracle_price) / oracle_price * 100
            print(f"\n  Direction: {direction}")
            print(f"  Undervaluation: {undervalue_pct:.1f}%")

    elif dev > 10 and total_debt / 1e18 < 1000:
        print(f"\n  High deviation but low TVL — not economically viable")

print("\n\n" + "="*70)
print("KEY ANALYSIS: LLAMMA ORACLE LAG")
print("="*70)
print("""
Curve LLAMMA uses an EMA (Exponential Moving Average) oracle that INTENTIONALLY
lags behind spot price. Large deviations can be normal during volatile markets.

The oracle is updated via a time-weighted EMA that converges to the external
price oracle (Chainlink) over time. The EMA speed is governed by the 'alpha'
parameter.

For exploitation, we need to determine:
1. Can the oracle-spot deviation be AMPLIFIED by a flash loan?
   - No: LLAMMA oracle is EMA-based, not AMM-spot-based
   - The oracle comes from an EXTERNAL Chainlink feed, not the AMM
2. Can the AMM spot price be manipulated to force bad liquidations?
   - The AMM's get_p() is the internal price, but health() uses price_oracle()
   - price_oracle() uses the EMA of the external oracle, NOT get_p()
3. Is the deviation just normal EMA lag?
   - Most likely YES for the ETH-based markets (1-20% deviation is EMA lag)
   - Market #4 (CRV/crvUSD 494%) is suspicious but might be low-liquidity

Conclusion: LLAMMA oracle deviations are EXPECTED behavior from the EMA design.
The oracle does NOT read from the AMM spot price, so AMM manipulation doesn't
affect liquidations.

The remaining question is whether the EXTERNAL oracle (Chainlink) feeding into
the EMA can be manipulated. But Chainlink feeds are external and costly to
manipulate (multi-block, infrastructure access needed).
""")
