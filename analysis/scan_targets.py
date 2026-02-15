#!/usr/bin/env python3
"""
DeFi Target Scanner
===================
Scans contracts from contracts.txt (lines 200-1568) to find high-value DeFi
targets that haven't been deeply analyzed yet.

Strategy:
1. First pass: batch check ETH + token balances via RPC (fast, no rate limit issues)
2. Filter to contracts with significant holdings (>$100K equivalent)
3. Second pass: check Etherscan for verified source + contract name (rate-limited)
4. Rank and output results
"""

import requests
import json
import time
import os
import sys
from datetime import datetime

# === Configuration ===
ETHERSCAN_KEY = "5UWN6DNT7UZCEJYNE3J6FCVAWH4QJW255K"
RPC_URL = "https://eth-mainnet.g.alchemy.com/v2/pLXdY7rYRY10SH_UTLBGH"
ETHERSCAN_API = "https://api.etherscan.io/v2/api"

CONTRACTS_FILE = "/home/user/contracs/contracts.txt"
OUTPUT_DIR = "/home/user/contracs/analysis"

# Token addresses
WETH = "0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2"
USDC = "0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48"
USDT = "0xdAC17F958D2ee523a2206206994597C13D831ec7"
DAI  = "0x6B175474E89094C44Da98b954EedeAC495271d0F"

# Approximate prices for value estimation (USD)
TOKEN_INFO = {
    WETH.lower(): {"symbol": "WETH", "decimals": 18, "price_usd": 2700},
    USDC.lower(): {"symbol": "USDC", "decimals": 6,  "price_usd": 1},
    USDT.lower(): {"symbol": "USDT", "decimals": 6,  "price_usd": 1},
    DAI.lower():  {"symbol": "DAI",  "decimals": 18, "price_usd": 1},
}

# Already deeply analyzed contracts (names from the user's list)
ALREADY_ANALYZED_NAMES = {
    "etherdelta", "idex", "curve", "tricrypto", "xsushi", "masterchef",
    "compound", "dydx", "solomargin", "parity", "tornado", "timelockcontroller",
    "optimism", "l1standardbridge", "aave", "collector", "cwbtc", "ctoken",
    "easyauction", "guildbank", "bentobox", "etherflip", "tristerslightminter",
    "metaswap", "frxethminter", "ydai", "ens", "l1_eth_bridge", "forwarding",
    "crowdsale", "ammwrapperwithpath", "tokenlon", "hydro", "ddex", "ethprime",
    "savingaccount", "r1exchange", "dex2", "pmm", "celerwallet", "ethertoken",
    "perpetualv1", "zora", "dutchexchange", "acedapp", "proceeds", "lientoken",
    "smoothyv1", "rsk", "depositboxeth", "multisig", "dolasavings", "liquity",
    "bamm", "layerzero", "oft", "vependle", "acceleratingdistributor",
    "cvxlockerv2", "ethenaminting", "hubpool", "collateralvault", "stakingrewards",
    "apecoinstaking", "fraxetherredemptionqueue", "scroll", "l1messenger",
    "stader", "swell", "rswexit", "akuauction", "stargateethvault",
    "stargatepoolnative", "stargate", "pros",
}

# Known non-DeFi / token-only contract names to skip
SKIP_NAMES = {
    "tether", "usdcoin", "shib", "pepe", "doge", "floki",
    "erc20", "tokencontract", "standardtoken",
}

# ============================================================
# RPC helpers
# ============================================================

def rpc_call(method, params, rpc_url=RPC_URL):
    """Make a single JSON-RPC call."""
    payload = {
        "jsonrpc": "2.0",
        "method": method,
        "params": params,
        "id": 1,
    }
    resp = requests.post(rpc_url, json=payload, timeout=30)
    resp.raise_for_status()
    data = resp.json()
    if "error" in data:
        return None
    return data.get("result")

def rpc_batch(calls, rpc_url=RPC_URL, batch_size=50):
    """Make batched JSON-RPC calls. Each call is (method, params)."""
    results = []
    for i in range(0, len(calls), batch_size):
        batch = []
        for j, (method, params) in enumerate(calls[i:i+batch_size]):
            batch.append({
                "jsonrpc": "2.0",
                "method": method,
                "params": params,
                "id": i + j,
            })
        try:
            resp = requests.post(rpc_url, json=batch, timeout=60)
            resp.raise_for_status()
            data = resp.json()
            # Sort by id to maintain order
            data.sort(key=lambda x: x.get("id", 0))
            for item in data:
                results.append(item.get("result"))
        except Exception as e:
            print(f"  RPC batch error at offset {i}: {e}", file=sys.stderr)
            results.extend([None] * len(batch))
        if i + batch_size < len(calls):
            time.sleep(0.1)  # small delay between batches
    return results

