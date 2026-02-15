# DeFi Contract Analysis - Batch 2

## Summary

Analyzed 20 contracts (including proxy implementations) from Etherscan-verified sources.
Source code saved to `/home/user/contracs/src_cache/`.

---

## Joyso (0x04f062809b244e37e7fdc21d9409469c989c2342) - 85 ETH
- Type: Off-chain order matching DEX (centralized matching, on-chain settlement)
- Solidity: 0.4.19
- Key functions: `depositToken`, `depositEther`, `withdraw`, `matchByAdmin_TwH36`, `matchTokenOrderByAdmin_k44j`, `withdrawByAdmin_Unau`, `cancelByAdmin`, `migrateByAdmin_DQV`, `lockMe/unlockMe`
- Architecture: Users deposit ETH/tokens, admin matches signed orders on-chain. Users can self-withdraw after a lock period (30 days default). Signature-based order verification with `ecrecover`.
- Attack surfaces:
  - Admin-controlled matching and withdrawal - admin can execute trades on behalf of users using their signatures
  - `migrateByAdmin_DQV` sends user funds to arbitrary `newContract` address (address comes from `inputs[0]`) - admin trust required
  - Signature replay protection via `usedHash` for withdrawals and `orderFills` for trades
  - `verify` uses raw `ecrecover` without checking for address(0) return (ecrecover returns 0 on invalid sig, but user lookup from userId would catch this)
  - Old Solidity 0.4.19 - no overflow protection in some places (but uses SafeMath)
  - Complex bit-packing in order data makes audit difficult
- PRIORITY: **LOW** - Centralized exchange model, 85 ETH is modest, admin-trust model by design

---

## Treasure (0x25a06d4e1f804ce62cf11b091180a5c84980d93a) - 98 ETH
- Type: Ponzi/dividend token scheme (P3D/POWH3D clone)
- Solidity: 0.4.20
- Key functions: `buy`, `sell`, `withdraw`, `reinvest`, `transfer`
- Architecture: Bonding curve token with 10% dividend fee on buy/sell. Referral system. Community and trading wallet addresses receive fees. Users buy tokens on a bonding curve, dividends are distributed to all holders.
- Attack surfaces:
  - Classic P3D clone architecture - well-known dividend calculation patterns
  - Selling mechanics use `sellingWithdrawBalance_` separate from dividend withdrawals
  - Very old Solidity with basic math operations
  - Not interesting DeFi logic - pure Ponzi mechanics
- PRIORITY: **LOW** - Ponzi token clone, no novel DeFi logic worth analyzing

---

## EthManager (0xf9fb1c508ff49f78b60d3a96dea99fa5d7f3a8a6) - 94 ETH
- Type: Harmony bridge ETH lock/unlock contract
- Solidity: 0.5.17
- Key functions: `lockEth`, `unlockEth`
- Architecture: Simple bridge manager. Users call `lockEth` to lock ETH (emits event for Harmony side). `wallet` (multisig) calls `unlockEth` to release ETH based on burn receipts from Harmony. Uses `usedEvents_` mapping to prevent receipt replay.
- Attack surfaces:
  - Single `wallet` address controls all unlocks - if wallet is compromised, all 94 ETH can be drained
  - No expiration or challenge period on unlock operations
  - `recipient.transfer(amount)` uses 2300 gas stipend (could DoS if recipient is a contract)
  - Minimal logic - bridge security depends entirely on the multisig wallet and cross-chain validation
- PRIORITY: **LOW** - Minimal on-chain logic, security depends on off-chain multisig

---

