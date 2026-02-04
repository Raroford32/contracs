# Sophisticated Attack Chain Design
## Based on Complete Evidence Collection

---

## REASONING OVER EVIDENCE

### Key Evidence Summary

| Evidence Category | Finding | Attack Relevance |
|------------------|---------|------------------|
| Storage Layout | vaultHwmPps = 1.0, currentPPS = 1.007018 | Unrealized profit exists |
| Storage Layout | performanceFeeBps = 1000 (10%) | Fee skim will extract ~$11.6K |
| Call Semantics | executeHooks allows arbitrary external calls | Fund extraction vector |
| Call Semantics | fulfillRedeemRequests has slippage bounds | Manager extraction vector |
| Oracle Mechanism | PPS is oracle-provided, not calculated | Cannot manipulate via deposits |
| Pendle Integration | SY exchangeRate = SuperVault PPS (instant) | No lag between layers |
| Pendle Integration | AMM liquidity = $832K | Sufficient for instant exit |
| Pendle Integration | PT discount = 1.8% | Cost of instant exit bypass |
| Admin Controls | Hook timelock = 15 minutes | Window for detection |
| Admin Controls | Post-unpause skim lock = 12 hours | Rug prevention mechanism |
| Live State | TVL = $16.7M USDC | High-value target |

### Critical Architectural Insight

```
The SuperVault system has a FUNDAMENTAL DESIGN TENSION:

1. ERC7540 async withdrawals are designed to prevent instant arbitrage
2. BUT the Pendle SY wrapper creates a SECONDARY MARKET
3. The secondary market BYPASSES the async mechanism entirely

This is NOT a bug - it's an architectural consequence of:
- Allowing external protocols to wrap vault shares
- Those wrappers being tradeable on DEXes/AMMs
```

---

## ATTACK CHAIN 1: Fee Skim Front-Running (HIGHEST FEASIBILITY)

### Prerequisites
- Monitoring infrastructure for mempool
- Flash loan access (~$1M USDC)
- Pendle Router integration

### Economic Model

```
Current State:
- totalSupply = 16,590,587 shares
- currentPPS = 1.007018
- vaultHwmPps = 1.000000
- Profit above HWM = 0.7018% = ~$116,432 USDC
- Performance Fee = 10% of profit = ~$11,643 USDC

Fee Skim Impact:
- Fee extracted from TVL = $11,643
- PPS reduction = $11,643 / 16,590,587 shares = ~0.0007 per share
- New PPS after skim ≈ 1.007018 - 0.0007 ≈ 1.006318
- PPS drop percentage = 0.07%

Attack Profitability Check:
- Pendle exit cost = 1.8% PT discount + 0.17% swap = ~2%
- PPS drop from skim = 0.07%
- LOSS = 2% - 0.07% = 1.93%

VERDICT: NOT PROFITABLE at current unrealized profit level
```

### Break-Even Analysis

```
For attack to be profitable:
Fee_Skim_PPS_Drop > Pendle_Exit_Cost

Performance_Fee * Profit_Above_HWM / TVL > 2%
0.10 * Profit_% > 2%
Profit_% > 20%

REQUIREMENT: PPS must be 20%+ above HWM for this attack to work
Current profit: 0.7% - FAR BELOW THRESHOLD
```

### Attack Chain (For Future Reference When Conditions Met)

```
CONDITION: PPS reaches 1.20+ (20% above HWM of 1.0)

BLOCK N-1 (Monitoring):
1. Monitor mempool for skimPerformanceFee() transaction
2. Verify: currentPPS > 1.20

BLOCK N (Attack Execution):
1. Flash loan 1,000,000 USDC from Aave V3
2. Front-run: Deposit USDC to SuperVault
   - Get ~833,333 shares at PPS 1.20
3. Deposit shares to Pendle SY
   - Get ~833,333 SY tokens
4. Swap SY → PT on Pendle AMM
   - Accept 1.8% discount
   - Receive ~817,916 PT tokens

BLOCK N (Fee Skim Executes):
5. skimPerformanceFee() extracts 10% of 20% = 2% of TVL
6. New PPS ≈ 1.20 - 0.024 = 1.176 (2% drop)

BLOCK N+1 to N+X (Recovery):
7. Wait for PPS recovery OR hold PT to maturity
8. Swap PT → SY OR wait for April 30, 2026 maturity
9. Redeem SY for SuperVault shares
10. Repeat async withdrawal process

PROFIT CALCULATION:
- Position preserved from 2% dilution by exiting before skim
- Pendle cost: 1.8% + fees
- Net gain: 2% - 1.8% = 0.2% = $2,000 on $1M position
```

