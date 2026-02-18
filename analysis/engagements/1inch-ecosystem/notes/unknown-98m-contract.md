# Investigation: Unknown $98M+ Contract at 0x111cff45948819988857bbf1966a0399e0d1141e

## Definitive Identification

**Contract Type:** Gnosis MultiSigWallet (original, base version without daily limit)

**Source:** `github.com/gnosis/MultiSigWallet/contracts/MultiSigWallet.sol`

**This is NOT a proxy, NOT a Gnosis Safe, and NOT a custom contract.** It is the canonical Gnosis
MultiSigWallet compiled with Solidity 0.4.x. Source code is unverified on Etherscan but the bytecode
is a 100% match to the well-known open-source Gnosis MultiSigWallet.sol.

---

## Evidence Summary

### Bytecode Analysis

- **Runtime bytecode length:** 5,905 bytes
- **Compiler:** Solidity 0.4.x (confirmed by `0x6060` prefix and `a165627a7a72305820` CBOR metadata format)
- **Bytecode SHA256:** `b2ce3994f9af9e59e660158139cf761b8b890be31ddf061b5a6329e476ce5cb5`
- **Solidity metadata hash:** `bb50b57380a5c91951c410be1c0fee3232edd0869fa5ab4ee3c3ba194125ece6`
- **No proxy pattern:** EIP-1967 implementation and admin slots are both zero
- **MAX_OWNER_COUNT constant (0x32 = 50):** Present in bytecode, matching Gnosis MultiSigWallet

### Function Selector Dispatch (21 selectors, all matching Gnosis MultiSigWallet)

| Selector | Function |
|----------|----------|
| `0x025e7c27` | `owners(uint256)` |
| `0x173825d9` | `removeOwner(address)` |
| `0x20ea8d86` | `revokeConfirmation(uint256)` |
| `0x2f54bf6e` | `isOwner(address)` |
| `0x3411c81c` | `confirmations(uint256,address)` |
| `0x54741525` | `getTransactionCount(bool,bool)` |
| `0x7065cb48` | `addOwner(address)` |
| `0x784547a7` | `isConfirmed(uint256)` |
| `0x8b51d13f` | `getConfirmationCount(uint256)` |
| `0x9ace38c2` | `transactions(uint256)` |
| `0xa0e67e2b` | `getOwners()` |
| `0xa8abe69a` | `getTransactionIds(uint256,uint256,bool,bool)` |
| `0xb5dc40c3` | `getConfirmations(uint256)` |
| `0xb77bf600` | `transactionCount()` |
| `0xba51a6df` | `changeRequirement(uint256)` |
| `0xc01a8c84` | `confirmTransaction(uint256)` |
| `0xc6427474` | `submitTransaction(address,uint256,bytes)` |
| `0xd74f8edd` | `MAX_OWNER_COUNT()` |
| `0xdc8452cd` | `required()` |
| `0xe20056e6` | `replaceOwner(address,address)` |
| `0xee22610b` | `executeTransaction(uint256)` |

### Event Signatures Verified (all 9 Gnosis MultiSigWallet events present in bytecode)

- `Deposit(address,uint256)` - `e1fffcc4...`
- `Confirmation(address,uint256)` - `4a504a94...`
- `Submission(uint256)` - `c0ba8fe4...`
- `Execution(uint256)` - `33e13ecb...`
- `ExecutionFailure(uint256)` - `526441bb...`
- `OwnerAddition(address)` - `f39e6e1e...`
- `OwnerRemoval(address)` - `8001553a...`
- `RequirementChange(uint256)` - `a3f1ee91...`
- `Revocation(address,uint256)` - `f6a31715...`

---

## Configuration (from storage)

| Storage Slot | Value | Meaning |
|---|---|---|
| Slot 0 | `0x00` | (unused / mapping base) |
| Slot 1 | `0x00` | (unused / mapping base) |
| Slot 2 | `0x00` | (unused / mapping base) |
| Slot 3 | `0x03` | `owners.length` = 3 owners |
| Slot 4 | `0x03` | `required` = 3 confirmations needed |
| Slot 5 | `0x228d` | `transactionCount` = 8,845 total transactions |

### Owners (3-of-3 multisig)

| Index | Address | Role (observed) |
|---|---|---|
| 0 | `0x38465c60beec719f3800339c951a0ec5ea0fbb3c` | Primary submitter (calls `submitTransaction`) |
| 1 | `0x34472e69dae03301f6ff2f7c5efe24cbb58304bd` | Confirmer (calls `confirmTransaction`) |
| 2 | `0x4314de1186be78851038f53c8a7d04cf9fbc7230` | Confirmer (calls `confirmTransaction`) |

All three owners are EOAs. Both owners[1] and owners[2] were initially funded by
`0xb01cb49fe0d6d6e47edf3a072d15dfe73155331c` (same EOA that later deposited 43,972 ETH).

---

## Deployment Details

- **Deployed at:** Block 9,778,222 (March 31, 2020 18:27:02 UTC)
- **Deployer:** `0xe1037cf03fa0bbf6038e8c2542a91f0f6d365356` (EOA, funded by `0xb01cb49fe...`)
- **Creation TX:** `0x2bec49ba7f5f037c12c45c1c9a29d3bbffa2967c3330efd89329ee56409259c3`
- **Constructor args (ABI-encoded):** 3 owners + required=3 (confirmed from creation tx input tail)
- **Same deployer** also created another unverified contract at Block 12,625,368:
  `0x3523b9678888a5cc7d31a724126f50b2394064d6` (also unverified source)

