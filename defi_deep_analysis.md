# Deep Smart Contract Vulnerability Analysis

## Contract-by-Contract Assessment

---

### 1. E2X (0x99a923b8f3a4e41740e3f8947fd7be6aa736d8a6) -- 69 ETH

**What it does:** HEX-like staking token with an auction lobby (xfLobby). Users send ETH to enter daily lobbies, exit later to receive minted E2X tokens. Users stake E2X tokens for daily payouts + ETH dividends. 5% inflation model. 10% dev share flushed to a hardcoded address.

**Key value-moving functions:**
- `xfLobbyEnter()` -- payable, sends ETH into daily lobby pools
- `xfLobbyExit()` -- mints E2X tokens proportional to lobby share
- `stakeStart()` / `stakeEnd()` -- lock/unlock tokens with dividends
- `xfFlush()` -- transfers 10% of daily dividends to dev address

**Access control:** No owner/admin. Hardcoded `T2X_SHARE_ADDR`. All functions are permissionless.

**Potential vulnerabilities:**

- **Truncation in `_globalsSync` (REAL CONCERN):** Values like `lockedSunsTotal`, `stakeSharesTotal`, `stakePenaltyTotal` are stored as `uint72` but computed as `uint256`. When syncing back, they are cast with `uint72(g._lockedSunsTotal)`. If the 256-bit value exceeds `uint72` max (~4.7e21), silent truncation occurs. This could corrupt global accounting. However, triggering this requires enormous token supply which may not be practical.

- **`dailyDataRange` off-by-one bug:** The function increments `dst` twice in the loop body (`dst++` for `_dayPayoutTotal` and `dst++` for `_dayDividends`) but only increments `src` once. This means `_dayDividends` writes into wrong indices, making the view function return garbage. This is a view function bug, not exploitable for value extraction.

- **Reentrancy in `stakeEnd`:** `msg.sender.transfer(dividends)` is called before `_mint` and `_stakeRemove`. The `.transfer()` call forwards only 2300 gas, which prevents reentrancy in practice.

- **`xfFlush` can be front-run:** Anyone can call it. The `LAST_FLUSHED_DAY` is sequential. If dailyData hasn't been updated, the dividend amount could be stale. Not directly exploitable for profit.

**Verdict: LOW risk.** The uint72 truncation is a real code defect but practically hard to trigger. No clear permissionless value extraction path.

---

### 2. EthPool (0x44e081cac2406a4efe165178c2a4d77f7a7854d4) -- 70 ETH

**What it does:** An ERC20-like wrapper for native ETH. Users deposit ETH, get internal balance. Supports approve/transferFrom for spending by approved contracts (designed for Celer Network state channels).

**Key value-moving functions:**
- `deposit()` -- payable, credits `_receiver` with ETH balance
- `withdraw()` -- transfers ETH back to `msg.sender`
- `transferFrom()` -- approved spender moves ETH between accounts
- `transferToCelerWallet()` -- approved spender sends ETH to a CelerWallet

**Access control:** No owner. Fully permissionless deposit/withdraw.

**Potential vulnerabilities:**

- **Reentrancy in `_transfer` (NOTABLE):** The `_transfer` function updates balance before calling `_to.transfer(_value)`. The pattern is: subtract balance -> emit event -> send ETH. The `.transfer()` only forwards 2300 gas, mitigating reentrancy for EOAs and simple contracts. However, with EIP-2929/EIP-3529 changes and potential future gas repricing, this 2300 gas assumption is fragile.

- **`transferToCelerWallet` external call:** After deducting the balance, it calls `wallet.depositETH.value(_value)(_walletId)` on an arbitrary address. The `_walletAddr` is caller-chosen. However, this requires allowance from `_from`, so a legitimate user would need to approve the attacker first.

- **No reentrancy guard:** The contract has no ReentrancyGuard. It relies on `.transfer()` gas limit.

**Verdict: LOW risk.** The 2300 gas limit on `.transfer()` is the primary defense. The contract is simple and well-structured for its purpose. No permissionless extraction path.

---

### 3. Joyso (0x04f062809b244e37e7fdc21d9409469c989c2342) -- 85 ETH

**What it does:** A decentralized exchange with off-chain order matching. Users deposit ETH/tokens, sign orders off-chain, and admins submit matched orders on-chain. Withdrawal requires a lock period (30 days by default).