## LienToken (0xab37e1358b639fd877f015027bb62d3ddaa7557e) - 88 ETH
- Type: ERC20 dividend token with vesting (Lien protocol governance)
- Solidity: 0.6.5
- Key functions: `settleProfit`, `receiveDividend`, `createGrant`, `transfer`, `transferFrom`
- Architecture: ERC20 token that records historical balances at regular intervals ("terms"). Profit (ETH or ERC20) is settled per term, and dividends are distributed pro rata based on historical balances. Includes vesting grants. Dividends expire after `expiration` terms if unclaimed.
- Attack surfaces:
  - `receiveDividend` iterates over terms in a loop - if many terms have passed, could hit gas limits
  - `settleProfit` computes `unsettledProfit` based on contract balance minus tracked amounts - donation attacks could inflate profits for a term
  - Expired dividends are "carried over" - creates a redistribution mechanism that could be gamed by timing entries/exits around term boundaries
  - Vesting + dividend interaction could have edge cases with grant creation timing
  - Uses `call{value: total}("")` for ETH transfer (reentrancy potential, though bounded by state updates)
- PRIORITY: **MEDIUM** - Interesting dividend accounting with term-based settlement, potential donation/timing attacks, but only 88 ETH

---

## HonestDice (0xd79b4c6791784184e2755b2fc1659eaab0f80456) - 83 ETH
- Type: Gambling dice game (commit-reveal with server seed)
- Solidity: pre-0.4.x (no pragma, very old)
- Key functions: `roll`, `serverSeed`, `claim`, `claimTimeout`, `withdraw`
- Architecture: Two-phase commit-reveal dice. User submits hash of secret + bet. Server provides seed. User reveals secret to claim winnings. Max payout = 5% of bankroll. 1% house edge.
- Attack surfaces:
  - **Critical bug**: `lockBetsForWithdraw()` and `unlockBets()` use `uint betsLocked = ...` which creates a LOCAL variable shadowing the state variable - the state variable `betsLocked` is NEVER set, meaning `withdraw()` check `betsLocked == 0` always passes and owner can withdraw anytime (but this is owner-only)
  - Uses `msg.sender.send()` without checking return value (funds could be silently lost)
  - Server seed is provided by `feed` address - server can choose seed adversarially after seeing user's bet
  - Very old Solidity - no SafeMath, no visibility modifiers on functions (all public by default)
  - `Roll r = rolls[msg.sender]` creates a storage reference without `storage` keyword (works in old Solidity but confusing)
- PRIORITY: **LOW** - Simple gambling contract, server-trust model, 83 ETH

---

## E2X (0x99a923b8f3a4e41740e3f8947fd7be6aa736d8a6) - 69 ETH
- Type: HEX-clone staking/auction token (ETH-to-token transform)
- Solidity: (HEX fork)
- Key functions: `xfLobbyEnter`, `xfLobbyExit`, `stakeStart`, `stakeEnd`, `stakeGoodAccounting`
- Architecture: HEX-like token with daily "transform lobby" (auction) where ETH is bid for daily token allocation. Staking with time-locked certificates. Share rate system for T-share accounting. Referral bonuses (5% to referred, 10% to referrer).
- Attack surfaces:
  - `xfLobbyExit`: referral bonus can mint extra tokens (5% + 10%) - referral system could be self-referred for bonus
  - Self-referral check exists (`referrerAddr == msg.sender`) but can be trivially bypassed with a second address
  - Share rate calculation complexity could have edge cases at extreme values
  - Daily lobby mechanism has MEV potential (timing of entry relative to total ETH for the day)
  - Fallback function accepts ETH without action (line 1862: `function() external payable {}`)
- PRIORITY: **LOW** - HEX clone, well-studied mechanics, only 69 ETH

---

## EthPool (0x44e081cac2406a4efe165178c2a4d77f7a7854d4) - 70 ETH
- Type: Celer Network ETH pool (ERC20-like wrapper for ETH)
- Solidity: 0.5.1
- Key functions: `deposit`, `withdraw`, `approve`, `transferFrom`, `transferToCelerWallet`
- Architecture: Wraps ETH with ERC20-like approve/transferFrom semantics. Used by Celer payment channels. Users deposit ETH and get internal balances. Approved spenders can transfer ETH to other addresses or to CelerWallet contracts.
- Attack surfaces:
  - `transferToCelerWallet` calls external `wallet.depositETH.value(_value)(_walletId)` - the wallet address is caller-controlled parameter, but allowance-gated
  - `_transfer` uses `_to.transfer(_value)` (2300 gas) - could DoS if recipient is contract
  - Standard approve race condition (mitigated by increaseAllowance/decreaseAllowance)
  - No reentrancy guard, but `_transfer` updates balance before external call and uses `.transfer()` which limits gas
