# 1inch AggregationRouterV5 -- Approval Surface & transferFrom Analysis

**Contract:** `AggregationRouterV5` (Solidity 0.8.17)
**Source:** `/home/user/contracs/src_cache/1inch_v5_router.sol`
**Inheritance chain:** `EIP712, Ownable, ClipperRouter, GenericRouter, UnoswapRouter, UnoswapV3Router, OrderMixin, OrderRFQMixin`

---

## Executive Summary

**V5 has NO path that allows an arbitrary attacker to drain a victim's approved tokens using only public functions.**

All transferFrom call sites in the V5 router use either:
1. `msg.sender` as the `from` address (direct user transfers), OR
2. An ECDSA-verified `order.maker` as the `from` address (limit/RFQ orders), OR
3. `address(this)` (the router itself) as the `from` address (WETH wrapping paths), OR
4. A `payer` derived from the callback data parameter, but constrained to only be `msg.sender` or `address(this)` by the call chain.

**However, there is one notable difference from V6**: the `_callTransferFrom` function in `OrderMixin` appends arbitrary `makerAssetData`/`takerAssetData` bytes AFTER the standard transferFrom calldata. While this does not enable token theft (the `from` is still validated), it is a design pattern V6 removed. Additionally, the `simulate()` function uses unrestricted `delegatecall`, which is a unique V5 surface not present in V6.

---

## Complete transferFrom Call Site Inventory

### SITE 1: `ClipperRouter.clipperSwapTo()` -- WETH path (assembly)
**File line:** ~532-542
**Code (assembly):**
```solidity
mstore(ptr, transferFromSelector)    // transferFrom selector
mstore(add(ptr, 0x04), caller())     // from = msg.sender
mstore(add(ptr, 0x24), address())    // to = address(this)
mstore(add(ptr, 0x44), inputAmount)
call(gas(), weth, 0, ptr, 0x64, 0, 0)
```
**`from` address:** `caller()` = `msg.sender` -- HARDCODED
**Risk:** NONE. Only transfers from the caller.

---

### SITE 2: `ClipperRouter.clipperSwapTo()` -- ERC20 path (SafeERC20)
**File line:** ~556
**Code:**
```solidity
srcToken.safeTransferFrom(msg.sender, address(clipperExchange), inputAmount);
```
**`from` address:** `msg.sender` -- HARDCODED
**Risk:** NONE.

---

### SITE 3: `GenericRouter.swap()` (SafeERC20)
**File line:** ~1002
**Code:**
```solidity
srcToken.safeTransferFrom(msg.sender, desc.srcReceiver, desc.amount);
```
**`from` address:** `msg.sender` -- HARDCODED
**Risk:** NONE. `desc.srcReceiver` is the `to` address (where tokens go), not the `from`.

---

### SITE 4: `UnoswapRouter._unoswap()` -- ERC20 path (assembly)
**File line:** ~1235-1241
**Code (assembly):**
```solidity
mstore(emptyPtr, _TRANSFER_FROM_CALL_SELECTOR)  // 0x23b872dd
mstore(add(emptyPtr, 0x4), caller())             // from = msg.sender
mstore(add(emptyPtr, 0x24), and(rawPair, _ADDRESS_MASK))  // to = first pool
mstore(add(emptyPtr, 0x44), amount)
call(gas(), srcToken, 0, emptyPtr, 0x64, 0, 0x20)
```
**`from` address:** `caller()` = `msg.sender` -- HARDCODED
**Risk:** NONE.

---

### SITE 5: `UnoswapV3Router.uniswapV3SwapCallback()` -- payer != address(this) path (assembly)
**File line:** ~2905-2923
**Code (assembly):**
```solidity
let payer := calldataload(0x84)
// ...
// When payer != address(this):
// token.safeTransferFrom(payer, msg.sender, amount)
mstore(add(emptyPtr, 0x14), payer)
mstore(add(emptyPtr, 0x34), caller())
mstore(add(emptyPtr, 0x54), amount)
call(gas(), token, 0, add(emptyPtr, 0x10), 0x64, 0, 0x20)
```
**`from` address:** `payer`, loaded from calldata offset 0x84
**Access control on callback:** Verifies `caller()` is a legitimate Uniswap V3 pool by:
1. Calling `token0()`, `token1()`, `fee()` on `caller()`
2. Computing `CREATE2` address from `_FF_FACTORY` + `_POOL_INIT_CODE_HASH`
3. Requiring `computed_pool == caller()` (line 2900: `if xor(pool, caller()) { revert BadPool() }`)

