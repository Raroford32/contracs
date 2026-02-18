# Memory (liquity-v1)

## Pinned Reality
- chain_id: 1
- fork_block: 21486502
- ETH price at fork: $3,368
- attacker_tier: public mempool (flash loans from Aave/dYdX/Balancer)
- capital_model: flash allowed; unlimited single-tx capital

## Contract Map Summary
- core: TroveManager, BorrowerOperations, StabilityPool (14 contracts total)
- proxies: NONE (all immutable, ownership renounced at setAddresses())
- oracles: PriceFeed (Chainlink ETH/USD + Tellor fallback)
- DEX: none directly; LUSD trades externally on Curve/Uniswap

## Control Plane & Auth
- ALL OWNERSHIP RENOUNCED → no admin, no upgrades, no re-config
- LUSDToken: immutable troveManager/stabilityPool/borrowerOperations addresses
- Bypass: N/A — no proxy, no admin, no upgrade path

## On-Chain State (fork block 21486502)
- 305 active troves, TCR = 672%
- SP: P=1.19e17, epoch=0, scale=0, 30.3M LUSD deposits, 1191 ETH
- L_ETH = 0, L_LUSDDebt = 0 (zero redistributions ever)
- baseRate ≈ 0, 57.6M LQTY staked, lowest trove ICR = 172%

## Fork Test Results (19/19 passed)
### D1-D8: Basic Discriminators
- D1: TCR 672%, healthy state confirmed
- D2: Lowest ICR = 172% (no liquidatable troves)
- D3: Redemption fee has 0.5% hard floor — no below-floor extraction
- D4: P=1.19e17, need ~13M LUSD single liquidation for scale change (impractical)
- D5: Recovery Mode needs 99%+ price drop ($3368→$500)
- D6: 57.6M LQTY staked — fee loss impossible
- D7: Zero redistributions ever — rounding H5 untestable
- D8: No liquidatable troves exist → flash SP attack blocked

### Deep1-6: Advanced Analysis
- Deep1: Price crash to $2054 → only 1 trove liquidatable (25K debt vs 30M SP)
- Deep2: Front-end kickback = UI/social issue, not protocol vuln
- Deep3: Self-redemption always loses 0.5%+ fee — no free ETH
- Deep4: SP LUSD/ETH balance == internal trackers (0 surplus) — rounding precise
- Deep5: Gas comp at $2000: ~$540 total for 2 liquidatable troves (negligible)
- Deep6: Cannot push TCR below 150% via borrowing (check enforced)

### Final1-5: Deep Reasoning Directive Tests
- Final1: 14-step atomic open+deposit+liquidate: NET LOSS ($3672 LUSD lost vs $368 gas comp)
- Final2: baseRate decays to floor 0.5% — cannot go below
- Final3: Preview vs execution consistent (no disagreement)
- Final4: SP snapshot system prevents front-running of ETH gains
- Final5: No exploitable reflexivity — SP emptying → redistribution (no cascade)

## Solvency Equation
`sum(trove.coll) * price >= sum(trove.debt)` — currently 672% overcollateralized

## Assessment
**No E3-qualifying vulnerabilities found.** Liquity V1 demonstrates:
- Mathematically sound P/S/G product-sum system with error correction
- Strict CEI pattern preventing reentrancy across all ETH transfers
- Immutable architecture (no admin keys, no proxies, no upgradeability)
- Self-limiting fee mechanisms (0.5% floor, self-adjusting baseRate)
- BorrowerOperations enforces TCR >= 150% preventing Recovery Mode manipulation
- Chainlink oracle immune to flash loan manipulation
- Rounding consistently favors the pool (never the user)

## Why This Protocol Is Resilient
The key design insight is **radical simplicity + immutability**:
1. No governance, no admin, no upgrades → no privilege escalation surface
2. Single collateral (ETH only) → no token confusion or multi-asset complexity
3. Off-chain oracle (Chainlink) → immune to on-chain manipulation
4. Product-sum math with error correction → O(1) complexity, bounded errors
5. All fees have hard floors → no zero-fee exploitation
6. TCR check on borrowing → cannot be pushed into Recovery Mode
