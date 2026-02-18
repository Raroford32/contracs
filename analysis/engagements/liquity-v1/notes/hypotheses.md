# Hypotheses — Liquity V1 (10-20 Multi-Step Cross-Contract Sequences)

## Active Hypotheses

### H1: StabilityPool Scale Boundary ETH Gain Theft
**Broken assumption**: ETH gain tracking is perfectly precise across P scale changes
**Reasoning chain**:
1. P tracks deposit depletion as a running product that decreases toward 0
2. When P * newProductFactor / 1e18 < 1e9, P gets multiplied by 1e9 (scale increment)
3. ETH gains across scale boundary use: `firstPortion + secondPortion/SCALE_FACTOR`
4. If attacker can engineer a liquidation that pushes P exactly to the scale boundary...
5. ...the secondPortion calculation `epochToScaleToSum[epoch][scale+1] / 1e9` loses precision
6. Deposit at scale N, trigger large liquidation → scale change → claim ETH with rounding in attacker's favor
**Sequence** (12 steps):
1. Flash loan large ETH
2. Open trove with maximum leverage (110% ICR)
3. Borrow max LUSD
4. Deposit all LUSD into StabilityPool (becoming major depositor)
5. Create a sacrificial trove with precise debt amount
6. Manipulate ETH price via oracle stale window (if possible) OR wait for natural price drop
7. Trigger liquidation of sacrificial trove → SP offset → P decreases
8. Engineer the liquidation amount to push P exactly across scale boundary
9. Claim ETH gain from SP → disproportionate ETH due to rounding
10. Withdraw remaining LUSD from SP
11. Close trove, repay flash loan
12. Profit = excess ETH from rounding
**Feasibility**: LOW - error correction mechanisms (lastETHError_Offset, lastLUSDLossError_Offset) designed to prevent this; P rounding "favors the pool"

### H2: Redemption Fee Arbitrage via BaseRate Decay Timing
**Broken assumption**: baseRate accurately reflects current demand; time decay is continuous
**Reasoning chain**:
1. baseRate decays with MINUTE_DECAY_FACTOR^(minutes elapsed) (half-life 12h)
2. After long idle period, baseRate → ~0, so redemption fee → floor (0.5%)
3. Attacker flash loans massive LUSD → redeems for ETH at 0.5% fee
4. BUT: `_updateBaseRateFromRedemption` is called AFTER the redemption loop
5. The fee is calculated on `_getRedemptionFee(totalETHDrawn)` using the ALREADY UPDATED baseRate
6. Wait — re-read: baseRate is updated BEFORE fee calculation at line 997-1000
7. So large redemption → high baseRate → high fee on SAME redemption. Self-limiting.
**Sequence** (8 steps):
1. Wait for baseRate to decay to near-zero (long idle period)
2. Flash loan large amount of LUSD from Curve/Uniswap
3. Call redeemCollateral with large LUSD amount
4. baseRate updates BEFORE fee calc → fee includes size of this redemption
5. Receive ETH minus fee
6. Sell ETH for LUSD to repay flash loan
7. Net = ETH received minus (LUSD cost + fee + slippage)
8. Compare with direct ETH market purchase
**Feasibility**: VERY LOW - self-limiting design; large redemptions increase their own fee. Also, _maxFeePercentage provides protection.

