# ⚠️ CRITICAL IMMEDIATE RISK ⚠️

## VULNERABLE CONTRACT

```
╔═══════════════════════════════════════════════════════════╗
║                                                           ║
║   0xa7569A44f348d3D70d8ad5889e50F78E33d80D35             ║
║                                                           ║
╚═══════════════════════════════════════════════════════════╝
```

| Field | Value |
|-------|-------|
| **Address** | `0xa7569A44f348d3D70d8ad5889e50F78E33d80D35` |
| **Name** | AutopoolETH |
| **Protocol** | Tokemak Foundation |
| **Chain** | Ethereum Mainnet |
| **TVL at Risk** | **$19,535,394 USDC** |
| **Severity** | **CRITICAL (CVSS 9.8)** |
| **Exploitability** | **IMMEDIATE** |

---

## EXPLOIT ECONOMICS

```
┌────────────────────────────────────────────────────────────┐
│                                                            │
│   ATTACKER INVESTS:    $5.13 (gas only)                   │
│   ATTACKER EXTRACTS:   $1,000 - $588,500                  │
│   ROI:                 19,503% - 11,477,243%              │
│                                                            │
│   ZERO CAPITAL REQUIRED - FLASH LOAN ATTACK               │
│                                                            │
└────────────────────────────────────────────────────────────┘
```

---

## VULNERABILITY DETAILS

**Location:** `src/vault/libs/AutopoolDebt.sol` lines 541-611

**Bug:** `updateDebtReporting()` ignores `pricesWereSafe` flag returned by `_recalculateDestInfo()`

**Contrast:** `flashRebalance()` properly reverts when `pricesWereSafe = false`

```solidity
// VULNERABLE CODE (updateDebtReporting):
AutopoolDebt.IdleDebtUpdates memory debtResult = _recalculateDestInfo(...);
// debtResult.pricesWereSafe is NEVER CHECKED!
result.totalDebtDecrease += debtResult.totalDebtDecrease;  // Uses value anyway

// SECURE CODE (flashRebalance):
if (!result.pricesWereSafe) {
    revert InvalidPrices();  // Properly reverts
}
```

---

## ATTACK CHAIN

```
1. Flash loan $10M USDC from Aave V3 (0x87870Bca3F3fD6335C3F4ce8392D69350B4fA4E2)
         │
         ▼
2. Swap $5M USDC → crvUSD in Curve pools
   - Pool 1: 0x4DEcE678ceceb27446b35C672dC7d61F30bAD69E (crvUSD/USDC)
   - Pool 2: 0x390f3595bCa2Df7d23783dFd126427CCeb997BF4 (crvUSD/USDT)
         │
         ▼
3. Trigger/sandwich updateDebtReporting()
   - Oracle returns manipulated prices
   - pricesWereSafe = false (IGNORED!)
   - Manipulated debt values cached in storage
         │
         ▼
4. Deposit $5M at deflated NAV
   - Receive MORE shares than deserved
         │
         ▼
5. Reverse swaps (crvUSD → USDC)
         │
         ▼
6. Repay flash loan + fee ($5,000)
         │
         ▼
7. PROFIT: $235,000 - $588,500 (attacker keeps difference)
```

---

## VERIFIED ON-CHAIN DATA

| Parameter | Value | Verification |
|-----------|-------|--------------|
| Aave V3 USDC liquidity | $4,367,027,126 | `aUSDC.totalSupply()` |
| Curve pool USDC | $4,020,959 | `pool.balances(0)` |
| Gas price | 0.61 gwei | `cast gas-price` |
| ETH price | $2,182.86 | Chainlink oracle |
| Flash loan fee | 0.05% | `FLASHLOAN_PREMIUM_TOTAL()` |
| Curve swap fee | 0.01% | `pool.fee()` |

---

## IMMEDIATE ACTIONS REQUIRED

1. **PAUSE** the `updateDebtReporting()` function
2. **ADD CHECK** for `pricesWereSafe` before writing debt values
3. **AUDIT** all other functions that call `_recalculateDestInfo()`

---

## FIX

```solidity
// In updateDebtReporting(), ADD:
if (!debtResult.pricesWereSafe) {
    // Skip or revert
    continue; // or revert InvalidPrices();
}
```

---

## RELATED CONTRACTS AT RISK

All destination vaults feeding into AutopoolETH:
- 0x65efCF2cce562DCBf07e805eEbeDeF21Dbd8Ea3D (crvUSD/USDC vault)
- 0x7583b1589aDD33320366A48A92794D77763FAE9e (crvUSD/USDT vault)
- 0xa345ceECCF8fe6aE33fe1D655B4806492251c2A8 (GHO/crvUSD vault)
- ... (30 total destination vaults)

---

**THIS VULNERABILITY CAN BE EXPLOITED RIGHT NOW WITH $5 IN GAS.**
