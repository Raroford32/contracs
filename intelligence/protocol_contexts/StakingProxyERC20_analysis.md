# StakingProxyERC20 Deep Analysis

## Contract Identity
- **Address**: 0x8e0fd32e77ad1f85c94e1d1656f23f9958d85018
- **Type**: Implementation contract (cloned for each user vault)
- **Protocol**: Convex FXN (cvxFXN) - Convex integration with f(x) Protocol
- **Compiler**: Solidity 0.8.10 (checked arithmetic)

## Constructor Arguments (Immutables)
```
poolRegistry: 0xdb95d646012bb87ac2e6cd63eab2c42323c1f5af
feeRegistry: 0x4f258fecc91b2ff162ca702c2bd9abf2af089611
fxnMinter: 0xc8b194925d55d5de9555ad1db74c149329f71def
```

## Constants
```
fxn: 0x365AccFCa291e7D3914637ABf1F7635dB165Bb09
vefxnProxy: 0xd11a4Ee017cA0BECA8FA45fF2abFe9C6267b7881
FEE_DENOMINATOR: 10000
```

## Storage Layout (Mutable State)
```
slot 0: owner (address) - vault owner
slot 1: gaugeAddress (address) - FXN gauge
slot 2: stakingToken (address) - LP/staking token
slot 3: rewards (address) - Convex extra rewards
slot 4: usingProxy (address) - veFXN proxy override
slot 5: pid (uint256) - pool ID
slot 6: _status (uint256) - ReentrancyGuard
```

---

## ATTACK SURFACE ANALYSIS

### 1. execute() Function - CRITICAL

```solidity
function execute(
    address _to,
    uint256 _value,
    bytes calldata _data
) external onlyOwner returns (bool, bytes memory) {
    // Block: fxn, stakingToken, rewards
    _checkExecutable(_to);

    // Only gauge calls if pool is NOT shutdown
    if(_to == gaugeAddress){
        (, , , , uint8 shutdown) = IPoolRegistry(poolRegistry).poolInfo(pid);
        require(shutdown == 0,"!shutdown");
    }

    (bool success, bytes memory result) = _to.call{value:_value}(_data);
    require(success, "!success");
    return (success, result);
}
```

**Blocked Targets**:
- fxn token (0x365AccFCa291e7D3914637ABf1F7635dB165Bb09)
- stakingToken (set during initialize)
- rewards contract (set during initialize)

**ALLOWED Targets** (attack surface):
- gaugeAddress (if pool not shutdown)
- feeRegistry (immutable)
- poolRegistry (immutable)
- fxnMinter (immutable)
- ANY OTHER ADDRESS

**Interesting Findings**:
1. gaugeAddress NOT blocked when pool is shutdown
2. feeRegistry, poolRegistry, fxnMinter are NOT in blocked list
3. Can call ANY external contract except the 3 blocked ones

**Potential Vectors**:
- Call `setRewardReceiver()` on gauge to redirect rewards
- Call `acceptSharedVote()` on gauge to manipulate boost
- Call arbitrary contracts that might callback

---

### 2. initialize() Function

```solidity
function initialize(address _owner, uint256 _pid) public override{
    super.initialize(_owner, _pid);

    // Set infinite approval to gauge
    IERC20(stakingToken).approve(gaugeAddress, type(uint256).max);

    // Set reward receiver to owner
    IFxnGauge(gaugeAddress).setRewardReceiver(_owner);
}
```

**Check**: `require(owner == address(0),"already init");`

This prevents re-initialization. However, this is an implementation contract - the actual vulnerability would be in cloned instances.

---

### 3. earned() Function - MUTATES STATE

```solidity
function earned() external override returns (address[] memory token_addresses, uint256[] memory total_earned) {
    // ...

    // MINTS FXN (state change!)
    try IFxnTokenMinter(fxnMinter).mint(gaugeAddress){}catch{}

    // CLAIMS REWARDS (state change!)
    IFxnGauge(gaugeAddress).claim(address(this),address(this));

    // ...
}
```

**CRITICAL**: `earned()` is NOT a view function - it actually claims rewards!
- Anyone can call `earned()` (no access control)
- This claims FXN via minter
- This claims gauge rewards to the vault

**Attack Scenario**:
Could this be exploited by calling earned() at strategic times to manipulate reward distribution?

---

### 4. getReward() Flow

```solidity
function getReward(bool _claim) public override{
    if(_claim){
        // Mint FXN
        try IFxnTokenMinter(fxnMinter).mint(gaugeAddress){}catch{}
        // Claim from gauge (goes to owner via rewardReceiver)
        IFxnGauge(gaugeAddress).claim();
    }
    _processFxn();
    _processExtraRewards();
}
```