### H3: Recovery Mode Boundary Manipulation → Liquidate Healthy Troves
**Broken assumption**: System cannot be pushed into Recovery Mode by attacker
**Reasoning chain**:
1. Recovery Mode triggers when TCR < 150% (CCR)
2. In Recovery Mode, troves with ICR < TCR can be liquidated (even if ICR > 110%)
3. Currently TCR ~483% — extremely far from 150%
4. To push TCR below 150%: need to reduce collateral value OR increase debt
5. Collateral reduction: ETH price crash (external); not attacker-controlled
6. Debt increase: open many max-leverage troves? Each must have ICR ≥ 110%
7. Even maximizing: newTCR check prevents opening trove that would push TCR below 150%
8. BorrowerOperations._requireNewTCRisAboveCCR(newTCR) enforces this in Normal Mode
**Sequence** (15 steps):
1. Flash loan massive ETH
2. Open trove at exactly 150% ICR
3. Check: _requireNewTCRisAboveCCR prevents TCR dropping below 150%
4. BLOCKED at step 3 — cannot push system into Recovery Mode via borrowing
5. Alternative: wait for natural ETH price decline to near Recovery Mode boundary
6. When TCR is near 150%, flash loan ETH → open trove at 150.01% → push TCR just below 150%
7. Now in Recovery Mode: target troves with 110% < ICR < TCR
8. Call batchLiquidateTroves([target_troves])
9. Liquidator receives gas compensation (200 LUSD + 0.5% of coll per trove)
10. Troves with MCR ≤ ICR < TCR: capped liquidation at 110% MCR, surplus to CollSurplusPool
11. Attacker gets gas comp; victims lose position at capped 110% rate
12. Close attacker's trove
13. Repay flash loan
14. Profit = sum of gas compensation - flash loan cost
15. Issue: need TCR naturally near boundary; gas comp is only 0.5% + 200 LUSD
**Feasibility**: LOW - requires natural TCR near 150%, gas compensation is small

### H4: StabilityPool Epoch Reset + First Depositor Front-Running
**Broken assumption**: Empty pool state after epoch increment is safe
**Reasoning chain**:
1. When SP is fully emptied by liquidation, epoch increments, P resets to 1e18, scale resets to 0
2. After epoch reset, new depositor gets fresh snapshots (P=1e18, S=0)
3. If attacker front-runs the next liquidation after epoch reset...
4. Deposit 1 wei LUSD → become sole depositor → next liquidation ETH goes to attacker
5. BUT: TroveManager checks `totalLUSD == 0 || _debtToOffset == 0` in SP.offset()
6. If totalLUSD is 0, offset returns immediately → redistribution instead of SP offset
7. 1 wei deposit: totalLUSD = 1 → offset proceeds → 1 wei absorbs debt, attacker gets all ETH
8. BUT: `_debtToOffset <= totalLUSD` assertion → debt > 1 wei → would violate assertion
9. Wait: `debtToOffset = _min(_debt, _LUSDInStabPool)` → debtToOffset = 1 (min of debt and 1)
10. collToSendToSP = coll * 1 / debt ≈ 0 (rounds to 0 for any reasonable debt)
11. So attacker gets ~0 ETH. Not viable.
**Sequence** (10 steps):
1. Monitor for SP emptying event (epoch increment)
2. Deposit small LUSD into empty SP
3. Wait for next liquidation
4. SP.offset called with small totalLUSD → barely any ETH transferred
5. Most gets redistributed to active troves
**Feasibility**: NONE - the math correctly handles small deposits

### H5: Redistribution Reward Rounding Accumulation → Steal from Small Troves
**Broken assumption**: Redistribution rewards are precisely tracked via L_ETH/L_LUSDDebt
**Reasoning chain**:
1. When troves are liquidated and SP has no LUSD, debt+coll are redistributed
2. `L_ETH += (coll * 1e18 + lastETHError) / totalStakes` — per-unit-staked
3. Pending reward: `stake * (L_ETH - snapshot_L_ETH) / 1e18`
4. For very small troves (tiny stake), this division can round to 0
5. Repeatedly opening+closing small troves → each time earning 0 pending reward
6. The "lost" fractions accumulate in the error tracker
7. Eventually error tracker grows large enough to shift L_ETH by an extra unit
8. A large trove then claims that extra unit disproportionately
9. BUT: error correction is designed to prevent systematic bias
10. Error is bounded: `lastETHError = numerator - quotient * totalStakes` < totalStakes
**Sequence** (20 steps):
1-4. Open 4 tiny troves at minimum debt (2000 LUSD + 200 gas comp)
5. Open 1 large trove as attacker
6-9. Create 4 sacrificial troves with ICR just below 110% (in Normal Mode)
10-13. Liquidate all 4 sacrificial troves → redistributed to remaining troves
14. Each tiny trove gets floor(tiny_stake * L_ETH_delta / 1e18) = possibly 0
15. Attacker's large trove gets floor(large_stake * L_ETH_delta / 1e18) = nearly all
16-19. Close all 4 tiny troves (their pending rewards round to 0)
20. Attacker claims pending rewards → gets slightly more than proportional share
**Feasibility**: VERY LOW - rounding errors are on the order of wei; not economically significant even at scale

