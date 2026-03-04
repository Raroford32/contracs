#!/usr/bin/env python3
"""
Quantify the NUSD oracle risk with backup=primary misconfiguration.

Finding summary:
- PT-sNUSD and PT-srNUSD Morpho Blue markets use MetaOracleDeviationTimelock
- Backup oracle = primary oracle (same contract)
- Deviation detection is dead — cannot catch NUSD depeg
- Deterministic oracle always prices PT near $1.00 regardless of NUSD market price
- NUSD has depegged to $0.975 (Nov 2025), has NO Chainlink feed
- Total exposed: ~$7.7M in borrow

Need to check:
1. LLTV for each market
2. What depeg level triggers bad debt
3. Who supplies the lending side (who bears the risk)
4. Current health factors of positions
"""

import os
import time
import json
import requests
from web3 import Web3

RPCS = [
    os.environ.get("ETH_RPC", ""),
    "https://ethereum-rpc.publicnode.com",
    "https://1rpc.io/eth",
]
RPCS = [r for r in RPCS if r]

w3 = None
for rpc in RPCS:
    try:
        _w3 = Web3(Web3.HTTPProvider(rpc, request_kwargs={"timeout": 15}))
        bn = _w3.eth.block_number
        w3 = _w3
        print(f"Block: {bn}")
        break
    except:
        continue

now = w3.eth.get_block("latest")["timestamp"]
print(f"Time: {time.strftime('%Y-%m-%d %H:%M:%S UTC', time.gmtime(now))}")

# ============================================================================
# Get market details from Morpho API
# ============================================================================
MORPHO_API = "https://blue-api.morpho.org/graphql"

# Query with more details
query = """{
  markets(
    where: { chainId_in: [1] }
    first: 500
    orderBy: BorrowAssetsUsd
    orderDirection: Desc
  ) {
    items {
      uniqueKey
      loanAsset { address symbol decimals }
      collateralAsset { address symbol decimals }
      oracleAddress
      lltv
      state {
        supplyAssetsUsd
        borrowAssetsUsd
        supplyAssets
        borrowAssets
        utilization
      }
    }
  }
}"""

resp = requests.post(MORPHO_API, json={"query": query}, timeout=30)
data = resp.json()
markets = data.get("data", {}).get("markets", {}).get("items", [])

# Find NUSD markets
nusd_markets = []
for m in markets:
    cs = m.get("collateralAsset", {}).get("symbol", "")
    if "NUSD" in cs.upper() and "PT" in cs.upper():
        nusd_markets.append(m)

print(f"\nNUSD-related PT markets found: {len(nusd_markets)}")

