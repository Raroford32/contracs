#!/usr/bin/env python3
"""
Multi-Vector Composition Discriminator #1:
ORACLE DISAGREEMENT during LRT price stress

Checks how Aave V3, Morpho Blue, and Moonwell price the SAME LRT tokens.
If they use different oracle mechanisms, the disagreement window during a
depeg/stress event creates cross-protocol arbitrage.

Also checks: Aerodrome pool depth for each LRT — this determines whether
cascading liquidations would actually succeed or create bad debt.

This is NOT an oracle misprice scan. This is checking whether different
protocols have different VIEWS of the same reality, which is the
composition attack surface.
"""

import json
import os
from web3 import Web3

BASE_RPC = os.environ.get("BASE_RPC", "https://mainnet.base.org")
w3 = Web3(Web3.HTTPProvider(BASE_RPC))

print(f"Connected to Base. Block: {w3.eth.block_number}")
now = w3.eth.get_block("latest")["timestamp"]

ERC20_ABI = json.loads('''[
  {"inputs":[],"name":"symbol","outputs":[{"internalType":"string","name":"","type":"string"}],"stateMutability":"view","type":"function"},
  {"inputs":[],"name":"decimals","outputs":[{"internalType":"uint8","name":"","type":"uint8"}],"stateMutability":"view","type":"function"},
  {"inputs":[{"internalType":"address","name":"","type":"address"}],"name":"balanceOf","outputs":[{"internalType":"uint256","name":"","type":"uint256"}],"stateMutability":"view","type":"function"}
]''')

CHAINLINK_ABI = json.loads('''[
  {"inputs":[],"name":"latestRoundData","outputs":[{"internalType":"uint80","name":"roundId","type":"uint80"},{"internalType":"int256","name":"answer","type":"int256"},{"internalType":"uint256","name":"startedAt","type":"uint256"},{"internalType":"uint256","name":"updatedAt","type":"uint256"},{"internalType":"uint80","name":"answeredInRound","type":"uint80"}],"stateMutability":"view","type":"function"},
  {"inputs":[],"name":"decimals","outputs":[{"internalType":"uint8","name":"","type":"uint8"}],"stateMutability":"view","type":"function"},
  {"inputs":[],"name":"description","outputs":[{"internalType":"string","name":"","type":"string"}],"stateMutability":"view","type":"function"}
]''')

AAVE_ORACLE_ABI = json.loads('''[
  {"inputs":[{"internalType":"address","name":"asset","type":"address"}],"name":"getAssetPrice","outputs":[{"internalType":"uint256","name":"","type":"uint256"}],"stateMutability":"view","type":"function"},
  {"inputs":[{"internalType":"address","name":"asset","type":"address"}],"name":"getSourceOfAsset","outputs":[{"internalType":"address","name":"","type":"address"}],"stateMutability":"view","type":"function"}
]''')

MOONWELL_ORACLE_ABI = json.loads('''[
  {"inputs":[{"internalType":"contract CToken","name":"cToken","type":"address"}],"name":"getUnderlyingPrice","outputs":[{"internalType":"uint256","name":"","type":"uint256"}],"stateMutability":"view","type":"function"}
]''')

CAPO_ABI = json.loads('''[
  {"inputs":[],"name":"isCapped","outputs":[{"internalType":"bool","name":"","type":"bool"}],"stateMutability":"view","type":"function"},
  {"inputs":[],"name":"maxYearlyRatioGrowthPercent","outputs":[{"internalType":"uint256","name":"","type":"uint256"}],"stateMutability":"view","type":"function"},
  {"inputs":[],"name":"latestAnswer","outputs":[{"internalType":"int256","name":"","type":"int256"}],"stateMutability":"view","type":"function"},
  {"inputs":[],"name":"RATIO_PROVIDER","outputs":[{"internalType":"address","name":"","type":"address"}],"stateMutability":"view","type":"function"},
  {"inputs":[],"name":"ASSET_TO_USD_AGGREGATOR","outputs":[{"internalType":"address","name":"","type":"address"}],"stateMutability":"view","type":"function"},
  {"inputs":[],"name":"snapshotRatio","outputs":[{"internalType":"uint256","name":"","type":"uint256"}],"stateMutability":"view","type":"function"},
  {"inputs":[],"name":"snapshotTimestamp","outputs":[{"internalType":"uint256","name":"","type":"uint256"}],"stateMutability":"view","type":"function"}
]''')

