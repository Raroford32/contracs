# Value Flows — Compound V3 USDT Market

## Money Entry Points
1. **Supply base (USDT)**: Users deposit USDT to earn interest or repay borrows
2. **Supply collateral (XAUt + 14 others)**: Users deposit collateral to enable borrowing
3. **buyCollateral base payment**: Liquidation buyers pay USDT to purchase discounted collateral

## Money Exit Points
1. **Withdraw base (USDT)**: Users withdraw supplied USDT or borrow USDT
2. **Withdraw collateral**: Users withdraw their collateral
3. **buyCollateral collateral delivery**: Buyers receive discounted collateral
4. **withdrawReserves (governor)**: Protocol reserves withdrawn by governance

## Value Transforms

### Interest Accrual
- Supply: `presentValue = principal * baseSupplyIndex / BASE_INDEX_SCALE`
- Borrow: `presentValue = principal * baseBorrowIndex / BASE_INDEX_SCALE`
- Indices grow per block based on utilization rate and kink model
- Interest spreads: borrow rate > supply rate → protocol earns reserves

### Collateral Valuation
- `value = balance * oraclePrice / scale`
- Borrow check: `sum(collateral_value * borrowCF) >= debt_value`
- Liquidation check: `sum(collateral_value * liquidateCF) < debt_value`
- XAUt: `value = XAUt_balance * XAU_USD_price / 1e6`

### Liquidation Value Transform
- Absorb: seize all collateral, credit `value * liquidationFactor` toward debt
- XAUt liquidationFactor = 0.90 → protocol absorbs 10% haircut on seized XAUt
- buyCollateral: sell absorbed collateral at `storeFrontPriceFactor * (1 - liquidationFactor)` discount
- Discount for XAUt = 6% off oracle → protocol recovers ~94% of seized value

## Fee Extraction
- From borrowers to suppliers: interest rate spread
- From liquidated users: liquidation penalty (collateral seized at below-market value)
- Reserves accumulate from: interest spread + liquidation penalties - bad debt absorptions

## Actor Model

| Actor | Goal | Power | Dual-Role Risk |
|---|---|---|---|
| Supplier (USDT) | Earn interest | Supply/withdraw USDT | Could also be borrower |
| Borrower | Leverage/liquidity | Supply collateral + borrow USDT | Also supplier of collateral |
| Liquidator (absorber) | Earn liquidation incentive | Call `absorb` on underwater accounts | No conflict |
| Collateral buyer | Buy discounted assets | Call `buyCollateral` | Could also be absorber |
| Governor (Timelock) | Protocol management | Pause, reserves, approvals, upgrades | Trust assumption |
| Pause Guardian | Emergency circuit breaker | Can only pause | Limited scope |

## Solvency Equation
```
sum(user_collateral[i] * price[i]) * liquidateCF >= total_borrow * baseBorrowIndex / BASE_INDEX_SCALE
```

Or equivalently for the protocol:
```
USDT_balance >= total_supply_present_value - total_borrow_present_value + reserves
```

Where:
- `reserves = USDT_balance - total_supply_present_value + total_borrow_present_value`

## XAUt-Specific Value Flow
```
Entry: User transfers XAUt → Comet (supplyCollateral)
  → doTransferIn (balance-before/after pattern)
  → totalsCollateral[XAUt] += amount
  → userCollateral[user][XAUt] += amount
  → assetsIn bit 14 set

Transform: XAUt valued at gold spot via Chainlink XAU/USD
  → Contributes to borrow capacity at 70% CF
  → Liquidation threshold at 75% CF

Exit (normal): User withdraws XAUt (withdrawCollateral)
  → doTransferOut (direct transfer)
  → Collateralization re-checked

Exit (liquidation): absorb seizes XAUt
  → No token transfer (internal accounting)
  → Collateral held by protocol
  → buyCollateral: buyer pays USDT, receives XAUt at 6% discount
```
