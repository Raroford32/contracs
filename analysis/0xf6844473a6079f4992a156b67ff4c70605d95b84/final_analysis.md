# Final Analysis: FlyingTulipFund Token Paths
## Contract: 0xf6844473a6079f4992a156b67ff4c70605d95b84

---

## Executive Summary

After comprehensive analysis of all token paths, access controls, and cross-contract interactions, **no viable external exploit path exists** to extract USDC/USDT from this contract.

---

## Critical Finding: $6M Untracked USDC

### Discovery
| Metric | Amount |
|--------|--------|
| USDC Balance (on-chain) | $7,169,630.09 |
| USDC in Commit Tracking | $1,167,977.00 |
| **DISCREPANCY** | **$6,001,653.09** |

### Source of Discrepancy
- Single transfer of $6,001,620.82 from BitGo multisig (0xc6738424551bcb31fdcab85a9a2d0fff745c32cf)
- TX: 0x90ed507bf8d7d72897b1272ac904bca77cba220e21b72d497f12a14db68b8061
- Block: 24371461
- **NOT routed through commit()** - direct transfer

### Exploitation Status: NOT EXPLOITABLE
- `remit()` requires matching commit balance: `totals[user][option][token].commitSum - remitSum >= amount`
- No way to create commit entries without actual token deposit
- Only owner (2-of-N Gnosis Safe) can access via `transfer()`

---

## Complete Token Flow Map

```
                    ┌─────────────────────────────────────────────────┐
                    │          FlyingTulipFund                        │
                    │          $7.17M USDC + $301K USDT               │
                    └─────────────────────────────────────────────────┘
                                         │
         ┌───────────────────────────────┼───────────────────────────────┐
         │                               │                               │
         ▼                               ▼                               ▼
┌─────────────────┐            ┌─────────────────┐            ┌─────────────────┐
│   commit()      │            │    remit()      │            │   Owner Only    │
│  COMMIT_LEVEL   │            │   REMIT_LEVEL   │            │  transfer()     │
│                 │            │                 │            │   approve()     │
│  Tokens IN      │            │  Tokens OUT     │            │                 │
│  from User      │            │  to User        │            │  Tokens OUT     │
│                 │            │                 │            │  anywhere       │
│  Updates:       │            │  Requires:      │            │                 │
│  totals[].      │            │  commitSum -    │            │  Requires:      │
│  commitSum      │            │  remitSum >= amt│            │  2/N Safe sigs  │
└─────────────────┘            └─────────────────┘            └─────────────────┘
         │                               │                               │
         │                               │                               │
         ▼                               ▼                               ▼
   Tracked in                    Only to users               Untracked $6M
   totals mapping                with commit balance         accessible here
```

---

## Access Control Analysis

### Role: COMMIT_LEVEL (2)
- **Holder**: 0xc66c2f2ad297fcf1fd20a119d8a0e1cfa097e32b (EOA)
- **Capability**: Call commit() to accept user deposits
- **Token Flow**: FROM user TO contract
- **Risk**: Can only accept deposits, cannot extract

### Role: REMIT_LEVEL (4)
- **Holder**: 0xc66c2f2ad297fcf1fd20a119d8a0e1cfa097e32b (EOA)
- **Capability**: Call remit() to return user deposits
- **Token Flow**: FROM contract TO user (with commit balance only)
- **Risk**: Cannot redirect to arbitrary addresses

### Owner
- **Address**: 0x78c7ab5b34d779d1fee5928963ac426eb5a17b1d
- **Type**: Gnosis Safe (2/N multisig)
- **Capability**: transfer(), approve(), toggle(), grantRoles()
- **Token Flow**: Unrestricted but requires 2 signatures

---

## Attack Vectors Analyzed

### 1. External Attacker (No Access)
| Attack Path | Status | Reason |
|-------------|--------|--------|
| Call commit() | BLOCKED | Requires COMMIT_LEVEL role |
| Call remit() | BLOCKED | Requires REMIT_LEVEL role |
| Call transfer() | BLOCKED | Requires owner |
| Create fake commit | IMPOSSIBLE | commit() requires real transfer |

