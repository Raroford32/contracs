#!/usr/bin/env python3
"""Download historical EVM data from SQD Network gateways.

Implements the router/worker loop described in the official docs:
https://docs.sqd.ai/subsquid-network/reference/evm-api/

Output is NDJSON (one JSON object per line; each line is a block payload).
"""

import argparse
import json
import os
import sys
import time
from copy import deepcopy
from typing import Optional
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError


class SQDError(Exception):
    pass


def http_text(url: str, timeout: int = 30) -> str:
    req = Request(url, method="GET")
    # Cloudflare may block default Python user agents.
    req.add_header("User-Agent", "curl/8.0.0")
    try:
        with urlopen(req, timeout=timeout) as resp:
            return resp.read().decode("utf-8").strip()
    except HTTPError as e:
        raise SQDError(f"HTTP {e.code} for {url}") from e
    except URLError as e:
        raise SQDError(f"URL error for {url}: {e}") from e


def http_json(url: str, method: str = "GET", body=None, timeout: int = 120):
    data = None
    if body is not None:
        data = json.dumps(body).encode("utf-8")
    req = Request(url, data=data, method=method)
    # Cloudflare may block default Python user agents.
    req.add_header("User-Agent", "curl/8.0.0")
    req.add_header("Accept", "application/json")
    if body is not None:
        req.add_header("Content-Type", "application/json")

    try:
        with urlopen(req, timeout=timeout) as resp:
            raw = resp.read().decode("utf-8")
            if not raw:
                return None
            return json.loads(raw)
    except HTTPError as e:
        raise SQDError(f"HTTP {e.code} for {url}") from e
    except URLError as e:
        raise SQDError(f"URL error for {url}: {e}") from e
    except json.JSONDecodeError as e:
        raise SQDError(f"Invalid JSON from {url}: {e}") from e


def normalize_gateway(url: str) -> str:
    u = url.strip()
    if not u:
        raise SQDError("Empty gateway URL")
    return u.rstrip("/")


def sqd_height(gateway_url: str, timeout: int = 30) -> int:
    txt = http_text(f"{gateway_url}/height", timeout=timeout)
    try:
        return int(txt)
    except ValueError as e:
        raise SQDError(f"Unexpected height response: {txt}") from e


def sqd_worker_url(gateway_url: str, block: int, timeout: int = 30) -> str:
    return http_text(f"{gateway_url}/{block}/worker", timeout=timeout)


def last_block_number(batch) -> int:
    if not isinstance(batch, list) or not batch:
        raise SQDError("Empty or invalid worker response")
    last = batch[-1]
    if not isinstance(last, dict):
        raise SQDError("Unexpected response item type")
    header = last.get("header")
    if not isinstance(header, dict):
        raise SQDError("Missing header in response item")
    if "number" in header:
        return int(header["number"])
    if "height" in header:
        return int(header["height"])
    raise SQDError("Header missing block number/height")


def load_query(path: Optional[str], inline: Optional[str]):
    if path:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    if inline:
        return json.loads(inline)
    raise SQDError("Provide --query-file or --query")


def main():
    p = argparse.ArgumentParser(description="Dump EVM data from an SQD Network gateway (NDJSON)")
    p.add_argument("--gateway", required=True, help="Gateway/router URL, e.g. https://v2.archive.subsquid.io/network/ethereum-mainnet")
    p.add_argument("--query-file", help="Path to JSON query")
    p.add_argument("--query", help="Inline JSON query string")
    p.add_argument("--out", required=True, help="Output NDJSON file")
    p.add_argument("--from-block", type=int, help="Override query fromBlock")
    p.add_argument("--to-block", type=int, help="Override query toBlock")
    p.add_argument("--sleep", type=float, default=0.0, help="Sleep between router/worker requests")
    p.add_argument("--timeout", type=int, default=120, help="Worker POST timeout seconds")
    p.add_argument("--router-timeout", type=int, default=30, help="Router GET timeout seconds")
    p.add_argument("--max-batches", type=int, default=0, help="Stop after N worker batches (debug)")
    args = p.parse_args()

    gateway = normalize_gateway(args.gateway)
    query = load_query(args.query_file, args.query)
    if not isinstance(query, dict):
        raise SQDError("Query must be a JSON object")

    if args.from_block is not None:
        query["fromBlock"] = args.from_block
    if args.to_block is not None:
        query["toBlock"] = args.to_block

    if "fromBlock" not in query:
        raise SQDError("Query must include fromBlock (or pass --from-block)")

    from_block = int(query["fromBlock"])

    height = sqd_height(gateway, timeout=args.router_timeout)
    to_block = int(query.get("toBlock", height))
    end_block = min(to_block, height)

    os.makedirs(os.path.dirname(args.out) or ".", exist_ok=True)

    current = from_block
    batches = 0

    with open(args.out, "w", encoding="utf-8") as out_f:
        while current <= end_block:
            worker = sqd_worker_url(gateway, current, timeout=args.router_timeout)
            q = deepcopy(query)
            q["fromBlock"] = current
            q["toBlock"] = end_block

            batch = http_json(worker, method="POST", body=q, timeout=args.timeout)
            if not isinstance(batch, list):
                raise SQDError("Worker response is not a JSON array")

            for item in batch:
                out_f.write(json.dumps(item, separators=(",", ":"), sort_keys=False))
                out_f.write("\n")

            last = last_block_number(batch)
            if last < current:
                raise SQDError(f"Non-advancing batch: last={last} current={current}")
            current = last + 1

            batches += 1
            if args.max_batches and batches >= args.max_batches:
                break

            if args.sleep:
                time.sleep(args.sleep)


if __name__ == "__main__":
    try:
        main()
    except SQDError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
    except KeyboardInterrupt:
        print("Interrupted", file=sys.stderr)
        sys.exit(1)
