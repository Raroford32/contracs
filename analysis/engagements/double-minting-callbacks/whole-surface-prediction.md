# Whole-Surface Failure Shape Analysis — All contracts.txt Contracts

**Date:** 9 March 2026
**Scope:** 1,568 addresses in `contracts.txt`, 66 source files in `src_cache/`
**Framework:** 5 failure shapes derived from 2025–2026 incident pattern analysis

---

## The Prediction

The next real exploit of a deployed, audited protocol will hit a **rare path** where the code is locally reasonable but the system-level invariant is wrong. The exact payload will be new. The geometry will not.

Five geometries dominate the 2025–2026 incident landscape. Every contract in our corpus was scanned against all five.

---

## Failure Shape 1: Authenticated Envelope, Unbound Payload

*The outer message is "valid," the inner meaning is not tightly bound.*

| Severity | Contract | File | Envelope | Unbound Payload |
|----------|----------|------|----------|-----------------|
| CRITICAL | BentoBox/DegenBox deposit | degenbox.sol | `allowed(from)` | Any token accepted (ERC777 callback) |
| CRITICAL | BentoBox/DegenBox `batch()` | degenbox.sol | None (public) | `delegatecall` to self with user-supplied calldata; **msg.value reused across all batch items** (known exploited vuln) |
| CRITICAL | BentoBox/DegenBox flashLoan | degenbox.sol | Balance repayment check | Arbitrary `borrower.onFlashLoan()` callback, no reentrancy guard |
| CRITICAL | AdEx Identity `execute()` | adx_flash_loans.sol | Privilege-level signature check | Arbitrary `to`, `value`, `data` in signed txns — auth validates "who" not "what" |
| CRITICAL | AdEx Identity `executeRoutines()` | adx_flash_loans.sol | RoutineAuthorization hash | `op.data` NOT part of auth hash — anyone can substitute operations after auth passes |
| CRITICAL | ADXFlashLoans `flash()` | adx_flash_loans.sol | Balance repayment | Flash-loaned funds + Identity's `execute()` = arbitrary-call with loaned capital |
| CRITICAL | CelerWallet | celerwallet.sol | Operator+Owner auth | Any receiver, any token, any amount in `withdraw()` |
| CRITICAL | Compound V1 MoneyMarket | compound_v1_moneymarket.sol | Oracle-based collateral check | Admin-settable oracle (exact Moonwell shape) |
| CRITICAL | MasterChef migrate | masterchef.sol | Owner-set migrator + balance check | Migrator returns any token, has full approval, side effects unbound |
| HIGH | EtherDelta | etherdelta.sol | Balance accounting | User-controlled token addresses (any contract accepted) |
| HIGH | Hydro DEX | hydro.sol | Signature verification | Batch order parameters, relayer controls matching |
| HIGH | R1Exchange | r1exchange.sol | `onlyAdmin` | Admin can withdraw any user's funds to any address |
| HIGH | Clipper Exchange | clipper_*.sol | Signature verification | `auxiliaryData` unvalidated, `destinationAddress` unbound |
| HIGH | Conditional Tokens | conditional_tokens.sol | Balance check | Arbitrary `conditionId` and `partition` creation |
| HIGH | ADX Flash Loans | adx_flash_loans.sol | Balance repayment check | Arbitrary `onFlashLoan` callback, no reentrancy guard |
| HIGH | Opyn PerpVault | opyn_*.sol | `onlyOwner` | Action modules execute arbitrary logic with vault WETH |
| MEDIUM | DODO PMM | dodo_pmm.sol | Pricing algorithm | Oracle dependency, owner-settable |
| MEDIUM | Perpetual V1 | perpetualv1.sol | Margin requirements | AMM + oracle manipulation window |
| MEDIUM | Curve Pools | *.vy | Invariant math | `min_dy` user-controlled (can be 0), admin params |
| MEDIUM | cDAI/Compound | cdai*.sol | Comptroller proxy | Upgradeable auth logic |
| MEDIUM | Harvest Reward Pool | harvest_reward_pool.sol | `onlyRewardDistribution` | Reward amount unvalidated against balance |
| MEDIUM | SafeBox | safebox.sol | cToken exchange rate | External rate dependency |

---

## Failure Shape 2: Programmable Authority

*"Authorized signer" is no longer a simple fact — it is a rule engine with plugins.*

