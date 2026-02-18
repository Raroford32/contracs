# Hypotheses — 1inch Ecosystem Cross-Protocol Audit

## Confirmed (limited impact, not E3)

### H1: curveSwapCallback Drain (CONFIRMED — V6 only, negligible impact)
- **Broken assumption**: curveSwapCallback only called by legitimate Curve pools
- **Reality**: callable by anyone, no access control (V6 line 5601-5609)
- **Impact**: Can drain router balance (0 in practice, 1-wei optimization)
- **E3 status**: NOT E3 — net profit < $0.01
- **Fork evidence**: test_CurveCallbackDrain — 0 tokens drained

### H2: uniswapV3SwapCallback payer==self (CONFIRMED — V6 only, negligible impact)
- **Broken assumption**: uniswapV3SwapCallback validates pool for all transfers
- **Reality**: When payer==address(this), no CREATE2 validation (V6 line 5674)
- **Impact**: Same as H1
- **E3 status**: NOT E3
- **Fork evidence**: Same test — V6 balance is 0

---

## Falsified — Full Evidence

### H3: Multi-hop Intermediate Token Theft
- **Test**: Can fake pool in multi-hop steal intermediate tokens?
- **Result**: Attacker is always the caller → input tokens are attacker's own
- **Status**: FALSIFIED

### H4: Taker Interaction Reentrancy in fillOrder
- **Test**: Can taker reenter to double-fill same order?
- **Result**: Per-order bit invalidator updated BEFORE external calls (CEI)
- **Status**: FALSIFIED

### H5: Assembly Calldata Parsing Overflow
- **Test**: Can crafted calldata cause arithmetic overflow in assembly?
- **Result**: Clean 160-bit masking, V2 k-invariant defense-in-depth, bounded selectors
- **Status**: FALSIFIED

### H6: transferFrom Suffix Exploitation
- **Test**: Can trailing bytes in _callTransferFromWithSuffix exploit exotic tokens?
- **Result**: Standard ERC20 ignores extra calldata; suffix is maker-signed
- **Status**: FALSIFIED

### H7: Cross-Router Approval Exploitation (V3/V4/V5 → V6)
- **Test**: Do older routers have weaker transferFrom security exploitable via stale approvals?
- **Analysis**: V3/V4/V5/V6 ALL use msg.sender or ECDSA-verified maker
- **Evidence**: notes/approval-surface.md
- **Status**: FALSIFIED

### H8: Permit2 Cross-Protocol Allowance Confusion
- **Test**: Can Permit2's shared state surface be exploited across protocols?
- **Result**: Per-spender allowances, always msg.sender or verified maker
- **Status**: FALSIFIED

### H9: IERC1271 Contract Signature Confusion
- **Test**: Can attacker deploy contract validating any hash, create fake orders?
- **Result**: Maker must HOLD tokens AND approve router — attacker trades own tokens
- **Status**: FALSIFIED

### H10: Pre-Interaction State Manipulation → Settlement Exploitation
- **Test**: Can maker's preInteraction callback manipulate state to change fill amounts?
- **Result**: Amounts computed BEFORE preInteraction; CEI correct
- **Status**: FALSIFIED

### H11: Flash Loan → Limit Order Fill → Value Extraction
- **Test**: Flash borrow → fill stale orders → profit?
- **Result**: Normal limit order arbitrage — designed behavior, not an exploit
- **Status**: FALSIFIED

### H12: Callback Chain Amplification (Multi-Protocol)
- **Test**: During multi-hop, drain intermediate tokens via callback?
- **Result**: Attacker IS the caller — steals only own tokens in transit
- **Status**: FALSIFIED

### H14: st1INCH Governance Flash-Stake Attack
- **Test**: Flash borrow 1INCH → stake → governance power → exploit → unstake?
- **Kill points**: 30-day lock, no on-chain governance, non-transferable, off-chain Snapshot, independent owners
- **Status**: FALSIFIED at 5 independent barriers

### H15: Taker Interaction Mid-Swap Cross-Contract Exploit
- **Test**: Can taker callback manipulate state to affect fill amounts?
- **Result**: Amounts fixed before takerInteraction, threshold protection
- **Status**: FALSIFIED

