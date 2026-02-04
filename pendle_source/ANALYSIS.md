# PendleERC4626NoRedeemWithAdapterSY Contract Analysis

**Contract Address:** `0xb9cdea29f7f976ce1a50944f3b6d0569ee88d9c4`
**Contract Name:** `PendleERC4626NoRedeemWithAdapterSY`
**Compiler Version:** `v0.8.24+commit.e11b9ed9`

---

## Contract Hierarchy

```
PendleERC4626NoRedeemWithAdapterSY
    ├── SYBaseUpg
    │   ├── IStandardizedYield
    │   ├── PendleERC20PermitUpg
    │   │   ├── PendleERC20Upg (with built-in ReentrancyGuard)
    │   │   │   ├── IERC20
    │   │   │   └── IERC20Metadata
    │   │   ├── IERC20Permit
    │   │   └── EIP712Upgradeable
    │   ├── TokenHelper
    │   ├── BoringOwnableUpgradeable__deprecated
    │   └── Pausable
    ├── MerklRewardAbstract__NoStorage
    └── IPStandardizedYieldWithAdapter
```

---

## Key State Variables

### Immutable (set in constructor)
| Variable | Type | Description |
|----------|------|-------------|
| `yieldToken` | `address` | The underlying ERC4626 vault address (set in `SYBaseUpg`) |
| `asset` | `address` | The underlying asset of the ERC4626 vault (e.g., USDC) |
| `decimals` | `uint8` | Token decimals (inherited from yieldToken) |

### Mutable Storage
| Variable | Type | Description |
|----------|------|-------------|
| `adapter` | `address` | Optional adapter for converting non-native tokens |
| `owner` | `address` | Contract owner (from BoringOwnableUpgradeable) |
| `_totalSupply` | `uint248` | Total SY tokens minted (packed with reentrancy status) |
| `_status` | `uint8` | Reentrancy guard status (packed with totalSupply) |

---

## DEPOSIT FUNCTION - Detailed Flow

### Entry Point: `SYBaseUpg.deposit()`

```solidity
function deposit(
    address receiver,      // Who receives the minted SY tokens
    address tokenIn,       // Token being deposited
    uint256 amountTokenToDeposit,  // Amount to deposit
    uint256 minSharesOut   // Slippage protection
) external payable nonReentrant returns (uint256 amountSharesOut)
```

### Deposit Flow Diagram

```
User calls deposit(receiver, tokenIn, amount, minShares)
                    │
                    ▼
    ┌─────────────────────────────────────┐
    │  1. VALIDATION                       │
    │  • isValidTokenIn(tokenIn) check    │
    │  • amountTokenToDeposit != 0        │
    └─────────────────────────────────────┘
                    │
                    ▼
    ┌─────────────────────────────────────┐
    │  2. TRANSFER IN (TokenHelper)       │
    │  • _transferIn(tokenIn, msg.sender, │
    │    amountTokenToDeposit)            │
    │  • Uses SafeERC20.safeTransferFrom  │
    └─────────────────────────────────────┘
                    │
                    ▼
    ┌─────────────────────────────────────┐
    │  3. INTERNAL _deposit()             │
    │  (PendleERC4626NoRedeemWithAdapterSY)│
    └─────────────────────────────────────┘
                    │
        ┌───────────┴───────────┐
        ▼                       ▼
┌───────────────────┐   ┌───────────────────┐
│ tokenIn is        │   │ tokenIn is NOT    │
│ yieldToken or     │   │ yieldToken or     │
│ asset             │   │ asset             │
└───────────────────┘   └───────────────────┘
        │                       │
        │               ┌───────┴───────┐
        │               │ 3a. ADAPTER   │
        │               │ CONVERSION    │
        │               │ • _transferOut│
        │               │   to adapter  │
        │               │ • adapter.    │
        │               │   convertTo   │
        │               │   Deposit()   │
        │               │ → returns     │
        │               │   asset amount│
        │               └───────────────┘
        │                       │
        └───────────┬───────────┘
                    ▼
    ┌─────────────────────────────────────┐
    │  4. DEPOSIT INTO ERC4626 VAULT      │
    │  IF tokenIn == yieldToken:          │
    │    amountSharesOut = amountDeposited│
    │  ELSE:                              │
    │    amountSharesOut = IERC4626(      │
    │      yieldToken).deposit(           │
    │      amountDeposited, address(this))│
    └─────────────────────────────────────┘
                    │
                    ▼
    ┌─────────────────────────────────────┐
    │  5. INVARIANT CHECK                 │
    │  require(_selfBalance(yieldToken)   │
    │    >= totalSupply() + amountShares) │
    └─────────────────────────────────────┘
                    │
                    ▼
    ┌─────────────────────────────────────┐
    │  6. SLIPPAGE CHECK                  │
    │  require(amountSharesOut >=         │
    │    minSharesOut)                    │
    └─────────────────────────────────────┘
                    │
                    ▼
    ┌─────────────────────────────────────┐
    │  7. MINT SY TOKENS                  │
    │  _mint(receiver, amountSharesOut)   │
    │  • Updates _totalSupply             │
    │  • Updates _balances[receiver]      │
    │  • Emits Transfer event             │
    └─────────────────────────────────────┘
                    │
                    ▼
    ┌─────────────────────────────────────┐
    │  8. EMIT DEPOSIT EVENT              │
    │  Deposit(msg.sender, receiver,      │
    │    tokenIn, amountDeposited,        │
    │    amountSharesOut)                 │
    └─────────────────────────────────────┘
```