**Analysis of `payer` value:**
The `payer` comes from the `data` parameter of the Uniswap V3 pool callback. In `_makeSwap()` (line 2928-2949), the `data` is `abi.encode(payer)`. The `payer` argument to `_makeSwap` is set in `_uniswapV3Swap()`:
- First pool (no WETH wrapping): `payer = msg.sender` (line 2825, 2832)
- First pool (with WETH wrapping): `payer = address(this)` (line 2825, 2832)
- Subsequent pools: `payer = address(this)` (line 2828)
- Last pool: `payer = address(this)` (line 2830)

**Risk:** LOW -- `payer` is always either `msg.sender` or `address(this)`, constrained by the private `_makeSwap` function. An external attacker cannot directly call `uniswapV3SwapCallback` with an arbitrary payer because the callback validates that `msg.sender` is a legitimate Uniswap V3 factory-deployed pool. A malicious pool cannot be created through the canonical factory with arbitrary token addresses to redirect to a victim.

**IMPORTANT NUANCE:** `calldataload(0x84)` reads the 4th ABI argument position (offset 0x84 = 132 bytes = 4 selector + 4*32 args). The callback signature is `uniswapV3SwapCallback(int256, int256, bytes)`. The `bytes` parameter at offset 0x84 in practice points to the ABI-encoded offset of the bytes, not the raw payer address. However, the assembly reads it as a raw word. Looking at the Uniswap V3 pool contract behavior: it passes the `data` parameter through to the callback unchanged. The `_makeSwap` encodes the payer as `abi.encode(payer)`, and the pool passes this as the 3rd argument (bytes). With standard ABI encoding of `(int256, int256, bytes)`:
- offset 0x00: selector
- offset 0x04: amount0Delta
- offset 0x24: amount1Delta
- offset 0x44: offset to bytes data (= 0x60)
- offset 0x64: length of bytes
- offset 0x84: first 32 bytes of the bytes data = the payer address

So `calldataload(0x84)` correctly reads the payer address from the encoded bytes. This is safe as long as only legitimate pools call back with data created by `_makeSwap`.

---

### SITE 6: `OrderRFQMixin._fillOrderRFQTo()` -- WETH maker transfer
**File line:** ~3714
**Code:**
```solidity
_WETH.transferFrom(maker, address(this), makingAmount);
```
**`from` address:** `maker = order.maker`
**Authentication:** `order.maker` is ECDSA-verified via `ECDSA.recoverOrIsValidSignature(order.maker, orderHash, r, vs)` or `ECDSA.isValidSignature(order.maker, orderHash, r, vs)` (lines 3602-3610 for compact, 3658-3663 for standard).
**Risk:** NONE. Maker must sign the order. Attacker cannot forge a signature for an arbitrary victim.

---

### SITE 7: `OrderRFQMixin._fillOrderRFQTo()` -- ERC20 maker transfer (SafeERC20)
**File line:** ~3720
**Code:**
```solidity
IERC20(order.makerAsset).safeTransferFrom(maker, target, makingAmount);
```
**`from` address:** `maker = order.maker` -- ECDSA-verified (same as Site 6)
**Risk:** NONE.

---

### SITE 8: `OrderRFQMixin._fillOrderRFQTo()` -- taker transfer (SafeERC20)
**File line:** ~3730
**Code:**
```solidity
IERC20(order.takerAsset).safeTransferFrom(msg.sender, maker, takingAmount);
```
**`from` address:** `msg.sender` -- HARDCODED
**Risk:** NONE.

---

