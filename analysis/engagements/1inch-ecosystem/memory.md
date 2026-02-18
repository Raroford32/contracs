# Memory (1inch-ecosystem)

## Pinned Reality
- chain_id: 1
- fork_block: latest (dynamic fork via RPC)
- attacker_tier: public mempool (escalate to builder if needed)
- capital_model: flash loans from Aave/dYdX/Balancer, unlimited single-tx capital

## Contract Map Summary
- AggregationRouterV6: 0x111111125421cA6dc452d289314280a0f8842A65 (5786-line, Solidity 0.8.23)
- AggregationRouterV5: 0x1111111254EEB25477B68fb85Ed929f73A960582
- AggregationRouterV4: 0x1111111254fb6c44bAC0beD2854e76F90643097d
- AggregationRouterV3: 0x11111112542D85B3EF69AE05771c2dCCff4fAa26
- OneInchExchangeV2: 0x111111125434b319222CdBf8C261674aDB56F3ae
- 1INCH Token: 0x111111111117dC0aa78b770fA6A738034120C302
- st1INCH: 0x9A0C8Ff858d273f57072D714bca7411D717501D7 (260M 1INCH, non-transferable, 30-day min lock)
- LimitOrderProtocolV2: 0x119c71D3BbAC22029622cbaEc24854d3D32D2828
- LimitOrderProtocolV3: 0x227B0c196eA8db17A665EA6824D972A64202E936
- Settlement (Fusion): 0xfb2809a5314473E1165f6B58018E20ed8F07b840
- FeeBank: 0x3608aA1a7F15f0F6e7119FD3CB47C69D4dAfBeAd
- OffchainOracle: 0x07D91f5fb9Bf7798734C3f606dB065549F6893bb
- MooniswapFactory: 0xbAF9A5d4b0052359326A6CDAb54BABAa3a3A9643
- MooniswapPool3 (ETH/WBTC): 0x6a11F3E5a01D129e566d783A7b6E8862bFD66CcA

## Control Plane & Auth
- V6: Ownable (OZ v5) + Pausable + EIP-712 sigs + MakerTraits + nonce/epoch
- V5: Ownable + simulate() delegatecall (always reverts) + destroy() selfdestruct
- Settlement: onlyLimitOrderProtocol modifier + Whitelist + priority fee validation
- st1INCH: Ownable, non-transferable, ReentrancyGuard on ERC20Pods, time-locked
- LOP V3: interaction whitelist, per-order invalidator (CEI correct)
- LOP V2: NO interaction whitelist (but callback target is maker-signed)
- bypass hypotheses: All falsified (standard OZ, no reinit, not upgradeable)

## Coverage Status (paths relative to analysis/engagements/1inch-ecosystem/)
- fork tests: exploit_test/test/OneInchEcosystemExploit.t.sol (10 tests)
- fork tests: exploit_test/test/OracleDeepExploit.t.sol (5 tests)
- fork tests: exploit_test/test/CrossContractExploit.t.sol (9 tests)
- bundled sources: contract-bundles/chain-1/ (11 addresses bundled)
- V6-specific notes: ../1inch-v6/notes/ (entrypoints, control-plane, taint-map, tokens, etc.)

## Value Model Summary
- custody assets: NONE in routers (0 balance in V6; dust in V3/V5)
- st1INCH custody: 260,219,530 1INCH (~$78M+), protected by non-transferable + time-lock
- FeeBank: resolver credit system, deposit/withdraw 1INCH, checked math
- solvency: st1INCH 1INCH balance == totalDeposits (surplus = 0, exactly solvent)

## Corridor Results (ALL with fork evidence)

### Corridor A: Mooniswap AMM — EXHAUSTED
- Sandwich: -18.88 ETH loss on 50 ETH attempt (virtual balance protection)
- Virtual balance decay: 33.91 ETH loss on 100 ETH round-trip even after full 108s decay
- Rounding loop: 0.647 ETH loss over 10x 1 ETH round-trips (~1.5% per trip)
- Donation: No receive() for ETH; ERC20 donation doesn't bypass virtual balance
- LP manipulation: k invariant increases (fees captured correctly)
- Referral extraction: Zero LP rewards earned
- First depositor: Factory active but no victim value to extract

