# Taint Map — 1inch V6 AggregationRouter (0x111111125421cA6dc452d289314280a0f8842A65)

## Summary of External Call Surfaces

The 1inch V6 router has **multiple caller-influenced external call sites**, categorized below by risk level for arbitrary call exploitation.

---

## HIGH RISK: Unprotected Callbacks (drain any router balance)

### 1. `curveSwapCallback` (line 5601-5609) — NO ACCESS CONTROL

```solidity
function curveSwapCallback(
    address /* sender */, address /* receiver */,
    address inCoin, uint256 dx, uint256 /* dy */
) external {
    IERC20(inCoin).safeTransfer(msg.sender, dx);
}
```

| Field | Classification |
|---|---|
| Target | SELF (router calls `inCoin.transfer`) |
| `inCoin` (token address) | **CALLER-CONTROLLED** — attacker picks any ERC20 |
| `dx` (amount) | **CALLER-CONTROLLED** — attacker picks any amount |
| `msg.sender` (recipient) | **CALLER** — tokens go to whoever calls this |
| Safety checks | **NONE** — no caller validation, no reentrancy guard |

**Vulnerability**: Any external account or contract can call `curveSwapCallback(_, _, tokenAddress, amount, _)` and the router will execute `IERC20(tokenAddress).safeTransfer(caller, amount)`. If the router holds any balance of that token, it is drained to the caller.

**Current impact**: LOW — the router keeps 1 wei per traded token (gas optimization). But any accidental deposit, airdrop, or rebasing accumulation becomes stealable.

---

### 2. `uniswapV3SwapCallback` (line 5621-5734) — UNVALIDATED WHEN payer==address(this)

```solidity
function uniswapV3SwapCallback(int256 amount0Delta, int256 amount1Delta, bytes calldata) external override {
    // ...
    let payer := calldataload(0x84)
    switch eq(payer, address())
    case 1 {
        // Transfer from router balance to caller — NO POOL VALIDATION
        safeERC20(token, 0, ...)
    }
    default {
        // Pool validation via CREATE2 address check
        // ...
        if xor(pool, caller()) { revert BadPool() }
        // transferFrom(payer, pool, amount)
    }
}
```

| Field | Classification |
|---|---|
| `amount0Delta`, `amount1Delta` | **CALLER-CONTROLLED** — function parameters |
| `payer` (calldata offset 0x84) | **CALLER-CONTROLLED** — can be set to address(this) |
| `token` | **DERIVED** — from `caller().token0()` or `caller().token1()` (attacker controls the caller contract) |
| Pool validation | **NONE** when `payer==address(this)`, **CREATE2** check when `payer!=address(this)` |

**Vulnerability**: When `payer == address(router)` (crafted in calldata), the router transfers tokens from its own balance to the calling contract WITHOUT validating that the caller is a legitimate Uniswap V3 pool. The attacker deploys a contract implementing `token0()`, `token1()`, `fee()` that returns any desired token addresses, then calls `uniswapV3SwapCallback(amount, 0, <payer=router>)`.

**Current impact**: LOW — same 1 wei limitation as above.

---

## MEDIUM RISK: Caller-Controlled External Call Targets

### 3. `swap(executor, desc, data)` (line 4758) → `_execute(executor, ...)` (line 4807)

```solidity
// In _execute:
call(gas(), executor, callvalue(), ptr, add(0x44, data.length), 0, 0x20)
```

| Field | Classification |
|---|---|
| `executor` (call target) | **CALLER-CONTROLLED** — any address |
| `data` (forwarded bytes) | **CALLER-CONTROLLED** |
| `msg.value` | **CALLER-CONTROLLED** (forwarded via callvalue()) |
| srcToken transfer | FROM `msg.sender` only (line 4784) |

**Assessment**: The executor runs in its own context (not delegatecall), so it cannot abuse the router's approvals. Source tokens come from `msg.sender`. The executor is intended to be an off-chain-computed routing contract. **Not directly exploitable** because it only affects the caller's own tokens.

### 4. `clipperSwapTo(clipperExchange, ...)` (line 4611)

```solidity
call(gas(), clipper, inputAmount, ptr, 0x149, 0, 0)  // or variants
```

| Field | Classification |
|---|---|
| `clipperExchange` (call target) | **CALLER-CONTROLLED** — any address |
| Source tokens | FROM `msg.sender` to `clipperExchange` (line 4627) |

**Assessment**: The Clipper exchange address is caller-provided. Source tokens come from `msg.sender`. The call forwards specific selector+params, not arbitrary calldata. **Not directly exploitable** — caller can only route their own tokens to a chosen Clipper exchange.

