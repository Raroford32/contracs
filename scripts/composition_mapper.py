#!/usr/bin/env python3
"""
Cross-Protocol Composition Attack Surface Mapper — Base Chain

Maps the interconnections between DeFi protocols where shared state,
tokens, or dependencies create novel multi-vector attack surfaces.

Focus: MetaMorpho vaults, LRT tokens, DEX LP tokens used as collateral,
governance dual-roles, cross-protocol liquidation cascades.
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
  {"inputs":[{"internalType":"address","name":"","type":"address"}],"name":"balanceOf","outputs":[{"internalType":"uint256","name":"","type":"uint256"}],"stateMutability":"view","type":"function"},
  {"inputs":[],"name":"totalSupply","outputs":[{"internalType":"uint256","name":"","type":"uint256"}],"stateMutability":"view","type":"function"}
]''')

VAULT_ABI = json.loads('''[
  {"inputs":[],"name":"asset","outputs":[{"internalType":"address","name":"","type":"address"}],"stateMutability":"view","type":"function"},
  {"inputs":[],"name":"totalAssets","outputs":[{"internalType":"uint256","name":"","type":"uint256"}],"stateMutability":"view","type":"function"},
  {"inputs":[],"name":"totalSupply","outputs":[{"internalType":"uint256","name":"","type":"uint256"}],"stateMutability":"view","type":"function"},
  {"inputs":[{"internalType":"uint256","name":"shares","type":"uint256"}],
   "name":"convertToAssets","outputs":[{"internalType":"uint256","name":"","type":"uint256"}],"stateMutability":"view","type":"function"},
  {"inputs":[{"internalType":"uint256","name":"assets","type":"uint256"}],
   "name":"convertToShares","outputs":[{"internalType":"uint256","name":"","type":"uint256"}],"stateMutability":"view","type":"function"},
  {"inputs":[],"name":"symbol","outputs":[{"internalType":"string","name":"","type":"string"}],"stateMutability":"view","type":"function"},
  {"inputs":[],"name":"name","outputs":[{"internalType":"string","name":"","type":"string"}],"stateMutability":"view","type":"function"},
  {"inputs":[],"name":"decimals","outputs":[{"internalType":"uint8","name":"","type":"uint8"}],"stateMutability":"view","type":"function"}
]''')

# MetaMorpho specific
METAMORPHO_ABI = json.loads('''[
  {"inputs":[],"name":"asset","outputs":[{"internalType":"address","name":"","type":"address"}],"stateMutability":"view","type":"function"},
  {"inputs":[],"name":"totalAssets","outputs":[{"internalType":"uint256","name":"","type":"uint256"}],"stateMutability":"view","type":"function"},
  {"inputs":[],"name":"totalSupply","outputs":[{"internalType":"uint256","name":"","type":"uint256"}],"stateMutability":"view","type":"function"},
  {"inputs":[],"name":"curator","outputs":[{"internalType":"address","name":"","type":"address"}],"stateMutability":"view","type":"function"},
  {"inputs":[],"name":"guardian","outputs":[{"internalType":"address","name":"","type":"address"}],"stateMutability":"view","type":"function"},
  {"inputs":[],"name":"owner","outputs":[{"internalType":"address","name":"","type":"address"}],"stateMutability":"view","type":"function"},
  {"inputs":[],"name":"fee","outputs":[{"internalType":"uint96","name":"","type":"uint96"}],"stateMutability":"view","type":"function"},
  {"inputs":[],"name":"feeRecipient","outputs":[{"internalType":"address","name":"","type":"address"}],"stateMutability":"view","type":"function"},
  {"inputs":[],"name":"supplyQueueLength","outputs":[{"internalType":"uint256","name":"","type":"uint256"}],"stateMutability":"view","type":"function"},
  {"inputs":[],"name":"withdrawQueueLength","outputs":[{"internalType":"uint256","name":"","type":"uint256"}],"stateMutability":"view","type":"function"},
  {"inputs":[{"internalType":"uint256","name":"","type":"uint256"}],"name":"supplyQueue","outputs":[{"internalType":"Id","name":"","type":"bytes32"}],"stateMutability":"view","type":"function"},
  {"inputs":[{"internalType":"uint256","name":"","type":"uint256"}],"name":"withdrawQueue","outputs":[{"internalType":"Id","name":"","type":"bytes32"}],"stateMutability":"view","type":"function"},
  {"inputs":[{"internalType":"Id","name":"","type":"bytes32"}],"name":"config","outputs":[{"internalType":"uint184","name":"cap","type":"uint184"},{"internalType":"bool","name":"enabled","type":"bool"},{"internalType":"uint64","name":"removableAt","type":"uint64"}],"stateMutability":"view","type":"function"},
  {"inputs":[],"name":"timelock","outputs":[{"internalType":"uint256","name":"","type":"uint256"}],"stateMutability":"view","type":"function"},
  {"inputs":[],"name":"symbol","outputs":[{"internalType":"string","name":"","type":"string"}],"stateMutability":"view","type":"function"},
  {"inputs":[],"name":"name","outputs":[{"internalType":"string","name":"","type":"string"}],"stateMutability":"view","type":"function"}
]''')

MORPHO_ABI = json.loads('''[
  {"inputs":[{"internalType":"Id","name":"id","type":"bytes32"}],"name":"idToMarketParams","outputs":[{"components":[{"internalType":"address","name":"loanToken","type":"address"},{"internalType":"address","name":"collateralToken","type":"address"},{"internalType":"address","name":"oracle","type":"address"},{"internalType":"address","name":"irm","type":"address"},{"internalType":"uint256","name":"lltv","type":"uint256"}],"internalType":"struct MarketParams","name":"","type":"tuple"}],"stateMutability":"view","type":"function"},
  {"inputs":[{"internalType":"Id","name":"id","type":"bytes32"}],"name":"market","outputs":[{"internalType":"uint128","name":"totalSupplyAssets","type":"uint128"},{"internalType":"uint128","name":"totalSupplyShares","type":"uint128"},{"internalType":"uint128","name":"totalBorrowAssets","type":"uint128"},{"internalType":"uint128","name":"totalBorrowShares","type":"uint128"},{"internalType":"uint128","name":"lastUpdate","type":"uint128"},{"internalType":"uint128","name":"fee","type":"uint128"}],"stateMutability":"view","type":"function"}
]''')

MORPHO_ORACLE_ABI = json.loads('''[
  {"inputs":[],"name":"price","outputs":[{"internalType":"uint256","name":"","type":"uint256"}],"stateMutability":"view","type":"function"},
  {"inputs":[],"name":"BASE_VAULT","outputs":[{"internalType":"contract IERC4626","name":"","type":"address"}],"stateMutability":"view","type":"function"},
  {"inputs":[],"name":"QUOTE_VAULT","outputs":[{"internalType":"contract IERC4626","name":"","type":"address"}],"stateMutability":"view","type":"function"},
  {"inputs":[],"name":"BASE_FEED_1","outputs":[{"internalType":"contract AggregatorV3Interface","name":"","type":"address"}],"stateMutability":"view","type":"function"},
  {"inputs":[],"name":"BASE_FEED_2","outputs":[{"internalType":"contract AggregatorV3Interface","name":"","type":"address"}],"stateMutability":"view","type":"function"},
  {"inputs":[],"name":"QUOTE_FEED_1","outputs":[{"internalType":"contract AggregatorV3Interface","name":"","type":"address"}],"stateMutability":"view","type":"function"},
  {"inputs":[],"name":"QUOTE_FEED_2","outputs":[{"internalType":"contract AggregatorV3Interface","name":"","type":"address"}],"stateMutability":"view","type":"function"},
  {"inputs":[],"name":"SCALE_FACTOR","outputs":[{"internalType":"uint256","name":"","type":"uint256"}],"stateMutability":"view","type":"function"}
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

def get_dec(addr):
    c = w3.eth.contract(address=Web3.to_checksum_address(addr), abi=ERC20_ABI)
    return safe_call(c, "decimals") or 18

MORPHO_BASE = "0xBBBBBbbBBb9cC5e90e3b3Af64bdAF62C37EEFFCb"
morpho = w3.eth.contract(address=Web3.to_checksum_address(MORPHO_BASE), abi=MORPHO_ABI)

# ============================================================================
# 1. FIND METAMORPHO VAULTS ON BASE
# ============================================================================
# Known MetaMorpho vault factory on Base
# Look for ERC-4626 vaults that are themselves used as collateral in Morpho markets
# This creates a reflexive loop: Vault -> Morpho market -> Vault token as collateral

# Known large MetaMorpho vaults on Base (from ecosystem data)
KNOWN_VAULTS = {
    # Gauntlet USDC Vault (one of the largest)
    "0xc1256Ae5FF1cf2719D4937adb3bbCCab2E00A2Ca": "Gauntlet USDC Core",
    # Moonwell Flagship USDC
    "0xc1256Ae5FF1cf2719D4937adb3bbCCab2E00A2Ca": "Moonwell Flagship USDC",
    # Steakhouse USDC
    "0xBEEF01735c132Ada46AA9aA4c54623cAA92A64CB": "Steakhouse USDC",
    # Re7 WETH
    "0xa0E430870c4604CcfC7B38CA7845B1FF653D0ff1": "Re7 WETH",
    # Gauntlet WETH
    "0x2371e134e3455e0593363cBF89d3b6cf53740618": "Gauntlet WETH Core",
    # Moonwell Flagship ETH
    "0xa0E430870c4604CcfC7B38CA7845B1FF653D0ff1": "Moonwell Flagship ETH",
    # Steakhouse WETH
    "0x9419f6a0bC4Fd3C6F077ecD227B70Bc2eD651821": "Steakhouse WETH",
    # Various cbBTC, EURC vaults
    "0x543257eF2161176D7C8cD90BA65C2d4CaEF5a796": "Gauntlet cbBTC Core",
    "0x616a4E1db8AaDcF3Be0FE45b3D4F12b7473401aB": "Moonwell Flagship EURC",
}

print("="*100)
print("1. METAMORPHO VAULT ANALYSIS — COMPOSITION SURFACE")
print("="*100)

vault_data = {}
for addr, label in KNOWN_VAULTS.items():
    vc = w3.eth.contract(address=Web3.to_checksum_address(addr), abi=METAMORPHO_ABI)
    sym = safe_call(vc, "symbol") or "?"
    name = safe_call(vc, "name") or "?"
    asset = safe_call(vc, "asset")
    total_assets = safe_call(vc, "totalAssets") or 0
    total_supply = safe_call(vc, "totalSupply") or 0
    curator = safe_call(vc, "curator")
    owner = safe_call(vc, "owner")
    fee = safe_call(vc, "fee")
    timelock = safe_call(vc, "timelock")
    sq_len = safe_call(vc, "supplyQueueLength") or 0
    wq_len = safe_call(vc, "withdrawQueueLength") or 0

    if not asset:
        print(f"\n  [{label}] at {addr}: NOT A METAMORPHO VAULT (no asset)")
        continue

    asset_sym = get_sym(asset)
    asset_dec = get_dec(asset)
    ta_human = total_assets / (10 ** asset_dec) if total_assets else 0
    rate = total_assets / total_supply if total_supply > 0 else 0

    vault_data[addr] = {
        "sym": sym, "name": name, "asset": asset, "asset_sym": asset_sym,
        "total_assets": total_assets, "total_supply": total_supply,
        "ta_human": ta_human, "rate": rate, "curator": curator,
        "supply_queue_len": sq_len, "withdraw_queue_len": wq_len,
        "timelock": timelock,
    }

    print(f"\n  {sym} ({name})")
    print(f"    Asset: {asset_sym} ({asset})")
    print(f"    Total Assets: {ta_human:,.2f} {asset_sym}")
    print(f"    Total Supply: {total_supply}")
    print(f"    Exchange Rate: {rate:.8f}")
    print(f"    Curator: {curator}")
    print(f"    Owner: {owner}")
    print(f"    Fee: {fee}")
    print(f"    Timelock: {timelock}s")
    print(f"    Supply Queue Length: {sq_len}")
    print(f"    Withdraw Queue Length: {wq_len}")

    # Map supply queue — which Morpho Blue markets does this vault allocate to?
    print(f"    Supply Queue (markets this vault lends into):")
    for i in range(min(sq_len, 10)):
        mid = safe_call(vc, "supplyQueue", i)
        if mid:
            params = safe_call(morpho, "idToMarketParams", mid)
            market_data = safe_call(morpho, "market", mid)
            config = safe_call(vc, "config", mid)

            if params and market_data:
                coll_sym = get_sym(params[1])
                oracle_addr = params[2]
                lltv = params[4]

                supply = market_data[0]
                borrow = market_data[2]
                loan_dec = get_dec(params[0])
                supply_h = supply / (10 ** loan_dec)
                borrow_h = borrow / (10 ** loan_dec)

                # Check if the COLLATERAL in this market is itself a vault token
                coll_is_vault = False
                coll_vault_asset = None
                cv = w3.eth.contract(address=Web3.to_checksum_address(params[1]), abi=VAULT_ABI)
                coll_vault_asset_addr = safe_call(cv, "asset")
                if coll_vault_asset_addr:
                    coll_is_vault = True
                    coll_vault_asset = get_sym(coll_vault_asset_addr)

                # Check oracle for BASE_VAULT (reads vault exchange rate)
                oc = w3.eth.contract(address=Web3.to_checksum_address(oracle_addr), abi=MORPHO_ORACLE_ABI)
                base_vault = safe_call(oc, "BASE_VAULT")
                quote_vault = safe_call(oc, "QUOTE_VAULT")

                cap = config[0] if config else 0
                enabled = config[1] if config else False

                flags = []
                if coll_is_vault:
                    flags.append(f"COLLATERAL_IS_VAULT(asset={coll_vault_asset})")
                if base_vault and base_vault != ZERO:
                    flags.append(f"ORACLE_READS_BASE_VAULT({base_vault[:10]}...)")
                if quote_vault and quote_vault != ZERO:
                    flags.append(f"ORACLE_READS_QUOTE_VAULT({quote_vault[:10]}...)")

                flag_str = " | ".join(flags) if flags else "clean"

                print(f"      [{i}] Coll: {coll_sym} | LLTV: {lltv/1e18:.0%} | Supply: {supply_h:,.0f} | Borrow: {borrow_h:,.0f} | Cap: {cap/(10**loan_dec) if cap else 0:,.0f}")
                print(f"           Oracle: {oracle_addr[:14]}... | Flags: [{flag_str}]")

                # COMPOSITION CHECK: Is the collateral token ANOTHER MetaMorpho vault?
                if coll_is_vault:
                    print(f"           >>> COMPOSITION: Vault lends into market where collateral is ANOTHER VAULT")
                    print(f"           >>> Collateral vault asset: {coll_vault_asset}")
                    # Check if the collateral vault is one of our known vaults
                    if params[1].lower() in [a.lower() for a in KNOWN_VAULTS.keys()]:
                        print(f"           >>> !!! REFLEXIVE: Vault -> Market -> Vault (same ecosystem) !!!")

    # Withdraw queue
    print(f"    Withdraw Queue (order of market withdrawal):")
    for i in range(min(wq_len, 10)):
        mid = safe_call(vc, "withdrawQueue", i)
        if mid:
            params = safe_call(morpho, "idToMarketParams", mid)
            if params:
                coll_sym = get_sym(params[1])
                print(f"      [{i}] Coll: {coll_sym}")

# ============================================================================
# 2. LRT TOKENS — CROSS-PROTOCOL COLLATERAL MAPPING
# ============================================================================
print(f"\n\n{'='*100}")
print("2. LRT/LST TOKEN CROSS-PROTOCOL EXPOSURE")
print("="*100)

# Known LRT/LST tokens on Base
LRT_TOKENS = {
    "0xc1CBa3fCea344f92D9239c08C0568f6F2F0ee452": "wstETH",
    "0x2Ae3F1Ec7F1F5012CFEab0185bfc7aa3cf0DEc22": "cbETH",
    "0x04C0599Ae5A44757c0af6F9eC3b93da8976c150A": "weETH",
    "0x2416092f143378750bb29b79eD961ab195CcEea5": "ezETH",
    "0xEDfa23602D0EC14714057867A78d01e94176BEA0": "wrsETH",
    "0xB6fe221Fe9EeF5aBa221c348bA20A1Bf5e73624c": "rETH",
    "0xcbB7C0000aB88B473b1f5aFd9ef808440eed33Bf": "cbBTC",
    "0xecAc9C5F704e954931349Da37F60E39f515c11c1": "LBTC",
}

# Where are these tokens deposited? Check balances in key protocols
PROTOCOL_CONTRACTS = {
    "Morpho Blue": MORPHO_BASE,
    "Aave V3 Pool": "0xA238Dd80C259a72e81d7e4664a9801593F98d1c5",
    "Moonwell WETH": "0x628ff693426583D9a7FB391E54366292F509D457",
    "Moonwell cbETH": "0x3bf93770f2d4a794c3d9EBEfBAeBAE2a8f09A5E5",
    "Moonwell wstETH": "0x627Fe393Bc6EdDA28e99AE648fD6fF362514304b",
}

for token_addr, token_sym in LRT_TOKENS.items():
    tc = w3.eth.contract(address=Web3.to_checksum_address(token_addr), abi=ERC20_ABI)
    total_supply = safe_call(tc, "totalSupply") or 0
    dec = get_dec(token_addr)

    # Is this token itself an ERC-4626 vault?
    vc = w3.eth.contract(address=Web3.to_checksum_address(token_addr), abi=VAULT_ABI)
    vault_asset = safe_call(vc, "asset")
    is_vault = vault_asset is not None

    print(f"\n  {token_sym} ({token_addr[:14]}...)")
    print(f"    Total Supply: {total_supply / (10**dec):,.2f}")
    if is_vault:
        va_sym = get_sym(vault_asset)
        vault_ta = safe_call(vc, "totalAssets") or 0
        vault_ts = safe_call(vc, "totalSupply") or 1
        rate = vault_ta / vault_ts if vault_ts > 0 else 0
        print(f"    IS ERC-4626 VAULT: asset={va_sym}, rate={rate:.6f}")
        print(f"    >>> Exchange rate is LIVE and MANIPULABLE via donation")

    # Check balances in various protocols
    print(f"    Protocol exposure:")
    for proto_name, proto_addr in PROTOCOL_CONTRACTS.items():
        bal = safe_call(tc, "balanceOf", Web3.to_checksum_address(proto_addr))
        if bal and bal > 0:
            bal_human = bal / (10**dec)
            print(f"      {proto_name}: {bal_human:,.4f} {token_sym}")

# ============================================================================
# 3. GOVERNANCE TOKEN DUAL-ROLE ANALYSIS
# ============================================================================
print(f"\n\n{'='*100}")
print("3. GOVERNANCE TOKEN DUAL-ROLE ANALYSIS")
print("="*100)

GOV_TOKENS = {
    "0x940181a94A35A4569E4529A3CDfB74e38FD98631": ("AERO", "Aerodrome governance + LP incentives"),
    "0xA88594D404727625A9437C3f886C7643872296AE": ("WELL", "Moonwell governance"),
    "0xBAa5CC21fd487B8Fcc2F632f3F4E8D37262a0842": ("MORPHO", "Morpho governance"),
}

for addr, (sym, role) in GOV_TOKENS.items():
    tc = w3.eth.contract(address=Web3.to_checksum_address(addr), abi=ERC20_ABI)
    total_supply = safe_call(tc, "totalSupply") or 0
    dec = get_dec(addr)

    print(f"\n  {sym}: {role}")
    print(f"    Total Supply: {total_supply / (10**dec):,.0f}")

    # Where is this token used as collateral?
    # Check if it's in Moonwell
    for mtoken_addr, mtoken_name in [
        ("0xdC7810B47eAAb250De623F0eE07764afa5F71ED1", "mWELL"),
        ("0x73902f619CEB9B31FD8EFecf435CbDf89E369Ba6", "mAERO"),
        ("0x6308204872BdB7432dF97b04B42443c714904F3E", "mMORPHO"),
    ]:
        mt = w3.eth.contract(address=Web3.to_checksum_address(mtoken_addr), abi=ERC20_ABI)
        bal = safe_call(tc, "balanceOf", Web3.to_checksum_address(mtoken_addr))
        mts = safe_call(mt, "totalSupply") or 0
        if bal and bal > 0:
            bal_human = bal / (10**dec)
            print(f"    As collateral in {mtoken_name}: {bal_human:,.0f} {sym}")
            print(f"      >>> DUAL ROLE: governance power + collateral value")
            print(f"      >>> Can flash-borrow {sym}, use as collateral, borrow stables?")

# ============================================================================
# 4. KEY COMPOSITION QUESTION: VAULT-ON-VAULT REFLEXIVITY
# ============================================================================
print(f"\n\n{'='*100}")
print("4. VAULT-ON-VAULT REFLEXIVITY CHECK")
print("="*100)
print("""
Key question: In Morpho Blue, can a MetaMorpho vault token be used as COLLATERAL
in a market that the SAME vault lends into?

If yes: Deposit into vault -> get vault tokens -> post as collateral in market
-> vault automatically lends your deposit into that market -> borrow against it
-> REFLEXIVE LOOP that amplifies leverage beyond intended LLTV

This is the novel composition vector:
1. Deposit X into MetaMorpho vault, get X vault tokens
2. Post vault tokens as collateral in Morpho market (where vault lends)
3. Borrow from that market — vault's deposit backs the borrowing
4. Deposit borrowed amount back into vault — get more vault tokens
5. Repeat — leverage amplification beyond what LLTV allows

The economic question: Does the vault's share price correctly reflect
the risk of its own token being used as collateral in markets it lends into?
""")

print("\nDone. See composition analysis above.")
