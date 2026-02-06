# storage-trace - Storage Trace Comparator

Purpose:
- Compare storage access patterns between two functions.
- Detect upgrade/refactor drift in read/write surfaces.

Installation:
```bash
brew install traverse
# or download binary
curl -sSfL -o /usr/local/bin/storage-trace \
  https://github.com/calltrace/traverse/releases/latest/download/storage-trace-macos-arm64
chmod +x /usr/local/bin/storage-trace
```

Basic usage:
```bash
# Compare two functions in the same contract
storage-trace --func1 deposit --func2 depositFor contracts/Vault.sol

# Compare functions across different contracts
storage-trace --func1 TokenV1.transfer --func2 TokenV2.transfer contracts/

# Save comparison to file
storage-trace --func1 stake --func2 stakeFor contracts/*.sol -o comparison.md
```

Command line options:
Required arguments
- `--func1 <FUNC1>`: First function to compare (format: `functionName` or `Contract.functionName`)
- `--func2 <FUNC2>`: Second function to compare
- `<INPUT_PATHS>...`: Solidity files to analyze

Output options
- `-o, --output-file <OUTPUT_FILE>`: Output file for comparison report (default: stdout)

Interface resolution
- `--bindings <BINDINGS>`: Path to binding.yaml file for interface resolution
- `--manifest-file <MANIFEST_FILE>`: Path to pre-generated manifest.yaml

General
- `-h, --help`: Show help information
- `-V, --version`: Show version information

Output format (example):
```markdown
# Storage Trace Comparison: deposit vs depositFor

## Function 1 (deposit)
- **Reads**: [balance, totalSupply, lastUpdate]
- **Writes**: [balance, totalSupply, lastUpdate]

## Function 2 (depositFor)
- **Reads**: [balance, totalSupply, allowance, lastUpdate]
- **Writes**: [balance, totalSupply, lastUpdate, allowance]

## Differences

### Only in depositFor reads:
- allowance

### Only in depositFor writes:
- allowance

### Common reads:
- balance, totalSupply, lastUpdate

### Common writes:
- balance, totalSupply, lastUpdate

## Safety Analysis

### Compatible
- Both functions modify the same core storage variables
- No breaking changes to essential state

### Additional Access
- `depositFor` accesses additional `allowance` storage
- This may indicate different behavior or access control

### Recommendations
1. Ensure `depositFor` has proper access controls for allowance manipulation
2. Consider if additional storage access is intended
3. Test both functions with same input parameters

## Gas Impact
- Function 1 (deposit): ~45,000 gas
- Function 2 (depositFor): ~52,000 gas
- Difference: +7,000 gas (+15.6%)
```
