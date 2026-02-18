# Feasibility — 1inch V6 AggregationRouter

## H1: curveSwapCallback Drain

| Constraint | Assessment |
|---|---|
| Attacker tier | Public mempool — no ordering requirement |
| Ordering requirement | None — single tx, no front/backrun needed |
| Capital requirement | Zero — only gas costs |
| Oracle dependency | None |
| Liquidity requirement | None |
| Prerequisite | Router must hold > 0 tokens of target |

**Feasibility**: TRIVIALLY EXECUTABLE by anyone. The only constraint is that the router must actually hold tokens worth stealing.

**Current real-world impact**: Near-zero. At block 21880000, the router holds 0 WETH and 0 USDC. The 1-wei gas optimization appears to keep balances at exactly 0 or 1 wei for most tokens. The attack would yield < $0.01 in most cases.

**Escalation scenarios**:
1. Accidental token deposit to router address — drainable immediately by MEV bots
2. Positive rebasing token accumulation — drainable as it accrues
3. Airdrop to router address — drainable immediately
4. Future integration that temporarily holds tokens on router — drainable during the window

**Fork test evidence**: `exploit_test/test/OneInchV6CallbackDrain.t.sol::test_curveSwapCallback_drain` — 5/5 PASS

## H2: uniswapV3SwapCallback Drain (payer==self)

| Constraint | Assessment |
|---|---|
| Attacker tier | Public mempool — no ordering requirement |
| Ordering requirement | None — single tx |
| Capital requirement | Contract deployment gas only (~218k gas for FakeV3Pool) |
| Oracle dependency | None |
| Liquidity requirement | None |
| Prerequisite | Router must hold > 0 tokens of target; attacker must deploy FakeV3Pool |

**Feasibility**: TRIVIALLY EXECUTABLE. Same constraints as H1, slightly higher gas cost due to contract deployment.

**Fork test evidence**: `exploit_test/test/OneInchV6CallbackDrain.t.sol::test_uniswapV3SwapCallback_drain_via_fake_pool` — 5/5 PASS

## H3: Multi-hop Intermediate Token Theft — FALSIFIED

**Reason**: The attacker is always the caller. In unoswapTo2/unoswapTo3, input tokens come from msg.sender. Fake pools in the hop chain can only redirect the attacker's own tokens.

## H4: Taker Interaction Reentrancy — NOT EXPLOITABLE

| Constraint | Assessment |
|---|---|
| Same-order double-fill | Prevented by CEI per-order (invalidator updated before callbacks) |
| Cross-order reentrancy | Allowed by design; each order has independent state |
| Flash-loan window | Intentional design feature; taker gets maker tokens before paying |

**Assessment**: No exploitable reentrancy. The per-order CEI pattern is correct.

## H5: Assembly Calldata Parsing Overflow — NOT EXPLOITABLE

| Concern | Assessment |
|---|---|
| Address extraction | Clean mask: `and(dex, _ADDRESS_MASK)` where _ADDRESS_MASK = (1<<160)-1 |
| Overflow in V2 amount*numerator | Theoretical wrapping at 2^224, but economically infeasible |
| Invalid protocol enum values | Silent no-op with minReturn revert — self-griefing only |
| Custom numerator inflation | V2 pair's own k-invariant check prevents over-extraction |
| CREATE2 validation | Sound — hardcoded factory + init code hash + caller() check |

## Approval Drain Vector Analysis — NOT EXPLOITABLE

All 10 transferFrom sites verified. No path exists to set `from` to an arbitrary victim address.

## Summary: No E3-grade Finding

The callback drains (H1, H2) are confirmed but yield < $0.01 under normal conditions. No high-impact vulnerability found despite exhaustive analysis.
