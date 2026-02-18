# Numeric Boundaries — Curve Tricrypto2

## Key Boundary Experiments Needed

### 1. Empty/Near-Empty Pool
- First depositor attack: can initial LP tokens be manipulated?
- Small deposit after large withdrawal: precision loss?

### 2. Extreme Imbalance
- All-in-one-token deposit: price_scale vs actual price divergence
- Near-zero balance of one token: Newton's method convergence?

### 3. Price Scale Boundaries
- price_scale near 0 or near max: overflow in internal math?
- price_scale diverging significantly from price_oracle

### 4. Virtual Price Manipulation
- Can virtual_price be decreased? (Should be monotonically increasing)
- Donation attack: send tokens directly → affects balances() vs internal tracking?

### 5. Fee Boundaries
- fee_gamma = 0: division by zero in fee calculation?
- mid_fee = out_fee: degenerate case
- admin_fee at maximum: all fees go to admin

### 6. A/Gamma Boundaries
- A at minimum (1) or maximum
- gamma at minimum or maximum
- During A/gamma ramp: intermediate values

### 7. Newton's Method Convergence
- Can specific inputs cause non-convergence?
- Very large swaps relative to pool size

### 8. Decimal Handling
- USDT (6 dec) vs WBTC (8 dec) vs WETH (18 dec)
- PRICE_PRECISION_MUL factors: 10^12 for USDT, 10^10 for WBTC, 1 for WETH
- Rounding in precision multiplication/division

## Results
TBD — will be filled during fork testing