**Key value-moving functions:**
- `depositEther()` / `depositToken()` -- deposit funds
- `withdraw()` -- withdraw after lock period
- `withdrawByAdmin_Unau()` -- admin-facilitated withdrawal with signature
- `matchByAdmin_TwH36()` / `matchTokenOrderByAdmin_k44j()` -- admin-submitted trades
- `migrateByAdmin_DQV()` -- batch migration to new contract

**Access control:** Owner + isAdmin mapping. Most value-moving functions are `onlyAdmin`.

**Potential vulnerabilities:**

- **Signature replay across chains / contracts:** The `verify` function uses `keccak256(this, ...)` which includes the contract address, providing cross-contract replay protection. However, there is no chain ID in the hash, making signatures valid on all EVM chains where this contract might be deployed at the same address.

- **ecrecover returning address(0):** If `ecrecover` returns `address(0)` and `sender` happens to be `address(0)`, the `verify` function would return `true`. However, `userId2Address[0]` would map to `address(0)` only if explicitly set, and the `addUser` function starts at userId 1, so `userId2Address[0]` = `address(0)` by default (ether address mapping). If a user's computed address via userId lookup happens to be 0x0, this could be exploitable. But the hash structure and v/r/s values would need to produce exactly 0x0 from ecrecover, which is extremely unlikely.

- **Migration function external call:** `migrateByAdmin_DQV` calls `Migratable(newContract).migrate(...)` where `newContract` is from `inputs[0]`. This is admin-only but allows calling arbitrary contracts.

- **Lock/unlock race:** A user can `unlockMe()` immediately after `lockMe()`, which resets the lock. But both are user-controlled and don't affect other users.

**Verdict: LOW-MEDIUM risk.** The main concern is admin centralization and potential ecrecover edge cases. The lock period mechanism provides reasonable self-custody guarantees. No clear permissionless extraction path for non-admin actors.

---

### 4. Zethr (0xd48b633045af65ff636f3c6edd744748351e020d) -- 280 ETH

**What it does:** A variable-dividend token with bonding curve pricing (Ponzi-scheme characteristics). Users buy tokens with ETH, choosing a dividend rate (2-33%). Sells generate dividends distributed to holders. Features include ICO phase, referral system, div card holders, and bankroll address.

**Key value-moving functions:**
- `buyAndSetDivPercentage()` / `buy()` -- buy tokens with ETH
- `sell()` -- sell tokens for ETH (minus dividend tax)
- `withdraw()` -- withdraw accumulated dividends
- `reinvest()` -- reinvest dividends into tokens

**Access control:** Multi-admin system (8 hardcoded admins). Admins can change bankroll, staking requirement, name/symbol, and start/end phases.

**Potential vulnerabilities:**

- **Reentrancy via `withdrawFrom` in `transferFromInternal` (SIGNIFICANT):** When tokens are transferred, `transferFromInternal` calls `withdrawFrom(_customerAddress)` which does `_customerAddress.transfer(_dividends)`. This sends ETH to the `_from` address BEFORE updating the balances. The `.transfer()` 2300 gas limit mitigates this, but the pattern is dangerous.

- **ERC223 callback in `transferFromInternal`:** After the transfer logic, if `_toAddress` is a contract, it calls `receiver.tokenFallback(_from, _amountOfTokens, _data)`. This is after balance updates, but the external call could be used for reentrancy in other paths.

- **Withdrawal to arbitrary address:** `withdraw(address _recipient)` allows specifying where dividends are sent. If `_recipient` is 0x0, it defaults to `msg.sender`. This is intended behavior.

- **`getUserAverageDividendRate` division by zero:** If `frontTokenBalanceLedger_[user]` is 0, this function reverts. This can DoS the `sell()` function or transfers if a user's front-end balance somehow becomes 0 while they still hold dividend tokens (accounting desync).

- **Integer precision in bonding curve math:** The `toPowerOfThreeHalves` and `toPowerOfTwoThirds` functions use integer approximations of fractional exponents. Precision loss at scale boundaries could create tiny arbitrage opportunities through repeated buy/sell cycles.

**Verdict: MEDIUM risk.** The combination of external calls during transfers, complex bonding curve math, and dual-token accounting creates a surface where accounting inconsistencies could accumulate. However, practical exploitation is limited by the 2300 gas limit on `.transfer()`.

---

### 5. EulerBeats (0x8754f54074400ce745a7ceddc928fb1b7e985ed6) -- 215 ETH