def get_eth_balances(addresses):
    """Get ETH balances for a list of addresses."""
    calls = [("eth_getBalance", [addr, "latest"]) for addr in addresses]
    results = rpc_batch(calls)
    balances = {}
    for addr, result in zip(addresses, results):
        if result:
            balances[addr.lower()] = int(result, 16) / 1e18
        else:
            balances[addr.lower()] = 0
    return balances

def get_erc20_balances(token_addr, holder_addresses):
    """Get ERC20 token balances using eth_call for balanceOf."""
    # balanceOf(address) = 0x70a08231 + address padded to 32 bytes
    calls = []
    for holder in holder_addresses:
        calldata = "0x70a08231" + holder[2:].lower().zfill(64)
        calls.append(("eth_call", [{"to": token_addr, "data": calldata}, "latest"]))
    results = rpc_batch(calls)
    balances = {}
    for holder, result in zip(holder_addresses, results):
        if result and result != "0x":
            try:
                balances[holder.lower()] = int(result, 16)
            except:
                balances[holder.lower()] = 0
        else:
            balances[holder.lower()] = 0
    return balances

def check_is_contract(addresses):
    """Check which addresses are contracts (have code)."""
    calls = [("eth_getCode", [addr, "latest"]) for addr in addresses]
    results = rpc_batch(calls)
    is_contract = {}
    for addr, result in zip(addresses, results):
        is_contract[addr.lower()] = result is not None and result != "0x" and len(result) > 4
    return is_contract

# ============================================================
# Etherscan helpers
# ============================================================

_last_etherscan_call = 0

def etherscan_get_source(address):
    """Get source code info from Etherscan. Rate-limited."""
    global _last_etherscan_call
    elapsed = time.time() - _last_etherscan_call
    if elapsed < 0.22:  # ~4.5 req/s to stay under 5/s
        time.sleep(0.22 - elapsed)
    
    params = {
        "chainid": "1",
        "module": "contract",
        "action": "getsourcecode",
        "address": address,
        "apikey": ETHERSCAN_KEY,
    }
    try:
        resp = requests.get(ETHERSCAN_API, params=params, timeout=15)
        resp.raise_for_status()
        data = resp.json()
        _last_etherscan_call = time.time()
        if data.get("status") == "1" and data.get("result"):
            result = data["result"][0]
            return {
                "name": result.get("ContractName", ""),
                "verified": bool(result.get("SourceCode", "")),
                "proxy": result.get("Proxy", "0") == "1",
                "implementation": result.get("Implementation", ""),
                "compiler": result.get("CompilerVersion", ""),
                "abi": result.get("ABI", ""),
            }
    except Exception as e:
        print(f"  Etherscan error for {address}: {e}", file=sys.stderr)
        _last_etherscan_call = time.time()
    return None

# ============================================================
# Analysis logic
# ============================================================

def is_already_analyzed(name):
    """Check if a contract name matches already-analyzed protocols."""
    name_lower = name.lower().replace(" ", "").replace("-", "").replace("_", "")
    for analyzed in ALREADY_ANALYZED_NAMES:
        if analyzed in name_lower or name_lower in analyzed:
            return True
    return False

def is_likely_defi(name, abi_str=""):
    """Heuristic: is this contract likely a DeFi protocol?"""
    name_lower = name.lower()
    
    # Skip known non-DeFi
    for skip in SKIP_NAMES:
        if skip in name_lower:
            return False, "token/skip"
    
    defi_keywords = {
        "vault": "vault/yield",
        "pool": "pool/dex",
        "swap": "dex",
        "exchange": "dex",
        "lending": "lending",
        "borrow": "lending",
        "collateral": "lending",
        "stake": "staking",
        "staking": "staking",
        "farm": "farming",
        "reward": "rewards",
        "bridge": "bridge",
        "router": "router",
        "aggregator": "aggregator",
        "oracle": "oracle",
        "liquidat": "liquidation",
        "margin": "margin",
        "perpetual": "perps",
        "option": "options",
        "auction": "auction",
        "governance": "governance",
        "treasury": "treasury",
        "strategy": "vault/strategy",
        "controller": "controller",
        "manager": "manager",
        "registry": "registry",
        "diamond": "diamond/proxy",
        "proxy": "proxy",
        "deposit": "deposit",
        "withdraw": "withdraw",
        "mint": "minting",
        "redeem": "redeem",
        "locker": "locker",
        "escrow": "escrow",
        "distributor": "distributor",
        "vesting": "vesting",
        "market": "market",
        "orderbook": "orderbook",
        "amm": "amm",
        "lp": "lp",
        "liquidity": "liquidity",
        "synth": "synthetics",
        "wrapper": "wrapper",
        "adapter": "adapter",
        "zap": "zap",
        "converter": "converter",
        "savings": "savings",
        "cdp": "cdp",
    }
    
    for keyword, category in defi_keywords.items():
        if keyword in name_lower:
            return True, category
    
    # Check ABI for DeFi-like function signatures
    if abi_str and abi_str != "Contract source code not verified":
        abi_lower = abi_str.lower()
        abi_signals = ["deposit", "withdraw", "stake", "borrow", "repay", 
                       "liquidat", "swap", "flashloan", "getreserve", "totalassets",
                       "pricepershare", "exchangerate", "getunderlying"]
        for sig in abi_signals:
            if sig in abi_lower:
                return True, f"abi-signal:{sig}"
    
    return False, "unknown"

