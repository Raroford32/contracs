# StakingProxyERC20 Security Analysis Report

**Contract Address**: `0x8e0fd32e77ad1f85c94e1d1656f23f9958d85018`
**Protocol**: Convex FXN (cvxFXN) - Convex integration with f(x) Protocol
**Analysis Date**: 2026-02-04
**Analyzer**: Claude Code

---

## Executive Summary

StakingProxyERC20 is an implementation contract for user vault clones in the Convex FXN ecosystem. Each user gets their own vault cloned from this implementation to stake tokens in FXN gauges while receiving boosted rewards through Convex's veFXN delegation.

**Overall Risk Assessment**: LOW-MEDIUM

No critical exploits were identified that would allow direct extraction of value from other users. The main findings relate to:
1. Permissionless functions that could enable griefing attacks
2. Asymmetric behavior between `earned()` and `getReward()` functions
3. `execute()` function's broad capabilities (by design)

---

## Contract Architecture

### Inheritance Chain
```
StakingProxyERC20
    └── StakingProxyBase
        └── IProxyVault
    └── ReentrancyGuard
```

### Key Dependencies
| Contract | Address | Role |
|----------|---------|------|
| PoolRegistry | 0xdb95d646012bb87ac2e6cd63eab2c42323c1f5af | Pool/vault management |
| FeeRegistry | 0x4f258fecc91b2ff162ca702c2bd9abf2af089611 | Fee configuration |
| FXN Token | 0x365AccFCa291e7D3914637ABf1F7635dB165Bb09 | Protocol token |
| FXN Minter | 0xc8b194925d55d5de9555ad1db74c149329f71def | Mints FXN rewards |
| veFXN Proxy | 0xd11a4Ee017cA0BECA8FA45fF2abFe9C6267b7881 | Boost delegation |

### Storage Layout
| Slot | Variable | Type | Description |
|------|----------|------|-------------|
| 0 | owner | address | Vault owner |
| 1 | gaugeAddress | address | FXN gauge contract |
| 2 | stakingToken | address | LP/staking token |
| 3 | rewards | address | Convex extra rewards |
| 4 | usingProxy | address | veFXN proxy override |
| 5 | pid | uint256 | Pool ID |
| 6 | _status | uint256 | ReentrancyGuard |

---

## Security Findings

### Finding 1: Permissionless getReward() and earned() [MEDIUM]

**Location**: `StakingProxyERC20.sol:132-160, 78-114`

**Description**: Both `getReward()` and `earned()` functions have NO access control modifiers, allowing anyone to trigger reward claims for any vault.

**Code Reference**:
```solidity
// Line 132 - No onlyOwner!
function getReward() external override{
    getReward(true);
}

// Line 78 - No onlyOwner!
function earned() external override returns (address[] memory, uint256[] memory) {
    // ... mints FXN and claims gauge rewards
}
```

**Impact**:
- Griefing: Attacker can force reward claims at inopportune times
- Timing manipulation: Affects when rewards are distributed
- Tax implications: Could affect tax reporting timing for vault owners

**Risk**: LOW-MEDIUM
- No direct value extraction possible
- Rewards still go to rightful owner
- Main impact is UX and timing

**Recommendation**: Consider adding access control or documenting this as intended behavior.

---

### Finding 2: earned() vs getReward() Asymmetry [MEDIUM]

**Location**: `StakingProxyERC20.sol:96, 140`

**Description**: These functions handle gauge reward claiming differently:

| Function | Gauge Claim Behavior | Destination |
|----------|---------------------|-------------|
| `earned()` | `claim(address(this), address(this))` | **Vault** |
| `getReward()` | `claim()` via rewardReceiver | **Owner** |

**Code Reference**:
```solidity
// In earned() - Line 96
IFxnGauge(gaugeAddress).claim(address(this), address(this));

// In getReward() - Line 140
IFxnGauge(gaugeAddress).claim(); // Uses rewardReceiver set in initialize()
```

**Attack Scenario**:
1. Attacker monitors for vault with pending gauge rewards
2. Attacker calls `earned()` on victim's vault
3. Gauge rewards claimed to vault (not owner)
4. Owner calls `getReward()` - nothing new to claim from gauge
5. Gauge rewards (if non-FXN) remain in vault
6. Owner must manually call `transferTokens([token])` to recover

**Impact**:
- Gauge reward tokens may get "stuck" in vault temporarily
- Owner must know about and manually transfer each reward token
- Creates friction in reward collection process

**Risk**: LOW-MEDIUM
- Value not permanently lost
- Owner can recover via `transferTokens()`
- Main impact is UX degradation

---

### Finding 3: execute() Function Attack Surface [LOW]

**Location**: `StakingProxyBase.sol:176-195`

**Description**: The `execute()` function allows vault owners to make arbitrary calls to most addresses.

**Blocked Targets** (cannot call via execute):
- FXN token (`0x365AccFCa291e7D3914637ABf1F7635dB165Bb09`)
- stakingToken (set during initialize)
- rewards contract (set during initialize)

**Allowed Targets**:
- gaugeAddress (if pool not shutdown)
- feeRegistry
- poolRegistry
- fxnMinter
- **Any other address**

**Notable Allowed Operations**:
```solidity
// Owner can call gauge to redirect their own rewards:
execute(gaugeAddress, 0, abi.encodeCall(IFxnGauge.setRewardReceiver, (newAddress)));

// Owner can call gauge to manipulate boost:
execute(gaugeAddress, 0, abi.encodeCall(IFxnGauge.acceptSharedVote, (boostProvider)));
```

**Risk**: LOW
- Requires owner authorization
- External contracts have their own access controls
- FeeRegistry/PoolRegistry functions require onlyOwner/onlyOperator
- Appears to be intentional design for flexibility