**What it does:** Generative art NFTs (ERC1155) with a bonding curve for prints. Original seeds are minted for 0.271 ETH (max 27). Prints of seeds are minted along an exponential bonding curve. Burns return 90% of the current print price from the reserve.

**Key value-moving functions:**
- `mint()` -- mint original seed NFT (0.271 ETH)
- `mintPrint()` -- mint a print along bonding curve
- `burnPrint()` -- burn a print, receive ETH from reserve
- `withdraw()` -- owner withdraws excess funds (above reserve)

**Access control:** Ownable. Owner controls enable/disable, pricing, scripts, URI, and withdrawal.

**Potential vulnerabilities:**

- **Reentrancy in `mintPrint` via `seedOwner.call{value: seedOwnerRoyalty}("")` (SIGNIFICANT):** The royalty payment to the seed owner uses `.call{value}` which forwards all available gas. This happens AFTER `_mint` (which updates balances) but BEFORE the refund. A malicious seed owner contract could re-enter `mintPrint` or `burnPrint`. The `totalSupply[tokenId]` has already been incremented, so re-entering `mintPrint` would compute the next price correctly. However, re-entering `burnPrint` while `reserve` has been incremented but before the transaction completes could drain the reserve.

- **Reentrancy in `burnPrint` via `msg.sender.call{value: burnPrice}("")`:** Burns ETH to `msg.sender` using `.call{}`. If `msg.sender` is a contract, it can re-enter. State updates (supply decrement, reserve decrement) happen BEFORE the ETH send, following CEI pattern. This appears safe.

- **No reentrancy guard:** Neither `mintPrint` nor `burnPrint` have reentrancy guards. The V1 contract (this one) lacks `ReentrancyGuard`.

- **Refund mechanism:** `_refundSender` sends excess ETH back via `.call{}`. If combined with reentrancy through the royalty payment, there could be a complex attack vector.

- **Bonding curve overflow:** The exponential pricing `(11^n / 10^n)` can overflow for large print numbers. The `MAX_PRINT_SUPPLY = 120` should keep this in bounds, but the math near the edges could have precision issues.

**Verdict: MEDIUM-HIGH risk.** The lack of reentrancy guards combined with `.call{value}` for royalty payments to arbitrary addresses (seed owners) is the most concerning pattern. A malicious seed owner could potentially exploit the mintPrint flow through reentrancy. This is the most promising attack vector among these contracts.

---

### 6. EulerBeatsV2 (0xa98771a46dcb34b34cdad5355718f8a97c8e603e) -- 85 ETH

**What it does:** V2 of EulerBeats with improved security. Similar bonding curve for prints, but originals are minted for free (onlyOwner). Uses `ReentrancyGuard`, `Address.sendValue`, and a `RoyaltyDistributor` for safer royalty distribution.

**Key value-moving functions:**
- `mint()` -- onlyOwner, mints original seed
- `mintPrint()` -- mint print along bonding curve (nonReentrant)
- `burnPrint()` -- burn print, receive ETH from reserve (nonReentrant)
- `withdraw()` -- owner withdraws excess funds (nonReentrant)

**Access control:** Ownable with fine-grained enable/disable for mint, mintPrint, burnPrint. Owner-only for originals.

**Potential vulnerabilities:**

- **Mitigated reentrancy:** Both `mintPrint` and `burnPrint` use `nonReentrant` modifier. This addresses the V1 reentrancy concern.

- **RoyaltyDistributor external call:** `_distributeRoyalty` handles three cases: ERC165 RoyaltyReceiver contracts, regular contracts, and EOAs. Uses `sendValue` which forwards all gas. The `nonReentrant` modifier on `mintPrint` prevents re-entry.

- **Contract mint restriction bypass:** `_contractMintPrintEnabled` flag restricts contract-originated `mintPrint` calls. This can be bypassed during construction (extcodesize returns 0 during constructor execution), but the check is `msg.sender != tx.origin`, not `isContract()`, so constructor bypass doesn't help.

- **Bonding curve**: Different constants (A=12, B=140, C=100) than V1. First 100 prints have price = C*X (linear), then exponential growth kicks in. Well-bounded math.

**Verdict: LOW risk.** V2 addresses the main V1 concerns with reentrancy guards and safer royalty distribution. No clear permissionless extraction path.

---

### 7. Treasure (0x25a06d4e1f804ce62cf11b091180a5c84980d93a) -- 98 ETH