- PRIORITY: **LOW** - Simple ETH wrapper, well-structured, 70 ETH

---

## EulerBeats (0x8754f54074400ce745a7ceddc928fb1b7e985ed6) - 215 ETH
- Type: NFT with bonding curve for prints (ERC1155)
- Solidity: 0.7.x (pragma in source)
- Key functions: `mint` (originals), `mintPrint`, `burnPrint`, `getPrintPrice`, `getBurnPrice`
- Architecture: Original NFTs are minted at fixed price. "Prints" of originals have a bonding curve price. Print price increases with supply (exponential formula). Burn price = 90% of print price at current supply. Reserve tracks funds needed for burns. Seed owner gets 80% of fee (price - reserve cut). Owner gets remaining 20%.
- Attack surfaces:
  - **Bonding curve economics**: `getPrintPrice` uses exponential formula `(10^(B-n) * decimals) / (11^(B-n))` - potential for precision loss or unexpected behavior at boundary values
  - `burnPrint` has `minimumSupply` parameter for frontrun protection, but price depends on current supply - MEV sandwich attacks on mint/burn
  - `reserve` accounting: if `reserve` diverges from actual contract balance (e.g., through selfdestruct ETH injection), burn operations could drain more than intended
  - `_refundSender` sends excess ETH back - reentrancy potential if caller is a contract (but ERC1155 callback checks may protect)
  - Seed owner gets royalties on every print mint - creating a print NFT market with owner extracting rents
  - `msg.sender.call{value: burnPrice}` in burnPrint - reentrancy risk on burn
- PRIORITY: **HIGH** - 215 ETH, bonding curve with complex pricing, reserve accounting, potential for MEV and reentrancy on mint/burn paths

---

## EulerBeatsV2 (0xa98771a46dcb34b34cdad5355718f8a97c8e603e) - 85 ETH
- Type: EulerBeats V2 - same concept as V1 with improvements
- Key functions: Same as V1 (mint, mintPrint, burnPrint)
- Architecture: Updated version of EulerBeats with same bonding curve print mechanism
- Attack surfaces: Similar to V1 - bonding curve, reserve accounting, MEV
- PRIORITY: **MEDIUM** - Same as V1 but smaller balance (85 ETH), likely has fixes for V1 issues

---

## RedemptionContract (0x899f9a0440face1397a1ee1e3f6bf3580a6633d1) - 206 ETH
- Type: Token-to-ETH redemption contract
- Solidity: 0.4.9
- Key functions: `redeemTokens`, fallback (funder deposits ETH)
- Architecture: Extremely simple. Funder deposits ETH. Users send approved tokens to contract, receive ETH at fixed `exchangeRate` (amount / exchangeRate). Tokens accumulate in the contract.
- Attack surfaces:
  - `exchangeRate` is fixed at construction - no admin ability to update
  - `amount / exchangeRate` uses integer division - rounding could leave dust
  - `msg.sender.transfer(redemptionValue)` - 2300 gas limit
  - Very old Solidity (0.4.9) - no SafeMath, but division can't overflow
  - No way for funder to recover deposited tokens (tokens sent to contract are stuck forever)
  - **206 ETH stuck because**: if the token contract is paused/frozen or exchange rate doesn't cover remaining ETH, funds are trapped
- PRIORITY: **LOW** - Trivially simple contract, no complex logic to exploit. The 206 ETH is likely stuck/unclaimed redemption funds

---

