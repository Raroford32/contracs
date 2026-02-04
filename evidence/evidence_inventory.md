# EVIDENCE COLLECTION: f(x) Protocol + Convex FXN Integration
## Systematic Evidence Inventory for Attack Chain Design

**Date**: 2026-02-04
**Target Contracts**:
- StakingProxyERC20: 0x8e0fd32e77ad1f85c94e1d1656f23f9958d85018
- Gauge Proxy: 0xc2def1e39ff35367f2f2a312a793477c576fd4c3
- Gauge Impl: 0x72a6239f1651a4556f4c40fe97575885a195f535
- Market Proxy: 0x267c6a96db7422faa60aa7198ffeeec4169cd65f
- Market Impl: 0x2c613d2c163247cd43fd05d6efc487c327d1b248
- Treasury Proxy: 0x781ba968d5cc0b40eb592d5c8a9a3a4000063885
- Treasury Impl: 0xdd8f6860f5a3eecd8b7a902df75cb7548387c224
- Base Token (eETH): 0xcd5fe23c85820f7b72d0926fc9b05b43e359b7ee

---

## 1. ON-CHAIN STATE & ACCOUNT TERMINOLOGY

### COLLECTED ✓
| Evidence | Source | Value |
|----------|--------|-------|
| Treasury Proxy address | Constructor args | 0x781ba968d5cc0b40eb592d5c8a9a3a4000063885 |
| Treasury Implementation | EIP-1967 slot | 0xdd8f6860f5a3eecd8b7a902df75cb7548387c224 |
| Market Implementation | EIP-1967 slot | 0x2c613d2c163247cd43fd05d6efc487c327d1b248 |
| Gauge Implementation | EIP-1967 slot | 0x72a6239f1651a4556f4c40fe97575885a195f535 |
| Base Token (eETH) | Code analysis | 0xcd5fe23c85820f7b72d0926fc9b05b43e359b7ee |

### MISSING - NEED TO COLLECT ✗
| Evidence | Method to Collect |
|----------|-------------------|
| Current state root at analysis block | eth_getBlockByNumber |
| Account nonces for all contracts | eth_getTransactionCount |
| ETH balances for all contracts | eth_getBalance |
| Code hashes for all contracts | eth_getCode → keccak256 |
| Storage roots for key contracts | eth_getProof |

---

## 2. STORAGE PRIMITIVES (Slot/Offset/Word)

### COLLECTED ✓
| Contract | Slot | Value | Meaning |
|----------|------|-------|---------|
| Treasury Proxy | 0x360894... (EIP-1967) | 0x...dd8f... | Implementation address |
| Market Proxy | 0x360894... (EIP-1967) | 0x...2c61... | Implementation address |
| Gauge Proxy | 0x360894... (EIP-1967) | 0x...72a6... | Implementation address |

### STORAGE LAYOUT ANALYSIS FROM SOURCE ✓
```
TreasuryV2 Storage Layout:
├── Slot 0: Initializable._initialized (uint8)
├── Slot 1: AccessControl._roles mapping base
├── Slot 50+: Custom variables
│   ├── priceOracle (address)
│   ├── referenceBaseTokenPrice (uint256)
│   ├── totalBaseToken (uint256)
│   ├── baseTokenCap (uint256)
│   ├── strategy (address)
│   ├── strategyUnderlying (uint256)
│   ├── emaLeverageRatio (EMAStorage struct)
│   ├── platform (address)
│   ├── rebalancePoolSplitter (address)
│   └── _miscData (bytes32 packed)

WrappedTokenTreasuryV2 extends TreasuryV2:
├── rateProvider (address)
```

### MISSING - NEED TO COLLECT ✗
| Evidence | Method to Collect |
|----------|-------------------|
| Actual slot values for Treasury state vars | eth_getStorageAt for each slot |
| priceOracle address (exact slot) | Calculate slot from inheritance |
| rateProvider address | eth_getStorageAt |
| totalBaseToken current value | eth_getStorageAt or eth_call |
| referenceBaseTokenPrice | eth_getStorageAt |
| Current collateralRatio | eth_call to collateralRatio() |
| Gauge storage layout | Map from source code |
| Gauge staker balances | eth_getStorageAt for mapping |

