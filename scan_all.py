#!/usr/bin/env python3
"""Batch scan all contracts: balance check via RPC, then name lookup via Etherscan."""
import json
import time
import sys
import os
import urllib.request
import urllib.error

RPC_URL = "https://eth-mainnet.g.alchemy.com/v2/pLXdY7rYRY10SH_UTLBGH"
ETHERSCAN_KEY = "5UWN6DNT7UZCEJYNE3J6FCVAWH4QJW255K"
ETHERSCAN_URL = "https://api.etherscan.io/v2/api"

def read_addresses(path):
    addrs = []
    with open(path) as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            # Extract hex address (handle numbered lines like "1→0x...")
            parts = line.split("→")
            addr = parts[-1].strip() if "→" in line else line.strip()
            if addr.startswith("0x") and len(addr) == 42:
                addrs.append(addr)
    return addrs

def batch_balances(addrs, batch_size=500):
    """Fetch ETH balances via JSON-RPC batch calls."""
    results = {}
    for i in range(0, len(addrs), batch_size):
        batch = addrs[i:i+batch_size]
        payload = []
        for j, addr in enumerate(batch):
            payload.append({
                "jsonrpc": "2.0",
                "method": "eth_getBalance",
                "params": [addr, "latest"],
                "id": i + j
            })
        data = json.dumps(payload).encode()
        req = urllib.request.Request(RPC_URL, data=data, headers={"Content-Type": "application/json"})
        try:
            resp = urllib.request.urlopen(req, timeout=30)
            body = json.loads(resp.read())
            for item in body:
                idx = item["id"]
                if "result" in item:
                    wei = int(item["result"], 16)
                    results[addrs[idx]] = wei / 1e18
                else:
                    results[addrs[idx]] = -1
        except Exception as e:
            print(f"  RPC batch error at offset {i}: {e}", file=sys.stderr)
            for addr in batch:
                results.setdefault(addr, -1)
        if i + batch_size < len(addrs):
            time.sleep(0.5)
    return results

def get_contract_name(addr):
    """Fetch contract name via Etherscan getsourcecode."""
    url = f"{ETHERSCAN_URL}?chainid=1&module=contract&action=getsourcecode&address={addr}&apikey={ETHERSCAN_KEY}"
    try:
        req = urllib.request.Request(url)
        resp = urllib.request.urlopen(req, timeout=15)
        data = json.loads(resp.read())
        if data.get("status") == "1" and data.get("result"):
            r = data["result"][0]
            name = r.get("ContractName", "")
            proxy = r.get("Proxy", "0")
            impl = r.get("Implementation", "")
            is_proxy = proxy == "1"
            has_source = bool(name and name != "")
            return name if has_source else "UNVERIFIED", is_proxy, impl
    except Exception as e:
        return "ERROR", False, ""
    return "UNVERIFIED", False, ""

def get_code_size(addr):
    """Check if address has code (is a contract)."""
    payload = json.dumps({
        "jsonrpc": "2.0",
        "method": "eth_getCode",
        "params": [addr, "latest"],
        "id": 1
    }).encode()
    req = urllib.request.Request(RPC_URL, data=payload, headers={"Content-Type": "application/json"})
    try:
        resp = urllib.request.urlopen(req, timeout=10)
        data = json.loads(resp.read())
        code = data.get("result", "0x")
        return (len(code) - 2) // 2  # bytes of code
    except:
        return -1

