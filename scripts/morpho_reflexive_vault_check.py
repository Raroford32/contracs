#!/usr/bin/env python3
"""
Check for reflexive vault-on-vault loops in Morpho Blue on Ethereum mainnet.

NOVEL COMPOSITION HYPOTHESIS:
If a MetaMorpho vault token is used as collateral in a Morpho market,
AND that vault allocates deposits into the SAME market, we get:
  deposit into vault → vault deposits into market → vault token used as collateral → borrow → deposit again

This creates leverage beyond what the LLTV allows in a single market.

Steps:
1. Find all MetaMorpho vault tokens used as collateral on Morpho
2. Check each vault's supply queue (which markets does it lend into?)
3. Check if the vault token is collateral in any of those markets
"""

import json
import os
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

if not w3:
    exit(1)

MORPHO_API = "https://blue-api.morpho.org/graphql"
ZERO = "0x" + "0" * 40

def safe_call(addr, abi, func_name, *args):
    try:
        c = w3.eth.contract(address=Web3.to_checksum_address(addr), abi=abi)
        return getattr(c.functions, func_name)(*args).call()
    except:
        return None

VAULT_ABI = json.loads('''[
  {"inputs":[],"name":"asset","outputs":[{"type":"address"}],"stateMutability":"view","type":"function"},
  {"inputs":[],"name":"totalAssets","outputs":[{"type":"uint256"}],"stateMutability":"view","type":"function"},
  {"inputs":[],"name":"totalSupply","outputs":[{"type":"uint256"}],"stateMutability":"view","type":"function"},
  {"inputs":[],"name":"symbol","outputs":[{"type":"string"}],"stateMutability":"view","type":"function"},
  {"inputs":[],"name":"curator","outputs":[{"type":"address"}],"stateMutability":"view","type":"function"},
  {"inputs":[{"type":"uint256"}],"name":"supplyQueue","outputs":[{"type":"bytes32"}],"stateMutability":"view","type":"function"},
  {"inputs":[],"name":"supplyQueueLength","outputs":[{"type":"uint256"}],"stateMutability":"view","type":"function"},
  {"inputs":[{"type":"uint256"}],"name":"withdrawQueue","outputs":[{"type":"bytes32"}],"stateMutability":"view","type":"function"},
  {"inputs":[],"name":"withdrawQueueLength","outputs":[{"type":"uint256"}],"stateMutability":"view","type":"function"}
]''')

# Step 1: Get all Morpho markets with significant activity
query = """{
  markets(
    where: { chainId_in: [1], borrowAssetsUsd_gte: 100000 }
    first: 300
    orderBy: BorrowAssetsUsd
    orderDirection: Desc
  ) {
    items {
      uniqueKey
      loanAsset { address symbol }
      collateralAsset { address symbol }
      oracleAddress
      lltv
      state { supplyAssetsUsd borrowAssetsUsd }
    }
  }
}"""

resp = requests.post(MORPHO_API, json={"query": query}, timeout=30)
data = resp.json()
markets = data.get("data", {}).get("markets", {}).get("items", [])
print(f"Markets with >$100K borrow: {len(markets)}")

# Build market index
market_by_key = {}
markets_by_collateral = {}
for m in markets:
    key = m["uniqueKey"]
    market_by_key[key] = m
    coll_addr = m.get("collateralAsset", {}).get("address", "").lower()
    if coll_addr:
        if coll_addr not in markets_by_collateral:
            markets_by_collateral[coll_addr] = []
        markets_by_collateral[coll_addr].append(m)

# Step 2: Find vault-collateral markets (ERC-4626)
vault_collateral_markets = []
for m in markets:
    coll_addr = m.get("collateralAsset", {}).get("address", "")
    if not coll_addr:
        continue

    # Check if collateral is a vault (has asset() function)
    vault_asset = safe_call(coll_addr, VAULT_ABI, "asset")
    if vault_asset:
        curator = safe_call(coll_addr, VAULT_ABI, "curator")
        is_metamorpho = curator is not None
        if is_metamorpho:
            vault_collateral_markets.append({
                "market": m,
                "vault_addr": coll_addr,
                "vault_asset": vault_asset,
                "curator": curator,
            })

print(f"MetaMorpho vault-collateral markets: {len(vault_collateral_markets)}")

# Step 3: Check for reflexive loops
print(f"\n{'='*100}")
print("REFLEXIVE VAULT-ON-VAULT LOOP CHECK")
print(f"{'='*100}")