**No access control on getReward()!** Anyone can call it.

---

### 5. _checkpointRewards() - Reward Accounting

```solidity
function _checkpointRewards() internal{
    address _rewards = rewards;
    if(IRewards(_rewards).rewardState() == IRewards.RewardState.Active){
        uint256 userLiq = IFxnGauge(gaugeAddress).balanceOf(address(this));
        uint256 bal = IRewards(_rewards).balanceOf(address(this));
        if(userLiq >= bal){
            IRewards(_rewards).deposit(owner, userLiq - bal);
        }else{
            IRewards(_rewards).withdraw(owner, bal - userLiq);
        }
    }
}
```

**Analysis**:
- Syncs reward contract balance with gauge balance
- Called after deposit/withdraw
- No external calls during deposit/withdraw (ReentrancyGuard)

---

### 6. _processExtraRewards() - First Call Edge Case

```solidity
function _processExtraRewards() internal{
    address _rewards = rewards;
    if(IRewards(_rewards).rewardState() == IRewards.RewardState.Active){
        uint256 bal = IRewards(_rewards).balanceOf(address(this));
        uint256 gaugeBalance = IFxnGauge(gaugeAddress).balanceOf(address(this));

        // FIRST CALL INITIALIZATION
        if(bal == 0 && gaugeBalance > 0){
            IRewards(_rewards).deposit(owner,gaugeBalance);
        }
        IRewards(_rewards).getReward(owner);
    }
}
```

**Observation**: If `bal == 0` but `gaugeBalance > 0`, it initializes the reward balance.
This happens on first `getReward()` call after reward activation.

---

## CROSS-CONTRACT DEPENDENCIES

```
StakingProxyERC20
    ├── IFxnGauge (gaugeAddress)
    │   ├── deposit(amount)
    │   ├── withdraw(amount)
    │   ├── claim()
    │   ├── setRewardReceiver()
    │   ├── acceptSharedVote()
    │   └── balanceOf()
    │
    ├── IFxnTokenMinter (fxnMinter)
    │   └── mint(gauge)
    │
    ├── IRewards (rewards)
    │   ├── deposit(owner, amount)
    │   ├── withdraw(owner, amount)
    │   ├── getReward(owner)
    │   ├── balanceOf()
    │   └── rewardState()
    │
    ├── IFeeRegistry (feeRegistry)
    │   ├── totalFees()
    │   └── getFeeDepositor()
    │
    └── IPoolRegistry (poolRegistry)
        └── poolInfo(pid)
```

---

## HYPOTHESIS CANDIDATES

### H-001: execute() gauge manipulation when shutdown
- When pool is shutdown, execute() allows gauge calls
- Could manipulate gauge state (claim rewards, change receiver)
- Need to check what functions are callable

### H-002: earned() anyone can claim
- earned() has no access control
- It claims FXN and gauge rewards to vault
- Could this be used to grief or manipulate timing?

### H-003: getReward() permissionless calling
- Anyone can trigger reward claims
- Fees are sent to feeDepositor
- Owner gets remainder
- Timing attacks on reward distribution?

### H-004: First reward claim initialization
- _processExtraRewards has first-call initialization
- Could race condition exist between first deposit and first claim?

### H-005: execute() to feeRegistry/poolRegistry
- These immutable addresses are NOT blocked
- What functions can be called on them?
- Could manipulate fee routing?

---

## STORAGE ASYMMETRY ANALYSIS

### deposit() vs withdraw()

**deposit()**:
1. transferFrom(msg.sender -> vault)
2. gauge.deposit(balanceOf)
3. _checkpointRewards()

**withdraw()**:
1. gauge.withdraw(amount)
2. _checkpointRewards()
3. transfer(vault -> msg.sender)

**Asymmetry**:
- deposit uses balanceOf (handles fee-on-transfer)
- withdraw uses exact amount
- Both checkpoint at same point (AFTER gauge interaction)

### getReward() states

**With _claim=true**:
1. mint FXN
2. gauge.claim() -> goes to owner via rewardReceiver
3. _processFxn() -> fees deducted, remainder to owner
4. _processExtraRewards() -> convex rewards to owner

**With _claim=false**:
1. SKIP minting/claiming
2. _processFxn() -> only processes existing FXN in vault
3. _processExtraRewards() -> only processes existing convex rewards

---

## NEXT STEPS

1. Query the FXN gauge contract for attack surface
2. Check what functions are available via execute()
3. Analyze the PoolRegistry for pool manipulation
4. Check actual vault instances for TVL
5. Build fork tests to validate hypotheses
