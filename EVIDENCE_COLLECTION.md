# Complete Evidence Collection for SuperVault Attack Chain
## Systematic Documentation Following Evidence Taxonomy

---

## 1. ON-CHAIN STATE & ACCOUNT EVIDENCE

### 1.1 Contract Accounts (Verified)

| Role | Address | Type | Verified |
|------|---------|------|----------|
| Pendle SY Proxy | 0x4d654f255d54637112844bd8802b716170904fee | TransparentUpgradeableProxy | ✓ |
| Pendle SY Implementation | 0xb9cdea29f7f976ce1a50944f3b6d0569ee88d9c4 | PendleERC4626NoRedeemWithAdapterSY | ✓ |
| Pendle SY Admin | 0xa28c08f165116587d4f3e708743b4dee155c5e64 | Proxy Admin | ✓ |
| SuperVault | 0xf6ebea08a0dfd44825f67fa9963911c81be2a947 | SuperVault (ERC4626+ERC7540) | ✓ |
| Strategy | 0x41a9eb398518d2487301c61d2b33e4e966a9f1dd | SuperVaultStrategy | ✓ |
| Aggregator | 0x10ac0b33e1c4501cf3ec1cb1ae51ebfdbd2d4698 | SuperVaultAggregator | ✓ |
| Escrow | 0x11c016dfb1745a81587e5e3fa8fc75f5693f427b | SuperVaultEscrow | ✓ |
| Pendle Market | 0x3d83a85e0b0fe9cc116a4efc61bb29cb29c3cb9a | PendleMarket (AMM) | ✓ |
| PT Token | 0x5d99ff7bcd32c432cbc07fbb0a593ef4cc9d019d | PT-superUSDC-30APR2026 | ✓ |
| YT Token | 0xb34c5b00c62dc45bfc63d640bf4e80fcf2ececeb | YT-superUSDC-30APR2026 | ✓ |
| USDC | 0xa0b86991c6218b36c1d19d4a2e9eb0ce3606eb48 | ERC20 (Circle) | ✓ |

### 1.2 EIP-1967 Proxy Slots (Verified On-Chain)

**Pendle SY Proxy (0x4d654f255d54637112844bd8802b716170904fee):**
```
Implementation Slot (0x360894...bbc): 0xb9cdea29f7f976ce1a50944f3b6d0569ee88d9c4
Admin Slot (0xb53127...103): 0xa28c08f165116587d4f3e708743b4dee155c5e64
```

---

## 2. STORAGE PRIMITIVES & SLOT MAPPINGS

### 2.1 SuperVault Storage Layout

```solidity
// Slot 0: share (address) - packed
// Evidence: 0x000000000000000000000000f6ebea08a0dfd44825f67fa9963911c81be2a947
share = 0xf6ebea08a0dfd44825f67fa9963911c81be2a947 (self-reference)

// Slot 1: _asset (IERC20) + _underlyingDecimals (uint8) - packed
// Evidence: 0x000000000000000000000006a0b86991c6218b36c1d19d4a2e9eb0ce3606eb48
_asset = 0xa0b86991c6218b36c1d19d4a2e9eb0ce3606eb48 (USDC)
_underlyingDecimals = 0x06 = 6

// Slot 2: strategy (ISuperVaultStrategy)
// Evidence: 0x00000000000000000000000041a9eb398518d2487301c61d2b33e4e966a9f1dd
strategy = 0x41a9eb398518d2487301c61d2b33e4e966a9f1dd

// Slot 3: escrow (address)
// Evidence: 0x00000000000000000000000011c016dfb1745a81587e5e3fa8fc75f5693f427b
escrow = 0x11c016dfb1745a81587e5e3fa8fc75f5693f427b

// Slot 4: PRECISION (uint256)
// Evidence: 0x00000000000000000000000000000000000000000000000000000000000f4240
PRECISION = 1,000,000 (10^6 for USDC)
```