### SITE 9: `OrderMixin.fillOrderTo()` via `_callTransferFrom` -- maker to taker
**File line:** ~4501-4507
**Code:**
```solidity
_callTransferFrom(
    order.makerAsset,
    order.maker,        // from
    target,             // to
    actualMakingAmount,
    order.makerAssetData()
)
```
**`from` address:** `order.maker` -- ECDSA-verified at line 4438:
```solidity
if (!ECDSA.recoverOrIsValidSignature(order.maker, orderHash, signature)) revert BadSignature();
```
**Risk:** NONE for token theft. The maker must have signed the order.

**NOTE:** `_callTransferFrom` appends `order.makerAssetData()` after the standard transferFrom arguments (line 4581). This means the actual call to the token is: `transferFrom(from, to, amount) ++ makerAssetData`. For standard ERC20 tokens, the extra data is ignored. This is a design pattern used for tokens that support extended transferFrom. The `makerAssetData` is part of the signed order, so the maker controls it. This is safe but unusual.

---

### SITE 10: `OrderMixin.fillOrderTo()` via `_callTransferFrom` -- taker to maker
**File line:** ~4537-4543
**Code:**
```solidity
_callTransferFrom(
    order.takerAsset,
    msg.sender,           // from
    order.receiver == address(0) ? order.maker : order.receiver,  // to
    actualTakingAmount,
    order.takerAssetData()
)
```
**`from` address:** `msg.sender` -- HARDCODED
**Risk:** NONE for direct token theft.

**NOTE:** Same pattern -- appends `order.takerAssetData()` after standard transferFrom args. The `takerAssetData` is part of the MAKER's signed order, meaning the maker controls what extra bytes are appended to the transferFrom call on the TAKER's tokens. For standard ERC20 tokens this is harmless (extra calldata ignored). For exotic tokens with extended transferFrom semantics, this could theoretically matter, but no known ERC20 tokens interpret trailing calldata.

---

### SITE 11: `UniERC20.uniTransferFrom()` (SafeERC20)
**File line:** ~853-871
**Code:**
```solidity
function uniTransferFrom(IERC20 token, address payable from, address to, uint256 amount) internal {
    if (amount > 0) {
        if (isETH(token)) {
            if (msg.value < amount) revert NotEnoughValue();
            if (from != msg.sender) revert FromIsNotSender();
            // ...
        } else {
            token.safeTransferFrom(from, to, amount);
        }
    }
}
```
**Callers:** This is a library function. Searching for call sites shows it is NOT called from any external function with an attacker-controlled `from`. The only usage pattern I can identify is internal to the library. The ETH path explicitly requires `from == msg.sender`.
**Risk:** NONE at the library level; safety depends on callers (which are all analyzed above).

---

## Additional Attack Surfaces

