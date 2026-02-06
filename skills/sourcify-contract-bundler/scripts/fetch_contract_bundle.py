#!/usr/bin/env python3
import argparse
import json
import os
import sys
import time
from urllib.parse import urlencode
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError

DEFAULT_SOURCIFY_BASE = "https://sourcify.dev/server"
DEFAULT_ETHERSCAN_BASE = "https://api.etherscan.io/v2/api"
DEFAULT_SQD_GATEWAY_BASE = "https://v2.archive.subsquid.io/network"

EIP1967_IMPLEMENTATION_SLOT = "0x360894a13ba1a3210667c828492db98dca3e2076cc3735a920a3ca505d382bbc"
EIP1967_BEACON_SLOT = "0xa3f0ad74e5423aebfd80d3ef4346578335a9a72aeaee59ff6cb3582b35133d50"
BEACON_IMPL_SELECTOR = "0x5c60da1b"


class FetchError(Exception):
    pass


def http_text(url, method="GET", body=None, headers=None, timeout=30):
    data = None
    if body is not None:
        data = json.dumps(body).encode("utf-8")
    req = Request(url, data=data, method=method)
    # Some gateways sit behind Cloudflare and may block default Python user agents.
    req.add_header("User-Agent", "curl/8.0.0")
    if headers:
        for k, v in headers.items():
            req.add_header(k, v)
    try:
        with urlopen(req, timeout=timeout) as resp:
            return resp.read().decode("utf-8").strip()
    except HTTPError as e:
        if e.code == 404:
            return ""
        raise FetchError(f"HTTP {e.code} for {url}") from e
    except URLError as e:
        raise FetchError(f"URL error for {url}: {e}") from e


def http_json(url, method="GET", body=None, headers=None, timeout=30):
    data = None
    if body is not None:
        data = json.dumps(body).encode("utf-8")
    req = Request(url, data=data, method=method)
    # Some gateways sit behind Cloudflare and may block default Python user agents.
    req.add_header("User-Agent", "curl/8.0.0")
    req.add_header("Accept", "application/json")
    if body is not None:
        req.add_header("Content-Type", "application/json")
    if headers:
        for k, v in headers.items():
            req.add_header(k, v)
    try:
        with urlopen(req, timeout=timeout) as resp:
            raw = resp.read().decode("utf-8")
            if not raw:
                return None
            return json.loads(raw)
    except HTTPError as e:
        if e.code == 404:
            return None
        raise FetchError(f"HTTP {e.code} for {url}") from e
    except URLError as e:
        raise FetchError(f"URL error for {url}: {e}") from e
    except json.JSONDecodeError as e:
        raise FetchError(f"Invalid JSON from {url}: {e}") from e


def normalize_address(addr):
    a = addr.strip()
    if not a:
        return ""
    if not a.startswith("0x"):
        a = "0x" + a
    return a.lower()


def ensure_dir(path):
    os.makedirs(path, exist_ok=True)


def write_json(path, obj):
    ensure_dir(os.path.dirname(path))
    with open(path, "w", encoding="utf-8") as f:
        json.dump(obj, f, indent=2, sort_keys=False)


def write_sources(base_dir, sources_map, fallback_name="Contract.sol"):
    for file_path, info in sources_map.items():
        if isinstance(info, dict) and "content" in info:
            content = info["content"]
        elif isinstance(info, str):
            content = info
        else:
            content = ""
        rel_path = file_path.strip() if file_path.strip() else fallback_name
        out_path = os.path.join(base_dir, rel_path)
        ensure_dir(os.path.dirname(out_path))
        with open(out_path, "w", encoding="utf-8") as f:
            f.write(content)


