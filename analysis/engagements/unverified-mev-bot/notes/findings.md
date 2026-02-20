# Analysis — Unverified MEV Bot (0xa462d9...)

## Summary

**Alert**: CRITICAL_MISMATCH_RUSH
**Resolution**: FALSE POSITIVE
**Reason**: Fresh deployment of a private MEV/DEX trading bot, not an upgrade of an existing contract.

## Contract Architecture

```
EOA (bot operator: 0xc54b77...)
  → Proxy (UUPS: 0xa462d9...)
    → Implementation (0xc3c7d1...) [DELEGATECALL]
      → Logic contract (0xb7dce6...) [DELEGATECALL]
        → External DEX calls (UniV2/UniV3/Core DEX)
```

### Storage Layout (proxy context)
| Slot | Value | Description |
|------|-------|-------------|
| 0 | 0xc54b77... | Bot operator address |
| 1 | 0xb7dce6... | Logic contract (trade routing) |
| 2 | 0xe0e0e0... | Core DEX contract |
| 3 | 0x2260fa... | WBTC token address |
| EIP-1967 | 0xc3c7d1... | UUPS implementation |

### Key Addresses
- **Owner** (Ownable): `0xe3488b445b4c198c696600ff66d97560ab68cf4c`
- **Bot operator**: `0xc54b77b28ee4d18cd3d93991f08b79bc85c71097`
- **Proxy deployer**: `0xecabaf897fe72beb1e393dba01ecf63005b875c5`
- **TVL**: 431 WETH (~$848K)

## Why This Is a False Positive

### 1. "Upgrade" is actually a fresh deployment
The `upgrade_tx` (0x10658160...) has `to: null`, meaning it's a **contract creation** transaction — the proxy was being deployed for the first time, not upgraded. There was no pre-existing proxy at this address.

### 2. Unverified source is expected for MEV bots
MEV bots intentionally keep source unverified to protect proprietary trading strategies. This is standard practice.

### 3. Same-block impl/proxy deployment is normal
For a fresh deployment, deploying the implementation and proxy in the same block (or close) is the standard pattern. The `hours_impl_to_upgrade: 0` flag is meaningless for new deployments.

## Security Analysis

### Auth Bypass Testing (All BLOCKED)

| Attack Vector | Result | Evidence |
|---|---|---|
| `withdraw()` from random | NO-OP — returns success but transfers nothing | No WETH transfer in callTracer; state diff shows only nonce change |
| `upgradeToAndCall()` from random | REVERTS: `OwnableUnauthorizedAccount` | Properly gated by OZ Ownable |
| `initialize()` on impl | REVERTS: `InvalidInitialization` | Already initialized |
| `upgradeToAndCall()` on impl directly | REVERTS: `UUPSUnauthorizedCallContext` | Proper UUPS guard |
| Trade function (0x44471415) from random | REVERTS | Hardcoded operator check in logic bytecode |
| `payCallback()` from non-Core | REVERTS: `"not core"` | msg.sender check against stored Core address |
| `payCallback()` from Core | REVERTS: `"no debt"` | Requires active lock/flash loan sequence |
| All unknown selectors from random | REVERT or NO-OP | Owner-gated or getter functions |

### Logic Contract Bytecode Analysis

The logic contract at `0xb7dce6...` has a dual-dispatch architecture:

```
Entry point:
  PUSH20 <bot_operator_addr>  // 0xc54b77...
  CALLER
  EQ
  ISZERO
  PUSH2 0x0701               // Jump to standard dispatch
  JUMPI

  // Bot operator path:
  CALLDATALOAD >> 224         // Extract selector
  TIMESTAMP
  EQ                          // selector == block.timestamp (MEV protection!)
  ...                         // Execute trade with timestamp-based selector

0x0701:
  // Standard function dispatch (withdraw, deposit, etc.)
  // No SLOAD/SSTORE — pure routing via external CALLs
```

**Key insight**: The trade function uses `block.timestamp` as the function selector. This is a classic MEV bot anti-frontrunning technique — the calldata selector changes every block, making it impossible to construct a valid trade call without knowing the exact block it will land in.

### WETH Flow Pattern

The bot executes multi-hop DEX arbitrage:
- Deposits/holds WETH as working capital
- Swaps across UniV2, UniV3, and a custom Core DEX
- Typical trade: WETH → Token → USDC → WETH (triangular arb)
- Approves WETH to DEX routers dynamically (approve-before-swap pattern)
- Current WETH approvals are all at 0 (reset after each trade)

### Remaining Contracts in Triage

| Proxy | Name | TVL | Status |
|---|---|---|---|
| 0xdd7fa0... | OperatorStakingRenameTokenV2 | $38K | Chainlink staking — likely false positive |
| 0xb8ecac... | UNVERIFIED | $16K | Low value |
| 0x4b1d53... | UNVERIFIED | $9K | Low value |
| 0x3ca208... | ChimpStrategy | $1.4K | Low value strategy |
| 0xe789de... | StreetStrategy | $60 | Negligible |
| 0xac0ac0... | UNVERIFIED | $0 | Empty |

All remaining contracts have low TVL (<$38K) and are unlikely to be worth deep analysis.

## Conclusion

Both analyzed contracts from the CRITICAL_MISMATCH_RUSH list are **FALSE POSITIVES**:

1. **Compound V3 USDT Market** (0x3afdc9...): Known blue-chip protocol adding XAUt collateral. Zero code diff between old/new implementation. Standard governance execution.

2. **Unverified MEV Bot** (0xa462d9...): Fresh deployment (not upgrade) of a private trading bot. All auth checks are properly implemented. High TVL but properly secured with hardcoded operator checks, OZ Ownable, UUPS guards, and callback gating.

The remaining 6 contracts all have TVL < $38K and do not warrant deep investigation.
