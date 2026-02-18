# Value Flows — 1inch V6 AggregationRouter

## Money Entry Points (how tokens reach the router)

### 1. Swap Flow (GenericRouter)
- User calls `swap(executor, desc, data)`
- `srcToken.safeTransferFromUniversal(msg.sender, desc.srcReceiver, desc.amount, ...)`
- Tokens go from **msg.sender** → **desc.srcReceiver** (typically the executor or a pool)
- Router never holds these tokens (direct transfer from user to pool)

### 2. Unoswap Flow (UnoswapRouter)
- User calls `unoswap/unoswapTo/unoswap2/unoswap3` etc
- V2 path: `safeTransferFromUniversal(msg.sender, pool, amount, ...)` — direct to pool
- V3 path: `pool.swap()` → callback → `transferFrom(msg.sender, pool, amount)` — via callback
- Curve path: `safeTransferFromUniversal(msg.sender, address(this), amount)` → router holds briefly → `approve(pool, amount)` → `pool.exchange(...)` — router is temporary custodian
- ETH path: user sends ETH → `WETH.deposit{value: msg.value}()` → WETH in router → swap

### 3. Clipper Flow (ClipperRouter)
- `srcToken.safeTransferFromUniversal(msg.sender, clipperExchange, amount, ...)` — direct to clipper

### 4. Limit Order Flow (OrderMixin)
- Maker→Taker: `transferFrom(order.maker, taker/target, makingAmount)` — direct
- Taker→Maker: `transferFrom(msg.sender, order.receiver, takingAmount)` — direct

### 5. ETH receive()
- Only intended for WETH unwrap (pool sends ETH to router during swap)

## Money Exit Points (how tokens leave the router)

### 1. Normal swap completion
- Output tokens go from pool → user (or user-specified receiver)
- In V2: `pool.swap(amount0Out, amount1Out, recipient, "")` sends directly to recipient
- In V3: `pool.swap(recipient, ...)` sends directly to recipient
- In Curve: pool sends to router → router sends to user
- In Clipper: clipper sends directly to user

### 2. WETH unwrap
- Router unwraps WETH → sends ETH to user: `uniTransfer(IERC20(0), receiver, amount)`

### 3. Callback drains (unprotected — H1, H2)
- `curveSwapCallback(_, _, token, amount, _)` → `token.safeTransfer(msg.sender, amount)`
- `uniswapV3SwapCallback(amount, 0, <payer=router>)` → `token.transfer(msg.sender, amount)`

### 4. rescueFunds (owner only)
- `token.uniTransfer(to, amount)` — owner can sweep any tokens from router

## Value Transforms

The router does NOT transform value itself. It routes user tokens through external DEX pools which perform the actual price transformation. The router's role is:
1. Accept source tokens from user
2. Route to appropriate DEX pool(s)
3. Ensure output meets minimum return

## Fee Extraction

**No explicit protocol fee in the router contract itself.**
- The 1inch protocol extracts value via the spread between the guaranteed minReturn and the actual execution (positive slippage)
- The `swap()` function returns actual output to the user, but the off-chain routing can capture surplus via the executor contract
- Unoswap has a configurable numerator (fee parameter in V2) but this is the DEX fee, not the 1inch fee

## Actor Model

| Actor | Role | Power | Information |
|---|---|---|---|
| User/Swapper | Provides tokens, calls swap | Controls amount, receiver, slippage tolerance | Sees public order book, mempool |
| Executor | Off-chain computed routing contract | Receives user tokens, executes multi-hop logic | Knows optimal route (1inch API) |
| Maker (limit orders) | Signs orders with specific terms | Controls price, amount, expiry, receiver | Knows their own order parameters |
| Taker (limit orders) | Fills maker orders | Controls fill amount, target address | Sees signed orders on resolver API |
| Owner (1inch) | Admin operations | Pause/unpause, rescueFunds, transfer ownership | Full admin access |
| DEX Pools | Execute swaps | Transform tokens at their invariant curve | Know their own reserves |

### Dual Roles
- **Taker who is also an executor**: Could fill an order and route tokens through own executor — but this is expected behavior
- **Owner who is also a taker**: Could pause protocol during a fill — but that would revert the fill, not extract value
- **Attacker who deploys fake pools**: Can call unoswap with fake pool address, but can only steal from themselves (source tokens always from msg.sender)

## Custody Model

**The 1inch V6 router is a non-custodial router.** It does NOT hold user funds between transactions. The security model explicitly depends on this:
- 1 wei per token is kept for gas optimization (storage slot warm-keeping)
- Any accumulation beyond 1 wei is drainable via the unprotected callbacks
- `rescueFunds` exists as a safety valve for accidental deposits

## Solvency Equation

For a non-custodial router: `router_balance_of_any_token <= 1 wei` (invariant, by design)

If violated (e.g., accidental deposit, airdrop, rebasing):
- Difference is drainable by anyone via curveSwapCallback or uniswapV3SwapCallback
- rescueFunds (owner-only) can also recover
