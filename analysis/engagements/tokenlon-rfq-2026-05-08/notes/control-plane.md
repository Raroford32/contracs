# Control plane / auth-bypass map

## Auth gates (live)

| Surface | Gate | State location | Writers | Reachable to attacker? |
|---|---|---|---|---|
| `UserProxy.toRFQ/toRFQv2/toPMM/toAMM/toLimitOrder` | `tx.origin == msg.sender` (EOA only) + `is*Enabled` | UserProxyStorage | operator | YES from any EOA — by design |
| `RFQ.fill / RFQv2.fillRFQ / PMM.fill / LimitOrder.fill* / AMMWrapper.trade` | `onlyUserProxy` | immutable | none | indirectly via UserProxy |
| `Spender.spendFromUser/spendFromUserTo` | `authorized[msg.sender] == true` | Spender storage | operator (timelocked) | NO — only the 5 Tokenlon strategies |
| `AllowanceTarget.executeCall` | `msg.sender == spender` | immutable | spender (timelocked) | NO — only Spender |
| `PermanentStorage.set*Seen / setCurvePoolInfo / setRelayersValid` | `permission[storageId][caller]` | PS storage | operator + designated roles | NO — only the strategies and operator |
| `*.setAllowance / setSubsidyFactor / upgradeSpender / transferOwnership` | `onlyOperator` | each strategy | operator | NO — Gnosis Safe |

## Auth-bypass attempts (negative results)

1. **Init/reinit** — All implementations are TUP-style behind operator. No `initialize` is publicly callable post-deploy. ✅ closed.

2. **Proxy/impl confusion** — UserProxy + PermanentStorage are TUP. Calling
   the implementation directly does not affect proxy state. The strategies
   themselves are NOT proxies. ✅ closed.

3. **Upgrade authority drift** — `transferOwnership` requires `onlyOperator`
   (Gnosis Safe).  No `setOperator` race condition: nominate+accept pattern
   on UserProxy, direct `transferOwnership` on strategies. ✅ closed.

4. **Signature replay across strategies** —
   - Each strategy uses domain `Tokenlon` v5 with its own `verifyingContract`.
   - The struct typehashes also differ (`Order` vs `fillWithPermit` vs
     `tradeWithPermit` vs `Fill` vs `AllowFill` vs `Offer` vs `RFQOrder`).
   - PermanentStorage maintains separate per-strategy replay sets. ✅ closed.

5. **Callback/hook trust** — Strategies do not register hooks; no
   inbound-from-DEX callback affects state. The Curve/UniV2/V3 swaps run
   in-place inside `_swap*`. ✅ closed.

6. **delegatecall/plugin clobber** — UserProxy.multicall is `delegatecall`
   to *self*, not external. ✅ closed.

7. **Boolean/logic slips in access checks** — Access checks are simple
   equality (`msg.sender == X`) or single-mapping lookups. No `||` vs `&&`
   inversion observed. ✅ closed.

8. **Timelock/guard miswire** — `Spender.authorize` and
   `AllowanceTarget.setSpenderWithTimelock` both gate on
   `now >= timelockExpirationTime`. Both reset the pending state on
   `complete*`. No alternate unguarded path. ✅ closed.

9. **isValidSignature wallet-mode (Type 6)** —
   - explicit `iszero(extcodesize(walletAddress)) → revert "WALLET_ERROR"`
   - explicit `eq(returndatasize(), 32) → revert` if wallet returned wrong size
   - magic prefix check is a 4-byte AND on the returned 32 bytes
   - cannot be bypassed by an EOA "victim" address. ✅ closed.

10. **isValidSignature WalletBytes (Type 4)** — calls
    `IERC1271Wallet.isValidSignature(_data, _sig)` with `_data = bytes("")`
    in RFQ/AMMWrapper.  A wallet that ignores `_data` and validates only
    `_sig` could return magic for any `_data`.  This is exploitable only
    if the **maker or taker** address is a contract whose `isValidSignature`
    is permissive for empty `_data`.  No production wallet observed doing
    this; off-chain risk only.

## Operator (multisig) blast radius

If the Gnosis Safe `0x63ef071b…29f` is compromised:
- Can call `Spender.authorize([attacker])` → wait 1 day → `completeAuthorize` →
  `Spender.spendFromUser(any user, any token, any amount)` → drain every
  user approval.
- Can call `*.upgradeSpender(attacker_spender)` on any strategy → reroute
  pulls to attacker.
- Can call `AllowanceTarget.setSpenderWithTimelock(attacker)` (timelock 1 day)
  → directly drain user approvals.

This is **the** central trust assumption of the entire Tokenlon system.
No public lever shortens or bypasses these timelocks.