### 5. `_unoswap` family — pool addresses from `dex` parameter (line 5220+)

| Field | Classification |
|---|---|
| `pool` address | **CALLER-CONTROLLED** — extracted from packed `dex` parameter |
| `protocol` type | **CALLER-CONTROLLED** — top 3 bits of `dex` |
| Source tokens | FROM `msg.sender` (V2: line 5235; V3: via callback; Curve: line 5240) |

**Assessment**: Pool addresses are caller-controlled. For V2, tokens go from msg.sender to the pool, then pool.swap is called. For V3, pool.swap is called then callback validates pool (when payer != address(this)). For Curve, tokens go to router then to pool via approval.

A fake pool can steal the caller's OWN tokens (the ones sent to it), but cannot steal other users' tokens. **Not directly exploitable for stealing others' funds.**

---

## MEDIUM RISK: Callback/Interaction Patterns

### 6. `fillOrderArgs` — taker interaction (line 4018-4023)

```solidity
if (interaction.length > 19) {
    ITakerInteraction(address(bytes20(interaction))).takerInteraction(
        order, extension, orderHash, msg.sender, makingAmount, takingAmount, remainingMakingAmount, interaction[20:]
    );
}
```

| Field | Classification |
|---|---|
| Interaction target | **CALLER-CONTROLLED** — first 20 bytes of `interaction` from `args` |
| Interaction data | **CALLER-CONTROLLED** — remaining bytes |
| Timing | Between maker→taker transfer and taker→maker transfer |

**Assessment**: The taker (msg.sender) controls the interaction target and data. The taker interaction happens AFTER maker's tokens are sent to the taker but BEFORE taker sends tokens to the maker. No reentrancy guard exists on the generic flow (only on specific remaining-invalidator path). The taker could reenter the router, but maker tokens have already left and taker tokens haven't been sent yet. Limited exploitation potential since the taker is msg.sender (attacker would be stealing from themselves).

### 7. `fillOrderArgs` — pre/post interaction (lines 3985-3995, 4068-4078)

| Field | Classification |
|---|---|
| Pre-interaction target | Default: `order.maker.get()`, or `address(bytes20(data))` from extension |
| Post-interaction target | Default: `order.maker.get()`, or `address(bytes20(data))` from extension |

**Assessment**: Controlled by the order's extension data which is validated against the maker's signature (line 3814). The maker signs the order including the extension hash. Cannot be forged by the taker. **Not exploitable by taker.**

### 8. `permitAndCall(permit, action)` (line 2428)

```solidity
delegatecall(gas(), address(), ptr, action.length, 0, 0)
```

| Field | Classification |
|---|---|
| Permit target | **CALLER-CONTROLLED** — `address(bytes20(permit))` |
| Action (delegatecall data) | **CALLER-CONTROLLED** — any function on the router |

**Assessment**: Delegatecall to self (address()) preserves msg.sender. Functionally equivalent to: (1) call permit on a token, (2) call any router function as yourself. No privilege escalation — the caller can only do what they could already do. The permit requires a valid signature from the token holder.

### 9. `simulate(target, data)` (line 3711)

```solidity
(bool success, bytes memory result) = target.delegatecall(data);
revert SimulationResults(success, result);
```

| Field | Classification |
|---|---|
| `target` | **CALLER-CONTROLLED** — any address |
| `data` | **CALLER-CONTROLLED** — any calldata |

**Assessment**: Delegatecall to arbitrary target with arbitrary data, but ALWAYS reverts (line 3714). All state changes from the delegatecall are rolled back. **Not exploitable** — the revert is unconditional.

---

## LOW RISK: View/Static Call Surfaces

### 10. `checkPredicate(predicate)` (line 3761), `arbitraryStaticCall(target, data)` (line 1435)

Both use `_staticcallForUint(target, data)` — a staticcall that cannot modify state. **Not exploitable.**

### 11. Predicate helpers: `and`, `or`, `not`, `eq`, `gt`, `lt` (lines 1370-1445)

All use `_staticcallForUint(address(this), data)` — staticcall to self. Read-only. **Not exploitable.**

---

## Key Structural Observation

The 1inch V6 router's security model for swap functions is: **source tokens always come from msg.sender**. This means the caller can only risk their own funds. The router does NOT hold user funds long-term (except 1 wei per token for gas optimization).

The unprotected callbacks (`curveSwapCallback`, `uniswapV3SwapCallback` payer==self path) can drain any router balance. Current practical impact is limited to ~1 wei per token. Impact increases if:
1. Tokens are accidentally sent to the router
2. Rebasing/airdrop tokens accumulate
3. A new integration temporarily deposits tokens in the router