| Severity | Contract | File | Authority Model | Programmable Element |
|----------|----------|------|-----------------|---------------------|
| CRITICAL | BentoBox/DegenBox | degenbox.sol | Signature + Master Contract | Approval extends to ALL clones; no expiry on sigs |
| CRITICAL | CelerWallet | celerwallet.sol | Operator + Owner | Operator transferable, multi-wallet pivot |
| CRITICAL | Compound V1 | compound_v1_moneymarket.sol | Single Admin | Oracle, interest model, risk params — no timelock, no bounds |
| CRITICAL | MasterChef | masterchef.sol | Single Owner | Migrator (token swap), pool params, alloc points |
| CRITICAL | Marketing Mining | marketing_mining_*.sol | Admin Proxy | Implementation swap → full storage takeover |
| CRITICAL | Opyn PerpVault | opyn_*.sol | Owner + Modules | Action modules = Safe modules analog |
| HIGH | cDAI/Compound | cdai*.sol | Admin Proxy | Implementation + arbitrary init data via `_becomeImplementation` |
| HIGH | stkAAVE | 0xd784...sol | Governance Proxy | Slash, cooldown, emissions, upgrade |
| HIGH | Hydro DEX | hydro.sol | Signature + Relayer | Relayer delegation + execution ordering |
| HIGH | R1Exchange | r1exchange.sol | Single Admin | Admin withdraw + accounts contract swap |
| HIGH | Floor Token | floor.sol | Token Logic | `_beforeTokenTransfer` as programmable transfer gate |
| HIGH | FEG Token/Stake | feg_*.sol | Token Logic | Burn-on-transfer as authority over received amounts |
| MEDIUM | DODO PMM | dodo_pmm.sol | Single Owner | Oracle + K + fees |
| MEDIUM | ADX Loyalty Pool | adx_loyalty_pool.sol | External Controller | Supply controller minting authority |
| MEDIUM | Curve Pools | *.vy | Admin | A coefficient + fees (time-ramped — best practice) |
| MEDIUM | Harvest Reward | harvest_reward_pool.sol | Owner + Distributor | Reward distribution identity mutable |

---

## Failure Shape 3: Live Config / Governance / Rollout Semantics

*Not a fossil bug class. Live-system semantics going sideways after deployment.*

| Severity | Contract | File | Config Surface | What Breaks |
|----------|----------|------|---------------|-------------|
| CRITICAL | Compound V1 | compound_v1_moneymarket.sol | `_setOracle()`, `_setRiskParameters()`, `_setMarketInterestRateModel()` | **Moonwell-exact:** wrong oracle → mass liquidation → bad debt. No timelock, no bounds. |
| CRITICAL | MasterChef | masterchef.sol | `setMigrator()`, `add()`, `set()` | Token swap → reentrancy; alloc manipulation → reward theft |
| CRITICAL | Marketing Mining | marketing_mining_*.sol | `_setImplementation()` | Storage collision or drain via malicious impl |
| CRITICAL | Opyn PerpVault | opyn_*.sol | `setActions()`, `rollOver()` | Malicious action module → vault drain |
| HIGH | DODO PMM | dodo_pmm.sol | `setOracle()`, `setK()`, `setFees()` | K=0 → no slippage → pool drain; wrong oracle → mispricing |
| HIGH | cDAI/Compound | cdai*.sol | `_setImplementation()`, `_setComptroller()` | Upgrade corruption; market malfunction |
| HIGH | stkAAVE | 0xd784...sol | Cooldown, slash %, emissions | Locked funds; 100% slash; reward insolvency |
| HIGH | Harvest Reward | harvest_reward_pool.sol | `notifyRewardAmount()` | Phantom rewards (no balance check) → bank run |
| HIGH | Curve Pools | *.vy | `ramp_A()`, `commit_new_fee()` | Imbalance amplification. *But*: has `MIN_RAMP_TIME` guardrail |
| HIGH | yDAI | 0x16de...sol | `setProvider()` | Malicious provider → vault fund drain |
| HIGH | SafeBox | safebox.sol | `setCToken()` | Wrong Compound market → accounting mismatch |
| MEDIUM | Smoothy V1 | smoothy_v1.sol | `setFees()`, `setRewardCollector()` | 100% fee; reward redirection |
| MEDIUM | ADX Loyalty | adx_loyalty_pool.sol | Supply controller address | Over-minting → dilution |
| MEDIUM | Conditional Tokens | conditional_tokens.sol | Reporter identity (immutable after set) | Key compromise → wrong outcomes |
| MEDIUM | FEG Token/Stake | feg_*.sol | Burn rate | Accounting divergence mid-stake |

