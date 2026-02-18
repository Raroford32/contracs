# Hypotheses — Curve Tricrypto2

## SUMMARY: All hypotheses FALSIFIED — no E3-qualifying vulnerability found.

---

## H1: Donation + Gulp + Swap Profit (Balance Manipulation)
BROKEN ASSUMPTION: A2 (balances reflects true holdings) + A11 (gulp is safe)
REASONING: claim_admin_fees() gulps balanceOf() into self.balances. Donation creates imbalance.
  Step 1: Flash loan large amount of USDT
  Step 2: Send USDT directly to pool (donation, no LP minting)
  Step 3: Call claim_admin_fees() -> pool syncs balances -> D recalculated with extra USDT
  Step 4: Pool now has excess USDT -> internal price of USDT drops relative to WBTC/WETH
  Step 5: Flash loan WBTC
  Step 6: Swap WBTC -> USDT at the manipulated favorable rate
  Step 7: Get more USDT than fair market value
  Step 8: Repay flash loans
  Step 9: Net profit = excess USDT from favorable swap - donation cost
FORK TEST RESULT: **FALSIFIED** — NET NEGATIVE
  - 1M USDT donation produced only $18K swap advantage (1 WBTC swap)
  - Donation is irrecoverable without LP tokens
  - Evidence: CurveTricrypto.t.sol::test_H1_DonationGulpSwap

## H2: Price Oracle Manipulation -> External Protocol Exploitation
BROKEN ASSUMPTION: A5 (oracle resists single-block manipulation)
FORK TEST RESULT: **PARTIALLY CONFIRMED as cross-protocol risk, NOT Tricrypto2 vulnerability**
  - Same-block: oracle moves only 0.001% (timestamp check prevents update)
  - Multi-block (10 blocks, 2M USDT donation): 700 bps (7%) drift
  - Cost: 2M USDT irrecoverable donation
  - Need >$28.6M external exposure to profit
  - Evidence: CurveTricryptoDeep.t.sol::test_Deep2, CurveTricryptoFinal.t.sol::test_Final2
  - CONCLUSION: Known AMM oracle risk, not specific to Tricrypto2

## H3: Virtual Price Decrease During A/Gamma Ramp
BROKEN ASSUMPTION: A3 (virtual_price monotonically increases)
FEASIBILITY: NOT TESTED — requires owner action (ramp_A_gamma), admin-only
  - future_A_gamma_time = 0, no active ramp
  - Would require compromised admin -> out of scope for public mempool attacker

## H4: Donation + Gulp -> Virtual Price Inflation -> LP Minting
BROKEN ASSUMPTION: A2 + A11
FORK TEST RESULT: **FALSIFIED** — VP inflation trivial
  - 1M USDT donation only increases VP by 7 bps
  - LP minting after donation gives fair share but donation already distributed to ALL LP holders
  - Evidence: CurveTricrypto.t.sol::test_H4_DonationVirtualPriceInflation

## H5: Read-Only Reentrancy via Virtual Price
BROKEN ASSUMPTION: External protocols trust get_virtual_price() during state transitions
FORK TEST RESULT: **FALSIFIED** — VP staleness negligible
  - VP increase from $1M swap: only 2 bps
  - During ETH callback (between balance update and tweak_price), VP is stale by at most 2 bps
  - No external protocol could profitably exploit this
  - Evidence: CurveTricrypto.t.sol::test_H5, CurveTricryptoFinal.t.sol::test_Final3

## H6: Fee-on-Transfer Token Exploitation
BROKEN ASSUMPTION: A1 (exact transfer amounts)
FORK TEST RESULT: **NOT APPLICABLE** — USDT fee is currently 0 basis points
  - Future risk only; no current exploitation

## H7: Sandwich Attack on add_liquidity
FORK TEST RESULT: **FALSIFIED** — CryptoSwap defeats sandwich
  - Attacker LOST 6.16 WETH attempting sandwich on single-sided deposit
  - CryptoSwap's concentrated liquidity and dynamic fees make sandwich unprofitable
  - Evidence: CurveTricrypto.t.sol::test_H7_SandwichAddLiquidity