## BondedECDSAKeepFactory (0xa7d9e842efb252389d613da88eda3731512e40bd) - 258 ETH
- Type: tBTC threshold ECDSA keep factory (creates multi-party signing groups)
- Solidity: 0.5.17
- Key functions: `openKeep`, `setMinimumBondableValue`, `createSortitionPool`, `isOperatorAuthorized`, `isOperatorEligible`
- Architecture: Part of Keep Network / tBTC. Creates bonded ECDSA keeps (multi-sig groups) using sortition pools weighted by staked KEEP tokens. Operators must be authorized, staked, and bonded. Minimum bond is 20 ETH. Uses randomness from Random Beacon for group selection.
- Attack surfaces:
  - Complex multi-contract system (TokenStaking, KeepBonding, SortitionPool, RandomBeacon)
  - Sortition pool selection weighted by stake - potential for stake manipulation to control group membership
  - Bond seizure mechanics in related KeepBonding contract
  - Factory creates proxy clones of master keep - initialization patterns
  - Massive codebase (352KB) with many moving parts
- PRIORITY: **MEDIUM** - Complex staking/bonding system, 258 ETH, but highly audited tBTC code. Attack would require deep understanding of Keep Network economics

---

## KeepBonding (0x27321f84704a599ab740281e285cc4463d89a3d5) - 234 ETH
- Type: tBTC operator bonding contract (ETH collateral for signing groups)
- Solidity: 0.5.17
- Key functions: `withdraw`, `withdrawAsManagedGrantee`, `deposit` (via AbstractBonding), `createBond`, `reassignBond`, `freeBond`, `seizeBond`
- Architecture: Holds ETH bonds for Keep Network operators. Operators deposit ETH to be eligible for signing group selection. Bonds are created when operators are selected for keeps. Bond seizure happens on misbehavior. Complex permission model (operator, owner, grantee, managed grantee).
- Attack surfaces:
  - Bond seizure by authorized keep contracts - if a keep contract is compromised, bonds can be seized
  - Permission model complexity (operator vs owner vs grantee vs managed grantee) - potential for confused deputy
  - `withdraw` allows operator, token owner, or grantee to withdraw unbonded ETH
  - Interacts with TokenStaking and TokenGrant contracts for authorization checks
- PRIORITY: **MEDIUM** - 234 ETH bonding pool, complex auth model, but well-audited tBTC infrastructure

---

## WorkLock (0xe9778e69a961e64d3cdbb34cf6778281d34667c2) - 291 ETH
- Type: NuCypher WorkLock (work-for-tokens distribution mechanism)
- Solidity: 0.5.x
- Key functions: `bid`, `cancelBid`, `claim`, `refund`, `forceRefund`, `verifyBidders`, `withdrawCompensation`
- Architecture: Novel token distribution mechanism. Users bid ETH to receive NU tokens. Tokens are locked in staking escrow. As users perform work (staking/servicing), they earn back their ETH. Boosting refund mechanism. Bidder verification phase. Compensation for excess bids.
- Attack surfaces:
  - Complex bidding/refund economics with boosting coefficient
  - `verifyBidders` iterates over bidder array - potential for gas griefing if many small bidders
  - `forceRefund` allows anyone to force-refund a bidder who hasn't claimed - could be used to grief legitimate bidders
  - `bonusETHSupply` and `bonusDepositRate` calculations have precision considerations
  - Refund rate depends on completed work - gaming work verification could accelerate ETH refund
  - Large codebase (143KB) includes StakingEscrow and NU token
- PRIORITY: **MEDIUM** - 291 ETH, interesting economics, but NuCypher WorkLock has been completed (historical mechanism). ETH likely represents unclaimed refunds

---