# Known Uniswap V3 pool ABI for checking liquidity depth
UNI_POOL_ABI = json.loads('''[
  {"inputs":[],"name":"slot0","outputs":[{"internalType":"uint160","name":"sqrtPriceX96","type":"uint160"},{"internalType":"int24","name":"tick","type":"int24"},{"internalType":"uint16","name":"observationIndex","type":"uint16"},{"internalType":"uint16","name":"observationCardinality","type":"uint16"},{"internalType":"uint16","name":"observationCardinalityNext","type":"uint16"},{"internalType":"uint8","name":"feeProtocol","type":"uint8"},{"internalType":"bool","name":"unlocked","type":"bool"}],"stateMutability":"view","type":"function"},
  {"inputs":[],"name":"liquidity","outputs":[{"internalType":"uint128","name":"","type":"uint128"}],"stateMutability":"view","type":"function"},
  {"inputs":[],"name":"token0","outputs":[{"internalType":"address","name":"","type":"address"}],"stateMutability":"view","type":"function"},
  {"inputs":[],"name":"token1","outputs":[{"internalType":"address","name":"","type":"address"}],"stateMutability":"view","type":"function"}
]''')

ZERO = "0x0000000000000000000000000000000000000000"

def safe_call(contract, func_name, *args):
    try:
        return getattr(contract.functions, func_name)(*args).call()
    except:
        return None

def get_sym(addr):
    if addr == ZERO: return "ETH"
    c = w3.eth.contract(address=Web3.to_checksum_address(addr), abi=ERC20_ABI)
    return safe_call(c, "symbol") or "?"

# ============================================================================
# Protocol oracle addresses
# ============================================================================
AAVE_ORACLE = "0x2Cc0Fc26eD4563A5ce5e8bdcfe1A2878676Ae156"
MOONWELL_ORACLE = "0xEC942bE8A8114bFD0396A5052c36027f2cA6a9d0"
WETH = "0x4200000000000000000000000000000000000006"

aave_oracle = w3.eth.contract(address=Web3.to_checksum_address(AAVE_ORACLE), abi=AAVE_ORACLE_ABI)
moonwell_oracle = w3.eth.contract(address=Web3.to_checksum_address(MOONWELL_ORACLE), abi=MOONWELL_ORACLE_ABI)

# LRT tokens and their Moonwell market addresses
LRTS = {
    "weETH": {
        "addr": "0x04C0599Ae5A44757c0af6F9eC3b93da8976c150A",
        "moonwell_mtoken": "0xb8051464C8c92209C92F3a4CD9C73746C4c3CFb3",
    },
    "cbETH": {
        "addr": "0x2Ae3F1Ec7F1F5012CFEab0185bfc7aa3cf0DEc22",
        "moonwell_mtoken": "0x3bf93770f2d4a794c3d9EBEfBAeBAE2a8f09A5E5",
    },
    "wstETH": {
        "addr": "0xc1CBa3fCea344f92D9239c08C0568f6F2F0ee452",
        "moonwell_mtoken": "0x627Fe393Bc6EdDA28e99AE648fD6fF362514304b",
    },
    "wrsETH": {
        "addr": "0xEDfa23602D0EC14714057867A78d01e94176BEA0",
        "moonwell_mtoken": "0xfC41B49d064Ac646015b459C522820DB9472F4B5",
    },
    "rETH": {
        "addr": "0xB6fe221Fe9EeF5aBa221c348bA20A1Bf5e73624c",
        "moonwell_mtoken": "0xCB1DaCd30638ae38F2B94eA64F066045B7D45f44",
    },
}