## H8: xcp_profit Manipulation via Donation
BROKEN ASSUMPTION: A6 + A11
FORK TEST RESULT: **FALSIFIED** — admin fee LP minting << donation cost
  - Donation triggers admin fee LP minting via xcp_profit increase
  - But minted LP value is far less than donation cost
  - Evidence: CurveTricrypto.t.sol::test_H8_XcpProfitManipulation

## H9: Newton's Method Convergence Failure (DoS)
BROKEN ASSUMPTION: A4 (Newton always converges)
FEASIBILITY: LOW — safety bounds at lines 111-114 of crypto_math.vy are tight
  - x[0] must be in [10^9, 10^15 * 10^18]
  - Ratio check: frac = x[i] * 10^18 / x[0] > 10^11
  - NOT TESTED — DoS is not value extraction

## H10: Price Scale Manipulation via Repeated Trades
BROKEN ASSUMPTION: A9 (price_scale adjusts correctly)
FORK TEST RESULT: **FALSIFIED** by H15/Deep2 analysis
  - Price scale adjustment requires norm > adjustment_step^2 (4.9e14)
  - Multi-block arb correction defeats sustained manipulation
  - Evidence: CurveTricryptoDeep.t.sol::test_Deep5

## H11: claim_admin_fees Gulp + Imbalanced Exchange
BROKEN ASSUMPTION: A2 + A11
FORK TEST RESULT: **FALSIFIED** — refined H1
  - Donation is irrecoverable without LP tokens
  - Attacker gets no LP tokens for donated portion
  - Donated tokens increase value for ALL existing LP holders
  - Evidence: CurveTricryptoFinal.t.sol::test_Final1 — NET LOSS $914,822

## H12: Precision Loss in Swap Fee Application
BROKEN ASSUMPTION: A10 (rounding favors pool)
FORK TEST RESULT: **FALSIFIED** — zero extractable value
  - Small swap rounding gives 0 to attacker
  - Gas cost per swap >> rounding profit (~0.001 USDT)
  - Evidence: CurveTricrypto.t.sol::test_H12_SmallSwapFeeRounding

## H13: Admin Fee Receiver as Value Extraction
BROKEN ASSUMPTION: A6 (admin fee extraction correct)
FEASIBILITY: N/A — requires admin compromise (owner-only)
  - Owner is contract (code size 5282, likely DAO/multisig)
  - Evidence: CurveTricryptoDeep.t.sol::test_Deep7

## H14: Stale D After Proportional remove_liquidity
BROKEN ASSUMPTION: D remains consistent after operations
FORK TEST RESULT: **FALSIFIED** — deviation is negligible
  - D linear update vs newton_D recompute: deviation only 1627 wei
  - Not exploitable at any scale
  - Evidence: CurveTricrypto.t.sol::test_H14_DConsistencyAfterRemoval

## H15: Donation + Gulp -> Price Oracle Drift
BROKEN ASSUMPTION: A2 + A5 + A11
FORK TEST RESULT: **PARTIALLY CONFIRMED as cross-protocol risk only**
  - Donation causes last_prices jump: 1943->2491 ETH (28% spike)
  - But price_oracle EMA dampens: only 0.001% single-block movement
  - Multi-block (10 blocks): 700 bps drift with 2M USDT donation
  - Cost: 2M USDT irrecoverable -> need >$28.6M external exposure
  - Evidence: CurveTricrypto.t.sol::test_H15, CurveTricryptoDeep.t.sol::test_Deep1, test_Deep2

## Backlog (NOT TESTED — low feasibility or not relevant)
- B1: Cross-pool arbitrage (not a vulnerability, normal arb)
- B2: LP token as collateral attack (external protocol risk, not Tricrypto2)
- B3: Gas griefing via newton_D (DoS, not value extraction)
- B4: Governance attack on owner (requires admin compromise)
