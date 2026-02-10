# Quick Reference: Complex Vulnerability Patterns

## Vulnerability Identification Guide

### 🔴 CRITICAL (Requires Immediate Attention)

#### 1. Cross-Function Reentrancy
**Pattern:**
```solidity
function withdraw() {
    shares[msg.sender] -= amount;  // State update
    token.transfer(msg.sender, amount);  // External call - CAN REENTER OTHER FUNCTIONS
}

function borrow() {
    collateral = getCollateral(msg.sender);  // READS STALE STATE
    // If called during withdraw, reads old share value
}
```

**Detection:** Look for external calls that can reenter view/read functions

---

#### 2. ERC-4626 Inflation Attack
**Pattern:**
```solidity
if (totalShares == 0) {
    shares = assets;  // NO MINIMUM CHECK
} else {
    shares = (assets * totalShares) / totalAssets;  // ROUNDS DOWN
}
```

**Detection:** First deposit + donation + rounding = vulnerability

---

#### 3. Oracle Manipulation
**Pattern:**
```solidity
function getPrice() view returns (uint256) {
    return reserve1 / reserve0;  // SPOT PRICE - MANIPULATABLE
}
```

**Detection:** Any spot price oracle without TWAP

---

#### 4. Flash Loan Governance
**Pattern:**
```solidity
function vote() {
    votes = token.balanceOf(msg.sender);  // CURRENT BALANCE, NOT SNAPSHOT
    proposals[id].votes += votes;
}

function execute() {
    require(votes > threshold);
    target.call(data);  // IMMEDIATE EXECUTION, NO TIMELOCK
}
```

**Detection:** No snapshot + no timelock = vulnerable

---

### 🟠 HIGH (Complex Exploitation Required)

#### 5. MEV Sandwich Attack
**Pattern:**
```solidity
function swap(uint amountIn, uint amountOut) {
    // NO minAmountOut CHECK
    // NO deadline CHECK
    // Transaction can be sandwiched
}
```

**Detection:** Missing slippage protection

---

#### 6. JIT Liquidity
**Pattern:**
```solidity
function addLiquidity() { /* no time lock */ }
function swap() { /* pays fees to LPs */ }
function removeLiquidity() { /* can be same block */ }
```

**Detection:** Add/remove liquidity + swap in same block

---

#### 7. Protocol Insolvency
**Pattern:**
```solidity
function borrow() {
    // User can supply borrowed assets as collateral
    // Creates recursive debt layers
    // totalBorrowed > liquidationCapacity
}
```

**Detection:** Recursive collateral without checks

---

## Attack Complexity Matrix

| Vulnerability | Complexity | Capital Required | Success Rate | Real-World $ |
|--------------|------------|------------------|--------------|--------------|
| ERC-4626 Inflation | Very High | Low ($1K-$10K) | High | $1M+ |
| Cross-Function Reentrancy | Very High | Medium | Medium | $200M+ |
| Oracle Manipulation | Very High | High (flash loan) | High | $150M+ |
| Flash Loan Governance | Very High | High (flash loan) | High | $180M+ |
| MEV Sandwich | High | Medium | Very High | $1B+ annual |
| JIT Liquidity | Very High | Low-Medium | High | Unknown |
| Protocol Insolvency | Very High | Medium | Medium | Case-dependent |
| Interest Rate Manipulation | High | High | Medium | Case-dependent |

## Exploitation Requirements

### Minimal (Script Kiddie)
- ❌ None in this repository
- These are advanced attacks only

### Intermediate
- Basic understanding of Solidity
- Access to testing environment
- Ability to deploy contracts

### Advanced (Required for Most Attacks)
- ✅ Deep DeFi protocol knowledge
- ✅ Understanding of MEV
- ✅ Flash loan integration skills
- ✅ Transaction ordering knowledge
- ✅ Economic incentive analysis

### Expert (Required for Novel Attacks)
- ✅ Protocol composition understanding
- ✅ Systemic risk analysis
- ✅ Custom MEV bot development
- ✅ Multi-protocol orchestration
- ✅ Advanced testing infrastructure

## Defense Checklist

### For Vault Protocols
- [ ] Enforce minimum share amount
- [ ] Lock initial liquidity
- [ ] Use checks-effects-interactions
- [ ] Implement reentrancy guards on ALL functions
- [ ] Add withdrawal delays

### For Lending Protocols
- [ ] Use TWAP oracles
- [ ] Prevent recursive borrowing
- [ ] Implement circuit breakers
- [ ] Add interest rate caps
- [ ] Limit liquidation sizes

### For Governance
- [ ] Implement snapshot voting
- [ ] Add minimum timelock (48h+)
- [ ] Require quorum
- [ ] Token lock periods
- [ ] Delegation limits

### For AMMs
- [ ] Mandatory slippage protection
- [ ] Deadline parameters
- [ ] Minimum liquidity lock
- [ ] TWAP for price feeds
- [ ] MEV protection (Flashbots)

## Testing Priorities

1. **Cross-function reentrancy:** Test ALL function combinations
2. **First deposit:** Always test with 1 wei deposits
3. **Oracle manipulation:** Test with flash loan scenarios
4. **Governance:** Test with 51% attack vectors
5. **Edge cases:** Zero values, max values, rounding

## Common Misconceptions

❌ "Checks-effects-interactions prevents all reentrancy"
→ Only prevents same-function reentrancy

❌ "Reentrancy guard makes contract safe"
→ Only if applied to ALL vulnerable functions

❌ "Using Chainlink oracle is always safe"
→ Must check staleness, multiple sources

❌ "Timelock prevents all governance attacks"
→ Need snapshot voting too

❌ "Can't be exploited without my private keys"
→ These are economic/logic exploits, not access control

## Real-World Incident Response

If you discover any of these vulnerabilities:

1. **DO NOT** disclose publicly immediately
2. **DO** contact protocol team privately
3. **DO** use bug bounty programs (Immunefi, etc.)
4. **DO** document proof of concept
5. **DO** allow reasonable response time (30-90 days)
6. **DO NOT** exploit for personal gain

## Further Study

- **Secureum Bootcamp:** Comprehensive security training
- **Damn Vulnerable DeFi:** Hands-on challenges
- **MEV University:** MEV-specific education
- **Trail of Bits Blog:** Advanced research
- **Immunefi Reports:** Real incident analysis

---

**Last Updated:** 2026-01
**Threat Level:** These patterns are actively exploited
**Recommended Action:** Audit all protocols for these issues
