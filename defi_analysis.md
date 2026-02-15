# DeFi Contract Analysis

## TerminalV1 (0xd569d3cce55b71a8a3f3c418c329a66e5f714431) - 5,130 ETH
- Type: Treasury/funding protocol (Juicebox V1)
- Source verified: yes (multi-file Solidity 0.8.6)
- Key functions: `pay()` (payable, permissionless), `tap()` (permissionless, withdraws from funding cycle), `redeem()` (burn tickets for ETH), `addToBalance()` (payable), `migrate()` (governance-gated), `printPreminedTickets()`, `printReservedTickets()`
- Value flows: ETH enters via `pay()` and `addToBalance()`. ETH exits via `tap()` (project owners withdraw according to funding cycle rules), `redeem()` (ticket holders burn for proportional ETH), and payout mods (splits to addresses/allocators). Fee taken on `tap()` sent to governance.
- Access control: `tap()` is permissionless (anyone can trigger for any project). `redeem()` is permissionless for ticket holders. `migrate()` and `allowMigration()` are onlyGov. Fee setting is onlyGov. `printPreminedTickets` requires project operator permission via Operatable.
- Attack surfaces: (1) `tap()` is fully permissionless -- anyone can tap a project's funding cycle if conditions met, potentially front-running project operators. (2) `redeem()` calculates claimable overflow proportionally -- share price manipulation via donation/large pay could be exploited. (3) Price oracle dependency (`prices.getETHPriceFor`) for currency conversion in `tap()`. (4) Payout mods can target arbitrary addresses/allocators with delegatecall-like patterns. (5) Complex funding cycle configuration could lead to unexpected fund release.
- Prior audit status: Juicebox V1 was audited (referenced in community). Well-known protocol.
- PRIORITY: MEDIUM -- permissionless `tap()` and `redeem()` with oracle dependency and complex accounting are notable, but this is a well-audited, widely-used protocol.

---

## Bridge (0xe61dd9ca7364225afbfb79e15ad33864424e6ae4) - 2,026 ETH
- Type: Cross-chain bridge (multi-sig operator controlled)
- Source verified: yes (flat Solidity, 895 lines)
- Key functions: `depositNative()` (payable, permissionless), `depositToken()`, `withdrawNative()` (onlyOperator, multi-sig), `withdrawToken()` (onlyOperator, multi-sig), `modifyAdminAddress()` (whenPaused), `setDepositSelector()`, `setWithdrawSelector()`
- Value flows: ETH enters via `depositNative()` (permissionless). ETH exits via `withdrawNative()` which requires `onlyOperator` + multi-sig task approval (`supportTask` with `operatorRequireNum` confirmations). Token withdrawals use configurable function selectors (`withdrawSelector`).
- Access control: Multi-sig with owners/operators/pausers. Withdrawals require operator multi-sig (N of M). `modifyAdminAddress()` only works when paused. Owner can set fees. Operators control withdraw/deposit selectors for arbitrary tokens.
- Attack surfaces: (1) `setDepositSelector` / `setWithdrawSelector` allow operators to set **arbitrary function selectors** for token interactions -- if an operator is compromised, they could set a selector that calls a malicious function. (2) `depositTokenLogic` uses low-level `token.call(abi.encodeWithSignature(...))` with operator-controlled selectors -- potential arbitrary call vector. (3) Multi-sig operator compromise is the main risk vector. (4) `modifyAdminAddress` when paused could be exploited if pause is somehow triggered.
- Prior audit status: Not mentioned in source.
- PRIORITY: MEDIUM -- all withdrawals are operator-gated with multi-sig. The arbitrary selector pattern is concerning but requires operator compromise.

---

## CollSurplusPool (0x3d32e8b97ed5881324241cf03b2da5e2ebce5521) - 1,605 ETH
- Type: Collateral surplus holding pool (Liquity protocol)
- Source verified: yes (multi-file Solidity 0.6.11)
- Key functions: `accountSurplus()` (only TroveManager), `claimColl()` (only BorrowerOperations), `getETH()`, `getCollateral()`, `receive()` (only ActivePool)
- Value flows: ETH enters only from ActivePool via `receive()`. ETH exits only via `claimColl()` which can only be called by BorrowerOperations contract. Surplus is tracked per-account by TroveManager.
- Access control: Extremely strict. After `setAddresses()` (onlyOwner, then ownership renounced), all state-changing functions require caller to be specific Liquity system contracts (BorrowerOperations, TroveManager, ActivePool). No permissionless withdrawal path.
- Attack surfaces: Minimal direct attack surface. Ownership is renounced after initialization. All functions require specific trusted contract callers. Attack would need to go through BorrowerOperations or TroveManager.
- Prior audit status: Liquity is extensively audited (Trail of Bits, Coinspect). Very well-known.
- PRIORITY: LOW -- no permissionless value extraction paths; all gated by Liquity system contracts.