def parse_etherscan_source(source_code_raw):
    if not source_code_raw:
        return None
    raw = source_code_raw.strip()
    if raw.lower().startswith("contract source code not verified"):
        return None

    # Handle Etherscan's double-brace JSON
    if raw.startswith("{{") and raw.endswith("}}"): 
        raw = raw[1:-1]

    if raw.startswith("{") or raw.startswith("["):
        try:
            data = json.loads(raw)
            if isinstance(data, dict) and "sources" in data:
                return data["sources"]
            if isinstance(data, dict) and "SourceCode" in data and isinstance(data["SourceCode"], dict):
                sc = data["SourceCode"]
                if "sources" in sc:
                    return sc["sources"]
            if isinstance(data, list):
                # Uncommon, but treat as list of files
                sources = {}
                for idx, item in enumerate(data):
                    key = f"File{idx+1}.sol"
                    if isinstance(item, dict) and "content" in item:
                        sources[key] = {"content": item["content"]}
                    else:
                        sources[key] = {"content": json.dumps(item)}
                return sources
        except json.JSONDecodeError:
            pass

    # Fallback: treat as single file
    return {"Contract.sol": {"content": raw}}


def etherscan_get(base_url, chain_id, address, action, api_key):
    params = {
        "chainid": str(chain_id),
        "module": "contract",
        "action": action,
        "address": address,
        "apikey": api_key or ""
    }
    url = f"{base_url}?{urlencode(params)}"
    return http_json(url)


def sourcify_contract(base_url, chain_id, address, fields):
    url = f"{base_url}/v2/contract/{chain_id}/{address}?fields={fields}"
    return http_json(url)


def rpc_call(rpc_url, method, params):
    payload = {"jsonrpc": "2.0", "id": int(time.time()), "method": method, "params": params}
    resp = http_json(rpc_url, method="POST", body=payload)
    if resp is None:
        return None
    if "error" in resp:
        return None
    return resp.get("result")


def slot_to_address(slot_value):
    if not slot_value or not slot_value.startswith("0x"):
        return None
    hex_value = slot_value[2:].rjust(64, "0")
    addr = "0x" + hex_value[-40:]
    if int(addr, 16) == 0:
        return None
    return addr.lower()


def parse_impls_from_etherscan(result_item):
    impls = []
    proxy_flag = str(result_item.get("Proxy", "0")).strip()
    impl_field = str(result_item.get("Implementation", "")).strip()
    if proxy_flag == "1" and impl_field:
        for part in impl_field.replace(";", ",").split(","):
            addr = normalize_address(part)
            if addr:
                impls.append(addr)
    return impls


def sqd_normalize_gateway(gateway_url, network_slug):
    if gateway_url and network_slug:
        raise FetchError("Use only one of --sqd-gateway or --sqd-network")
    if gateway_url:
        return gateway_url.strip().rstrip("/")
    if network_slug:
        slug = network_slug.strip().strip("/")
        if not slug:
            raise FetchError("Empty --sqd-network")
        return f"{DEFAULT_SQD_GATEWAY_BASE}/{slug}"
    return ""


def sqd_height(gateway_url, timeout=30):
    txt = http_text(f"{gateway_url}/height", timeout=timeout)
    if not txt:
        raise FetchError(f"Empty height response from {gateway_url}")
    try:
        return int(txt)
    except ValueError as e:
        raise FetchError(f"Unexpected height response: {txt}") from e


def sqd_worker_url(gateway_url, block, timeout=30):
    worker = http_text(f"{gateway_url}/{block}/worker", timeout=timeout)
    if not worker:
        raise FetchError(f"Empty worker URL from {gateway_url} at block {block}")
    return worker


def sqd_last_block_number(batch):
    if not isinstance(batch, list) or not batch:
        raise FetchError("Empty or invalid worker response")
    last = batch[-1]
    if not isinstance(last, dict):
        raise FetchError("Unexpected worker response item type")
    header = last.get("header")
    if not isinstance(header, dict):
        raise FetchError("Missing header in worker response")
    if "number" in header:
        return int(header["number"])
    if "height" in header:
        return int(header["height"])
    raise FetchError("Header missing block number/height")