---

## 3. DERIVED ADDRESSING TERMS (Mappings, Arrays)

### COLLECTED FROM SOURCE ✓
```solidity
// TreasuryV2 mappings:
// AccessControl._roles: mapping(bytes32 => RoleData)
//   Slot: keccak256(role . 1)  // assuming _roles at slot 1

// FxUSDShareableRebalancePool mappings:
mapping(address => uint256) private _balances;  // user staking balance
mapping(address => uint256) private _rewards;   // accumulated rewards
mapping(address => address) public getStakerVoteOwner;  // vote delegation
mapping(address => mapping(address => bool)) public isStakerAllowed;  // vote sharing allowlist
```

### MAPPING SLOT CALCULATIONS NEEDED ✗
| Mapping | Key | Formula | Need Value |
|---------|-----|---------|------------|
| _balances[user] | user addr | keccak256(user . balances_slot) | YES |
| _rewards[user] | user addr | keccak256(user . rewards_slot) | YES |
| isStakerAllowed[A][B] | A, B | keccak256(B . keccak256(A . slot)) | YES |
| AccessControl roles | role hash | keccak256(role . slot) | YES - for LIQUIDATOR_ROLE |

---

## 4. DATA LOCATIONS DURING EXECUTION

### COLLECTED FROM SOURCE ANALYSIS ✓
```
StakingProxyERC20.execute() flow:
1. CALLDATA: (address _to, uint256 _value, bytes _data)
2. MEMORY: Loaded for _data processing
3. STORAGE READ: poolRegistry, fxn (for _checkExecutable)
4. EXTERNAL CALL: _to.call{value:_value}(_data)
5. RETURNDATA: (bool success, bytes result)

Treasury.collateralRatio() flow:
1. STORAGE READ: totalBaseToken
2. EXTERNAL CALL: priceOracle.getPrice()
3. EXTERNAL CALL: fToken.totalSupply()
4. EXTERNAL CALL: xToken.totalSupply()
5. MEMORY: SwapState struct computation
6. RETURN: uint256 ratio
```

### MISSING ✗
| Evidence | Need For |
|----------|----------|
| Free memory pointer state during critical functions | Reentrancy analysis |
| Stack depth at cross-contract calls | Call depth attack analysis |
| Calldata encoding for each entry point | Exploit payload construction |

---

## 5. TRANSIENT STORAGE (EIP-1153)

### STATUS: NOT USED ✓
- Analyzed contracts do NOT use TLOAD/TSTORE
- All state is persistent storage
- ReentrancyGuard uses traditional storage slot pattern

---

## 6. OPCODE-LEVEL EVIDENCE

### COLLECTED FROM SOURCE ✓
```
Critical opcode patterns identified:

DELEGATECALL usage:
- StakingProxyERC20 clones use delegatecall to implementation
- Storage context: clone's storage, code: implementation

STATICCALL usage:
- collateralRatio() uses staticcall to oracle
- prevents state modification during price reads

CALL with value:
- execute() allows value transfer: _to.call{value:_value}(_data)
- Potential for ETH injection attacks

External calls WITHOUT reentrancy guard:
- StakingProxy.getReward() - no explicit nonReentrant
- StakingProxy.earned() - no explicit nonReentrant
```

### MISSING - NEED TO COLLECT ✗
| Evidence | Method |
|----------|--------|
| Full bytecode disassembly | eth_getCode → disassemble |
| Control flow graph | Decompile runtime bytecode |
| Jump table / dispatcher analysis | Bytecode analysis |
| Gas costs for attack sequences | eth_estimateGas |

---

## 7. ABI & DECODING TERMINOLOGY

### COLLECTED ✓
```
Function Selectors:
- deposit(uint256): 0xb6b55f25
- withdraw(uint256): 0x2e1a7d4d
- getReward(): 0x3d18b912
- earned(): 0x96c55175
- execute(address,uint256,bytes): 0xb61d27f6
- collateralRatio(): 0x5d1ca631
- checkpoint(address): 0xc2c4c5c1

Event Signatures (need to collect):
- Deposit(address,uint256)
- Withdraw(address,uint256)
- RewardPaid(address,uint256)
- Liquidate(...)
```

