# f(x) Protocol Cross-Contract Chain Analysis

**Analysis Date**: 2026-02-04
**Contracts Analyzed**: StakingProxyERC20, FxUSDShareableRebalancePool, MarketV2
**Network**: Ethereum Mainnet

---

## Executive Summary

Comprehensive analysis of the f(x) Protocol integration with Convex FXN staking system. The analysis focused on cross-contract call chains, composability risks, and novel attack vectors.

**Key Finding**: No critical exploits identified that allow unauthorized value extraction. Several medium-risk vectors exist around:
- Permissionless function calls (griefing)
- Vote sharing manipulation (requires pre-approval)
- Liquidation timing (requires LIQUIDATOR_ROLE)

---

## Protocol Architecture

```
┌─────────────────────────────────────────────────────────────────────────┐
│                        f(x) Protocol Ecosystem                           │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  ┌──────────────┐     ┌──────────────┐     ┌──────────────────────────┐ │
│  │  User/Convex │────►│ StakingProxy │────►│ FxUSDShareableRebalance  │ │
│  │    Vault     │     │    ERC20     │     │         Pool (Gauge)     │ │
│  └──────────────┘     └──────────────┘     └──────────────────────────┘ │
│        │                    │                         │                  │
│        │                    │                         │                  │
│        ▼                    ▼                         ▼                  │
│  ┌──────────────┐     ┌──────────────┐     ┌──────────────────────────┐ │
│  │   Convex     │     │   FXN        │     │      Treasury            │ │
│  │   Rewards    │     │   Minter     │     │  (Collateral Mgmt)       │ │
│  └──────────────┘     └──────────────┘     └──────────────────────────┘ │
│                             │                         │                  │
│                             ▼                         ▼                  │
│                       ┌──────────────┐     ┌──────────────────────────┐ │
│                       │    Gauge     │     │      MarketV2            │ │
│                       │  Controller  │     │  (Mint/Redeem fToken)    │ │
│                       └──────────────┘     └──────────────────────────┘ │
│                                                       │                  │
│                                                       ▼                  │
│                                            ┌──────────────────────────┐ │
│                                            │      eETH (Etherfi)      │ │
│                                            │    (Base Collateral)     │ │
│                                            └──────────────────────────┘ │
└─────────────────────────────────────────────────────────────────────────┘
```

## Key Addresses (Pool 17)

| Component | Address |
|-----------|---------|
| Gauge Proxy | 0xc2def1e39ff35367f2f2a312a793477c576fd4c3 |
| Gauge Impl | 0x72a6239f1651a4556f4c40fe97575885a195f535 |
| Market | 0x267c6a96db7422faa60aa7198ffeeec4169cd65f |
| Staking Token | 0x9216272158f563488ffc36afb877aca2f265c560 |
| Base Token (eETH) | 0xcd5fe23c85820f7b72d0926fc9b05b43e359b7ee |
| FXN Token | 0x365AccFCa291e7D3914637ABf1F7635dB165Bb09 |
| FXN Minter | 0xc8b194925d55d5de9555ad1db74c149329f71def |
| Gauge Controller | 0xe60eb8098b34ed775ac44b1dde864e098c6d7f37 |

---

## Cross-Contract Call Chains

### Chain 1: Deposit Flow
```
User → StakingProxy.deposit(amount)
    → IERC20.safeTransferFrom(user, vault, amount)
    → IFxnGauge.deposit(amount)
        → Gauge._checkpoint(vault)
            → ICurveTokenMinter.mint(gauge)  [every 24h]
            → IVotingEscrowHelper.checkpoint(voteOwner)
        → Gauge updates balances and boost
    → Proxy._checkpointRewards()
        → IRewards.deposit(owner, delta)
```

### Chain 2: Reward Claim Flow (getReward)
```
Anyone → StakingProxy.getReward()
    → IFxnTokenMinter.mint(gauge)  [FXN to vault]
    → IFxnGauge.claim()
        → Uses rewardReceiver → owner
    → Proxy._processFxn()
        → Transfer fees to feeDepositor
        → Transfer remainder to owner
    → Proxy._processExtraRewards()
        → IRewards.getReward(owner)
```

### Chain 3: Alternative Claim Flow (earned)
```
Anyone → StakingProxy.earned()
    → IFxnTokenMinter.mint(gauge)  [FXN to vault]
    → IFxnGauge.claim(vault, vault)  [DIFFERENT! Rewards to vault]
    → Returns earned amounts (no transfer)
```

### Chain 4: Liquidation Flow (Privileged)
```
LIQUIDATOR_ROLE → Gauge.liquidate(maxAmount, minBaseOut)
    → Check: collateralRatio < liquidatableCollateralRatio
    → IFxMarket.redeem(fToken) → baseToken (eETH)
    → IFxTokenWrapper.wrap(baseToken)  [if needed]
    → _accumulateReward(token, amount)  [distribute to stakers]
    → _notifyLoss(liquidated)
```

