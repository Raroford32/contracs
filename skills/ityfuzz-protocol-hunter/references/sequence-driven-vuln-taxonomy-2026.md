# Sequence-Driven Vulnerability Taxonomy (2026)

Use this list as a **hypothesis generator** for fuzz campaigns. The goal is not to “name the bug”;
it is to synthesize **stateful, multi-step sequences** that move the protocol across boundaries
where accounting/oracle/state-machine assumptions break.

## Value, accounting & invariant discontinuities

1. Cross-Module Conservation Breaks
2. Net-Positive Closed-Loop Cycles
3. Share Price / Exchange-Rate Inflation Paths
4. Debt-Collateral Accounting Desynchronization
5. Bootstrap Exchange-Rate Shaping (First Depositor / First Borrower)
6. Zero-Supply / Empty-Pool Boundary Exploits
7. Cache Invalidation Failures at Boundaries
8. Rounding Direction Drift Amplified by Repetition
9. Precision Loss Compounding Under Repetition
10. Unit/Scale Normalization Applied Twice (or Skipped Once)
11. Rate Provider / Index Provider Mis-measurement
12. Invariant Solver vs Implementation Mismatch (Curve / Stable-Math Drift)
13. Extreme-Input Domain Discontinuities (wrap/truncate -> free/near-free pricing)
14. Path-Dependent Branch Flip Extraction
15. "Move the Measurement -> Redeem the Measurement" Tight-Loop Windows

## Reference, oracle & valuation discontinuities

16. Attacker-Chosen Reference Injection (pool/oracle/path)
17. Execution-Time Spot Liquidity Shaping Used as "Truth"
18. TWAP Window Engineering / Observation Poisoning
19. Staleness / Heartbeat Lag Exploited by Timing
20. Cross-Oracle Inconsistency (same asset, different truth)
21. Decimal / Inversion / Normalization Drift Across Feeds
22. Outlier Acceptance (missing clamps / missing circuit breakers)
23. Manipulable On-Chain References Used for Caps, Limits, or Eligibility

## Sequencing, state machine & multi-tx discontinuities

24. Non-Atomic Global Updates with Interleavable Value Realization
25. Snapshot-Checked Solvency vs Mutable Execution-Time State
26. Multi-Tx State Shaping -> Harvest (setup phase + realization phase)
27. Epoch / Cooldown / Delay Realization Attacks (delay != fix)
28. Order-Execution Windows with Incomplete Coupled Updates
29. State Machine Skip / Re-entry via Alternate Call Paths
30. Callback Context Forgery (hooks/callbacks treated as authenticated)

## MEV & market microstructure discontinuities

31. Slippage Margin Harvest via Bracketing (sandwich / backrun sequences)
32. MEV Extraction Around Rebalance / Harvest / Settlement Steps
33. Liquidation-Swap-Arbitrage Triangle Exploits
34. Keeper / Auction / Priority Execution Gameability
35. Atomic Capital Amplification for Multi-Protocol Sequences

## Composability, programmability & "legit feature becomes exploit" discontinuities

36. Approved-Module Steering via Attacker-Controlled Execution Args
37. Instrument Confusion (asset treated as different instrument/class)
38. Programmable Router/Aggregator Payload Abuse (protocol-intended flexibility -> exploit)
39. Long-Lived Approval Surfaces Turning into Extraction Paths
40. Liquidity / Reward / Fee Distribution Function Gaming
41. Assumption Failure: Receipt/Staked Token Transferability Creates Repeatable Side Effects

## Cross-domain & chain-specific discontinuities (still permissionless)

42. Validator/Stake Concentration to Satisfy "Economic Security" Assumptions
43. Cross-Chain Supply Accounting Discontinuities (mint <-> collateral mismatch)
44. Precompile/System-Path Validation Gaps (chain-specific privileged routes)
45. EVM Semantic Divergence Exploits (chain-specific edge behaviors)
46. Domain Separation / Replay Failures Across Message Paths

