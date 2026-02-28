# On-Chain Contract Security Analysis: Bridge Protocols

## Analysis Scope
Deep source code review of 4 bridge protocol contracts:
1. Across SpokePool (0x5c7BCd6E7De5423a257D81B442095A1a6ced35C5)
2. Across HubPool (0xc186fA914353c44b2E33eBE05f21846F1048bEda)
3. Across BondToken (ABT)
4. Celer cBridge V2 (0x5427FEFA711Eff984124bfBB1AB6fbf5E3DA1820)
5. Synapse FastBridge (0x5523D3c98809DdDB82C686E152F5C58B1B0fB59E)
6. Hop L1 ETH Bridge (0xb8901acB165ed027E32754E0FFe830802919727f)

---

## Across SpokePool Findings

### Fill Status State Machine: SOUND
- 3-state machine (Unfilled→RequestedSlowFill→Filled) correctly implemented
- No path from Filled back to any other state
- Fast fill can replace slow fill request (FillType.ReplacedSlowFill)
- No partial fills supported (eliminates accounting complexity)

### M1 [Medium]: Speed-Up Signature Replay with unsafeDeposit
- File: across_SpokePool.sol lines 805, 821-904, 643-680
- If unsafeDeposit produces same depositId as prior deposit, speed-up signatures are replayable
- Signature binds to (depositId, originChainId) but NOT to specific relay data
- Acknowledged in NatSpec but real risk for unsafeDeposit users
- Impact: stale updatedRecipient/updatedOutputAmount applied to new deposit

### M2 [Medium]: Fee-on-Transfer Token Accounting Mismatch
- File: across_SpokePool.sol lines 1358-1362 (deposit), 1660-1665 (fill)
- Contract records nominal amounts, not actual received amounts
- Deposits: SpokePool receives less than inputAmount but off-chain records inputAmount
- Fills: recipient receives less than outputAmount
- Mitigated off-chain via route configuration; no on-chain enforcement

### M3 [Medium]: Admin executeExternalCall Grants Arbitrary Call
- File: across_SpokePool.sol lines 381-395
- onlyAdmin gated but allows arbitrary target + calldata (min 4 bytes)
- Admin could approve tokens, call arbitrary contracts
- Trust assumption: HubPool (admin) is honest

### L1 [Low]: Zero-Amount Deposits/Fills Permitted
- No check preventing inputAmount=0 or outputAmount=0
- Creates ghost deposits in event logs; off-chain must validate

### L2 [Low]: amountToReturn Not in Balance Check
- File: across_SpokePool.sol line 1406
- _distributeRelayerRefunds checks totalRefundedAmount <= spokeStartBalance
- Does NOT include amountToReturn in comparison
- Could fail on _bridgeTokensToHubPool if balance insufficient

### L3 [Low]: Inconsistent nonReentrant on speedUpV3Deposit
- speedUpDeposit has nonReentrant, speedUpV3Deposit does not
- Only emits events, so not directly exploitable

### INFO: Reentrancy properly mitigated
- handleV3AcrossMessage callback protected by nonReentrant
- State updated before callback (checks-effects-interactions)
- EIP-7702 delegated wallet detection for native ETH transfers

### INFO: Relay hash collision impossible for safe deposits
- Uses abi.encode (not encodePacked) with all V3RelayData fields + chainId
- Safe deposits use incrementing uint32 counter
- Unsafe deposits use keccak256 of (msgSender, depositor, depositNonce) - no encoding ambiguity

---

## Across HubPool Findings

### DESIGN: No Semantic Validation of Root Bundles On-Chain
- HubPool has ZERO validation of merkle root contents
- Security depends entirely on: (1) ABT whitelist, (2) off-chain disputers, (3) liveness window
- If whitelisted proposer colludes AND disputers fail → full pool drain

### M4 [Medium]: _cancelBundle Uses transfer Instead of safeTransfer
- File: across_HubPool.sol line 855
- Inconsistent with all other bond transfers that use safeTransfer/safeTransferFrom
- If bondToken returns nothing (non-standard), call could silently fail or revert

### M5 [Medium]: BondToken Only Overrides transferFrom, Not transfer
- File: across_BondToken.sol line 73
- Users can send ABT to HubPool via transfer() bypassing whitelist
- Doesn't enable unauthorized proposals (proposeRootBundle uses safeTransferFrom)
- But could affect _sync accounting for that token

### L4 [Low]: haircutReserves Has No Bounds Checking
- File: across_HubPool.sol line 432-436
- Owner can set utilizedReserves to any value, potentially bricking exchange rate
- Owner-only, reversible