### `_deposit()` Implementation

```solidity
function _deposit(
    address tokenIn,
    uint256 amountDeposited
) internal virtual override returns (uint256 amountSharesOut) {
    // PATH A: Token needs adapter conversion
    if (tokenIn != yieldToken && tokenIn != asset) {
        // Transfer token to adapter
        _transferOut(tokenIn, adapter, amountDeposited);
        // Adapter converts to asset
        (tokenIn, amountDeposited) = (
            asset,
            IStandardizedYieldAdapter(adapter).convertToDeposit(tokenIn, amountDeposited)
        );
    }

    // PATH B: Direct yieldToken deposit (1:1 minting)
    if (tokenIn == yieldToken) {
        amountSharesOut = amountDeposited;
    }
    // PATH C: Asset deposit into ERC4626 vault
    else {
        amountSharesOut = IERC4626(yieldToken).deposit(amountDeposited, address(this));
    }

    // INVARIANT: Contract must hold enough yieldTokens to back all SY tokens
    require(_selfBalance(yieldToken) >= totalSupply() + amountSharesOut, "SY: insufficient shares");
}
```

### Valid Tokens In

```solidity
function isValidTokenIn(address token) public view virtual override returns (bool) {
    if (adapter == address(0)) {
        // Only yieldToken and asset allowed when no adapter
        return token == yieldToken || token == asset;
    }
    // With adapter: yieldToken, asset, or any adapter-supported token
    return token == yieldToken ||
           token == asset ||
           IStandardizedYieldAdapter(adapter).getAdapterTokensDeposit().contains(token);
}
```

---

## REDEEM FUNCTION - Detailed Flow

### Entry Point: `SYBaseUpg.redeem()`

```solidity
function redeem(
    address receiver,           // Who receives output tokens
    uint256 amountSharesToRedeem, // SY tokens to burn
    address tokenOut,           // Desired output token
    uint256 minTokenOut,        // Slippage protection
    bool burnFromInternalBalance // Burn from address(this) or msg.sender
) external nonReentrant returns (uint256 amountTokenOut)
```

### Redeem Flow Diagram

```
User calls redeem(receiver, shares, tokenOut, minOut, burnFromInternal)
                    │
                    ▼
    ┌─────────────────────────────────────┐
    │  1. VALIDATION                       │
    │  • isValidTokenOut(tokenOut) check  │
    │  • amountSharesToRedeem != 0        │
    └─────────────────────────────────────┘
                    │
                    ▼
    ┌─────────────────────────────────────┐
    │  2. BURN SY TOKENS                  │
    │  IF burnFromInternalBalance:        │
    │    _burn(address(this), amount)     │
    │  ELSE:                              │
    │    _burn(msg.sender, amount)        │
    │  • Updates _balances                │
    │  • Decrements _totalSupply          │
    │  • Emits Transfer event             │
    └─────────────────────────────────────┘
                    │
                    ▼
    ┌─────────────────────────────────────┐
    │  3. INTERNAL _redeem()              │
    │  (PendleERC4626NoRedeemWithAdapterSY)│
    └─────────────────────────────────────┘
                    │
                    ▼
    ┌─────────────────────────────────────┐
    │  ** CRITICAL: NO VAULT REDEEM **    │
    │  _transferOut(yieldToken, receiver, │
    │    amountSharesToRedeem)            │
    │  return amountSharesToRedeem        │
    │                                     │
    │  User receives yieldToken (vault    │
    │  shares), NOT underlying asset      │
    └─────────────────────────────────────┘
                    │
                    ▼
    ┌─────────────────────────────────────┐
    │  4. SLIPPAGE CHECK                  │
    │  require(amountTokenOut >= minOut)  │
    └─────────────────────────────────────┘
                    │
                    ▼
    ┌─────────────────────────────────────┐
    │  5. EMIT REDEEM EVENT               │
    │  Redeem(msg.sender, receiver,       │
    │    tokenOut, amountShares, amountOut│
    └─────────────────────────────────────┘
```

### `_redeem()` Implementation

```solidity
function _redeem(
    address receiver,
    address /*tokenOut*/,  // IGNORED - always outputs yieldToken
    uint256 amountSharesToRedeem
) internal virtual override returns (uint256) {
    // NO ERC4626 redeem call - just transfer the yieldToken (vault shares)
    _transferOut(yieldToken, receiver, amountSharesToRedeem);
    return amountSharesToRedeem;  // 1:1 ratio
}
```

