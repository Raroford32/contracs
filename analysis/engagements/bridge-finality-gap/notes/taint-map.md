# Taint Map: Bridge Finality Gap

## Critical External Callsites

### Across SpokePool — _transferTokensToRecipient (SpokePool.sol:1644)

**Callsite 1: Native token unwrap + send**
- where: `_unwrapwrappedNativeTokenTo(payable(recipientToSend), amountToSend)` (line ~1661)
- target source: recipientToSend derived from relayData.recipient (caller-controlled for fast fill; depositor-controlled for slow fill)
- calldata source: amount from relayData.outputAmount / updatedOutputAmount
- value source: amountToSend (from relay data)
- safety checks: fillStatus must be Unfilled; fillDeadline not expired; relayHash uniqueness
- discriminator needed: Can a phantom deposit hash pass all checks?

**Callsite 2: ERC20 transfer (slow fill path)**
- where: `IERC20Upgradeable(outputToken).safeTransfer(recipientToSend, amountToSend)` (line ~1666)
- target source: outputToken from relayData (depositor-controlled)
- value source: amountToSend from slow fill leaf
- safety checks: merkle proof against admin-posted root; fillStatus check
- discriminator needed: Can dataworker be tricked into including phantom slow fill leaf?

**Callsite 3: AcrossMessageHandler callback**
- where: `AcrossMessageHandler(recipientToSend).handleV3AcrossMessage(...)` (line ~1671)
- target source: recipientToSend (depositor/relayData controlled)
- calldata source: updatedMessage (depositor-controlled via EIP712 signed update)
- safety checks: only called if message.length > 0 && recipientToSend.isContract()
- discriminator needed: Can attacker use message handler callback for reentrancy? (reentrancy guard present)

### Across SpokePool — executeExternalCall (SpokePool.sol:381)
- where: `target.call(data)` inside executeExternalCall
- target source: admin-controlled (decoded from message parameter)
- gating: onlyAdmin (cross-domain admin)
- safety checks: target != address(0), data.length >= 4
- risk: LOW (admin-only)

### Metis L1 Bridge — finalizeETHWithdrawal
- where: `_to.call{value: _amount}(new bytes(0))`
- target source: _to from cross-domain message (L2 bridge relays user's address)
- value source: _amount from cross-domain message
- safety checks: onlyFromCrossDomainAccount(l2TokenBridge)
- discriminator needed: Can cross-domain messenger be fed unfinalized messages?

## User-Controlled Input → Fund Release Paths

### Path 1: Fast Fill (Low systemic risk — relayer pays)
```
User controls: relayData params (depositor, recipient, amounts, tokens, depositId, etc.)
Relayer controls: msg.sender, repaymentChainId, repaymentAddress
Flow: fillRelay(relayData, ...) → _fillRelayV3 → safeTransferFrom(msg.sender, ...)
Risk: Relayer pays own tokens. If deposit is phantom, relayer loses.
```

### Path 2: Slow Fill (HIGH systemic risk — pool pays)
```
User controls: relayData params (same as above)
Anyone can call: requestSlowFill(relayData) → emits RequestedSlowFill event
Dataworker: reads event, validates deposit, includes in merkle root
Admin: relayRootBundle(refundRoot, slowRelayRoot) → stores roots
Anyone can call: executeSlowRelayLeaf(leaf, rootBundleId, proof) → SpokePool.safeTransfer
Risk: If phantom deposit is included in root, pool pays for non-existent deposit.
```

### Path 3: Cross-Domain Bridge (Metis)
```
Messenger controls: msg.sender must be messenger
Messenger relays: xDomainMessageSender must be l2TokenBridge
Flow: finalizeETHWithdrawal → _to.call{value: _amount}
Risk: If messenger relays unfinalized message, bridge pays for phantom withdrawal.
```
