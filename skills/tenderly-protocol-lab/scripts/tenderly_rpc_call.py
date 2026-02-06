#!/usr/bin/env python3
"""
Generic JSON-RPC caller that saves request/response pairs as evidence artifacts.

Design goals:
- Zero non-stdlib dependencies
- Works with Tenderly Node RPC, Virtual TestNet RPC, and Virtual TestNet Admin RPC
- Disk-first: store exact request + exact response to avoid "lost evidence"
"""

from __future__ import annotations

import argparse
import datetime as _dt
import json
import os
import re
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path


def _sanitize_label(s: str) -> str:
    s = s.strip()
    if not s:
        return ""
    s = s.replace(" ", "-")
    s = re.sub(r"[^A-Za-z0-9._-]+", "_", s)
    s = re.sub(r"_+", "_", s)
    return s[:120]


def _utc_stamp() -> str:
    return _dt.datetime.now(tz=_dt.timezone.utc).strftime("%Y%m%d_%H%M%SZ")


def _read_json_file(path: str) -> object:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def _json_dumps(obj: object) -> str:
    return json.dumps(obj, indent=2, sort_keys=True)


def _write_text(path: Path, s: str) -> None:
    path.write_text(s, encoding="utf-8")


def _post_json(rpc_url: str, payload: dict, timeout_s: float) -> tuple[int, dict | str]:
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        rpc_url,
        data=data,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout_s) as resp:
            body_bytes = resp.read()
            body = body_bytes.decode("utf-8", errors="replace")
            try:
                return resp.status, json.loads(body)
            except json.JSONDecodeError:
                return resp.status, body
    except urllib.error.HTTPError as e:
        # HTTPError is also a file-like response; try to read body for evidence.
        try:
            body = e.read().decode("utf-8", errors="replace")
        except Exception:
            body = ""
        out: dict[str, object] = {
            "error": "http_error",
            "status": getattr(e, "code", None),
            "reason": getattr(e, "reason", None),
            "body": body,
        }
        return int(getattr(e, "code", 0) or 0), out
    except urllib.error.URLError as e:
        out2: dict[str, object] = {
            "error": "url_error",
            "reason": str(e.reason) if hasattr(e, "reason") else str(e),
        }
        return 0, out2


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(description="Call a JSON-RPC method and optionally save evidence artifacts.")
    ap.add_argument("--rpc-url", required=True, help="Full JSON-RPC URL (e.g., Tenderly Node RPC or Admin RPC URL).")
    ap.add_argument("--method", required=True, help="JSON-RPC method name.")
    group = ap.add_mutually_exclusive_group()
    group.add_argument("--params-json", default="[]", help="JSON for params (usually an array). Default: []")
    group.add_argument("--params-file", help="Path to a JSON file containing params (array/object).")
    ap.add_argument("--id", type=int, default=1, help="JSON-RPC id. Default: 1")
    ap.add_argument("--timeout", type=float, default=120.0, help="HTTP timeout seconds. Default: 120")
    ap.add_argument("--out-dir", help="Directory to write artifacts. Creates a timestamped subdir per call.")
    ap.add_argument("--label", default="", help="Optional label included in artifact directory name.")
    args = ap.parse_args(argv)

    if args.params_file:
        params_obj = _read_json_file(args.params_file)
    else:
        try:
            params_obj = json.loads(args.params_json)
        except json.JSONDecodeError as e:
            print(f"Invalid --params-json: {e}", file=sys.stderr)
            return 2

    payload = {"jsonrpc": "2.0", "id": args.id, "method": args.method, "params": params_obj}

    t0 = time.time()
    status, resp_obj = _post_json(args.rpc_url, payload, timeout_s=args.timeout)
    elapsed_ms = int((time.time() - t0) * 1000)

    if args.out_dir:
        out_dir = Path(args.out_dir)
        out_dir.mkdir(parents=True, exist_ok=True)

        stamp = _utc_stamp()
        label = _sanitize_label(args.label)
        method = _sanitize_label(args.method)
        parts = [stamp]
        if label:
            parts.append(label)
        parts.append(method)
        run_dir = out_dir / ("__".join(parts))
        run_dir.mkdir(parents=True, exist_ok=True)

        _write_text(run_dir / "request.json", _json_dumps(payload) + "\n")
        if isinstance(resp_obj, dict):
            _write_text(run_dir / "response.json", _json_dumps(resp_obj) + "\n")
        else:
            _write_text(run_dir / "response.txt", resp_obj + "\n")

        meta = {
            "rpc_url": args.rpc_url,
            "method": args.method,
            "status": status,
            "elapsed_ms": elapsed_ms,
            "cwd": os.getcwd(),
            "params_source": ("file:" + args.params_file) if args.params_file else "inline",
        }
        _write_text(run_dir / "meta.json", _json_dumps(meta) + "\n")

        print(str(run_dir))
        return 0 if status and status < 400 else 1

    # stdout mode
    if isinstance(resp_obj, dict):
        print(_json_dumps(resp_obj))
    else:
        print(resp_obj)
    return 0 if status and status < 400 else 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))

