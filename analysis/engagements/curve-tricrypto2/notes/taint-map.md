# Taint Map — Curve Tricrypto2

## External Callsites in Pool

### Token Transfers (raw_call)
- `_transfer_in(coin_idx, _from, amount)` — transferFrom user to pool
  - Target: fixed (coins[i])
  - Calldata: transferFrom (ABI-encoded, not caller-controlled)
  - Value: 0
  - Safety: token addresses immutable
  - Risk: USDT void return (handled by raw_call with max_outsize)

- `_transfer_out(coin_idx, _to, amount)` — transfer from pool to user
  - Target: fixed (coins[i])
  - Calldata: transfer (ABI-encoded, not caller-controlled)
  - Value: 0
  - Safety: token addresses immutable

### LP Token Interactions
- `token.mint(to, amount)` — mint LP tokens
  - Target: fixed (token address)
  - Safety: only pool can call mint

- `token.burnFrom(from, amount)` — burn LP tokens
  - Target: fixed (token address)
  - Safety: only pool can call burnFrom

### Math Library
- External calls to CryptoMath contract for Newton's method
  - Target: fixed (math address, set at deploy)
  - Calldata: derived from pool state (not caller-controlled)
  - Risk: if math contract has bugs, all pool operations affected

## No Dynamic Dispatch
- Vyper contract: no delegatecall, no low-level call with user-controlled target
- All external call targets are immutable (set at deployment)

## Conclusion
- No arbitrary-call corridors
- All external calls go to fixed, known contracts
- Primary risk: math library correctness, token transfer edge cases (USDT)
