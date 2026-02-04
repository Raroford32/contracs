# FINAL EVIDENCE COLLECTION
## f(x) Protocol + Convex FXN Integration
## Evidence Collected: 2026-02-04

---

## 1. CONTRACT ADDRESSES (VERIFIED)

| Role | Address | Implementation |
|------|---------|----------------|
| StakingProxyERC20 | 0x8e0fd32e77ad1f85c94e1d1656f23f9958d85018 | Implementation contract |
| Gauge Proxy | 0xc2def1e39ff35367f2f2a312a793477c576fd4c3 | TransparentUpgradeableProxy |
| Gauge Impl | 0x72a6239f1651a4556f4c40fe97575885a195f535 | FxUSDShareableRebalancePool |
| Market Proxy | 0x267c6a96db7422faa60aa7198ffeeec4169cd65f | TransparentUpgradeableProxy |
| Market Impl | 0x2c613d2c163247cd43fd05d6efc487c327d1b248 | MarketV2 |
| Treasury Proxy | 0x781ba968d5cc0b40eb592d5c8a9a3a4000063885 | TransparentUpgradeableProxy |
| Treasury Impl | 0xdd8f6860f5a3eecd8b7a902df75cb7548387c224 | WrappedTokenTreasuryV2 |
| Price Oracle | 0xe1b11bb0b6d1b321eeb7e0298a3f9eb92171693b | FxEETHOracleV2 |
| Base Token (eETH) | 0xcd5fe23c85820f7b72d0926fc9b05b43e359b7ee | Etherfi eETH |
| Platform | 0x0084c2e1b1823564e597ff4848a88d61ac63d703 | Fee recipient |
| Rebalance Splitter | 0x015729c84a1c5e541dfbf6f0ddc59ae66527b5ed | Reward distribution |

---

## 2. ORACLE STATE (LIVE QUERY)

```
priceOracle.getPrice() at block 24383988:
├── isValid: TRUE
├── twap: 2207.5279437378704 USD/ETH
├── minPrice: 2197.936032649733 USD/ETH
├── maxPrice: 2210.9387171084395 USD/ETH
└── SPREAD: 0.589% ((maxPrice - minPrice) / twap)
```

**CRITICAL FINDING: Price divergence exists**
- minPrice used for: MintFToken, RedeemXToken
- maxPrice used for: MintXToken, RedeemFToken
- Arbitrage window: 0.59% (may be insufficient after fees)

---

## 3. TREASURY STORAGE STATE

| Slot | Variable | Value | Decoded |
|------|----------|-------|---------|
| 151 | priceOracle | 0xe1b11bb0b6d1b321eeb7e0298a3f9eb92171693b | FxEETHOracleV2 |
| 152 | referenceBaseTokenPrice | 0xbd8d04a9d40e6b2200 | ~3496.60 USD |
| 153 | totalBaseToken | 0x128683d35fef051b65 | ~341.73 ETH underlying |
| 154 | baseTokenCap | 0x10f0cf064dd59200000 | 5000 ETH |
| 157 | emaLeverageRatio (packed) | 0x...6982f02b | EMA storage struct |
| 158 | platform | 0x0084c2e1b1823564e597ff4848a88d61ac63d703 | Fee recipient |
| 159 | rebalancePoolSplitter | 0x015729c84a1c5e541dfbf6f0ddc59ae66527b5ed | Reward splitter |
| 160 | _miscData | 0x2625a01dcd6500 | Packed ratios |

---

## 4. GAUGE STATE

```
Gauge.totalSupply(): 253,999.6106 fTokens staked
Gauge.treasury(): 0x781ba968d5cc0b40eb592d5c8a9a3a4000063885 ✓
Gauge.market(): 0x267c6a96db7422faa60aa7198ffeeec4169cd65f ✓
```

---

## 5. FUNCTION SELECTORS (VERIFIED)

### StakingProxyERC20
| Function | Selector | Access |
|----------|----------|--------|
| deposit(uint256) | 0xb6b55f25 | Owner |
| withdraw(uint256) | 0x2e1a7d4d | Owner |
| getReward() | 0x3d18b912 | PERMISSIONLESS |
| earned() | 0x96c55175 | PERMISSIONLESS |
| execute(address,uint256,bytes) | 0xb61d27f6 | Owner |
| transferTokens(address) | 0x... | Owner |

### Key Gauge Functions
| Function | Selector | Access |
|----------|----------|--------|
| checkpoint(address) | 0xc2c4c5c1 | PERMISSIONLESS |
| claim() | 0x4e71d92d | User |
| liquidate(uint256,uint256) | 0x... | LIQUIDATOR_ROLE |
| acceptSharedVote(address) | 0x... | Requires isStakerAllowed |
| toggleVoteSharing(address) | 0x... | VE_SHARING_ROLE |