def compute_total_value(eth_bal, token_bals):
    """Compute total USD value from balances."""
    total = eth_bal * 2700  # ETH price estimate
    for token_addr, raw_balance in token_bals.items():
        info = TOKEN_INFO.get(token_addr.lower(), {})
        if info and raw_balance > 0:
            decimals = info["decimals"]
            price = info["price_usd"]
            total += (raw_balance / (10 ** decimals)) * price
    return total

# ============================================================
# Main scanning pipeline
# ============================================================

def main():
    print(f"=== DeFi Target Scanner ===")
    print(f"Started: {datetime.now().isoformat()}")
    print()
    
    # 1. Load addresses (lines 200-1568, 0-indexed: 199-1567)
    with open(CONTRACTS_FILE, "r") as f:
        all_addresses = [line.strip().lower() for line in f if line.strip()]
    
    print(f"Total addresses in file: {len(all_addresses)}")
    
    # We scan lines 200-1568 (0-indexed: 199 to end)
    scan_addresses = all_addresses[199:]
    print(f"Addresses to scan (lines 200-{len(all_addresses)}): {len(scan_addresses)}")
    
    # Remove duplicates while preserving order
    seen = set()
    unique_addresses = []
    for addr in scan_addresses:
        if addr not in seen:
            seen.add(addr)
            unique_addresses.append(addr)
    print(f"Unique addresses: {len(unique_addresses)}")
    print()
    
    # 2. PASS 1: Check ETH balances (fast, via RPC batch)
    print("--- Pass 1: Checking ETH balances ---")
    eth_balances = get_eth_balances(unique_addresses)
    eth_rich = {addr: bal for addr, bal in eth_balances.items() if bal > 5}  # > 5 ETH
    print(f"  Addresses with >5 ETH: {len(eth_rich)}")
    
    # 3. PASS 2: Check WETH, USDC, USDT, DAI balances (via RPC batch)
    print("--- Pass 2: Checking token balances (WETH, USDC, USDT, DAI) ---")
    token_balances = {}  # addr -> {token -> raw_balance}
    
    for token_addr, info in TOKEN_INFO.items():
        print(f"  Checking {info['symbol']}...")
        bals = get_erc20_balances(token_addr, unique_addresses)
        for holder, raw_bal in bals.items():
            if raw_bal > 0:
                if holder not in token_balances:
                    token_balances[holder] = {}
                token_balances[holder][token_addr] = raw_bal
    
    # 4. Compute total value for each address
    print("--- Computing total value ---")
    address_values = {}
    for addr in unique_addresses:
        eth_bal = eth_balances.get(addr, 0)
        tok_bals = token_balances.get(addr, {})
        total_usd = compute_total_value(eth_bal, tok_bals)
        if total_usd > 0:
            address_values[addr] = {
                "eth": eth_bal,
                "tokens": tok_bals,
                "total_usd": total_usd,
            }
    
    # Filter to >$50K total value (cast wider net, then narrow)
    high_value = {addr: v for addr, v in address_values.items() if v["total_usd"] > 50000}
    print(f"  Addresses with >$50K total value: {len(high_value)}")
    
    # Sort by value descending
    ranked = sorted(high_value.items(), key=lambda x: x[1]["total_usd"], reverse=True)
    
    # 5. PASS 3: Etherscan source check for high-value addresses
    print(f"\n--- Pass 3: Checking Etherscan source for top {min(len(ranked), 300)} high-value addresses ---")
    
    results = []
    checked = 0
    for addr, value_info in ranked[:300]:
        checked += 1
        if checked % 20 == 0:
            print(f"  Checked {checked}/{min(len(ranked), 300)}...")
        
        source_info = etherscan_get_source(addr)
        if source_info is None:
            continue
        
        name = source_info["name"]
        verified = source_info["verified"]
        
        if not verified or not name:
            continue
        
        # Check if already analyzed
        already = is_already_analyzed(name)
        
        # Check if likely DeFi
        is_defi, category = is_likely_defi(name, source_info.get("abi", ""))
        
        # Build token balance summary
        tok_summary = {}
        for token_addr, raw_bal in value_info["tokens"].items():
            info = TOKEN_INFO[token_addr]
            human_bal = raw_bal / (10 ** info["decimals"])
            if human_bal > 0.01:
                tok_summary[info["symbol"]] = human_bal
        
        results.append({
            "address": addr,
            "name": name,
            "verified": verified,
            "proxy": source_info["proxy"],
            "implementation": source_info["implementation"],
            "eth_balance": value_info["eth"],
            "token_balances": tok_summary,
            "total_usd": value_info["total_usd"],
            "is_defi": is_defi,
            "defi_category": category,
            "already_analyzed": already,
            "compiler": source_info.get("compiler", ""),
        })
    
    print(f"  Total verified contracts checked: {len(results)}")
    
    # 6. Filter and rank results
    # Priority: DeFi + not analyzed + high value
    defi_targets = [r for r in results if r["is_defi"] and not r["already_analyzed"]]
    defi_targets.sort(key=lambda x: x["total_usd"], reverse=True)
    
    # Also collect high-value non-DeFi-classified (might be interesting custom contracts)
    high_value_unclassified = [r for r in results 
                                if not r["is_defi"] and not r["already_analyzed"] 
                                and r["total_usd"] > 500000]
    high_value_unclassified.sort(key=lambda x: x["total_usd"], reverse=True)
    
    # 7. Output results
    print(f"\n{'='*80}")
    print(f"RESULTS SUMMARY")
    print(f"{'='*80}")
    print(f"Total scanned: {len(unique_addresses)}")
    print(f"High value (>$50K): {len(high_value)}")
    print(f"Verified + source checked: {len(results)}")
    print(f"DeFi targets (not analyzed): {len(defi_targets)}")
    print(f"High-value unclassified (>$500K): {len(high_value_unclassified)}")
    
    # Write detailed results
    output_file = os.path.join(OUTPUT_DIR, "target_scan_results.md")
    with open(output_file, "w") as f:
        f.write(f"# DeFi Target Scan Results\n")
        f.write(f"Generated: {datetime.now().isoformat()}\n")
        f.write(f"Scan range: lines 200-{len(all_addresses)} of contracts.txt\n")
        f.write(f"Unique addresses scanned: {len(unique_addresses)}\n\n")
        
        f.write(f"## Top DeFi Targets (Not Previously Analyzed)\n\n")
        f.write(f"| # | Address | Name | Category | ETH | WETH | USDC | USDT | DAI | Total USD | Proxy |\n")
        f.write(f"|---|---------|------|----------|-----|------|------|------|-----|-----------|-------|\n")
        
        for i, r in enumerate(defi_targets[:100], 1):
            eth_str = f"{r['eth_balance']:.1f}" if r['eth_balance'] > 0.1 else "-"
            weth_str = f"{r['token_balances'].get('WETH', 0):.1f}" if r['token_balances'].get('WETH', 0) > 0.1 else "-"
            usdc_str = f"{r['token_balances'].get('USDC', 0):,.0f}" if r['token_balances'].get('USDC', 0) > 1 else "-"
            usdt_str = f"{r['token_balances'].get('USDT', 0):,.0f}" if r['token_balances'].get('USDT', 0) > 1 else "-"
            dai_str = f"{r['token_balances'].get('DAI', 0):,.0f}" if r['token_balances'].get('DAI', 0) > 1 else "-"
            total_str = f"${r['total_usd']:,.0f}"
            proxy_str = "Yes" if r['proxy'] else "No"
            
            f.write(f"| {i} | `{r['address']}` | {r['name']} | {r['defi_category']} | {eth_str} | {weth_str} | {usdc_str} | {usdt_str} | {dai_str} | {total_str} | {proxy_str} |\n")
        
        f.write(f"\n## High-Value Unclassified Contracts (>$500K, Not Analyzed)\n\n")
        f.write(f"| # | Address | Name | ETH | WETH | USDC | USDT | DAI | Total USD | Proxy |\n")
        f.write(f"|---|---------|------|-----|------|------|------|-----|-----------|-------|\n")
        
        for i, r in enumerate(high_value_unclassified[:50], 1):
            eth_str = f"{r['eth_balance']:.1f}" if r['eth_balance'] > 0.1 else "-"
            weth_str = f"{r['token_balances'].get('WETH', 0):.1f}" if r['token_balances'].get('WETH', 0) > 0.1 else "-"
            usdc_str = f"{r['token_balances'].get('USDC', 0):,.0f}" if r['token_balances'].get('USDC', 0) > 1 else "-"
            usdt_str = f"{r['token_balances'].get('USDT', 0):,.0f}" if r['token_balances'].get('USDT', 0) > 1 else "-"
            dai_str = f"{r['token_balances'].get('DAI', 0):,.0f}" if r['token_balances'].get('DAI', 0) > 1 else "-"
            total_str = f"${r['total_usd']:,.0f}"
            proxy_str = "Yes" if r['proxy'] else "No"
            
            f.write(f"| {i} | `{r['address']}` | {r['name']} | {eth_str} | {weth_str} | {usdc_str} | {usdt_str} | {dai_str} | {total_str} | {proxy_str} |\n")
        
        # Write all results as appendix
        f.write(f"\n## All Verified High-Value Contracts (Full List)\n\n")
        all_sorted = sorted(results, key=lambda x: x["total_usd"], reverse=True)
        for i, r in enumerate(all_sorted, 1):
            status = ""
            if r["already_analyzed"]:
                status = " [ALREADY ANALYZED]"
            elif r["is_defi"]:
                status = f" [{r['defi_category'].upper()}]"
            f.write(f"{i}. `{r['address']}` - **{r['name']}** - ${r['total_usd']:,.0f}{status}\n")
    
    print(f"\nDetailed results written to: {output_file}")
    
    # Write JSON for programmatic use
    json_file = os.path.join(OUTPUT_DIR, "target_scan_results.json")
    with open(json_file, "w") as f:
        json.dump({
            "scan_time": datetime.now().isoformat(),
            "total_scanned": len(unique_addresses),
            "high_value_count": len(high_value),
            "defi_targets": defi_targets[:100],
            "unclassified_high_value": high_value_unclassified[:50],
            "all_results": all_sorted,
        }, f, indent=2, default=str)
    
    print(f"JSON results written to: {json_file}")
    
    # Print top 30 to console
    print(f"\n{'='*80}")
    print(f"TOP 30 DeFi TARGETS (not previously analyzed)")
    print(f"{'='*80}")
    for i, r in enumerate(defi_targets[:30], 1):
        tokens_str = ", ".join(f"{k}: {v:,.1f}" for k, v in r['token_balances'].items() if v > 0.1)
        eth_str = f"ETH: {r['eth_balance']:.1f}" if r['eth_balance'] > 0.1 else ""
        bal_parts = [s for s in [eth_str, tokens_str] if s]
        bal_str = " | ".join(bal_parts) if bal_parts else "minimal"
        proxy_str = " [PROXY]" if r['proxy'] else ""
        impl_str = f" -> {r['implementation'][:10]}..." if r['implementation'] else ""
        print(f"  {i:2d}. {r['address']} | {r['name']}{proxy_str}{impl_str}")
        print(f"      Category: {r['defi_category']} | Value: ${r['total_usd']:,.0f} | {bal_str}")
    
    if high_value_unclassified:
        print(f"\n{'='*80}")
        print(f"TOP UNCLASSIFIED HIGH-VALUE (>$500K, may be custom DeFi)")
        print(f"{'='*80}")
        for i, r in enumerate(high_value_unclassified[:15], 1):
            tokens_str = ", ".join(f"{k}: {v:,.1f}" for k, v in r['token_balances'].items() if v > 0.1)
            eth_str = f"ETH: {r['eth_balance']:.1f}" if r['eth_balance'] > 0.1 else ""
            bal_parts = [s for s in [eth_str, tokens_str] if s]
            bal_str = " | ".join(bal_parts) if bal_parts else "minimal"
            proxy_str = " [PROXY]" if r['proxy'] else ""
            print(f"  {i:2d}. {r['address']} | {r['name']}{proxy_str}")
            print(f"      Value: ${r['total_usd']:,.0f} | {bal_str}")
    
    print(f"\nDone. {datetime.now().isoformat()}")


if __name__ == "__main__":
    main()
