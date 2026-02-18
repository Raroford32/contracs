# Value Flows — Liquity V1

## Money Entry Points
1. **openTrove** (BorrowerOps): ETH in → LUSD minted → user gets LUSD, protocol holds ETH in ActivePool
2. **provideToSP** (StabilityPool): LUSD from user → SP holds LUSD deposits
3. **stake** (LQTYStaking): LQTY from user → staking contract holds LQTY

## Money Exit Points
1. **closeTrove** (BorrowerOps): user repays LUSD+fee → gets ETH back from ActivePool
2. **redeemCollateral** (TroveManager): user burns LUSD → gets ETH from ActivePool (minus redemption fee)
3. **withdrawFromSP** (StabilityPool): user gets LUSD back + ETH gains from liquidations
4. **claimCollateral** (CollSurplusPool): user claims surplus ETH from capped Recovery Mode liquidation
5. **unstake** (LQTYStaking): user gets LQTY back + accumulated ETH+LUSD fees

## Value Transforms
1. **Liquidation (SP offset)**: Trove's LUSD debt absorbed by SP → SP LUSD burned, SP gets ETH → depositors' LUSD decreases, ETH increases
2. **Liquidation (redistribution)**: When SP insufficient → Trove's debt+coll redistributed to all active troves proportional to stake
3. **Redemption**: LUSD→ETH at oracle price, minus fee. Walks lowest-ICR-first troves.
4. **Borrowing fee**: LUSD minted to LQTYStaking on each borrow (baseRate + 0.5% floor)
5. **Redemption fee**: ETH deducted from redemption proceeds → sent to LQTYStaking (baseRate + 0.5% floor)

## Fee Extraction
- **Borrowing fee**: Borrower → LQTYStaking (LUSD). Range: [0.5%, 5%] of LUSD borrowed
- **Redemption fee**: Redeemer → LQTYStaking (ETH). Range: [0.5%, 100%] of ETH redeemed
- **Gas compensation**: Protocol → Liquidator. Fixed 200 LUSD + 0.5% of coll

## Actor Model
| Actor | Wants | Power | Dual Roles |
|-------|-------|-------|------------|
| Borrower | Leverage on ETH; LUSD liquidity | Open/close/adjust troves | Can also be SP depositor, liquidator, redeemer |
| SP Depositor | Earn ETH from liquidations + LQTY rewards | Deposit/withdraw LUSD | Can also be borrower (withdrawETHGainToTrove) |
| Redeemer | Arbitrage LUSD→ETH when LUSD < $1 | Burn LUSD for ETH | Forces other borrowers' troves to close |
| Liquidator | Gas compensation | Trigger liquidation of undercollateralized troves | MEV searcher role |
| LQTY Staker | Earn protocol fees (ETH+LUSD) | Stake/unstake LQTY | No governance power in V1 |

## Key Dual-Role Conflicts
- Redeemer who is also lowest-ICR borrower: can redeem their own trove's debt (no real gain)
- SP depositor who is also borrower: benefits from liquidations that increase protocol risk
- Large SP depositor: can dilute other depositors' liquidation gains (but also dilutes own)
