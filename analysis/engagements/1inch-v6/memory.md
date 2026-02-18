# Memory (1inch-v6)

## Pinned Reality
- chain_id: 1
- fork_block: 21880000
- attacker_tier: public mempool
- capital_model: flash loans allowed, unlimited single-tx capital

## Contract Map Summary
- core: 0x111111125421cA6dc452d289314280a0f8842A65 (AggregationRouterV6)
- NOT a proxy — direct deployment, 5786-line flattened Solidity (0.8.23)
- Hierarchy: AggregationRouterV6 is EIP712, Ownable, Pausable, ClipperRouter, GenericRouter, UnoswapRouter, PermitAndCall, OrderMixin
- Owner: 0x9F8102b1bB05785BaD2874f2C7B1aaea4c6D976a
- Uses Uniswap V3 factory 0x1F98431c8aD98523631AE4a59f267346ea31F984 (hardcoded)
- WETH: 0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2 (hardcoded)

## Control Plane & Auth
- auth mechanisms: Ownable (OZ v5), Pausable, EIP-712 sigs, MakerTraits, nonce/epoch
- auth state locations: OZ ERC-7201 namespaced storage
- auth writers: owner only for pause/rescue/transfer; msg.sender for cancel/epoch
- bypass hypotheses: None successful (standard OZ v5, no reinit, not upgradeable)
- bypass attempts: N/A — standard implementations, no custom gates

## Coverage Status (all complete)
- entrypoints: notes/entrypoints.md
- control plane: notes/control-plane.md
- taint map: notes/taint-map.md (11 callsites classified)
- tokens: notes/tokens.md
- numeric boundaries: notes/numeric-boundaries.md
- feasibility: notes/feasibility.md
- evm semantics: notes/evm-semantics.md (PUSH0, assembly blocks verified)
- value flows: notes/value-flows.md
- assumptions: notes/assumptions.md (12 assumptions enumerated)
- hypotheses: notes/hypotheses.md (6 hypotheses + approval drain analysis)

## Value Model Summary
- custody assets: NONE between txs (non-custodial router, 1-wei gas optimization)
- entitlements: N/A (router doesn't track entitlements)
- key measurements: minReturn check on output
- key settlements: transferFrom(msg.sender, pool/recipient, amount)
- solvency equation: router_balance <= 1 wei per token (by design)

## Economic Model
- money entry: user tokens via transferFrom(msg.sender, ...)
- money exit: pool output to user-specified recipient
- value transforms: external DEX pools (not the router)
- fee extraction: no explicit protocol fee in router; 1inch captures spread off-chain
- actor dual-roles: none exploitable identified
- dependency gaps: none — external pools enforce their own invariants
- top implicit assumptions:
  1. Router holds no value between txs (A1 — EXPLOITABLE via H1/H2 but low impact)
  2. Source tokens always from msg.sender (A2 — VERIFIED across all 10 transferFrom sites)
  3. CREATE2 prevents fake V3 pool callbacks (A3 — VERIFIED)

## Confirmed Findings (not E3)

1) H1: curveSwapCallback — anyone can drain router balance, zero access control
   - broken assumption: A1 (router holds no value)
   - evidence: exploit_test/test/OneInchV6CallbackDrain.t.sol (5/5 PASS)
   - impact: < $0.01 at block 21880000 (router balance = 0)

2) H2: uniswapV3SwapCallback payer==self — same drain, via FakeV3Pool contract
   - same broken assumption: A1
   - evidence: same test file (5/5 PASS)
   - impact: same as H1

## Falsified Hypotheses
- H3: Multi-hop theft — attacker = caller = fund source
- H4: Taker reentrancy — CEI per-order prevents double-fill
- H5: Assembly overflow — clean masking, V2 k-check defense-in-depth
- H6: transferFrom suffix — standard ERC20 ignores extra calldata
- Approval drain — all transferFrom sites use msg.sender or ECDSA-verified maker

## Last Experiment
- command: forge test --fork-url ... --fork-block-number 21880000 --match-contract OneInchV6 -vvvv
- evidence: exploit_test/test/OneInchV6CallbackDrain.t.sol — 5/5 PASS
- result: Both callback drains work perfectly on fork. Router balance = 0 in practice.
- belief change: H1/H2 confirmed mechanically but low economic impact

## Next Discriminator
- No further discriminators needed — all hypotheses resolved
- Possible future: monitor router balance across blocks for accumulation events

## Open Unknowns
- None significant for arbitrary call focus
