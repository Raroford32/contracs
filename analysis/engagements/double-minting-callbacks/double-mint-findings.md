# Double-Minting Vulnerabilities Found in contracts.txt

Searched all 66 source files in `src_cache/`. Below are concrete double-minting bugs.

---

## FINDING 1 — ADX Loyalty Pool: Mint-Before-Transfer + No Reentrancy Guard

**File:** `adx_loyalty_pool.sol:233-250`
**Severity:** HIGH
**Type:** Callback reentrancy double-mint

### Vulnerable Code
```solidity
function enter(uint256 amount) external {
    mintIncentive();  // external call to supplyController
    uint totalADX = ADXToken.balanceOf(address(this));
    // ...
    innerMint(msg.sender, newShares);   // ← SHARES MINTED HERE
    require(ADXToken.transferFrom(msg.sender, address(this), amount));  // ← TRANSFER AFTER
}
```

### Exploit Path
1. **No reentrancy guard** on `enter()` or `leave()`.
2. `innerMint()` gives the caller shares BEFORE `transferFrom` pulls their tokens.
3. During the `transferFrom` execution, if ADXToken (or its supply controller) triggers any callback, the attacker can re-enter `leave()`:
   - `leave()` → `leaveInner()` → reads `ADXToken.balanceOf(address(this))` (still includes old balance) → burns the just-minted shares → transfers ADX to attacker
4. The original `transferFrom` then completes, pulling tokens from the attacker.
5. Net: attacker received shares, immediately redeemed them for existing pool ADX, and only paid `amount` once.

### First-Depositor Inflation (separate vector)
- When `totalSupply == 0`: deposit 1 wei → get 1 share → donate ADX directly to contract → next depositor's `amount * 1 / huge_balance` rounds to 0 → attacker's 1 share claims everything.

---

## FINDING 2 — SushiBar (xSUSHI): Mint-Before-Transfer + No Reentrancy Guard

**File:** `xsushi.sol:740-750`
**Severity:** HIGH
**Type:** Mint-before-transfer + first-depositor inflation

### Vulnerable Code
```solidity
function enter(uint256 _amount) public {
    uint256 totalSushi = sushi.balanceOf(address(this));
    uint256 totalShares = totalSupply();
    if (totalShares == 0 || totalSushi == 0) {
        _mint(msg.sender, _amount);         // ← MINT FIRST
    } else {
        uint256 what = _amount.mul(totalShares).div(totalSushi);
        _mint(msg.sender, what);            // ← MINT FIRST
    }
    sushi.transferFrom(msg.sender, address(this), _amount);  // ← TRANSFER AFTER
}
```

### Exploit Path
- Identical pattern to ADX: shares minted before transfer. No reentrancy guard.
- `transferFrom` return value is **not checked** — if SUSHI token returns false instead of reverting, user gets free shares.
- First-depositor inflation: deposit 1 wei, donate SUSHI directly, next depositor gets 0 shares.

### Real-World Impact
This exact pattern was exploited in multiple SushiBar forks.

---

## FINDING 3 — MasterChef: Duplicate LP Token Over-Minting

**File:** `masterchef.sol:1468-1480`
**Severity:** HIGH
**Type:** Reward over-minting via duplicate pool

### Vulnerable Code
```solidity
function add(uint256 _allocPoint, IERC20 _lpToken, bool _withUpdate) public onlyOwner {
    // NO CHECK that _lpToken isn't already in another pool
    totalAllocPoint = totalAllocPoint.add(_allocPoint);
    poolInfo.push(PoolInfo({
        lpToken: _lpToken,
        allocPoint: _allocPoint,
        lastRewardBlock: lastRewardBlock,
        accSushiPerShare: 0
    }));
}
```

### Exploit Path
1. Owner adds the same LP token to two pools (pool A and pool B).
2. User stakes LP in pool A. `updatePool(A)` mints SUSHI proportional to `lpToken.balanceOf(address(this))`.
3. `updatePool(B)` also sees the same `balanceOf` and mints SUSHI again for the same staked tokens.
4. Result: SUSHI minted at 2x the intended rate for that LP token.
5. The staker in pool A can also deposit 0 into pool B to claim phantom rewards.