### Corridor B: Settlement/Fusion — EXHAUSTED
- Priority fee: Valid EVM constraint, no underflow
- Dutch auction math: Correct piecewise linear interpolation + gas bump compensation
- IntegratorFee _sendEth: State written before external calls
- WhitelistExtension: 80-bit masking, 2^80 infeasible to brute-force
- ResolverFee: In order extension (maker-signed, immutable)

### Corridor C: OffchainOracle — EXHAUSTED
- WBTC via Mooniswap: 137 bps change at 200 ETH cost (cost-prohibitive)
- 1INCH via Mooniswap: 1 bps from 55 ETH (negligible)
- USDC/USDT: 0 bps (negligible)
- WETH/USDC: 0 bps change even after 200 ETH manipulation
- Adapter weights: Top 2 WETH adapters via 0xFFFF dominate (99.9% of weight^2)

### Corridor D: LOP V2/V3 — EXHAUSTED
- V2 unwhitelisted interaction: Callback target is maker-signed, not attacker-controlled
- V3 CEI: Per-order invalidator written BEFORE external calls, prevents double-fill
- V3 taker interaction: Flash fill by design, amounts fixed before callback
- V3 extension data: Included in EIP-712 order hash (maker-signed, immutable)

### Corridor E: V6 Router — EXHAUSTED
- curveSwapCallback: Zero access control BUT router holds 0 balance
- uniswapV3SwapCallback (payer==self): Same — 0 balance to drain
- simulate(): Always reverts (state rollback), safe by design
- Generic swap: Executor runs in own context, cannot abuse router approvals

### Additional Vectors — EXHAUSTED
- st1INCH early withdrawal: loss + ret == depAmount exactly at ALL time points
- st1INCH dust deposit: 1 wei → 4 wei stBal, 0 voting power, no exploitation
- st1INCH depositFor: Can only ADD value, cannot extend lock or reduce balance
- st1INCH solvency: Exactly 0 surplus (tight but correct)
- FeeBank/FeeBankCharger: Checked math, proper invariant, supply-bounded unchecked ops
- ERC20Pods: ReentrancyGuard, 500k gas limit, silent failure = no protocol harm
- VotingPowerCalculator: Exponential decay via bit-manipulation, rounding bias systematic but negligible
- Legacy routers: V3 holds ~$881 (263 USDC + 618 USDT), V2 holds ~$1,308 USDT — not E3 scale
- Cross-protocol oracle→predicate: Cost-prohibitive (~200 ETH for <2% change)

## Falsified Hypotheses (27 total, all with evidence)
- H1-H15: See notes/hypotheses.md (original V6 analysis)
- H16: Mooniswap sandwich — fork test: -18.88 ETH loss
- H17: Virtual balance decay exploit — fork test: -33.91 ETH after full decay
- H18: Oracle manipulation → downstream — fork test: 0 bps on WETH/USDC
- H19: Mooniswap donation — fork test: no receive()
- H20: LP token manipulation — fork test: k invariant increases
- H21: Referral extraction — fork test: 0 rewards
- H22: curveSwapCallback drain — fork test: 0 tokens
- H23: st1INCH early withdrawal underflow — fork test: math exact
- H24: st1INCH depositFor griefing — fork test: only adds value
- H25: Mooniswap rounding accumulation — fork test: -0.647 ETH per 10 trips
- H26: Cross-protocol oracle predicate — fork test: 200 ETH → 0 bps on WETH/USDC
- H27: First depositor Mooniswap — no victim value, factory active but pools tiny

## Last Experiment
- command: 9 fork tests in CrossContractExploit.t.sol
- evidence: exploit_test/test/CrossContractExploit.t.sol (ALL PASS)
- result: No E3-grade vulnerability. All corridors exhausted with fork evidence.
- belief change: 1inch ecosystem is comprehensively secure for E3 threat model

## Next Discriminator
- All 5 corridors exhausted with fork evidence
- 24+ fork tests executed, 27+ hypotheses falsified
- Remaining avenues: ItyFuzz automated campaigns (not available), Tenderly deep traces
- These are diminishing returns — manual analysis + fork tests covered all primary attack surfaces

## Open Unknowns
- Resolver/executor contract internals (off-chain infrastructure, not part of on-chain attack surface)
- ItyFuzz automated sequence discovery (tool not available in environment)
- Tenderly evidence-grade traces (no API key available)
