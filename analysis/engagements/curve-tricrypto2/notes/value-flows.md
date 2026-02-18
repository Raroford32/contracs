# Value Flows — Curve Tricrypto2

## Money Entry Points
1. **add_liquidity**: Users deposit USDT/WBTC/WETH → receive LP tokens
2. **exchange (dx in)**: Traders send one token to swap for another

## Money Exit Points
1. **remove_liquidity**: LP holders burn LP → receive proportional USDT/WBTC/WETH
2. **remove_liquidity_one_coin**: LP holders burn LP → receive single token
3. **exchange (dy out)**: Traders receive output token from swap
4. **claim_admin_fees**: Admin fees accumulated → minted as LP tokens to fee receiver

## Value Transforms
1. **Swap pricing**: Newton's method solver computes dy from dx using CryptoSwap invariant
   - D (invariant) computed from balances + A + gamma
   - Price internally scaled to USDT denomination via price_scale
   - Fee applied: fee = mid_fee * (1 - g) + out_fee * g where g = fee_gamma / (fee_gamma + (1 - K))
   - K measures how balanced the pool is
2. **LP token pricing**: virtual_price = D / totalSupply
   - D computed from internal balances (after fee accumulation)
   - Monotonically increasing (in theory)
3. **Price oracle (EMA)**: Exponential moving average of last_prices
   - Used by external protocols to price assets
   - ma_half_time controls EMA decay speed
4. **Price scale adjustment**: Internal prices adjusted towards oracle prices
   - adjustment_step controls step size
   - allowed_extra_profit controls profit threshold for adjustment

## Fee Extraction
- **Swap fees**: fee applied to dy, split between:
  - LP holders (fee stays in pool, increases virtual_price)
  - Admin (admin_fee fraction, accumulated as xcp_profit)
- **Admin fee distribution**: claim_admin_fees mints LP tokens to admin_fee_receiver
  - Amount = (xcp_profit - xcp_profit_a) * totalSupply / (2 * xcp_profit) * admin_fee / FEE_DENOMINATOR

## Actor Model
| Actor | Role | Power | Conflict |
|-------|------|-------|----------|
| LP Provider | Deposit/withdraw | Earns swap fees, bears IL | Can sandwich own deposits |
| Trader | Swap | Sets last_prices, moves oracle | Can manipulate price_oracle via trades |
| Owner | Admin params | Change fees, A, gamma, kill | Can kill pool, change parameters |
| Fee Receiver | Collect fees | claim_admin_fees (permissionless) | None direct |
| External Oracle Consumer | Read price_oracle | Depends on pool price for decisions | Flash loan price manipulation |
| Liquidator/Arb | Arbitrage | Corrects prices, earns spread | Benefits from pool imbalance |

## Dual-Role Conflicts
1. **LP + Trader**: Same entity can deposit, trade to move prices, then withdraw
2. **Oracle Consumer + Trader**: Entity reading price_oracle can also move it via trades
3. **LP + Oracle Consumer**: Deposit to change virtual_price, which external protocols may use

## Solvency Equation
The CryptoSwap invariant must hold:
```
K * D^(N-1) * sum(x_i) + prod(x_i) = K * D^N + (D/N)^N
where K = A * gamma^2 / (gamma + 1 - K0)^2, K0 = N^N * prod(x_i) / D^N
```

LP token solvency: `virtual_price = D / totalSupply >= 1.0` (should only increase over time from fees)