**Key observation:** Nearly every CRITICAL/HIGH finding shares one trait — **no timelock on critical parameter changes.** Curve is the notable exception.

---

## Failure Shape 4: Generic Execution Surfaces + Leftover Trust

*The contract's real trust model and the user's mental model diverge.*

| Severity | Contract | File | Generic Surface | Mental Model Gap |
|----------|----------|------|----------------|-----------------|
| CRITICAL | BentoBox/DegenBox | degenbox.sol | `deposit()`/`flashLoan()`/`batch()` with callbacks | Master contract approval extends to ALL clones; `batch()` = `delegatecall` to self with any calldata |
| CRITICAL | MasterChef | masterchef.sol | `migrate()` gives full `safeApprove` to arbitrary contract | Users think staking is static; migrator swaps underlying |
| CRITICAL | CelerWallet | celerwallet.sol | `withdraw()` to any receiver; `transferToOperator()` | Operator has full fund routing power |
| CRITICAL | Compound V1 | compound_v1_moneymarket.sol | Admin oracle/model changes + `_withdrawEquity()` | Single key controls entire economic model |
| HIGH | EtherDelta | etherdelta.sol | Any contract address accepted as "token" | Malicious token returns true without transferring |
| HIGH | R1Exchange | r1exchange.sol | `adminWithdraw()` of any user's funds | Admin bypass of user withdrawal intent |
| HIGH | ADX Flash Loans | adx_flash_loans.sol | `onFlashLoan` callback, no reentrancy guard | Callback can interact with ADXLoyaltyPool (also no guard) |
| HIGH | Smoothy V1 | smoothy_v1.sol | Admin-set `_rewardCollector` gets minted LP | Hidden dilution mechanism |
| HIGH | Opyn PerpVault | opyn_*.sol | Actions receive vault WETH + execute arbitrarily | Owner-set modules = Safe modules |
| HIGH | BentoBox batch | degenbox.sol | `delegatecall` to self with any calldata | Complex multi-step attack orchestration |
| MEDIUM | DODO PMM | dodo_pmm.sol | `withdrawAllBase()` / `withdrawAllQuote()` | Owner access to all liquidity |
| MEDIUM | yDAI | 0x16de...sol | Admin-set lending protocols get vault funds | Malicious provider drains vault |
| MEDIUM | Harvest Reward | harvest_reward_pool.sol | `notifyRewardAmount()` without balance check | Promises rewards that don't exist |
| MEDIUM | Curve Vyper | curve_pool_vyper_vuln.vy | Broken `@nonreentrant` in old Vyper | Compiler bug invalidates reentrancy protection |

---

## Failure Shape 5: Extreme-State Accounting & Invariant Collapse

*Tiny local assumptions, giant global mess.*