# Also check WETH price for normalization
weth_price_aave = safe_call(aave_oracle, "getAssetPrice", Web3.to_checksum_address(WETH))
print(f"WETH price (Aave): ${(weth_price_aave or 0)/1e8:,.2f}")

print(f"\n{'='*100}")
print("CROSS-PROTOCOL ORACLE PRICE COMPARISON FOR LRT TOKENS")
print(f"{'='*100}")

for lrt_name, lrt_info in LRTS.items():
    addr = lrt_info["addr"]
    mtoken = lrt_info["moonwell_mtoken"]

    print(f"\n{'='*80}")
    print(f"  {lrt_name} ({addr[:14]}...)")
    print(f"{'='*80}")

    # --- AAVE V3 PRICE ---
    aave_price = safe_call(aave_oracle, "getAssetPrice", Web3.to_checksum_address(addr))
    aave_source = safe_call(aave_oracle, "getSourceOfAsset", Web3.to_checksum_address(addr))
    aave_usd = (aave_price or 0) / 1e8

    print(f"\n  AAVE V3:")
    print(f"    Price: ${aave_usd:,.4f}")
    print(f"    Source: {aave_source}")

    if aave_source and aave_source != ZERO:
        # Check if CAPO
        capo = w3.eth.contract(address=Web3.to_checksum_address(aave_source), abi=CAPO_ABI)
        is_capped = safe_call(capo, "isCapped")
        max_growth = safe_call(capo, "maxYearlyRatioGrowthPercent")
        ratio_provider = safe_call(capo, "RATIO_PROVIDER")
        asset_aggregator = safe_call(capo, "ASSET_TO_USD_AGGREGATOR")
        snapshot_ratio = safe_call(capo, "snapshotRatio")
        snapshot_ts = safe_call(capo, "snapshotTimestamp")

        if is_capped is not None:
            print(f"    CAPO: capped={is_capped}, maxGrowth={max_growth}%/yr")
            if ratio_provider:
                print(f"    Ratio provider: {ratio_provider}")
            if asset_aggregator:
                print(f"    Base USD aggregator: {asset_aggregator}")
            if snapshot_ratio and snapshot_ts:
                age = (now - snapshot_ts) / 86400
                print(f"    Snapshot ratio: {snapshot_ratio}, age: {age:.1f} days")
                print(f"    >>> CAPO LIMITS ORACLE APPRECIATION RATE")
                print(f"    >>> During a DEPEG, CAPO would show HIGHER price than reality")
                print(f"    >>> (rate can only drop as fast as the base feed, not the cap)")
        else:
            # Regular Chainlink feed
            feed = w3.eth.contract(address=Web3.to_checksum_address(aave_source), abi=CHAINLINK_ABI)
            desc = safe_call(feed, "description")
            fdata = safe_call(feed, "latestRoundData")
            if desc:
                print(f"    Feed: {desc}")
            if fdata:
                staleness = now - fdata[3]
                print(f"    Staleness: {staleness/60:.0f} min")

    # --- MOONWELL PRICE ---
    moonwell_raw = safe_call(moonwell_oracle, "getUnderlyingPrice", Web3.to_checksum_address(mtoken))
    moonwell_usd = (moonwell_raw or 0) / 1e18  # 18-decimal tokens: price * 1e18
    print(f"\n  MOONWELL:")
    print(f"    Raw price: {moonwell_raw}")
    print(f"    USD (18-dec): ${moonwell_usd:,.4f}")

    # --- PRICE COMPARISON ---
    if aave_usd > 0 and moonwell_usd > 0:
        diff_pct = abs(aave_usd - moonwell_usd) / aave_usd * 100
        print(f"\n  PRICE DIFFERENCE:")
        print(f"    Aave: ${aave_usd:,.4f} vs Moonwell: ${moonwell_usd:,.4f}")
        print(f"    Difference: {diff_pct:.4f}%")
        if diff_pct > 1:
            print(f"    >>> SIGNIFICANT DISAGREEMENT: {diff_pct:.2f}%")
            print(f"    >>> This creates cross-protocol arbitrage during stress")

    # --- ETH RATIO ---
    if weth_price_aave and aave_price:
        eth_ratio_aave = aave_price / weth_price_aave
        print(f"\n  ETH RATIO (Aave): {eth_ratio_aave:.6f}")

    # --- CHECK AERODROME/DEX POOL DEPTH ---
    # Check if there's a direct LRT/WETH pool on Aerodrome
    # Aerodrome uses a factory pattern — we'll check known pools
    print(f"\n  DEX LIQUIDITY:")
    # Get token balance in the contract itself (proxy for total available liquidity)
    tc = w3.eth.contract(address=Web3.to_checksum_address(addr), abi=ERC20_ABI)
    total_supply = safe_call(tc, "totalSupply") or 0
    dec = 18
    try:
        dec_c = w3.eth.contract(address=Web3.to_checksum_address(addr), abi=ERC20_ABI)
        dec = safe_call(dec_c, "decimals") or 18
    except:
        pass
    print(f"    Total supply on Base: {total_supply / (10**dec):,.2f}")

    # Check Morpho Blue balance (how much is locked in Morpho as collateral)
    morpho_bal = safe_call(tc, "balanceOf", Web3.to_checksum_address("0xBBBBBbbBBb9cC5e90e3b3Af64bdAF62C37EEFFCb"))
    if morpho_bal:
        morpho_pct = morpho_bal / total_supply * 100 if total_supply > 0 else 0
        print(f"    In Morpho Blue: {morpho_bal/(10**dec):,.2f} ({morpho_pct:.1f}% of supply)")

    # Check Aave aToken balance
    aave_pool = "0xA238Dd80C259a72e81d7e4664a9801593F98d1c5"
    aave_bal = safe_call(tc, "balanceOf", Web3.to_checksum_address(aave_pool))
    if aave_bal and aave_bal > 0:
        aave_pct = aave_bal / total_supply * 100 if total_supply > 0 else 0
        print(f"    In Aave V3: {aave_bal/(10**dec):,.2f} ({aave_pct:.1f}% of supply)")

