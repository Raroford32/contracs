# Token Semantics — 1inch V6 AggregationRouter

## Router Token Interaction Model

The router is a non-custodial pass-through. It does not hold tokens between transactions. Token interactions are:
1. Transfer from user to pool (or router for Curve)
2. Transfer from pool to user (or router, then to user for Curve)
3. Callbacks may transfer from router balance to caller (unprotected)

## Key Tokens in Router Flows

### WETH (0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2)
- **Role**: Intermediary for ETH swaps (wrap/unwrap)
- **Semantics**: Standard, no rebasing, no fee-on-transfer, no hooks
- **Router balance at block 21880000**: 0 wei
- **Risk**: If WETH accumulates on router (e.g., failed unwrap), drainable via H1/H2

### USDC (0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48)
- **Role**: Example high-value token traded through router
- **Semantics**: Proxy-upgradeable, pausable, blacklistable. Standard return values.
- **Router balance at block 21880000**: 0 units
- **Risk**: Blacklist could cause router transactions to revert (DOS only, not fund loss)

### Arbitrary ERC20 (user-supplied via swap/unoswap parameters)
- **Role**: Any token can be swapped through the router
- **Semantics**: Varies wildly
- **Router defense**: minReturn check catches fee-on-transfer shortfalls
- **Risk matrix**:

| Token Property | Router Impact | Severity |
|---|---|---|
| Fee-on-transfer | Less received than expected; minReturn may revert | Low (self-griefing) |
| Rebasing (positive) | Balance accumulates on router → drainable via H1/H2 | Low-Medium |
| Rebasing (negative) | Less available for transfer; may revert | Low (self-griefing) |
| ERC777 hooks | Reentrancy during transfer; but CEI holds per-order | Low |
| Non-standard return | safeTransfer/safeTransferFrom handles both bool and no-return | None |
| Pausable/Blacklistable | Transfer reverts; DOS on swap | Low (self-griefing) |
| Upgradeable | Behavior could change; impossible to defend against | Accepted risk |
| Max uint256 approval | Standard pattern; router only transfers from msg.sender | None |

## _callTransferFromWithSuffix Concern

The router's `_callTransferFromWithSuffix` (line 4149) appends arbitrary suffix bytes after the standard `transferFrom(from, to, amount)` calldata. For standard ERC20 tokens, this extra data is ignored. However:

- If a token's `transferFrom` implementation reads beyond the 3 standard parameters (e.g., some hypothetical hook/plugin system), the suffix could influence behavior
- The suffix comes from maker-signed extension data (maker chose to sign an order for that specific token)
- Practical risk: negligible — no known tokens parse extra transferFrom calldata

## Discriminator Results

### Fork test: Router balance at block 21880000
- WETH: 0 wei (confirmed via `test_real_world_residual_balances`)
- USDC: 0 units (confirmed via `test_real_world_residual_balances`)
- The 1-wei optimization is working as designed — both are actually 0 at this block
