# SuperVault ERC7540 Bypass Analysis
## Intelligent Approaches to Circumvent Async Withdrawal Limitation

**Target**: SuperVault (0xf6ebea08a0dfd44825f67fa9963911c81be2a947) + Pendle SY (0x4d654f255d54637112844bd8802b716170904fee)

---

## Executive Summary

The SuperVault's ERC7540 async withdrawal mechanism can be bypassed through multiple vectors:

| Bypass Vector | Feasibility | Profit Potential | Requirements |
|--------------|-------------|-----------------|--------------|
| Pendle AMM Instant Exit | HIGH | Variable | Pendle market exists |
| Manager Fulfillment Manipulation | HIGH | Up to 10%+ | Manager collusion |
| Hook Execution Extraction | MEDIUM | Unlimited | Manager + 15min timelock |
| Performance Fee Front-Running | MEDIUM | 2-5% | Event monitoring |
| Cross-Layer Oracle Arbitrage | LOW | 0.1-0.5% | Microsecond timing |

---

## Bypass Vector 1: Pendle AMM Instant Exit (PRIMARY BYPASS)

### Discovery

A Pendle market exists for the SuperVault SY token:

```
Market: 0x3d83a85e0b0fe9cc116a4efc61bb29cb29c3cb9a
Expiry: April 30, 2026
Liquidity: $832,060 USD

Tokens:
- SY: 0x4d654f255d54637112844bd8802b716170904fee
- PT: 0x5d99ff7bcd32c432cbc07fbb0a593ef4cc9d019d (1.8% discount)
- YT: 0xb34c5b00c62dc45bfc63d640bf4e80fcf2ececeb
```

### Bypass Mechanism

```
STANDARD PATH (Async):
1. User holds SuperVault shares
2. requestRedeem() → shares locked in escrow
3. Wait for manager to fulfill
4. withdraw() → receive USDC

BYPASS PATH (Instant via Pendle):
1. User holds SuperVault shares
2. Deposit shares to Pendle SY → receive SY tokens
3. Swap SY → PT on Pendle AMM (INSTANT)
4. Either:
   a. Wait until April 30, 2026 → redeem PT for underlying
   b. Sell PT on secondary market

NO ASYNC WAIT REQUIRED!
```

### Economic Analysis

```
Cost of Instant Exit:
- PT Discount: ~1.8% (current market)
- Swap Fee: ~0.17%
- Total Cost: ~2% of position value

When This Is Profitable:
- If expected PPS drop > 2% (e.g., fee skim, market event)
- If liquidity needs justify 2% premium
- If opportunity cost of async wait > 2%
```

### Attack: Fee Skim Front-Running via Pendle

```solidity
// Scenario: Manager about to call skimPerformanceFee()
// Performance fee: 51% of profit above HWM
// Current PPS: 1.10 (10% above HWM of 1.0)

// Before skim:
Profit above HWM = (1.10 - 1.0) * totalSupply = 10% * 16.2M = 1.62M USDC
Fee to extract = 51% * 1.62M = ~826K USDC
PPS reduction = 826K / 16.2M shares = ~5.1%

// Attack sequence:
1. Monitor mempool for skimPerformanceFee() tx
2. Front-run: Exit through Pendle (-2% cost)
3. Fee skim executes: PPS drops 5.1%
4. Re-enter at new lower PPS
5. Net profit: 5.1% - 2% = 3.1% on position
```

---

## Bypass Vector 2: Manager Fulfillment Manipulation

### Vulnerability

The manager controls `totalAssetsOut` for each redemption, bounded only by slippage:

```solidity
// From SuperVaultStrategy.sol:806-808
if (totalAssetsOut < minAssetsOut || totalAssetsOut > theoreticalAssets) {
    revert BOUNDS_EXCEEDED(minAssetsOut, theoreticalAssets, totalAssetsOut);
}
```

### Exploitation Mechanics

```
User Request:
- Shares: 1,000,000
- PPS at request: 1.00
- averageRequestPPS: 1.00

Time Passes... PPS rises to 1.10

Manager Fulfillment:
- minAssetsOut = 1M * 1.00 * (1 - 0.005) = 995,000 USDC
- theoreticalAssets = 1M * 1.10 = 1,100,000 USDC
- Manager gives: 995,000 USDC (minimum)
- Excess retained: 105,000 USDC stays in strategy contract

EXTRACTION: Manager extracts via hooks or waits for performance fee
```

### Economic Impact

For a vault with $16M TVL and 10% price appreciation:
- Potential extraction per cycle: ~$1.6M * 0.5% slippage = ~$80K
- If PPS appreciates 10%: extraction = ~10% * TVL * 0.5% = $800K

---

## Bypass Vector 3: Hook-Based Fund Extraction

### Mechanism

Managers can execute arbitrary hooks with Merkle proof validation:

```solidity
// SuperVaultStrategy.sol:273-296
function executeHooks(ExecuteArgs calldata args) external payable nonReentrant {
    _isManager(msg.sender);
    // ... hooks executed with strategy as caller
    // Strategy holds USDC from underpaid fulfillments
}
```

### Attack Prerequisites

1. Manager proposes strategy hooks root (15-minute timelock)
2. Hooks root includes fund extraction hook
3. Manager waits 15 minutes
4. Manager executes hook to extract accumulated funds

### Mitigation Check

```solidity
// Strategy blocks direct aggregator calls
if (vars.executions[j].target == aggregatorAddr) revert OPERATION_FAILED();
```

But hooks can still:
- Transfer USDC to external addresses
- Interact with DeFi protocols
- Create complex extraction patterns

---

## Bypass Vector 4: Three-Layer Price Arbitrage

### Price Sources

