# Complex Smart Contract Vulnerabilities (2026 Level)

This repository contains sophisticated, real-world smart contract vulnerabilities that require deep understanding of DeFi mechanics, MEV, and protocol composition. These are NOT simple bugs - they are complex exploits that demonstrate advanced attack vectors.

## ⚠️ WARNING
**DO NOT USE THESE CONTRACTS IN PRODUCTION**  
These contracts are deliberately vulnerable and are for educational purposes only.

---

## Table of Contents
1. [Vulnerable Vault - Multi-Vector DeFi Protocol](#1-vulnerable-vault)
2. [Vulnerable Governance - Flash Loan Attacks](#2-vulnerable-governance)
3. [Vulnerable AMM - MEV Exploitation](#3-vulnerable-amm)

---

## 1. Vulnerable Vault

**File:** `contracts/VulnerableVault.sol`  
**Exploits:** `exploits/VaultExploits.sol`

### Vulnerability 1: ERC-4626 Inflation Attack

**Complexity:** High - Requires understanding of share-based vault mechanics

**Attack Vector:**
```
1. Attacker deposits 1 wei → receives 1 share
2. Attacker directly transfers 10,000 ETH to vault (donation)
3. Now: 1 share = 10,000 ETH + 1 wei
4. Victim deposits 9,999 ETH
5. Victim receives: (9,999 * 1) / 10,000 = 0 shares (rounds down!)
6. Attacker withdraws 1 share → gets ~20,000 ETH
```

**Why It Works:**
- First deposit sets initial share ratio
- Direct transfers inflate share value
- Integer division rounds down
- Subsequent depositors lose funds to rounding

**Real-World Impact:**
- Yearn Finance vaults use similar mechanisms
- Requires careful minimum deposit checks
- $1M+ stolen in historical attacks

**Code Reference:**
```solidity
// Vulnerable code in deposit()
if (totalShares == 0) {
    shares = assets;  // No minimum shares enforced
} else {
    shares = (assets * totalShares) / totalAssets;  // Rounds down
}
```

**Exploit Contract:** `Exploit1_InflationAttack`

---

### Vulnerability 2: Cross-Function Reentrancy with State Inconsistency

**Complexity:** Very High - Multi-function, multi-step attack

**Attack Vector:**
```
1. User calls withdraw(shares)
2. Contract decrements shares
3. Contract calls asset.transfer() to user
4. In receive(), attacker calls borrow()
5. getCollateralValue() reads shareBalances
6. BUT: withdraw hasn't finished updating all state
7. Attacker borrows based on STALE collateral value
8. withdraw() completes
9. Attacker now undercollateralized with excess funds
```

**Why It Works:**
- Not same-function reentrancy (harder to detect)
- Exploits state read during inconsistent state
- View functions appear "safe" but can be exploited
- Requires precise timing and understanding of execution flow

**Real-World Impact:**
- Cream Finance: $130M stolen (similar pattern)
- Fei Protocol: $80M exploit
- Read-only reentrancy is often overlooked

**Code Reference:**
```solidity
// In withdraw():
shareBalances[msg.sender] -= shares;  // State updated
totalShares -= shares;
asset.transfer(msg.sender, assets);    // External call - REENTRANCY HERE

// In borrow():
uint256 collateralValue = getCollateralValue(msg.sender);  // Reads stale state!
```

**Exploit Contract:** `Exploit2_CrossFunctionReentrancy`

---

### Vulnerability 3: Oracle Manipulation via Flash Loan

**Complexity:** Very High - Requires understanding of oracle mechanics and DeFi composability

**Attack Vector:**
```
1. Take flash loan of 100,000 ETH
2. Swap large amount on DEX to manipulate price oracle upward
3. Deposit collateral (now valued at inflated price)
4. Borrow maximum based on manipulated price
5. Let price return to normal (or reverse swap)
6. Position now undercollateralized
7. Repay flash loan
8. Keep borrowed funds as profit
```

**Why It Works:**
- Spot price oracles can be manipulated in single transaction
- Flash loans provide capital without collateral
- Atomic transaction means no capital risk
- Protocol reads manipulated price

**Real-World Impact:**
- Mango Markets: $114M stolen
- Inverse Finance: $15M
- Dozens of similar attacks in 2021-2023

**Code Reference:**
```solidity
// Vulnerable oracle:
function getPrice(address token) external view returns (uint256) {
    return prices[token];  // Spot price - manipulatable!
}

// Used in collateral calculation:
uint256 price = oracle.getPrice(address(asset));
return userAssets * price / 1e18;
```

**Exploit Contract:** `Exploit3_OracleManipulation`

---

### Vulnerability 4: MEV-Exploitable Liquidations

**Complexity:** High - Requires understanding of MEV and transaction ordering

**Attack Vector:**
```
1. Monitor mempool for liquidatable positions
2. When threshold crossed, submit liquidation with higher gas
3. Frontrun other liquidators
4. Capture fixed 10% bonus
5. No slippage protection means guaranteed profit
```

**Why It Works:**
- Liquidations are predictable (threshold-based)
- Fixed bonus creates MEV opportunity
- No partial liquidation (all-or-nothing)
- Highest gas price wins

**Real-World Impact:**
- $1B+ in MEV extracted annually
- Liquidation bots dominate this space
- Protocol users pay the MEV tax

**Code Reference:**
```solidity
// Fixed bonus creates MEV:
uint256 collateralToSeize = (liquidationAmount * LIQUIDATION_BONUS) / 100;

// No slippage protection
// No partial liquidation
```

**Exploit Contract:** `Exploit6_MEVLiquidation`

---

### Vulnerability 5: Precision Loss in Complex Calculations

**Complexity:** Medium-High - Requires understanding of Solidity math

**Attack Vector:**
```
1. Make many small deposits/withdrawals
2. Each operation loses precision due to division
3. Accumulate dust from rounding errors
4. After thousands of iterations, dust becomes significant
```

**Why It Works:**
- Division before multiplication loses precision
- Solidity has no floating point
- Rounding errors accumulate
- Can be exploited systematically

**Code Reference:**
```solidity
// Vulnerable calculation:
shares = (assets * totalShares) / totalAssets;  // Division loses precision
```

**Exploit Contract:** `Exploit5_PrecisionLoss`

---

## 2. Vulnerable Governance

**File:** `contracts/VulnerableGovernance.sol`

### Vulnerability 6: Flash Loan Governance Attack

**Complexity:** Very High - Multi-contract, multi-step attack

**Attack Vector:**
```
1. Take flash loan of 51% of governance tokens
2. Delegate voting power to self
3. Vote on malicious proposal
4. Proposal passes due to 51% voting power
5. Return tokens to flash loan
6. Proposal executes (no timelock)
7. Attacker controls protocol
```

**Why It Works:**
- No snapshot mechanism (voting power at vote time)
- No token lock period
- No timelock before execution
- Flash loan enables temporary 51% attack

**Real-World Impact:**
- Beanstalk: $182M stolen via flash loan governance
- Build Finance: Governance takeover
- Multiple DAOs vulnerable

**Code Reference:**
```solidity
// Vulnerable voting:
function vote(uint256 proposalId, bool support) external {
    uint256 votes = balanceOf[msg.sender];  // Current balance, not snapshot!
    // Can use flash-loaned tokens
}

// No timelock:
function execute(uint256 proposalId) external {
    require(proposal.forVotes > proposal.againstVotes);
    proposal.target.call(proposal.data);  // Executes immediately!
}
```

**Exploit Contract:** `GovernanceExploit`

---

### Vulnerability 7: Delegation Loop DoS

**Complexity:** Medium - Creative attack on delegation logic

**Attack Vector:**
```
1. Create accounts A, B, C
2. A delegates to B
3. B delegates to C
4. C delegates to A
5. Trying to calculate votes causes infinite loop
6. Governance frozen (DoS)
```

**Why It Works:**
- No cycle detection in delegation chain
- Recursive vote calculation
- Gas limit exceeded when trying to resolve

**Code Reference:**
```solidity
// No cycle detection:
function delegate(address delegatee) external {
    delegates[msg.sender] = delegatee;
    // Can create A->B->C->A loop
}
```

---

### Vulnerability 8: No Quorum Requirement

**Complexity:** Low-Medium - But dangerous in practice

**Attack Vector:**
```
1. Wait for off-hours (low participation)
2. Propose malicious action
3. Vote with minimal tokens
4. Proposal passes (1 vote for, 0 against)
5. Execute immediately
```

**Why It Works:**
- No minimum participation required
- Off-hours attacks possible
- Low token requirement to propose

---

## 3. Vulnerable AMM

**File:** `contracts/VulnerableAMM.sol`

### Vulnerability 9: Sandwich Attack

**Complexity:** High - Requires MEV infrastructure

**Attack Vector:**
```
1. MEV bot monitors mempool
2. Sees user's large swap transaction
3. Frontruns: Swaps in same direction (raises price)
4. User's swap executes at worse price
5. Backruns: Swaps in opposite direction
6. Bot profits from price difference
```

**Why It Works:**
- No slippage protection
- Predictable price impact
- Transaction ordering manipulation
- All happens in single block

**Real-World Impact:**
- $1B+ extracted via sandwich attacks
- ~5% of all DEX volume affected
- Major problem for DeFi users

**Code Reference:**
```solidity
// No slippage protection:
function swap(uint256 amount0In, uint256 amount1In, 
              uint256 amount0Out, uint256 amount1Out) external {
    // No minAmountOut parameter
    // No deadline check
}
```

**Exploit Contract:** `SandwichAttackBot`

---

### Vulnerability 10: Just-In-Time (JIT) Liquidity

**Complexity:** Very High - Advanced MEV strategy

**Attack Vector:**
```
1. Bot sees large swap in mempool
2. Frontruns: Adds liquidity
3. Large swap executes, paying fees
4. Bot captures most fees (largest LP momentarily)
5. Backruns: Removes liquidity
6. Profit with minimal capital exposure
```

**Why It Works:**
- Can add/remove liquidity in same block as swap
- Fees distributed proportionally
- No minimum liquidity time
- Capital efficiency for MEV bots

**Real-World Impact:**
- Uniswap V3 especially vulnerable
- Reduces LP profitability
- Sophisticated MEV strategy

**Exploit Contract:** `JITLiquidityAttack`

---

### Vulnerability 11: Cross-DEX Arbitrage

**Complexity:** Medium-High - Requires monitoring multiple DEXes

**Attack Vector:**
```
1. Monitor prices across multiple AMMs
2. When price difference detected:
   - Buy from cheaper AMM
   - Sell to expensive AMM
3. Risk-free profit in single transaction
```

**Why It Works:**
- Price updates aren't instant across DEXes
- Atomic transactions eliminate risk
- Arbitrage is necessary but extractive

**Exploit Contract:** `CrossDEXArbitrage`

---

## Why These Vulnerabilities Matter

### Sophistication Level
These are not simple bugs like:
- ❌ Missing access control on one function
- ❌ Integer overflow (prevented in Solidity 0.8+)
- ❌ Simple reentrancy on same function

These are complex exploits requiring:
- ✅ Understanding of protocol mechanics
- ✅ Multi-step attack coordination
- ✅ Knowledge of MEV and transaction ordering
- ✅ DeFi composability understanding
- ✅ Economic incentive analysis

### Real-World Relevance
- **$3B+** stolen from DeFi protocols (2021-2024)
- **Top protocols affected:** Mango Markets, Beanstalk, Cream Finance, Inverse Finance
- **MEV extraction:** $1B+ annually
- **Active exploit ecosystem:** Profitable for attackers

### 2026 Relevance
These attacks represent current state-of-the-art:
- Flash loan integration is standard
- MEV infrastructure is mature
- Cross-protocol attacks are common
- Require sophisticated understanding

---

## Testing the Exploits

Each exploit contract can be deployed and tested:

```bash
# Setup (if using Foundry)
forge init
forge install

# Run specific exploit test
forge test --match-contract Exploit1_InflationAttack -vvv

# Run all tests
forge test -vvv
```

---

## Mitigations

### For ERC-4626 Inflation:
- Enforce minimum share amount
- Lock initial liquidity
- Use virtual reserves

### For Reentrancy:
- Use checks-effects-interactions pattern
- Implement reentrancy guards on ALL functions
- Use OpenZeppelin's ReentrancyGuard

### For Oracle Manipulation:
- Use TWAP (Time-Weighted Average Price)
- Multiple oracle sources
- Chainlink or other decentralized oracles

### For MEV:
- Implement slippage protection
- Use private mempools (Flashbots)
- Time-weighted liquidity rewards

### For Governance:
- Snapshot mechanism for voting power
- Timelock before execution
- Quorum requirements
- Minimum token lock period

---

## References

1. **Immunefi Reports:** Top DeFi hacks analysis
2. **Flashbots Research:** MEV taxonomy
3. **Consensys Diligence:** Smart contract best practices
4. **Trail of Bits:** Security patterns
5. **OpenZeppelin:** Security audits and patterns

---

## Learning Resources

- **Damn Vulnerable DeFi:** Practice challenges
- **Ethernaut:** Smart contract security game
- **Secureum:** Security training bootcamp
- **MEV University:** MEV education
- **Smart Contract Security Verification Standard:** SCSVS

---

## License

MIT - For educational purposes only

## Disclaimer

These contracts are intentionally vulnerable. Never use them with real funds. Always audit smart contracts before deployment.
