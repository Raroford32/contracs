# Assumptions — Curve Tricrypto2

## A1: Token transfers move exact amounts
ASSUMPTION: ERC20 transferFrom/transfer moves exactly the specified amount
EVIDENCE IN CODE: exchange() line 613-618 updates self.balances[i] = x0 + dx without checking actual received
VIOLATION CONDITION: Fee-on-transfer token (USDT has fee mechanism, currently 0)
CONSEQUENCE: Balance inflation → pool credits more than received → attacker can withdraw excess
VIOLATION FEASIBILITY: CURRENTLY LOW — USDT fee is 0, WBTC/WETH standard. But USDT CAN enable fees.

## A2: balances[] reflects true token holdings
ASSUMPTION: self.balances[i] == ERC20(coins[i]).balanceOf(self) at all times
EVIDENCE IN CODE: exchange/add_liquidity update balances optimistically; only claim_admin_fees gulps
VIOLATION CONDITION: Direct token transfer (donation) without going through pool functions
CONSEQUENCE: balances[] diverges from reality; claim_admin_fees() syncs and changes D/virtual_price
VIOLATION FEASIBILITY: HIGH — anyone can send tokens to the pool address

## A3: Virtual price is monotonically increasing
ASSUMPTION: virtual_price should only increase over time (from fee accumulation)
EVIDENCE IN CODE: tweak_price line 519 checks `virtual_price < old_virtual_price and t == 0: raise "Loss"`
VIOLATION CONDITION: During A/gamma ramp (t != 0), virtual_price CAN decrease without reverting
CONSEQUENCE: LP holders lose value; virtual_price-based oracles give wrong readings
VIOLATION FEASIBILITY: MEDIUM — requires active A/gamma ramp (admin action)

## A4: Newton's method converges for all valid inputs
ASSUMPTION: newton_D and newton_y always converge within 255 iterations
EVIDENCE IN CODE: Both loop 255 times and raise "Did not converge" on failure
VIOLATION CONDITION: Extreme balance ratios or parameter combinations
CONSEQUENCE: All pool operations revert → DoS
VIOLATION FEASIBILITY: LOW — safety checks at lines 111-114 and 181-184 bound inputs

## A5: Price oracle cannot be manipulated in a single block
ASSUMPTION: EMA price oracle resists single-block manipulation
EVIDENCE IN CODE: tweak_price uses halfpow EMA decay with ma_half_time=600s
VIOLATION CONDITION: Large trade moves last_prices; but EMA only partially updates
CONSEQUENCE: Small oracle movement per block, but repeated blocks compound
VIOLATION FEASIBILITY: MEDIUM — single-block manipulation is small, but multi-block possible

## A6: Admin fee extraction is correct
ASSUMPTION: claim_admin_fees mints the correct amount of LP tokens for admin fees
EVIDENCE IN CODE: line 410: fees = (xcp_profit - xcp_profit_a) * admin_fee / (2 * 10**10)
VIOLATION CONDITION: xcp_profit manipulation (donation → gulp → profit increase)
CONSEQUENCE: Admin fee minting could be inflated or suppressed
VIOLATION FEASIBILITY: LOW-MEDIUM — needs investigation of xcp_profit after donation

## A7: Pool is safe from reentrancy
ASSUMPTION: nonreentrant lock prevents all reentrancy attacks
EVIDENCE IN CODE: exchange, add_liquidity, remove_liquidity*, apply_new_parameters use @nonreentrant('lock')
VIOLATION CONDITION: Cross-function reentrancy or callback during ETH transfer
CONSEQUENCE: State manipulation mid-execution
VIOLATION FEASIBILITY: VERY LOW — nonreentrant covers all state-changing functions

## A8: Kill deadline has passed
ASSUMPTION: kill_me() can no longer be called (kill_deadline in 2021)
EVIDENCE IN CODE: line 1155: assert self.kill_deadline > block.timestamp
VIOLATION CONDITION: kill_deadline > current block.timestamp
CONSEQUENCE: If passed, kill_me is permanently disabled → pool can never be killed
VIOLATION FEASIBILITY: CONFIRMED — kill_deadline=1631395083 (Sep 2021), long past

## A9: Price scale adjusts correctly toward oracle
ASSUMPTION: price_scale moves toward price_oracle at rate bounded by adjustment_step
EVIDENCE IN CODE: tweak_price lines 533-577 compute adjustment
VIOLATION CONDITION: oracle manipulation → price_scale adjusts to wrong price
CONSEQUENCE: Pool internal prices diverge from reality → unfavorable swaps
VIOLATION FEASIBILITY: MEDIUM — depends on oracle manipulation feasibility (A5)

## A10: Rounding favors the pool
ASSUMPTION: All rounding errors favor the pool (not the user)
EVIDENCE IN CODE: exchange line 652: dy -= 1 (reduces output by 1 wei)
VIOLATION CONDITION: Rounding in fee calculation, D computation, or price scaling that favors user
CONSEQUENCE: Drainable via repeated round-trip swaps
VIOLATION FEASIBILITY: LOW — need to check all rounding directions

## A11: claim_admin_fees gulp is safe
ASSUMPTION: Syncing balances to actual balanceOf() is harmless
EVIDENCE IN CODE: _claim_admin_fees lines 404-405 sets self.balances = balanceOf
VIOLATION CONDITION: Someone donates large amount → gulp changes D dramatically
CONSEQUENCE: D changes → virtual_price changes → price oracle affected → admin fees affected
VIOLATION FEASIBILITY: HIGH — donation is permissionless, gulp is permissionless

## A12: Decimal precision handling is correct
ASSUMPTION: PRECISIONS multipliers correctly normalize all tokens to 18 decimals
EVIDENCE IN CODE: PRECISIONS = [1e12, 1e10, 1] for USDT(6)/WBTC(8)/WETH(18)
VIOLATION CONDITION: Precision loss in multiplication/division ordering
CONSEQUENCE: Systematic over/under-estimation of token values
VIOLATION FEASIBILITY: LOW — standard pattern, but worth testing at boundaries
