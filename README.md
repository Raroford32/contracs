# Complex Smart Contract Vulnerabilities Research

A comprehensive collection of **sophisticated, real-world smart contract exploits** demonstrating 2026-level attack vectors. These are NOT simple bugs - they represent complex, multi-step attacks requiring deep understanding of DeFi mechanics, MEV, protocol composition, and economic incentives.

## 🎯 What Makes These Exploits "Complex"?

### NOT Included (Too Simple):
- ❌ Basic access control issues
- ❌ Simple same-function reentrancy
- ❌ Integer overflows (Solidity 0.8+ handles this)
- ❌ Uninitialized variables
- ❌ tx.origin authentication

### ✅ Actually Included (Advanced):
- **Cross-function reentrancy** with state inconsistency exploitation
- **Flash loan governance attacks** requiring multi-contract coordination
- **Oracle manipulation** via protocol composition
- **ERC-4626 inflation attacks** exploiting share-based vaults
- **MEV extraction** (sandwich attacks, JIT liquidity, liquidations)
- **Protocol insolvency** via recursive borrowing and debt cascades
- **Governance takeovers** using flash loans and delegation
- **Interest rate manipulation** exploiting economic models
- **Systemic liquidation cascades** creating death spirals

## 📁 Repository Structure

```
contracs/
├── contracts/
│   ├── VulnerableVault.sol              # DeFi vault with 8 vulnerabilities
│   ├── VulnerableGovernance.sol         # Flash loan governance exploits
│   ├── VulnerableAMM.sol                # MEV exploitation vectors
│   └── AdvancedProtocolVulnerabilities.sol  # Protocol-level exploits
├── exploits/
│   └── VaultExploits.sol                # 6 different exploit contracts
├── VULNERABILITIES.md                   # Detailed vulnerability documentation
└── README.md                            # This file
```

## 🔥 Key Vulnerabilities Demonstrated

### 1. ERC-4626 Inflation Attack
**Complexity: Very High**
- First depositor manipulates share price via donation
- Subsequent depositors receive 0 shares due to rounding
- Attacker steals victim's entire deposit
- **Real-world impact:** Historical attacks stole $1M+

### 2. Cross-Function Reentrancy
**Complexity: Very High**
- NOT simple same-function reentrancy
- Exploits state reads during inconsistent state updates
- Requires understanding of execution flow across multiple functions
- **Real-world impact:** Cream Finance ($130M), Fei Protocol ($80M)

### 3. Oracle Manipulation via Flash Loan
**Complexity: Very High**
- Multi-step: Flash loan → manipulate price → borrow → profit
- Requires understanding of oracle mechanics and DeFi composability
- Atomic transaction eliminates capital risk
- **Real-world impact:** Mango Markets ($114M), Inverse Finance ($15M)

### 4. Flash Loan Governance Attack
**Complexity: Very High**
- Borrow 51% of tokens, vote, return in one transaction
- No snapshot mechanism exploited
- Immediate execution without timelock
- **Real-world impact:** Beanstalk ($182M)

### 5. MEV Sandwich Attacks
**Complexity: High**
- Frontrun victim swap to raise price
- Victim executes at worse price
- Backrun to capture profit
- **Real-world impact:** $1B+ extracted annually

### 6. JIT (Just-In-Time) Liquidity Attack
**Complexity: Very High**
- Add liquidity right before large swap
- Capture fees with minimal capital exposure
- Remove liquidity immediately after
- Advanced MEV strategy requiring precise timing

### 7. Protocol Insolvency via Recursive Borrowing
**Complexity: Very High**
- Create layered debt across multiple collateral types
- Total borrowed exceeds liquidation capacity
- Protocol becomes mathematically insolvent
- Systemic risk exploitation

### 8. Interest Rate Manipulation
**Complexity: High**
- Manipulate utilization ratio to force extreme rates
- Exploits economic model of lending protocol
- Other users pay artificially high interest

## 📚 Documentation

