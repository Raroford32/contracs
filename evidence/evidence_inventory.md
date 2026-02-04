# Evidence Inventory for Contract 0xa7569A44f348d3D70d8ad5889e50F78E33d80D35

## Status Legend
- ✅ COLLECTED
- ⚠️ PARTIAL
- ❌ MISSING (CRITICAL)
- 🔄 IN PROGRESS

---

## 1. ON-CHAIN STATE & ACCOUNT DATA

### Contract Addresses
| Item | Status | Value |
|------|--------|-------|
| Proxy Address | ✅ | `0xa7569A44f348d3D70d8ad5889e50F78E33d80D35` |
| Implementation Address | ✅ | `0xfb2ebdedc38a7d19080e44ab1d621bc9afad0695` |
| Base Asset (USDC) | ✅ | `0xa0b86991c6218b36c1d19d4a2e9eb0ce3606eb48` |
| SystemRegistry | ❌ | NEED TO QUERY |
| AccessController | ❌ | NEED TO QUERY |
| Destination Vaults | ❌ | NEED TO QUERY - CRITICAL |
| Oracle Addresses | ❌ | NEED TO QUERY - CRITICAL |
| Fee Sink | ❌ | NEED TO QUERY |
| Rewarder | ❌ | NEED TO QUERY |

### Account State
| Item | Status | Value |
|------|--------|-------|
| Proxy Nonce | ❌ | NEED TO QUERY |
| Proxy Balance (ETH) | ❌ | NEED TO QUERY |
| USDC Balance | ⚠️ | ~$20.2M (from totalAssets, not direct query) |
| Code Hash | ❌ | NEED TO QUERY |
| Storage Root | ❌ | NEED TO QUERY (eth_getProof) |

---

## 2. STORAGE PRIMITIVES

### ERC-1967 Proxy Slots
| Slot | Purpose | Status | Value |
|------|---------|--------|-------|
| `0x360894...e1234` | Implementation | ✅ | `0xfb2ebdedc38a7d19080e44ab1d621bc9afad0695` |
| `0xb53127...42dc1` | Admin | ❌ | NEED TO QUERY |
| `0xa3f0ad...b4bc2` | Beacon | ❌ | NEED TO QUERY |

### AutopoolStorage Namespace
- Uses ERC-7201 style namespaced storage
- Base slot: `keccak256("tokemak.autopool.storage") - 1`
| Variable | Relative Offset | Status | Value |
|----------|-----------------|--------|-------|
| assetBreakdown.totalIdle | +0 | ❌ | NEED TO QUERY |
| assetBreakdown.totalDebt | +1 | ❌ | NEED TO QUERY |
| assetBreakdown.totalDebtMin | +2 | ❌ | NEED TO QUERY |
| assetBreakdown.totalDebtMax | +3 | ❌ | NEED TO QUERY |
| destinations (EnumerableSet) | +? | ❌ | NEED TO QUERY |
| destinationInfo mapping | +? | ❌ | NEED TO QUERY |
| withdrawalQueue | +? | ❌ | NEED TO QUERY |
| debtReportQueue | +? | ❌ | NEED TO QUERY |
| shutdown | +? | ❌ | NEED TO QUERY |
| token.totalSupply | +? | ⚠️ | ~18.9M (from function call) |
| profitUnlockSettings | +? | ❌ | NEED TO QUERY |
| feeSettings | +? | ❌ | NEED TO QUERY |

---

## 3. DERIVED ADDRESSING

### Mappings to Query
| Mapping | Key | Status | Notes |
|---------|-----|--------|-------|
| destinationInfo[addr] | Each destination vault | ❌ | Need dest addresses first |
| token.balances[addr] | Key holders | ❌ | Need holder list |
| token.allowances[owner][spender] | Key pairs | ❌ | Need to identify |

### Dynamic Arrays/Lists
| Array | Status | Contents |
|-------|--------|----------|
| destinations (set) | ❌ | NEED TO QUERY |
| withdrawalQueue (linked list) | ❌ | NEED TO QUERY |
| debtReportQueue (linked list) | ❌ | NEED TO QUERY |
| removalQueue (set) | ❌ | NEED TO QUERY |
| hooks array | ❌ | NEED TO QUERY |

---

## 4. SOURCE CODE EVIDENCE

### AutopoolETH Implementation
| File | Status | Key Findings |
|------|--------|--------------|
| AutopoolETH.sol | ✅ | Main contract, ERC4626 vault |
| AutopoolDebt.sol | ✅ | Debt tracking, rebalance logic |
| AutopoolFees.sol | ⚠️ | Fee calculation (partial) |
| Autopool4626.sol | ✅ | Deposit/withdraw/share conversion |
| AutopoolToken.sol | ⚠️ | Token operations (partial) |
| AutopoolDestinations.sol | ⚠️ | Destination management (partial) |
| AutopoolStrategyHooks.sol | ✅ | Hook system |
| AutopoolState.sol | ⚠️ | State struct definitions (partial) |

### Destination Vault Interface
| Function | Status | Security Notes |
|----------|--------|----------------|
| getRangePricesLP() | ✅ | Returns (spotPrice, safePrice, isSpotSafe) |
| getUnderlyerCeilingPrice() | ✅ | **DOCUMENTED AS ATTACKABLE** |
| getUnderlyerFloorPrice() | ⚠️ | Mentioned but not fully analyzed |
| depositUnderlying() | ✅ | Standard deposit |
| withdrawUnderlying() | ✅ | Standard withdraw |
| balanceOf() | ✅ | Share balance |
| rewarder() | ⚠️ | Reward distribution |