### 2.2 SuperVaultStrategy Storage Layout

```solidity
// Slot 0: PRECISION
// Evidence: 0x00000000000000000000000000000000000000000000000000000000000f4240
PRECISION = 1,000,000

// Slot 1: _vault (address, 20 bytes) + _vaultDecimals (uint8, 1 byte) + gap (11 bytes)
// Evidence: 0x000000000000000000000006f6ebea08a0dfd44825f67fa9963911c81be2a947
_vault = 0xf6ebea08a0dfd44825f67fa9963911c81be2a947
_vaultDecimals = 6

// Slot 2: _asset (IERC20)
// Evidence: 0x000000000000000000000000a0b86991c6218b36c1d19d4a2e9eb0ce3606eb48
_asset = 0xa0b86991c6218b36c1d19d4a2e9eb0ce3606eb48 (USDC)

// Slot 3: feeConfig.performanceFeeBps
// Evidence: 0x00000000000000000000000000000000000000000000000000000000000003e8
performanceFeeBps = 1000 (10% = 1000 bps)

// Slot 4: feeConfig.managementFeeBps
// Evidence: 0x0000000000000000000000000000000000000000000000000000000000000000
managementFeeBps = 0 (no entry fee)

// Slot 5: feeConfig.recipient
// Evidence: 0x0000000000000000000000006fcc6a6a825fc14e6e56fd14978fc6b97acb5d15
recipient = 0x6fcc6a6a825fc14e6e56fd14978fc6b97acb5d15

// Slot 12 (0xc): ppsExpiration
// Evidence: 0x0000000000000000000000000000000000000000000000000000000000015180
ppsExpiration = 86400 seconds = 1 day

// Slot 14 (0xe): yieldSourcesList.length (EnumerableSet)
// Evidence: 0x0000000000000000000000000000000000000000000000000000000000000015
yieldSourcesList.length = 21 yield sources

// Slot 16 (0x10): vaultHwmPps
// Evidence: 0x00000000000000000000000000000000000000000000000000000000000f4240
vaultHwmPps = 1,000,000 (1.0 in 6 decimals) = Initial HWM
```

### 2.3 Aggregator Storage Layout

```solidity
// Slot 11 (0xb): _globalHooksRoot
// Evidence: 0x1186475477f3814002fd1308a19653f9118b723a7c3f800ea59f65dfaa74c1cf
globalHooksRoot = 0x1186475477f3814002fd1308a19653f9118b723a7c3f800ea59f65dfaa74c1cf

// Slot 10 (0xa): _hooksRootUpdateTimelock
// Evidence: 0x0000000000000000000000000000000000000000000000000000000000000384
_hooksRootUpdateTimelock = 900 seconds = 15 minutes
```

---

## 3. DERIVED ADDRESSING (MAPPINGS & DYNAMIC STORAGE)

### 3.1 Strategy superVaultState Mapping

```solidity
// Base slot for mapping: slot X (after EnumerableSet)
// Mapping: mapping(address controller => SuperVaultState state)

// SuperVaultState struct:
struct SuperVaultState {
    uint256 pendingRedeemRequest;      // +0
    uint256 averageRequestPPS;         // +1
    uint256 maxWithdraw;               // +2
    uint256 averageWithdrawPrice;      // +3
    uint256 claimableCancelRedeemRequest; // +4
    bool pendingCancelRedeemRequest;   // +5
    uint16 redeemSlippageBps;          // +5 (packed)
}

// Slot derivation: keccak256(h(controller) . baseSlot)
```

### 3.2 Aggregator _strategyData Mapping

```solidity
// mapping(address strategy => StrategyData data)
// StrategyData contains:
// - mainManager
// - ppsData (storedPPS, lastUpdateTimestamp)
// - managerHooksRoot
// - hooksRootVetoed
// - paused
// - secondaryManagers (EnumerableSet)
```

---

## 4. LIVE STATE VALUES (Block Latest)

