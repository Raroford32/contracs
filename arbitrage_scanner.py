#!/usr/bin/env python3
"""
Cross-protocol arbitrage and MEV opportunity scanner
Look for:
1. Price differences between DEXs/oracles
2. Liquidation opportunities in lending protocols
3. Stale prices that can be exploited
4. Token mechanics manipulation
"""
import json
import subprocess
import time

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

def get_balance(addr):
    result = rpc_call("eth_getBalance", [addr, "latest"])
    if result and 'result' in result:
        return int(result['result'], 16) / 1e18
    return 0

def get_storage(addr, slot):
    result = rpc_call("eth_getStorageAt", [addr, slot, "latest"])
    if result and 'result' in result:
        return result['result']
    return None

def get_source(addr):
    url = f"https://api.etherscan.io/v2/api?chainid=1&module=contract&action=getsourcecode&address={addr}&apikey={ETHERSCAN_API}"
    result = subprocess.run(["curl", "-s", url], capture_output=True, text=True)
    try:
        data = json.loads(result.stdout)
        if data.get("status") == "1" and data.get("result"):
            return data["result"][0]
    except:
        pass
    return None

print("=" * 80)
print("CROSS-PROTOCOL ARBITRAGE & MEV SCANNER")
print("=" * 80)

# Known DeFi protocols with potential arbitrage
KNOWN_PROTOCOLS = {
    # Uniswap V2 Router
    "uniswap_v2_router": "0x7a250d5630B4cF539739dF2C5dAcb4c659F2488D",
    # Uniswap V3 Router
    "uniswap_v3_router": "0xE592427A0AEce92De3Edee1F18E0157C05861564",
    # Sushiswap Router
    "sushiswap_router": "0xd9e1cE17f2641f24aE83637ab66a2cca9C378B9F",
    # Curve Pool Registry
    "curve_registry": "0x90E00ACe148ca3b23Ac1bC8C240C2a7Dd9c2d7f5",
    # Balancer Vault
    "balancer_vault": "0xBA12222222228d8Ba445958a75a0704d566BF2C8",
    # Aave V3 Pool
    "aave_v3_pool": "0x87870Bca3F3fD6335C3F4ce8392D69350B4fA4E2",
    # Compound V3 Comet (USDC)
    "compound_v3_usdc": "0xc3d688B66703497DAA19211EEdff47f25384cdc3",
}

# Check prices on different DEXs for common pairs
WETH = "0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2"
USDC = "0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48"
USDT = "0xdAC17F958D2ee523a2206206994597C13D831ec7"
DAI = "0x6B175474E89094C44Da98b954EesadFEA3C52E"

print("\n[1] CHECKING DEX PRICE DISCREPANCIES")
print("-" * 50)

# Get WETH/USDC price from Uniswap V2
# getAmountsOut(uint256,address[])
amount_in = hex(10**18)  # 1 WETH
path = WETH.lower()[2:].zfill(64) + USDC.lower()[2:].zfill(64)

# Call getAmountsOut on Uniswap V2 Router
# 0xd06ca61f = getAmountsOut(uint256,address[])
data = "0xd06ca61f" + amount_in[2:].zfill(64) + "0000000000000000000000000000000000000000000000000000000000000040" + "0000000000000000000000000000000000000000000000000000000000000002" + "000000000000000000000000" + WETH[2:].lower() + "000000000000000000000000" + USDC[2:].lower()

result = eth_call(KNOWN_PROTOCOLS["uniswap_v2_router"], data)
if result and result.get('result') and len(result['result']) > 130:
    try:
        # Parse amounts out
        hex_data = result['result'][2:]
        # Skip offset and array length, get second amount (USDC out)
        usdc_out = int(hex_data[192:256], 16)
        print(f"Uniswap V2: 1 WETH = {usdc_out / 1e6:.2f} USDC")
    except Exception as e:
        print(f"Uniswap V2 parse error: {e}")

# Check Sushiswap
result = eth_call(KNOWN_PROTOCOLS["sushiswap_router"], data)
if result and result.get('result') and len(result['result']) > 130:
    try:
        hex_data = result['result'][2:]
        usdc_out = int(hex_data[192:256], 16)
        print(f"Sushiswap: 1 WETH = {usdc_out / 1e6:.2f} USDC")
    except Exception as e:
        print(f"Sushiswap parse error: {e}")

print("\n[2] CHECKING LENDING PROTOCOL LIQUIDATIONS")
print("-" * 50)

# Check Aave V3 for liquidatable positions
# This would require knowing user addresses with positions
# For now, check if liquidation functions are accessible

# Aave V3 liquidationCall
# liquidationCall(address,address,address,uint256,bool)
# 0x00a718a9

# Check if liquidation is possible by looking at pool state
pool_selector = "0x7535d246"  # getReserveData(address)
weth_data = pool_selector + "000000000000000000000000" + WETH[2:].lower()