for entry in vault_collateral_markets:
    m = entry["market"]
    vault_addr = entry["vault_addr"]
    vault_asset = entry["vault_asset"]
    curator = entry["curator"]
    coll_sym = m["collateralAsset"]["symbol"]
    loan_sym = m["loanAsset"]["symbol"]
    borrow = m["state"]["borrowAssetsUsd"] or 0

    print(f"\n  {coll_sym}/{loan_sym} | Borrow: ${borrow:,.0f}")
    print(f"  Vault: {vault_addr}")
    print(f"  Curator: {curator}")

    # Get supply queue
    sq_len = safe_call(vault_addr, VAULT_ABI, "supplyQueueLength") or 0
    print(f"  Supply queue length: {sq_len}")

    market_key = m["uniqueKey"]

    for i in range(min(sq_len, 20)):
        queue_mid = safe_call(vault_addr, VAULT_ABI, "supplyQueue", i)
        if queue_mid:
            queue_hex = "0x" + bytes(queue_mid).hex()

            # Check if this market uses the vault token as collateral
            if queue_hex.lower() == market_key.lower():
                print(f"  !!! REFLEXIVE LOOP DETECTED !!!")
                print(f"  Vault lends into market where its own token is collateral")
                print(f"  Supply queue[{i}] = {queue_hex[:20]}...")
                print(f"  Market key = {market_key[:20]}...")
            else:
                # Check what this market is
                if queue_hex in market_by_key:
                    qm = market_by_key[queue_hex]
                    qc = qm["collateralAsset"]["symbol"]
                    ql = qm["loanAsset"]["symbol"]
                    qb = qm["state"]["borrowAssetsUsd"] or 0
                    print(f"    queue[{i}]: {qc}/{ql} (${qb:,.0f} borrow)")
                else:
                    print(f"    queue[{i}]: {queue_hex[:20]}... (not in top markets)")

    # Also check: does ANY market in the supply queue have a collateral token
    # that is the SAME vault token?
    # This is the indirect reflexive loop
    wq_len = safe_call(vault_addr, VAULT_ABI, "withdrawQueueLength") or 0
    print(f"  Withdraw queue length: {wq_len}")

# Step 4: Also check for INDIRECT reflexive loops
# Vault A lends into Market X
# Market X's collateral is Vault B
# Vault B lends into Market Y
# Market Y's collateral is Vault A
# This creates a circular dependency

print(f"\n{'='*100}")
print("INDIRECT REFLEXIVE LOOP CHECK (2-hop)")
print(f"{'='*100}")

# For each MetaMorpho vault used as collateral, trace its lending destinations
# and check if any of THOSE markets' collateral tokens are ALSO MetaMorpho vaults
# that lend into markets where our original vault is collateral

for entry in vault_collateral_markets:
    m = entry["market"]
    vault_addr = entry["vault_addr"].lower()
    coll_sym = m["collateralAsset"]["symbol"]
    borrow = m["state"]["borrowAssetsUsd"] or 0

    if borrow < 1_000_000:
        continue

    sq_len = safe_call(entry["vault_addr"], VAULT_ABI, "supplyQueueLength") or 0

    for i in range(min(sq_len, 10)):
        queue_mid = safe_call(entry["vault_addr"], VAULT_ABI, "supplyQueue", i)
        if not queue_mid:
            continue

        queue_hex = "0x" + bytes(queue_mid).hex()
        if queue_hex not in market_by_key:
            continue

        qm = market_by_key[queue_hex]
        qcoll_addr = qm["collateralAsset"]["address"].lower()

        # Is this collateral also a MetaMorpho vault?
        qcurator = safe_call(qcoll_addr, VAULT_ABI, "curator")
        if qcurator is None:
            continue

        # It IS a MetaMorpho vault! Check if it lends back to markets
        # where our original vault is collateral
        qsq_len = safe_call(qcoll_addr, VAULT_ABI, "supplyQueueLength") or 0
        for j in range(min(qsq_len, 10)):
            queue2 = safe_call(qcoll_addr, VAULT_ABI, "supplyQueue", j)
            if not queue2:
                continue
            queue2_hex = "0x" + bytes(queue2).hex()

            if queue2_hex in market_by_key:
                q2m = market_by_key[queue2_hex]
                q2coll = q2m["collateralAsset"]["address"].lower()

                if q2coll == vault_addr:
                    print(f"\n  !!! 2-HOP REFLEXIVE LOOP !!!")
                    print(f"  Vault A ({coll_sym}, {vault_addr[:14]}...)")
                    print(f"    → lends into market with collateral {qm['collateralAsset']['symbol']}")
                    print(f"    → that vault ({qcoll_addr[:14]}...) lends into market with collateral Vault A")
                    print(f"  Vault A borrow: ${borrow:,.0f}")

print("\nDone.")
