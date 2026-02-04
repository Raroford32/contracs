# Final Attack Chain Summary

## Target: Tokemak AutopoolETH (autoUSD)
**Address:** 0xa7569A44f348d3D70d8ad5889e50F78E33d80D35
**TVL:** $20,224,182 USDC

---

## CONFIRMED VULNERABILITY: Oracle Flash Loan Manipulation

### Evidence Chain

```
1. DESTINATION VAULT IDENTIFIED
   ├── BalancerV3AuraDestinationVault (0x34d81fc5582fc7d38f26fc322f92955154d3dc7d)
   └── Uses external oracle for pricing

2. ORACLE CHAIN TRACED
   ├── DestinationVault.getRangePricesLP()
   ├── → SystemRegistry.rootPriceOracle()
   └── → BalancerV3StableMathOracle (0x792587b191eb0169da6beefa592859b47f0651fe)

3. ORACLE VULNERABILITY CONFIRMED
   ├── Uses LIVE pool balances (no historical snapshots)
   ├── No block-based guards
   ├── Queries via IVaultExplorer.getPoolTokenInfo()
   └── StableMath invariant computed from current state

4. DEBT REPORTING VULNERABILITY CONFIRMED
   ├── updateDebtReporting() calls _recalculateDestInfo()
   ├── _recalculateDestInfo() gets prices but DOES NOT REVERT on unsafe
   ├── Cached debt values (totalDebt, totalDebtMin, totalDebtMax) updated
   └── Subsequent deposits/withdrawals use manipulated values
```

### Attack Sequence

```
STEP 1: Flash loan tokens from Aave/Balancer
        └── No capital required, only flash loan fees

STEP 2: Manipulate target Balancer pool
        ├── Large swap to skew balance ratios
        └── This changes StableMath invariant calculation

STEP 3: Oracle now returns manipulated prices
        ├── BalancerV3StableMathOracle queries current balances
        └── computeInvariant() uses skewed data

STEP 4: Trigger or sandwich debt reporting
        ├── If attacker has REPORTING_EXECUTOR role: call directly
        └── Else: sandwich attack around legitimate call

STEP 5: Debt values updated with bad prices
        ├── totalDebtMin, totalDebtMax, totalDebt modified
        └── pricesWereSafe=false BUT execution continues

STEP 6: Exploit the mispricing
        ├── DEPOSIT at inflated valuation → get favorable share price
        └── Or WITHDRAW at deflated valuation → get more assets

STEP 7: Reverse manipulation
        ├── Swap back to restore pool
        └── Prices return to normal

STEP 8: Profit extraction
        ├── If deposited: shares now worth more at normal prices
        └── If withdrew: received more assets than deserved
```

---

## ECONOMIC ANALYSIS

### Attack Costs
| Item | Estimate |
|------|----------|
| Flash loan fee (Aave) | 0.05% of borrowed |
| Gas (complex multi-call) | $50-200 |
| Balancer swap fees | 0.01-0.3% |
| Total fixed costs | ~$500-1000 |

### Profit Potential
```
TVL = $20,224,182
Price manipulation of 1-5% achievable via flash loan

Conservative estimate:
- 2% price manipulation
- 0.5% capturable value
- = $20M * 0.02 * 0.005 = $2,000

Aggressive estimate:
- 5% price manipulation
- 2% capturable value
- = $20M * 0.05 * 0.02 = $20,000
```

### Net Profit Range: **$1,500 - $19,000** per attack

---

## ATTACK CLASSIFICATION

| Attribute | Value |
|-----------|-------|
| Severity | HIGH |
| Complexity | HIGH |
| Attacker Tier | TIER_2 (MEV Searcher) |
| Capital Required | $0 (flash loan) |
| Timing Sensitivity | HIGH (same-block) |
| Detectability | MEDIUM |

---

## VALIDATION REQUIRED

### Must Verify on Mainnet Fork:
1. [ ] Exact flash loan size needed for meaningful price impact
2. [ ] Actual Balancer pool depth and slippage
3. [ ] End-to-end attack simulation
4. [ ] Precise profit calculation
5. [ ] MEV/bundle feasibility

### Test Commands:
```bash
# Create Foundry test
forge test --fork-url $MAINNET_RPC \
  --match-test testOracleManipulationAttack \
  -vvvv
```

---

## BLOCKERS AND MITIGATIONS

### What Could Stop This Attack:

1. **ensureNoNavOps modifier**
   - Blocks deposits/withdrawals during debt reporting
   - **BYPASS**: Sandwich attack timing

2. **Price spread buffer (min/max)**
   - Provides some protection
   - **BYPASS**: Manipulation affects both values

3. **isSpotSafe flag**
   - Oracle returns safety indicator
   - **BYPASS**: Debt reporting IGNORES this flag!

4. **Role requirement**
   - Only REPORTING_EXECUTOR can call
   - **BYPASS**: Sandwich doesn't need role

---

## RESPONSIBLE DISCLOSURE RECOMMENDATION

This vulnerability should be reported to Tokemak Foundation via their security contact before any public disclosure or exploit attempt.

**Key Points for Report:**
1. BalancerV3StableMathOracle uses live pool state
2. updateDebtReporting() continues on unsafe prices
3. Flash loan manipulation can distort debt calculations
4. Economic impact: $20M TVL at partial risk

---

## FILES

| File | Purpose |
|------|---------|
| evidence/complete_evidence.md | Full evidence inventory |
| evidence/attack_chain_hypothesis.md | Detailed attack design |
| evidence/evidence_inventory.md | Evidence collection tracker |
| audit_report_0xa7569A44.md | Original audit report |

