# Assumptions — Tokenlon RFQ stack

Each row: implicit assumption made by the protocol, where in code it is
relied upon, what would have to happen for it to be false, what goes
wrong if it is, whether the adversary can cause it.

---

ASSUMPTION 1: maker EIP712 signature is sufficient to authorize ALL fills of an Order
- EVIDENCE: RFQ.fill — `isValidSignature(makerAddr, orderDigest, "", mmSig)`
- VIOLATION CONDITION: maker sig leaks; same hash valid forever (no nonce)
- CONSEQUENCE: orders fillable until deadline by anyone with both maker and taker sigs
- VIOLATION FEASIBILITY: yes — sigs leak via UI bugs / mempool / phishing
- COMPENSATING CONTROL: per-tx hash replay set (`setRFQTransactionSeen`); deadline; taker sig also required

ASSUMPTION 2: taker EIP712 signature commits the receiver
- EVIDENCE: RFQ.FILL_WITH_PERMIT_TYPEHASH includes receiverAddr
- VIOLATION CONDITION: typehash misses a receiver field
- CONSEQUENCE: attacker chooses receiver, drains taker's signed payment
- VIOLATION FEASIBILITY: would need a code change
- COMPENSATING CONTROL: typehash audited; receiver IS included

ASSUMPTION 3: PermanentStorage replay sets are append-only
- EVIDENCE: PS.setRFQTransactionSeen requires `!seen[h]` then sets to true
- VIOLATION CONDITION: a function exists to clear `seen[h]`; or storage layout collision
- CONSEQUENCE: signed orders re-fillable indefinitely
- VIOLATION FEASIBILITY: would require a privileged function or storage bug
- COMPENSATING CONTROL: no clear() exists; storage IDs are bytes32 namespaces

ASSUMPTION 4: Spender authority cannot be expanded permissionlessly
- EVIDENCE: `Spender.authorize` is `onlyOperator` + 1-day timelock + `completeAuthorize`
- VIOLATION CONDITION: an unguarded path adds an authorized contract
- CONSEQUENCE: new contract can call `spendFromUser` and drain user approvals
- VIOLATION FEASIBILITY: requires operator compromise; timelock enforced
- COMPENSATING CONTROL: timelock 1 day + multisig

ASSUMPTION 5: AllowanceTarget can only be re-rooted by the current Spender
- EVIDENCE: AllowanceTarget.setSpenderWithTimelock requires `onlySpender`
- VIOLATION CONDITION: a path lets non-spender call it
- CONSEQUENCE: user approvals re-rooted under attacker control
- VIOLATION FEASIBILITY: requires Spender compromise
- COMPENSATING CONTROL: Spender's auth is the operator; same multisig trust

ASSUMPTION 6: every authorized strategy validates its own callers via signatures
- EVIDENCE: each strategy has `onlyUserProxy` + signature checks
- VIOLATION CONDITION: a strategy with a permissive `spendFromUser` invocation gets authorized
- CONSEQUENCE: that strategy becomes a universal drain primitive
- VIOLATION FEASIBILITY: requires operator action
- COMPENSATING CONTROL: timelocked authorize; operator review

ASSUMPTION 7: AMMWrapper.trade output ≥ user's signed makerAssetAmount minus subsidy
- EVIDENCE: AMM `_settle` requires `inSubsidyRange` for shortfalls; non-validated relayers cannot subsidize
- VIOLATION CONDITION: subsidy math wrong; or a path that outputs >0 but <minAmount slips through
- CONSEQUENCE: user receives less than they signed for
- VIOLATION FEASIBILITY: math reviewed correct
- COMPENSATING CONTROL: explicit require with safe arithmetic; validated relayer set is small

ASSUMPTION 8: LimitOrder protocol-fill output ≥ takerTokenAmount
- EVIDENCE: `require(takerTokenOut >= _settlement.takerTokenAmount)`
- VIOLATION CONDITION: AMM swap rounds to zero; or token transfer hook subverts balance accounting
- CONSEQUENCE: maker gets less than signed
- VIOLATION FEASIBILITY: would need a malicious token in the path; tokens chosen by maker
- COMPENSATING CONTROL: maker selects makerToken/takerToken; relayer chooses path

ASSUMPTION 9: ECDSA recovery cannot produce a non-zero address from random data
- EVIDENCE: SignatureValidator does `address(0)` reject; relies on standard ECDSA
- VIOLATION CONDITION: hash collision in EIP712 digest; ECDSA malleability
- CONSEQUENCE: forged signature accepted
- VIOLATION FEASIBILITY: cryptographically infeasible
- COMPENSATING CONTROL: standard primitives; v∈{27,28} not enforced — possible malleability via {v,27-v} flip but does not yield a different signer

ASSUMPTION 10: ERC1271 wallet implementations honor isValidSignature semantics
- EVIDENCE: SignatureValidator types 4/5/6 trust wallet's response
- VIOLATION CONDITION: a wallet at maker/taker address returns magic for any data
- CONSEQUENCE: anyone with control of that wallet's logic can sign-as-them
- VIOLATION FEASIBILITY: only if maker/taker chose to be a permissive contract; user error, not protocol bug
- COMPENSATING CONTROL: extcodesize + returndatasize + magic prefix check

ASSUMPTION 11: 0x v2 ZeroExchange replay protection covers PMM
- EVIDENCE: PMM.fill calls `zeroExchange.executeTransaction(salt, address(this), data, "")`
- VIOLATION CONDITION: 0x v2 transaction replay protection breaks
- CONSEQUENCE: PMM fills replayable
- VIOLATION FEASIBILITY: would require a 0x v2 vulnerability
- COMPENSATING CONTROL: 0x v2 sets `transactions[hash].executed = true`; no PMM-side replay store needed

ASSUMPTION 12: PermanentStorage role permissions are correctly initialized
- EVIDENCE: `permission[storageId][caller]` mapping
- VIOLATION CONDITION: storageId clash, or operator misregisters a role
- CONSEQUENCE: an unauthorized contract could mark txns "seen" or alter Curve indexes
- VIOLATION FEASIBILITY: live state reviewed; permissions match expectations
- COMPENSATING CONTROL: operator review; events emit on permission change

ASSUMPTION 13: tx.origin == msg.sender in UserProxy.toRFQ/toPMM/etc. is sufficient EOA-only gating
- EVIDENCE: explicit `require(msg.sender == tx.origin)` in to* functions
- VIOLATION CONDITION: contract callers
- CONSEQUENCE: aggregator/router contracts can't compose with Tokenlon
- VIOLATION FEASIBILITY: by design, no exploit
- COMPENSATING CONTROL: tx.origin used only as gating, not for authorization decisions

ASSUMPTION 14: RFQ contract holds no tokens between fills
- EVIDENCE: every fill atomically transfers in/out; no lingering balances
- VIOLATION CONDITION: someone donates tokens to the RFQ contract
- CONSEQUENCE: dust accumulates; not directly drainable (no public withdraw)
- VIOLATION FEASIBILITY: anyone can transfer tokens to the contract
- COMPENSATING CONTROL: operator can sweep via setAllowance + spender
