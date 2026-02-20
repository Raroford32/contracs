# Feasibility Ledger — Compound V3 USDT Market

## Hypothesis 1: XAUt blocklist DoS on liquidations
- **Description**: Tether blocks the Comet contract address; XAUt cannot be transferred out
- **Attacker tier**: N/A (requires Tether admin action, not an attacker exploit)
- **Ordering requirement**: None
- **Oracle requirement**: None
- **Liquidity requirement**: None
- **Feasibility**: NOT an attacker-exploitable vulnerability
- **Impact**: XAUt withdrawals and buyCollateral would fail, but absorb still works (internal accounting)
- **Conclusion**: Dependency risk accepted by governance, not an exploit

## Hypothesis 2: XAUt price oracle manipulation
- **Description**: Manipulate Chainlink XAU/USD feed to inflate XAUt collateral value
- **Attacker tier**: Would require Chainlink node operator compromise
- **Ordering requirement**: N/A
- **Oracle**: Chainlink `EACAggregatorProxy` (decentralized, multiple nodes)
- **Feasibility**: INFEASIBLE — Chainlink gold feeds use professional data providers
- **Conclusion**: Not viable

## Hypothesis 3: XAUt peg deviation
- **Description**: XAUt depegs from gold spot → Comet still prices at gold spot via XAU/USD feed
- **Attacker tier**: Public mempool (buy cheap XAUt, deposit as collateral, borrow against gold-spot valuation)
- **Ordering requirement**: None (no MEV needed)
- **Oracle**: Feed reports gold spot, not XAUt market price
- **Liquidity**: Need enough XAUt market liquidity to buy cheaply
- **Feasibility**: POSSIBLE in theory but:
  - Supply cap is 200 XAUt (~$1M) — limits exposure
  - XAUt is well-established (712K total supply, $3.5B market cap)
  - Significant depeg is unlikely for a fully-backed gold token
  - Even at 10% depeg, max extractable = 10% of $1M cap = $100K
- **Conclusion**: Theoretically possible but economically bounded by supply cap

## Hypothesis 4: Storage layout conflict after upgrade
- **Description**: New asset list causes storage conflict with old data
- **Attacker tier**: N/A (not exploitable)
- **Feasibility**: ANALYZED AND FALSIFIED
  - Old `assetsIn` bit 14 was never set (asset 14 didn't exist)
  - New `assetList` is a separate contract (doesn't modify Comet storage)
  - `totalsCollateral[XAUt]` starts at 0 (fresh mapping entry)
  - `userCollateral[anyone][XAUt]` starts at 0
- **Conclusion**: No storage conflict

## Hypothesis 5: Reentrancy via XAUt transfer hooks
- **Description**: XAUt transfer triggers callback that re-enters Comet
- **Attacker tier**: N/A
- **Feasibility**: FALSIFIED
  - XAUt uses standard OZ ERC20Upgradeable (no hooks, no ERC777)
  - All state-modifying Comet functions are `nonReentrant`
- **Conclusion**: Not viable

## Overall Assessment
No feasible attacker-exploitable vulnerability identified from this upgrade.
The CRITICAL_MISMATCH_RUSH alert is a FALSE POSITIVE for Compound's standard governance architecture.