### H6: LUSD Permit (EIP-2612) Replay Across Chain Forks
**Broken assumption**: Domain separator invalidation is sufficient across chain forks
**Reasoning chain**:
1. LUSDToken implements EIP-2612 permit with cached domain separator
2. `domainSeparator()` checks `_chainID() == _CACHED_CHAIN_ID`
3. If chain ID changes (hard fork), recomputes domain separator
4. BUT: on a chain fork where chain ID doesn't change (or is set identically)
5. A permit signed on chain A could be replayed on chain B
6. Attack: sign permit on mainnet → replay on fork chain with same chainId
7. This requires an actual chain fork event, not just an Ethereum fork
**Sequence** (6 steps):
1. On mainnet: user signs permit(spender=attacker, amount=maxUint256)
2. Chain forks with same chainId
3. On fork chain: attacker submits permit tx → gets approval
4. attacker.transferFrom(user, attacker, user_balance) on fork
5. Attacker drains user's LUSD on fork chain
6. On mainnet: original permit is already consumed (nonce incremented)
**Feasibility**: EXTREMELY LOW - requires actual chain fork; domain separator handles it; practical exploitation near-zero on mainnet

### H7: Price Feed Manipulation via Chainlink Stale Window + Flash Liquidation
**Broken assumption**: PriceFeed always returns a current, accurate price
**Reasoning chain**:
1. PriceFeed uses Chainlink with Tellor as fallback
2. Chainlink has deviation threshold + heartbeat (typically 1% / 1 hour for ETH/USD)
3. Between heartbeats, price can deviate up to threshold without update
4. If ETH price drops 0.99% (below Chainlink update threshold), PriceFeed still returns old price
5. At old (higher) price, some troves appear healthy but are actually undercollateralized
6. Attacker cannot liquidate them because PriceFeed returns too-high price
7. Alternatively: if price spikes 0.99%, PriceFeed returns stale low price
8. Troves opened at "stale low" price get favorable ICR when real price is higher
9. But Liquity calls `priceFeed.fetchPrice()` which triggers Chainlink latestRoundData()
10. This always returns the latest on-chain oracle price, not a cached value
**Sequence** (10 steps):
1. Monitor Chainlink ETH/USD for approaching heartbeat window
2. Observe real ETH price has moved but Chainlink hasn't updated yet
3. Call fetchPrice() → gets stale Chainlink price
4. If stale price > real: troves appear healthier than they are → no extra liquidations possible
5. If stale price < real: troves appear less healthy → potential liquidations at stale price
6. Liquidate troves that are healthy at real price but appear unhealthy at stale price
7. Receive gas compensation + ETH from liquidation
8. In reality: trove was actually healthy, so attacker forced unfair liquidation
9. BUT: Chainlink deviation is tiny (1%) and heartbeat is 1 hour
10. At $1,939 ETH, 1% = $19.39 → not enough to flip ICR for well-collateralized troves
**Feasibility**: VERY LOW - Chainlink price accuracy is very tight; MCR is 110% leaving 10% buffer

