# Evidence Audit Against Complete Taxonomy
## Systematic Gap Analysis for SuperVault Attack Chain

---

## SECTION 1: ON-CHAIN STATE & ACCOUNT EVIDENCE

### 1.1 Global / World State Commitments

| Term | Status | Evidence |
|------|--------|----------|
| world state / global state | ✅ | Queried via eth_getStorageAt, eth_call |
| state | ✅ | Multiple storage slots read |
| state transition | ⚠️ PARTIAL | Need historical traces |
| state root | ❌ MISSING | Not queried block header |
| state trie (MPT) | ❌ MISSING | No trie proofs collected |
| Merkle proof / inclusion proof | ❌ MISSING | Need eth_getProof |
| witness | ❌ MISSING | No execution witnesses |
| state diff | ⚠️ PARTIAL | Compared current vs expected |
| reorg | ❌ N/A | Not relevant to static analysis |

### 1.2 Trie / Encoding Evidence

| Term | Status | Evidence |
|------|--------|----------|
| Merkle-Patricia Trie | ❌ MISSING | No raw trie data |
| RLP encoding | ❌ MISSING | Not decoded raw data |
| account key derivation | ✅ | keccak256(address) understood |
| storage key derivation | ✅ | Mapping slot computation verified |

### 1.3 Account-Level Evidence

| Contract | Address | Nonce | Balance | Code | Code Hash | Storage Root |
|----------|---------|-------|---------|------|-----------|--------------|
| Pendle SY Proxy | 0x4d654f...fee | ❌ | ❌ | ⚠️ | ❌ | ❌ |
| Pendle SY Impl | 0xb9cdea...9c4 | ❌ | ❌ | ✅ | ❌ | ❌ |
| SuperVault | 0xf6ebea...947 | ❌ | ❌ | ✅ | ❌ | ❌ |
| Strategy | 0x41a9eb...1dd | ❌ | ❌ | ✅ | ❌ | ❌ |
| Aggregator | 0x10ac0b...698 | ❌ | ❌ | ✅ | ❌ | ❌ |
| Escrow | 0x11c016...27b | ❌ | ❌ | ❌ | ❌ | ❌ |

### 1.4 Storage Evidence

| Contract | Slots Read | Storage Proof | Account Proof |
|----------|------------|---------------|---------------|
| SuperVault | Slots 0-3 | ❌ MISSING | ❌ MISSING |
| Strategy | Slots 0-16 | ❌ MISSING | ❌ MISSING |
| Aggregator | Slots 0-20 | ❌ MISSING | ❌ MISSING |

**GAP**: Need `eth_getProof` for cryptographic verification

---

## SECTION 2: STORAGE PRIMITIVES

### 2.1 Fundamental Units - ALL VERIFIED ✅

| Term | Evidence |
|------|----------|
| slot | ✅ 256-bit indices used |
| word | ✅ 32-byte values read |
| offset | ✅ Packed variables decoded (slot 1: vault + decimals) |
| packed storage | ✅ Observed in Strategy slot 1 |
| mask/shift | ✅ Understood from packed reading |

### 2.2 Solidity Storage Layout - VERIFIED ✅

| Contract | Layout Mapped | Encoding Types |
|----------|--------------|----------------|
| SuperVault | ✅ Slots 0-4 | inplace, mapping |
| Strategy | ✅ Slots 0-16+ | inplace, mapping, dynamic_array |
| Aggregator | ⚠️ Partial | inplace, mapping |

### 2.3 Layout Rule Evidence

| Term | Status | Notes |
|------|--------|-------|
| sequential slot assignment | ✅ | Verified in all contracts |
| inheritance linearization | ⚠️ | Not fully traced |
| struct packing | ✅ | FeeConfig spans 3 slots |
| storage collision | ✅ | Checked proxy patterns |
| storage gap | ✅ | __gap observed in Strategy |

---

## SECTION 3: DERIVED STORAGE ADDRESSING

### 3.1 Mappings

| Mapping | Base Slot | Location Formula | Verified |
|---------|-----------|------------------|----------|
| superVaultState | ~17+ | keccak256(controller . slot) | ⚠️ Not probed |
| yieldSources | 13 | keccak256(source . 13) | ⚠️ Not probed |
| _strategyData | ~? | keccak256(strategy . slot) | ⚠️ Not probed |
| isOperator | ~? | keccak256(operator . keccak256(owner . slot)) | ⚠️ Not probed |

**GAP**: Need to probe specific mapping entries with known keys

### 3.2 Dynamic Arrays