| Severity | Contract | File | Pattern | Boundary Condition |
|----------|----------|------|---------|-------------------|
| CRITICAL | xSushi (SushiBar) | xsushi.sol | Mint-before-transfer (reverse CEI) | ERC777 callback → re-enter `leave()` with unbacked shares; first-depositor inflation; donation attack |
| CRITICAL | BentoBox/DegenBox | degenbox.sol | Effects-before-interactions + elastic/base divergence | ERC777 callback; donation inflates real balance vs tracked elastic; toBase/toElastic rounding at extremes |
| CRITICAL | ConvexStakingWrapper | ConvexStakingWrapperAbra.sol | Mint-before-transfer + reward checkpoint inflation | `_beforeTokenTransfer` checkpoints with inflated balance BEFORE tokens arrive. No reentrancy needed. |
| CRITICAL | ADX Loyalty Pool | adx_loyalty_pool.sol | Mint-before-transfer + `mintIncentive()` external call | No reentrancy guard; supply controller as pre-callback; first-depositor attack |
| CRITICAL | MasterChef | masterchef.sol | State-after-externals (3 external calls before `user.amount` update) | ERC777 LP → re-enter `deposit(pid,0)` → double reward claim; `accSushiPerShare` overflow with tiny supply |
| CRITICAL | Compound V1 | compound_v1_moneymarket.sol | Interest index arithmetic | Rate × blockDelta overflow; oracle price manipulation → bad debt; supply/borrow index divergence |
| CRITICAL | Smoothy V1 | smoothy_v1.sol | Stale `_totalBalance` during transfer callback | Multi-token reentrancy: second `mint()` gets cheaper LP; normalization precision loss across decimals |
| HIGH | Curve Pools | *.vy | Vyper reentrancy bug + Newton's method edge cases | Near-zero reserves → solver failure; A=very large → constant-sum (no slippage) → drain; admin fee accumulation drift |
| HIGH | yDAI | 0x16de...sol | Stale pool value across external calls | `_calcPoolValueInToken()` reads Compound/Aave/dYdX rates (manipulable); `invest()` uses pre-rebalance pool value |
| HIGH | Harvest Reward Pool | harvest_reward_pool.sol | `totalSupply()==0` reward accumulation | Flash-stake captures entire reward period; phantom rewards from unvalidated `notifyRewardAmount` |
| HIGH | DODO PMM | dodo_pmm.sol | K=0 and oracle=0 edge cases | K=0 → no slippage → drain; oracle returns 0 → free tokens; target amounts near 0 → precision failure |
| HIGH | cDAI | cdai*.sol | Exchange rate manipulation + first-mint edge | Donation attack on cToken; `totalSupply==0` → `initialExchangeRateMantissa` with 1 wei mint |
| HIGH | Perpetual V1 | perpetualv1.sol | Funding rate accumulation + mark/index price divergence | Long-held positions silently undercollateralized; MEV at margin threshold |
| HIGH | SafeBox | safebox.sol | Double exchange rate (SafeBox wraps cToken wraps underlying) | cToken rate manipulation; double precision loss |
| HIGH | Conditional Tokens | conditional_tokens.sol | Split/merge rounding with many outcomes | Dust from 256-outcome positions; fractional payout precision loss |

---

## Unified Contract × Failure Shape Matrix

**Contracts appearing in 3+ failure shapes are the highest-risk targets.**

| Contract | Shape 1: Envelope | Shape 2: Authority | Shape 3: Config | Shape 4: Generic Exec | Shape 5: Accounting | Count | Max Severity |
|----------|:-:|:-:|:-:|:-:|:-:|:-:|:-:|
| **BentoBox/DegenBox** | CRIT | CRIT | — | CRIT | CRIT | **4** | CRITICAL |
| **MasterChef** | CRIT | CRIT | CRIT | CRIT | CRIT | **5** | CRITICAL |
| **Compound V1 MoneyMarket** | CRIT | CRIT | CRIT | CRIT | CRIT | **5** | CRITICAL |
| **CelerWallet** | CRIT | CRIT | HIGH | CRIT | — | **4** | CRITICAL |
| **Opyn PerpVault** | HIGH | CRIT | CRIT | HIGH | — | **4** | CRITICAL |
| **xSushi (SushiBar)** | — | — | — | — | CRIT | **1** | CRITICAL |
| **ConvexStakingWrapper** | — | — | — | — | CRIT | **1** | CRITICAL |
| **AdEx Identity + Flash** | CRIT | CRIT | — | CRIT | — | **3** | CRITICAL |
| **ADX Loyalty Pool** | — | MED | MED | — | CRIT | **3** | CRITICAL |
| **Marketing Mining** | — | CRIT | CRIT | — | — | **2** | CRITICAL |
| **Smoothy V1** | — | — | MED | HIGH | CRIT | **3** | CRITICAL |
| **Compound cDAI** | MED | HIGH | HIGH | — | HIGH | **4** | HIGH |
| **DODO PMM** | MED | MED | HIGH | MED | HIGH | **5** | HIGH |
| **Curve Pools** | MED | MED | HIGH | MED | HIGH | **5** | HIGH |
| **yDAI** | — | — | HIGH | MED | HIGH | **3** | HIGH |
| **Harvest Reward Pool** | MED | MED | HIGH | MED | HIGH | **5** | HIGH |
| **stkAAVE** | — | HIGH | HIGH | — | — | **2** | HIGH |
| **Perpetual V1** | MED | MED | HIGH | MED | HIGH | **5** | HIGH |
| **SafeBox** | MED | MED | HIGH | — | HIGH | **4** | HIGH |
| **EtherDelta** | HIGH | — | LOW | HIGH | — | **3** | HIGH |
| **R1Exchange** | HIGH | HIGH | — | HIGH | — | **3** | HIGH |
| **Hydro DEX** | HIGH | HIGH | — | — | — | **2** | HIGH |
| **Clipper Exchange** | HIGH | — | MED | — | — | **2** | HIGH |
| **ADX Flash Loans** | HIGH | — | — | HIGH | — | **2** | HIGH |
| **Conditional Tokens** | HIGH | — | MED | — | HIGH | **3** | HIGH |
| **FEG Token/Stake** | — | HIGH | MED | — | — | **2** | HIGH |
| **Floor Token** | — | HIGH | — | — | — | **1** | HIGH |
| **Lien Protocol** | — | HIGH | MED | — | — | **2** | HIGH |
| **Liquidity Pool V2** | — | — | MED | — | — | **1** | MEDIUM |
| **Kyber Fee** | — | — | MED | MED | — | **2** | MEDIUM |
| **DAOVault** | — | — | — | MED | — | **1** | MEDIUM |
| **WETH Strategy** | — | — | MED | — | — | **1** | MEDIUM |