### MISSING ✗
| Evidence | Needed For |
|----------|------------|
| All event topic0 hashes | Log filtering |
| Custom error selectors | Revert analysis |
| Packed encoding patterns | Exploit payload |

---

## 8. LOGS / RECEIPTS

### MISSING - CRITICAL ✗
| Evidence | Method | Purpose |
|----------|--------|---------|
| Recent Liquidate events | eth_getLogs with topic filter | Identify liquidation patterns |
| Recent Deposit/Withdraw events | eth_getLogs | Understand TVL flows |
| Oracle update events | eth_getLogs on priceOracle | Price update frequency |
| VoteSharing toggle events | eth_getLogs | Identify vulnerable accounts |
| Recent large transactions | eth_getLogs + analysis | Whale activity |

---

## 9. PROXY + UPGRADE STORAGE-SLOT STANDARDS

### COLLECTED ✓
```
EIP-1967 Implementation Slots Verified:
- Treasury: 0x360894a13ba1a3210667c828492db98dca3e2076cc3735a920a3ca505d382bbc
  → Value: 0x...dd8f6860f5a3eecd8b7a902df75cb7548387c224

- Market: 0x360894a13ba1a3210667c828492db98dca3e2076cc3735a920a3ca505d382bbc
  → Value: 0x...2c613d2c163247cd43fd05d6efc487c327d1b248

- Gauge: 0x360894a13ba1a3210667c828492db98dca3e2076cc3735a920a3ca505d382bbc
  → Value: 0x...72a6239f1651a4556f4c40fe97575885a195f535

Proxy Pattern: TransparentUpgradeableProxy (OpenZeppelin)
Admin Slot: 0xb53127684a568b3173ae13b9f8a6016e243e63b6e8ee1178d6a717850b5d6103
```

### MISSING ✗
| Evidence | Method |
|----------|--------|
| Admin addresses for each proxy | eth_getStorageAt(admin_slot) |
| Beacon slot if applicable | eth_getStorageAt(beacon_slot) |
| Upgrade history | Event logs |

---

## 10. JSON-RPC / NODE ACCESS

### AVAILABLE ✓
```
RPC Endpoints:
- Infura: https://mainnet.infura.io/v3/bfc7283659224dd6b5124ebbc2b14e2c
- Alchemy: https://eth-mainnet.g.alchemy.com/v2/pLXdY7rYRY10SH_UTLBGH

Archive Access: YES (Infura provides historical state)
```

### QUERIES NEEDED ✗
| Method | Target | Purpose |
|--------|--------|---------|
| eth_getStorageAt | All key slots | Current state snapshot |
| eth_getProof | Treasury, Gauge | Merkle proofs for state |
| eth_call | All view functions | Current computed values |
| eth_getLogs | Key events | Historical activity |
| debug_traceTransaction | Recent txs | Execution traces |

---

## 11. BYTECODE / COMPILATION ARTIFACTS

### COLLECTED ✓
```
Verified Contracts:
✓ StakingProxyERC20 - Etherscan verified
✓ TreasuryV2 - Etherscan verified
✓ WrappedTokenTreasuryV2 - Etherscan verified
✓ MarketV2 - Etherscan verified
✓ FxUSDShareableRebalancePool - Etherscan verified

Compiler Settings (from Etherscan):
- Solidity 0.8.20
- Optimizer: enabled, 200 runs
- EVM Version: Shanghai
```

### MISSING ✗
| Evidence | Purpose |
|----------|---------|
| Constructor arguments decoded | Initialization params |
| Linked library addresses | Dependency analysis |
| Metadata hash extraction | Source verification |

---

## 12. CANONICAL CHAIN OBJECTS (Blocks, Txs, Receipts)

### NEED TO COLLECT ✗
| Evidence | Method | Purpose |
|----------|--------|---------|
| Current block number | eth_blockNumber | State reference |
| Block at analysis time | eth_getBlockByNumber | State root, timestamp |
| Recent Treasury txs | eth_getTransactionsByAddress | Activity patterns |
| Recent Gauge txs | eth_getTransactionsByAddress | Liquidation history |
| Receipts for recent ops | eth_getTransactionReceipt | Actual gas used, logs |

---

## 13. CONTRACT DATA NOT IN STORAGE (Immutables)

