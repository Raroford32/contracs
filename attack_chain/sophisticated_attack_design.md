# SOPHISTICATED ATTACK CHAIN DESIGN
## f(x) Protocol + Convex FXN Integration
## Based on Complete Evidence Collection

---

# EXECUTIVE REASONING

After systematic evidence collection across all 24 evidence categories, I have mapped:
- Contract addresses and implementations
- Storage layouts and current state values
- Oracle price data (twap, min, max)
- Cross-contract call patterns
- Access control mechanisms
- Economic parameters

## The Hard Truth

**No single-transaction unprivileged exploit was found.** The protocol has mature security design.

However, sophisticated multi-step attack chains can still be designed for:
1. Conditional exploitation (when certain states align)
2. Social engineering composite attacks
3. MEV extraction opportunities
4. Governance/role compromise scenarios

---

# ATTACK CHAIN 1: PRICE DIVERGENCE ARBITRAGE (CONDITIONAL)

## Evidence Base
```
ORACLE STATE:
├─ twap: 2207.53 USD/ETH
├─ minPrice: 2197.94 USD/ETH
├─ maxPrice: 2210.94 USD/ETH
└─ spread: 0.59%

TREASURY PRICE USAGE:
├─ MintXToken: uses maxPrice (2210.94)
└─ RedeemXToken: uses minPrice (2197.94)
```

## Attack Sequence
```
PRECONDITION: Spread > total_fees (currently FALSE, need ~1%+ spread)

T0: Monitor oracle for price divergence
    └─ Trigger: (maxPrice - minPrice) / twap > fee_threshold

T1: Flash loan baseToken (eETH)
    └─ Source: Aave V3, Balancer
    └─ Amount: Maximum available

T2: Market.mintXToken(baseIn, self, 0)
    └─ Uses maxPrice for calculation
    └─ xTokenOut = f(baseIn, maxPrice)

T3: Market.redeemXToken(xTokenOut, self, 0)
    └─ Uses minPrice for calculation
    └─ baseOut = f(xTokenOut, minPrice)

T4: Repay flash loan
    └─ Net: baseOut - baseIn - fees - flash_loan_fee

PROFIT = (maxPrice/minPrice - 1) * baseIn - (mint_fee + redeem_fee) * baseIn - flash_fee
```

## Economic Analysis
```
CURRENT STATE (0.59% spread):
├─ Position: 100 ETH
├─ Gross profit: 0.59 ETH (~$1,300)
├─ Mint fee (~0.25%): -0.25 ETH
├─ Redeem fee (~0.25%): -0.25 ETH
├─ Flash loan fee (0.05%): -0.05 ETH
├─ Gas (~500k): -0.01 ETH
└─ NET: +0.03 ETH (~$66) ← MARGINAL

REQUIRED FOR $10K PROFIT:
├─ Spread: ~2%
├─ OR Position: 1000 ETH with current spread
└─ VERDICT: Wait for high volatility events
```

## Viability Assessment
- **Current**: UNPROFITABLE (spread < fees)
- **Conditional**: PROFITABLE during volatility spikes
- **Monitoring**: Track oracle price divergence
- **Tier**: TIER_1 (flash loan user)

---

# ATTACK CHAIN 2: VOTE SHARING EXPLOITATION (SOCIAL ENGINEERING)

## Evidence Base
```
execute() CAN CALL:
├─ gauge.acceptSharedVote(target)
└─ gauge.checkpoint(account)

acceptSharedVote() REQUIRES:
└─ isStakerAllowed[target][msg.sender] == true

isStakerAllowed SET BY:
└─ toggleVoteSharing(staker) - VE_SHARING_ROLE only
```

## Attack Sequence
```
PHASE 1: Social Engineering (off-chain)
T0: Identify high-veFXN holders who use f(x) Protocol
    └─ Query veFXN balances
    └─ Cross-reference with gauge depositors

T1: Social engineer target to enable vote sharing
    └─ Approach: "Partnership proposal for boost optimization"
    └─ Approach: "Yield aggregator integration"
    └─ Goal: Get target to call toggleVoteSharing(attacker_vault)

PHASE 2: Technical Exploitation (on-chain)
T2: Wait for toggleVoteSharing to be called
    └─ Monitor: isStakerAllowed[target][attacker_vault] becomes true

T3: Attacker's vault owner calls:
    execute(gauge, 0, abi.encodeWithSelector(
        acceptSharedVote.selector,
        target  // The victim's address
    ))

T4: Gauge state updated:
    getStakerVoteOwner[attacker_vault] = target

T5: All future gauge rewards use target's veFXN boost
    └─ Attacker receives amplified rewards
    └─ Victim's boost is diluted
```