---

## Top 5 Most Dangerous Contracts (by failure shape coverage × severity)

### 1. MasterChef — 5/5 shapes, all CRITICAL
Every failure shape hits this contract. The `migrate()` function alone is a triple threat (envelope, authority, config). No reentrancy guards. Governance controls everything with no timelock.

### 2. Compound V1 MoneyMarket — 5/5 shapes, all CRITICAL
Single admin key controls the entire economic model (oracle, rates, risk params, equity withdrawal). No timelock. No bounds. This is the exact Moonwell failure shape at scale.

### 3. BentoBox/DegenBox — 4/5 shapes, all CRITICAL
Universal vault accepting any token with no reentrancy guard, effects-before-interactions, `batch()` as generic `delegatecall` executor, master contract approval extending to all clones, and elastic/base accounting that diverges under donation.

### 4. CelerWallet — 4/5 shapes, mostly CRITICAL
Multi-layer authority with transferable operators, unbound withdrawal destinations, and cross-wallet pivot potential.

### 5. Opyn PerpVault — 4/5 shapes, CRITICAL
Owner-controlled module system (Safe modules analog) where action contracts receive vault WETH and execute arbitrary logic.

---

## Cross-Cutting Insights

### Anti-patterns that survived audits (why these exist)

0. **msg.value reuse in batch/multicall delegatecall loops.** BentoBox's `batch()` does `delegatecall` in a loop — every subcall sees the same `msg.value`. This was exploited in production (SushiSwap BentoBox exploit). The "envelope" authenticates nothing; the payload is arbitrary delegatecall data.

1. **No timelock on critical setters.** Nearly every CRITICAL finding shares this. Curve's `MIN_RAMP_TIME` and EtherDelta's "fee can only decrease" are rare correct examples.

2. **Effects-before-interactions without reentrancy guards.** BentoBox, xSushi, MasterChef, ADX — all update state before external calls with no `nonReentrant`. ConvexStakingWrapper HAS `nonReentrant` but the reward inflation is within a single call.

3. **"Any token" surfaces.** BentoBox, EtherDelta, MasterChef (via migrator), Smoothy — accepting arbitrary token addresses turns every ERC777/fee-on-transfer/rebasing token into an attack vector.

4. **Master contract / module / action patterns.** BentoBox master contracts, Opyn actions, Marketing Mining delegation — all are "locally reasonable" plugin systems where one compromised module drains everything.

5. **Reward distribution without balance validation.** Harvest Reward Pool, ConvexStakingWrapper (timing), MasterChef (double-claim) — reward accounting that promises more than exists.

### The failure shape that matters most on 9 March 2026

**Shape 3 (Live Config / Governance / Rollout Semantics)** is the most likely next real-world hit because:
- It doesn't require a smart contract bug — just a wrong governance proposal
- It's the hardest to audit (can't review future parameter values)
- Moonwell proved it in February 2025 ($1.78M bad debt from one oracle config call)
- Every contract with admin-settable oracles/rates/implementations is permanently exposed

The exact payload will be: a governance proposal that passes, sets a parameter that looks reasonable, and breaks a system-level invariant that nobody checked. The code is correct. The configuration isn't.
