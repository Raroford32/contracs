# Assumptions — 1inch V6 AggregationRouter

## Critical Assumptions (security depends on these)

### A1: Router holds no value between transactions
- **Evidence in code**: 1-wei retention pattern in Curve swap return (line 5541: `ret := sub(ret, 1)`)
- **Violation condition**: Accidental deposit, airdrop, rebasing token accumulation, fee-on-transfer dust
- **Consequence**: Anyone drains the balance via curveSwapCallback or uniswapV3SwapCallback (confirmed H1/H2)
- **Violation feasibility**: Low in normal operation; possible with exotic tokens or user error
- **Status**: CONFIRMED EXPLOITABLE (fork test proves drain mechanism works)

### A2: Source tokens always come from msg.sender
- **Evidence in code**: Every transferFrom has `from = msg.sender` (lines 4784, 5235, 5240, 4627, 4051) except maker→taker which uses ECDSA-verified maker address
- **Violation condition**: Any path where `from` can be set to an arbitrary address
- **Consequence**: Drain approved tokens from any user who approved the router
- **Violation feasibility**: Exhaustive audit of all transferFrom sites confirms NO violation path exists
- **Status**: HOLDS — verified across all 10 transferFrom sites

### A3: Only legitimate Uniswap V3 pools trigger the V3 callback with external payer
- **Evidence in code**: CREATE2 validation at lines 5697-5704 checking `keccak256(0xff ++ factory ++ salt ++ initCodeHash) == caller()`
- **Violation condition**: Deploying a contract at a CREATE2-matching address with different behavior
- **Consequence**: `transferFrom(victim, attacker, amount)` for any victim who approved the router
- **Violation feasibility**: Requires control of the canonical Uniswap V3 factory deployer — impossible
- **Status**: HOLDS — CREATE2 check is sound

### A4: ECDSA signatures cannot be forged for limit orders
- **Evidence in code**: `ECDSA.recover(orderHash, r, vs)` at line 3814
- **Violation condition**: ECDSA break, signature malleability, hash collision in order struct
- **Consequence**: Attacker creates orders on behalf of any maker, draining their approved tokens
- **Violation feasibility**: Standard ECDSA; OpenZeppelin library handles malleability (s-value normalization); EIP-712 typed data prevents cross-domain replay
- **Status**: HOLDS — standard cryptographic assumption

### A5: Order invalidator state prevents double-fill
- **Evidence in code**: Bit invalidator set at line 3979 before any external call; remaining invalidator updated at line 3981 before any external call
- **Violation condition**: State update after external call (CEI violation), or invalidator storage corruption
- **Consequence**: Double-fill of same order, extracting maker tokens twice
- **Violation feasibility**: Code follows CEI pattern per-order; invalidator is updated before pre-interaction, transfers, taker interaction, post-interaction
- **Status**: HOLDS — verified

## Moderate Assumptions

### A6: External tokens behave as standard ERC20
- **Evidence in code**: `safeTransfer/safeTransferFrom` wrappers (OpenZeppelin); `_callTransferFromWithSuffix` appends suffix bytes
- **Violation condition**: Fee-on-transfer tokens (amount received < amount sent), rebasing tokens (balance changes without transfer), ERC777 hooks (reentrancy via tokensReceived), tokens with non-standard return values
- **Consequence varies**:
  - Fee-on-transfer: User receives less than expected (but minReturn check should catch this)
  - Rebasing: Balance accumulation on router becomes drainable via H1/H2
  - ERC777: Reentrancy during transfer — but router uses CEI for order invalidation
- **Status**: ACCEPTED RISK — standard DeFi assumption; minReturn check is primary defense

### A7: DEX pools return honest reserve/price data
- **Evidence in code**: `pool.getReserves()` in V2 path (line 5276); pool.swap() return values in V3 (line 5350)
- **Violation condition**: Fake pool returns manipulated reserves
- **Consequence**: Router computes wrong output amount for V2 — but V2 pair's own k-invariant check is the real guardrail; attacker can only harm themselves
- **Status**: HOLDS (defense in depth) — real V2/V3 pools enforce their own invariants

### A8: The executor in swap() cannot abuse router context
- **Evidence in code**: `call(gas(), executor, callvalue(), ...)` at line 4807 — regular call, not delegatecall
- **Violation condition**: If executor were called via delegatecall instead of call
- **Consequence**: Executor could access router storage, manipulate state, drain approvals
- **Violation feasibility**: NOT possible — the code uses `call`, not `delegatecall`
- **Status**: HOLDS

### A9: simulate() delegatecall always reverts
- **Evidence in code**: `revert SimulationResults(success, result)` at line 3714 — unconditional revert after delegatecall
- **Violation condition**: If the revert could be bypassed or if the delegatecall corrupts storage before revert
- **Consequence**: Arbitrary delegatecall to any target with any data could corrupt router storage
- **Violation feasibility**: Revert is unconditional; EVM guarantees all state changes from a reverted subcall are rolled back
- **Status**: HOLDS — EVM semantics guarantee safety

### A10: permitAndCall delegatecall-to-self preserves msg.sender correctly
- **Evidence in code**: `delegatecall(gas(), address(), ...)` at line 2434 — delegatecall to self
- **Violation condition**: If delegatecall to self could change msg.sender or msg.value semantics
- **Consequence**: Permit could set approval for router, then action could transfer from a different user
- **Violation feasibility**: EVM spec: delegatecall preserves msg.sender and msg.value
- **Status**: HOLDS — EVM semantics guarantee

## Low-Priority Assumptions

### A11: Assembly memory management is correct
- **Evidence in code**: All assembly blocks declare `"memory-safe"`; free pointer managed at line 5274 etc.
- **Violation condition**: Memory corruption via incorrect pointer arithmetic
- **Consequence**: Wrong call parameters, potentially redirected transfers
- **Violation feasibility**: Code uses standard patterns; no overlapping writes observed in audit
- **Status**: HOLDS — but difficult to prove exhaustively for 5786 lines

### A12: Packed Address type extracts address correctly
- **Evidence in code**: `and(dex, _ADDRESS_MASK)` where `_ADDRESS_MASK = (1<<160)-1` (line 4968)
- **Violation condition**: If flag bits leaked into address extraction
- **Consequence**: Wrong pool address, potentially malicious contract called
- **Violation feasibility**: Mask is correct; `uint160` truncation is clean
- **Status**: HOLDS — verified