---

## Current Holdings

- **ETH Balance:** 27,357.33 ETH (~$98M+ at current prices)
- **ERC-20 tokens:** 66+ distinct tokens including:
  - BAT (Basic Attention Token) - large historical inflows (millions of BAT)
  - MKR (Maker) - recent activity (70 MKR transfers out)
  - RNDR (Render Token)
  - MASK (Mask Network)
  - IMX (Immutable X)
  - DCR (Decred)

---

## Operational Pattern (from transaction history)

### Standard Workflow (3-of-3 confirmation)

1. **Owner[0]** (`0x3846...`) calls `submitTransaction(destination, value, data)` - creates a new pending tx
2. **Owner[1]** (`0x3447...`) calls `confirmTransaction(txId)` - adds second confirmation
3. **Owner[2]** (`0x4314...`) calls `confirmTransaction(txId)` - adds third confirmation, triggering automatic execution

All three confirmations are required (3-of-3). When the third confirmation arrives, the Gnosis
MultiSigWallet automatically executes the transaction via `executeTransaction()`.

### Recent Activity Samples

**ETH Outflows (to EOA `0xa9264494a92ced04747ac84fc9ca5a0b9549b491`):**
- Block 24,481,617: 730 ETH sent
- Block 24,473,923: 500 ETH sent (visible as internal tx)
- Block 24,473,910: 250 ETH submitted
- Block 24,465,483: 107 ETH submitted

**ERC-20 Outflows (MKR to `0x1dd123d7d927401572982eb2a14718e5726bb16d`):**
- Block 24,472,625: 70 MKR transfer
- Block 24,466,677: 70 MKR transfer

**ETH Inflows (from EOA `0x835033bd90b943fa0d0f8e5382d9dc568d3fbd96`):**
- Block 24,477,164: 1,237 ETH deposited
- Block 24,469,990: 989 ETH deposited
- Block 24,462,813: 752 ETH deposited

**ERC-20 Inflows (various tokens from multiple EOAs):**
- Regular inflows of BAT, MKR, RNDR, MASK, IMX, DCR from distinct EOA addresses

---

## Key Counterparty Addresses

| Address | Type | Relationship |
|---|---|---|
| `0xa9264494a92ced04747ac84fc9ca5a0b9549b491` | EOA | Primary ETH recipient |
| `0x835033bd90b943fa0d0f8e5382d9dc568d3fbd96` | EOA | Regular ETH depositor (hot wallet pattern - many small txs) |
| `0x1dd123d7d927401572982eb2a14718e5726bb16d` | EOA | MKR token recipient |
| `0x53c3584fb8867ed931917891d037f88af0218cc2` | EOA | BAT token sender (large historical deposits) |
| `0xb01cb49fe0d6d6e47edf3a072d15dfe73155331c` | EOA | Original funder (43,972 ETH initial deposit + owner funding) |
| `0xe1037cf03fa0bbf6038e8c2542a91f0f6d365356` | EOA | Contract deployer (deployed 2 contracts) |

---

## Security Assessment (for the 1inch Ecosystem Engagement)

### What This Contract Is

This is a **cold storage / treasury multisig wallet** operated by an entity with significant crypto
holdings. The operational pattern (regular ETH/token inflows from hot wallets, periodic outflows to
specific EOAs, 3-of-3 confirmation requirement) is consistent with a **centralized entity's treasury
management** operation (exchange, fund, or protocol treasury).

### Relevance to 1inch Ecosystem

This contract should be assessed for its relationship to the 1inch ecosystem:
- The deployer `0xe1037cf...` and funder `0xb01cb49f...` should be checked against known 1inch
  team/investor addresses
- The consistent operational pattern of the 3 owners suggests coordinated control by a single entity
- The diverse token portfolio (BAT, MKR, RNDR, MASK, IMX, DCR, etc.) suggests this is an
  investment fund or exchange cold wallet rather than a protocol-specific treasury

### No External Vulnerability Surface

As a Gnosis MultiSigWallet:
- All state-changing operations require 3-of-3 owner signatures
- The contract has no external dependencies (no oracles, no tokens, no DeFi integrations)
- The fallback function only accepts ETH deposits (emits `Deposit` event)
- `addOwner`, `removeOwner`, `replaceOwner`, `changeRequirement` all require `onlyWallet` modifier
  (can only be called by the multisig itself via a confirmed transaction)
- No upgrade mechanism, no proxy pattern, no delegatecall to user-controlled targets
- The `executeTransaction` external call uses the low-level `destination.call.value(value)(data)`
  pattern, which is standard for Gnosis MultiSig and only executable after 3-of-3 confirmation

### Risk: The Contract Uses the ORIGINAL Gnosis MultiSigWallet, Not Gnosis Safe

The original Gnosis MultiSigWallet has a known limitation compared to Gnosis Safe:
- **No guard mechanism** - cannot add transaction guards/hooks
- **No module system** - cannot extend functionality
- **`executeTransaction` uses `address.call()` with a fixed gas stipend** - the `f1` opcode (CALL)
  with a raw subcall; the gas forwarding is `gas - 34710` (the `6187965a03` pattern visible in
  bytecode translates to `GAS SUB(0x8796)` = `GAS - 34710`), which is the standard Gnosis pattern
- **No EIP-1271 support** - cannot sign messages on behalf of the wallet
- **No replay protection across chains** - the wallet has no chain-specific nonce or domain separator

These are design limitations, not exploitable vulnerabilities, given the 3-of-3 owner requirement.