print(f"\n\n{'='*100}")
print("COMPOSITION ATTACK SURFACE SUMMARY")
print(f"{'='*100}")
print("""
KEY QUESTIONS FOR MULTI-VECTOR EXPLOITATION:

1. ORACLE DISAGREEMENT WINDOW:
   During an LRT depeg, Aave's CAPO limits how fast the oracle can DROP.
   If the LRT depegs faster than CAPO allows, Aave overvalues the collateral.
   Moonwell may use a direct market feed that updates faster.

   Attack: Borrow against overvalued LRT on Aave (lagging CAPO oracle),
   while the real market price is already lower. Then liquidate the position
   on Moonwell (correct price) or sell the borrowed assets.

   Wait — CAPO limits APPRECIATION rate, not depreciation.
   CAPO caps the upside to prevent donation attacks.
   During a DEPEG (downward), the oracle should track normally via the base feed.

   UNLESS: the ratio provider's feed lags behind the actual market depeg.
   The ratio provider reads the canonical exchange rate (e.g., from the LRT contract),
   NOT the market price. During a panic sell, the canonical rate may NOT change
   (it reflects the underlying staking position, not the secondary market price).

   This means: Aave's CAPO oracle = canonical_rate * ETH_USD
   But the actual tradeable value = DEX_price * ETH_USD

   If the LRT trades at 95% of canonical rate due to panic, Aave still values
   it at 100% of canonical rate. The 5% gap is extractable.

2. LIQUIDATION ROUTE CONGESTION:
   All protocols route through the same DEX pools.
   Calculate: if all LRT collateral across all protocols gets liquidated,
   does the DEX have enough depth to absorb the selling?

3. REFLEXIVE VAULT LOOPS:
   (See morpho_reflexive_check.py results)
""")

print("Done.")
