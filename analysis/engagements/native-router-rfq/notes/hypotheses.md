# Hypotheses — Pendle Boros RFQ

## Active set

### H1 — Soft agent expiry persists post-natural-expiry on-chain (Design risk)
- **Broken assumption (A1)**: "expired agent ⇒ can no longer sign valid OTC sigs on-chain"
- **Reasoning chain**:
  1. `_approveAgent(acc, agent, expiry)` sets `agentExpiry[acc][agent] = expiry`. expiry is a timestamp.
  2. After block.timestamp passes that expiry, the storage value remains `expiry > 0` (no auto-clear).
  3. `_revokeAgent` is the only path that zeroes it (`delete agentExpiry[acc][agent]`).
  4. `_verifyAgentSoft` checks `agentExpiry > 0`, NOT `agentExpiry > block.timestamp`.
  5. Therefore a naturally-expired agent's signature passes the on-chain agent gate.
  6. The off-chain validator's co-signature is then the only barrier.
- **Value extraction trace**: zero direct extraction without (a) leaked agent key + (b) malicious/compromised validator. With both, attacker can execute arbitrary OTC trades against the user.
- **Discriminator**:
  1. RPC view: `agentExpiry(account, agent) → uint256`. Find any (account, agent) pair where returned value < block.timestamp but > 0.
  2. Tenderly sim: build a minimal `executeOTCTrade(req)` where `makerData.agent = X` (X has expired-but-unrevoked authority), with synthetic validator → confirm only the validator co-sig matters.
- **Status**: code-confirmed. Cannot fork-test without RPC. Not a permissionless exploit. **DOCUMENTED BY THE PROTOCOL** (comment: "Loose agent check (expiry > 0, not block.timestamp). Only for messages that are verified by an off-chain validator at signing time.").
- **Severity**: Low (relies on validator integrity).

### H2 — Single OTC validator address is a centralization SPOF
- **Broken assumption (A2)**: "validator co-signature provides robust consensus"
- **Reasoning chain**:
  1. `_OMS().validator` is a single address.
  2. `setOTCTradeValidator` is `onlyAuthorized` (admin role).
  3. If validator's key/key-custody is compromised: attacker forges all execMsgs.
  4. Attacker can then craft `executeOTCTrade(req)` with synthesized makerData/takerData (using any known leaked or expired-but-unrevoked agent keys per H1) + forged validator sig.
  5. On-chain check passes; trade executes.
- **Value extraction**: bounded by victims' positionable margin and market liquidity.
- **Discriminator**: not fork-grounded — operational/key-custody investigation.
- **Severity**: Medium-High (operational).

### H3 — Free option for relayer/validator within signature expiry window
- **Reasoning chain**: Maker signs at T0 with expiry T0+Δ. Between T0 and execution, market moves. Relayer chooses to execute or not based on which side wins.
- **Value extraction**: bounded by market vol × expiry window. Standard MEV/RFQ tradeoff.
- **Severity**: Inherent.

## Backlog (not actively pursued)

### B1 — `maker == taker` self-OTC
- No explicit check that maker and taker addresses differ. Likely blocks at `IMarket.orderAndOtc` margin layer. Not pursued; low priority.

### B2 — Deferred-modules audit (AMM_MODULE, CONDITIONAL_MODULE, DEPOSIT_MODULE, MISC_MODULE)
- Not yet bundled. The conditional-order flow is likely structurally similar to OTC (place + execute with off-chain validator). Same trust assumptions.
- Recommendation: bundle and skim if engagement continues.

### B3 — TransparentProxy admin upgrade as exploit chain
- Out of permissionless scope. Recorded for completeness.

### B4 — `_checkAgentAllowedToCall` whitelist gaps
- `payTreasury` is in the agent whitelist — a malicious agent can drain user's cash by paying treasury. Recorded; user-trust attack only.

## Unvalidated hypotheses (failed at code-read level)

```
HYPOTHESIS: EIP-712 type encoding mismatch between primary and nested struct (AcceptOTCFullMessage / OTCTradeReq)
BROKEN ASSUMPTION (hypothesized): incorrect alphabetical ordering of nested type definitions
REASONING CHAIN: EIP-712 spec requires nested types appended in alphabetical order; if the contract concatenates wrong order, attacker can reuse signatures across distinct primary types.
FAILED BECAUSE: _ACCEPT_OTC_FULL_MESSAGE definition is "AcceptOTCFullMessage(...)OTCTradeReq(...)" — primary type first, single nested type second. Correct.
EVIDENCE: SigningBase.sol L168-183.
INSIGHT: Pendle's EIP-712 layout is canonical.
```

```
HYPOTHESIS: ECDSA-first SignatureChecker fork allows malicious smart-contract signers to bypass via crafted ECDSA preimage
BROKEN ASSUMPTION: ECDSA recovery for a contract address would never succeed (so the fallback to ERC-1271 is the only valid path)
REASONING CHAIN: SignatureChecker.isValidSignatureNow tries ECDSA first; if it succeeds with recovered == signer, returns true. For a smart-contract signer, the recovered address would have to equal the contract's address — possible only if attacker found r,s,v hashing to that exact 20-byte address.
FAILED BECAUSE: 2^-160 search space — practically infeasible.
INSIGHT: The fork is safe; "ECDSA-first" benefits EIP-7702 EOAs without compromising contract-only signers.
```

```
HYPOTHESIS: Validator's signature replayable across OTC trades because it lacks a nonce
BROKEN ASSUMPTION: tradeHash replay protection covers validator-side replay
REASONING CHAIN: validator signs (makerHash, takerHash, expiry). If attacker bundles different trade body but reuses (makerHash, takerHash), they could replay validator sig.
FAILED BECAUSE: makerHash and takerHash each commit to the trade body (via _hashOTCTradeReq nested in AcceptOTCFullMessage). Different trade body ⇒ different inner hashes ⇒ different validator-signed message.
INSIGHT: Replay key chain is closed.
```

```
HYPOTHESIS: cross/marketId encoding in MarketAcc allows collision between (cross=true) and a market with id == MarketIdLib.CROSS
BROKEN ASSUMPTION: distinct (cross, marketId) inputs always produce distinct MarketAccs
REASONING CHAIN: cross=true sets marketId field to MarketIdLib.CROSS (0xFFFFFF). cross=false uses given marketId. If given marketId == 0xFFFFFF, they collide.
FAILED BECAUSE: MarketId is uint24; CROSS = type(uint24).max. The MarketFactory presumably reserves this value (cannot deploy a market with marketId=CROSS) — but I haven't confirmed by reading MarketFactory.
INSIGHT: If MarketFactory does NOT reject CROSS marketId, this is a valid concern. Recorded for follow-up.
```

## Conclusion
No E3 finding from static analysis. Code is well-engineered. The most concerning observation (H1) is documented-as-intentional behavior with the off-chain validator as the actual security boundary. To meaningfully advance, the engagement needs:
- A working RPC for fork-grounded experiments
- The Conditional/Deposit/AMM/Misc module sources
- An adversary model that includes operational compromise (validator/relayer/admin)