**What it does:** A Ponzi-scheme token with bonding curve pricing. 15% fee on buy (5% referral + 10% to holders OR 15% to holders). 10% fee on sell (distributed to holders). 5% fee on transfer. 20% fee on dividend withdrawal (10% community + 10% trading wallet).

**Key value-moving functions:**
- `buy()` / fallback -- purchase tokens with ETH
- `sell()` -- sell tokens, proceeds go to `sellingWithdrawBalance_`
- `withdraw()` -- withdraw dividends (minus 20% fees)
- `sellingWithdraw()` -- withdraw selling proceeds
- `transfer()` -- transfer tokens (5% burn fee)
- `reinvest()` -- reinvest dividends

**Access control:** Administrator via `keccak256(address)` mapping. The administrator hash `0x2d059f...` is hardcoded.

**Potential vulnerabilities:**

- **CRITICAL: Dividend accounting manipulation.** The `profitPerShareAsPerHoldings` function iterates over ALL addresses (`contractTokenHolderAddresses_`), computing each holder's share of dividends and adding it to `payoutsTo_`. The `dividendsOf()` function simply returns `payoutsTo_[address]` directly -- it does NOT subtract any expected baseline. This means dividends only ever accumulate. There is no mechanism where selling tokens reduces your future dividend claims proportionally. Combined with the `withdraw()` function which zeroes out `payoutsTo_` and `referralBalance_`, this creates an accounting mismatch where value can leak.

- **O(N) gas bomb:** `profitPerShareAsPerHoldings` iterates over all holder addresses twice (once to sum, once to distribute). As the user base grows, every buy/sell/transfer/reinvest call becomes increasingly expensive, eventually exceeding block gas limits. This would **freeze the contract** -- nobody could buy, sell, withdraw, or reinvest.

- **The `else if` branch in `profitPerShareAsPerHoldings` distributes entire `calculatedDividend` to each zero-balance holder:** When `noOfTokens_ == 0` (everyone has sold), every holder in the list gets the full `calculatedDividend` added to their `payoutsTo_`. This is a multiplication of funds -- if there are N zero-balance holders, N * `calculatedDividend` is distributed instead of just `calculatedDividend`. This is a real bug.

- **Reentrancy in `withdraw` and `sellingWithdraw`:** Both functions zero out state BEFORE calling `.transfer()`. This follows CEI pattern and is safe.

- **Unbounded array `contractTokenHolderAddresses_`:** Never shrinks. Once gas costs exceed limits, the contract is permanently bricked.

**Verdict: HIGH risk.** The O(N) gas bomb is a contract-killing vulnerability -- once enough users join, the contract becomes permanently unusable. The dividend accounting when `noOfTokens_ == 0` is also a real bug that multiplies distributed value. However, extracting the remaining 98 ETH may be impractical if the contract is already gas-limited.

---

### 8. HonestDice (0xd79b4c6791784184e2755b2fc1659eaab0f80456) -- 83 ETH

**What it does:** A dice gambling contract. Users submit a bet with a secret hash, the server provides a seed, and the combined hash determines the outcome. 1% house edge. Max payout is 5% of bankroll.

**Key value-moving functions:**
- `roll()` -- place a bet with secret hash
- `claim()` -- claim winnings using secret
- `claimTimeout()` -- reclaim bet if server doesn't respond within 20 blocks
- `withdraw()` -- owner withdraws bankroll (after lock period)

**Access control:** Owner can set feed address, lock/unlock bets, withdraw.

**Potential vulnerabilities:**

- **CRITICAL: `lockBetsForWithdraw` and `unlockBets` shadow state variable.** Both functions declare `uint betsLocked` as a LOCAL variable instead of modifying the state variable. `lockBetsForWithdraw()` does `uint betsLocked = block.number;` which creates a local variable and never updates the storage `betsLocked`. Similarly, `unlockBets()` does `uint betsLocked = 0;`. This means the storage `betsLocked` is ALWAYS 0 (default). Since `withdraw()` requires `betsLocked != 0`, **the owner can never withdraw via this function**. The 83 ETH may be permanently locked unless the owner can win it back through bets.

- **Server seed manipulation:** The `feed` address (set by owner) can provide arbitrary seeds. This means the house can always choose to lose or win by selecting the seed after seeing the user's secretHash. However, the user's secret hash is committed first, so the server cannot predict the combined hash without knowing the secret.

- **`msg.sender.send()` return value not checked:** In `roll()`, `claim()`, and `claimTimeout()`, the `send()` return value is not checked. If the send fails (e.g., recipient is a contract that reverts), the funds are lost to the user but the roll/claim state is still cleaned up.