---

## ATTACK CHAIN 2: Manager Fulfillment Extraction (REQUIRES COLLUSION)

### Prerequisites
- Control or collusion with Strategy Manager
- Users with pending redemption requests
- Time for PPS appreciation between request and fulfillment

### Mechanism Deep Dive

```solidity
// From evidence: fulfillment bounds
minAssetsOut = shares * averageRequestPPS * (1 - slippageBps) / PRECISION
theoreticalAssets = shares * currentPPS / PRECISION

// Manager can give ANY amount in [minAssetsOut, theoreticalAssets]
// Difference stays in Strategy contract
```

### Attack Scenario

```
SETUP:
- User requests redeem 1,000,000 shares at PPS = 1.00
- averageRequestPPS = 1.00
- Default slippage = 0.5% (50 bps)

TIME PASSES: PPS rises to 1.10 (10% appreciation)

FULFILLMENT:
- minAssetsOut = 1,000,000 * 1.00 * 0.995 = 995,000 USDC
- theoreticalAssets = 1,000,000 * 1.10 = 1,100,000 USDC

MANAGER GIVES: 995,000 USDC (minimum allowed)
RETAINED IN STRATEGY: 105,000 USDC

EXTRACTION:
- Manager proposes hooks root update with extraction hook
- Wait 15 minutes
- Execute hooks to transfer USDC to external address

PROFIT: 105,000 USDC (10.5% of redemption amount)
```

### Detection Difficulty

```
- Fulfillments within slippage bounds appear LEGITIMATE
- Users receive "acceptable" amounts (within their slippage tolerance)
- Extraction via hooks requires Merkle proof (pre-planned)
- 15-minute timelock provides minimal detection window
```

---

## ATTACK CHAIN 3: Oracle Timing Arbitrage (MEV-STYLE)

### Prerequisites
- PPS oracle transaction monitoring
- Sub-block execution capability (MEV relay)
- Flash loan access

### Oracle Update Flow

```
                    Oracle Backend
                         │
                         │ Detects NAV change
                         ▼
                  ┌──────────────┐
                  │ forwardPPS() │
                  │ transaction  │
                  └──────┬───────┘
                         │
              ┌──────────┼──────────┐
              │   MEMPOOL           │
              │   (observable)      │
              └──────────┬──────────┘
                         │
                    BLOCK N
        ┌────────────────┼────────────────┐
        │                │                │
   Tx Position 1    Tx Position 2    Tx Position 3
   (our front-run)  (oracle update)  (our back-run)
```

### Attack Sequence

```
MONITORING:
1. Watch mempool for forwardPPS(strategy, newPPS)
2. Extract newPPS from calldata
3. Compare: newPPS vs currentPPS

CASE A: newPPS > currentPPS (PPS increasing)
- Front-run with deposit
- Get shares at OLD (lower) PPS
- After oracle update, shares worth more
- Exit via Pendle at NEW (higher) rate

CASE B: newPPS < currentPPS (PPS decreasing)
- Front-run with Pendle exit (sell SY)
- Exit at OLD (higher) rate
- After oracle update, re-enter at lower cost

PROFIT CALCULATION:
- Profit = |newPPS - currentPPS| * position_size / PPS
- Minus: Gas costs, Pendle fees (~2%), MEV relay costs
- Break-even: PPS change > 2.5%
```

### Practical Limitations

```
- PPS changes are typically small (yield accrual: ~0.01-0.05% per update)
- Oracle updates may be batched/infrequent
- MEV competition erodes profits
- Requires sophisticated infrastructure
```

---

## ATTACK CHAIN 4: Cross-Protocol Composability (ADVANCED)

### Concept

```
If SuperVault shares or Pendle SY/PT can be used as COLLATERAL elsewhere:
1. Deposit USDC → Get shares
2. Use shares as collateral → Borrow against them
3. Manipulate collateral value perception → Extract value
4. No need to go through async redemption
```

### Investigation Required

```
CHECK: Does any lending protocol accept:
- SuperVault shares (0xf6ebea08a0dfd44825f67fa9963911c81be2a947)?
- Pendle SY tokens (0x4d654f255d54637112844bd8802b716170904fee)?
- Pendle PT tokens (0x5d99ff7bcd32c432cbc07fbb0a593ef4cc9d019d)?

Protocols to check:
- Aave V3
- Compound V3
- Euler
- Silo Finance
- Morpho
- Pendle's own lending features

If YES → New attack vector opens
If NO → This chain not viable
```

---

## ATTACK CHAIN 5: Yield Source Manipulation (DEEP INFRASTRUCTURE)

### Evidence Gap