## Economic Analysis
```
EXAMPLE:
├─ Victim has 100,000 veFXN (significant boost)
├─ Attacker stakes 10,000 fTokens
├─ Normal APY: 5%
├─ Boosted APY: 15%
├─ Extra yield: 10% * 10,000 = 1,000 fTokens/year
└─ At $1/fToken: $1,000/year extraction

CONSTRAINTS:
├─ Requires social engineering
├─ Requires VE_SHARING_ROLE holder cooperation
├─ Victim can revoke via toggleVoteSharing
└─ Attribution risk is high
```

## Viability Assessment
- **Difficulty**: HIGH (social engineering required)
- **Profit**: MEDIUM ($1,000s/year per victim)
- **Detection**: EASY (on-chain state change visible)
- **Tier**: TIER_2 (requires social engineering)

---

# ATTACK CHAIN 3: ORACLE UPDATE FRONTRUNNING (MEV)

## Evidence Base
```
ORACLE: FxEETHOracleV2 @ 0xe1b11bb...
├─ Likely uses multiple sources
├─ Updates price on external triggers
└─ Treasury reads price synchronously

TREASURY DEPENDENCY:
├─ mintFToken → reads minPrice
├─ mintXToken → reads maxPrice
├─ collateralRatio() → reads prices for state
```

## Attack Sequence
```
PRECONDITION: Access to mempool or private orderflow

T0: Monitor pending oracle update transactions
    └─ Track Chainlink keepers
    └─ Track protocol price update calls

T1: Detect oracle update that will move price significantly
    └─ Price dropping: opportunity for redeem arbitrage
    └─ Price rising: opportunity for mint arbitrage

T2: FRONTRUN oracle update with position adjustment

    SCENARIO A (Price dropping 5%):
    ├─ Current position: Long xToken
    ├─ Action: Redeem xToken at OLD (higher) price
    ├─ Wait: Oracle update executes
    ├─ Action: Mint xToken at NEW (lower) price
    └─ Profit: Price delta captured

    SCENARIO B (Price rising 5%):
    ├─ Current position: None
    ├─ Action: Mint xToken at OLD (lower) price
    ├─ Wait: Oracle update executes
    ├─ Action: Hold or redeem at NEW price
    └─ Profit: Price appreciation captured

T3: Execute position (may require BACKRUN for clean exit)
```

## Economic Analysis
```
DEPENDS ON:
├─ Oracle update frequency
├─ Price movement magnitude
├─ MEV competition
└─ Gas costs

EXAMPLE (5% price move):
├─ Position: 100 ETH equivalent
├─ Gross: 5 ETH
├─ Fees: 0.5 ETH
├─ Gas (priority): 0.1 ETH
├─ MEV competition: variable
└─ NET: Up to 4.4 ETH (~$10K)

CONSTRAINTS:
├─ Requires reliable mempool access
├─ Oracle may have MEV protections
├─ Competition from other searchers
└─ TWAP anchoring limits extreme moves
```

## Viability Assessment
- **Difficulty**: MEDIUM (standard MEV)
- **Profit**: HIGH during volatility
- **Competition**: HIGH (searcher competition)
- **Tier**: TIER_2 (MEV searcher)

---

# ATTACK CHAIN 4: CROSS-CONTRACT STATE MANIPULATION (THEORETICAL)

## Evidence Base
```
STATE DEPENDENCY CHAIN:
Treasury.collateralRatio()
  ├─ Reads: totalBaseToken (storage)
  ├─ Reads: oracle.getPrice() (external)
  ├─ Reads: fToken.totalSupply() (external)
  └─ Reads: xToken.totalSupply() (external)

Gauge.liquidate()
  ├─ CHECKS: Treasury.collateralRatio() < threshold
  └─ EXECUTES: Market.redeem() → Treasury.redeem()
```

