# Memory (curve-tricrypto2)

## Pinned Reality
- chain_id: 1
- fork_block: 24486676
- ETH price at fork: ~$1,944
- BTC price at fork: ~$66,131
- attacker_tier: public mempool (flash loans from Aave/Balancer)
- capital_model: flash allowed; unlimited single-tx capital

## Contract Map Summary
- core: Tricrypto2 Pool (Vyper 0.2.12), CryptoMath, LP Token, Views
- proxies: NONE (all immutable deployment)
- oracles: Internal EMA price oracle (ma_half_time=600s)
- DEX: Self-contained CryptoSwap AMM for USDT/WBTC/WETH

## Control Plane & Auth
- owner: 0x7a1f2f99b65f6c3b2413648c86c0326cff8d8837 (contract, code size 5282)
- Auth: simple owner check (msg.sender == self.owner)
- commit/apply pattern with ADMIN_ACTIONS_DELAY = 3 days
- kill_deadline: 1631395083 (Sep 2021) — EXPIRED -> kill_me() permanently disabled
- admin_actions_deadline: 0 (no pending actions)
- future_A_gamma_time: 0 (no active ramp)
- Bypass: N/A — no proxy, no init, owner is fixed

## On-Chain State (fork block 24486676)
- Balances: 3.45M USDT, 52.46 WBTC, 1787.33 WETH
- TVL: ~$10.4M (33/33/33% balanced)
- LP supply: 6434.13 tokens
- A: 170.76 (raw: 1707629), gamma: 1.18e13
- D: 10,466,728 (18 dec)
- virtual_price: 1.0669
- price_oracle: WBTC=66131, WETH=1943
- price_scale: WBTC=66780, WETH=1966
- Fees: mid=0.03%, out=0.3%, admin=50%, dynamic fee=0.074%
- is_killed: false, kill_deadline expired
- allowed_extra_profit: 2e12, adjustment_step: 4.9e14
- ma_half_time: 600s

## Solvency Equation
CryptoSwap invariant: K*D^(N-1)*sum(x_i) + prod(x_i) = K*D^N + (D/N)^N
LP solvency: virtual_price = D / totalSupply >= 1.0 (monotonically increasing from fees)

## Fork Test Results (24 tests, all PASSED)

### CurveTricrypto.t.sol (11 tests)
- H1: Donation+gulp+swap NET NEGATIVE ($18K advantage vs $1M donation cost)
- H4: VP inflation from donation tiny: 7bps increase for 1M USDT donation
- H5: Read-only reentrancy VP staleness: only 2 bps for $1M swap
- H7: Sandwich on add_liquidity LOST 6.16 WETH for attacker
- H8: Admin fee LP minting: LP minted << donation cost
- H12: Rounding on small swaps: 0 to attacker
- H14: D consistency after removal: deviation only 1627 wei
- H15: Oracle drift single-block: only 0.001% (EMA dampens)

### CurveTricryptoDeep.t.sol (8 tests)
- Deep1: Donation causes last_prices jump 1943->2491 (28%) but oracle barely moves
- Deep2: Multi-block oracle drift: 700bps (7%) over 10 blocks with 2M USDT donation
- Deep3: Swap fair value confirmed within 2.5% of oracle
- Deep4: VP monotonically increases through round-trip swaps (correct)
- Deep5: Price scale/oracle divergence: 0.97% natural divergence
- Deep7: Owner is a contract (code size 5282 bytes)
- Deep8: use_eth=true path confirmed (ETH sent via raw_call)

### CurveTricryptoFinal.t.sol (5 tests)
- Final1: Corrected donation accounting: NET LOSS $914,822
  - Cost: $2.02M (500K deposit + 1M donation + 265K WBTC + 253K WETH)
  - Received: $1.10M (440K USDT + 332K WBTC + 331K WETH)
  - Attacker LP share: 888 bps -> only recovers ~8.9% of donation
- Final2: Oracle manipulation cost/benefit: 700bps drift costs 2M USDT
  - Need >$28.6M external exposure to profit from oracle manipulation
- Final3: VP staleness during ETH callback: only 2bps for $1M swap
- Final4: Exchange rates confirm pool is functioning correctly
- Final5: Pool is perfectly balanced at 33/33/33%

## Conclusion: NO E3-QUALIFYING VULNERABILITY FOUND
All 15 hypotheses tested; none produces net-positive extraction:
1. Donation attacks: distributed to all LP holders, NET LOSS for attacker
2. Oracle manipulation: EMA dampens single-block; multi-block drift costs >$2M donation
3. Read-only reentrancy: VP staleness only 2bps, negligible
4. Sandwich attacks: CryptoSwap's concentrated liquidity defeats sandwich
5. Admin fee manipulation: minting amount << donation cost
6. Rounding exploitation: zero extractable value
7. D consistency: deviation is wei-scale, not exploitable

## Coverage Status
- entrypoints: notes/entrypoints.md
- control plane: notes/control-plane.md
- taint map: notes/taint-map.md
- tokens: notes/tokens.md
- numeric boundaries: notes/numeric-boundaries.md
- feasibility: notes/feasibility.md
- value flows: notes/value-flows.md
- assumptions: notes/assumptions.md
- hypotheses: notes/hypotheses.md
