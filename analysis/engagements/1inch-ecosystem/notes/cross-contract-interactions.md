# Cross-Contract Interaction Matrix — 1inch Ecosystem

## Contract Universe

| Contract | Address | Role |
|----------|---------|------|
| AggregationRouterV6 | 0x111111125421cA6dc452d289314280a0f8842A65 | Current router + limit orders |
| AggregationRouterV5 | 0x1111111254EEB25477B68fb85Ed929f73A960582 | Legacy router (live approvals) |
| AggregationRouterV4 | 0x1111111254fb6c44bAC0beD2854e76F90643097d | Legacy router (live approvals) |
| AggregationRouterV3 | 0x11111112542D85B3EF69AE05771c2dCCff4fAa26 | Legacy router (live approvals) |
| 1INCH Token | 0x111111111117dC0aa78b770fA6A738034120C302 | Governance/staking token |
| st1INCH | 0x9A0C8Ff858d273f57072D714bca7411D717501D7 | Staking (non-transferable, locked) |
| Permit2 | 0x000000000022D473030F116dDEE9F6B43aC78BA3 | Shared approval layer (V6 only) |
| UniV3 Factory | 0x1F98431c8aD98523631AE4a59f267346ea31F984 | Pool deployment (callback validation) |
| WETH | 0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2 | Wrapped ETH |
| $98M Multisig | 0x111cff45948819988857bbf1966a0399e0d1141e | Gnosis 3-of-3 (NOT protocol contract) |

## Interaction Matrix

### V6 Router → External Contracts

| Caller | Callee | Function | Data Source | Condition | Risk |
|--------|--------|----------|------------|-----------|------|
| V6 Router | ERC20 Token | transferFrom(msg.sender, pool, amt) | User params | swap/unoswap | SAFE: from=msg.sender |
| V6 Router | ERC20 Token | transferFrom(maker, receiver, amt) | Signed order | fillOrder | SAFE: ECDSA-verified maker |
| V6 Router | UniV3 Pool | swap() | Packed dex param | Unoswap path | SAFE: pool is external |
| UniV3 Pool | V6 Router | uniswapV3SwapCallback() | Pool params | During swap | SAFE if pool CREATE2-valid; H2 when payer==self |
| Curve Pool | V6 Router | curveSwapCallback() | Pool params | During Curve swap | H1: NO access control (negligible impact) |
| V6 Router | IAmountGetter | getMakingAmount/getTakingAmount() | Maker extension | fillOrder with extension | SAFE: staticcall |
| V6 Router | IPreInteraction | preInteraction() | Maker extension | fillOrder with pre-interaction | Maker-controlled, fires after invalidation |
| V6 Router | ITakerInteraction | takerInteraction() | Taker args | fillOrder with interaction | Taker-controlled, amounts already fixed |
| V6 Router | IPostInteraction | postInteraction() | Maker extension | fillOrder with post-interaction | Maker-controlled, after all transfers |
| V6 Router | Permit2 | transferFrom(msg.sender, to, amt, token) | Order params | USE_PERMIT2 flag | SAFE: from=msg.sender or verified maker |
| V6 Router | WETH | deposit/withdraw | Internal | ETH wrapping | SAFE: hardcoded WETH |
| V6 Router | ERC20 Token | tryPermit() | Maker extension | First fill, maker permit | SAFE: permit is for maker's own tokens |

### V5 Router → External Contracts

| Caller | Callee | Function | Data Source | Condition | Risk |
|--------|--------|----------|------------|-----------|------|
| V5 Router | ERC20 Token | transferFrom(msg.sender, ...) | User params | All swap paths | SAFE: from=msg.sender |
| V5 Router | ERC20 Token | transferFrom(maker, ...) | Signed order | fillOrder/fillOrderRFQ | SAFE: ECDSA-verified |
| UniV3 Pool | V5 Router | uniswapV3SwapCallback() | Pool params | During swap | SAFE: CREATE2 always validates |
| V5 Router | Executor | execute() | User-chosen | swap() | SAFE: tokens pre-transferred from msg.sender |
| V5 Router | Target | delegatecall() | User params | simulate() | SAFE: always reverts |