```
Layer 1: SuperVault storedPPS (Oracle-provided)
└─ Updated by authorized PPS Oracles
└─ Can lag real value

Layer 2: Pendle SY exchangeRate
└─ exchangeRate() = SuperVault.convertToAssets(1e18)
└─ Instantly reflects storedPPS changes

Layer 3: Pendle AMM Market Price
└─ Supply/demand driven
└─ May lag exchangeRate changes
```

### Arbitrage Window

```
t=0: Oracle prepares PPS update (1.00 → 1.05)
t=1: Oracle tx submitted to mempool
t=2: Arbitrageur detects oracle tx
t=3: Arbitrageur front-runs with deposit
     - Deposits at old PPS (1.00)
     - Gets 5% more shares
t=4: Oracle tx executes, PPS = 1.05
t=5: Arbitrageur exits through Pendle
     - Pays 2% Pendle fee
     - Net profit: 5% - 2% = 3%
```

### Requirements

- Mempool monitoring infrastructure
- Fast transaction execution
- Sufficient capital to justify gas costs

---

## Bypass Vector 5: Slippage Setting Manipulation

### User Slippage Vulnerability

```solidity
// Users can set their own slippage tolerance
function setRedeemSlippage(uint16 slippageBps) external {
    if (slippageBps > BPS_PRECISION) revert INVALID_REDEEM_SLIPPAGE_BPS();
    superVaultState[msg.sender].redeemSlippageBps = slippageBps;
}
```

### Social Engineering Attack

1. Convince user to set high slippage (e.g., 10%)
2. User requests redeem
3. PPS increases 8%
4. Manager fulfills at -10% slippage
5. User loses 10%, manager retains funds

---

## Bypass Vector 6: Cross-Protocol Composability

### SuperVault Shares as Collateral

If SuperVault shares can be used as collateral in other protocols:

```
1. Deposit USDC → Get SuperVault shares
2. Use shares as collateral → Borrow against them
3. If PPS changes → Manipulate collateral value
4. No need to redeem shares directly
```

### Investigation Needed

- Check Aave, Compound, Euler for SuperVault share support
- Check if Pendle SY/PT can be used as collateral
- Map all protocols that accept these tokens

---

## Complete Bypass Attack: Maximum Extraction

### Combined Attack Sequence

```
PHASE 1: Setup (Day 0)
- Accumulate 1M USDC
- Deposit to SuperVault at PPS = 1.00
- Receive ~1M shares

PHASE 2: Appreciation Period (Days 1-30)
- PPS rises to 1.10 (10% yield)
- Value: 1.1M USDC

PHASE 3: Pre-Skim Detection (Day 30)
- Monitor for skimPerformanceFee() transaction
- Performance fee will extract ~5% of vault

PHASE 4: Instant Pendle Exit (Day 30, Block N)
- Front-run fee skim
- Deposit shares to Pendle SY
- Swap SY → PT on Pendle AMM
- Accept 2% Pendle cost
- Position value: 1.1M * 0.98 = 1.078M USDC equivalent

PHASE 5: Post-Skim Re-Entry (Day 30, Block N+1)
- Fee skim executes: PPS drops to ~1.045
- Swap PT → SY on Pendle (or wait for expiry)
- Re-deposit to SuperVault
- Get more shares at lower PPS

PHASE 6: Repeat
- Wait for next appreciation cycle
- Repeat bypass when fee skim approaches

Net Result:
- Avoided 5.1% dilution from fee skim
- Paid 2% Pendle round-trip cost
- Net saved: 3.1% per cycle
```

---

## Profitability Matrix

| Scenario | Without Bypass | With Pendle Bypass | Net Benefit |
|----------|---------------|-------------------|-------------|
| Fee skim (5% PPS drop) | -5% | -2% | +3% |
| PPS oracle delay (2%) | 0% | +2% - 2% = 0% | 0% |
| Emergency exit need | -X days opportunity | Instant | Time value |
| Manager collusion | -0.5% to -10% | -2% | +3% to +8% |

---

## Recommendations for Protocol

### To Prevent Pendle Bypass
1. Request Pendle to delist or add restrictions to SY wrapper
2. Add transfer restrictions to SuperVault shares
3. Implement velocity limits on deposits after large exits

### To Prevent Manager Exploitation
1. Reduce maximum slippage tolerance
2. Require fulfillment at market price (currentPPS based)
3. Add independent validation of fulfillment amounts

### To Prevent Oracle Front-Running
1. Use commit-reveal scheme for PPS updates
2. Implement TWAP-based PPS
3. Add randomness to update timing

---

## Conclusion

The ERC7540 async withdrawal mechanism provides limited protection when:
1. Secondary markets exist (Pendle)
2. Managers have broad powers
3. Oracle updates are predictable

The Pendle market provides a **complete bypass** of the async withdrawal system at a ~2% cost, making timing-based attacks (fee skim front-running) economically viable for positions where the expected PPS drop exceeds 2%.

---

## Appendix: Contract Addresses

| Contract | Address |
|----------|---------|
| Pendle SY | 0x4d654f255d54637112844bd8802b716170904fee |
| SuperVault | 0xf6ebea08a0dfd44825f67fa9963911c81be2a947 |
| Strategy | 0x41a9eb398518d2487301c61d2b33e4e966a9f1dd |
| Aggregator | 0x10ac0b33e1c4501cf3ec1cb1ae51ebfdbd2d4698 |
| Pendle Market | 0x3d83a85e0b0fe9cc116a4efc61bb29cb29c3cb9a |
| PT Token | 0x5d99ff7bcd32c432cbc07fbb0a593ef4cc9d019d |
| YT Token | 0xb34c5b00c62dc45bfc63d640bf4e80fcf2ececeb |

---

*Analysis Date: February 4, 2026*