| Array | Length Slot | Data Start | Verified |
|-------|-------------|------------|----------|
| yieldSourcesList | 14 | keccak256(14) | ⚠️ Length only (21) |

### 3.3 EnumerableSet

| Set | Base Slot | Structure | Verified |
|-----|-----------|-----------|----------|
| yieldSourcesList | 14-15 | _inner (array + mapping) | ⚠️ Partial |

---

## SECTION 4: DATA LOCATIONS DURING EXECUTION

| Location | Evidence |
|----------|----------|
| stack | ❌ No opcode traces |
| memory | ❌ No opcode traces |
| calldata | ✅ Function selectors used |
| returndata | ✅ eth_call results decoded |
| code | ✅ Source verified |

**GAP**: Need debug_traceTransaction for execution-level evidence

---

## SECTION 5: TRANSIENT STORAGE (EIP-1153)

| Term | Status | Notes |
|------|--------|-------|
| TLOAD/TSTORE usage | ❌ UNKNOWN | Need to check if contracts use transient storage |
| Transaction-scoped state | ❌ NOT CHECKED | |

**GAP**: Search source code for transient storage usage

---

## SECTION 6: OPCODE-LEVEL EVIDENCE

### Critical Opcodes to Verify in Code

| Opcode | Used | Evidence |
|--------|------|----------|
| SLOAD | ✅ | Storage reads throughout |
| SSTORE | ✅ | Storage writes in state changes |
| DELEGATECALL | ✅ | Proxy pattern |
| CALL | ✅ | External calls to strategy, aggregator |
| STATICCALL | ⚠️ | View functions |
| KECCAK256 | ✅ | Slot computation, Merkle proofs |
| SELFDESTRUCT | ❌ NOT CHECKED | Post-Cancun semantics |

**GAP**: Need bytecode disassembly for opcode inventory

---

## SECTION 7: ABI & DECODING EVIDENCE

### 7.1 Function Selectors Verified

| Function | Selector | Contract | Verified |
|----------|----------|----------|----------|
| totalSupply() | 0x18160ddd | SuperVault | ✅ |
| totalAssets() | 0x01e1d114 | SuperVault | ✅ |
| exchangeRate() | 0x3ba0b9a9 | Pendle SY | ✅ |
| balanceOf(address) | 0x70a08231 | ERC20 | ✅ |
| deposit(uint256,address) | ❌ | SuperVault | Not probed |
| requestRedeem(...) | ❌ | SuperVault | Not probed |
| executeHooks(...) | ❌ | Strategy | Not probed |
| forwardPPS(...) | ❌ | Aggregator | Not probed |

### 7.2 Event Signatures

| Event | Signature Hash | Verified |
|-------|----------------|----------|
| Deposit | ❌ | Need to compute |
| RedeemRequest | ❌ | Need to compute |
| HooksExecuted | ❌ | Need to compute |
| PerformanceFeeSkimmed | ❌ | Need to compute |

**GAP**: Need full event signature inventory for log analysis

---

## SECTION 8: LOGS / RECEIPTS EVIDENCE

| Evidence Type | Status | Notes |
|---------------|--------|-------|
| Historical logs | ❌ MISSING | Need eth_getLogs |
| Transaction receipts | ❌ MISSING | Need historical tx analysis |
| logsBloom | ❌ MISSING | Not queried |

**GAP**: Query historical events for:
- Recent fee skims
- Recent fulfillments
- PPS updates
- Manager changes

---

## SECTION 9: PROXY / UPGRADE EVIDENCE

### 9.1 Proxy Patterns Identified

| Contract | Pattern | Implementation Slot | Admin Slot |
|----------|---------|---------------------|------------|
| Pendle SY | TransparentUpgradeable | ✅ 0xb9cdea...9c4 | ✅ 0xa28c08...e64 |
| SuperVault | Non-proxy (direct) | N/A | N/A |
| Strategy | Non-proxy (direct) | N/A | N/A |

### 9.2 EIP-1967 Slots Verified

| Slot | Name | Value |
|------|------|-------|
| 0x360894...bbc | Implementation | ✅ |
| 0xb53127...103 | Admin | ✅ |
| 0xa3f0ad...d50 | Beacon | ❌ Not checked |

### 9.3 Upgrade Safety

| Check | Status |
|-------|--------|
| Storage collision analysis | ⚠️ Partial |
| Initializer protection | ✅ _disableInitializers() used |
| Upgrade authority | ⚠️ Admin address identified |

---

## SECTION 10: JSON-RPC / NODE ACCESS

