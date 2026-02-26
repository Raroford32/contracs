# Value Flows: Finality Gap Attack Vector

## Entry → Transform → Exit Chains

### Flow 1: Fast Bridge Withdrawal (Category A - Highest Priority)

```
ENTRY: User deposits tokens into L2 bridge contract
  → L2 event emitted (DepositLocked / WithdrawalInitiated)

TRANSFORM (off-chain, Web2 boundary):
  → Off-chain agent reads L2 RPC ("latest" block)
  → Agent validates event against its business logic
  → Agent signs ECDSA payload authorizing L1 release
  → Agent submits signed tx to L1

EXIT: L1 bridge contract:
  → Verifies ECDSA signature == trusted relayer
  → Releases funds (ETH/ERC20) to recipient address
  → Marks withdrawal as completed (nonce consumed)

ATTACK FLOW:
  ENTRY: Attacker creates phantom L2 deposit in soon-to-be-orphaned block
  TRANSFORM: Agent reads phantom event, signs L1 release
  EXIT: L1 releases real funds for phantom L2 deposit
  POST: L2 block reorged; phantom deposit vanishes; L1 release persists
```

### Flow 2: Solver/Intent-Based Fill (Category A variant)

```
ENTRY: User posts cross-chain intent on L2 (swap X on L2 for Y on L1)

TRANSFORM (off-chain):
  → Solver monitors L2 for intents
  → Solver evaluates profitability
  → Solver fills on L1 (sends Y to user's L1 address)
  → Solver later claims reimbursement from protocol

EXIT: Solver receives reimbursement after settlement

ATTACK FLOW:
  ENTRY: Phantom intent on L2 (large swap at attractive rate)
  TRANSFORM: Solver fills on L1, sending real tokens
  EXIT: Solver claims reimbursement; but L2 intent was phantom
  → Protocol may reimburse solver from pool (socialized loss)
  → Or solver bears loss directly (concentrated loss)
```

### Flow 3: Metis L1 Bridge (From cached contracts)

```
Contract: 0x3980c9ed79d2c191a89e02fa3529c60ed6e9c04b_impl

ENTRY: User calls withdraw on L2 Metis bridge
  → L2 sends cross-domain message

TRANSFORM:
  → Cross-domain messenger relays message to L1
  → L1 bridge verifies onlyFromCrossDomainAccount(l2TokenBridge)

EXIT: finalizeETHWithdrawal / finalizeERC20Withdrawal
  → (bool success, ) = _to.call{value: _amount}(new bytes(0))
  → SafeERC20.safeTransfer(IERC20(_l1Token), _to, _amount)

TRUST BOUNDARY: CrossDomainEnabled.onlyFromCrossDomainAccount
  → Checks msg.sender == messenger && messenger.xDomainMessageSender() == l2TokenBridge
  → If messenger is compromised or reads unfinalized state: phantom withdrawal
```

## Fee Extraction Points

| Protocol Type | Fee Source | Fee Recipient | Manipulation Risk |
|--------------|-----------|---------------|-------------------|
| Fast bridge relayer | Spread (user pays higher fee for speed) | Relayer | Relayer fee not relevant to attack |
| DEX exchange (EtherDelta) | adminWithdraw feeWithdrawal | Admin/feeAccount | Admin can overcharge |
| Intent/solver | Solver spread | Solver | Not relevant to finality attack |
| Cross-domain bridge | Gas/relay fee | Protocol/messenger | Gas manipulation possible |

## Actor Model with Dual-Role Analysis

| Actor | Primary Role | Potential Dual Role | Conflict |
|-------|-------------|-------------------|----------|
| Bridge Relayer | Signs L1 payouts | Also monitors L2 state | Agent's view = protocol's truth |
| Solver/Filler | Fills intents on L1 | Also validates L2 intents | May not verify finality |
| L2 Sequencer | Orders L2 transactions | Also produces blocks | Can create phantom blocks |
| RPC Provider | Serves blockchain data | Shared infra for validators | Single point of failure |
| Bridge User | Deposits/withdraws | Also potential attacker | Can create phantom deposits |

### Critical Dual-Role: L2 Sequencer as Phantom Block Producer
- On rollups with centralized sequencers, the sequencer IS the block producer
- A compromised/malicious sequencer can create blocks containing phantom txs
- These blocks are broadcast to RPCs before finality proofs are generated
- Any agent reading "latest" will see the phantom as real