def sqd_dump_ndjson(gateway_url, base_query, out_path, from_block, to_block=None, include_all_blocks=False,
                    router_timeout=30, worker_timeout=120, sleep_sec=0.0, max_batches=0):
    gateway = gateway_url.rstrip("/")
    height = sqd_height(gateway, timeout=router_timeout)
    end = min(int(to_block) if to_block is not None else height, height)

    if from_block is None:
        raise FetchError("fromBlock is required for SQD dump")
    current = int(from_block)

    ensure_dir(os.path.dirname(out_path))

    batches = 0
    with open(out_path, "w", encoding="utf-8") as out_f:
        while current <= end:
            worker = sqd_worker_url(gateway, current, timeout=router_timeout)
            # Copy the query without mutating the caller's object.
            q = json.loads(json.dumps(base_query))
            q["fromBlock"] = current
            q["toBlock"] = end
            if include_all_blocks:
                q["includeAllBlocks"] = True

            batch = http_json(worker, method="POST", body=q, timeout=worker_timeout)
            if not isinstance(batch, list):
                raise FetchError("Worker response is not a JSON array")
            for item in batch:
                out_f.write(json.dumps(item, separators=(",", ":"), sort_keys=False))
                out_f.write("\n")

            last = sqd_last_block_number(batch)
            if last < current:
                raise FetchError(f"Non-advancing SQD batch: last={last} current={current}")
            current = last + 1

            batches += 1
            if max_batches and batches >= max_batches:
                break
            if sleep_sec:
                time.sleep(sleep_sec)

    return {"fromBlock": int(from_block), "toBlock": end, "height": height, "batches": batches}


