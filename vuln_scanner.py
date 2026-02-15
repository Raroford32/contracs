#!/usr/bin/env python3
"""Scan cached source files for specific vulnerability patterns."""
import os
import re
import sys

SRC_DIR = "/home/user/contracs/src_cache"

PATTERNS = {
    "delegatecall_user_input": {
        "regex": r"delegatecall\s*\(",
        "desc": "delegatecall (check if target is user-controlled)",
        "severity": "HIGH"
    },
    "selfdestruct": {
        "regex": r"selfdestruct\s*\(",
        "desc": "selfdestruct usage",
        "severity": "HIGH"
    },
    "ecrecover_no_zero_check": {
        "regex": r"ecrecover\s*\(",
        "desc": "ecrecover usage (check for zero address return)",
        "severity": "MEDIUM"
    },
    "tx_origin": {
        "regex": r"tx\.origin",
        "desc": "tx.origin usage (phishing vector)",
        "severity": "MEDIUM"
    },
    "unchecked_call": {
        "regex": r"\.call\{.*\}\s*\(\s*\"\"\s*\)|\.call\.value\s*\(",
        "desc": "Low-level call with value",
        "severity": "MEDIUM"
    },
    "balance_based_accounting": {
        "regex": r"address\(this\)\.balance|balanceOf\(address\(this\)\)",
        "desc": "Balance-based accounting (donation attack vector)",
        "severity": "HIGH"
    },
    "initialize_public": {
        "regex": r"function\s+initialize\s*\([^)]*\)\s*(public|external)",
        "desc": "Public initialize function (uninitialized proxy risk)",
        "severity": "HIGH"
    },
    "no_reentrancy_guard": {
        "regex": r"\.call\{value:\s*[^}]+\}\s*\(\s*\"\"\s*\)",
        "desc": "ETH transfer via call (check for reentrancy guard)",
        "severity": "MEDIUM"
    },
    "block_timestamp_dependence": {
        "regex": r"block\.timestamp\s*[<>=]|now\s*[<>=]",
        "desc": "Block timestamp used in comparison",
        "severity": "LOW"
    },
    "assembly_block": {
        "regex": r"assembly\s*\{",
        "desc": "Inline assembly usage",
        "severity": "INFO"
    },
    "transfer_without_return_check": {
        "regex": r"\.transfer\s*\([^)]+\)\s*;",
        "desc": "ERC20 transfer without return value check",
        "severity": "MEDIUM"
    },
    "division_before_multiplication": {
        "regex": r"/\s*\w+\s*\*\s*\w+",
        "desc": "Possible division before multiplication (precision loss)",
        "severity": "MEDIUM"
    },
    "hardcoded_gas": {
        "regex": r"\.gas\(\d+\)|\.call\{gas:\s*\d+",
        "desc": "Hardcoded gas limit",
        "severity": "LOW"
    },
    "send_usage": {
        "regex": r"\.send\s*\(",
        "desc": ".send() usage (2300 gas limit, silent failure)",
        "severity": "MEDIUM"
    },
    "unprotected_ether_withdrawal": {
        "regex": r"function\s+withdraw\s*\([^)]*\)\s*(public|external)\s*(?!.*onlyOwner|.*onlyAdmin|.*require\(msg\.sender)",
        "desc": "Withdraw function (check access control)",
        "severity": "HIGH"
    },
    "arbitrary_call_target": {
        "regex": r"address\s*\([^)]*\)\.call|\.call\{",
        "desc": "Arbitrary address call (check if target is user-controlled)",
        "severity": "HIGH"
    },
    "slot_collision_risk": {
        "regex": r"sstore\s*\(|sload\s*\(",
        "desc": "Direct storage access (slot collision risk)",
        "severity": "MEDIUM"
    },
}

def scan_file(filepath):
    try:
        with open(filepath, 'r', errors='ignore') as f:
            content = f.read()
    except:
        return []

    findings = []
    lines = content.split('\n')

    for name, pattern in PATTERNS.items():
        for i, line in enumerate(lines):
            if re.search(pattern["regex"], line):
                findings.append({
                    "file": os.path.basename(filepath),
                    "line": i + 1,
                    "pattern": name,
                    "severity": pattern["severity"],
                    "desc": pattern["desc"],
                    "code": line.strip()[:120]
                })

    return findings

def check_reentrancy_risk(filepath):
    """Check for functions that transfer ETH/tokens before state updates."""
    try:
        with open(filepath, 'r', errors='ignore') as f:
            content = f.read()
    except:
        return []

    findings = []
    # Look for .call{value:} or .transfer() NOT preceded by state update in same function
    # This is a simplified heuristic
    has_nonreentrant = "nonReentrant" in content or "ReentrancyGuard" in content
    has_eth_transfer = ".call{value:" in content or ".call.value(" in content or ".transfer(" in content
    has_state_after = False  # Would need deeper analysis

    if has_eth_transfer and not has_nonreentrant:
        findings.append({
            "file": os.path.basename(filepath),
            "line": 0,
            "pattern": "NO_REENTRANCY_GUARD",
            "severity": "HIGH",
            "desc": "Contract transfers ETH but has NO ReentrancyGuard",
            "code": ""
        })

    return findings

def main():
    all_findings = []

    for fname in sorted(os.listdir(SRC_DIR)):
        if not fname.endswith('.sol'):
            continue
        fpath = os.path.join(SRC_DIR, fname)
        findings = scan_file(fpath)
        findings += check_reentrancy_risk(fpath)
        all_findings.extend(findings)

    # Sort by severity
    severity_order = {"HIGH": 0, "MEDIUM": 1, "LOW": 2, "INFO": 3}
    all_findings.sort(key=lambda x: (severity_order.get(x["severity"], 4), x["file"]))

    # Output
    outpath = "/home/user/contracs/vuln_scan_results.txt"
    with open(outpath, 'w') as f:
        f.write("VULNERABILITY PATTERN SCAN RESULTS\n")
        f.write("="*100 + "\n\n")

        # HIGH severity only
        f.write("## HIGH SEVERITY FINDINGS\n")
        f.write("-"*100 + "\n")
        high_findings = [x for x in all_findings if x["severity"] == "HIGH"]
        for finding in high_findings:
            f.write(f"[{finding['severity']}] {finding['file']}:{finding['line']} - {finding['desc']}\n")
            if finding['code']:
                f.write(f"  CODE: {finding['code']}\n")
            f.write("\n")

        f.write(f"\n## SUMMARY\n")
        f.write(f"Total files scanned: {len([f for f in os.listdir(SRC_DIR) if f.endswith('.sol')])}\n")
        for sev in ["HIGH", "MEDIUM", "LOW", "INFO"]:
            count = sum(1 for x in all_findings if x["severity"] == sev)
            f.write(f"{sev}: {count}\n")

    # Print HIGH findings to stdout
    print(f"Scanned {len([f for f in os.listdir(SRC_DIR) if f.endswith('.sol')])} files")
    print(f"\nHIGH SEVERITY FINDINGS ({len(high_findings)}):")
    print("-"*80)

    # Group by file
    by_file = {}
    for f in high_findings:
        by_file.setdefault(f["file"], []).append(f)

    for fname, findings in sorted(by_file.items()):
        print(f"\n{fname}:")
        for f in findings:
            print(f"  L{f['line']:5d} [{f['pattern']}] {f['desc']}")
            if f['code'] and len(f['code']) < 100:
                print(f"         {f['code']}")

if __name__ == "__main__":
    main()