- **Front-running `claim()`:** The `secret` is revealed in the claim transaction. A miner or MEV bot could see the secret in the mempool, compute whether it's a winning bet, and front-run to steal the claim. However, `rolls` is mapped to `msg.sender`, so only the original bettor can claim their own roll.

- **No minimum bet enforcement on old Solidity:** The contract is pre-0.4.x (no version pragma). The `send()` pattern is ancient and could have subtleties.

**Verdict: MEDIUM risk for users (server can choose seeds maliciously); the variable shadowing bug means owner's `withdraw()` is broken but funds aren't extractable by attackers either. The 83 ETH appears to be effectively locked -- only claimable by bettors who win.**

---

### 9. ProfitSharing (0x6822aaf4ab22e6cca8352a927b9ae0a8fdb58d9d) -- 111 ETH

**What it does:** A dividend distribution contract for MiniMeToken holders. The owner deposits ETH dividends, and token holders can claim proportional to their token balance at the deposit block. Unclaimed dividends can be recycled after 1 year.

**Key value-moving functions:**
- `depositDividend()` -- onlyOwner deposits ETH
- `claimDividend()` -- claim a specific dividend
- `claimDividendAll()` -- claim all unclaimed dividends
- `recycleDividend()` -- onlyOwner recycles old unclaimed dividends

**Access control:** Ownable. Only owner can deposit and recycle dividends.

**Potential vulnerabilities:**

- **Reentrancy in `claimDividend` (SIGNIFICANT):** The function sets `dividend.claimed[msg.sender] = true` and updates `claimedAmount` BEFORE calling `msg.sender.transfer(claim)`. This follows CEI pattern and appears safe against reentrancy on the same dividend index.

- **Cross-dividend reentrancy via `claimDividendAll`:** `claimDividendAll` loops through dividends and calls `claimDividend(i)` for each unclaimed one. The `dividendsClaimed[msg.sender]` is updated within the loop. If `msg.sender` is a contract that re-enters `claimDividendAll` during the `.transfer()` call in `claimDividend`, the `dividendsClaimed` index has already been advanced, so the same dividend would have `claimed == true`. The `.transfer()` 2300 gas limit prevents meaningful reentrancy.

- **Rounding dust:** `balance.mul(dividend.amount).div(dividend.totalSupply)` truncates. Over many claims, small amounts of dust accumulate in the contract. This is not exploitable.

- **Owner control:** Owner can deposit dividends referencing any block's totalSupply. If they deposit while totalSupply is very small (e.g., 1 token), that single token holder gets the entire dividend. This is owner-privilege abuse, not a permissionless exploit.

- **Recycled dividend creates new dividend at current supply:** When recycling, the unclaimed amount becomes a new dividend at the current token supply. If the supply has changed significantly, this redistributes unclaimed funds differently. This is intended behavior.

**Verdict: LOW risk.** The contract is well-structured with proper CEI pattern. The `.transfer()` gas limit mitigates reentrancy. No permissionless extraction path. The 111 ETH is only accessible to legitimate token holders or the owner.

---

### 10. GuildBank (0x83d0d842e6db3b020f384a2af11bd14787bec8e7) -- 287 ETH

**What it does:** A multi-token treasury (GuildBank) for Hakka Finance. Paired with a Burner contract that allows HAKKA token holders to "ragequit" -- burn their tokens to claim a proportional share of all assets in the GuildBank.

**Key value-moving functions:**
- `GuildBank.withdraw()` -- owner or burner can withdraw any token/ETH to any address
- `Burner.ragequit()` -- burn HAKKA tokens, receive proportional share of specified bank tokens

**Access control:** GuildBank: owner + hardcoded burner address. Burner: permissionless ragequit (but requires HAKKA tokens).

**Potential vulnerabilities:**

