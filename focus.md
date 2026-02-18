# Focus Card — Current Investigation State

last_updated: 2026-02-18T09:30:00Z

## Goal (Never Changes)

Discover an **E3-promoted**, economically feasible exploit in a mature, battle-tested protocol.

**Stop Conditions:**
1. E3 achieved with net_profit > $10,000 USD
2. External interrupt (emit resume_pack.md)

---

## Current Status

**7 sessions completed. Zero E3 exploits found across 1568+ contracts.**

### Session 7: 1inch Ecosystem Cross-Protocol Audit (COMPLETE)

Full cross-contract ecosystem audit of the 1inch protocol — not just the V6 router, but all router versions (V3-V6), st1INCH staking, governance, limit order protocol, Fusion settlement, Permit2 integration, and a $98M unverified contract.

**Contracts analyzed this session:**
- AggregationRouterV6 (5786 lines) — 2 low-impact callback drains (H1/H2)
- AggregationRouterV5 (4809 lines) — 11 transferFrom sites audited, all safe
- AggregationRouterV4 (2375 lines) — all transferFrom sites safe
- AggregationRouterV3 (1276 lines) — only msg.sender transfers
- st1INCH staking (98KB) — non-transferable, 30-day lock, no on-chain governance
- 1INCH token — ERC20Permit + Burnable, no delegation/checkpoints
- $98M contract (0x111cff45...) — Gnosis MultiSigWallet 3-of-3, NOT 1inch protocol
- Permit2 integration analysis
- V6 order fill chain (18-step sequence analysis)

**15 hypotheses tested (H1-H15), results:**
- H1/H2: Confirmed but negligible (router balance = 0, < $0.01 extractable)
- H3-H6: Falsified (single-contract vectors)
- H7: Cross-router approval drain — FALSIFIED (all routers enforce from=msg.sender)
- H8: Permit2 cross-protocol confusion — FALSIFIED (per-spender allowances)
- H9: IERC1271 signature confusion — FALSIFIED (tokens from maker contract only)
- H10: Pre-interaction state manipulation — FALSIFIED (CEI pattern correct)
- H11: Flash loan order fills — FALSIFIED (designed behavior, not exploit)
- H12: Callback chain amplification — FALSIFIED (attacker steals own tokens)
- H14: Governance flash attack — FALSIFIED (5 independent barriers)
- H15: Taker mid-swap manipulation — FALSIFIED (amounts fixed before callback)

**Key findings:**
- 1inch ecosystem is comprehensively secure for its threat model
- Core invariant `from ∈ {msg.sender, ECDSA_verified_maker}` holds across all versions
- V5/V4 actually MORE secure than V6 for callbacks
- Non-custodial design (router balance ≤ 1 wei) prevents custody-based attacks
- No on-chain governance execution exists; off-chain Snapshot + multisig

### Prior Sessions (1-6)
- EtherDelta, Exchange 0x2a0c, Curve Tricrypto2, Curve Aave Pool
- xSUSHI, MasterChef, Compound V1 (PAUSED)
- dYdX SoloMargin — All 7 vectors ruled out via fork test
- Parity Multisig (frozen), Tornado Cash (zk-SNARK)
- 7 Compound V2 cTokens, Multiple multisigs/timelocks/bridges
- 188+ contracts from sessions 1-4, process framework in session 5

### Key Observations
1. All DeFi protocols use CEI, reentrancy guards, SafeMath/checked math
2. Oracles are robust (MakerDAO Medianizer, Chainlink multi-oracle)
3. Interest accrual staleness is economically insignificant
4. Cross-protocol vectors not actionable across all tested targets
5. High-ETH contracts are multisigs, frozen wallets, bridges, or timelocks
6. **1inch cross-protocol composition is secure** — no inter-contract exploit chains found

---

## Engagement Artifacts

- `analysis/engagements/1inch-v6/` — Single-contract V6 analysis
- `analysis/engagements/1inch-ecosystem/` — Full ecosystem cross-protocol audit
- `analysis/engagements/1inch-ecosystem/memory.md` — Ecosystem belief tracker
- `analysis/engagements/1inch-ecosystem/notes/hypotheses.md` — All 15 hypotheses
- `analysis/engagements/1inch-ecosystem/notes/cross-contract-interactions.md` — Interaction matrix
- `analysis/engagements/1inch-ecosystem/notes/approval-surface.md` — V5 transferFrom audit
- `analysis/engagements/1inch-ecosystem/notes/unknown-98m-contract.md` — $98M contract investigation
- `exploit_test/test/OneInchV6CallbackDrain.t.sol` — H1/H2 fork-grounded PoC (5/5 PASS)

---

## Next Actions (Priority Ordered)

1. **Scan remaining ~1200 unanalyzed contracts** from contracts.txt
2. **Look for exotic/custom contracts** — Non-standard DeFi with bespoke logic
3. **Analyze resolver/executor contracts** — 1inch Fusion resolver internals
4. **Monitor for new contract deployments** — Fresh contracts may have less battle-testing

---

## Foundry Fork Tests Created

- `test/DydxSoloExploit.t.sol` - dYdX SoloMargin state query + exploit probes
- `exploit_test/test/OneInchV6CallbackDrain.t.sol` - 1inch V6 callback drain PoC (5/5 PASS)