def load_addresses(args):
    addrs = []
    if args.addresses:
        for part in args.addresses.split(","):
            a = normalize_address(part)
            if a:
                addrs.append(a)
    if args.address_file:
        with open(args.address_file, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                a = normalize_address(line)
                if a:
                    addrs.append(a)
    if not addrs:
        raise FetchError("No addresses provided")
    return list(dict.fromkeys(addrs))


def main():
    parser = argparse.ArgumentParser(description="Fetch contract sources/ABI via Sourcify, Etherscan, RPC (+ optional SQD evidence)")
    parser.add_argument("--chain-id", required=True, help="Chain ID")
    parser.add_argument("--addresses", help="Comma-separated addresses")
    parser.add_argument("--address-file", help="File with one address per line")
    parser.add_argument("--out", default="analysis/contract-bundles", help="Output directory")
    parser.add_argument("--sourcify-base", default=DEFAULT_SOURCIFY_BASE)
    parser.add_argument("--sourcify-fields", default="all")
    parser.add_argument("--skip-sourcify", action="store_true")
    parser.add_argument("--etherscan-base", default=DEFAULT_ETHERSCAN_BASE)
    parser.add_argument("--etherscan-key", default=os.environ.get("ETHERSCAN_API_KEY", ""))
    parser.add_argument("--skip-etherscan", action="store_true")
    parser.add_argument("--rpc-url", default=os.environ.get("RPC_URL", ""))
    parser.add_argument("--skip-rpc", action="store_true")
    parser.add_argument("--max-depth", type=int, default=2, help="Max proxy-follow depth")
    # SQD / SubSquid evidence extraction (optional)
    parser.add_argument("--sqd-gateway", default="",
                        help="SQD gateway URL (router), e.g. https://v2.archive.subsquid.io/network/ethereum-mainnet")
    parser.add_argument("--sqd-network", default="",
                        help="Gateway network slug, e.g. ethereum-mainnet (expands to https://v2.archive.subsquid.io/network/<slug>)")
    parser.add_argument("--skip-sqd", action="store_true", help="Disable SQD evidence even if configured")
    parser.add_argument("--sqd-types", default="logs,transactions",
                        help="Comma-separated evidence types: logs,transactions,traces,stateDiffs (default: logs,transactions)")
    parser.add_argument("--sqd-from-block", type=int, default=None,
                        help="Override evidence fromBlock (defaults to deployment block if known, else 0)")
    parser.add_argument("--sqd-to-block", type=int, default=None,
                        help="Override evidence toBlock (defaults to gateway height)")
    parser.add_argument("--sqd-evidence-depth", type=int, default=0,
                        help="Fetch SQD evidence only for contracts at depth<=N (default: 0 = seeds only)")
    parser.add_argument("--sqd-router-timeout", type=int, default=30)
    parser.add_argument("--sqd-worker-timeout", type=int, default=120)
    parser.add_argument("--sqd-sleep", type=float, default=0.0, help="Sleep between SQD requests (rate limiting/backoff)")
    parser.add_argument("--sqd-max-batches", type=int, default=0, help="Stop after N worker batches (debug)")
    parser.add_argument("--sqd-include-all-blocks", action="store_true", help="Set includeAllBlocks=true (usually increases output size)")
    parser.add_argument("--sqd-with-tx-logs", action="store_true", help="When fetching transactions evidence, also retrieve logs for those txs")
    parser.add_argument("--sqd-with-tx-traces", action="store_true", help="When fetching transactions evidence, also retrieve traces for those txs")
    parser.add_argument("--sqd-with-tx-state-diffs", action="store_true", help="When fetching transactions evidence, also retrieve state diffs for those txs")
    args = parser.parse_args()

    chain_id = str(args.chain_id)
    addresses = load_addresses(args)

    out_dir = args.out
    ensure_dir(out_dir)

    sqd_gateway = sqd_normalize_gateway(args.sqd_gateway, args.sqd_network)
    sqd_types = [t.strip() for t in (args.sqd_types or "").split(",") if t.strip()]

    manifest = {
        "chainId": chain_id,
        "generatedAt": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "contracts": {}
    }

    queue = [(addr, 0, None) for addr in addresses]
    visited = set()

    while queue:
        address, depth, parent = queue.pop(0)
        address = normalize_address(address)
        if not address or address in visited:
            continue
        visited.add(address)

        contract_dir = os.path.join(out_dir, f"chain-{chain_id}", address)
        src_dir = os.path.join(contract_dir, "src")
        abi_dir = os.path.join(contract_dir, "abi")
        meta_dir = os.path.join(contract_dir, "metadata")
        rpc_dir = os.path.join(contract_dir, "rpc")
        ensure_dir(src_dir)
        ensure_dir(abi_dir)
        ensure_dir(meta_dir)
        ensure_dir(rpc_dir)

        info = {
            "address": address,
            "chainId": chain_id,
            "parent": parent,
            "sources": None,
            "abi": None,
            "compiler": None,
            "verification": {},
            "proxy": {
                "isProxy": False,
                "type": None,
                "implementations": []
            },
            "evidence": {}
        }

        # Sourcify lookup
        sourcify_data = None
        if not args.skip_sourcify:
            try:
                sourcify_data = sourcify_contract(args.sourcify_base, chain_id, address, args.sourcify_fields)
            except FetchError as e:
                sourcify_data = None
                info["verification"]["sourcify_error"] = str(e)

        if sourcify_data:
            write_json(os.path.join(meta_dir, "sourcify-contract.json"), sourcify_data)
            sources = sourcify_data.get("sources") or {}
            if sources:
                write_sources(src_dir, sources)
                info["sources"] = "sourcify"
            abi = sourcify_data.get("abi")
            if abi:
                write_json(os.path.join(abi_dir, "abi.json"), abi)
                info["abi"] = "sourcify"
            info["compiler"] = sourcify_data.get("compilation", {}).get("compilerVersion")
            info["verification"]["sourcify"] = {
                "match": sourcify_data.get("match"),
                "creationMatch": sourcify_data.get("creationMatch"),
                "runtimeMatch": sourcify_data.get("runtimeMatch"),
                "verifiedAt": sourcify_data.get("verifiedAt")
            }
            proxy_res = sourcify_data.get("proxyResolution") or {}
            if proxy_res.get("isProxy"):
                info["proxy"]["isProxy"] = True
                info["proxy"]["type"] = proxy_res.get("proxyType")
                impls = []
                for item in proxy_res.get("implementations", []):
                    addr = normalize_address(item.get("address", "")) if isinstance(item, dict) else normalize_address(str(item))
                    if addr:
                        impls.append(addr)
                info["proxy"]["implementations"].extend(impls)
            # Deployment info (when present) is useful for selecting a sensible evidence start block.
            dep = sourcify_data.get("deployment") or {}
            if isinstance(dep, dict) and dep.get("blockNumber") is not None:
                info["verification"]["deploymentBlockNumber"] = dep.get("blockNumber")

        # Etherscan fallback or complement
        etherscan_item = None
        if not args.skip_etherscan and (not info["sources"] or not info["abi"]):
            if not args.etherscan_key:
                info["verification"]["etherscan_error"] = "Missing Etherscan API key"
            else:
                try:
                    src_resp = etherscan_get(args.etherscan_base, chain_id, address, "getsourcecode", args.etherscan_key)
                    if src_resp and src_resp.get("status") == "1":
                        result = src_resp.get("result") or []
                        if result:
                            etherscan_item = result[0]
                            write_json(os.path.join(meta_dir, "etherscan-source.json"), src_resp)
                            if not info["sources"]:
                                sources = parse_etherscan_source(etherscan_item.get("SourceCode", ""))
                                if sources:
                                    contract_name = etherscan_item.get("ContractName") or "Contract"
                                    write_sources(src_dir, sources, f"{contract_name}.sol")
                                    info["sources"] = "etherscan"
                            info["compiler"] = etherscan_item.get("CompilerVersion") or info["compiler"]
                            info["verification"]["etherscan"] = {
                                "contractName": etherscan_item.get("ContractName"),
                                "compilerVersion": etherscan_item.get("CompilerVersion"),
                                "optimizationUsed": etherscan_item.get("OptimizationUsed"),
                                "runs": etherscan_item.get("Runs"),
                                "licenseType": etherscan_item.get("LicenseType")
                            }
                except FetchError as e:
                    info["verification"]["etherscan_error"] = str(e)

                if not info["abi"]:
                    try:
                        abi_resp = etherscan_get(args.etherscan_base, chain_id, address, "getabi", args.etherscan_key)
                        if abi_resp and abi_resp.get("status") == "1":
                            abi_raw = abi_resp.get("result")
                            abi = json.loads(abi_raw) if isinstance(abi_raw, str) else abi_raw
                            write_json(os.path.join(abi_dir, "abi.json"), abi)
                            info["abi"] = "etherscan"
                    except (FetchError, json.JSONDecodeError) as e:
                        info["verification"]["etherscan_abi_error"] = str(e)

        # Proxy hints from etherscan
        if etherscan_item:
            info["proxy"]["implementations"].extend(parse_impls_from_etherscan(etherscan_item))
            if str(etherscan_item.get("Proxy", "0")).strip() == "1":
                info["proxy"]["isProxy"] = True

        # RPC proxy detection
        if not args.skip_rpc and args.rpc_url:
            slots = {}
            impl_slot = rpc_call(args.rpc_url, "eth_getStorageAt", [address, EIP1967_IMPLEMENTATION_SLOT, "latest"])
            slots["implementation"] = impl_slot
            impl_addr = slot_to_address(impl_slot)
            if impl_addr:
                info["proxy"]["isProxy"] = True
                info["proxy"]["implementations"].append(impl_addr)

            beacon_slot = rpc_call(args.rpc_url, "eth_getStorageAt", [address, EIP1967_BEACON_SLOT, "latest"])
            slots["beacon"] = beacon_slot
            beacon_addr = slot_to_address(beacon_slot)
            if beacon_addr:
                info["proxy"]["isProxy"] = True
                slots["beaconAddress"] = beacon_addr
                impl_call = rpc_call(args.rpc_url, "eth_call", [{"to": beacon_addr, "data": BEACON_IMPL_SELECTOR}, "latest"])
                slots["beaconImplementationRaw"] = impl_call
                impl_from_beacon = slot_to_address(impl_call)
                if impl_from_beacon:
                    info["proxy"]["implementations"].append(impl_from_beacon)

            write_json(os.path.join(rpc_dir, "slots.json"), slots)

        # Normalize proxy implementations list
        impls = []
        for item in info["proxy"]["implementations"]:
            addr = normalize_address(item)
            if addr and addr not in impls:
                impls.append(addr)
        info["proxy"]["implementations"] = impls

        # SQD evidence extraction (optional)
        if sqd_gateway and (not args.skip_sqd) and depth <= args.sqd_evidence_depth and sqd_types:
            sqd_dir = os.path.join(contract_dir, "sqd")
            sqd_q_dir = os.path.join(sqd_dir, "queries")
            sqd_r_dir = os.path.join(sqd_dir, "results")
            ensure_dir(sqd_q_dir)
            ensure_dir(sqd_r_dir)

            # Determine evidence block range.
            from_block = args.sqd_from_block
            if from_block is None:
                dep_bn = info.get("verification", {}).get("deploymentBlockNumber")
                try:
                    from_block = int(dep_bn) if dep_bn is not None and str(dep_bn).isdigit() else None
                except (TypeError, ValueError):
                    from_block = None
            if from_block is None:
                from_block = 0

            to_block = args.sqd_to_block

            # Minimal field selection for evidence (avoid expensive defaults where possible).
            fields_min = {
                "transaction": {"hash": True, "from": True, "to": True, "input": True, "value": True},
                "log": {"address": True, "topics": True, "data": True, "transactionHash": True},
            }

            evidence_cfg = {
                "gateway": sqd_gateway,
                "types": sqd_types,
                "fromBlock": from_block,
                "toBlock": to_block,
                "generatedAt": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            }
            write_json(os.path.join(sqd_dir, "config.json"), evidence_cfg)

            outputs = {}
            for t in sqd_types:
                if t not in ("logs", "transactions", "traces", "stateDiffs"):
                    continue

                if t == "logs":
                    query = {
                        "fields": fields_min,
                        "logs": [
                            {
                                "address": [address],
                            }
                        ],
                    }
                elif t == "transactions":
                    txn_req = {"to": [address]}
                    if args.sqd_with_tx_logs:
                        txn_req["logs"] = True
                    if args.sqd_with_tx_traces:
                        txn_req["traces"] = True
                    if args.sqd_with_tx_state_diffs:
                        txn_req["stateDiffs"] = True
                    query = {
                        "fields": fields_min,
                        "transactions": [txn_req],
                    }
                elif t == "traces":
                    query = {
                        "traces": [
                            {
                                "type": ["call"],
                                "callTo": [address],
                                "transaction": True,
                            }
                        ],
                    }
                else:  # stateDiffs
                    query = {
                        "stateDiffs": [
                            {
                                "address": [address],
                                "transaction": True,
                            }
                        ],
                    }

                write_json(os.path.join(sqd_q_dir, f"{t}.json"), query)
                out_path = os.path.join(sqd_r_dir, f"{t}.ndjson")

                try:
                    summary = sqd_dump_ndjson(
                        sqd_gateway,
                        query,
                        out_path,
                        from_block,
                        to_block=to_block,
                        include_all_blocks=args.sqd_include_all_blocks,
                        router_timeout=args.sqd_router_timeout,
                        worker_timeout=args.sqd_worker_timeout,
                        sleep_sec=args.sqd_sleep,
                        max_batches=args.sqd_max_batches,
                    )
                    outputs[t] = {"ndjson": os.path.relpath(out_path, contract_dir), "summary": summary}
                except FetchError as e:
                    outputs[t] = {"error": str(e)}

            info["evidence"]["sqd"] = {
                "gateway": sqd_gateway,
                "fromBlock": from_block,
                "toBlock": to_block,
                "types": sqd_types,
                "outputs": outputs,
            }

        write_json(os.path.join(contract_dir, "info.json"), info)
        manifest["contracts"][address] = info

        # Enqueue implementations
        if info["proxy"]["implementations"] and depth < args.max_depth:
            for impl in info["proxy"]["implementations"]:
                if impl not in visited:
                    queue.append((impl, depth + 1, address))

    write_json(os.path.join(out_dir, "manifest.json"), manifest)


if __name__ == "__main__":
    try:
        main()
    except FetchError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
    except KeyboardInterrupt:
        print("Interrupted", file=sys.stderr)
        sys.exit(1)