### L5 [Low]: delegatecall to Admin-Configured Adapters
- Adapters execute with HubPool storage context
- Malicious adapter = full state corruption
- Admin-only configuration, but adapter is critical trust dependency

### INFO: First Depositor Attack Mitigated
- _sync adjusts both liquidReserves and utilizedReserves by same amount in opposite directions
- Donations cancel out in exchange rate numerator
- Effective defense against classic donation attack

### INFO: disputeRootBundle Does NOT Require Unpaused (Intentional)
- Disputes always possible even when contract paused - correct design

### INFO: multicall Cannot Batch nonReentrant Functions
- Reentrancy guard triggers on first delegatecall, blocks subsequent nonReentrant calls in batch

---

## Celer cBridge V2 Findings

### Signature Verification: SOUND
- Uses OpenZeppelin ECDSA.recover (prevents malleability)
- Ascending order enforcement prevents duplicate signer counting
- Domain separation with chainid + contract address per operation type

### M6 [Medium]: Epoch Boundary Volume Doubling
- File: celer_cbridge_v2.sol lines 1787-1791
- Volume resets at epoch boundaries
- Attacker can extract 2x cap in short window (just before + just after boundary)
- Inherent to epoch-based rate limiting without rolling windows

### M7 [Medium]: Fee-on-Transfer Token Accounting Discrepancy
- File: celer_pool.sol line 53; celer_bridge.sol line 53
- Events emit nominal _amount, not actual received amount
- Off-chain LP system records more than pool actually holds
- Gradual insolvency for last withdrawers

### L6 [Low-Med]: Native Token Receiver Griefing
- File: celer_pool.sol lines 108-113
- Gas limit of 50000 for ETH transfers
- Receiver that always reverts permanently locks delayed transfer liquidity
- No cancel mechanism for delayed transfers

### L7 [Low]: No On-Chain Share Tracking for LP
- addLiquidity records no shares; withdrawal amounts determined by signer quorum
- Full trust in signer set for custody
- DelayedTransfer and VolumeControl provide some mitigation

### INFO: Transfer ID schemes use fixed-width types - no collision risk
### INFO: Governor can disable delays and volume control (centralization risk)
### INFO: receive() allows anyone to send ETH that becomes trapped

---

## Synapse FastBridge Findings

### Overall: Well-Designed
- Proper fee-on-transfer handling via balance diffs in _pullToken
- Clean status machine (NULL→REQUESTED→RELAYER_PROVED→RELAYER_CLAIMED|REFUNDED)
- Replay protection via bridgeStatuses/bridgeRelays mappings

### INFO: relay() Not nonReentrant
- State set before transfers (bridgeRelays[id] = true)
- RELAYER_ROLE gate prevents external exploitation
- Safe in practice

### INFO: params.sender vs msg.sender in bridge()
- Tokens pulled from msg.sender but refund goes to params.sender
- Designed for meta-transactions; not exploitable

---

## Hop L1 ETH Bridge Findings

### Overall: Mature Design
- Proper merkle proof verification for withdrawals
- _addToAmountWithdrawn prevents over-withdrawal (amountWithdrawn <= total)
- _markTransferSpent prevents double-withdrawal
- Challenge mechanism with 1-day challenge + 10-day resolution
- Bonder credit/debit accounting with requirePositiveBalance guard

### INFO: ETH Transfer to Recipient
- Uses recipient.call{value: amount}(new bytes(0)) with no gas limit
- Could enable reentrancy but protected by nonReentrant
- If recipient is contract that reverts, withdrawal permanently fails

### INFO: rescueTransferRoot Governance Only
- Allows governance to withdraw unclaimed funds after RESCUE_DELAY
- Proper design for handling stuck funds

---

## E3 Candidacy Assessment

### NONE of the on-chain findings reach E3 threshold:

1. **Speed-up replay (M1)**: Requires unsafeDeposit usage + prior speed-up signature existence. Acknowledged in code. Impact bounded (redirect to stale recipient).

2. **Fee-on-transfer (M2, M7)**: Requires protocol to accept non-standard tokens. Off-chain mitigation in place. Not a permissionless exploit.

3. **Admin arbitrary call (M3)**: Requires admin compromise. Admin IS the HubPool cross-chain message.

4. **Epoch boundary (M6)**: Bounded by 2x cap. Requires specific timing. Impact proportional to cap size.

5. **No semantic root validation**: Requires proposer whitelist compromise AND disputer failure. Multi-layer defense.

All findings are either:
- Bounded by existing safety mechanisms (volume caps, rate limits, timelocks)
- Gated behind privileged roles (admin, owner, governor, bonder)
- Design trade-offs acknowledged in code/docs
- Off-chain mitigated with no on-chain enforcement gap exploitable permissionlessly
