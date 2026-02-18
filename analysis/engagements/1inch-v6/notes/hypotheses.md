# Hypotheses — 1inch V6 AggregationRouter

## Confirmed (fork-grounded evidence)

### H1: curveSwapCallback Drain (CONFIRMED — limited impact)
- **Broken assumption**: curveSwapCallback is only called by legitimate Curve pools during swaps
- **Reality**: callable by anyone, no access control (line 5601-5609)
- **Sequence**: attacker calls `curveSwapCallback(_, _, token, routerBalance, _)` → router transfers tokens
- **Impact**: Can drain any token balance the router holds
- **Current magnitude**: 0 for WETH/USDC at block 21880000 (confirmed by fork test)
- **Escalation potential**: increases if tokens accumulate (accidents, rebasing, airdrops)
- **Fork test**: `exploit_test/test/OneInchV6CallbackDrain.t.sol::test_curveSwapCallback_drain` — PASS
- **E3 status**: NOT E3 — net profit < $0.01 under normal conditions

### H2: uniswapV3SwapCallback Unvalidated Path (CONFIRMED — limited impact)
- **Broken assumption**: uniswapV3SwapCallback validates pool identity for all transfers
- **Reality**: When payer==address(this), no CREATE2 validation occurs (line 5674)
- **Sequence**: deploy FakeV3Pool(token0=WETH) → call drainViaCallback(amount) → callback transfers from router
- **Impact**: Same as H1 — can drain router's own token balances
- **Fork test**: `exploit_test/test/OneInchV6CallbackDrain.t.sol::test_uniswapV3SwapCallback_drain_via_fake_pool` — PASS
- **E3 status**: NOT E3 — same limitation as H1

## Analyzed and Not Exploitable

### H4: Taker Interaction Reentrancy in fillOrder — NOT EXPLOITABLE
- **Broken assumption tested**: taker interaction cannot reenter router to double-fill
- **Analysis result**:
  - No global `nonReentrant` guard exists
  - BUT: per-order invalidator is updated at lines 3978-3982 BEFORE any external call
  - Bit invalidator: reentrant fill of same order reverts with `BitInvalidatedOrder()`
  - Remaining invalidator: reentrant fill sees already-reduced remaining, can only fill actual remainder
  - Cross-order reentrancy is by design (independent order state)
  - Flash-loan window (lines 4018-4023) is intentional taker interaction facility
- **Narrow reentrancy check**: exists at line 3820-3823 for permit-path only
- **Status**: FALSIFIED — CEI per-order prevents double-fill

### H5: Assembly Calldata Parsing Overflow — NOT EXPLOITABLE
- **Analysis result**:
  - Address extraction: `and(dex, _ADDRESS_MASK)` — clean 160-bit mask, verified
  - V2 AMM: `mul(amount, numerator)` wraps at 2^224 — economically infeasible
  - V2 pair k-invariant provides defense-in-depth against inflated output
  - Custom numerator: capped at uint32, defaults to 997M if zero
  - Invalid protocol values (3-7): silent no-op, minReturn catches it
  - Selector index: bounded at 17, within packed constant buffer
  - CREATE2 validation: structurally correct, hardcoded factory + init hash
- **Status**: FALSIFIED — assembly is well-engineered

### H6: _callTransferFromWithSuffix with Exotic Tokens — NOT EXPLOITABLE
- **Analysis result**:
  - Suffix appended at offset 0x64 (after from/to/amount)
  - Standard ERC20 ignores extra calldata
  - No known tokens parse extra transferFrom calldata
  - Suffix comes from maker-signed extension data (maker's own risk)
- **Status**: FALSIFIED — theoretical only, no practical impact

### Approval Drain via Any Path — NOT EXPLOITABLE
- **Analysis**: Exhaustive audit of all 10 transferFrom sites in the contract
- **Result**: `from` is always `msg.sender` (hardcoded) or ECDSA-verified `order.maker`
- **No path** exists to set `from` to an arbitrary victim address
- **Status**: FALSIFIED

## Falsified (early)

### H3: Multi-hop Intermediate Token Theft via Fake Pool
- **Reason**: attacker is always the caller → input tokens are the attacker's own
- **Status**: FALSIFIED

## Backlog (not investigated — low priority)
- Permit2 integration edge cases (cross-allowance confusion)
- ERC777 callback during token transfer in swap flow (mitigated by per-order CEI)
- WETH wrap/unwrap atomicity in edge cases
- Flash loan + multi-hop ordering attacks (covered by "source tokens from msg.sender" invariant)

## Overall Assessment

The 1inch V6 AggregationRouter is well-designed for its threat model. The key architectural principle — **source tokens always come from msg.sender** — effectively prevents approval drain attacks. The unprotected callbacks (H1, H2) are acknowledged design choices (documented in code comments at line 5596-5597) with near-zero current economic impact. The assembly internals are carefully implemented with proper masking, bounds checking, and defense-in-depth from underlying DEX pool invariants.

**No E3-grade vulnerability found.**