---

### Finding 4: getReward() Missing nonReentrant [INFO]

**Location**: `StakingProxyERC20.sol:132-160`

**Description**: The `getReward()` function makes multiple external calls without `nonReentrant` protection:
1. `fxnMinter.mint()` - external call
2. `gauge.claim()` - external call (sends tokens to owner)
3. `_processFxn()` - transfers to feeDepositor and owner
4. `_processExtraRewards()` - calls to rewards contract

**Analysis**:
- Callback would come from owner receiving tokens
- Owner attacking their own vault is not a meaningful threat
- External contracts (minter, gauge, rewards) are trusted Convex contracts

**Risk**: INFORMATIONAL
- No practical exploit path identified
- External dependencies are protocol-controlled

---

### Finding 5: transferTokens() Doesn't Block Gauge Reward Tokens [INFO]

**Location**: `StakingProxyBase.sol:147-159`

**Description**: The `_transferTokens()` function blocks FXN and gaugeAddress, but allows transfer of gauge reward tokens.

```solidity
function _transferTokens(address[] memory _tokens) internal{
    for(uint256 i = 0; i < _tokens.length; i++){
        // Only blocks fxn and gaugeAddress (not a token)
        if(_tokens[i] != fxn && _tokens[i] != gaugeAddress){
            // ... transfers allowed
        }
    }
}
```

**Implication**: If gauge distributes WETH, CRV, or other tokens as rewards, owner can transfer them directly without going through the `getReward()` flow.

**Risk**: INFORMATIONAL
- This appears intentional
- Owner controls their own vault
- No fee evasion (gauge rewards don't have protocol fees)

---

## Protocol Context

### Active Pools (as of analysis)
| Pool ID | Status | Gauge | TVL (tokens) |
|---------|--------|-------|--------------|
| 17 | Active | 0xc2def1e... | ~253,999 |
| 18 | Active | 0x7eb0ed1... | ~66,493 |

### Fee Structure
- FXN rewards have protocol fees deducted in `_processFxn()`
- Fees sent to `feeDepositor` via `FeeRegistry.getFeeDepositor()`
- Gauge rewards (non-FXN) have NO protocol fees

### Security Controls
- `onlyOwner` on deposit, withdraw, transferTokens, execute
- `onlyAdmin` on setVeFXNProxy (only vefxnProxy can call)
- `nonReentrant` on deposit, withdraw
- FeeRegistry/PoolRegistry have proper access controls

---

## Call Graph Summary

```
StakingProxyERC20
    │
    ├── deposit(amount) [onlyOwner, nonReentrant]
    │   ├── IERC20.safeTransferFrom(owner -> vault)
    │   ├── IFxnGauge.deposit(amount)
    │   └── _checkpointRewards()
    │
    ├── withdraw(amount) [onlyOwner, nonReentrant]
    │   ├── IFxnGauge.withdraw(amount)
    │   ├── _checkpointRewards()
    │   └── IERC20.safeTransfer(vault -> owner)
    │
    ├── getReward() [PERMISSIONLESS]
    │   ├── IFxnTokenMinter.mint(gauge) -- FXN to vault
    │   ├── IFxnGauge.claim() ----------- rewards to owner
    │   ├── _processFxn() --------------- fees + FXN to owner
    │   └── _processExtraRewards() ------ convex rewards
    │
    ├── earned() [PERMISSIONLESS, MUTATES STATE]
    │   ├── IFxnTokenMinter.mint(gauge) -- FXN to vault
    │   ├── IFxnGauge.claim(vault,vault) - rewards to VAULT
    │   └── IRewards.claimableRewards() -- query only
    │
    ├── transferTokens(tokens) [onlyOwner]
    │   └── IERC20.safeTransfer(vault -> owner) [excludes fxn]
    │
    └── execute(to, value, data) [onlyOwner]
        └── arbitrary.call(data) [excludes fxn, stakingToken, rewards]
```

---

## Recommendations

### For Protocol Team

1. **Document Permissionless Functions**: Clearly document that `getReward()` and `earned()` can be called by anyone. Ensure frontend handles this gracefully.

2. **Consider earned() Behavior**: The asymmetry with `getReward()` may cause confusion. Consider:
   - Making `earned()` a view function (don't actually claim)
   - Aligning claim behavior between functions

3. **Add nonReentrant to getReward()**: While no exploit was found, adding reentrancy protection is defensive best practice.

### For Users

1. **Check Vault Balances**: If gauge distributes multiple reward tokens, check vault balance for each and use `transferTokens()` if needed.

2. **Be Aware of Permissionless Claims**: Anyone can trigger `getReward()` on your vault. Plan tax reporting accordingly.

3. **execute() Power**: The `execute()` function is powerful. Secure your owner key carefully.

---

## Conclusion

StakingProxyERC20 is a well-designed vault implementation with appropriate security controls. The main findings relate to UX concerns (permissionless functions, asymmetric behavior) rather than exploitable vulnerabilities. The contract successfully prevents unauthorized value extraction while maintaining flexibility for vault owners.

**No critical or high-severity vulnerabilities were identified.**

---

## Appendix: Tested Hypotheses

| ID | Hypothesis | Status | Result |
|----|-----------|--------|--------|
| H-001 | Permissionless getReward/earned manipulation | Tested | Low-risk griefing only |
| H-002 | execute() to feeRegistry | Invalidated | feeRegistry has access controls |
| H-003 | Gauge manipulation via execute | Tested | Owner-only, intentional feature |
| H-004 | earned/getReward asymmetry | Confirmed | UX issue, not exploitable |