## Zethr (0xd48b633045af65ff636f3c6edd744748351e020d) - 280 ETH
- Type: Gambling platform token with dividend mechanics (P3D variant)
- Solidity: 0.4.x
- Key functions: `buyAndSetDivPercentage`, `sell`, `withdraw`, `transfer`, `transferFrom`
- Architecture: Enhanced P3D clone with variable dividend rates (users choose their div rate on buy). Has front-end tokens and dividend tokens. Bankroll system for games. Dividend card system for bonus dividends. Multiple dividend tiers (2-33%).
- Attack surfaces:
  - Variable dividend rate per user creates complex accounting with `tokenBalanceLedger_`, `payoutsTo_`
  - `dividendRate` chosen by user on buy - creates asymmetric dividend pools
  - `transferFromInternal` with `_data` parameter and token receiver callback (`tokenFallback`) - potential for reentrancy
  - Bankroll integration - games interact with the token contract
  - `ZethrDividendCards` and `ZethrBankroll` external contract interactions
  - 280 ETH is significant for a gambling token
- PRIORITY: **MEDIUM** - 280 ETH, complex multi-tier dividend mechanics, gambling platform with external game contracts, but P3D-style contracts are well-studied

---

## GuildBank (0x83d0d842e6db3b020f384a2af11bd14787bec8e7) - 287 ETH
- Type: MolochDAO-style guild bank (Hakka Finance variant)
- Solidity: 0.5.16
- Key functions: `withdraw` (owner or burner), `ragequit` (via Burner contract)
- Architecture: Treasury contract holding multiple token types (including ETH). Two access paths: (1) Owner can withdraw anything, (2) Burner contract allows holders of HAKKA token to burn shares and receive pro-rata of all bank assets ("ragequit"). Burner uses `hakka.burn(msg.sender, share)` then iterates tokens to withdraw proportional amounts.
- Attack surfaces:
  - **Ragequit accounting**: `share.mul(tokenInBank).div(totalShare)` - totalShare read from `hakka.totalSupply()` BEFORE burn, but burn happens first. Since `hakka.burn` reduces totalSupply, the `totalShare` used is the pre-burn supply, which is correct. BUT if another user frontruns and burns tokens, `totalShare` would already be lower, giving the victim a larger share.
  - **Reentrancy in ragequit**: `bank.withdraw` for ETH uses `receiver.call.value(amount)("")` - if receiver is a contract, it could reenter. The Burner has a `lock` boolean reentrancy guard, but `GuildBank.withdraw` itself has no guard.
  - **Token ordering**: `require(uint256(tokens[i-1]) < uint256(tokens[i]))` prevents duplicate tokens but not reentrancy between token transfers
  - **doTransferOut assembly**: Handles non-standard ERC20 returns but could behave unexpectedly with malicious tokens
  - **Flash loan attack vector**: Flash-borrow HAKKA, burn for pro-rata share of bank assets (287 ETH + tokens), profit if bank holds more value than HAKKA market cap implies
  - Burner address is hardcoded as constant `0xde02...`
- PRIORITY: **HIGH** - 287 ETH + likely holds other tokens, ragequit mechanism with potential flash loan drain (burn HAKKA for pro-rata ETH/tokens), reentrancy via ETH withdrawal callback

---

## TornadoCash_Eth_01 (0x12d66f87a04a9e220743712ce6d9bb1b5616b8fc) - 510 ETH
- Type: Privacy mixer (Tornado Cash 0.1 ETH pool, migrated version)
- Solidity: 0.5.8
- Key functions: `deposit`, `withdraw`, `migrateState`, `initializeTreeForMigration`, `finishMigration`
- Architecture: Standard Tornado Cash with zkSNARK proof verification. Fixed denomination (0.1 ETH). Merkle tree for commitments. Nullifier hashes prevent double-spending. Operator-controlled verifier updates. This is the migrated v2 of the 0.1 ETH pool.
- Attack surfaces:
  - zkSNARK verifier is trusted - if verifier contract is malicious, funds can be drained
  - `operator` can update verifier address - if operator key is compromised, attacker can deploy fake verifier
  - Migration functions (`migrateState`, `initializeTreeForMigration`) can only be called before `isMigrated = true`
  - Root history limited to 100 entries - very old commitments could theoretically be orphaned, but this is by design
  - Well-audited Tornado Cash code - no novel attack surfaces
  - 510 ETH is significant but spread across many 0.1 ETH deposits