### Treasury
| Function | Selector | Access |
|----------|----------|--------|
| collateralRatio() | 0x5d1ca631 | View |
| settle() | 0x... | SETTLE_WHITELIST_ROLE |

### Oracle
| Function | Selector | Return |
|----------|----------|--------|
| getPrice() | 0x98d5fdca | (bool,uint256,uint256,uint256) |

---

## 6. ACCESS CONTROL MAPPING

### Treasury Roles
```
FX_MARKET_ROLE = keccak256("FX_MARKET_ROLE")
  → Holders: Market contract only
  → Grants: mint/redeem access

SETTLE_WHITELIST_ROLE = keccak256("SETTLE_WHITELIST_ROLE")
  → Holders: Unknown (need to query)
  → Grants: settle() access

PROTOCOL_INITIALIZER_ROLE = keccak256("PROTOCOL_INITIALIZER_ROLE")
  → Holders: Unknown
  → Grants: initializeProtocol() (one-time)
```

### Gauge Roles
```
LIQUIDATOR_ROLE = keccak256("LIQUIDATOR_ROLE")
  → Holders: Unknown (CRITICAL - need to identify)
  → Grants: liquidate() access

VE_SHARING_ROLE = keccak256("VE_SHARING_ROLE")
  → Holders: Unknown
  → Grants: toggleVoteSharing() access

WITHDRAW_FROM_ROLE = keccak256("WITHDRAW_FROM_ROLE")
  → Holders: Unknown
  → Grants: withdrawFrom() access
```

---

## 7. CROSS-CONTRACT CALL PATTERNS

### Pattern 1: Deposit Flow
```
User → StakingProxy.deposit(amount)
     → gauge.deposit(amount, msg.sender)
        STORAGE: _balances[msg.sender] += amount
        STORAGE: totalSupply += amount
```

### Pattern 2: Reward Claim Flow
```
Anyone → StakingProxy.getReward()  [PERMISSIONLESS]
      → gauge.claim()
         → minter.mint(address(this))
            → FXN transfer to vault
         THEN: _processFxn() distributes rewards
```

### Pattern 3: Execute() Arbitrary Call
```
Owner → StakingProxy.execute(to, value, data)
      → _checkExecutable(to)  // Blocks fxn, stakingToken, rewards
      → IF to == gauge AND pool.shutdown:
           REVERT("!shutdown")
      → to.call{value}(data)
         → ARBITRARY CALL TO GAUGE
         → Can call: acceptSharedVote(), checkpoint(), etc.
```

### Pattern 4: Liquidation Flow
```
LIQUIDATOR_ROLE → gauge.liquidate(maxAmount, minOut)
               → _beforeLiquidate()
                  → CHECK: collateralRatio < liquidatableCollateralRatio
               → market.redeem(fTokenIn, recipient)
                  → treasury.redeem(fTokenIn, 0, owner)
                     → BURNS fToken
                     → TRANSFERS baseToken
               → DISTRIBUTES baseToken to stakers
```

### Pattern 5: Vote Sharing (via execute)
```
Attacker → StakingProxy.execute(gauge, 0,
             abi.encodeWithSelector(acceptSharedVote.selector, victim))
         → gauge.acceptSharedVote(victim)
            → REQUIRE: isStakerAllowed[victim][msg.sender]
            → IF TRUE: getStakerVoteOwner[msg.sender] = victim
               → Attacker vault uses victim's veFXN boost
```

---

## 8. STATE DEPENDENCIES GRAPH