### Chain 5: Vote Sharing Flow
```
VE_SHARING_ROLE → Gauge.toggleVoteSharing(staker)
    → isStakerAllowed[owner][staker] = !current

Staker (via execute) → Gauge.acceptSharedVote(newOwner)
    → Check: isStakerAllowed[newOwner][staker]
    → Update getStakerVoteOwner[staker] = newOwner
    → Update boost checkpoint to use newOwner's veFXN
```

---

## Identified Attack Vectors

### H-005: Vote Sharing Manipulation [MEDIUM]
**Vector**: Vault owner uses execute() to call acceptSharedVote()
**Constraint**: Requires victim to have enabled vote sharing
**Impact**: Could redirect boost rewards
**Status**: Valid but requires social engineering or pre-approval

### H-006: Checkpoint Timing Attack [LOW]
**Vector**: Strategic checkpoint() calls to lock favorable boost
**Constraint**: Boost is time-weighted, limited impact
**Impact**: Minor reward optimization
**Status**: More useful for defense than attack

### H-007: Liquidation Sandwich [LOW]
**Vector**: Manipulate collateral ratio + trigger liquidation
**Constraint**: Requires LIQUIDATOR_ROLE
**Impact**: Could extract liquidation rewards
**Status**: Blocked by access control

### H-008: JIT Liquidation Attack [LOW]
**Vector**: Flash deposit before liquidation to capture rewards
**Constraint**: Requires LIQUIDATOR_ROLE collusion
**Impact**: Could steal liquidation distribution
**Status**: Blocked by access control

### H-004: earned() vs getReward() Asymmetry [LOW]
**Vector**: earned() claims to vault, getReward() claims to owner
**Constraint**: Griefing only, no value extraction
**Impact**: Rewards stuck in vault temporarily
**Status**: Owner can recover via transferTokens()

---

## Novel Sequencing Opportunities

### Sequence A: Boost Optimization
```
1. Acquire veFXN
2. Lock for maximum duration
3. Checkpoint immediately after lock
4. Deposit into gauge
5. Checkpoint again to lock high boost
6. Claim rewards frequently to maximize boosted FXN
```

### Sequence B: Cross-Protocol Arbitrage (Theoretical)
```
1. Monitor f(x) collateral ratio
2. When ratio drops:
   - If profitable: Short eETH/ETH
   - Stake in rebalance pool
   - Wait for liquidation
   - Receive eETH rewards
   - Cover short with eETH
```

### Sequence C: Convex Fee Optimization
```
1. Use earned() to claim gauge rewards to vault
2. Call transferTokens() for non-FXN rewards
3. Bypass normal getReward() flow
4. Save gas on fee calculation path
(Note: No actual fee bypass, just different routing)
```

---

## Security Assessment

### Access Controls Verified
- LIQUIDATOR_ROLE: Protected, not widely distributed
- VE_SHARING_ROLE: Protected, requires admin grant
- WITHDRAW_FROM_ROLE: Protected, for specific integrations
- Admin functions: Properly restricted

### Reentrancy Protection
- StakingProxy: nonReentrant on deposit/withdraw
- Gauge: nonReentrant on claim functions
- Gap: getReward() in StakingProxy lacks nonReentrant (no exploit found)

### Oracle Dependencies
- Treasury uses oracle for collateral ratio
- Gauge uses veHelper for veFXN snapshots
- No direct oracle manipulation vectors identified

---

## Recommendations

### For Protocol Team
1. **Add time-weighting to liquidation rewards** - Prevents JIT attacks if LIQUIDATOR_ROLE is compromised
2. **Document earned() behavior** - Make clear that rewards go to vault, not owner
3. **Consider nonReentrant on getReward()** - Defense in depth

### For Users
1. **Use getReward() not earned()** - Unless specifically need vault accounting
2. **Monitor vote sharing status** - Don't enable for unknown addresses
3. **Understand Convex fee structure** - FXN fees apply, gauge rewards direct

---

## Conclusion

The f(x) Protocol integration with Convex FXN is well-designed with appropriate access controls. Cross-contract call chains are complex but properly secured. The main risks are around privileged role compromise (LIQUIDATOR_ROLE) rather than public attack vectors.

**No economically viable exploits identified for unprivileged attackers.**

The permissionless functions (earned, getReward, checkpoint) enable griefing but not value extraction. Vote sharing manipulation requires victim pre-approval. Liquidation attacks require role access.

---

## Appendix: Function Selector Reference

| Function | Selector |
|----------|----------|
| totalSupply() | 0x18160ddd |
| balanceOf(address) | 0x70a08231 |
| market() | 0x80f55605 |
| baseToken() | 0xc55dae63 |
| asset() | 0x38d52e0f |
| treasury() | 0x61d027b8 |
| claim() | 0x4e71d92d |
| claim(address) | 0x1e83409a |
| claim(address,address) | 0xaad3ec96 |
| checkpoint(address) | 0xc2c4c5c1 |
| acceptSharedVote(address) | 0x???? |
| liquidate(uint256,uint256) | 0x???? |
