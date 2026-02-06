#!/usr/bin/env python3
"""
Summarize an ItyFuzz work dir (bugs + generated PoCs).

Reads:
- vuln_info.jsonl (if present)
- vulnerabilities/ (if present)
"""

from __future__ import annotations

import argparse
import json
from collections import Counter, defaultdict
from pathlib import Path


def read_jsonl(path: Path):
    items = []
    if not path.exists():
        return items
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            items.append(json.loads(line))
        except json.JSONDecodeError:
            # Keep going; some builds may interleave non-JSON lines.
            continue
    return items


def main() -> None:
    p = argparse.ArgumentParser(description="Summarize an ItyFuzz work dir")
    p.add_argument("work_dir", help="Path passed as --work-dir to ityfuzz")
    args = p.parse_args()

    wd = Path(args.work_dir).resolve()
    if not wd.exists():
        raise SystemExit(f"ERROR: work dir not found: {wd}")

    vuln_info = read_jsonl(wd / "vuln_info.jsonl")
    vulns_dir = wd / "vulnerabilities"

    print("Work dir :", wd)

    if vuln_info:
        types = Counter()
        by_type = defaultdict(list)
        for item in vuln_info:
            bug_type = str(item.get("bug_type", ""))
            bug_info = str(item.get("bug_info", ""))
            bug_idx = item.get("bug_idx")
            types[bug_type] += 1
            by_type[bug_type].append((bug_idx, bug_info))

        print("\nBugs (vuln_info.jsonl)")
        for t, n in types.most_common():
            print(f"- {t or '(unknown)'}: {n}")

        print("\nSample bug_info per type")
        for t, rows in by_type.items():
            sample = rows[0]
            print(f"- {t or '(unknown)'}: idx={sample[0]} info={sample[1][:180]}")
    else:
        print("\nBugs: vuln_info.jsonl not found or empty")

    if vulns_dir.exists():
        tsol = sorted(p.name for p in vulns_dir.glob("*.t.sol"))
        replayable = sorted(p.name for p in vulns_dir.glob("*_replayable"))
        print("\nGenerated PoCs (vulnerabilities/)")
        print(f"- Foundry tests  : {len(tsol)}")
        if tsol[:10]:
            print("  " + " ".join(tsol[:10]) + (" ..." if len(tsol) > 10 else ""))
        print(f"- Replay traces  : {len(replayable)}")
        if replayable[:10]:
            print("  " + " ".join(replayable[:10]) + (" ..." if len(replayable) > 10 else ""))
    else:
        print("\nGenerated PoCs: vulnerabilities/ not found")


if __name__ == "__main__":
    main()