---

## MarketingMiningDelegator (0x0feccb11c5b61b3922c511d0f002c0b72d770dce) - 1,523 ETH (PROXY)
- Type: Yield farming / staking with referral system (ShardingDAO)
- Source verified: yes (flat Solidity, proxy -> impl at 0xab2cc3ab140e7596c5de18d1269ac39c53bd0db0)
- Key functions: `depositETH()` (payable, permissionless with invitation), `withdrawETH()` (permissionless for depositors), `deposit()`, `withdraw()`, `addAvailableDividend()`, `setDividendWeight()`, `transferAdmin()`
- Value flows: ETH enters via `depositETH()`. ETH exits via `withdrawETH()` which sends ETH directly to msg.sender. Rewards distributed in SHD token based on pool weight calculations. Complex invitation/referral system modifies weights.
- Access control: Deposits require accepted invitation (`invitor != address(0)`). Admin functions gated by `admin` address (not owner -- separate role). `transferAdmin()` requires current admin. Some setters like `setDividendWeight` and `setTokenAmountLimit` check for admin, not owner. Delegator pattern means implementation can be changed by admin.
- Attack surfaces: (1) **Delegator/proxy pattern** -- admin can change implementation address, potentially to malicious code. (2) `withdrawETH` uses `msg.sender.call{value: _amount}` -- reentrancy possible but amount is deducted from `user.amount` before transfer in `updateAfterwithdraw`. (3) Complex weight calculation with invitation system could have accounting bugs -- invitor weight updates interleave with user weight updates. (4) `setDividendWeight`, `setTokenAmountLimit`, `setContracSenderFeeRate` have inconsistent access control (some check admin, some check admin differently). (5) `transferAdmin` only requires current admin, no timelock. (6) Implementation upgrade path has no timelock or multi-sig.
- Prior audit status: Not mentioned in source.
- PRIORITY: HIGH -- proxy with admin-upgradeable implementation, complex accounting with invitation weights, inconsistent access control, and 1,523 ETH at stake.

---