### H16: Mooniswap Sandwich Attack
- **Test**: Front-run + back-run a swap via Mooniswap virtual balance mechanism
- **Fork test**: test_MooniswapSandwich
- **Result**: -18.88 ETH loss on 50 ETH sandwich attempt
- **Why**: Virtual balance mechanism (virtualBalancesForAddition/Removal) creates asymmetric pricing that prevents profitable sandwich
- **Status**: FALSIFIED

### H17: Mooniswap Virtual Balance Decay Exploitation
- **Test**: Swap, wait for full decay (108s), reverse swap at favorable rate
- **Fork test**: test_MooniswapVirtualBalanceState
- **Result**: -33.91 ETH loss on 100 ETH round-trip even after full decay
- **Why**: AMM slippage + 0.3% fee are permanent; virtual balance only protects the spread
- **Status**: FALSIFIED

### H18: OffchainOracle Manipulation → Downstream Impact
- **Test**: Manipulate Mooniswap pool → change oracle rate → exploit predicate-gated orders
- **Fork test**: test_CrossProtocolOraclePredicate, test_OracleAdapterAnalysis
- **Result**: 137 bps WBTC/ETH change from 200 ETH (cost-prohibitive); 0 bps on WETH/USDC
- **Why**: Top 2 WETH adapters via 0xFFFF connector account for 99.9% of oracle weight^2; Mooniswap contributes ~1%
- **Status**: FALSIFIED (cost far exceeds potential exploitation value)

### H19: Mooniswap Donation Attack
- **Test**: Donate ETH/tokens to pool to manipulate virtual balance
- **Fork test**: test_MooniswapDonation
- **Result**: Pool has no receive() for ETH; ERC20 donation doesn't bypass virtual balance math
- **Status**: FALSIFIED

### H20: Mooniswap LP Token Inflation Attack
- **Test**: Manipulate pool state to dilute LP holders via reward minting
- **Fork test**: test_MooniswapLPManipulation
- **Result**: k invariant INCREASES after swap cycle (fees captured correctly)
- **Status**: FALSIFIED

### H21: Mooniswap Referral Extraction
- **Test**: Earn referral rewards by self-referring swaps
- **Fork test**: test_MooniswapReferralExtraction
- **Result**: Zero LP rewards earned from referral
- **Status**: FALSIFIED

### H22: V6 curveSwapCallback Token Drain
- **Test**: Call curveSwapCallback to drain router token balances
- **Fork test**: test_CurveCallbackDrain
- **Result**: V6 router holds 0 balance on all major tokens (WETH, WBTC, USDC, DAI, 1INCH, USDT)
- **Status**: FALSIFIED (0 value to drain)

### H23: st1INCH Early Withdrawal Underflow
- **Test**: Can voting power decay cause `ret > depAmount` in `_earlyWithdrawLoss`?
- **Fork test**: test_St1inchEarlyWithdrawMath
- **Result**: `loss + ret == depAmount` EXACTLY at ALL 10 time points tested
- **Math proof**: `_votingPowerAt(stBalance, t) > depAmount/20` for all `t < unlockTime` (since decay is monotonic and boundary value only reached AT unlockTime)
- **Status**: FALSIFIED

### H24: st1INCH depositFor Griefing
- **Test**: Can attacker extend victim's lock or reduce balance via depositFor?
- **Fork test**: test_St1inchDepositForGriefing
- **Result**: depositFor with duration=0 cannot extend lock; only adds 1INCH to victim's stake
- **Status**: FALSIFIED (only adds value to victim)

### H25: Mooniswap Rounding Accumulation
- **Test**: Can repeated small round-trip swaps accumulate rounding profit?
- **Fork test**: test_MooniswapRoundingLoop
- **Result**: -0.647 ETH over 10x 1 ETH round-trips (~1.5% loss per trip)
- **Why**: 0.3% fee + AMM slippage dominate; rounding is negligible
- **Status**: FALSIFIED