### H8: Cross-Protocol: Flash Loan SP Deposit → Trigger Liquidation → Claim ETH Gain → Withdraw
**Broken assumption**: SP depositors can't atomically deposit, earn, and withdraw in one tx
**Reasoning chain**:
1. Flash loan LUSD → deposit into SP → trigger liquidation → claim ETH → withdraw → repay
2. BUT: `withdrawFromSP` has: `if (_amount !=0) {_requireNoUnderCollateralizedTroves();}`
3. This prevents non-zero withdrawal if there are liquidatable troves
4. Attack: deposit LUSD → liquidate troves → then withdraw
5. After liquidation, no more undercollateralized troves exist
6. So withdrawal check passes → can withdraw
7. But wait: the deposit was just made in the same tx
8. getCompoundedLUSDDeposit uses P/P_snapshot → if P changed due to liquidation in same tx
9. Depositor snapshot P_t was set at deposit time, before liquidation
10. After liquidation P drops → compoundedDeposit = initialDeposit * P / P_t < initialDeposit
11. ETH gain = initialDeposit * (S - S_t) / P_t / 1e18 > 0
12. So attacker loses some LUSD but gains ETH — net depends on liquidation ICR
**Sequence** (14 steps):
1. Flash loan X LUSD from Curve/Uniswap
2. Flash loan Y ETH from Aave
3. Create sacrificial trove with Y ETH, borrow minimal LUSD at ~109% ICR
4. Deposit X LUSD into StabilityPool via provideToSP(X, address(0))
5. ETH price is at $1,939; sacrificial trove is just below 110% MCR
6. Call liquidateTroves(1) to liquidate sacrificial trove
7. SP.offset() is called → burns LUSD from SP, sends ETH to SP
8. P drops, S increases → attacker now has ETH gain in SP
9. Call withdrawFromSP(compoundedDeposit) → get remaining LUSD + ETH gain
10. ETH gain from SP = sacrificial trove's ETH * (X/(X + other_SP_deposits))
11. LUSD loss from SP = sacrificial trove's debt * (X/(X + other_SP_deposits))
12. Net: (ETH_gain * price - LUSD_loss) depends on liquidation being profitable
13. Close sacrificial trove (already closed by liquidation)
14. Repay flash loans
**Key insight**: For liquidation at 109% ICR, SP depositors receive 109% worth of ETH for 100% worth of LUSD → 9% profit. Shared proportionally with other SP depositors.
**Feasibility**: MEDIUM-LOW — this is standard liquidation profit, not an exploit. SP depositors are *supposed* to profit from absorbing undercollateralized debt. The profit is proportional to attacker's share of SP. With $13M already in SP, a flash deposit of $100M LUSD would capture 100/113 ≈ 88% of the profit. BUT: need a liquidatable trove to exist.

### H9: Self-Liquidation for Gas Compensation Extraction
**Broken assumption**: Gas compensation is small relative to minimum debt
**Reasoning chain**:
1. Gas comp = 200 LUSD (from GasPool) + 0.5% of trove's ETH collateral
2. Open trove at exactly MCR (110%): 2200 LUSD debt (2000 min net + 200 gas comp)
3. Collateral = 2200/price * 1.1 = 2420/1939 ≈ 1.248 ETH
4. Gas comp ETH = 0.005 * 1.248 = 0.00624 ETH (~$12.10)
5. Gas comp LUSD = 200 LUSD
6. To trigger liquidation: need ICR < 110%. Price must drop slightly.
7. Liquidator gets: 200 LUSD + 0.00624 ETH
8. Borrower loses: trove position (net negative — they deposited 1.248 ETH and borrowed 2000 LUSD)
9. If attacker opens trove AND is the liquidator: net = gas comp - borrowing fee - gas costs
10. Borrowing fee in Recovery Mode = 0; in Normal Mode = based on baseRate
**Sequence** (8 steps):
1. Open trove at exactly 110% ICR
2. Wait for tiny ETH price drop (natural volatility)
3. Self-liquidate via liquidate(self)
4. Receive: 200 LUSD + 0.5% of coll as gas comp
5. Lost: initial ETH collateral minus what was borrowed
6. Net: NEGATIVE for self-liquidation (lost collateral > gas comp)
**Feasibility**: NONE - liquidation always costs the borrower more than the gas comp