```
                    ┌─────────────────────┐
                    │    Price Oracle     │
                    │ FxEETHOracleV2      │
                    │ 0xe1b11bb...        │
                    └─────────┬───────────┘
                              │ getPrice()
                              │ (twap, min, max)
                              ▼
┌───────────────────────────────────────────────────────────┐
│                       TREASURY                             │
│ WrappedTokenTreasuryV2 @ 0x781ba...                       │
│                                                            │
│ STATE:                                                     │
│ ├─ totalBaseToken: 341.73 ETH                             │
│ ├─ referenceBaseTokenPrice: 3496.60 USD                   │
│ ├─ baseTokenCap: 5000 ETH                                 │
│ └─ priceOracle: 0xe1b11bb...                              │
│                                                            │
│ COMPUTED:                                                  │
│ ├─ collateralRatio() = (baseSupply * baseNav) / fSupply   │
│ └─ Uses minPrice/maxPrice based on action                 │
└───────────────────────┬───────────────────────────────────┘
                        │ collateralRatio()
                        │ mint/redeem
                        ▼
┌───────────────────────────────────────────────────────────┐
│                        GAUGE                               │
│ FxUSDShareableRebalancePool @ 0xc2def...                  │
│                                                            │
│ STATE:                                                     │
│ ├─ totalSupply: 253,999.61 fTokens                        │
│ ├─ _balances[user]: staked amounts                        │
│ ├─ getStakerVoteOwner[staker]: boost delegation           │
│ └─ isStakerAllowed[owner][delegate]: allowlist            │
│                                                            │
│ CHECKS:                                                    │
│ ├─ liquidate(): collateralRatio < threshold               │
│ └─ acceptSharedVote(): isStakerAllowed check              │
└───────────────────────┬───────────────────────────────────┘
                        │ deposit/withdraw/claim
                        ▼
┌───────────────────────────────────────────────────────────┐
│                   STAKING PROXY                            │
│ StakingProxyERC20 @ 0x8e0fd...                            │
│                                                            │
│ ENTRY POINTS:                                              │
│ ├─ deposit(amount) [owner]                                │
│ ├─ withdraw(amount) [owner]                               │
│ ├─ getReward() [PERMISSIONLESS] ← Attack surface          │
│ ├─ earned() [PERMISSIONLESS] ← Claims to vault            │
│ └─ execute(to,val,data) [owner] ← Arbitrary gauge call    │
│                                                            │
│ BLOCKED by _checkExecutable:                               │
│ ├─ fxn token                                              │
│ ├─ stakingToken                                           │
│ └─ extra rewards                                          │
└───────────────────────────────────────────────────────────┘
```

---

## 9. IDENTIFIED ATTACK SURFACES

### Surface 1: Permissionless getReward()/earned()
- **Status**: Confirmed permissionless
- **Impact**: Griefing (rewards to vault not owner)
- **Profit**: None (recoverable via transferTokens)
- **Viability**: LOW

### Surface 2: Oracle Price Divergence Arbitrage
- **Status**: 0.59% spread observed
- **Impact**: Potential arbitrage
- **Profit**: Spread - fees (likely negative)
- **Viability**: MEDIUM (needs higher volatility)

### Surface 3: Vote Sharing via execute()
- **Status**: Requires isStakerAllowed[victim][attacker]
- **Impact**: Boost theft
- **Profit**: Increased rewards
- **Viability**: LOW (requires victim pre-allowlist)

### Surface 4: Liquidation MEV
- **Status**: LIQUIDATOR_ROLE required
- **Impact**: JIT liquidity for liquidation rewards
- **Viability**: BLOCKED (role-gated)

### Surface 5: Checkpoint Timing
- **Status**: Permissionless
- **Impact**: Boost optimization
- **Profit**: Marginal reward increase
- **Viability**: LOW (legitimate optimization)

---

## 10. ECONOMIC PARAMETERS

```
Protocol TVL (approximate):
├─ Treasury totalBaseToken: 341.73 ETH (~$750,000)
├─ Gauge totalSupply: 253,999.61 fTokens
└─ Base token cap: 5000 ETH (~$11M max)

Oracle Prices (current):
├─ TWAP: 2207.53 USD/ETH
├─ Min: 2197.94 USD/ETH
├─ Max: 2210.94 USD/ETH
└─ Spread: 0.59%

Fee Structure (need confirmation):
├─ Mint fees: ~0.1-0.5%
├─ Redeem fees: ~0.1-0.5%
└─ Total round-trip: ~0.2-1.0%
```

---

## 11. EVIDENCE GAPS

### Critical (Attack-blocking)
1. ✗ LIQUIDATOR_ROLE holders not identified
2. ✗ Exact fee ratios not confirmed
3. ✗ Historical price divergence data
4. ✗ Gas costs for attack sequences

### Important (Optimization)
1. ✗ isStakerAllowed mapping state
2. ✗ Vote sharing enabled accounts
3. ✗ Recent liquidation events
4. ✗ Oracle update frequency

---

## 12. CONCLUSION

Based on collected evidence:

**No high-confidence unprivileged exploit found.**

Residual attack vectors:
1. **Price Arbitrage**: Exists but likely unprofitable after fees
2. **Vote Sharing**: Requires victim pre-approval
3. **Liquidation**: Role-gated
4. **Griefing**: Possible but no value extraction

The protocol demonstrates mature security design with:
- Role-based access control on sensitive functions
- Multi-source oracle with TWAP anchoring
- Intentional price asymmetry for MEV protection