### 4.1 SuperVault ERC4626 State

```
totalSupply: 16,590,587.715602 shares
totalAssets: 16,707,020.460190 USDC
Implied PPS: 1.007018
```

### 4.2 Pendle SY State

```
totalSupply: 1,085,370.055927 SY tokens
exchangeRate: 1.007018 (matches SuperVault PPS exactly)
```

### 4.3 Fee Configuration

```
Performance Fee: 10% (1000 bps)
Management Fee: 0% (0 bps)
Fee Recipient: 0x6fcc6a6a825fc14e6e56fd14978fc6b97acb5d15
```

### 4.4 High Water Mark State

```
vaultHwmPps: 1.000000 (initial HWM)
currentPPS: 1.007018
Unrealized profit above HWM: 0.7018%
Profit = (1.007018 - 1.0) * 16,590,587 = ~116,432 USDC
```

### 4.5 USDC Balances

```
SuperVault: 0.00 USDC (funds deployed to yield sources)
Strategy: 0.00 USDC
Escrow: 0.00 USDC (no pending withdrawals in escrow)
Pendle SY: 0.00 USDC
Pendle Market: 0.00 USDC
```

---

## 5. CALL SEMANTICS & DELEGATION PATTERNS

### 5.1 Deposit Flow (DELEGATECALL Context)

```
User → SuperVault.deposit(assets, receiver)
    ├─ CALL: _asset.safeTransferFrom(user, strategy, assets)
    ├─ CALL: strategy.handleOperations4626Deposit(receiver, assets)
    │       ├─ Reads: aggregator.getPPS() [via SUPER_GOVERNOR]
    │       ├─ Reads: aggregator.isStrategyPaused()
    │       ├─ Reads: aggregator.isPPSStale()
    │       ├─ Computes: shares = assets * PRECISION / pps
    │       └─ Returns: shares
    └─ MINT: _mint(receiver, shares)
```

### 5.2 Redeem Request Flow

```
User → SuperVault.requestRedeem(shares, controller, owner)
    ├─ CHECK: balanceOf(owner) >= shares
    ├─ CALL: _approve(owner, escrow, shares)
    ├─ CALL: escrow.escrowShares(owner, shares)
    └─ CALL: strategy.handleOperations7540(RedeemRequest, controller, _, shares)
            ├─ Reads: getStoredPPS()
            ├─ Updates: superVaultState[controller].pendingRedeemRequest
            └─ Updates: superVaultState[controller].averageRequestPPS
```

### 5.3 Fulfillment Flow (Manager)

```
Manager → Strategy.fulfillRedeemRequests(controllers[], assetsOut[])
    ├─ CHECK: _isManager(msg.sender)
    ├─ CHECK: _validateStrategyState() [not paused, PPS fresh]
    ├─ FOR each controller:
    │       ├─ GET: pendingShares = superVaultState[controller].pendingRedeemRequest
    │       ├─ COMPUTE: theoreticalAssets = shares * currentPPS / PRECISION
    │       ├─ COMPUTE: minAssetsOut = shares * avgRequestPPS * (1 - slippage) / PRECISION
    │       ├─ CHECK: minAssetsOut <= assetsOut[i] <= theoreticalAssets
    │       └─ UPDATE: state (clear pending, set maxWithdraw)
    ├─ CALL: vault.burnShares(totalShares)
    └─ CALL: _asset.safeTransfer(escrow, totalAssetsOut)
```

### 5.4 Hook Execution Flow