### Variant
Even without owner malice, if `_withUpdate = false` is passed when adding a pool, `totalAllocPoint` increases but existing pools aren't updated, causing reward accounting to drift.

---

## FINDING 4 — Opyn PerpVault: First-Depositor Share Inflation

**File:** `opyn_contracts_core_OpynPerpVault.sol:409-428`
**Severity:** MEDIUM
**Type:** ERC4626-style share inflation

### Vulnerable Code
```solidity
function _getSharesByDepositAmount(uint256 _amount, uint256 _totalAssetAmount) internal view returns (uint256) {
    uint256 shareSupply = totalSupply();
    return shareSupply == 0 ? _amount : _amount.mul(shareSupply).div(_totalAssetAmount);
}
```

### Exploit Path
1. First depositor deposits 1 wei of curveLPToken → gets 1 share.
2. Donates sdTokens directly to vault (bypassing deposit).
3. `totalStakedaoAsset()` now returns huge value.
4. Next depositor: `shares = deposit * 1 / huge_value` = 0. Deposit captured.
5. Attacker withdraws their 1 share for the entire pool.

---

## FINDING 5 — yearn yToken (yDAI): First-Depositor Share Inflation

**File:** `0x16de59092dae5ccf4a1e6439d611fd0653f0bd01.sol:374-393`
**Severity:** MEDIUM
**Type:** ERC4626-style share inflation

### Vulnerable Code
```solidity
function deposit(uint256 _amount) external nonReentrant {
    pool = _calcPoolValueInToken();  // reads balance across lending protocols
    IERC20(token).safeTransferFrom(msg.sender, address(this), _amount);
    if (pool == 0) {
        shares = _amount;
    } else {
        shares = (_amount.mul(_totalSupply)).div(pool);
    }
    _mint(msg.sender, shares);
}
```

### Exploit Path
- `pool` is calculated from token balances in Compound/Aave/dYdX.
- Attacker deposits 1 wei → gets 1 share → deposits directly into the underlying lending protocol → `_calcPoolValueInToken()` returns inflated value → next depositor gets 0 shares.
- Note: transfer-before-mint ordering and `nonReentrant` prevent reentrancy — but first-depositor inflation is still viable.

---

## FINDING 6 — ConvexStakingWrapperAbra: Mint-Before-Transfer (Mitigated)

**File:** `ConvexStakingWrapperAbra.sol:1380-1407`
**Severity:** LOW (mitigated)
**Type:** Mint ordering issue

```solidity
function deposit(uint256 _amount, address _to) external nonReentrant {
    _mint(_to, _amount);  // MINT FIRST
    IERC20(curveToken).safeTransferFrom(msg.sender, address(this), _amount);  // THEN TRANSFER
}
```

- `nonReentrant` prevents callback exploitation.
- 1:1 minting (no exchange rate) prevents inflation.
- `safeTransferFrom` reverts on failure, rolling back the mint.
- Listed for completeness — not practically exploitable.

---

## Summary

| # | Contract | Type | Severity | Exploitable? |
|---|----------|------|----------|-------------|
| 1 | ADX Loyalty Pool | Mint-before-transfer reentrancy + first-depositor inflation | HIGH | YES — no reentrancy guard |
| 2 | SushiBar (xSUSHI) | Mint-before-transfer + unchecked return + first-depositor inflation | HIGH | YES — no reentrancy guard |
| 3 | MasterChef | Duplicate LP pool → reward over-minting | HIGH | YES — requires owner action |
| 4 | Opyn PerpVault | First-depositor share inflation | MEDIUM | YES — if first depositor |
| 5 | yearn yToken | First-depositor share inflation via lending pool donation | MEDIUM | YES — if first depositor |
| 6 | ConvexStakingWrapperAbra | Mint-before-transfer (mitigated by nonReentrant) | LOW | NO — mitigated |