See **[VULNERABILITIES.md](VULNERABILITIES.md)** for detailed explanations of each vulnerability including:
- Attack vectors and step-by-step exploitation
- Why each vulnerability works
- Real-world examples and impact
- Code references
- Mitigation strategies

## ⚠️ WARNING

**DO NOT USE THESE CONTRACTS IN PRODUCTION**

These contracts are deliberately vulnerable and are for educational and security research purposes only. Deploying these contracts with real funds will result in loss of funds.

## 🎓 Educational Value

This repository is designed for:
- **Security researchers** studying advanced attack vectors
- **Smart contract auditors** learning complex vulnerability patterns
- **Protocol developers** understanding systemic risks
- **MEV researchers** exploring extraction strategies
- **DeFi builders** learning what NOT to do

## 💡 Why These Exploits Matter

### Historical Context
Between 2021-2024, over **$3 billion** was stolen from DeFi protocols through attacks similar to those demonstrated here:

- **Mango Markets:** $114M (Oracle manipulation)
- **Beanstalk:** $182M (Flash loan governance)
- **Cream Finance:** $130M (Reentrancy)
- **Inverse Finance:** $15M (Oracle manipulation)
- **Fei Protocol:** $80M (Reentrancy)

### 2026 Relevance
These attacks represent **current state-of-the-art** in smart contract exploitation:
- Flash loan infrastructure is mature and accessible
- MEV extraction is a $1B+ annual industry
- Cross-protocol attacks are increasingly common
- Require sophisticated understanding of protocol mechanics

## 🛠️ Technical Requirements

- **Solidity:** ^0.8.20
- **Understanding Required:**
  - DeFi protocol mechanics
  - EVM execution model
  - MEV and transaction ordering
  - Economic incentive structures
  - Protocol composability

## 🔬 Research Areas Covered

1. **Cross-Function Reentrancy & Read-Only Reentrancy**
2. **ERC-4626 Vault Security**
3. **Oracle Design & Manipulation**
4. **Governance Security & Flash Loan Attacks**
5. **MEV Extraction Strategies**
6. **Protocol Solvency & Systemic Risk**
7. **Interest Rate Model Exploitation**
8. **Liquidation Mechanism Security**

## 📖 Learning Path

1. **Start with:** `VULNERABILITIES.md` - Understand each vulnerability
2. **Study:** Contract code with inline comments explaining vulnerabilities
3. **Analyze:** Exploit contracts showing attack implementation
4. **Compare:** Real-world incidents mentioned in documentation
5. **Practice:** Think about mitigations and defenses

## 🔐 Security Best Practices

This repository demonstrates what NOT to do. For production contracts:
- ✅ Use OpenZeppelin's audited contracts
- ✅ Implement comprehensive reentrancy guards
- ✅ Use TWAP oracles, never spot price
- ✅ Add slippage protection to all trades
- ✅ Implement timelocks on governance
- ✅ Use snapshot voting mechanisms
- ✅ Get professional security audits
- ✅ Consider formal verification
- ✅ Implement circuit breakers
- ✅ Monitor for unusual activity

## 🤝 Contributing

This is a research repository. If you discover additional complex vulnerabilities or have improvements to the documentation, contributions are welcome.

## 📜 License

MIT License - For educational purposes only

## 🔗 Additional Resources

- **Damn Vulnerable DeFi:** Practice challenges
- **Ethernaut:** Security game
- **Immunefi:** Bug bounty platform
- **Trail of Bits:** Security research
- **Consensys Diligence:** Audit reports
- **Flashbots:** MEV research
- **Smart Contract Security Verification Standard (SCSVS)**

## ⚡ Quick Start

```bash
# Clone repository
git clone https://github.com/Raroford32/contracs.git

# Review documentation
cat VULNERABILITIES.md

# Explore vulnerable contracts
ls -la contracts/

# Study exploit implementations
ls -la exploits/
```

---

**Remember:** These are sophisticated attacks used by real adversaries. Understanding them is crucial for building secure DeFi protocols. Never underestimate the complexity of smart contract security.