```
Manager → Strategy.executeHooks(args)
    ├─ CHECK: _isManager(msg.sender)
    ├─ CHECK: !aggregator.isGlobalHooksRootVetoed()
    ├─ FOR each hook:
    │       ├─ CHECK: _isRegisteredHook(hook)
    │       ├─ CHECK: _validateHook(hook, calldata, globalProof, strategyProof)
    │       │         └─ MerkleProof.verify(proof, root, leaf)
    │       ├─ CALL: hook.setExecutionContext(strategy)
    │       ├─ BUILD: executions = hook.build(prevHook, strategy, calldata)
    │       ├─ FOR each execution:
    │       │       └─ CALL: target.call{value}(callData)  ← ARBITRARY EXTERNAL CALLS
    │       └─ CALL: hook.resetExecutionState(strategy)
    └─ EMIT: HooksExecuted(hooks)
```

---

## 6. ORACLE & PRICE FEED MECHANISMS

### 6.1 PPS Oracle Architecture

```
                    ┌─────────────────────┐
                    │   Authorized PPS    │
                    │      Oracles        │
                    └──────────┬──────────┘
                               │ forwardPPS(strategy, newPPS)
                               ▼
              ┌────────────────────────────────┐
              │    SuperVaultAggregator        │
              │ ────────────────────────────── │
              │ _strategyData[strategy].pps    │
              │ _strategyData[strategy].ts     │
              └────────────────────────────────┘
                               │
            ┌──────────────────┴──────────────────┐
            │                                      │
            ▼                                      ▼
    ┌───────────────┐                    ┌───────────────────┐
    │ Strategy      │                    │ SuperVault        │
    │ getStoredPPS()│──reads from───────▶│ convertToAssets() │
    └───────────────┘                    │ convertToShares() │
                                         │ previewDeposit()  │
                                         └───────────────────┘
```

### 6.2 Price Data Sources

| Source | Value | Mechanism |
|--------|-------|-----------|
| SuperVault PPS | 1.007018 | Oracle-provided via Aggregator |
| Pendle SY Rate | 1.007018 | Derived from SuperVault.convertToAssets(1e18) |
| Pendle PT Price | $0.9817 | AMM market price (1.8% discount) |
| Pendle YT Price | $0.0180 | AMM market price |

### 6.3 Price Staleness Checks

```solidity
// PPS is stale if:
// 1. aggregator.isPPSStale(strategy) returns true
// 2. block.timestamp - lastPPSUpdateTimestamp > ppsExpiration (86400s = 1 day)

// Deposits blocked when PPS stale
// Fulfillments blocked when PPS stale
```

---

## 7. ADMIN CONTROLS & UPGRADE MECHANISMS

### 7.1 Role Hierarchy

```
SUPER_GOVERNOR (immutable)
    │
    ├─ getAddress(SUPER_VAULT_AGGREGATOR) → Aggregator
    ├─ getAddress(TREASURY) → Treasury
    ├─ isHookRegistered(hook) → Hook whitelist
    └─ getFee(PERFORMANCE_FEE_SHARE) → Superform's cut

Aggregator
    │
    ├─ Global Admin (proposes globalHooksRoot)
    │       └─ 15-minute timelock for hooks root update
    │
    └─ Per-Strategy:
        ├─ Primary Manager (mainManager)
        │       ├─ proposeVaultFeeConfigUpdate (7-day timelock)
        │       ├─ managePPSExpiration
        │       ├─ manageYieldSource
        │       └─ proposeManagerHooksRoot (15-min timelock)
        │
        ├─ Secondary Managers (up to 5)
        │       ├─ executeHooks
        │       ├─ fulfillRedeemRequests
        │       ├─ fulfillCancelRedeemRequests
        │       └─ skimPerformanceFee
        │
        └─ PPS Oracles (authorized to call forwardPPS)
```

### 7.2 Timelocks

| Action | Timelock | Source |
|--------|----------|--------|
| Global Hooks Root Update | 15 minutes | _hooksRootUpdateTimelock |
| Strategy Hooks Root Update | 15 minutes | _hooksRootUpdateTimelock |
| Fee Config Update | 7 days | PROPOSAL_TIMELOCK |
| PPS Expiry Threshold Update | 7 days | PROPOSAL_TIMELOCK |
| Manager Change | 7 days | _MANAGER_CHANGE_TIMELOCK |
| Post-Unpause Skim Lock | 12 hours | POST_UNPAUSE_SKIM_TIMELOCK |