- PRIORITY: **LOW** - Well-audited, proven Tornado Cash code. 510 ETH but ~5100 deposits at 0.1 ETH each. Operator key is the main trust assumption

---

## InitializableAdminUpgradeabilityProxy -> CollectorWithCustomImpl (0x464c71f6c2f760dda6093dcb91c24c39e5d6e18c) - 2435 ETH
- Type: Aave Treasury Collector (proxy -> CollectorWithCustomImpl at 0x83b7ce402a0e756e901c4a9d1cafa27ca9572afc)
- Key functions: `initialize`, `approve`, `transfer`, `createStream`, `withdrawFromStream`, `cancelStream`
- Architecture: Aave protocol treasury that collects fees. Supports Sablier-style streaming of tokens to recipients. Has FUNDS_ADMIN role for access control. Uses OpenZeppelin upgradeable proxy pattern with AccessControl.
- Attack surfaces:
  - Upgradeable proxy - admin can change implementation
  - FUNDS_ADMIN role controls all fund movements
  - Stream mechanism allows time-locked fund distribution
  - Well-audited Aave infrastructure code
  - 2435 ETH is very significant but controlled by Aave governance
- PRIORITY: **LOW** for permissionless exploit (governance-controlled), **HIGH** value at risk if governance is compromised

---

## L1ChugSplashProxy -> L1StandardBridge (0x3980c9ed79d2c191a89e02fa3529c60ed6e9c04b) - 2537 ETH
- Type: Metis L1 Standard Bridge (L1 side of L2 bridge)
- Implementation: L1StandardBridge at 0xa0cfe8af2ab5c9232714647702dbacf862ea4798
- Key functions: `depositETH`, `depositETHTo`, `depositERC20`, `finalizeETHWithdrawal`, `finalizeERC20Withdrawal`
- Architecture: Standard optimistic rollup bridge. Users deposit ETH/ERC20 on L1, get minted tokens on L2 (Metis). Withdrawals are finalized via cross-domain messenger after challenge period. L1ChugSplashProxy uses storage-based admin slot.
- Attack surfaces:
  - Cross-domain messenger trust - if messenger is compromised, bridge can be drained
  - `donateETH` function allows anyone to send ETH to the bridge
  - ChugSplash proxy pattern - admin controls upgrades
  - Multiple chain ID support (`depositETHByChainId`, `depositETHToByChainId`)
  - Bridge security depends on Metis sequencer and challenge period
  - 2537 ETH is very high value
- PRIORITY: **MEDIUM** - High value (2537 ETH) but well-studied bridge pattern. Cross-domain messenger and sequencer are the trust roots. Would need messenger compromise or sequencer manipulation to exploit

---

## Proxy -> StarkExchange (0x5fdcca53617f4d2b9134b29090c87d01058e27e9) - 5264 ETH
- Type: StarkEx exchange (StarkWare validity rollup)
- Implementation: MainDispatcher at 0x4edd62189732e9ff476aba880b48c29432a7ac9b (which delegates to sub-dispatchers)
- Key contracts: `StarkExchange`, `MainDispatcher`, `MainDispatcherBase`, `BlockDirectCall`
- Architecture: StarkWare's diamond-like dispatcher pattern. MainDispatcher delegates calls to sub-contracts based on function selector routing. Uses validity proofs (STARK proofs) for state transitions. Governance-controlled upgrades with delay.
- Attack surfaces:
  - Complex dispatcher pattern with multiple sub-implementations
  - Governance upgrade mechanism with timelock
  - STARK proof verification - if verifier has bugs, state can be manipulated
  - 5264 ETH is the highest value target in this batch
  - StarkWare has been extensively audited and runs in production
- PRIORITY: **LOW** for permissionless exploit (STARK-verified, governance-controlled), but **HIGHEST** value at risk