## Hourglass (0xb3775fb83f7d12a36e0475abdd1fca35c091efbe) - 2,159 ETH
- Type: Ponzi/dividend token (PoWH3D / P3D clone)
- Source verified: yes (flat Solidity, 807 lines)
- Key functions: `buy()` (payable, permissionless), `sell()` (permissionless), `withdraw()` (permissionless), `exit()` (sell + withdraw), `reinvest()`, `transfer()` (with 10% fee)
- Value flows: ETH enters via `buy()` or fallback (permissionless). 10% fee on buy distributed as dividends. ETH exits via `withdraw()` (claim dividends) and `sell()` converts tokens back to ETH (minus 10% dividend fee). Transfer also takes 10% fee.
- Access control: Admin can only `disableInitialStage()`, `setAdministrator()`, `setStakingRequirement()`, `setName()`. No admin withdrawal function. Value extraction is fully permissionless for token holders.
- Attack surfaces: (1) Classic P3D dividend math with `profitPerShare_` and `payoutsTo_` using `int256` -- historically had overflow/underflow bugs in similar contracts. (2) `sell()` updates `payoutsTo_` with `(int256) (profitPerShare_ * _tokens + (_taxedEthereum * magnitude))` -- potential integer overflow if profitPerShare_ is very large. (3) Ambassador quota system during initial phase could be manipulated. (4) Division by `tokenSupply_` when distributing dividends -- if tokenSupply_ drops to very small values, precision issues arise. (5) No reentrancy guard on `withdraw()` which does `.transfer()` (2300 gas limit mitigates but doesn't eliminate all risk).
- Prior audit status: PoWH3D/P3D had known exploits historically. This appears to be a clone.
- PRIORITY: HIGH -- fully permissionless buy/sell/withdraw with complex dividend math, large ETH balance, and historical precedent of exploits in similar contracts.

---

## StabilityPool (0x66017d22b0f8556afdd19fc67041899eb65a21bb) - 649 ETH
- Type: Stability pool (Liquity protocol)
- Source verified: yes (multi-file Solidity 0.6.11)
- Key functions: `provideToSP()` (permissionless), `withdrawFromSP()` (permissionless), `withdrawETHGainToTrove()` (permissionless), `offset()` (only TroveManager), `registerFrontEnd()`
- Value flows: LUSD enters via `provideToSP()`. ETH enters via `offset()` (liquidation gains from TroveManager). ETH exits to depositors via `withdrawFromSP()` and `withdrawETHGainToTrove()`. LQTY rewards distributed to depositors and front ends.
- Access control: `provideToSP()` and `withdrawFromSP()` are permissionless for depositors (withdraw their own). `offset()` restricted to TroveManager. `registerFrontEnd()` permissionless but one-time.
- Attack surfaces: (1) Complex epoch/scale accounting with P, S, G snapshots -- potential precision loss in edge cases. (2) `_sendETHGainToDepositor` sends ETH without reentrancy guard (but Liquity has been thoroughly reviewed). (3) Front-end kickback rate system adds complexity but is well-tested.
- Prior audit status: Liquity extensively audited by Trail of Bits, Coinspect.
- PRIORITY: LOW -- well-audited Liquity contract with strong access controls.

---

## LiquidityPoolV2 (0x35ffd6e268610e764ff6944d07760d0efe5e40e5) - 413 ETH
- Type: Lending/flash-loan liquidity pool (Keeper DAO / KeeperDAO)
- Source verified: yes (flat Solidity, upgradeable proxy pattern)
- Key functions: `deposit()` (payable, permissionless), `withdraw()` (permissionless for kToken holders), `borrow()` (flash loan, permissionless), `register()` (onlyOperator), `migrate()` (onlyOperator), `recoverTokens()` (onlyOperator)
- Value flows: ETH enters via `deposit()`. Users receive kTokens. ETH exits via `withdraw()` (burn kTokens for underlying). Flash loans via `borrow()` -- borrows and must repay within same tx plus fee. `migrate()` can move all funds to a new LP.
- Access control: Deposit/withdraw permissionless. `borrow()` permissionless but requires repayment. Operator controls: register tokens, set fees, migrate, recover tokens, pause. Upgradeable proxy with admin.
- Attack surfaces: (1) `borrow()` flash loan -- borrower proxy calls `lend()` on arbitrary borrower contract with borrowed funds. If fee calculation or balance check is wrong, could drain pool. (2) `migrate()` (onlyOperator) can move ALL funds to a new LP address -- operator compromise drains everything. (3) `calculateMintAmount` and `calculateWithdrawAmount` use kToken supply ratios -- first depositor / empty pool edge cases. (4) Upgradeable proxy -- admin can upgrade implementation. (5) `recoverTokens()` could be used to extract tokens (but blacklisted registered tokens).
- Prior audit status: KeeperDAO was audited.
- PRIORITY: MEDIUM -- flash loan mechanism and operator migration path are concerning, but relatively small balance.

---

## FoMo3Dlong (0xa62142888aba8370742be823c1782d17a0389da1) - 1,119 ETH
- Type: Game/gambling (FoMo3D -- last-key-buyer wins pot)
- Source verified: yes (flat Solidity, 2041 lines)
- Key functions: `buyXid()`, `buyXaddr()`, `buyXname()` (payable, permissionless key purchases), `withdraw()` (permissionless earnings withdrawal), `registerNameXID/Xaddr/Xname()` (payable name registration)
- Value flows: ETH enters via key purchases (`buyX*`). ETH is distributed: portion to existing key holders as dividends, portion to pot, portion to affiliates, portion to community (P3D). When round timer expires, last buyer wins the pot. `withdraw()` claims accumulated earnings.
- Access control: `withdraw()` has `isActivated()` and `isHuman()` modifiers (no contracts). Key purchases are permissionless. No admin withdrawal function. Round activation is controlled.
- Attack surfaces: (1) Famous for the "dark forest" block-stuffing attack -- attacker buys last key and fills subsequent blocks to prevent anyone else from buying. (2) `isHuman()` modifier only checks `msg.sender == tx.origin` -- can be bypassed in some contexts. (3) Complex multi-round accounting with player earnings across rounds. (4) `withdrawEarnings()` modifies multiple state vars -- potential accounting manipulation. (5) Affiliate referral system with cascading payments. (6) The contract holds 1,119 ETH which may represent unclaimed winnings/dividends from old rounds.
- Prior audit status: Well-known game contract from 2018. The block-stuffing exploit was publicly documented.
- PRIORITY: MEDIUM -- most funds are likely locked in game mechanics. The main attack (block-stuffing) is well-known. Remaining ETH is likely unclaimed player earnings.

---

## R1Exchange (0xc7c9b856d33651cc2bcd9e0099efa85f59f78302) - 150 ETH
- Type: Decentralized exchange (order-book DEX)
- Source verified: yes (flat Solidity, 558 lines, old pragma)
- Key functions: `deposit()` (payable, permissionless), `depositToken()`, `withdraw()` (permissionless with apply/approve mechanism), `withdrawNoLimit()` (when enabled), `applyWithdraw()`, `approveWithdraw()` (onlyAdmin), `adminWithdraw()` (onlyAdmin), `trade()` (onlyAdmin), `innerTransfer()`, `refund()` (onlyAdmin)
- Value flows: ETH enters via `deposit()`. ETH exits via `withdraw()` (two paths: admin-approved or time-locked after apply). `withdrawNoLimit()` available when `withdrawEnabled`. Admin can execute trades matching signed orders.
- Access control: Deposit is permissionless. Withdrawal has two paths: (1) apply + wait lock time, then withdraw; (2) admin approves immediately. Trading is onlyAdmin. Owner controls enable/disable flags.
- Attack surfaces: (1) **Time-lock bypass**: `withdraw()` allows self-service withdrawal after `applyWait` period (max 7 days). Anyone who deposited can eventually withdraw regardless of admin approval. (2) `trade()` signature verification -- `ecrecover` on order hashes. Signature malleability or hash collision could forge trades. (3) `adminWithdraw` uses ecrecover -- standard v,r,s signature which is malleable (no EIP-712). (4) `refund()` is admin-only but can send any user's balance to them. (5) Channel system adds complexity. (6) Old Solidity version without overflow protection (but uses SafeMath).
- Prior audit status: Not mentioned.
- PRIORITY: LOW -- small balance (150 ETH), and withdrawal is time-locked + permissionless path exists for own funds.

---

## WrapperLockEth (0xaa7427d8f17d87a28f5e1ba3adbb270badbe1011) - 950 ETH
- Type: Wrapped ETH with time-lock (Ethfinex/DeversiFi)
- Source verified: yes (flat Solidity, 304 lines)
- Key functions: `deposit()` (payable, permissionless with time-lock), `withdraw()` (permissionless after lock or with signer signature), `transferFrom()` (restricted to transfer proxies), `addSigner()` (any existing signer), `withdrawDifferentToken()` (onlyOwner)
- Value flows: ETH enters via `deposit()` with a lock period (`_forTime` hours). ETH exits via `withdraw()` -- either after lock expires or with a valid signer signature before lock expires. `transferFrom()` only works through hardcoded TRANSFER_PROXY addresses and requires signer participation.
- Access control: Deposit permissionless. Withdraw permissionless after lock. Early withdraw requires signer signature. `addSigner()` can be called by any existing signer (no owner check!). Owner can withdraw OTHER tokens (not ETH).
- Attack surfaces: (1) **CRITICAL: `totalSupply_` bug in `withdraw()`** -- line `totalSupply_ = totalSupply_.sub(msg.value)` uses `msg.value` instead of `_value`. Since `withdraw()` is not payable, `msg.value` is always 0, so `totalSupply_` is never decremented on withdrawal. This is a confirmed bug but doesn't directly enable theft -- it corrupts the totalSupply accounting. (2) **`addSigner()` is callable by ANY existing signer** with no owner/admin check -- if any signer is compromised, they can add arbitrary new signers who can then approve early withdrawals for anyone. (3) Signature scheme uses simple `ecrecover(keccak256("\x19Ethereum Signed Message:\n32", hash), v, r, s)` -- no EIP-712, basic replay protection only via `signatureValidUntilBlock`. (4) `allowance()` returns max uint256 for transfer proxies -- unlimited approval. (5) Hardcoded proxy addresses.
- Prior audit status: Ethfinex/DeversiFi -- likely audited but the totalSupply bug suggests issues were missed.
- PRIORITY: HIGH -- 950 ETH with signer escalation vulnerability (`addSigner` callable by any signer), confirmed `totalSupply` accounting bug, and weak signature scheme.

---

## EtherToken (0xb59a226a2b8a2f2b0512baa35cc348b6b213b671) - 3,420 ETH
- Type: Wrapped ETH (Neufund EtherToken -- ERC223 compatible WETH)
- Source verified: yes (flat Solidity, 883 lines)
- Key functions: `deposit()` (payable, permissionless), `withdraw()` (permissionless for own balance), `transfer()` (ERC20+ERC223), `transferFrom()`, `reclaim()` (recover tokens sent to contract, restricted)
- Value flows: ETH enters via `deposit()`. ETH exits via `withdraw()` (burns wrapped tokens, sends ETH). Standard WETH-like 1:1 wrapping.
- Access control: `deposit()` and `withdraw()` are permissionless. `transfer`/`transferFrom` use standard ERC20 patterns with AccessPolicy role checks. `reclaim()` prevents reclaiming ETH (only other tokens). Access controlled via external IAccessPolicy contract.
- Attack surfaces: (1) ERC223 `transfer(address, uint256, bytes)` calls `onTokenTransfer` callback on receiving contracts -- potential reentrancy vector (but state is updated before callback). (2) External AccessPolicy dependency -- if policy contract is compromised, transfer restrictions could be bypassed. (3) Standard WETH-like accounting is simple and well-tested. (4) `reclaim()` explicitly blocks ETH reclamation.
- Prior audit status: Neufund platform was audited.
- PRIORITY: LOW -- simple WETH-like design, large balance but straightforward accounting with no obvious permissionless extraction vectors beyond normal withdraw-your-own-deposit.

---

## EthCustodian (0x6bfad42cfc4efc96f529d786d643ff4a8b89fa52) - 998 ETH
- Type: Cross-chain bridge custodian (Rainbow Bridge -- Ethereum to NEAR)
- Source verified: yes (multi-file Solidity 0.6.12)
- Key functions: `depositToEVM()` (payable, permissionless), `depositToNear()` (payable, permissionless), `withdraw()` (permissionless with NEAR proof), `adminPause()`, `adminSstore()`, `adminSendEth()`, `adminDelegatecall()`
- Value flows: ETH enters via `depositToEVM()` and `depositToNear()`. ETH exits via `withdraw()` which requires a valid proof from NEAR blockchain (verified by INearProver). Admin can also send ETH via `adminSendEth()`.
- Access control: Deposits permissionless. `withdraw()` permissionless but requires valid NEAR proof (`_parseAndConsumeProof`). Admin has extremely powerful functions: `adminSstore()` (arbitrary storage write!), `adminSendEth()` (send any ETH), `adminDelegatecall()` (arbitrary delegatecall!). Pausable by admin.
- Attack surfaces: (1) **`adminSstore()`** allows arbitrary storage slot writes -- admin can modify ANY state variable. (2) **`adminDelegatecall()`** allows delegatecall to any address -- admin can execute arbitrary code in contract context. (3) **`adminSendEth()`** can drain all ETH. (4) If NEAR prover is compromised or produces false proofs, `withdraw()` could drain funds. (5) Proof replay protection via `usedProofs` mapping but depends on prover correctness. (6) `result.ethCustodian == address(this)` check prevents cross-custodian confusion but is in the decoded proof data.
- Prior audit status: Rainbow Bridge has been audited (Aurora/NEAR security team).
- PRIORITY: MEDIUM -- admin has god-mode powers but is presumably a trusted multisig. The bridge proof verification is the critical trust assumption. 998 ETH at stake.

---

## IDOLvsETHBoxExchange (0x767696e13ff990d09954c7a36a49e2c4a1c804bd) - 82 ETH
- Type: Orderbook DEX / Box exchange (Lien Finance)
- Source verified: yes (flat Solidity, 2496 lines)
- Key functions: `orderEthToToken()`, `orderTokenToEth()`, `addLiquidity()`, `removeLiquidity()`, `executeUnexecutedBox()` (permissionless), `withdrawETH()` (permissionless), `sendMarketFeeToLien()`
- Value flows: ETH enters via orders and liquidity provision. ETH exits via `withdrawETH()` (claims ethBalances[msg.sender]). Box execution batches orders at a uniform price.
- Access control: All functions are permissionless. `withdrawETH()` withdraws only msg.sender's balance. `executeUnexecutedBox()` can be triggered by anyone.
- Attack surfaces: (1) `withdrawETH()` sets balance to 0 before transfer (safe pattern). (2) Oracle dependency for price/volatility calculations. (3) Box execution ordering could be manipulated. (4) Small balance reduces incentive for attack.
- Prior audit status: Lien Finance was audited.
- PRIORITY: LOW -- small balance (82 ETH), permissionless but well-structured withdrawal.

---

## ProfitSharing (0x6822aaf4ab22e6cca8352a927b9ae0a8fdb58d9d) - 111 ETH
- Type: Dividend distribution contract (MiniMeToken-based)
- Source verified: yes (flat Solidity, 757 lines)
- Key functions: `depositDividend()` (payable, onlyOwner), `claimDividend()` (permissionless), `claimDividendAll()` (permissionless), `recycleDividend()` (onlyOwner)
- Value flows: ETH enters via `depositDividend()` (owner-only). ETH exits via `claimDividend()` -- proportional to token balance at dividend block snapshot (MiniMeToken `balanceOfAt`).
- Access control: Deposit is owner-only. Claiming is permissionless for token holders. Recycle (reclaim unclaimed after 1 year) is owner-only.
- Attack surfaces: (1) `claimDividend()` uses `msg.sender.transfer(claim)` -- reentrancy possible through `claimDividendAll()` loop, but `dividend.claimed[msg.sender]` is set to true BEFORE transfer. (2) MiniMeToken snapshot dependency -- if MiniMeToken `balanceOfAt` is manipulable, claims could be inflated. (3) `claimDividendAll()` loop could run out of gas with many dividends. (4) No reentrancy guard but claim flag is set before transfer.
- Prior audit status: Not mentioned.
- PRIORITY: LOW -- small balance, straightforward dividend math with proper claim-before-transfer pattern.

---

## RelayHub (0xd216153c06e857cd7f72665e0af1d7d82172f494) - 521 ETH
- Type: Gas Station Network relay hub (GSN v1)
- Source verified: yes (flat Solidity, 1844 lines)
- Key functions: `stake()` (payable, for relay operators), `depositFor()` (payable, for dapp balances), `withdraw()` (permissionless for own balance), `unstake()` (for relay owners after delay), `relayCall()` (relay executes meta-tx), `penalizeRepeatedNonce()`, `penalizeIllegalTransaction()`
- Value flows: ETH enters via `stake()` (relay operators) and `depositFor()` (dapps depositing for gas). ETH exits via `withdraw()` (dapps withdraw own deposits) and `unstake()` (relay owners after unstake delay). Relayed calls charge dapp deposits.
- Access control: `withdraw()` is permissionless for msg.sender's own balance. `unstake()` requires relay owner + unstake delay elapsed. Penalize functions are permissionless (anyone can penalize misbehaving relays with proof).
- Attack surfaces: (1) `withdraw()` straightforward -- msg.sender withdraws own `balances[msg.sender]` balance. (2) Penalization system -- `penalizeRepeatedNonce` and `penalizeIllegalTransaction` slash relay stakes and reward reporter. If signature verification has issues, false penalization could drain stakes. (3) Complex relay call flow with pre/post relay hooks, gas accounting, and nonce management. (4) `relayCall()` signature verification via ecrecover. (5) The 521 ETH is likely relay stakes + dapp deposits.
- Prior audit status: GSN v1 was audited by OpenZeppelin.
- PRIORITY: LOW -- well-audited GSN infrastructure, all withdrawals are for own balance only.

---

## CelerWallet (0xa6cd930fc92f1634d8183af2fb86bd1766f2f82a) - 384 ETH
- Type: Payment channel wallet (Celer Network)
- Source verified: yes (flat Solidity, 722 lines)
- Key functions: `create()` (permissionless, creates wallet), `depositETH()` (payable), `depositERC20()`, `withdraw()` (onlyOperator + onlyWalletOwner), `transferToWallet()` (onlyOperator), `transferOperatorship()` (onlyOperator), `proposeNewOperator()` (onlyWalletOwner), `drainToken()` (onlyPauser, whenPaused)
- Value flows: ETH enters via `depositETH()` into wallet IDs. ETH exits via `withdraw()` (requires operator + receiver is wallet owner). Emergency `drainToken()` when paused, pauser-only.
- Access control: Wallet operations require operator (typically CelerLedger contract). Withdrawal requires both operator AND receiver to be a wallet owner. `drainToken()` is emergency-only (paused + pauser role). Wallet owners can propose new operator via unanimous vote.
- Attack surfaces: (1) `drainToken()` when paused can extract any amount -- pauser role is critical. (2) Operator (CelerLedger) controls all fund movements -- if ledger is compromised, all wallets are at risk. (3) `proposeNewOperator()` requires all owners to agree, but if there's only one owner, they can unilaterally change operator. (4) Wallet ID is `keccak256(address(this), msg.sender, _nonce)` -- predictable.
- Prior audit status: Celer Network was audited.
- PRIORITY: LOW -- funds are distributed across many wallets, controlled by CelerLedger. No direct permissionless extraction.

---

## EtherFlip (0xe5a04d98538231b0fab9aba60cd73ce4ff3039df) - 753 ETH
- Type: Gambling / coin flip game (Oraclize-based)
- Source verified: yes (flat Solidity, 1243 lines, very old pragma)
- Key functions: `fallback()` (payable -- placing bets), `__callback()` (Oraclize callback -- resolving bets), `refundTransfer()` (ownerAction), `updateMaxMinComparables()` (ownerAction), `updateOwner()` (ownerAction)
- Value flows: ETH enters via fallback function (betting). ETH exits via `__callback()` (winning payouts at 2x minus fees) and `refundTransfer()` (owner refunds). Owner can also send ETH/tokens via `walletSend()`.
- Access control: Betting is permissionless (within min/max bet). Payouts handled by Oraclize callback (only from `oraclize_cbAddress()`). All config functions are `ownerAction`. Owner can `refundTransfer()` arbitrary amounts.
- Attack surfaces: (1) **Oraclize/Provable is deprecated** -- if the oracle service is no longer running, bets may be stuck (ETH sent but no callback). (2) **`refundTransfer()` allows owner to drain all ETH**. (3) Random number generation: `uint(sha3(_result)) % 2**(2*8)` -- if Oraclize proof verification fails, refund is given, but if random source is predictable, outcomes could be manipulated. (4) Fee calculation `(feeMultiple - 3) * incrementFee` could underflow if `feeMultiple < 3` (when bet is small relative to `incrementDivisor`). (5) The 753 ETH may represent stale/abandoned contract funds if Oraclize is no longer active.
- Prior audit status: Not mentioned.
- PRIORITY: HIGH -- 753 ETH potentially stuck in abandoned gambling contract. Owner can drain via `refundTransfer()`. If Oraclize service is dead, bets cannot resolve. Potential arithmetic underflow in fee calculation.

---

## HONG (0x9fa8fa61a10ff892e4ebceb7f4e0fc684c2ce0a9) - 1,003 ETH
- Type: DAO/Investment fund token (HONG token -- DAO-like governance)
- Source verified: yes (flat Solidity, 817 lines, very old pragma)
- Key functions: `createTokenProxy()` (payable -- buy tokens during ICO), `refundMyIcoInvestment()` (permissionless refund before lock), `mgmtInvestProject()` (management-only), `mgmtDistribute()` (management-only), `kickoff()` (management-only fiscal year), `harvest()` (management-only final year)
- Value flows: ETH entered via token creation (ICO). ETH exits via `refundMyIcoInvestment()` (pre-lock refund), management fund operations, and distribution. Complex fiscal year system with fund lock/release.
- Access control: Token creation was during ICO period. Refunds only before fund lock. Management body controls investments, distributions, bounty tokens, and fiscal year progression. Token holder voting for freeze/kickoff actions.
- Attack surfaces: (1) Very old Solidity (no pragma version visible, uses `throw`). (2) `refundMyIcoInvestment()` -- if fund is not locked, token holders can get refund. Uses `msg.sender.send()` which is vulnerable to reentrancy but state is updated before. (3) Tiered token pricing with complex math -- potential rounding issues. (4) `extraBalanceWallet.returnAmountToMainAccount()` external call during refund. (5) Fund is likely locked (`isFundLocked`), making most extraction paths unavailable. (6) The 1,003 ETH is probably locked investment fund.
- Prior audit status: Not mentioned. Very old contract (2017-era DAO pattern).
- PRIORITY: MEDIUM -- 1,003 ETH likely locked in DAO fund. If fund is not locked, refund path exists. Old Solidity with potential issues but complex governance may protect funds.

---

## GandhiJi (0x167cb3f2446f829eb327344b66e271d1a7efec9a) - 664 ETH
- Type: Ponzi/dividend token (P3D/PoWH3D clone -- very similar to Hourglass)
- Source verified: yes (flat Solidity, 729 lines)
- Key functions: `buy()` (payable, permissionless), `sell()` (permissionless), `withdraw()` (permissionless), `exit()` (sell + withdraw), `reinvest()`, `transfer()` (with fee)
- Value flows: Identical to Hourglass/P3D pattern. ETH enters via `buy()`, 15% fee distributed as dividends. ETH exits via `sell()` + `withdraw()`. Transfer takes fee.
- Access control: Same as Hourglass -- admin can only set name/symbol/staking requirement. No admin drain function.
- Attack surfaces: Same as Hourglass: (1) `int256` overflow in dividend tracking. (2) Division precision issues when tokenSupply is small. (3) Ambassador/initial stage manipulation. (4) No reentrancy guard (uses `.transfer()` with 2300 gas limit). (5) `dividendFee_ = 15` (6.67% fee vs Hourglass 10%) changes the economics.
- Prior audit status: Clone of known vulnerable contract pattern.
- PRIORITY: HIGH -- 664 ETH in a P3D clone with known historical vulnerability patterns. Same dividend math issues as Hourglass.

---

## L1_ETH_Bridge (0xb8901acb165ed027e32754e0ffe830802919727f) - 613 ETH
- Type: L1 bridge (Hop Protocol)
- Source verified: yes (multi-file Solidity 0.6.12)
- Key functions: `sendToL2()` (payable, permissionless -- send ETH to L2), `bondTransferRoot()` (bonder-only), `confirmTransferRoot()` (L2 bridge only), `challengeTransferRoot()` (permissionless), `resolveChallenge()`, `withdraw()` (via Merkle proof from bonded root)
- Value flows: ETH enters via `sendToL2()`. ETH exits via withdrawal with Merkle proof against bonded transfer roots. Bonders stake collateral and bond transfer roots. Challenge mechanism allows disputing fraudulent roots.
- Access control: Sending is permissionless. Bonding requires bonder role. Root confirmation requires L2 bridge verification via messenger wrapper. Withdrawals require valid Merkle proof. Governance can set parameters.
- Attack surfaces: (1) Bonder can bond fraudulent roots -- mitigated by challenge period (1 day) and staking. (2) Messenger wrapper trust -- if `verifySender` in messenger wrapper is exploitable, false root confirmations possible. (3) Merkle proof verification for withdrawals. (4) Challenge resolution timing -- `challengeResolutionPeriod` (10 days). (5) `_transferFromBridge` uses `recipient.call{value: amount}` -- potential reentrancy but amount tracking in Accounting.sol.
- Prior audit status: Hop Protocol was audited.
- PRIORITY: LOW -- well-audited bridge protocol with challenge mechanism. Withdrawal requires valid Merkle proof.

---

## Floor (0x40ed3699c2ffe43939ecf2f3d11f633b522820ad) - 336 ETH
- Type: Token floor price mechanism (XVIX protocol)
- Source verified: yes (multi-file Solidity 0.6.12)
- Key functions: `refund()` (permissionless -- burn XVIX tokens for ETH at floor price), `getRefundAmount()` (view), `getMaxMintAmount()` (view), `capital()` (view)
- Value flows: ETH held as `capital` backing XVIX token floor price. ETH exits via `refund()` -- anyone holding XVIX can burn tokens and receive 90% of proportional ETH (`REFUND_BASIS_POINTS = 9000`). 10% of ETH is retained, increasing the floor price for remaining holders.
- Access control: `refund()` is permissionless for XVIX holders. `capital` is set during construction and modified only via `refund()` (decrease) and receiving ETH. XVIX burn requires msg.sender to hold XVIX.
- Attack surfaces: (1) `refund()` formula: `capital * _tokenAmount / totalSupply * 9000 / 10000` -- if totalSupply is manipulated (e.g., by large XVIX burn), the refund ratio changes for remaining holders. (2) NonReentrant guard present. (3) XVIX token has `burn()` restricted to Floor contract only. (4) Minter contract controls new XVIX minting -- if minter creates too many XVIX per ETH, floor price drops. (5) The 336 ETH represents the backing capital for XVIX floor price.
- Prior audit status: XVIX protocol -- not sure of formal audit.
- PRIORITY: MEDIUM -- 336 ETH with permissionless `refund()`. The economics are designed so that refund always returns less than the proportional ETH (90%), but large-scale burn could have edge effects.

