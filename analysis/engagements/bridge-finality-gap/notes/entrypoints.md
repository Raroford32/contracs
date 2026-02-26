# Entrypoints: Bridge Finality Gap Targets

## Cached Contract Surfaces

### Metis L1 StandardBridge (0x3980c9ed79d2c191a89e02fa3529c60ed6e9c04b_impl)

| Function | Selector | Callable By | Gate | External Calls | Notes |
|----------|----------|-------------|------|---------------|-------|
| finalizeETHWithdrawal | TBD | CrossDomainMessenger only | onlyFromCrossDomainAccount | _to.call{value} | ETH release |
| finalizeETHWithdrawalByChainId | TBD | CrossDomainMessenger only | onlyFromCrossDomainAccount | _to.call{value} | Multi-chain ETH |
| finalizeERC20Withdrawal | TBD | CrossDomainMessenger only | onlyFromCrossDomainAccount | SafeERC20.transfer | ERC20 release |
| finalizeERC20WithdrawalByChainId | TBD | CrossDomainMessenger only | onlyFromCrossDomainAccount | SafeERC20.transfer | Multi-chain ERC20 |
| finalizeMetisWithdrawalByChainId | TBD | CrossDomainMessenger only | onlyFromCrossDomainAccount | METIS transfer | Metis token |
| depositETH | TBD | EOA | None | messenger.sendMessage | L1→L2 deposit |
| depositETHTo | TBD | EOA | None | messenger.sendMessage | L1→L2 deposit to addr |
| depositERC20 | TBD | EOA | None | messenger.sendMessage | L1→L2 ERC20 deposit |

**Key observation:** ALL withdrawal functions gated by `onlyFromCrossDomainAccount(l2TokenBridge)`.
The security model reduces to: "Can the CrossDomainMessenger be made to relay a message from unfinalized state?"

### EtherDelta (0x2a0c0dbecc7e4d658f48e01e3fa353f44050c208)

| Function | Selector | Callable By | Gate | External Calls | Notes |
|----------|----------|-------------|------|---------------|-------|
| deposit | TBD | EOA | None | token.transferFrom | Deposit ERC20 |
| withdraw | TBD | EOA | None | token.transfer | User withdraws own tokens |
| depositEther | TBD | EOA | payable | None | Deposit ETH |
| withdrawEther | TBD | EOA | None | msg.sender.send | Withdraw ETH |
| adminWithdraw | TBD | Admin only | onlyAdmin + ecrecover | token.transfer | Admin-gated user withdrawal |
| trade | TBD | EOA | ecrecover order sig | internal accounting | Match orders |

**Key observation:** adminWithdraw is the relayer-signed payout pattern.
Admin acts as trusted relayer; user signs authorization; admin executes.
NOT a cross-chain bridge but demonstrates the ECDSA-gated release pattern.

## Target Protocols for On-Chain Investigation

### Priority 1: Across Protocol SpokePool
- Need to fetch and analyze: `fillV3Relay()` or `fillRelay()` function
- Relayer fills user's withdrawal on destination chain
- Key question: does fillRelay require any finality proof?

### Priority 2: Hop Protocol L1 Bridges
- Need to fetch and analyze: `bondWithdrawal()` function
- Bonder posts bond + signature to release funds
- Key question: what triggers the bonder to act? Finality of source chain?

### Priority 3: Synapse Bridge
- Need to fetch and analyze: relay/fill functions
- Multi-validator: what finality guarantee do validators provide?

## Next Steps
- [ ] Fetch Across SpokePool source via sourcify/etherscan
- [ ] Fetch Hop L1 Bridge source
- [ ] Map relayer/bonder signature verification in each
- [ ] Determine finality handling in off-chain agents (timing test or source code review)
