# Hypotheses — Compound V3 USDT Market (XAUt Upgrade)

## Active Set

### H1: XAUt peg deviation arbitrage
- **Broken assumption**: XAUt market price = gold spot price
- **Sequence**: Buy discounted XAUt on DEX → deposit as collateral → borrow USDT at gold-spot valuation → profit = (gold_spot - xaut_market) * amount * borrowCF
- **Reasoning chain**: Chainlink reports XAU/USD (gold spot), not XAUt/USD (token market). If XAUt trades at discount to gold, borrower gets artificially high collateral value.
- **Value extraction**: From USDT suppliers (bad debt if XAUt stays depegged)
- **Feasibility**: Supply cap = 200 XAUt (~$1M). Even at 10% depeg, max profit = $70K (200 * 5039 * 0.10 * 0.70). Not enough to justify E3 investigation.
- **Status**: DEPRIORITIZED (bounded by supply cap)
- **Discriminator**: Not needed (arithmetic proves bounded impact)

### H2: XAUt blocklist DoS cascade
- **Broken assumption**: XAUt transfers always succeed
- **Sequence**: Tether blocks Comet → XAUt withdrawals/buyCollateral fail
- **Reasoning chain**: Only affects XAUt-specific operations. Other assets unaffected. Absorb still works (no transfer). Governance can pause XAUt operations.
- **Feasibility**: Requires Tether admin action. NOT attacker-exploitable.
- **Status**: REJECTED (not an attack vector)

### H3: Storage bitmap confusion across upgrade
- **Broken assumption**: Pre-upgrade bit 14 data could affect post-upgrade asset tracking
- **Sequence**: User had bit 14 set before upgrade → post-upgrade interpreted as XAUt collateral
- **Reasoning chain**: FALSIFIED. Before upgrade, numAssets=14 (indices 0-13). `updateAssetsIn` only sets bits for valid assets. Bit 14 was never written.
- **Status**: FALSIFIED

### H4: First-depositor XAUt manipulation
- **Broken assumption**: Zero-state creates exploitable boundary
- **Sequence**: First depositor manipulates initial state to gain advantage
- **Reasoning chain**: FALSIFIED. Comet tracks collateral as direct balance (no shares/exchange rate). First deposit is `0 + amount`, no division, no inflation attack.
- **Status**: FALSIFIED

### H5: XAUt decimal mismatch in price calculation
- **Broken assumption**: Price calculation mishandles 6-decimal token
- **Sequence**: Decimal mismatch causes over/under-valuation of XAUt collateral
- **Reasoning chain**: FALSIFIED. XAUt scale = 1e6, price feed = 8 decimals. Same as USDT (base token). mulPrice divides by fromScale correctly. WBTC (also 8 decimals) already validates this code path.
- **Status**: FALSIFIED

## Backlog (low priority)

### H6: Chainlink XAU/USD heartbeat staleness
- Gold feeds may have longer heartbeat intervals than crypto feeds
- Comet doesn't check staleness
- Low priority: gold is less volatile, and this affects all Comet markets equally

### H7: XAUt upgradeable proxy risk
- Tether can upgrade XAUt to any new logic
- Not an attacker exploit; governance dependency risk

## Exhausted Corridors
- Auth bypass: All privileged ops are immutable-gated (governor baked in bytecode). No writer paths.
- Reentrancy: nonReentrant on all state-modifying ops. XAUt has no hooks.
- Numeric overflow: Solidity 0.8.15 with safe math. Unchecked blocks verified.
- Cross-asset interference: Each collateral is independently tracked.
