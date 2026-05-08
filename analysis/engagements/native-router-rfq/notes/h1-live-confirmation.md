# H1 — Soft-Expiry Agent: LIVE CONFIRMATION on Arbitrum

## Summary
The soft-expiry observation (H1) — that `_verifyAgentSoft` accepts an agent
whose `agentExpiry > 0` even if the recorded expiry is in the past — is no
longer hypothetical. Direct on-chain queries against the Pendle Boros
Router proxy on Arbitrum at block ~460,760,913 (May 8 2026) verify **141
distinct (account, agent) pairs across 8 distinct accounts** where:

1. The agent was approved at some past block (Aug-Sep 2025)
2. The on-chain `agentExpiry[account][agent]` storage value is non-zero
3. The stored expiry timestamp is **231+ days in the past**
4. No `_revokeAgent` has been called (storage was not zeroed)

For all 141 pairs, the on-chain code in `_verifyAgentSoft`:
```solidity
require(_AMS().agentExpiry[account][agent] > 0, Err.AuthInvalidAgent());
require(_isValidSignatureNow(agent, messageHash, signature), Err.AuthInvalidMessage());
```
**evaluates the first require as TRUE** — the soft check passes. Only the
ECDSA signature verification (and the off-chain validator's co-signature)
gate execution.

## Method
1. Queried Etherscan v2 logs API on Router proxy
   `0x8080808080dab95efed788a9214e400ba552def6` for AgentApproved
   `(topic0=0xd906018d619f6961a9e5364faba3fb70fbb4e769cf01e92f7264fec64b41759e)`
   from genesis to latest. Pulled 10,000 events (Etherscan max).
2. Filtered to: accountId byte == 0x00 (main accounts; AMM auto-sync events
   excluded), expiry timestamp < current block.timestamp.
3. Result: 141 candidate (account, agent) pairs with naturally-expired
   approvals.
4. For each candidate, called the public view selector
   `agentExpiry(bytes21,address)` (sig 0xc9c437b3) at block ~460,760,913 via
   Etherscan v2 eth_call proxy.
5. Result: **141/141 returned non-zero stored expiry** (i.e., not revoked).

CSV evidence: `notes/unrevoked_expired_at_block_460760913.csv`
Format: `<bytes21_account_hex>,<agent_addr>,<stored_expiry_ts>,<approval_block>`

## Distribution across accounts
| Account | Unrevoked-expired count |
|---|---|
| `0x904636b8922348e187426892a8bc96c3053b7176` | **82** |
| `0x0d198bc03844c4bb7c94cf708cf9595ea8dc96aa` | 26 (EIP-7702 delegated to MetaMask DeleGator) |
| `0x75e23ef658a2bcca87a774912a543ab1d741ed60` | 19 |
| `0x4626b191994c2a24af6b040745fbaf0b62f2ede6` | 5 |
| `0x1eca053af93a7afaefcd2133a352f422c3c04903` | 4 (EIP-7702 delegated) |
| `0x7d83e1632fc5a9d5791bb089c69e1080fe3e86db` | 3 |
| `0x5ebf929d852ed524b083d76673aff8f40633338e` | 1 |
| `0xc0faf4cbe4a9295e3e7fde4b2ffecca43fe828ee` | 1 |

The two EIP-7702 accounts:
- `0x0d198bc0…` → delegate `0x63c0c19a282a1b52b07dd5a65b58948a07dae32b`
  (verified as `EIP7702StatelessDeleGator` — MetaMask Delegation Toolkit)
- `0x1eca053a…` → delegate `0x06ee8eae31a5126f668a27b2426aa73d05643c7a`

A direct call to `0x0d198bc0…isValidSignature(0x00, 0x00)` reverts with
selector `0xf645eedf = ECDSAInvalidSignature()` — the delegate enforces
strict ECDSA, so it is NOT a backdoor: arbitrary signatures don't pass.

## What this confirms vs. what it doesn't

**Confirmed (E2-level evidence)**:
- The "loose check" pattern is live in production, not just a code-read concern.
- Multiple real users have stale approvals that the on-chain code still
  treats as valid for OTC AcceptOTCFullMessage signature verification.
- The protocol's off-chain validator (single address
  `0x862f53763a4cbb1bc74d605716342b53c6a84cc6`) is the only remaining gate
  preventing OTC execution against these accounts via these agents.

**Not yet exploited (E3 gate not met)**:
- ECDSA verification of the agent's signature still requires the agent's
  private key. The 141 agents are bare EOAs (no code, no EIP-7702
  delegation visible) — without a key leak, signatures cannot be forged.
- The OTC validator must additionally co-sign each
  ExecuteOTCTradeMessage for execution. Without validator key compromise
  or unauthorized validator co-signature, no trade can be submitted.

## Composition value of this finding
This concrete evidence elevates H1 from "design note" to "live operational
exposure":

1. **Quantified blast radius**: 141 agent keys, if any leak, retain
   on-chain validity for OTC trades against 8 accounts (subject to
   validator co-signature).
2. **Two of those accounts are EIP-7702 smart accounts** — likely
   institutional / high-balance users.
3. **231+ days of dormant exposure**: the protocol or its users have not
   acted on the soft-check semantic — the keys remain "valid".

## Recommended actions for the protocol
1. Tighten `_verifyAgentSoft` to `agentExpiry > block.timestamp` to match
   `_verifyAgentSigAndIncreaseNonce`'s strict check (the inconsistency
   between OTC and agentExecute paths is itself a smell).
2. Encourage / automate revocation of expired approvals (or auto-zero on
   reads when expiry has passed).
3. Treat the validator as a **defense in depth, not a primary gate** — and
   shore it up (e.g., move to multi-sig validator).

## Data freshness
- Block: ~460,760,913 (Arbitrum One)
- Timestamp: ~1,778,266,122 (May 8 2026)
- Evidence sources:
  - Router proxy `0x8080808080dab95efed788a9214e400ba552def6`
  - Validator `0x862f53763a4cbb1bc74d605716342b53c6a84cc6`
  - Etherscan v2 logs + eth_call proxy
  - Sources verified: Etherscan v2 chainid=42161 source-code endpoint