### H10: Redemption Ordering Manipulation → Force Partial Redemption on Target
**Broken assumption**: Redemption traverses sorted list fairly from lowest ICR upward
**Reasoning chain**:
1. Redemption starts from lowest-ICR trove (or _firstRedemptionHint if valid)
2. Only redeems from troves with ICR ≥ MCR (110%)
3. First redemption hint must be valid: ICR ≥ MCR and next trove has ICR < MCR
4. Attacker can provide _firstRedemptionHint pointing to a specific trove
5. BUT: _isValidFirstRedemptionHint checks that the next trove has ICR < MCR
6. So the hint must be the lowest trove with ICR ≥ MCR → can't skip troves
7. Partial redemption leaves remainder at higher ICR → reinsertion in sorted list
8. If hint is stale (another tx changes list), partial redemption cancels
**Sequence** (10 steps):
1. Observe target trove at position X in sorted list
2. Open troves below target with ICR just above 110% to "buffer"
3. Redeem LUSD → walks through attacker's buffer troves first
4. Attacker's troves get closed by redemption → attacker gets surplus from CollSurplusPool
5. When redemption reaches target trove → partial or full redemption
6. Target trove owner loses ETH proportional to LUSD redeemed
7. BUT: attacker's buffer troves are also redeemed at 1:1 LUSD:ETH ratio
8. Attacker loses ETH from buffer troves, gains from redemption... no net gain
**Feasibility**: NONE - attacker loses as much from their own troves as target loses

### H11: Cross-Contract Reentrancy via ETH Transfers
**Broken assumption**: No reentrancy possible despite ETH sends
**Reasoning chain**:
1. StabilityPool._sendETHGainToDepositor: `msg.sender.call{value: _amount}("")`
2. ActivePool.sendETH: `(bool success, ) = _account.call{ value: _amount }("")`
3. LQTYStaking._sendETHGainToUser: `(bool success, ) = msg.sender.call{ value: _amount }("")`
4. All use low-level call → triggers fallback function of receiving contract
5. Can attacker reenter during ETH transfer?
6. In StabilityPool.withdrawFromSP: ETH sent AFTER state updates (deposit updated, snapshots taken)
7. CEI pattern: checks → updates deposits/snapshots → transfers LUSD → transfers ETH (last)
8. In liquidateTroves: gas compensation ETH sent at the very end
9. In redeemCollateral: ETH sent at line 1016, after all state updates
**Sequence** (12 steps):
1. Deploy malicious contract with receive() that calls back into StabilityPool
2. Deposit LUSD via malicious contract → contract becomes SP depositor
3. Trigger liquidation → offset → contract earns ETH gain
4. Call withdrawFromSP → state updates → ETH transfer → receive() callback
5. In callback: try to withdrawFromSP again
6. BUT: deposit has already been updated to new compounded value
7. Second withdrawal: compoundedDeposit recalculated with ALREADY UPDATED snapshots
8. No double-counting possible because snapshots were updated before ETH send
9. Try callback into provideToSP: would take new snapshot, cannot steal
10. Try callback into withdrawETHGainToTrove: ETH already subtracted from SP
11. Even if reentrant, state is consistent after the update
12. CONCLUSION: CEI pattern holds; reentrancy does not yield extra funds
**Feasibility**: NONE - Liquity follows CEI pattern consistently

### H12: Sandwich Attack on SP Depositor's withdrawETHGainToTrove
**Broken assumption**: withdrawETHGainToTrove cannot be sandwiched for profit
**Reasoning chain**:
1. Victim calls withdrawETHGainToTrove → moves ETH gain from SP to their trove
2. This calls borrowerOperations.moveETHGainToTrove{value: ETHGain}(msg.sender, hints)
3. This increases victim's trove collateral → changes their ICR and position in sorted list
4. Attacker front-runs: deposits large LUSD into SP → dilutes victim's pending ETH gain
5. BUT: victim's ETH gain was already computed at the start of the function
6. `depositorETHGain = getDepositorETHGain(msg.sender)` → reads from snapshots, not affected by concurrent deposits
7. The ETH gain was "locked in" when the liquidation happened, based on old snapshots
**Feasibility**: NONE - ETH gain is based on historical snapshots, not current share