- **Reentrancy in `ragequit` with custom lock (NOTABLE):** The Burner uses a simple boolean `lock` (not OpenZeppelin's ReentrancyGuard). The flow is: set lock -> burn HAKKA -> loop through tokens -> call `bank.withdraw()` for each -> unset lock. The `bank.withdraw()` for ETH uses `receiver.call.value(amount)("")` which forwards all gas. If `msg.sender` is a malicious contract, it could re-enter... but the `lock` variable is set, so reentrancy is blocked. However, the `lock` is not in the same contract as the external call -- the Burner's `lock` prevents re-entering `ragequit`, but cannot prevent other interactions.

- **Token ordering requirement (`require(uint256(tokens[i-1]) < uint256(tokens[i]))`):** Prevents duplicate token claims in a single ragequit. Well-designed.

- **Race condition in `ragequit`:** `totalShare = hakka.totalSupply()` is captured before `hakka.burn(msg.sender, share)`. This means the share calculation uses the pre-burn supply. After burning, the actual proportional share per remaining supply is slightly different. However, since the burn reduces the numerator AND the denominator would be the same if recalculated, the math is: `share * tokenInBank / totalShare`. The totalShare is pre-burn, which is correct -- the user owned `share/totalShare` of the bank.

- **doTransferOut assembly:** The assembly-based token transfer handling correctly handles both standard and non-standard ERC20 tokens. This is a well-known pattern.

- **Owner can withdraw everything:** The owner can call `withdraw()` to drain the entire bank. This is a centralization risk, not a permissionless exploit.

- **ETH withdrawal via `.call.value`:** `receiver.call.value(amount)("")` in `withdraw` allows the receiver to execute arbitrary code. But this is only callable by owner or burner, so the receiver is either specified by owner or is `msg.sender` from ragequit.

**Verdict: LOW-MEDIUM risk.** The ragequit mechanism is reasonably well-designed. The boolean reentrancy lock protects the critical path. The main risk is owner centralization (owner can drain all 287 ETH). No permissionless extraction path for non-HAKKA-holders.

---

## Summary: Most Promising Attack Vectors (Ranked)

### Tier 1 -- Real exploitable concerns:

1. **EulerBeats V1 (215 ETH):** Lack of reentrancy guard on `mintPrint` + `.call{value}` royalty payment to arbitrary seed owner contracts. A malicious seed owner could potentially re-enter during the royalty callback. The contract has significant ETH and the reentrancy surface is genuine.

2. **Treasure (98 ETH):** The O(N) gas bomb in `profitPerShareAsPerHoldings` will eventually brick the contract. The `else if` branch that distributes entire dividends to each zero-balance holder is a real accounting bug. However, practical exploitation depends on the current number of unique addresses -- if already near gas limits, extraction is blocked.

### Tier 2 -- Bugs present but exploitation uncertain:

3. **Zethr (280 ETH):** Complex dual-token accounting with external calls during transfers. The `getUserAverageDividendRate` division-by-zero can DoS sells. The bonding curve precision loss could allow tiny arbitrage. The 2300 gas limit on `.transfer()` is the main defense against reentrancy.

4. **HonestDice (83 ETH):** The variable shadowing in `lockBetsForWithdraw`/`unlockBets` means owner can never call `withdraw()`. The ETH is effectively locked unless someone wins enough bets. The server (feed) has significant control over outcomes through seed selection.

5. **E2X (69 ETH):** The `uint72` truncation in `_globalsSync` is a real code defect that could corrupt global accounting at extreme values.

### Tier 3 -- Low practical risk:

6. **GuildBank (287 ETH):** Owner centralization is the main risk. Ragequit mechanism is reasonably safe.

7. **ProfitSharing (111 ETH):** Well-structured CEI pattern. No permissionless extraction.

8. **Joyso (85 ETH):** Admin-centric exchange. ecrecover edge case exists but is extremely unlikely.

9. **EthPool (70 ETH):** Simple, well-structured. 2300 gas limit on `.transfer()` prevents reentrancy.

10. **EulerBeatsV2 (85 ETH):** V2 fixes V1's reentrancy issues with `nonReentrant` modifier.

---

## Key Findings Per Vulnerability Class

| Pattern | Contracts Affected | Exploitable? |
|---|---|---|
| Reentrancy (no guard + .call{value}) | EulerBeats V1 | **YES -- most promising** |
| O(N) gas DoS (contract bricking) | Treasure | YES (griefing/permanent freeze) |
| Dividend accounting bug | Treasure | YES (value multiplication at zero supply) |
| Variable shadowing (owner lockout) | HonestDice | YES (owner can't withdraw) |
| uint72 truncation | E2X | Theoretical (extreme values) |
| Division by zero in view | Zethr | DoS only, not value extraction |
| ecrecover edge case | Joyso | Extremely unlikely |
| 2300 gas reentrancy reliance | EthPool, Zethr, ProfitSharing | Post-EIP fragile but currently safe |
| Owner centralization | GuildBank, ProfitSharing, EulerBeats* | Not permissionless exploit |