### CRITICAL: Destination Vault Implementation
| Item | Status | Notes |
|------|--------|-------|
| Actual implementation code | ❌ | **CRITICAL - NEED TO FETCH** |
| Price oracle source | ❌ | **CRITICAL - NEED TO IDENTIFY** |
| LP token mechanics | ❌ | **CRITICAL - NEED TO UNDERSTAND** |

---

## 5. TRANSACTION EVIDENCE

### Recent Transactions
| Hash | Function | From | Status |
|------|----------|------|--------|
| TBD | updateDebtReporting | 0x1a65e4844... | ❌ NEED TRACES |
| TBD | approve | Various | ❌ NEED TRACES |
| TBD | flashRebalance | ? | ❌ NEED TO FIND |

### Historical Events
| Event | Status | Notes |
|-------|--------|-------|
| Nav events | ❌ | Need to query |
| RebalanceStarted | ❌ | Need to query |
| RebalanceCompleted | ❌ | Need to query |
| DestinationDebtReporting | ❌ | Need to query |
| Deposit/Withdraw | ❌ | Need to query |

---

## 6. EXECUTION TRACES

### Required Traces
| Transaction Type | Status | Purpose |
|-----------------|--------|---------|
| flashRebalance | ❌ | Understand callback flow |
| updateDebtReporting | ❌ | Understand price updates |
| deposit | ❌ | Understand share minting |
| withdraw/redeem | ❌ | Understand share burning |

### Call Graph Evidence
| Path | Status | Notes |
|------|--------|-------|
| Autopool → DestinationVault | ❌ | Need trace |
| Autopool → Oracle | ❌ | Need trace |
| Autopool → Hooks | ❌ | Need trace |
| Rebalance callback flow | ⚠️ | Understood from code, need live trace |

---

## 7. ORACLE/PRICE EVIDENCE

### Price Sources
| Item | Status | Value |
|------|--------|-------|
| Root Price Oracle address | ❌ | NEED TO QUERY |
| Oracle type (Chainlink, TWAP, etc.) | ❌ | NEED TO IDENTIFY |
| Price staleness thresholds | ❌ | NEED TO QUERY |
| Historical price data | ❌ | NEED TO COLLECT |

### Price Safety Mechanics
| Check | Location | Status |
|-------|----------|--------|
| isSpotSafe | getRangePricesLP() | ✅ Documented |
| Price safety in rebalance | _handleRebalanceIn/Out | ✅ Reverts if unsafe |
| Price safety in debt reporting | updateDebtReporting | ✅ **CONTINUES IF UNSAFE** |
| Price staleness check | totalAssetsTimeChecked | ✅ 1 day threshold |

---

## 8. ACCESS CONTROL EVIDENCE

### Role Holders
| Role | Status | Address |
|------|--------|---------|
| SOLVER | ❌ | NEED TO QUERY |
| AUTO_POOL_REPORTING_EXECUTOR | ⚠️ | 0x1a65e4844... (from tx) |
| AUTO_POOL_FEE_UPDATER | ❌ | NEED TO QUERY |
| AUTO_POOL_MANAGER | ❌ | NEED TO QUERY |
| STRATEGY_HOOK_CONFIGURATION | ❌ | NEED TO QUERY |
| TOKEN_RECOVERY_MANAGER | ❌ | NEED TO QUERY |

### AccessController
| Item | Status | Notes |
|------|--------|-------|
| AccessController address | ❌ | NEED FROM SystemRegistry |
| Role assignments | ❌ | NEED TO QUERY |
| Admin/owner | ❌ | NEED TO QUERY |

---

## 9. ECONOMIC PARAMETERS

### Fee Settings
| Parameter | Status | Value |
|-----------|--------|-------|
| streamingFeeBps | ❌ | NEED TO QUERY |
| periodicFeeBps | ❌ | NEED TO QUERY |
| feeSink | ❌ | NEED TO QUERY |
| profitUnlockPeriod | ⚠️ | 86400 (from init, need confirm) |
| FEE_DIVISOR | ✅ | 10000 |

### Debt Parameters
| Parameter | Status | Value |
|-----------|--------|-------|
| MAX_DEBT_REPORT_AGE_SECONDS | ✅ | 86400 (1 day) |
| BASE_ASSET_INIT_DEPOSIT | ✅ | 100,000 |

---

## 10. CRITICAL GAPS FOR ATTACK DESIGN

### Must Have Before Attack Chain Design:
1. ❌ Destination vault addresses and their source code
2. ❌ Oracle implementation details
3. ❌ Actual storage state (idle, debt, min, max)
4. ❌ Trace of at least one flashRebalance execution
5. ❌ Price manipulation feasibility (LP pool depth)
6. ❌ Historical price divergence data

### Nice to Have:
1. ❌ Full role holder mapping
2. ❌ Hook configuration
3. ❌ Historical rebalance patterns
4. ❌ MEV/bundle analysis

---

## Evidence Collection Priority Queue

1. **HIGHEST**: Query destination vaults via getDestinations()
2. **HIGHEST**: Fetch destination vault source code
3. **HIGH**: Query SystemRegistry for oracle addresses
4. **HIGH**: Get storage state for assetBreakdown
5. **HIGH**: Find and trace a flashRebalance transaction
6. **MEDIUM**: Query all role holders
7. **MEDIUM**: Get historical events
8. **LOWER**: Full storage dump

