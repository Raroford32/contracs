#!/usr/bin/env python3
"""
Direct scan of smaller/newer lending and vault protocols on Ethereum mainnet.
Check their oracle configurations for misconfigurations that could be exploited.

Approach: enumerate known smaller protocols, check their oracle setups,
find price anomalies that would enable over-borrowing or under-liquidation.
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
    if addr.lower() in ("0xeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeee", "0x0000000000000000000000000000000000000000"):
        return "ETH"
    c = w3.eth.contract(address=Web3.to_checksum_address(addr), abi=ERC20_ABI)
    return safe_call(c, "symbol") or "?"

def get_dec(addr):
    if addr.lower() in ("0xeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeee", "0x0000000000000000000000000000000000000000"):
        return 18
    c = w3.eth.contract(address=Web3.to_checksum_address(addr), abi=ERC20_ABI)
    return safe_call(c, "decimals") or 18

def get_bal(token_addr, holder_addr):
    if token_addr.lower() in ("0xeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeee",):
        return w3.eth.get_balance(Web3.to_checksum_address(holder_addr))
    c = w3.eth.contract(address=Web3.to_checksum_address(token_addr), abi=ERC20_ABI)
    return safe_call(c, "balanceOf", Web3.to_checksum_address(holder_addr)) or 0

# ============================================================
# 1. SILO FINANCE V1 — Isolated lending markets
# ============================================================
print("\n" + "="*80)
print("1. SILO FINANCE V1")
print("="*80)

SILO_ROUTER = "0x8658047e48CC09161f4152c79155Dac1d710Ff0a"
SILO_REPOSITORY = "0xd998C35B7900b344bbBe6555cc11576942Cf309d"

SILO_REPO_ABI = json.loads('''[
  {"inputs":[],"name":"getSiloArray","outputs":[{"internalType":"address[]","name":"","type":"address[]"}],"stateMutability":"view","type":"function"},
  {"inputs":[],"name":"priceProvidersRepository","outputs":[{"internalType":"contract IPriceProvidersRepository","name":"","type":"address"}],"stateMutability":"view","type":"function"}
]''')

SILO_ABI = json.loads('''[
  {"inputs":[],"name":"assetStorage","outputs":[{"internalType":"address","name":"collateralToken","type":"address"},{"internalType":"address","name":"collateralOnlyToken","type":"address"},{"internalType":"address","name":"debtToken","type":"address"}],"stateMutability":"view","type":"function"},
  {"inputs":[],"name":"siloAsset","outputs":[{"internalType":"address","name":"","type":"address"}],"stateMutability":"view","type":"function"}
]''')

try:
    repo = w3.eth.contract(address=Web3.to_checksum_address(SILO_REPOSITORY), abi=SILO_REPO_ABI)
    silos = safe_call(repo, "getSiloArray")
    if silos:
        print(f"  Total Silos: {len(silos)}")
        price_repo = safe_call(repo, "priceProvidersRepository")
        print(f"  Price Providers Repository: {price_repo}")

        # Check a few silos for their assets and TVL
        for i, silo_addr in enumerate(silos[:5]):
            silo = w3.eth.contract(address=Web3.to_checksum_address(silo_addr), abi=SILO_ABI)
            asset = safe_call(silo, "siloAsset")
            if asset:
                sym = get_sym(asset)
                dec = get_dec(asset)
                bal = get_bal(asset, silo_addr)
                amount = bal / (10 ** dec)
                print(f"  Silo #{i}: {silo_addr} | Asset: {sym} | Balance: {amount:,.2f}")
    else:
        print("  Could not get silo array")
except Exception as e:
    print(f"  Error: {e}")

# ============================================================
# 2. INVERSE FINANCE (FiRM) — Fixed-Rate Market
# ============================================================
print("\n" + "="*80)
print("2. INVERSE FINANCE (FiRM)")
print("="*80)

# FiRM uses a custom oracle (DolaBorrowingRights + markets)
FIRM_MARKETS = [
    ("0x63Df5e4bB1b tried ", "wstETH"),  # placeholder
]

# FiRM Market interface
FIRM_MARKET_ABI = json.loads('''[
  {"inputs":[],"name":"oracle","outputs":[{"internalType":"contract IOracle","name":"","type":"address"}],"stateMutability":"view","type":"function"},
  {"inputs":[],"name":"collateral","outputs":[{"internalType":"contract IERC20","name":"","type":"address"}],"stateMutability":"view","type":"function"},
  {"inputs":[],"name":"totalDebt","outputs":[{"internalType":"uint256","name":"","type":"uint256"}],"stateMutability":"view","type":"function"},
  {"inputs":[],"name":"collateralFactorBps","outputs":[{"internalType":"uint256","name":"","type":"uint256"}],"stateMutability":"view","type":"function"}
]''')

FIRM_ORACLE_ABI = json.loads('''[
  {"inputs":[{"internalType":"contract IERC20","name":"token","type":"address"},{"internalType":"uint256","name":"","type":"uint256"}],"name":"getPrice","outputs":[{"internalType":"uint256","name":"","type":"uint256"}],"stateMutability":"view","type":"function"},
  {"inputs":[{"internalType":"contract IERC20","name":"token","type":"address"}],"name":"viewPrice","outputs":[{"internalType":"uint256","name":"price","type":"uint256"},{"internalType":"uint8","name":"confidence","type":"uint8"}],"stateMutability":"view","type":"function"}
]''')

# FiRM Markets - find them through events or known addresses
# Inverse Finance DBR (DOLA Borrowing Rights) token
DBR = "0xAD038Eb671c44b853887A7E32528FaB35dC5D710"
# Inverse Finance Fed controller
DOLA = "0x865377367054516e17014CcdED1e7d814EDC9ce4"

# Let's check known FiRM markets
FIRM_KNOWN_MARKETS = [
    "0xb516247596Ca36bf32876199FBdCaD6B3322330B",  # INV market
    "0x6C5d9C370677E57eE0e28Ce6890101FaA9e6fDC6",  # DOLA market?
]

for addr in FIRM_KNOWN_MARKETS:
    if not w3.eth.get_code(Web3.to_checksum_address(addr)):
        continue
    market = w3.eth.contract(address=Web3.to_checksum_address(addr), abi=FIRM_MARKET_ABI)
    oracle_addr = safe_call(market, "oracle")
    collateral = safe_call(market, "collateral")
    debt = safe_call(market, "totalDebt")
    cf = safe_call(market, "collateralFactorBps")

    if collateral:
        sym = get_sym(collateral)
        bal = get_bal(collateral, addr)
        dec = get_dec(collateral)
        print(f"\n  Market: {addr}")
        print(f"    Collateral: {sym} ({collateral})")
        print(f"    Balance: {bal / (10**dec):,.2f} {sym}")
        print(f"    Total Debt: {(debt or 0) / 1e18:,.2f} DOLA")
        print(f"    CF: {(cf or 0)/100:.0f}%")
        print(f"    Oracle: {oracle_addr}")

        if oracle_addr:
            oracle = w3.eth.contract(address=Web3.to_checksum_address(oracle_addr), abi=FIRM_ORACLE_ABI)
            price = safe_call(oracle, "viewPrice", Web3.to_checksum_address(collateral))
            if price:
                print(f"    Price: {price}")

# ============================================================
# 3. GEARBOX V3 — Credit Accounts with complex oracle
# ============================================================
print("\n" + "="*80)
print("3. GEARBOX V3")
print("="*80)

# Gearbox uses PriceOracle with complex feed chains
GEARBOX_ADDRESS_PROVIDER = "0x9ea7b04Da02a5373317D745c1571c84aaD03321D"

GEARBOX_AP_ABI = json.loads('''[
  {"inputs":[],"name":"getAddressOrRevert","outputs":[{"internalType":"address","name":"","type":"address"}],"stateMutability":"view","type":"function"},
  {"inputs":[{"internalType":"bytes32","name":"key","type":"bytes32"},{"internalType":"uint256","name":"_version","type":"uint256"}],"name":"getAddressOrRevert","outputs":[{"internalType":"address","name":"result","type":"address"}],"stateMutability":"view","type":"function"}
]''')

# Gearbox V3 Price Oracle key
PRICE_ORACLE_KEY = w3.keccak(text="PRICE_ORACLE")
ap = w3.eth.contract(address=Web3.to_checksum_address(GEARBOX_ADDRESS_PROVIDER), abi=GEARBOX_AP_ABI)
# Try to get the price oracle
gearbox_oracle = safe_call(ap, "getAddressOrRevert", PRICE_ORACLE_KEY, 3)
print(f"  Address Provider: {GEARBOX_ADDRESS_PROVIDER}")
print(f"  Price Oracle (V3): {gearbox_oracle}")

if gearbox_oracle:
    GEARBOX_ORACLE_ABI = json.loads('''[
      {"inputs":[{"internalType":"address","name":"token","type":"address"}],"name":"getPrice","outputs":[{"internalType":"uint256","name":"price","type":"uint256"}],"stateMutability":"view","type":"function"},
      {"inputs":[{"internalType":"address","name":"token","type":"address"}],"name":"priceFeeds","outputs":[{"internalType":"address","name":"priceFeed","type":"address"},{"internalType":"uint32","name":"stalenessPeriod","type":"uint32"},{"internalType":"bool","name":"skipCheck","type":"bool"},{"internalType":"uint8","name":"decimals","type":"uint8"}],"stateMutability":"view","type":"function"}
    ]''')

    go = w3.eth.contract(address=Web3.to_checksum_address(gearbox_oracle), abi=GEARBOX_ORACLE_ABI)

    # Check key tokens
    tokens_to_check = {
        "WETH": "0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2",
        "wstETH": "0x7f39C581F595B53c5cb19bD0b3f8dA6c935E2Ca0",
        "USDC": "0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48",
        "WBTC": "0x2260FAC5E5542a773Aa44fBCfeDf7C193bc2C599",
        "weETH": "0xCd5fE23C85820F7B72D0926FC9b05b43E359b7ee",
        "sUSDe": "0x9D39A5DE30e57443BfF2A8307A4256c8797A3497",
        "USDe": "0x4c9EDD5852cd905f086C759E8383e09bff1E68B3",
        "GHO": "0x40D16FC0246aD3160Ccc09B8D0D3A2cD28aE6C2f",
        "USDS": "0xdC035D45d973E3EC169d2276DDab16f1e407384F",
        "cbBTC": "0xcbB7C0000aB88B473b1f5aFd9ef808440eed33Bf",
        "PT-sUSDe-29MAY2025": "0xE00bd3Df25fb187d6ABBB620b3dfd19839947b81",
        "PT-eUSDe-29MAY2025": "0x50D2C7053a40dBc0daCf56e38C48850bcC200dA0",
        "rsETH": "0xA1290d69c65A6Fe4DF752f95823fae25cB99e5A7",
        "ezETH": "0xbf5495Efe5DB9ce00f80364C8B423567e58d2110",
    }

    for name, addr in tokens_to_check.items():
        price = safe_call(go, "getPrice", Web3.to_checksum_address(addr))
        feed_info = safe_call(go, "priceFeeds", Web3.to_checksum_address(addr))

        if price:
            # Gearbox prices are in USD with 8 decimals
            usd_price = price / 1e8
            print(f"  {name}: ${usd_price:,.4f}")

            if feed_info:
                feed_addr, staleness, skip_check, feed_dec = feed_info
                flags = []
                if skip_check:
                    flags.append("SKIP_CHECK!")
                if staleness > 86400:
                    flags.append(f"STALE_OK({staleness}s)")
                flag_str = " ".join(flags)
                print(f"    Feed: {feed_addr} | staleness: {staleness}s | decimals: {feed_dec} {flag_str}")

                # Check for anomalies
                if name in ("USDC", "USDT", "DAI", "GHO", "USDS", "USDe", "FRAX"):
                    if usd_price > 2 or usd_price < 0.5:
                        print(f"    *** STABLECOIN PRICE ANOMALY: ${usd_price:.4f} ***")
                elif name in ("WETH", "wstETH", "weETH", "cbETH", "rETH", "rsETH", "ezETH"):
                    if usd_price > 100000 or usd_price < 100:
                        print(f"    *** ETH-LIKE PRICE ANOMALY: ${usd_price:.4f} ***")
                elif name in ("WBTC", "cbBTC"):
                    if usd_price > 1000000 or usd_price < 10000:
                        print(f"    *** BTC-LIKE PRICE ANOMALY: ${usd_price:.4f} ***")

                if skip_check:
                    print(f"    *** WARNING: STALENESS CHECK DISABLED ***")

# ============================================================
# 4. PRISMA FINANCE — CDP protocol
# ============================================================
print("\n" + "="*80)
print("4. PRISMA FINANCE")
print("="*80)

PRISMA_FACTORY = "0x70b66E20766b775B2E9cE5B718bbD285Af59b7E1"
PRISMA_FACTORY_ABI = json.loads('''[
  {"inputs":[],"name":"troveManagerCount","outputs":[{"internalType":"uint256","name":"","type":"uint256"}],"stateMutability":"view","type":"function"},
  {"inputs":[{"internalType":"uint256","name":"","type":"uint256"}],"name":"troveManagers","outputs":[{"internalType":"address","name":"","type":"address"}],"stateMutability":"view","type":"function"},
  {"inputs":[],"name":"priceFeed","outputs":[{"internalType":"contract IPriceFeed","name":"","type":"address"}],"stateMutability":"view","type":"function"}
]''')

TROVE_MGR_ABI = json.loads('''[
  {"inputs":[],"name":"collateralToken","outputs":[{"internalType":"contract IERC20","name":"","type":"address"}],"stateMutability":"view","type":"function"},
  {"inputs":[],"name":"getTotalActiveCollateral","outputs":[{"internalType":"uint256","name":"","type":"uint256"}],"stateMutability":"view","type":"function"},
  {"inputs":[],"name":"getTotalActiveDebt","outputs":[{"internalType":"uint256","name":"","type":"uint256"}],"stateMutability":"view","type":"function"}
]''')

try:
    pf = w3.eth.contract(address=Web3.to_checksum_address(PRISMA_FACTORY), abi=PRISMA_FACTORY_ABI)
    tm_count = safe_call(pf, "troveManagerCount")
    price_feed = safe_call(pf, "priceFeed")
    print(f"  Factory: {PRISMA_FACTORY}")
    print(f"  Trove Managers: {tm_count}")
    print(f"  Price Feed: {price_feed}")

    if tm_count:
        for i in range(tm_count):
            tm_addr = safe_call(pf, "troveManagers", i)
            if tm_addr:
                tm = w3.eth.contract(address=Web3.to_checksum_address(tm_addr), abi=TROVE_MGR_ABI)
                coll = safe_call(tm, "collateralToken")
                total_coll = safe_call(tm, "getTotalActiveCollateral") or 0
                total_debt = safe_call(tm, "getTotalActiveDebt") or 0

                if coll:
                    sym = get_sym(coll)
                    dec = get_dec(coll)
                    print(f"\n  TroveManager #{i}: {tm_addr}")
                    print(f"    Collateral: {sym}")
                    print(f"    Active Collateral: {total_coll / (10**dec):,.2f} {sym}")
                    print(f"    Active Debt: {total_debt / 1e18:,.2f} mkUSD")
except Exception as e:
    print(f"  Error: {e}")

# ============================================================
# 5. GRAVITA PROTOCOL — CDP
# ============================================================
print("\n" + "="*80)
print("5. GRAVITA PROTOCOL")
print("="*80)

GRAVITA_BORROWER_OPS = "0x2bCA0300c2aa65de6F19c2d241B54a445C9990E2"
GRAVITA_ADMIN = "0xf7Cc67326F9A1D057c1e4b110eF6c680B13a1f53"
GRAVITA_VESSEL_MGR = "0xdB5DAcB1DFbe16326C3656a88017f0cB4ece0977"

VESSEL_MGR_ABI = json.loads('''[
  {"inputs":[],"name":"getEntireSystemColl","outputs":[{"internalType":"uint256","name":"entireSystemColl","type":"uint256"}],"stateMutability":"view","type":"function"},
  {"inputs":[],"name":"getEntireSystemDebt","outputs":[{"internalType":"uint256","name":"entireSystemDebt","type":"uint256"}],"stateMutability":"view","type":"function"}
]''')

try:
    vm = w3.eth.contract(address=Web3.to_checksum_address(GRAVITA_VESSEL_MGR), abi=VESSEL_MGR_ABI)
    total_coll = safe_call(vm, "getEntireSystemColl") or 0
    total_debt = safe_call(vm, "getEntireSystemDebt") or 0
    print(f"  Vessel Manager: {GRAVITA_VESSEL_MGR}")
    print(f"  Total Collateral: {total_coll / 1e18:,.2f}")
    print(f"  Total Debt: {total_debt / 1e18:,.2f} GRAI")
except Exception as e:
    print(f"  Error: {e}")

# ============================================================
# 6. CURVE LENDING (crvUSD LLAMMA markets)
# ============================================================
print("\n" + "="*80)
print("6. CURVE LENDING (crvUSD)")
print("="*80)

# crvUSD Controller Factory
CRVUSD_FACTORY = "0xC9332fdCB1C4b38bFAc67bA03C1E11B043aB4950"
has_code = len(w3.eth.get_code(Web3.to_checksum_address(CRVUSD_FACTORY)))
print(f"  Factory ({CRVUSD_FACTORY}): {'LIVE' if has_code > 2 else 'DEAD'} ({has_code} bytes)")

# Alternative: Curve Lending factory
CURVE_LENDING_FACTORY = "0xeA6876DDE9e3467564acBeE1Ed5bac88783205E0"
has_code2 = len(w3.eth.get_code(Web3.to_checksum_address(CURVE_LENDING_FACTORY)))
print(f"  Lending Factory ({CURVE_LENDING_FACTORY}): {'LIVE' if has_code2 > 2 else 'DEAD'} ({has_code2} bytes)")

# ============================================================
# 7. SPARK PROTOCOL — Aave V3 fork by MakerDAO
# ============================================================
print("\n" + "="*80)
print("7. SPARK PROTOCOL (MakerDAO)")
print("="*80)

SPARK_POOL = "0xC13e21B648A5Ee794902342038FF3aDAB66BE987"
SPARK_ORACLE = "0x8105f69D9C41644c6A0803fDA7D03Aa70996cFD2"

AAVE_POOL_ABI = json.loads('''[
  {"inputs":[],"name":"getReservesList","outputs":[{"internalType":"address[]","name":"","type":"address[]"}],"stateMutability":"view","type":"function"}
]''')

AAVE_ORACLE_ABI = json.loads('''[
  {"inputs":[{"internalType":"address","name":"asset","type":"address"}],"name":"getAssetPrice","outputs":[{"internalType":"uint256","name":"","type":"uint256"}],"stateMutability":"view","type":"function"},
  {"inputs":[{"internalType":"address","name":"asset","type":"address"}],"name":"getSourceOfAsset","outputs":[{"internalType":"address","name":"","type":"address"}],"stateMutability":"view","type":"function"}
]''')

try:
    spark = w3.eth.contract(address=Web3.to_checksum_address(SPARK_POOL), abi=AAVE_POOL_ABI)
    reserves = safe_call(spark, "getReservesList")
    if reserves:
        print(f"  Pool: {SPARK_POOL}")
        print(f"  Oracle: {SPARK_ORACLE}")
        print(f"  Reserves: {len(reserves)}")

        spark_oracle = w3.eth.contract(address=Web3.to_checksum_address(SPARK_ORACLE), abi=AAVE_ORACLE_ABI)

        for r in reserves:
            sym = get_sym(r)
            price = safe_call(spark_oracle, "getAssetPrice", Web3.to_checksum_address(r))
            source = safe_call(spark_oracle, "getSourceOfAsset", Web3.to_checksum_address(r))

            if price:
                usd = price / 1e8
                # Check for anomalies
                flag = ""
                if sym in ("USDC", "USDT", "DAI", "sDAI", "USDS", "sUSDS", "GHO"):
                    if usd > 5 or usd < 0.1:
                        flag = "*** STABLECOIN ANOMALY ***"
                elif "ETH" in sym or "stETH" in sym or "eETH" in sym:
                    if usd > 100000 or usd < 100:
                        flag = "*** ETH ANOMALY ***"
                elif "BTC" in sym:
                    if usd > 1000000 or usd < 10000:
                        flag = "*** BTC ANOMALY ***"

                print(f"  {sym}: ${usd:,.2f} | source: {source} {flag}")
except Exception as e:
    print(f"  Error: {e}")

# ============================================================
# 8. AAVE V3 LIDO INSTANCE — Separate deployment
# ============================================================
print("\n" + "="*80)
print("8. AAVE V3 LIDO INSTANCE")
print("="*80)

AAVE_LIDO_POOL = "0x4e033931ad43597d96D6bcc25c280717730B58B1"
AAVE_LIDO_ORACLE = "0x1233fa2a37C30Bb1F98B1D23c5bBD02Bb2D78D13"

try:
    lido_pool = w3.eth.contract(address=Web3.to_checksum_address(AAVE_LIDO_POOL), abi=AAVE_POOL_ABI)
    reserves = safe_call(lido_pool, "getReservesList")
    if reserves:
        print(f"  Pool: {AAVE_LIDO_POOL}")
        print(f"  Oracle: {AAVE_LIDO_ORACLE}")
        print(f"  Reserves: {len(reserves)}")

        lido_oracle = w3.eth.contract(address=Web3.to_checksum_address(AAVE_LIDO_ORACLE), abi=AAVE_ORACLE_ABI)

        for r in reserves:
            sym = get_sym(r)
            price = safe_call(lido_oracle, "getAssetPrice", Web3.to_checksum_address(r))
            if price:
                usd = price / 1e8
                flag = ""
                if sym in ("USDC", "USDT", "DAI", "USDS", "GHO"):
                    if usd > 5 or usd < 0.1:
                        flag = "*** STABLECOIN ANOMALY ***"
                elif "ETH" in sym or "stETH" in sym:
                    if usd > 100000 or usd < 100:
                        flag = "*** ETH ANOMALY ***"
                print(f"  {sym}: ${usd:,.2f} {flag}")
except Exception as e:
    print(f"  Error: {e}")

print("\n\n" + "="*80)
print("SCAN COMPLETE")
print("="*80)