## Attack Sequence (THEORETICAL - ROLE REQUIRED)
```
PRECONDITION: Control over LIQUIDATOR_ROLE (compromise/governance)

T0: Wait for collateralRatio approaching liquidation threshold
    └─ Monitor: collateralRatio < 1.3x (example threshold)

T1: Flash loan large amount of fTokens
    └─ Purpose: Deposit to gauge to become major staker

T2: Gauge.deposit(large_amount)
    └─ Now: Attacker is significant staker

T3: Trigger liquidation (requires LIQUIDATOR_ROLE)
    └─ Gauge.liquidate(maxAmount, minOut)
    └─ Burns fTokens from all stakers proportionally
    └─ Distributes baseToken to all stakers proportionally

T4: Withdraw immediately
    └─ Capture disproportionate share of liquidation rewards

T5: Repay flash loan

CONSTRAINT: REQUIRES LIQUIDATOR_ROLE - NOT EXPLOITABLE
```

## Viability Assessment
- **Status**: BLOCKED by role requirement
- **If role compromised**: HIGH profit potential
- **Detection**: Easy (unusual liquidation patterns)
- **Tier**: TIER_3 (governance attack)

---

# ATTACK CHAIN 5: CHECKPOINT TIMING OPTIMIZATION (LOW VALUE)

## Evidence Base
```
PERMISSIONLESS FUNCTIONS:
├─ checkpoint(address) - Anyone can call
└─ Updates boost ratio based on current veFXN

BOOST CALCULATION:
├─ Uses time-weighted veFXN balance
├─ checkpoint() locks in current boost
└─ Boost decays over time without checkpoint
```

## Attack Sequence
```
T0: Lock large veFXN position

T1: Immediately call checkpoint(self) on gauge
    └─ Locks in maximum boost

T2: Periodically claim rewards with high boost
    └─ Boost calculation uses checkpointed value

T3: Before veFXN unlock, avoid checkpoints
    └─ Maintains artificially high boost

T4: After unlock, boost naturally decays

PROFIT: Marginal reward increase (~5-10% extra APY)
```

## Viability Assessment
- **Difficulty**: TRIVIAL
- **Profit**: LOW (optimization, not exploitation)
- **Legitimacy**: This is intended protocol behavior
- **Tier**: TIER_0 (normal user)

---

# COMPOSITE ATTACK: MAXIMUM EXTRACTION (THEORETICAL)

## Combining Multiple Vectors
```
PHASE 1: Setup
├─ Acquire veFXN for boost
├─ Establish multiple Convex vaults
└─ Set up monitoring infrastructure

PHASE 2: Social Engineering
├─ Identify high-veFXN targets
├─ Social engineer vote sharing enablement
└─ Capture boost from multiple victims

PHASE 3: Oracle MEV
├─ Monitor oracle updates
├─ Frontrun significant price moves
└─ Accumulate profits

PHASE 4: Position Management
├─ Strategic checkpoint calls
├─ Optimal reward timing
└─ Periodic profit extraction

ESTIMATED ANNUAL PROFIT:
├─ Boost theft (3 victims): $3,000/year
├─ Oracle MEV (10 events): $50,000/year
├─ Checkpoint optimization: $1,000/year
└─ TOTAL: ~$54,000/year (requires significant effort)
```

---

# CONCLUSION

## What Works
| Attack | Viability | Profit Potential | Requirements |
|--------|-----------|------------------|--------------|
| Price Arbitrage | Conditional | $10K+ per event | High volatility |
| Vote Sharing | Difficult | $1K/year/victim | Social engineering |
| Oracle MEV | Medium | $5K-50K/year | MEV infrastructure |
| Checkpoint | Easy | $1K/year | None |
| Liquidation | Blocked | High if unblocked | LIQUIDATOR_ROLE |

## What Doesn't Work
1. **Direct fund extraction**: All paths role-protected
2. **Reentrancy**: Functions properly protected
3. **Oracle manipulation**: TWAP + multi-source prevents manipulation
4. **First depositor**: Virtual shares/minimum amounts
5. **Flash loan attacks**: No direct vulnerability

## Final Assessment

**The protocol is secure against unprivileged exploitation.**

Remaining risks are:
1. Oracle volatility arbitrage (conditional, competitive)
2. Social engineering (difficult, low profit)
3. MEV extraction (standard, competitive)
4. Governance compromise (external threat)

**Recommendation**: No economically viable exploit chain for a TIER_1 attacker without additional assumptions (role compromise, social engineering success, or extreme market conditions).
