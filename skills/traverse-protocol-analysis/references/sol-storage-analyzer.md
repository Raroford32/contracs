# sol-storage-analyzer - Storage Access Analyzer

Purpose:
- Map storage reads/writes for public and external functions.
- Highlight state mutation surfaces and optimization opportunities.

Installation:
```bash
brew install traverse
# or download binary
curl -sSfL -o /usr/local/bin/sol-storage-analyzer \
  https://github.com/calltrace/traverse/releases/latest/download/sol-storage-analyzer-macos-arm64
chmod +x /usr/local/bin/sol-storage-analyzer
```

Basic usage:
```bash
# Analyze single contract
sol-storage-analyzer Token.sol

# Analyze multiple contracts
sol-storage-analyzer contracts/Token.sol contracts/Vault.sol

# Process entire directory
sol-storage-analyzer src/

# Save analysis to file
sol-storage-analyzer contracts/ -o storage-report.md
```

Command line options:
Required arguments
- `<INPUT_PATHS>...`: One or more Solidity files or directories to analyze

Output options
- `-o, --output-file <OUTPUT_FILE>`: Output file for the analysis report (default: stdout)

Interface resolution
- `--bindings <BINDINGS>`: Path to binding.yaml file for interface resolution
- `--manifest-file <MANIFEST_FILE>`: Path to pre-generated manifest.yaml

General
- `-h, --help`: Show help information
- `-V, --version`: Show version information

Output format:
The tool generates a markdown report with detailed storage access information.

Example report structure:
```markdown
# Storage Access Analysis Report

## Summary
- **Total Contracts**: 3
- **Total Storage Variables**: 15
- **Functions with Storage Writes**: 8
- **Functions with Storage Reads Only**: 12

## Detailed Analysis

### ERC20 Token

| Function | Storage Reads | Storage Writes | Gas Estimate |
|----------|---------------|----------------|--------------|
| `transfer(address,uint256)` | `balances[from]`, `balances[to]` | `balances[from]`, `balances[to]` | ~50,000 |
| `balanceOf(address)` | `balances[account]` | - | ~2,000 |
| `approve(address,uint256)` | `allowances[owner][spender]` | `allowances[owner][spender]` | ~45,000 |
| `transferFrom(address,address,uint256)` | `balances[from]`, `balances[to]`, `allowances[owner][spender]` | `balances[from]`, `balances[to]`, `allowances[owner][spender]` | ~65,000 |

### Vault Contract

| Function | Storage Reads | Storage Writes | Gas Estimate |
|----------|---------------|----------------|--------------|
| `deposit(uint256)` | `balances[user]`, `totalDeposits` | `balances[user]`, `totalDeposits` | ~55,000 |
| `withdraw(uint256)` | `balances[user]`, `totalDeposits` | `balances[user]`, `totalDeposits` | ~60,000 |
| `getBalance(address)` | `balances[user]` | - | ~2,000 |

## Storage Variables
- `balances`: mapping(address => uint256)
- `allowances`: mapping(address => mapping(address => uint256))
- `totalSupply`: uint256
- `totalDeposits`: uint256
```