### V4 Router → External Contracts

| Caller | Callee | Function | Data Source | Condition | Risk |
|--------|--------|----------|------------|-----------|------|
| V4 Router | ERC20 Token | transferFrom(msg.sender, ...) | User params | All paths | SAFE: from=msg.sender |
| V4 Router | ERC20 Token | transferFrom(maker, ...) | Signed order | fillOrderRFQ | SAFE: ECDSA-verified |
| UniV3 Pool | V4 Router | uniswapV3SwapCallback() | Pool params | During swap | SAFE: CREATE2 always validates |

### V3 Router → External Contracts

| Caller | Callee | Function | Data Source | Condition | Risk |
|--------|--------|----------|------------|-----------|------|
| V3 Router | ERC20 Token | safeTransferFrom(msg.sender, ...) | User params | swap() | SAFE: from=msg.sender |

### Cross-Router Interactions

**None.** The router versions do NOT interact with each other on-chain. Each is a standalone contract. Users interact with whichever version they choose, but no cross-router calls exist.

### st1INCH Interactions

| Caller | Callee | Function | Condition | Risk |
|--------|--------|----------|-----------|------|
| User | st1INCH | deposit(amount, duration) | Min 30 days lock | SAFE |
| User | st1INCH | withdraw() | After unlock time | SAFE |
| st1INCH | 1INCH Token | transferFrom(msg.sender, ...) | deposit | SAFE |
| st1INCH | 1INCH Token | transfer(user, amount) | withdraw | SAFE |
| Anyone | st1INCH | votingPowerOf(user) | View only | SAFE: read-only |

**st1INCH has NO on-chain interaction with any router or oracle contract.**

## Key Security Properties Across Ecosystem

### Core Invariant: `transferFrom(from, ...) where from ∈ {msg.sender, ECDSA_verified_maker}`
- **V3**: ✅ Always msg.sender
- **V4**: ✅ msg.sender or ECDSA-verified maker (RFQ orders)
- **V5**: ✅ msg.sender or ECDSA-verified maker (limit + RFQ orders)
- **V6**: ✅ msg.sender or ECDSA/ERC-1271 verified maker + Permit2 (same invariant)

### Callback Security
- **V3**: No callbacks
- **V4**: uniswapV3SwapCallback with CREATE2 validation (ALWAYS runs)
- **V5**: uniswapV3SwapCallback with CREATE2 validation (ALWAYS runs)
- **V6**: uniswapV3SwapCallback (CREATE2 skipped when payer==self — H2), curveSwapCallback (NO access control — H1)

### Non-Custodial Property
- **All versions**: Router designed to hold ≤1 wei per token between transactions
- **Verified**: Router balance = 0 at block 21880000 and expected 0 at block 24482400

### Order Fill CEI
- **V6**: Order invalidated (state write) BEFORE all external calls (preInteraction, transfers, takerInteraction, postInteraction)
- **V5**: Same pattern — order nonce updated before transfers
- **V4**: Same pattern — RFQ order nonce checked before fill

## Cross-Protocol Composition Analysis

### 1inch ↔ Uniswap V3
- Interaction: V6/V5/V4 use UniV3 pools for swap execution
- Security: CREATE2 pool address verification prevents spoofed callbacks
- V6 weakness: payer==self path skips CREATE2 (H2, negligible impact)

### 1inch ↔ Curve
- Interaction: V6 uses Curve pools for swap execution via callback pattern
- Security: curveSwapCallback has NO access control (H1, negligible impact)
- Router temporarily holds tokens during Curve hops (attacker's own tokens)

### 1inch ↔ Permit2
- Interaction: V6 optionally uses Permit2 for token transfers
- Security: Permit2 allowances are per-spender; no cross-protocol confusion
- All Permit2 calls use msg.sender or verified maker as `from`

### 1inch ↔ Governance
- Interaction: NONE on-chain between router and st1INCH/governance
- Governance is off-chain (Snapshot) with multisig execution
- No atomic governance attack vector exists
