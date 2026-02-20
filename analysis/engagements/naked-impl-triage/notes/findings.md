# Naked Implementation Triage — 10 CRITICAL Proxies

## Alert Type
**CRITICAL — naked impl, high-value proxy (>100 ETH)**

The alert fires when a proxy's implementation contract has `impl_initialized: false` in the monitoring system, suggesting an attacker could call `initialize()` on the implementation directly. For UUPS proxies, this could allow an attacker to take ownership of the implementation, then call `upgradeToAndCall()` to brick or hijack the proxy.

## Resolution: ALL 10 FALSE POSITIVES

Every implementation properly calls `_disableInitializers()` in its constructor. The monitoring system's `impl_initialized: false` flag is likely checking the wrong storage slot or using an incomplete heuristic.

## Consolidated Results

| # | Proxy | Implementation | Protocol | Verified | OZ Version | Init Protected | UUPS Protected | Proxy TVL | ETH Throughput 90d |
|---|---|---|---|---|---|---|---|---|---|
| 1 | 0x036676...5d | 0xea38df...20 | **Kelp DAO** (LRTDepositPool) | YES | v4 | slot 0 = 0xff | N/A (Transparent) | $7.67M | 242K ETH |
| 2 | 0x2a3dd3...de | 0x66e012...ad | **Polygon** (AgglayerBridge) | YES | v4 | slot 0 = 0xff | N/A (Transparent) | $661T* | 107K ETH |
| 3 | 0xe3cbd0...8f | 0x01a360...a2 | **Mantle** (mETH Staking) | YES | v4 | slot 0 = 0xff | N/A (Transparent) | $98.9K | 102K ETH |
| 4 | 0xd52379...34 | 0x40b45c...66 | **Stader** (StakeWise Pool) | YES | v4 | slot 0 = 0xff | N/A (Transparent) | $0 | 73K ETH |
| 5 | 0x663dc1...51 | 0x3c857e...64 | **deBridge** (Router) | YES | v4 | slot 0 = 0xff | N/A (Transparent) | $1.8K | 36K ETH |
| 6 | 0xe6d8d8...08 | 0x927a83...cc | **StakeWise v3** (EthVault) | YES | v5 | namespaced = max64 | UUPS: UnauthorizedCallContext | $108.3M | 21K ETH |
| 7 | 0x5c7bcd...c5 | 0x5e5b72...3b | **Across Protocol** (SpokePool) | YES | v4 | slot 0 = 0xff | UUPS: onlyProxy | $363K | 18K ETH |
| 8 | 0x604dd0...6e | 0xf7aea2...e1 | **Astherus** (Vault) | YES | v5 | namespaced = max64 | UUPS: UnauthorizedCallContext | $138.4M | 17K ETH |
| 9 | 0xef4fb2...66 | 0x322b48...df | **deBridge** (DLN DlnSource) | YES | v4 | slot 0 = 0xff | N/A (Transparent) | $4.8M | 16K ETH |
| 10 | 0x74a096...f5 | 0xd5b3be...a0 | **Renzo** (RestakeManager) | YES | v4 | slot 0 = 0xff | N/A (Transparent) | $2.1K | 13K ETH |

*\* Polygon AgglayerBridge TVL inflated by DeBank — likely counts bridged assets.*

## Evidence Details

### OpenZeppelin v4 Contracts (7 of 10)
- Storage slot `0x00` contains `0xff` (uint8 max = 255)
- Set by `_disableInitializers()` in constructor
- `initialize()` reverts with: `"Initializable: contract is already initialized"`

### OpenZeppelin v5 Contracts (3 of 10: EthVault, AstherusVault, SpokePool-partial)
- Namespaced storage slot `0xf0c57e16840df040f15088dc2f81fe391c3923bec73e23a9662efc9c229c6a00` contains `0xffffffffffffffff` (uint64 max)
- Set by `_disableInitializers()` in constructor
- `initialize()` reverts with custom error: `InvalidInitialization()` (0xf92ee8a9)

### UUPS Contracts (3 of 10: EthVault, SpokePool, AstherusVault)
- `upgradeToAndCall()` called directly on implementation reverts with:
  - OZ v5: `UUPSUnauthorizedCallContext()` (0xe07c8dba)
  - OZ v4: `onlyProxy` modifier check fails
- No path to hijack the proxy via implementation takeover

## Monitoring System Recommendation

The `impl_initialized: false` heuristic should be updated to check:
1. **OZ v4**: Storage slot 0 on the implementation for value `0xff`
2. **OZ v5**: Namespaced slot `0xf0c57e16...` for value `0xffffffffffffffff`
3. Both indicate `_disableInitializers()` was called — these are NOT vulnerable.