for m in nusd_markets:
    cs = m["collateralAsset"]["symbol"]
    ls = m["loanAsset"]["symbol"]
    lltv_raw = int(m["lltv"]) if m["lltv"] else 0
    lltv_pct = lltv_raw / 1e18 * 100

    supply = m["state"]["supplyAssetsUsd"] or 0
    borrow = m["state"]["borrowAssetsUsd"] or 0
    util = m["state"]["utilization"] or 0

    print(f"\n{'='*80}")
    print(f"  {cs} / {ls}")
    print(f"  Market ID: {m['uniqueKey'][:20]}...")
    print(f"  Oracle: {m['oracleAddress']}")
    print(f"  LLTV: {lltv_pct:.2f}%")
    print(f"  Supply: ${supply:,.0f}")
    print(f"  Borrow: ${borrow:,.0f}")
    print(f"  Utilization: {util:.4f}")

    if lltv_pct > 0 and borrow > 0:
        # Calculate depeg threshold for bad debt
        # With LLTV = X%, positions are liquidatable when collateral/debt < 1/LLTV
        # But with a broken oracle, positions are never liquidated
        # Bad debt occurs when true collateral value < debt value
        # If oracle says $1.0 but NUSD is at $P:
        #   - Borrower has $1.0 * collateral_amount of oracle-valued collateral
        #   - Borrower has $borrow_amount of debt
        #   - Health factor (oracle) = oracle_collateral_value / debt * LLTV
        #   - True health = true_collateral_value / debt * LLTV = (P / 1.0) * health_oracle
        #   - Bad debt when true_collateral < debt, i.e., P < debt/collateral_oracle

        max_borrow_per_dollar = lltv_pct / 100
        print(f"\n  RISK ANALYSIS:")
        print(f"  Max borrowable per $1 oracle collateral: ${max_borrow_per_dollar:.4f}")
        print(f"  Break-even NUSD price: ${max_borrow_per_dollar:.4f}")
        print(f"    (If NUSD falls below this, bad debt starts accumulating)")

        # At NUSD = $0.975 (historical low):
        p_historical = 0.975
        overvaluation = (1.0 - p_historical) / 1.0 * 100
        potential_bad_debt_pct = max(0, (1 - p_historical / 1.0) * max_borrow_per_dollar)
        potential_bad_debt_usd = borrow * potential_bad_debt_pct

        print(f"\n  At historical low ($0.975):")
        print(f"    Overvaluation: {overvaluation:.1f}%")
        print(f"    Oracle still says $1.0 → no liquidation triggered")
        if p_historical > max_borrow_per_dollar:
            print(f"    No bad debt yet (NUSD > break-even {max_borrow_per_dollar:.4f})")
        else:
            print(f"    BAD DEBT: ${potential_bad_debt_usd:,.0f}")

        # At various depeg levels
        print(f"\n  Depeg scenarios (oracle always shows $1.0, no liquidation):")
        for depeg_pct in [2, 5, 10, 15, 20, 30, 50]:
            p = 1.0 - depeg_pct / 100
            # Bad debt = borrow * max(0, 1 - p/max_borrow_per_dollar) ... no
            # Actually: for a fully-utilized position at LLTV:
            #   collateral_value_oracle = debt / LLTV (position at max borrow)
            #   collateral_value_true = collateral_value_oracle * p = debt * p / LLTV
            #   bad debt if collateral_value_true < debt → p < LLTV
            #   bad debt amount = debt - collateral_value_true = debt * (1 - p/LLTV)

            if p < max_borrow_per_dollar:
                bad_debt = borrow * (1 - p / max_borrow_per_dollar)
                print(f"    NUSD at ${p:.2f} ({depeg_pct}% depeg): BAD DEBT = ${bad_debt:,.0f}")
            else:
                print(f"    NUSD at ${p:.2f} ({depeg_pct}% depeg): No bad debt (collateral > debt)")

        # Attack scenario: intentional depeg via Curve pool
        print(f"\n  ATTACK SCENARIO (intentional NUSD depeg):")
        print(f"    NUSD Curve pool liquidity: ~$10M")
        print(f"    To depeg NUSD by 10%: sell ~$5M NUSD into Curve")
        print(f"    Attacker deposits PT-sNUSD as collateral, oracle sees $1.0")
        print(f"    Borrows USDC at LLTV, then NUSD depegs, oracle doesn't catch it")
        print(f"    Profit = debt - true_collateral_value")

        # Check: can attacker flash-borrow NUSD?
        print(f"\n  FLASH LOAN FEASIBILITY:")
        print(f"    Deterministic oracle → flash loan doesn't change price")
        print(f"    Need sustained depeg, not single-tx manipulation")
        print(f"    But: attacker can POSITION FIRST (deposit PT, borrow USDC)")
        print(f"    Then trigger depeg separately (sell NUSD on Curve)")
        print(f"    Oracle never catches it → attacker walks away with excess debt")

# ============================================================================
# Also check: who is the curator/lender for these markets?
# ============================================================================
print(f"\n{'='*80}")
print("MARKET CURATOR / VAULT ANALYSIS")
print("=" * 80)

# Check if any MetaMorpho vault allocates to these markets
vault_query = """{
  vaults(
    where: { chainId_in: [1], totalAssetsUsd_gte: 100000 }
    first: 200
    orderBy: TotalAssetsUsd
    orderDirection: Desc
  ) {
    items {
      address
      name
      symbol
      curator { address }
      state {
        totalAssetsUsd
        totalSupplyUsd
      }
    }
  }
}"""

resp2 = requests.post(MORPHO_API, json={"query": vault_query}, timeout=30)
data2 = resp2.json()
vaults = data2.get("data", {}).get("vaults", {}).get("items", [])
print(f"MetaMorpho vaults with >$100K: {len(vaults)}")

for v in vaults[:20]:
    name = v.get("name", "?")
    ta = v.get("state", {}).get("totalAssetsUsd", 0) or 0
    curator = v.get("curator", {}).get("address", "?") if v.get("curator") else "none"
    if "steakhouse" in name.lower() or "nusd" in name.lower() or "steak" in name.lower():
        print(f"  {name}: ${ta:,.0f} (curator: {curator})")

print("\nDone.")