### The `simulate()` function -- UNRESTRICTED DELEGATECALL
**File line:** ~4360-4364
**Code:**
```solidity
function simulate(address target, bytes calldata data) external {
    (bool success, bytes memory result) = target.delegatecall(data);
    revert SimulationResults(success, result);
}
```
**Analysis:** This function performs a `delegatecall` to an arbitrary `target` with arbitrary `data`, then ALWAYS reverts with `SimulationResults`. Because it always reverts, no state changes persist. The delegatecall executes in the context of the router (with the router's storage, balance, and `address(this)`), but since the entire call frame reverts, no approvals or storage can be exploited.

**Risk:** NONE for direct exploitation because the revert undoes all state changes. However, this is a design difference from V6 that could interact with certain edge cases (e.g., view-function reentrancy where the revert data is observed mid-call by another contract). In practice, this is not exploitable for token theft.

---

### The `_execute()` function -- Executor pattern
**File line:** ~1030-1052
**Code:**
```solidity
function _execute(
    IAggregationExecutor executor,
    address srcTokenOwner,
    uint256 inputAmount,
    bytes calldata data
) private {
    // calls executor.execute(srcTokenOwner) with appended data + inputAmount
}
```
**Analysis:** The executor is a caller-chosen contract. The `srcTokenOwner` passed is `msg.sender`. The executor receives the identity of the token owner but CANNOT call transferFrom on the router's behalf -- the router has already transferred tokens from `msg.sender` to `desc.srcReceiver` BEFORE calling `_execute` (line 1002 vs 1005). The executor is just performing the swap logic (interacting with DEXes). The executor does NOT receive any special approval to move tokens from users.

**Risk:** NONE for V5 approval-based attacks. The executor cannot steal approved tokens.

---

### Callback functions and access control

| Callback | Access Control | Can it transferFrom a victim? |
|---|---|---|
| `uniswapV3SwapCallback` | Verifies `caller()` is a legitimate Uniswap V3 pool via CREATE2 address computation | No -- payer is constrained to msg.sender or address(this) by _makeSwap |
| `fillOrderPreInteraction` (external call TO a maker's contract) | N/A -- this is an outbound call, not inbound | No -- this is the router calling out |
| `fillOrderInteraction` (external call TO interaction target) | N/A -- outbound call | No |
| `fillOrderPostInteraction` (external call TO a maker's contract) | N/A -- outbound call | No |

---

## V5 vs V6 Security Model Comparison

| Aspect | V5 (AggregationRouterV5) | V6 |
|---|---|---|
| Number of transferFrom sites | 11 (including library/helper) | 10 |
| `from` in swap paths | Always `msg.sender` or `address(this)` | Always `msg.sender` or ECDSA-verified maker |
| `from` in limit orders | `msg.sender` (taker) or ECDSA-verified `order.maker` | Same |
| `from` in RFQ orders | `msg.sender` (taker) or ECDSA-verified `order.maker` | Same |
| `_callTransferFrom` extra data | Appends `makerAssetData`/`takerAssetData` after transferFrom args | Removed in V6 |
| `simulate()` delegatecall | Unrestricted target + data, always reverts | Removed or redesigned in V6 |
| Permit2 integration | None | Present |
| `uniswapV3SwapCallback` payer | From calldata, constrained by call chain + pool validation | From msg.sender directly |
| `destroy()` selfdestruct | Present (onlyOwner) | Removed |

---

## Conclusion: Can an attacker drain V5 approvals?

**NO -- there is no path for an arbitrary attacker to use the V5 router to transferFrom a victim's approved tokens.**

Every transferFrom call site is protected by one of:
1. Hardcoded `msg.sender` / `caller()` as the `from` address
2. ECDSA signature verification of the `from` address (limit/RFQ orders)
3. Access control that limits the callback caller to verified Uniswap V3 pools
4. The `from` being `address(this)` (the router itself, for WETH wrapping)

The V5 security model for approvals is **equivalent to V6** in terms of the core property: no unprivileged caller can specify an arbitrary victim as the `from` in a transferFrom.

### Differences that do NOT create exploitability but are worth noting:
1. **`_callTransferFrom` with trailing data**: Appends order maker/taker asset data after the transferFrom calldata. Standard ERC20s ignore this. If a non-standard token interprets trailing calldata, the maker controls `makerAssetData` (signed) and the taker controls nothing beyond standard args. V6 removed this pattern.
2. **`simulate()` with unrestricted delegatecall**: Always reverts, so no persistent state change. But this is an unusual design eliminated in V6.
3. **No Permit2**: V5 does not use Permit2. V6 adds Permit2 as an additional approval pathway.
4. **`destroy()` selfdestruct**: Owner-only, but if called, any remaining approvals to the V5 address become permanently useless (tokens cannot be retrieved via the contract). Post-Dencun, selfdestruct only sends ETH and does not destroy code, so this is less dangerous.

### Residual risk from stale V5 approvals:
The only risk from V5 approvals is **owner key compromise** -- if the V5 owner key is compromised, the owner could:
- Call `rescueFunds()` to extract tokens held by the router (but NOT tokens approved to the router)
- Call `destroy()` to selfdestruct the contract

Neither of these allows draining user-approved tokens. User ERC20 `approve(V5_router, amount)` only matters if the router actually calls `transferFrom(user, ...)`, and all such paths require the user themselves to be the `msg.sender`.
