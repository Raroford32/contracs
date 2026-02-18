# Entrypoints — Curve Tricrypto2

## Pool (0xd51a44d3fae010294c616388b506acda1bfaae46)
Vyper 0.2.12 — CryptoSwap pool for USDT/WBTC/WETH

### User-callable (permissionless)
- `exchange(uint256 i, uint256 j, uint256 dx, uint256 min_dy)` — swap coin i for coin j
- `add_liquidity(uint256[3] amounts, uint256 min_mint_amount)` — deposit coins, mint LP
- `remove_liquidity(uint256 _amount, uint256[3] min_amounts)` — burn LP, withdraw coins proportionally
- `remove_liquidity_one_coin(uint256 token_amount, uint256 i, uint256 min_amount)` — burn LP, withdraw single coin
- `claim_admin_fees()` — permissionless admin fee claim (triggers fee distribution)
- `get_dy(uint256 i, uint256 j, uint256 dx)` — view: preview swap output
- `calc_token_amount(uint256[3] amounts, bool deposit)` — view: preview LP tokens for deposit
- `calc_withdraw_one_coin(uint256 token_amount, uint256 i)` — view: preview withdraw amount
- `get_virtual_price()` — view: virtual price of LP token
- `price_oracle(uint256 k)` — view: EMA oracle price
- `price_scale(uint256 k)` — view: internal price scale
- `last_prices(uint256 k)` — view: last trade prices
- `fee()` — view: current fee
- `A()` / `gamma()` — view: current amplification and gamma

### Admin-only (owner-gated)
- `ramp_A_gamma(uint256 future_A, uint256 future_gamma, uint256 future_time)` — ramp A/gamma
- `stop_ramp_A_gamma()` — stop ongoing A/gamma ramp
- `commit_new_parameters(...)` — commit new fee/admin fee/price adjustment params
- `apply_new_parameters()` — apply committed params after delay
- `revert_new_parameters()` — revert pending param change
- `commit_transfer_ownership(address _owner)` — commit ownership transfer
- `apply_transfer_ownership()` — apply ownership transfer after delay
- `revert_transfer_ownership()` — revert pending ownership transfer
- `kill_me()` — emergency kill (only before kill_deadline)
- `unkill_me()` — restore from killed state

### Receive/Fallback
- None (Vyper contract)

## LP Token (0xc4AD29ba4B3c580e6D59105FFf484999997675Ff)
- Standard ERC20 with mint/burn callable only by minter (the pool)
- `transfer`, `transferFrom`, `approve` — standard ERC20
- `mint(address, uint256)` — minter-only
- `burnFrom(address, uint256)` — minter-only

## Tokens
- USDT (0xdac17f958d2ee523a2206206994597c13d831ec7) — 6 decimals, no return on transfer
- WBTC (0x2260fac5e5542a773aa44fbcfedf7c193bc2c599) — 8 decimals
- WETH (0xc02aaa39b223fe8d0a0e5c4f27ead9083c756cc2) — 18 decimals