---

## AdminUpgradeabilityProxy (0xf74bf048138a2b8f825eccabed9e02e481a0f6c0) - 291 ETH
- Type: Proxy with unverified implementation at 0x0634ee9e5163389a04b3ff6c9b05de71c24c1916
- Implementation: **SOURCE NOT VERIFIED** on Etherscan
- Key functions (proxy only): `upgradeTo`, `upgradeToAndCall`, `implementation`, `changeAdmin`, `admin`
- Architecture: Standard OpenZeppelin AdminUpgradeabilityProxy. Implementation contract source is not available.
- Attack surfaces:
  - **Cannot analyze** - implementation source not verified
  - Admin controls upgrades
  - 291 ETH held by unknown logic
- PRIORITY: **MEDIUM** - 291 ETH with unverified implementation. Would need bytecode analysis (evm-bytecode-lab) to understand the logic

---

# Priority Summary

## HIGH PRIORITY (interesting DeFi logic + significant ETH)
1. **EulerBeats** (0x8754f5...) - 215 ETH - Bonding curve with reserve accounting, MEV potential on mint/burn, reentrancy risk
2. **GuildBank** (0x83d0d8...) - 287 ETH - Ragequit/burn mechanism with flash loan drain potential, reentrancy via ETH callback

## MEDIUM PRIORITY
3. **LienToken** (0xab37e1...) - 88 ETH - Term-based dividend accounting, donation/timing attacks
4. **Zethr** (0xd48b63...) - 280 ETH - Complex multi-tier dividend gambling token
5. **WorkLock** (0xe9778e...) - 291 ETH - Novel bidding/refund economics (but likely historical/completed)
6. **BondedECDSAKeepFactory** (0xa7d9e8...) - 258 ETH - Complex staking/bonding, well-audited tBTC
7. **KeepBonding** (0x27321f...) - 234 ETH - ETH bonding pool with complex auth
8. **EulerBeatsV2** (0xa98771...) - 85 ETH - Same as V1 pattern
9. **L1StandardBridge** (0x3980c9...) - 2537 ETH - High value but bridge security depends on messenger/sequencer
10. **AdminUpgradeabilityProxy** (0xf74bf0...) - 291 ETH - Unverified implementation, needs bytecode analysis

## LOW PRIORITY
11. **Joyso** (0x04f062...) - 85 ETH - Centralized DEX, admin-trust model
12. **Treasure** (0x25a06d...) - 98 ETH - P3D Ponzi clone
13. **EthManager** (0xf9fb1c...) - 94 ETH - Simple bridge lock/unlock
14. **HonestDice** (0xd79b4c...) - 83 ETH - Simple gambling, server-trust
15. **E2X** (0x99a923...) - 69 ETH - HEX clone
16. **EthPool** (0x44e081...) - 70 ETH - Simple ETH wrapper for Celer
17. **RedemptionContract** (0x899f9a...) - 206 ETH - Trivially simple token redemption
18. **TornadoCash_Eth_01** (0x12d66f...) - 510 ETH - Well-audited Tornado Cash
19. **Aave Collector** (0x464c71...) - 2435 ETH - Governance-controlled treasury
20. **StarkExchange** (0x5fdcca...) - 5264 ETH - STARK-verified, governance-controlled

## Key Observations

- **Total ETH across all contracts**: ~15,178 ETH
- **Most promising targets**: GuildBank (flash loan + ragequit drain) and EulerBeats (bonding curve + reserve accounting)
- **Highest value**: StarkExchange (5264 ETH) and Metis Bridge (2537 ETH) but both are well-secured by cryptographic proofs / challenge periods
- **Several contracts are "stuck ETH"**: RedemptionContract, WorkLock, and some bridge contracts likely hold unclaimed/unredeemable funds
- **Unverified implementation**: 0xf74bf048 proxy holds 291 ETH with unverifiable logic - worth bytecode analysis