### 2. Role Holder Compromise
| Attack Path | Status | Reason |
|-------------|--------|--------|
| remit() to arbitrary address | BLOCKED | User must have commit balance |
| remit() more than committed | BLOCKED | Enforced by contract |
| Access untracked $6M | BLOCKED | No commit balance exists |

### 3. Cross-Contract Exploitation
| Attack Path | Status | Reason |
|-------------|--------|--------|
| investFor() drain | BLOCKED | Allowance to PutManager = 0 |
| PutManager callback | N/A | No reentrancy window |
| Safe transaction injection | BLOCKED | Requires 2 valid signatures |

### 4. Accounting Manipulation
| Attack Path | Status | Reason |
|-------------|--------|--------|
| Direct transfer + remit | BLOCKED | No commit balance created |
| Option/token confusion | BLOCKED | Proper separation in mapping |
| Overflow/underflow | BLOCKED | Solidity 0.8.30 checked math |

---

## Protocol Architecture

```
FlyingTulipFund (0xf684...)
       │
       ├── Owner: Gnosis Safe (0x78c7...) - 2/N threshold
       │
       ├── Role Holder: EOA (0xc66c...) - COMMIT + REMIT
       │
       ├── PutManager: Proxy (0xba49...)
       │         │
       │         └── Implementation (0x90ae...)
       │                   │
       │                   └── invest() requires:
       │                       - Token approval (currently 0)
       │                       - Whitelist proof
       │
       └── Token Balances:
           ├── USDC: $7,169,630.09
           │    ├── Tracked: $1,167,977.00 (16.3%)
           │    └── Untracked: $6,001,653.09 (83.7%)
           │
           └── USDT: $300,901.00
                └── Tracked: $300,901.00 (100%)
```

---

## Committed Users Summary

| Metric | USDC | USDT |
|--------|------|------|
| Total Commits | 225 | 334 |
| Total Committed | $1,167,977 | $300,901 |
| Largest Single | $800,000 | $42,400 |
| Unique Users | ~200 | ~300 |

### Top USDC Depositors
1. 0x708707234e5065f3887d0f9f8a1970013ebac926: $800,000
2. 0x48bf090e1f35ab9a7773d9a21214914d4c931dab: $50,000
3. 0xc1be3db5ba22d5bb5c769bb19ff9e8d6a113ccbc: $39,000

---

## Conclusion

### Finding Summary
1. **$6M USDC is untracked** - deposited directly without commit()
2. **No external exploit path** - all functions require privileged access
3. **Accounting is sound** - commit/remit properly enforces balances
4. **Role holder is EOA** - operational risk, not contract vulnerability

### Recommendations for Protocol
1. **Role Holder Security**: Convert EOA to contract/multisig
2. **Clarify $6M**: Document purpose of untracked funds
3. **Rate Limiting**: Consider time-delays on large remits
4. **Monitoring**: Alert on unusual remit patterns

### For Attackers
No viable attack path exists. The contract is well-designed with:
- Proper access control via Solady OwnableRoles
- Accurate accounting via totals mapping
- Owner protected by 2/N Gnosis Safe
- No reentrancy vectors
- No arithmetic issues (Solidity 0.8.30)

---

## Appendix: Key Addresses

| Role | Address | Type |
|------|---------|------|
| Contract | 0xf6844473a6079f4992a156b67ff4c70605d95b84 | FlyingTulipFund |
| Owner | 0x78c7ab5b34d779d1fee5928963ac426eb5a17b1d | Gnosis Safe 2/N |
| Role Holder | 0xc66c2f2ad297fcf1fd20a119d8a0e1cfa097e32b | EOA |
| PutManager | 0xba49d0ac42f4fba4e24a8677a22218a4df75ebaa | Proxy |
| $6M Source | 0xc6738424551bcb31fdcab85a9a2d0fff745c32cf | BitGo Multisig |
| USDC | 0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48 | Token |
| USDT | 0xdAC17F958D2ee523a2206206994597C13D831ec7 | Token |