def main():
    addrs = read_addresses("/home/user/contracs/contracts.txt")
    print(f"Total addresses: {len(addrs)}")

    # Step 1: Batch fetch all balances
    print("Fetching balances...")
    balances = batch_balances(addrs)

    # Sort by balance descending
    sorted_addrs = sorted(addrs, key=lambda a: balances.get(a, 0), reverse=True)

    # Step 2: Get contract names for top 300 by balance (rate limited)
    print("\nFetching contract names for top-balance addresses...")
    names = {}
    proxy_info = {}
    count = 0
    for addr in sorted_addrs:
        bal = balances.get(addr, 0)
        if bal <= 0.01 and count >= 100:
            break  # skip low-balance after first 100
        name, is_proxy, impl = get_contract_name(addr)
        names[addr] = name
        if is_proxy:
            proxy_info[addr] = impl
        count += 1
        if count % 5 == 0:
            time.sleep(1.1)  # Etherscan rate limit
        if count % 50 == 0:
            print(f"  ...processed {count} names")
        if count >= 400:
            break

    # Step 3: Output results
    outpath = "/home/user/contracs/full_scan_results.txt"
    with open(outpath, "w") as f:
        f.write(f"FULL SCAN: {len(addrs)} contracts\n")
        f.write(f"Generated: {time.strftime('%Y-%m-%d %H:%M:%S UTC')}\n")
        f.write("="*100 + "\n\n")

        # High-value contracts
        f.write("## HIGH VALUE (>100 ETH)\n")
        f.write("-"*100 + "\n")
        for addr in sorted_addrs:
            bal = balances.get(addr, 0)
            if bal < 100:
                break
            name = names.get(addr, "?")
            line_num = addrs.index(addr) + 1
            proxy_str = f" [PROXY -> {proxy_info[addr]}]" if addr in proxy_info else ""
            f.write(f"L{line_num:4d} | {addr} | {name:40s} | {bal:>15.4f} ETH{proxy_str}\n")

        f.write("\n## MEDIUM VALUE (10-100 ETH)\n")
        f.write("-"*100 + "\n")
        for addr in sorted_addrs:
            bal = balances.get(addr, 0)
            if bal >= 100 or bal < 10:
                continue
            name = names.get(addr, "?")
            line_num = addrs.index(addr) + 1
            proxy_str = f" [PROXY -> {proxy_info[addr]}]" if addr in proxy_info else ""
            f.write(f"L{line_num:4d} | {addr} | {name:40s} | {bal:>15.4f} ETH{proxy_str}\n")

        f.write("\n## LOW VALUE (1-10 ETH)\n")
        f.write("-"*100 + "\n")
        for addr in sorted_addrs:
            bal = balances.get(addr, 0)
            if bal >= 10 or bal < 1:
                continue
            name = names.get(addr, "?")
            line_num = addrs.index(addr) + 1
            proxy_str = f" [PROXY -> {proxy_info[addr]}]" if addr in proxy_info else ""
            f.write(f"L{line_num:4d} | {addr} | {name:40s} | {bal:>15.4f} ETH{proxy_str}\n")

        f.write("\n## MINIMAL VALUE (0.01-1 ETH)\n")
        f.write("-"*100 + "\n")
        for addr in sorted_addrs:
            bal = balances.get(addr, 0)
            if bal >= 1 or bal < 0.01:
                continue
            name = names.get(addr, "?")
            line_num = addrs.index(addr) + 1
            proxy_str = f" [PROXY -> {proxy_info[addr]}]" if addr in proxy_info else ""
            f.write(f"L{line_num:4d} | {addr} | {name:40s} | {bal:>15.4f} ETH{proxy_str}\n")

        # Summary stats
        f.write("\n\n## SUMMARY\n")
        f.write("-"*100 + "\n")
        high = sum(1 for a in addrs if balances.get(a, 0) >= 100)
        med = sum(1 for a in addrs if 10 <= balances.get(a, 0) < 100)
        low = sum(1 for a in addrs if 1 <= balances.get(a, 0) < 10)
        mini = sum(1 for a in addrs if 0.01 <= balances.get(a, 0) < 1)
        dust = sum(1 for a in addrs if 0 < balances.get(a, 0) < 0.01)
        zero = sum(1 for a in addrs if balances.get(a, 0) == 0)
        f.write(f"High (>100 ETH): {high}\n")
        f.write(f"Medium (10-100): {med}\n")
        f.write(f"Low (1-10):      {low}\n")
        f.write(f"Minimal (0.01-1):{mini}\n")
        f.write(f"Dust (<0.01):    {dust}\n")
        f.write(f"Zero/Error:      {zero}\n")
        f.write(f"Total:           {len(addrs)}\n")

        # DeFi classification hints
        f.write("\n## DEFI CANDIDATES (by name pattern)\n")
        f.write("-"*100 + "\n")
        defi_keywords = ['vault', 'pool', 'swap', 'exchange', 'lend', 'borrow', 'stake',
                         'farm', 'liquidity', 'amm', 'dex', 'router', 'strategy',
                         'controller', 'comptroller', 'oracle', 'price', 'yield',
                         'reserve', 'collateral', 'debt', 'interest', 'reward',
                         'bridge', 'wrapper', 'adapter', 'aggregator', 'auction',
                         'pmm', 'curve', 'balancer', 'aave', 'compound', 'maker',
                         'uniswap', 'sushi', 'yearn', 'convex']
        for addr in sorted_addrs:
            name = names.get(addr, "").lower()
            bal = balances.get(addr, 0)
            if bal <= 0:
                continue
            matched = [k for k in defi_keywords if k in name]
            if matched:
                proxy_str = f" [PROXY -> {proxy_info[addr]}]" if addr in proxy_info else ""
                f.write(f"{addr} | {names.get(addr,'?'):40s} | {bal:>12.4f} ETH | tags: {','.join(matched)}{proxy_str}\n")

    print(f"\nResults written to {outpath}")

    # Also print top 50 to stdout
    print("\n" + "="*100)
    print("TOP 50 BY ETH BALANCE:")
    print("="*100)
    for i, addr in enumerate(sorted_addrs[:50]):
        bal = balances.get(addr, 0)
        name = names.get(addr, "?")
        line_num = addrs.index(addr) + 1
        proxy_str = " [PROXY]" if addr in proxy_info else ""
        print(f"{i+1:3d}. L{line_num:4d} | {addr} | {name:40s} | {bal:>15.4f} ETH{proxy_str}")

if __name__ == "__main__":
    main()