### H26: Cross-Protocol Oracle→Predicate Chain
- **Test**: Manipulate Mooniswap → change OffchainOracle rate → affect limit order predicates
- **Fork test**: test_OraclePredicateChain
- **Result**: 200 ETH Mooniswap manipulation gives 0 bps change on WETH/USDC oracle rate
- **Why**: WETH/USDC doesn't route through Mooniswap at all
- **Status**: FALSIFIED

### H27: Mooniswap First Depositor Attack
- **Test**: Create new pool with skewed initial deposit to extract from subsequent depositors
- **Fork test**: test_MooniswapFirstDepositor
- **Result**: Factory active, no WETH/DAI pool exists, but attacker puts their own value in
- **Why**: No external protocol routes through Mooniswap; no victim deposits expected
- **Status**: FALSIFIED (no victim value to extract)

---

## Additional Vectors Analyzed (not numbered, all FALSIFIED)

### LOP V2 Unwhitelisted Interaction
- V2 has NO interaction whitelist (V3 added one)
- Callback fires between maker→taker and taker→maker transfers
- BUT: interaction target is part of maker's signed order — maker consented
- **Status**: Not attacker-exploitable (maker-controlled)

### FeeBank Credit System
- `gatherFees`: owner collects `accountDeposit - availableCredit`
- `_chargeFee`: checked math prevents underflow
- `decreaseAvailableCredit`: checked subtraction
- `increaseAvailableCredit`: unchecked but supply-bounded
- **Status**: Sound math, no exploitation path

### st1INCH ERC20Pods Silent Failure
- Pods called with 500k gas limit, failures are silent
- ReentrancyGuardExt prevents reentrance during pod callbacks
- Pod failure only affects pod's internal accounting, not st1INCH
- **Status**: No protocol-level harm from pod failures

### VotingPowerCalculator Decay Precision
- 30 immutable lookup table entries for exponential decay via bit manipulation
- Rounding is systematic (truncation), bias is downward in both directions
- Cumulative rounding ~30 wei per operation, negligible vs real values
- **Status**: Mathematically sound, rounding is non-exploitable

### Legacy Router Stuck Value
- V3 Router: ~$881 stuck (263 USDC + 618 USDT)
- V2 Exchange: ~$1,308 stuck (USDT)
- **Status**: Not E3 scale; extraction mechanism unclear for legacy contracts

### Comprehensive Value Scan
- V6 Router: 0 balance (all tokens)
- V5 Router: 1 wei ETH only
- st1INCH: 260M 1INCH (= totalDeposits exactly, surplus = 0)
- All other contracts: empty or dust
- **Status**: No extractable stuck value of significance

---

## Overall Assessment

**27+ hypotheses tested, ALL falsified or confirmed negligible.**

### Key Defenses That Held:
1. **Non-custodial router design**: V6 holds 0 balance → drain attacks yield nothing
2. **Mooniswap virtual balance**: Prevents sandwich attacks at the AMM math level
3. **OffchainOracle weight^2 aggregation**: Mooniswap contributes ~1% of total weight, making manipulation cost-prohibitive
4. **LOP V3 CEI pattern**: Per-order invalidator BEFORE external calls prevents reentrancy double-fill
5. **st1INCH defense-in-depth**: Non-transferable + 30-day lock + ReentrancyGuard + no on-chain governance
6. **Settlement whitelist + extension signing**: Unauthorized resolvers cannot fill Fusion orders
7. **EIP-712 order hashing**: Extension data is maker-signed and immutable

### Why No E3 Was Found:
The 1inch ecosystem was designed with security as a core architecture principle. The non-custodial router pattern eliminates the entire class of "drain router balance" attacks. The limit order protocol uses proper CEI with per-order state management. The st1INCH staking contract has layered defenses that are individually sufficient and collectively redundant. The economic model doesn't create the type of custody mismatches that lead to E3-grade exploits.

### Fork Evidence:
- 24+ fork tests across 3 test files (OneInchEcosystemExploit.t.sol, OracleDeepExploit.t.sol, CrossContractExploit.t.sol)
- All tests PASS (no unexpected reverts)
- Tests cover: Mooniswap AMM mechanics, oracle manipulation, st1INCH staking math, router callback security, cross-protocol oracle chains, comprehensive value scans