### COLLECTED FROM SOURCE ✓
```
TreasuryV2 Immutables:
- baseToken (address) - embedded in bytecode
- fToken (address) - embedded in bytecode
- xToken (address) - embedded in bytecode
- baseTokenScale (uint256) - computed from decimals

MarketV2 Immutables:
- treasury (address) - embedded in bytecode
- baseToken (address) - from treasury
- fToken (address) - from treasury
- xToken (address) - from treasury
```

### MISSING ✗
| Evidence | Method |
|----------|--------|
| Extract immutables from bytecode | Parse PUSH instructions |
| Verify immutable values | Compare to known addresses |

---

## 14. FORK / CONFIGURATION

### COLLECTED ✓
```
Target Network: Ethereum Mainnet
Chain ID: 1
Current Fork: Shanghai/Cancun
EIP-1153 (Transient Storage): Available but not used
EIP-4844 (Blobs): Available but not relevant
```

---

## 15. SYSTEM CONTRACTS & PRECOMPILES

### RELEVANT ✓
```
Used Precompiles:
- ECRECOVER (0x01): Signature verification (if any)
- SHA256 (0x02): Potentially in oracle
- KECCAK256: Heavy use for slot computation

System Contracts:
- Not directly interacting with beacon roots
- Not using any EIP-4788 features
```

---

## 16. EXECUTION SEMANTICS (Call Sequences, Frames)

### COLLECTED ✓
```
Critical Call Chains:

CHAIN 1: User → StakingProxy → Gauge → Minter
  deposit() → gauge.deposit()
  getReward() → gauge.claim() → minter.mint()

CHAIN 2: StakingProxy.execute() → Gauge.acceptSharedVote()
  execute(gauge, 0, abi.encodeWithSelector(acceptSharedVote.selector, target))
  → gauge.acceptSharedVote(target)
  → storage write: getStakerVoteOwner[caller] = target

CHAIN 3: Liquidator → Gauge → Market → Treasury
  liquidate(amount, minOut)
  → _beforeLiquidate() checks collateralRatio
  → IFxMarket.redeem(fTokenIn, recipient)
  → Treasury.redeem(fTokenIn, 0, owner)
  → baseToken transfer

DELEGATECALL Context:
- StakingProxy clones: storage = clone, code = implementation
- All storage reads/writes happen on clone's storage
- msg.sender/msg.value preserved through delegatecall
```

### MISSING ✗
| Evidence | Purpose |
|----------|---------|
| Full call trace for liquidation | Understand exact execution |
| Gas limits at each call depth | Attack feasibility |
| Return data handling | Error propagation |

---

## 17. TRACE EVIDENCE

### NEED TO COLLECT ✗
| Evidence | Method | Purpose |
|----------|--------|---------|
| debug_traceTransaction for recent liquidations | Geth debug API | Liquidation mechanics |
| Call traces for getReward() | debug_traceCall | Reward claim flow |
| State diff for checkpoint() | prestateTracer | Boost update mechanics |
| Storage access patterns | structLogTracer | Slot access order |

---

## 18. PROOF & VERIFIABILITY

### NEED TO COLLECT ✗
| Evidence | Method | Purpose |
|----------|--------|---------|
| eth_getProof for Treasury | RPC | State commitment |
| Storage proofs for key slots | eth_getProof | Verifiable state |
| Account proofs | eth_getProof | Balance verification |

---

## 19. ORDERING, MEMPOOL, MEV EVIDENCE

### CRITICAL FOR ATTACK DESIGN ✗
| Evidence | Source | Purpose |
|----------|--------|---------|
| Oracle update tx patterns | Historical txs | Frontrun timing |
| Liquidation tx patterns | Historical txs | MEV opportunity |
| Private relay usage | Builder analysis | Competition |
| Bundle simulation | Flashbots API | Attack viability |

### KNOWN MEV VECTORS
```
1. Oracle Update Frontrunning:
   - Monitor pending oracle updates
   - Frontrun with position adjustment
   - Requires: mempool access or MEV relay

2. Liquidation MEV:
   - Monitor collateralRatio approaching threshold
   - JIT deposit before liquidation
   - Extract liquidation rewards
   - Requires: LIQUIDATOR_ROLE (blocked)

3. Checkpoint Manipulation:
   - Strategic checkpoint() calls
   - Optimize boost timing
   - Permissionless but low value
```