result = eth_call(KNOWN_PROTOCOLS["aave_v3_pool"], weth_data)
if result and result.get('result'):
    r = result['result']
    if len(r) > 66:
        print(f"Aave V3 WETH Reserve data retrieved ({len(r)} bytes)")
        # Parse reserve data - complex struct, just check it's active
        config = int(r[2:66], 16)
        print(f"  Config word: {hex(config)}")

print("\n[3] CHECKING FOR STALE ORACLE PRICES")
print("-" * 50)

# Common Chainlink price feeds
CHAINLINK_ETH_USD = "0x5f4eC3Df9cbd43714FE2740f5E3616155c5b8419"
CHAINLINK_BTC_USD = "0xF4030086522a5bEEa4988F8cA5B36dbC97BeE88c"

# latestRoundData()
latest_round_selector = "0xfeaf968c"

for name, feed in [("ETH/USD", CHAINLINK_ETH_USD), ("BTC/USD", CHAINLINK_BTC_USD)]:
    result = eth_call(feed, latest_round_selector)
    if result and result.get('result'):
        r = result['result'][2:]
        if len(r) >= 320:
            try:
                round_id = int(r[0:64], 16)
                answer = int(r[64:128], 16)
                started_at = int(r[128:192], 16)
                updated_at = int(r[192:256], 16)
                answered_in_round = int(r[256:320], 16)

                current_time = int(time.time())
                staleness = current_time - updated_at

                price = answer / 1e8
                print(f"{name}:")
                print(f"  Price: ${price:,.2f}")
                print(f"  Updated: {staleness} seconds ago")
                print(f"  Round: {round_id}")

                if staleness > 3600:
                    print(f"  [!] STALE - Over 1 hour old!")
            except Exception as e:
                print(f"{name}: Parse error - {e}")

print("\n[4] SCANNING CONTRACTS FOR ORACLE ARBITRAGE SURFACE")
print("-" * 50)

# Load high-value contracts and check which ones use oracles
with open("contracts.txt", "r") as f:
    contracts = [line.strip() for line in f if line.strip().startswith("0x")]

oracle_contracts = []

for i, addr in enumerate(contracts[:100]):  # Check top 100
    balance = get_balance(addr)
    if balance < 30:
        continue

    time.sleep(0.2)
    source_data = get_source(addr)
    if not source_data:
        continue

    src = source_data.get("SourceCode", "")
    name = source_data.get("ContractName", "Unknown")

    if not src:
        continue

    # Parse multi-file
    if src.startswith("{{"):
        try:
            src_json = json.loads(src[1:-1])
            sources = src_json.get("sources", {})
            src = "\n".join([v.get("content", "") for v in sources.values()])
        except:
            pass

    src_lower = src.lower()

    # Look for oracle usage patterns that could be exploited
    oracle_patterns = {
        "chainlink": "aggregatorv3interface" in src_lower or "latestrounddata" in src_lower,
        "uniswap_twap": "observe" in src_lower and "uniswap" in src_lower,
        "spot_price": "getreserves" in src_lower and ("/" in src or "div" in src_lower),
        "custom_oracle": "oracle" in src_lower and "getprice" in src_lower,
    }

    active_oracles = [k for k, v in oracle_patterns.items() if v]

    if active_oracles:
        # Check if it has value transfer functions
        has_value_transfer = any(p in src_lower for p in [
            "transfer(", ".call{value", "withdraw", "liquidat"
        ])

        if has_value_transfer:
            oracle_contracts.append({
                "address": addr,
                "name": name,
                "balance": balance,
                "oracles": active_oracles,
            })
            print(f"\n[!] {name} ({addr[:16]}...)")
            print(f"    Balance: {balance:.2f} ETH")
            print(f"    Oracles: {active_oracles}")

print("\n[5] CHECKING FOR PROFITABLE FLASH LOAN ROUTES")
print("-" * 50)

# Check flash loan availability from major protocols
# Aave V3 flash loan
# flashLoan(address,address[],uint256[],uint256[],address,bytes,uint16)

# Balancer flash loan - typically free
print("Balancer Vault flash loans: FREE (no fee)")

# Aave V3 flash loan premium
# FLASHLOAN_PREMIUM_TOTAL
premium_selector = "0x074b2e43"
result = eth_call(KNOWN_PROTOCOLS["aave_v3_pool"], premium_selector)
if result and result.get('result'):
    try:
        premium = int(result['result'], 16)
        print(f"Aave V3 flash loan fee: {premium/100}%")
    except:
        pass

print("\n[6] SUMMARY OF POTENTIAL OPPORTUNITIES")
print("-" * 50)

print(f"\nOracle-dependent contracts with value: {len(oracle_contracts)}")
for c in oracle_contracts[:10]:
    print(f"  - {c['name']}: {c['balance']:.1f} ETH ({c['oracles']})")

# Save findings
with open("arbitrage_findings.json", "w") as f:
    json.dump({
        "oracle_contracts": oracle_contracts,
    }, f, indent=2)

print("\n" + "=" * 80)
print("SCAN COMPLETE - Findings saved to arbitrage_findings.json")
print("=" * 80)
