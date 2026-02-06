#!/usr/bin/env python3
"""
Run an ItyFuzz EVM campaign with reproducible logging.

This is intentionally a thin wrapper around:
  ityfuzz evm <args...>

Key behaviors:
- Ensures a work dir exists and captures stdout/stderr to files.
- Writes a manifest JSON with the exact command + selected env vars.
- Supports full pass-through of any official CLI flags (see references/cli-ityfuzz-evm-help.txt).

Usage examples:
  python scripts/ityfuzz_run_evm.py -w analysis/ityfuzz/aes -- \
    -t 0x40eD... -c bsc -b 23695904 -f -k "$BSC_ETHERSCAN_API_KEY"

  # Offchain glob fuzzing
  python scripts/ityfuzz_run_evm.py -w analysis/ityfuzz/local -- \
    -t './build/*' --detectors high_confidence
"""

from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional, Tuple


DEFAULT_ENV_KEYS = [
    "ETH_RPC_URL",
    "ETHERSCAN_API_KEY",
    "BSC_ETHERSCAN_API_KEY",
    "POLYGON_ETHERSCAN_API_KEY",
    "ARBISCAN_API_KEY",
    "BASESCAN_API_KEY",
]


@dataclass
class RunConfig:
    work_dir: Path
    ityfuzz_bin: str
    pass_args: List[str]
    extra_env: List[Tuple[str, str]]
    inherit_env: bool
    rust_backtrace: str


def which_ityfuzz(explicit: Optional[str]) -> str:
    if explicit:
        return explicit
    found = shutil.which("ityfuzz")
    if found:
        return found
    raise SystemExit("ERROR: `ityfuzz` not found in PATH (install via `ityfuzzup` or set --ityfuzz-bin)")


def parse_env_kv(items: List[str]) -> List[Tuple[str, str]]:
    out: List[Tuple[str, str]] = []
    for item in items:
        if "=" not in item:
            raise SystemExit(f"ERROR: invalid --env '{item}' (expected KEY=VALUE)")
        k, v = item.split("=", 1)
        k = k.strip()
        if not k:
            raise SystemExit(f"ERROR: invalid --env '{item}' (empty key)")
        out.append((k, v))
    return out


def has_work_dir_arg(args: List[str]) -> bool:
    # Handles: -w DIR, --work-dir DIR, --work-dir=DIR
    for i, a in enumerate(args):
        if a in ("-w", "--work-dir"):
            return True
        if a.startswith("--work-dir="):
            return True
    return False


def build_cmd(cfg: RunConfig) -> List[str]:
    cmd = [cfg.ityfuzz_bin, "evm"]
    if not has_work_dir_arg(cfg.pass_args):
        cmd += ["--work-dir", str(cfg.work_dir)]
    cmd += cfg.pass_args
    return cmd


def select_env(inherit: bool, extra: List[Tuple[str, str]], rust_backtrace: str) -> dict:
    env = os.environ.copy() if inherit else {}
    if rust_backtrace:
        env["RUST_BACKTRACE"] = rust_backtrace
    for k, v in extra:
        env[k] = v
    return env


def write_manifest(path: Path, cmd: List[str], env: dict) -> None:
    # Store a small, human-greppable subset of env by default.
    env_subset = {k: env.get(k, "") for k in DEFAULT_ENV_KEYS if k in env}
    manifest = {
        "ts": int(time.time()),
        "cmd": cmd,
        "env_subset": env_subset,
        "cwd": str(Path.cwd()),
    }
    path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")


def main() -> None:
    p = argparse.ArgumentParser(description="Run `ityfuzz evm` with logging + a manifest.")
    p.add_argument("-w", "--work-dir", required=True, help="Work dir (captures logs + outputs).")
    p.add_argument("--ityfuzz-bin", help="Path to ityfuzz binary (default: find in PATH).")
    p.add_argument(
        "--env",
        action="append",
        default=[],
        help="Set env var for the run (KEY=VALUE). Repeatable.",
    )
    p.add_argument(
        "--no-inherit-env",
        action="store_true",
        help="Do not inherit the current process env (use only --env and RUST_BACKTRACE).",
    )
    p.add_argument(
        "--rust-backtrace",
        default="1",
        help="Set RUST_BACKTRACE (default: 1). Use 0 to disable.",
    )
    p.add_argument(
        "--dry-run",
        action="store_true",
        help="Print command + manifest path, but do not execute.",
    )
    p.add_argument(
        "args",
        nargs=argparse.REMAINDER,
        help="Pass-through args for `ityfuzz evm`. Prefix with `--` to separate.",
    )
    args = p.parse_args()

    # argparse keeps the `--` separator in args; drop it if present.
    pass_args = args.args
    if pass_args and pass_args[0] == "--":
        pass_args = pass_args[1:]
    if not pass_args:
        raise SystemExit(
            "ERROR: provide pass-through args for `ityfuzz evm` after `--` (see references/cli-ityfuzz-evm-help.txt)"
        )

    cfg = RunConfig(
        work_dir=Path(args.work_dir).resolve(),
        ityfuzz_bin=which_ityfuzz(args.ityfuzz_bin),
        pass_args=pass_args,
        extra_env=parse_env_kv(args.env),
        inherit_env=not args.no_inherit_env,
        rust_backtrace=args.rust_backtrace,
    )

    cfg.work_dir.mkdir(parents=True, exist_ok=True)
    cmd = build_cmd(cfg)
    env = select_env(cfg.inherit_env, cfg.extra_env, cfg.rust_backtrace)

    manifest_path = cfg.work_dir / "run.manifest.json"
    write_manifest(manifest_path, cmd, env)

    stdout_path = cfg.work_dir / "stdout.log"
    stderr_path = cfg.work_dir / "stderr.log"

    print("Work dir :", cfg.work_dir)
    print("Manifest :", manifest_path)
    print("Command  :", " ".join(cmd))

    if args.dry_run:
        return

    with stdout_path.open("wb") as out, stderr_path.open("wb") as err:
        proc = subprocess.run(cmd, stdout=out, stderr=err, env=env)
    print("Exit code:", proc.returncode)
    print("Stdout   :", stdout_path)
    print("Stderr   :", stderr_path)

    # Convenience hints for common outputs.
    vuln_dir = cfg.work_dir / "vulnerabilities"
    if vuln_dir.exists():
        print("Vulns    :", vuln_dir)

    sys.exit(proc.returncode)


if __name__ == "__main__":
    main()