### 10.1 Methods Used

| Method | Used | Purpose |
|--------|------|---------|
| eth_getStorageAt | ✅ | Storage slot reads |
| eth_call | ✅ | View function calls |
| eth_getCode | ❌ | Not used directly |
| eth_getProof | ❌ MISSING | Cryptographic proofs |
| eth_getTransactionByHash | ❌ | Historical tx |
| eth_getTransactionReceipt | ❌ | Historical receipts |
| eth_getLogs | ❌ MISSING | Event history |
| eth_getBlockByNumber | ❌ | Block data |
| debug_traceTransaction | ❌ MISSING | Execution traces |

### 10.2 Block Tags Used

| Tag | Used |
|-----|------|
| latest | ✅ |
| pending | ❌ |
| safe | ❌ |
| finalized | ❌ |

---

## SECTION 11: BYTECODE / COMPILATION EVIDENCE

| Evidence | Status |
|----------|--------|
| Runtime bytecode | ✅ Via Etherscan source |
| Creation bytecode | ❌ Not retrieved |
| Constructor arguments | ❌ Not decoded |
| Metadata hash | ❌ Not extracted |
| Compiler version | ✅ 0.8.30 (from source) |
| Optimizer settings | ⚠️ Not verified |

---

## SECTION 12: CANONICAL OBJECTS

### 12.1 Block Header Evidence

| Field | Collected |
|-------|-----------|
| stateRoot | ❌ |
| transactionsRoot | ❌ |
| receiptsRoot | ❌ |
| timestamp | ❌ |
| baseFeePerGas | ❌ |
| blobGasUsed | ❌ |

**GAP**: Need eth_getBlockByNumber for current block context

### 12.2 Transaction Evidence

| Field | Collected |
|-------|-----------|
| Recent txs to contracts | ❌ MISSING |
| Gas patterns | ❌ MISSING |
| Access lists | ❌ MISSING |

---

## SECTION 13: TRANSACTION ENVELOPE EVIDENCE

| Tx Type | Relevant | Evidence |
|---------|----------|----------|
| Legacy (0x00) | ✅ | Most interactions |
| EIP-1559 (0x02) | ✅ | Modern txs |
| Blob (0x03) | ❌ | Not relevant |
| Set-code (0x04) | ⚠️ | Could affect EOA behavior |

---

## SECTION 14: FORK / CHAIN CONFIG

| Evidence | Status |
|----------|--------|
| chainId | ✅ 1 (Mainnet) |
| Fork rules | ✅ Post-Cancun assumed |
| eth_config | ❌ Not queried |

---

## SECTION 15: PRECOMPILES & SYSTEM CONTRACTS

| Precompile | Used by Contracts | Verified |
|------------|-------------------|----------|
| ECRECOVER (0x01) | Signature validation | ⚠️ |
| KECCAK256 | Everywhere | ✅ |
| MODEXP (0x05) | ❌ | Not checked |
| KZG (0x0A) | ❌ | Not relevant |

---

## SECTION 16: GAS / ACCESS / METERING

| Evidence | Status |
|----------|--------|
| Gas costs | ❌ Not estimated |
| Warm vs cold | ❌ Not analyzed |
| Access lists | ❌ Not generated |
| SSTORE cost model | ❌ Not modeled |

**GAP**: Need gas analysis for attack profitability

---

## SECTION 17: TRACING EVIDENCE

| Trace Type | Status | Priority |
|------------|--------|----------|
| Opcode trace | ❌ MISSING | HIGH |
| Call trace | ❌ MISSING | HIGH |
| State diff trace | ❌ MISSING | MEDIUM |
| Prestate trace | ❌ MISSING | MEDIUM |

**GAP**: Critical for understanding execution flow

---

## SECTION 18: PROOFS / WITNESSES

| Evidence | Status |
|----------|--------|
| eth_getProof | ❌ MISSING |
| accountProof | ❌ MISSING |
| storageProof | ❌ MISSING |

**GAP**: Need cryptographic proofs for verification

---

## SECTION 19: MEMPOOL / ORDERING / MEV

| Evidence | Status | Notes |
|----------|--------|-------|
| Mempool monitoring | ❌ | Would need real-time |
| Bundle patterns | ❌ | Private orderflow |
| Historical MEV | ⚠️ | Could query Flashbots |

---

## SECTION 20: ACCOUNT ABSTRACTION

| Evidence | Status |
|----------|--------|
| ERC-4337 usage | ❌ NOT CHECKED |
| EIP-7702 delegations | ❌ NOT CHECKED |

