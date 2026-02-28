# Morpho Blue ERC-4626 Donation Attack Surface Analysis

## Date: 2026-02-28
## Chain: Ethereum Mainnet (block ~24554000)

## Executive Summary

MorphoChainlinkOracleV2 reads `convertToAssets()` from ERC-4626 vaults LIVE with **NO growth cap, NO caching, NO TWAP**. This is fundamentally different from Aave's CAPO mechanism which caps yearly growth rates.

For any Morpho Blue market where:
1. The oracle uses `BASE_VAULT` pointing to an ERC-4626 vault
2. That vault's `totalAssets()` is inflatable via direct token donation
3. The vault has LOW TVL relative to borrow liquidity

...the exchange rate can be atomically manipulated via donation, inflating collateral value and enabling over-borrowing.

## Oracle Architecture

```solidity
// MorphoChainlinkOracleV2.price()
return SCALE_FACTOR.mulDiv(
    BASE_VAULT.getAssets(SAMPLE) * BASE_FEED_1.getPrice() * BASE_FEED_2.getPrice(),
    QUOTE_VAULT.getAssets(SAMPLE) * QUOTE_FEED_1.getPrice() * QUOTE_FEED_2.getPrice()
);
// VaultLib.getAssets() simply calls vault.convertToAssets(shares) — LIVE, NO CAP
```

## Comparison: Aave CAPO vs Morpho Oracle

| Feature | Aave sUSDe Oracle (CAPO) | Morpho MorphoChainlinkOracleV2 |
|---------|--------------------------|-------------------------------|
| Reads convertToAssets() | YES | YES |
| Growth cap | YES — linear cap from snapshot | **NO** |
| Snapshot delay | 14 days minimum | N/A |
| Admin required | Yes (RISK_ADMIN) | N/A |
| Atomic manipulation | BLOCKED | **POSSIBLE** |

## Known Exploit Precedents

1. **ResupplyFi** ($9.56M, June 2025): Empty cvcrvUSD vault, $4K flash loan, infinite rate inflation
2. **Venus/wUSDM** ($902K, Feb 2025): wUSDM vault on ZKsync, $4M flash loan, 65% rate inflation
3. **Morpho PAXG/USDC** ($230K, Oct 2024): Misconfigured SCALE_FACTOR

## Target Classification: Morpho Blue Vault Collateral Markets

### Category A: DONATION RESISTANT (safe)
| Vault | Mechanism | Markets |
|-------|-----------|---------|
| sUSDS (Sky) | SSR rate accumulator (chi) | $112M USDT, $14M AUSD, $10M PYUSD |
| stUSDS (Sky) | Internal chi accumulator | $44M USDT, $43M USDC, $5M USDS |
| syrupUSDC/USDT (Maple) | Revenue Distribution Token | $52M USDC, $19M PYUSD, $19M USDT |
| wstETH (Lido) | Oracle-controlled rate | $121M WETH, $79M USDC, $24M USDT |
| weETH (ether.fi) | Oracle-controlled rate | $44M WETH, $2M USDC |

### Category B: CONFIRMED DONATION SENSITIVE
| Vault | totalAssets() | TVL | Morpho Borrows | Attack Viability |
|-------|--------------|-----|----------------|-----------------|
| sUSDe (Ethena) | balanceOf - unvested | ~$6B | $83M PYUSD, $50M USDtb, $5.5M msUSD, $3M DAI | TVL too large — impractical |
| pufETH (Puffer) | stETH.balanceOf | ~$62M | $531K WETH | TVL too large for borrow amount |

### Category C: UNKNOWN — NEEDS ON-CHAIN VERIFICATION (priority targets)
| Vault | Address | Morpho Borrows | Priority |
|-------|---------|----------------|----------|
| **savETH** | 0xDA06eE2d... | $2.4M WETH | **HIGHEST** — $94K TVL if true |
| **siUSD** | 0xDBDC1Ef5... | $73M USDC | **HIGH** — massive borrow liquidity |
| **sUSDD** | 0xC5d6A7B6... | $60.3M USDT | HIGH |
| **stcUSD** | 0x88887bE4... | $31.5M USDC | MEDIUM |
| wsrUSD | 0xd3fD6320... | $21M USDT | MEDIUM |
| sNUSD | 0x08EFCC2F... | $9.4M USDC | MEDIUM |
| syzUSD | 0x6DFF69eb... | $7.7M AUSD | LOW |
| savUSD | 0xb8D89678... | $2.8M USDC | LOW |
| ynETHx | 0x657d9ABA... | $6M combined | MEDIUM |

## Attack Economics

### Collateral-Side Donation Attack (over-borrowing)
```
profit = A * (T+A+D)/(T+A) * LLTV - (A + D)
where: A = deposit, D = donation, T = vault totalAssets, LLTV = liquidation LTV
```

This is profitable ONLY when `A * LLTV / T > 1`, i.e., deposit > T/LLTV.
For tiny TVL vaults (T << available flash loans), this CAN be profitable.

### Loan-Side Donation Attack (self-liquidation via Venus pattern)
If the LOAN token is an ERC-4626 vault:
1. Deposit normal collateral (WETH), borrow vault token
2. Donate to vault → loan value increases → borrower underwater
3. Liquidate own position via second account → extract liquidation bonus
4. Profit = liquidation bonus * seized collateral - donation cost

Morpho explicitly warns: "vaults that can receive donations shouldn't be used as loan/quote assets"

## Next Steps
1. Verify savETH totalAssets() — if balanceOf-based with $94K TVL, IMMEDIATELY ACTIONABLE
2. Verify siUSD, sUSDD, stcUSD totalAssets() implementations
3. Check if any Morpho market uses a vault as QUOTE (loan) asset
4. Run on-chain scanner for all 901 MorphoChainlinkOracleV2 oracles
5. For viable targets: simulate donation + borrow on Tenderly fork
