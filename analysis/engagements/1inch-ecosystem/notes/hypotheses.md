# Hypotheses — 1inch Ecosystem Cross-Protocol Audit

## Confirmed (limited impact, not E3)

### H1: curveSwapCallback Drain (CONFIRMED — V6 only, negligible impact)
- **Broken assumption**: curveSwapCallback only called by legitimate Curve pools
- **Reality**: callable by anyone, no access control (V6 line 5601-5609)
- **Impact**: Can drain router balance (0 in practice, 1-wei optimization)
- **E3 status**: NOT E3 — net profit < $0.01

### H2: uniswapV3SwapCallback payer==self (CONFIRMED — V6 only, negligible impact)
- **Broken assumption**: uniswapV3SwapCallback validates pool for all transfers
- **Reality**: When payer==address(this), no CREATE2 validation (V6 line 5674)
- **Impact**: Same as H1
- **E3 status**: NOT E3

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
- **Analysis**:
  - V3: Only `srcToken.safeTransferFrom(msg.sender, ...)` — always msg.sender
  - V4: All transferFrom sites use msg.sender or ECDSA-verified maker; CREATE2 always validates V3 callbacks; no curveSwapCallback; `destroy()` is owner-only
  - V5: 11 transferFrom sites audited — all use msg.sender, address(this), or ECDSA-verified maker; `simulate()` delegatecall always reverts; no curveSwapCallback; CREATE2 always validates
- **Evidence**: notes/approval-surface.md (V5 complete inventory)
- **Status**: FALSIFIED — all routers enforce `from == msg.sender || from == ECDSA_verified_maker`

### H8: Permit2 Cross-Protocol Allowance Confusion
- **Test**: Can Permit2's shared state surface be exploited across protocols?
- **Analysis**:
  - All Permit2 transfers in V6 use `from=msg.sender` or `from=order.maker` (ECDSA-verified)
  - Permit2 allowance model is per-spender (router address), not shared across protocols
  - No path to invoke Permit2.transferFrom with unexpected `from` parameter
- **Status**: FALSIFIED

### H9: IERC1271 Contract Signature Confusion
- **Test**: Can attacker deploy malicious IERC1271 contract that validates any hash, then create "fake" orders to drain funds?
- **Analysis**:
  - Yes, can deploy contract returning magic value for any hash
  - BUT: maker-to-taker transfer uses transferFrom(maker_contract, receiver, amount)
  - Maker contract must HOLD tokens AND have granted router allowance
  - Attacker trades their own tokens against themselves — no third-party drain
  - fillContractOrder only checks ERC-1271 on first fill (optimization, safe because orderHash is deterministic)
- **Status**: FALSIFIED — security boundary is ERC20 transferFrom, not signature validation

### H10: Pre-Interaction State Manipulation → Settlement Exploitation
- **Test**: Can maker's preInteraction callback manipulate state to change fill amounts?
- **Analysis of V6 _fill sequence**:
  1. Amount computation via staticcall getters (step 6)
  2. Order invalidation — STATE WRITE (step 9)
  3. preInteraction — EXTERNAL CALL (step 10)
  4. Maker transfer (step 11)
  - Amounts are local variables computed BEFORE preInteraction fires
  - preInteraction cannot retroactively change amounts
  - CEI pattern correctly applied: invalidation before external calls
- **Status**: FALSIFIED — amounts fixed before any non-staticcall external call

### H11: Flash Loan → Limit Order Fill → Value Extraction
- **Test**: Can attacker flash borrow takerAsset, fill stale limit orders, sell makerAsset for profit?
- **Analysis**:
  - This describes NORMAL limit order arbitrage — the designed behavior
  - takerInteraction callback explicitly supports on-the-fly liquidity sourcing
  - Makers accept the rate when they sign orders; stale pricing is maker risk
  - Protection exists: allowedSender (resolver priority), predicates, expiration, epochs
  - Competitive MEV landscape fills mispriced orders within blocks
- **Status**: FALSIFIED (not an exploit — it's designed protocol behavior)

### H12: Callback Chain Amplification (Multi-Protocol)
- **Test**: During multi-hop V6 swap through Curve, can attacker drain intermediate tokens held by router?
- **Analysis**:
  - Curve path: router temporarily holds tokens (addressForPreTransfer returns address(this))
  - BUT: the attacker IS the caller — intermediate tokens are attacker's own tokens in transit
  - Calling curveSwapCallback during the callback window steals attacker's own tokens
  - Non-custodial design prevents amplification
- **Status**: FALSIFIED — attacker can only steal their own tokens

### H14: st1INCH Governance Flash-Stake Attack
- **Test**: Can attacker flash-borrow 1INCH → stake → gain governance power → change parameters → exploit → unstake?
- **Five independent kill points**:
  1. **30-day minimum lock period** — flash loans require same-tx repayment
  2. **No on-chain governance execution** — votingPowerOf() is view-only, no propose/vote/execute
  3. **Voting power not connected to any parameter** — router owner, oracle owner, st1INCH owner are independent addresses
  4. **st1INCH tokens non-transferable** — transfer() and transferFrom() always revert
  5. **Off-chain governance (Snapshot) + multisig execution** — cannot be atomically exploited
- **Status**: FALSIFIED at 5 independent barriers

### H15: Taker Interaction Mid-Swap Cross-Contract Exploit
- **Test**: Can taker's interaction callback manipulate state to affect the fill's taker payment?
- **Analysis**:
  - takerInteraction fires AFTER amounts are computed and fixed as local variables
  - takingAmount pulled via transferFrom(msg.sender, ...) uses the pre-computed amount
  - Taker has threshold protection in takerTraits
  - Cross-order manipulation possible but each order has independent threshold
- **Status**: FALSIFIED — amounts fixed before takerInteraction, threshold protection

---

## Backlog (investigated — low priority)

### Approval Drain via Any Path
- **Analysis**: Exhaustive audit across V3/V4/V5/V6 (40+ transferFrom sites total)
- **Result**: `from` is always `msg.sender` or ECDSA/ERC-1271 verified maker
- **Status**: FALSIFIED across entire ecosystem

### Unknown $98M Contract (0x111cff45...)
- **Identified as**: Gnosis MultiSigWallet (3-of-3), cold storage treasury
- **Owners**: 3 EOAs, all operations require 3-of-3 confirmation
- **Status**: NOT exploitable — standard Gnosis multisig, no external vulnerability surface
- **Evidence**: notes/unknown-98m-contract.md

---

## Overall Assessment

The 1inch ecosystem has been comprehensively audited across all major contract interactions:

**Router Security (V3-V6)**: All four router versions enforce the same core invariant — `transferFrom` always uses `msg.sender` or cryptographically verified maker addresses. No cross-router approval drain is possible. V5/V4 are actually MORE secure than V6 for callbacks (always CREATE2 validate, no curveSwapCallback).

**Order Fill Chain**: The V6 limit order system follows a correct CEI pattern with 5 external call windows (predicate staticcall, preInteraction, maker transfer, takerInteraction, postInteraction). Amounts are computed before mutable external calls. Each order is independently invalidated before callbacks.

**Governance**: st1INCH has no on-chain governance execution capability. Voting power is view-only. Flash-staking is impossible (30-day minimum lock). Tokens are non-transferable.

**Cross-Protocol**: Permit2 allowances are per-spender, preventing cross-protocol confusion. External DEX pools enforce their own invariants.

**No E3-grade vulnerability found across the entire 1inch ecosystem.**