---

## 20. ACCOUNT ABSTRACTION

### STATUS: NOT DIRECTLY RELEVANT ✓
- Analyzed contracts use EOA/contract auth
- No ERC-4337 integration found
- No EIP-7702 delegation

---

## 21. BLOBS & DATA AVAILABILITY

### STATUS: NOT RELEVANT ✓
- Protocol operates on L1 only
- No rollup posting
- No blob usage

---

## 22. ROLLUP/L2 CROSS-DOMAIN

### STATUS: NOT RELEVANT ✓
- Analysis focused on mainnet
- No cross-chain bridges in scope

---

## 23. GOVERNANCE, ADMIN, UPGRADES

### COLLECTED ✓
```
Role Analysis:

TREASURY ROLES:
- DEFAULT_ADMIN_ROLE: Manages all other roles
- FX_MARKET_ROLE: Can call mint/redeem (only Market)
- SETTLE_WHITELIST_ROLE: Can call settle()
- PROTOCOL_INITIALIZER_ROLE: One-time init

GAUGE ROLES:
- LIQUIDATOR_ROLE: Can call liquidate()
- VE_SHARING_ROLE: Can toggle vote sharing
- WITHDRAW_FROM_ROLE: Can withdraw on behalf

MARKET ROLES:
- DEFAULT_ADMIN_ROLE: Update fees, ratios
- EMERGENCY_DAO_ROLE: Pause/unpause
```

### MISSING ✗
| Evidence | Method | Purpose |
|----------|--------|---------|
| Role holder addresses | hasRole() queries | Identify privileged actors |
| Timelock addresses | Admin slot + analysis | Upgrade delay |
| Recent governance txs | Event logs | Recent changes |
| Multisig configs | Safe API | Signer requirements |

---

## 24. OFF-CHAIN INPUTS (Oracles, Keepers)

### COLLECTED FROM SOURCE ✓
```
Oracle Dependencies:

1. IFxPriceOracleV2 (priceOracle in Treasury):
   - getPrice() returns (isValid, twap, minPrice, maxPrice)
   - TWAP anchoring prevents manipulation
   - Deviation check via isValid flag

2. IFxRateProvider (rateProvider in WrappedTokenTreasury):
   - getRate() returns eETH/ETH exchange rate
   - Used for wrapped/underlying conversion
   - Critical for value calculations

Keeper Dependencies:
- settle() called by SETTLE_WHITELIST
- harvest() permissionless
- checkpoint() permissionless
```

### MISSING - CRITICAL ✗
| Evidence | Method | Purpose |
|----------|--------|---------|
| priceOracle address | eth_call or storage | Oracle contract |
| rateProvider address | eth_call or storage | Rate contract |
| Oracle implementation analysis | Fetch source | Manipulation resistance |
| Oracle update frequency | Historical logs | Staleness window |
| Current oracle prices | eth_call | Divergence analysis |
| Historical price divergence | Log analysis | Attack window |

---

## EVIDENCE COLLECTION PRIORITY

### CRITICAL (Must have for attack chain):
1. ✗ priceOracle contract address and implementation
2. ✗ rateProvider contract address and implementation
3. ✗ Current collateralRatio value
4. ✗ Current oracle prices (twap, min, max)
5. ✗ LIQUIDATOR_ROLE holders
6. ✗ Recent liquidation event history
7. ✗ Vote sharing allowlist state

### HIGH (Needed for validation):
1. ✗ Full storage slot values for Treasury
2. ✗ Full storage slot values for Gauge
3. ✗ Execution traces for key functions
4. ✗ Gas cost estimates for attack sequences

### MEDIUM (Useful for optimization):
1. ✗ Historical oracle price divergence
2. ✗ MEV opportunity frequency
3. ✗ Checkpoint timing patterns

---

## NEXT STEPS

1. Execute critical evidence collection queries
2. Analyze oracle implementation for manipulation vectors
3. Check current vote sharing allowlist for exploitable state
4. Calculate exact slot addresses for key mappings
5. Build complete state snapshot
6. Design attack chain with full evidence support