---

## SECTION 21: BLOBS / DATA AVAILABILITY

Not relevant for this analysis (no L2/blob interactions)

---

## SECTION 22: CROSS-DOMAIN / L2 / BRIDGE

| Evidence | Status | Notes |
|----------|--------|-------|
| Bridge integrations | ⚠️ | SuperVault is L1-only |
| Cross-chain exposure | ❌ | Not analyzed |

---

## SECTION 23: GOVERNANCE / ADMIN

| Evidence | Status | Details |
|----------|--------|---------|
| Owner/admin | ✅ | SUPER_GOVERNOR identified |
| Timelock | ✅ | 15min hooks, 7d fees |
| Multisig | ❌ UNKNOWN | Need to check admin address |
| Pause mechanism | ✅ | isStrategyPaused() |
| Role hierarchy | ✅ | Manager tiers documented |

---

## SECTION 24: OFF-CHAIN / EXTERNAL INPUT

### 24.1 Oracle Evidence

| Oracle Aspect | Status |
|---------------|--------|
| PPS Oracle identity | ❌ UNKNOWN |
| Update frequency | ❌ UNKNOWN |
| Update mechanism | ✅ forwardPPS() |
| Staleness threshold | ✅ 86400s (1 day) |

### 24.2 Signature Evidence

| Pattern | Used | Verified |
|---------|------|----------|
| EIP-712 | ✅ | authorizeOperator |
| Permit | ⚠️ | Not checked |
| Merkle proofs | ✅ | Hook validation |

---

## CRITICAL GAPS SUMMARY

### HIGH PRIORITY (Required for Attack Validation)

1. **eth_getProof** - Cryptographic verification of storage
2. **eth_getLogs** - Historical events (fee skims, fulfillments)
3. **debug_traceTransaction** - Execution traces
4. **Manager identity** - Who controls the strategy?
5. **PPS Oracle identity** - Who can update prices?
6. **Gas estimation** - Attack profitability calculation

### MEDIUM PRIORITY (Enhances Analysis)

7. **Yield source list** - Where is $16.7M deployed?
8. **Historical transactions** - Past behavior patterns
9. **Block header data** - Current chain context
10. **Event signatures** - Log decoding capability

### LOW PRIORITY (Completeness)

11. **Bytecode metadata** - Compilation verification
12. **Access list generation** - Gas optimization
13. **Mempool monitoring** - Real-time attack execution
14. **Cross-chain exposure** - Additional attack surface

---

---

## SUPPLEMENTAL EVIDENCE COLLECTED

### Block Context (Chain State)

```
Block Number: 24,384,031
Timestamp: 2026-02-04T14:16:59Z
State Root: 0xf8958a8fee2da625a9558cb51c2ba1551b5b0dd88c67f2ebb05488d125878882
Base Fee: 0.4180 Gwei
Gas Used: 24,005,201 (40.0% of limit)
Gas Limit: 60,000,000
Blob Gas Used: 1,048,576
```

### eth_getProof Results (Cryptographic Verification)

**SuperVault (0xf6ebea08a0dfd44825f67fa9963911c81be2a947)**:
```
Balance: 0x0
Nonce: 0x1
CodeHash: 0x938d8f84e61a99909fc2ba224549efcb3fb154f217184add1f3c401fe917465d
StorageHash: 0x97346e36ce322266101cd17a01904ea635b17a7fdec560218a3a007b20bf6b89
Account Proof Nodes: 9
```

### Historical Event Count

```
Strategy Contract Events: 5,905+ logs
(From block 0x13A0000 to latest)
```

---

## FINAL GAP ASSESSMENT

### COLLECTED ✅

1. Account proofs (eth_getProof)
2. Storage slot values
3. Block header context
4. EIP-1967 proxy slots
5. Contract source code
6. Live state values (PPS, TVL, HWM)
7. Pendle market data
8. Admin/governance structure

### STILL MISSING ⚠️

1. **Manager identity** - Need to trace contract creation or query aggregator mapping
2. **PPS Oracle identity** - Who calls forwardPPS()
3. **Execution traces** - debug_traceTransaction not available via public RPC
4. **Detailed event decoding** - Need event signatures computed
5. **Yield source addresses** - Where $16.7M is deployed

### NOT REQUIRED ❌

1. Mempool monitoring (real-time only)
2. Private orderflow data (not accessible)
3. L2/cross-chain evidence (L1-only system)

---

*Audit completed against comprehensive evidence taxonomy*
*Supplemental evidence collected: Feb 4, 2026*