### Valid Tokens Out

```solidity
function isValidTokenOut(address token) public view virtual override returns (bool) {
    return token == yieldToken;  // ONLY yieldToken can be redeemed
}

function getTokensOut() public view virtual override returns (address[] memory res) {
    return ArrayLib.create(yieldToken);  // Only one output token
}
```

---

## External Calls Summary

### During Deposit

| Call | Target | Purpose |
|------|--------|---------|
| `safeTransferFrom()` | `tokenIn` (ERC20) | Transfer tokens from user |
| `safeTransfer()` | `tokenIn` (ERC20) | Transfer to adapter (if needed) |
| `convertToDeposit()` | `adapter` | Convert non-native token to asset |
| `deposit()` | `yieldToken` (ERC4626) | Deposit asset into vault |
| `balanceOf()` | `yieldToken` | Check invariant |

### During Redeem

| Call | Target | Purpose |
|------|--------|---------|
| `safeTransfer()` | `yieldToken` (ERC20) | Transfer vault shares to receiver |

---

## State Changes Summary

### Deposit
1. **User's tokenIn balance**: Decreases by `amountTokenToDeposit`
2. **Adapter's asset balance**: Temporary (if adapter used)
3. **Contract's yieldToken balance**: Increases by `amountSharesOut`
4. **Contract's _totalSupply**: Increases by `amountSharesOut`
5. **Receiver's SY balance**: Increases by `amountSharesOut`

### Redeem
1. **Burner's SY balance**: Decreases by `amountSharesToRedeem`
2. **Contract's _totalSupply**: Decreases by `amountSharesToRedeem`
3. **Contract's yieldToken balance**: Decreases by `amountSharesToRedeem`
4. **Receiver's yieldToken balance**: Increases by `amountSharesToRedeem`

---

## Key Observations

### 1. "NoRedeem" Pattern
This contract is named `PendleERC4626NoRedeemWithAdapterSY` because:
- **Deposit**: Calls underlying ERC4626's `deposit()` function
- **Redeem**: Does NOT call underlying ERC4626's `redeem()` function
- User receives vault shares (yieldToken), not underlying assets
- To get underlying assets, user must call `redeem()` on the yieldToken directly

### 2. Exchange Rate
```solidity
function exchangeRate() public view virtual override returns (uint256) {
    return IERC4626(yieldToken).convertToAssets(PMath.ONE);  // 1e18 shares → assets
}
```
The exchange rate is derived from the underlying ERC4626 vault's conversion rate.

### 3. Share Invariant
```solidity
require(_selfBalance(yieldToken) >= totalSupply() + amountSharesOut, "SY: insufficient shares");
```
The contract ensures it always holds enough yieldToken shares to back all minted SY tokens.

### 4. Adapter Pattern
- Adapter must implement `IStandardizedYieldAdapter`
- Adapter's `PIVOT_TOKEN()` must equal `asset`
- Allows depositing non-native tokens by converting through adapter
- Adapter is NOT used for redemptions (only yieldToken output)

### 5. Reentrancy Protection
Built into `PendleERC20Upg`:
- Status packed with `_totalSupply` (uint248 + uint8)
- `nonReentrant` modifier on `deposit()`, `redeem()`, `transfer()`, `transferFrom()`

### 6. Pausable
- Owner can call `pause()` / `unpause()`
- `_beforeTokenTransfer` hook enforces `whenNotPaused`
- Affects all token transfers including deposit/redeem

---

## File Locations

| File | Path |
|------|------|
| Main Contract | `/home/user/contracs/pendle_source/contracts/sy/contracts/core/StandardizedYield/implementations/Adapter/extensions/PendleERC4626NoRedeemWithAdapterSY.sol` |
| SYBaseUpg | `/home/user/contracs/pendle_source/contracts/sy/contracts/core/StandardizedYield/SYBaseUpg.sol` |
| IStandardizedYield | `/home/user/contracs/pendle_source/contracts/sy/contracts/interfaces/IStandardizedYield.sol` |
| IStandardizedYieldAdapter | `/home/user/contracs/pendle_source/contracts/sy/contracts/interfaces/IStandardizedYieldAdapter.sol` |
| TokenHelper | `/home/user/contracs/pendle_source/contracts/sy/contracts/core/libraries/TokenHelper.sol` |
| IERC4626 | `/home/user/contracs/pendle_source/contracts/sy/contracts/interfaces/IERC4626.sol` |
| PendleERC20Upg | `/home/user/contracs/pendle_source/contracts/sy/contracts/core/erc20/PendleERC20Upg.sol` |
| PMath | `/home/user/contracs/pendle_source/contracts/sy/contracts/core/libraries/math/PMath.sol` |