### H13: Donation Attack on ActivePool → Inflate Collateral → Undermine Solvency Checks
**Broken assumption**: ActivePool ETH balance accurately represents protocol collateral
**Reasoning chain**:
1. ActivePool tracks internal `ETH` variable, incremented by receive() from BorrowerOps
2. But anyone can send ETH directly to ActivePool contract via selfdestruct
3. ActivePool.getETH() returns the internal tracker, NOT address(this).balance
4. Wait: let me check... ActivePool has `uint256 internal ETH` and `receive() external payable { ... }`
5. The receive() function only accepts ETH from authorized senders (BorrowerOps, TroveManager, DefaultPool)
6. Direct ETH send via selfdestruct increases balance but NOT the `ETH` tracker
7. Solvency calculations use getETH() which reads the tracker → unaffected
8. BUT: CollSurplusPool.claimColl sends ETH → might it differ?
**Sequence** (8 steps):
1. Send ETH to ActivePool via selfdestruct of sacrificial contract
2. ActivePool.balance > ActivePool.ETH (internal tracker)
3. No protocol function reads address(this).balance — all read the tracker
4. No impact on any solvency calculation
5. ETH just sits as "dust" in the contract forever
6. ALTERNATIVELY: can we drain this dust? No — no function sends address.balance
**Feasibility**: NONE - internal tracking variable is isolated from actual balance

### H14: Flash Loan LUSD → Massive SP Deposit → Trigger All Liquidations → Withdraw → Profit
**Broken assumption**: Flash depositing to capture liquidation value is not profitable at scale
**Reasoning chain**:
1. Flash loan 100M LUSD (if available on Curve pools)
2. Deposit 100M into SP (current SP has 13M → attacker gets 100/113 = 88.5% of all liquidation value)
3. Trigger batch liquidation of all liquidatable troves
4. Receive 88.5% of ETH from liquidated troves
5. Withdraw 88.5% of remaining LUSD + all ETH gain
6. Net: ETH_gain * price - LUSD_loss should be positive when ICR < 110%
7. For trove at 109% ICR: depositors get 109 ETH-value for absorbing 100 LUSD-debt → 9% gain
8. Attacker captures 88.5% of this 9% gain
9. At $1,939 ETH: need liquidatable troves to exist
10. Currently no troves near liquidation (TCR ~483%)
**Sequence** (10 steps):
1. Flash loan 100M LUSD from Curve
2. provideToSP(100M, address(0))
3. batchLiquidateTroves([all_liquidatable_troves])
4. For each liquidated trove: SP absorbs debt, receives ETH
5. withdrawFromSP(compoundedDeposit)
6. ETH gain = proportional to deposit share
7. Repay flash loan with LUSD
8. Sell excess ETH for profit
9. Profit margin = (weighted avg ICR of liquidated troves - 100%) * attacker share * total debt
10. Gas costs: batch liquidation is expensive; need enough troves to be profitable
**Feasibility**: MEDIUM — mathematically sound if liquidatable troves exist. This is the "intended" SP profit mechanism. But it requires troves to be undercollateralized. Currently there are no such troves. This is NOT a vulnerability — it's the intended economic design.

### H15: SortedTroves Manipulation via Hint Gaming → Block Legitimate Operations
**Broken assumption**: Hint system cannot be gamed to DoS other users
**Reasoning chain**:
1. SortedTroves is a doubly linked list sorted by nominal ICR (NICR)
2. Operations require hints (upper, lower) for insertion position
3. If hints are stale (list changed), insertion still works but costs more gas
4. Attacker cannot prevent insertion — just make it more expensive
5. Partial redemption: if hint is wrong, `cancelledPartial = true` → redemption stops
6. This means: attacker can front-run a redemption with a trove operation to invalidate the hint
7. The redeemer fails to redeem the last (partial) trove → loses some redemption capacity
8. BUT: redeemer just doesn't get the partial — they still redeem from the full troves
**Feasibility**: LOW - no actual value extraction, just minor griefing

