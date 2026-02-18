# Numeric Boundaries — 1inch V6 AggregationRouter

## V2 AMM Calculation (lines 5289-5290)

```
ret = (amount * numerator * reserve1) / (amount * numerator + reserve0 * DENOMINATOR)
```

| Parameter | Range | Overflow risk |
|---|---|---|
| amount | uint256 (from user) | mul wraps if amount > 2^224 |
| numerator | uint32 max | Small |
| reserve0, reserve1 | uint112 (V2 pair) | Small |
| DENOMINATOR | 1e9 | Small |

Theoretical overflow not practically exploitable — V2 pair's k-invariant prevents over-extraction.

## Order Fill Amount: Uses OpenZeppelin Math.mulDiv (512-bit safe). No overflow risk.

## 1-wei Retention: Curve output `sub(ret, 1)` — underflow if output is 0, but caught by returndata checks.

## numerator = 0 defaults to 997M. numerator = 0xffffffff computes inflated output but V2 pair k-check reverts.

## Zero-amount: Blocked by explicit checks in swap (line 4778) and fillOrder (line 3975).
