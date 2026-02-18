# Memory (1inch-ecosystem)

## Pinned Reality
- chain_id: 1
- fork_block: 24482400
- attacker_tier: public mempool (escalate to builder if needed)
- capital_model: flash loans from Aave/dYdX/Balancer, unlimited single-tx capital

## Contract Map Summary
- AggregationRouterV6: 0x111111125421cA6dc452d289314280a0f8842A65 (5786-line, Solidity 0.8.23)
- AggregationRouterV5: 0x1111111254EEB25477B68fb85Ed929f73A960582
- AggregationRouterV4: 0x1111111254fb6c44bAC0beD2854e76F90643097d
- AggregationRouterV3: 0x11111112542D85B3EF69AE05771c2dCCff4fAa26
- 1INCH Token: 0x111111111117dC0aa78b770fA6A738034120C302 (ERC20Permit + Burnable + Ownable)
- st1INCH: 0x9A0C8Ff858d273f57072D714bca7411D717501D7 (non-transferable, 30-day min lock)
- LimitOrderProtocolV2: 0x119c71D3BbAC22029622cbaEc24854d3D32D2828
- LimitOrderProtocolV3: 0x227B0c196eA8db17A665EA6824D972A64202E936
- Settlement: 0xfb2809a5314473E1165f6B58018E20ed8F07b840
- OffchainOracle: 0x07D91f5fb9Bf7798734C3f606dB065549F6893bb
- MooniswapFactory: 0xbAF9A5d4b0052359326A6CDAb54BABAa3a3A9643
- OneInchExchange (V2): 0x111111125434b319222CdBf8C261674aDB56F3ae
- Permit2 (shared): 0x000000000022D473030F116dDEE9F6B43aC78BA3
- UniV3 Factory: 0x1F98431c8aD98523631AE4a59f267346ea31F984
- WETH: 0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2
- 0x111cff45... ($98M): Gnosis MultiSigWallet 3-of-3, NOT a 1inch protocol contract
- Router V6 Owner: 0x9F8102b1bB05785BaD2874f2C7B1aaea4c6D976a

## Control Plane & Auth
- V6: Ownable (OZ v5) + Pausable + EIP-712 sigs + MakerTraits + nonce/epoch
- V5: Ownable (OZ v4) + simulate() delegatecall (always reverts) + destroy() selfdestruct
- V4: Ownable + destroy() selfdestruct
- V3: Ownable only
- st1INCH: Ownable, no governance execution, non-transferable, 30-day min lock
- Governance: Off-chain Snapshot + multisig execution (NOT atomic, NOT exploitable)
- bypass hypotheses: All falsified — standard OZ implementations, no reinit, not upgradeable

## Coverage Status
- entrypoints: notes from V6 engagement (analysis/engagements/1inch-v6/notes/entrypoints.md)
- control plane: analysis/engagements/1inch-v6/notes/control-plane.md + ecosystem notes
- taint map: analysis/engagements/1inch-v6/notes/taint-map.md (11 callsites)
- tokens: analysis/engagements/1inch-v6/notes/tokens.md
- numeric boundaries: analysis/engagements/1inch-v6/notes/numeric-boundaries.md
- feasibility: analysis/engagements/1inch-v6/notes/feasibility.md
- value flows: analysis/engagements/1inch-v6/notes/value-flows.md
- assumptions: analysis/engagements/1inch-v6/notes/assumptions.md
- hypotheses: notes/hypotheses.md (H7-H15 all resolved)
- approval surface: notes/approval-surface.md (V5 complete, V4 confirmed safe, V3 minimal)
- unknown contract: notes/unknown-98m-contract.md (Gnosis multisig, not exploitable)

## Value Model Summary
- custody assets: NONE between txs (non-custodial router, 1-wei gas optimization) across ALL versions
- entitlements: N/A (routers don't track entitlements)
- key measurements: minReturn check on output (V6), threshold in takerTraits (V6 limit orders)
- key settlements: transferFrom(msg.sender, pool/recipient, amount) — invariant across V3-V6
- solvency equation: router_balance <= 1 wei per token (by design, all versions)

## Economic Model
- money entry: user tokens via transferFrom(msg.sender, ...) — ALL versions
- money exit: pool output to user-specified recipient
- value transforms: external DEX pools (not the router)
- fee extraction: no explicit protocol fee in router; 1inch captures spread off-chain
- actor dual-roles: none exploitable identified across ecosystem
- dependency gaps: none — external pools enforce their own invariants
- top implicit assumptions:
  1. Router holds no value between txs (A1 — CONFIRMED, <=1 wei by design)
  2. Source tokens always from msg.sender (A2 — VERIFIED across ALL 4 router versions)
  3. CREATE2 prevents fake V3 pool callbacks (A3 — VERIFIED in V4/V5/V6)
  4. ECDSA/ERC-1271 prevents forged order signatures (A4 — VERIFIED)
  5. Permit2 allowances are per-spender (A5 — VERIFIED, no cross-protocol confusion)

## Confirmed Findings (not E3)
1) H1: curveSwapCallback — V6 only, anyone can drain router balance, zero access control
   - impact: < $0.01 (router balance = 0 in practice)
2) H2: uniswapV3SwapCallback payer==self — V6 only, same drain via FakeV3Pool
   - impact: same as H1

## Falsified Hypotheses (all evidence-grounded)
- H3: Multi-hop theft — attacker = caller = fund source
- H4: Taker reentrancy — CEI per-order prevents double-fill
- H5: Assembly overflow — clean masking, V2 k-check defense-in-depth
- H6: transferFrom suffix — standard ERC20 ignores extra calldata
- H7: Cross-router approval drain — ALL routers (V3/V4/V5/V6) use msg.sender or ECDSA-verified maker
- H8: Permit2 cross-protocol confusion — per-spender allowances, always msg.sender or verified maker
- H9: IERC1271 contract signature confusion — tokens must come from maker contract via transferFrom
- H10: Pre-interaction state manipulation — amounts computed before pre-interaction, CEI pattern
- H11: Flash loan limit order fills — designed behavior, not an exploit
- H12: Callback chain amplification — attacker can only steal own tokens
- H14: st1INCH governance flash attack — 5 independent kill points (30-day lock, no on-chain governance, non-transferable, off-chain Snapshot, independent owner addresses)
- H15: Taker mid-swap manipulation — amounts fixed before takerInteraction, threshold protection
- Approval drain — all transferFrom sites across V3-V6 use msg.sender or ECDSA-verified maker

## Last Experiment
- command: Deep analysis of V6 order fill chain (18 steps), V5/V4/V3 transferFrom audit, $98M contract bytecode analysis, st1INCH governance analysis
- evidence: notes/approval-surface.md, notes/unknown-98m-contract.md, notes/hypotheses.md
- result: ALL 15 hypotheses resolved. No E3-grade vulnerability found across entire 1inch ecosystem.
- belief change: 1inch ecosystem is comprehensively secure for its threat model

## Next Discriminator
- No further discriminators needed — all hypotheses resolved across full ecosystem
- Possible future: monitor for new 1inch contract deployments; analyze resolver/executor contracts; analyze Fusion-specific extension contracts; ItyFuzz campaigns on cross-contract universe

## Open Unknowns
- Resolver/executor contract internals (off-chain infrastructure)
- Specific IAmountGetter extension contracts used by Fusion orders (maker-deployed, not part of core protocol)
- Whether accumulation events ever cause router balance > 1 wei