### H16: LQTYStaking F_ETH/F_LUSD Division by Zero When totalLQTYStaked = 0
**Broken assumption**: Fees are never lost when no LQTY is staked
**Reasoning chain**:
1. increaseF_ETH: `if (totalLQTYStaked > 0) { ETHFeePerLQTYStaked = _ETHFee * 1e18 / totalLQTYStaked; }`
2. If totalLQTYStaked == 0: ETHFeePerLQTYStaked remains 0, fee is NOT added to F_ETH
3. The ETH fee is ALREADY SENT to the LQTYStaking contract at this point
4. ETH sits in LQTYStaking contract but F_ETH doesn't increase
5. This ETH is permanently stuck — no function to recover it
6. Similarly for LUSD fees when no LQTY staked
7. This is by design (documented behavior) but represents permanent value loss
8. NOT exploitable — attacker can't extract the stuck fees
**Sequence**: Monitor for totalLQTYStaked == 0, trigger redemption → fee goes to LQTYStaking → lost
**Feasibility**: NONE for exploitation (it's a known design choice, not a vulnerability)

### H17: Cross-Protocol Flash Loan + Liquidation Cascade Amplification
**Broken assumption**: Protocol is isolated from cross-protocol liquidation cascades
**Reasoning chain**:
1. Massive ETH price drop → Aave/Compound/Maker liquidations → ETH selling pressure → further price drop
2. If Chainlink price feed reflects this cascade quickly enough
3. Liquity troves become undercollateralized as price drops below their ICR thresholds
4. Attacker: flash loan ETH → sell on Uniswap → push price down → trigger Liquity liquidations → buy ETH back cheap
5. BUT: flash loan must be repaid in same tx → can't cause persistent price change
6. Oracle manipulation via spot price: Liquity uses Chainlink, NOT Uniswap TWAP
7. Cannot manipulate Chainlink price via flash loan
8. Would need actual market selling pressure (not flash-loan based)
**Feasibility**: NONE via flash loans — Chainlink oracle is resistant to flash loan manipulation

### H18: Trove Dust Attack → Create Minimum Troves → DoS Liquidation Gas
**Broken assumption**: liquidateTroves gas cost scales linearly
**Reasoning chain**:
1. Open thousands of minimum-size troves (2000 LUSD min net debt + 200 gas comp = 2200 total)
2. Each trove at exactly 110% ICR
3. When price drops: liquidateTroves(N) must iterate through all
4. Gas cost per liquidation is high (state updates, pool transfers)
5. If N is very large, batch liquidation runs out of gas
6. BUT: liquidateTroves takes _n parameter → can liquidate in batches
7. Also: batchLiquidateTroves takes explicit list → can target specific troves
8. Gas DoS doesn't prevent liquidation, just requires multiple txs
**Feasibility**: NONE — no profit extraction, just minor operational friction

### H19: Recovery Mode + Liquidation Gas Comp Farming
**Broken assumption**: Gas compensation in Recovery Mode is bounded
**Reasoning chain**:
1. In Recovery Mode, troves with MCR ≤ ICR < TCR can be liquidated
2. But only if SP has enough LUSD AND entire debt ≤ SP LUSD
3. Gas comp: 200 LUSD + 0.5% of the capped collateral (at 110% rate, not full coll)
4. For large troves: 0.5% of large collateral = significant gas comp
5. If a whale trove has 1000 ETH coll → gas comp = 5 ETH (~$9,700)
6. But attacker needs Recovery Mode (TCR < 150%) to liquidate troves with ICR > 110%
7. Currently TCR ~483% → cannot reach Recovery Mode
8. Even if TCR drops to 150%: attacker cannot push it below via borrowing (check enforced)
**Feasibility**: LOW — requires natural extreme market conditions

### H20: StabilityPool ETH/LUSD Accounting Divergence After Many Small Liquidations
**Broken assumption**: Error correction terms remain bounded over thousands of operations
**Reasoning chain**:
1. lastETHError_Offset, lastLUSDLossError_Offset track rounding errors
2. These are bounded by totalLUSDDeposits (denominator of division)
3. Over thousands of liquidations, cumulative rounding error grows
4. BUT: error correction is reapplied each time → error doesn't grow, it oscillates
5. The error term in each iteration compensates for the previous iteration's error
6. Mathematical proof: cumulative error is bounded by O(1) units, not O(n)
7. Even after millions of liquidations, accounting should be precise to within 1 wei per depositor
**Feasibility**: NONE — error correction is mathematically sound

## Backlog (Lower Priority)
- H21: LUSD permit front-running (EIP-2612 race condition)
- H22: SortedTroves linked list corruption via simultaneous operations
- H23: DefaultPool ETH stuck if sendETHToActivePool fails
- H24: GasPool LUSD balance exhaustion blocking liquidations
