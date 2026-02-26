# Control Plane: Bridge Finality Gap Targets

## Cached Contract Analysis

### 1. Metis L1 Bridge (0x3980c9ed79d2c191a89e02fa3529c60ed6e9c04b)

**Auth Mechanism:** CrossDomainEnabled.onlyFromCrossDomainAccount(l2TokenBridge)
- Checks: msg.sender == messenger
- Checks: messenger.xDomainMessageSender() == l2TokenBridge
- Trust chain: L1 contract → CrossDomainMessenger → L2 Bridge

**Auth State Locations:**
- `messenger` address (set at deployment/initialization)
- `l2TokenBridge` address (set at deployment/initialization)

**Auth Writers:**
- Constructor / initializer (one-time)
- Proxy admin (if upgradeable - needs verification)

**Bypass Hypotheses:**
1. Messenger compromise: if messenger contract is upgradeable, new impl could forge xDomainMessageSender
2. Direct call to impl: if proxy pattern, direct call to implementation may bypass auth
3. Cross-domain message from different L2 contract claiming to be l2TokenBridge

**Fund Release Functions (Critical Path):**
- `finalizeETHWithdrawal(from, to, amount, data)` → sends ETH
- `finalizeETHWithdrawalByChainId(chainId, from, to, amount, data)` → sends ETH
- `finalizeERC20Withdrawal(l1Token, l2Token, from, to, amount, data)` → sends ERC20
- `finalizeERC20WithdrawalByChainId(...)` → sends ERC20
- `finalizeMetisWithdrawalByChainId(...)` → sends Metis token

### 2. EtherDelta Exchange (0x2a0c0dbecc7e4d658f48e01e3fa353f44050c208)

**Auth Mechanism:** onlyAdmin modifier + ECDSA signature verification
- Admin address stored in contract
- User must sign withdrawal params
- Admin submits the signed withdrawal

**Auth State Locations:**
- `admin` address
- `feeAccount` address

**Auth Writers:**
- `changeAdmin(admin_)` - callable only by admin
- `changeFeeAccount(feeAccount_)` - callable only by admin

**Bypass Hypotheses:**
1. Admin key compromise → direct fund drain
2. Signature replay: nonce-based protection exists (withdrawn[hash] mapping)
3. Fee manipulation: admin controls feeWithdrawal parameter

### 3. AdEx Protocol (Validator-Signed Channels)

**Auth Mechanism:** M-of-N supermajority (2/3 validators)
- ECDSA signature verification per validator
- Multiple signature modes: EIP712, GETH, TREZOR, ADEX

**Auth State Locations:**
- Channel validators set at channel creation
- Identity privilege levels

**Auth Writers:**
- Channel creation (immutable validators)
- Identity setAddrPrivilege (privilege escalation)

**Bypass Hypotheses:**
1. Validator key compromise (need 2/3)
2. Shared RPC eclipse (all validators see same phantom)
3. Identity privilege escalation via flash loan (temporarily gain privilege)

## Priority Target for Finality Gap Analysis

**Metis L1 Bridge is the highest-priority target because:**
1. Uses cross-domain messenger pattern (standard L2 bridge)
2. Trust is delegated to messenger protocol's finality handling
3. Metis uses optimistic-style consensus → long finality window
4. If messenger relays messages from unfinalized L2 blocks → phantom withdrawals possible
5. Concrete L1 contract address in our cache for analysis

## Known Fast Bridge Protocols to Investigate (L1 Mainnet)

| Protocol | L1 Contract | Relayer Model | Priority |
|----------|------------|---------------|----------|
| Across Protocol | SpokePool (0x5c7BCd6E7De5423a257D81B442095A1a6ced35C5) | Single relayer fills | HIGH |
| Hop Protocol | L1 Bridge contracts per token | Bonder (single signer) | HIGH |
| Stargate V2 | Various endpoints | LayerZero DVN + relayer | MEDIUM |
| Synapse Bridge | SynapseBridge router | Validator committee | MEDIUM |
| Connext/Everclear | DiamondProxy | Router/solver based | MEDIUM |
| Celer cBridge | Bridge contract | SGN validator set | MEDIUM |
| Socket/Bungee | SocketGateway | Route-specific | LOW |
| Metis Bridge | 0x3980... (cached) | CrossDomainMessenger | HIGH (have source) |