### 7.3 Veto Mechanisms

```solidity
// Global veto: setGlobalHooksRootVeto(bool vetoed)
// When vetoed: executeHooks() fails, deposits fail
// Authority: SUPER_GOVERNOR

// Strategy veto: similar pattern per-strategy
```

---

## 8. PENDLE INTEGRATION EVIDENCE

### 8.1 Market Data (From Pendle API)

```json
{
  "market": "0x3d83a85e0b0fe9cc116a4efc61bb29cb29c3cb9a",
  "expiry": "2026-04-30",
  "liquidity": {
    "usd": 832060.88,
    "totalPt": 161739.36,
    "totalSy": 668804.52
  },
  "pricing": {
    "ptDiscount": 0.018008676 (1.8%),
    "impliedApy": 0.08134089 (8.13%),
    "underlyingApy": 0.05727532 (5.73%)
  },
  "fees": {
    "swapFeeRate": 0.00166 (0.17%)
  }
}
```

### 8.2 Pendle SY "NoRedeem" Pattern

```solidity
// Critical: SY can only output yieldToken (SuperVault shares), NOT USDC
function _redeem(
    address receiver,
    address /*tokenOut*/,
    uint256 amountSharesToRedeem
) internal virtual override returns (uint256) {
    _transferOut(yieldToken, receiver, amountSharesToRedeem);
    return amountSharesToRedeem;
}

// But Pendle AMM allows SY ↔ PT swaps WITHOUT calling _redeem!
```

### 8.3 Exchange Rate Derivation

```solidity
// Pendle SY exchange rate = SuperVault PPS
function exchangeRate() public view virtual override returns (uint256) {
    return IERC4626(yieldToken).convertToAssets(PMath.ONE); // 1e18
}

// This means: NO LAG between SuperVault PPS update and Pendle SY rate
// Arbitrage window is in AMM pricing, not rate derivation
```

---

## 9. CRITICAL OBSERVATIONS & ATTACK SURFACE

### 9.1 Key Asymmetries Identified

1. **Deposit vs Withdraw Timing**
   - Deposit: INSTANT
   - Withdraw: ASYNC (requires manager fulfillment)
   - **Bypass**: Pendle AMM allows instant exit

2. **PPS Update vs Market Price**
   - SuperVault PPS: Oracle-updated (can be stale)
   - Pendle AMM: Market-driven (can diverge)
   - **Window**: Oracle front-running opportunity

3. **Fulfillment Bounds**
   - minAssetsOut: Based on REQUEST time PPS
   - maxAssetsOut: Based on FULFILLMENT time PPS
   - **Extraction**: Manager can pocket difference

4. **HWM vs Current PPS**
   - Current HWM: 1.000000
   - Current PPS: 1.007018
   - **Unrealized Fee**: 10% of 0.7% = 0.07% of TVL = ~$11,690

### 9.2 Trust Assumptions Broken

| Assumption | Reality |
|------------|---------|
| Manager is honest | Manager can underpay within slippage |
| No instant exit | Pendle provides instant exit |
| PPS manipulation-proof | Oracle timing can be exploited |
| Hooks are safe | Arbitrary external calls possible |

---

## 10. EVIDENCE GAPS (REQUIRES FURTHER INVESTIGATION)

1. **Manager Identity**: Who is the mainManager for this strategy?
2. **Hook Registry**: What hooks are whitelisted in globalHooksRoot?
3. **Oracle Identity**: Who can call forwardPPS?
4. **Historical Traces**: Previous fee skims, fulfillments, PPS updates?
5. **Yield Sources**: Where is the $16.7M USDC actually deployed?

---

*Evidence Collection Timestamp: Block Latest (Feb 4, 2026)*
*Total TVL at Risk: ~$16.7M USDC*