```
From storage analysis:
- yieldSourcesList.length = 21
- But we don't know WHERE the $16.7M USDC is deployed

If yield sources include manipulatable protocols:
1. Identify yield source with oracle dependency
2. Manipulate yield source's price oracle
3. Cause SuperVault NAV to misreport
4. Arbitrage the mispricing
```

### Investigation Required

```
NEED: Query strategy.getYieldSourcesList()
NEED: For each yield source, analyze:
  - What protocol is it?
  - What oracle does it use?
  - Can that oracle be manipulated?
  - What's the cost vs. potential profit?
```

---

## SOPHISTICATED COMBINED ATTACK (THEORETICAL MAXIMUM)

### Multi-Phase Attack Design

```
PHASE 1: ACCUMULATION (Days 1-30)
- Accumulate significant SuperVault position ($1M+)
- Monitor PPS appreciation
- Track manager activities (fulfillments, fee skims)

PHASE 2: TIMING OPTIMIZATION (Day 30)
- Wait for conditions:
  a) Large unrealized profit (PPS >> HWM)
  b) Pending redemption requests from other users
  c) Manager preparing fee skim

PHASE 3: COORDINATED EXECUTION (Day 30, Block N)
Transaction Bundle (Atomic):
  1. Flash loan $5M USDC
  2. Deposit to SuperVault (maximize position)
  3. Deposit shares to Pendle SY
  4. Swap SY → PT (lock in exit price)
  5. Let fee skim execute (we're protected)
  6. After skim: Swap PT → SY
  7. Deposit SY shares back to SuperVault (at lower PPS)
  8. Repay flash loan

PHASE 4: PROFIT EXTRACTION (Days 31+)
- Hold new position at lower cost basis
- Wait for next PPS appreciation cycle
- Repeat or exit via Pendle when profitable
```

### Economic Model

```
Assumptions:
- Initial position: $5M
- PPS drop from fee skim: 2% (when profit = 20% above HWM)
- Pendle round-trip cost: 3.6% (2 x 1.8%)

Calculation:
- Without attack: Position drops from $5M to $4.9M (-$100K from skim)
- With attack: Exit before skim, re-enter after
  - Exit cost: $5M * 1.8% = $90K
  - Position value preserved
  - Re-entry at lower PPS: 2% more shares
  - Re-entry value: $5M * 1.02 = $5.1M
  - Net: $5.1M - $90K (exit cost) - $90K (entry cost) = $4.92M

VERDICT: Marginal profit (~$20K on $5M) when fee skim = 2%
         More profitable at higher fee skim levels
```

---

## FEASIBILITY MATRIX

| Attack Chain | Feasibility | Profit | Requirements | Detection Risk |
|-------------|-------------|--------|--------------|----------------|
| Fee Skim Front-Running | LOW (current) | Negative | PPS > HWM by 20%+ | Medium |
| Manager Extraction | HIGH (with collusion) | 5-10% | Manager control | Low |
| Oracle Timing | MEDIUM | 0-2% | MEV infrastructure | Low |
| Cross-Protocol | UNKNOWN | Variable | Collateral acceptance | Medium |
| Yield Source | UNKNOWN | Variable | Vulnerable oracle | High |
| Combined | LOW | Variable | Multiple conditions | High |

---

## CONCLUSIONS

### Current State Assessment

1. **Fee Skim Front-Running**: NOT viable at current 0.7% profit level. Need 20%+ appreciation.

2. **Pendle Bypass**: EXISTS and WORKS, but instant exit cost (~2%) exceeds typical arbitrage opportunities.

3. **Manager Extraction**: VIABLE with collusion. Highest actual exploit potential.

4. **Oracle Timing**: POSSIBLE but requires sophisticated infrastructure and large PPS movements.

### The Fundamental Defense

```
The ERC7540 async withdrawal system DOES protect against most attacks
WHEN the secondary market (Pendle) cost exceeds the arbitrage opportunity.

Current protection level:
- Pendle exit cost: ~2%
- Typical arbitrage opportunity: <0.5%
- Net: System is SECURE against opportunistic attacks

Breaking conditions:
- Fee skim with >20% profit accumulation
- Manager collusion
- Oracle failure/manipulation
- Pendle liquidity crisis
```

### Recommended Monitoring

For protocol defenders:
1. Monitor Pendle market liquidity (attack becomes easier if liquidity increases)
2. Monitor PPS vs HWM spread (attack viable when spread > 20%)
3. Audit manager fulfillment patterns (detect systematic underpayment)
4. Review hook executions (detect extraction attempts)

---

*Attack Chain Design Complete*
*Based on Evidence Collection dated Feb 4, 2026*
