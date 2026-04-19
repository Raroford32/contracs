# Memory (session-2026-04-19)

## Pinned Reality
- chain_id: 1
- fork_block: 24910815 (~2026-04-19)
- attacker_tier: public mempool (no builder/relay required)
- capital_model: up to 1M ETH via Aave/Balancer flash loans

## Scope
- 1,568 candidate addresses in contracts.txt
- 25 already analyzed (see src_cache/)
- Goal: novel E3 exploit for external caller, not already found in prior 11 sessions

## Known E3 result
- Session 11 confirmed: Hydro/DDEX HBTC oracle depeg ($22K+ profit per HBTC).
- No other confirmed E3 findings across 1568 contracts.

## Candidates Evaluated (This Session)

| Contract | Address | ETH | Verdict |
|---|---|---|---|
| Acid (DigixDAO refund) | 0x23ea10cc... | 11920 | Refund per original DGD holder, by design, no bug |
| MarketingMiningDelegator | 0x0feccb11... | 1523 | isDepositAvailable=false, withdraw-only; CEI violation exists but no pool uses hook-token |
| CollSurplusPool (Liquity) | 0x3d32e8b9... | 2064 | only callable from BorrowerOperations/TroveManager, CEI correct |
| EPlay (unverified) | 0x41aeb726... | 2335 | Unverified |
| HONG (DAO refund) | 0x9fa8fa61... | 1004 | ICO failed, isFundReleased=true, refund only for original buyers |
| Hourglass (P3D) | 0xb3775fb8... | 2094 | P3D bonding curve, ~20% round-trip fees |
| TerminalV1 (Juicebox) | 0xd569d3cc... | 5130 | Heavily audited, project-segregated balances |
| EtherToken (Neufund 3412) | 0xb59a226a... | 3412 | WETH-style wrapper, user-balance withdrawals |
| CryptoPunksMarket | 0xb47e3cd8... | 3363 | pendingWithdrawals per user, CEI correct |
| TokenStore DEX | 0x1ce7ae55... | 634 | EtherDelta clone, CEI correct, conservative |
| Dex (0x9a2d) | 0x9a2d163a... | 858 | EtherDelta clone, CEI correct |
| Phoenix Ponzi | 0xa33c4a31... | 109 | canceled=true, payback only for existing depositors |
| Floor (XVIX) | 0x40ed3699... | 336 | Capital/supply ratio grows; refund formula clean |
| XVIX Pair arb | pair 0x619aaa... | n/a | Market price 0.009478 vs refund 0.009573 - margins too thin for liquidity |
| WolkExchange | 0x728781e7... | 107 | ICO failed, exchange never enabled, refund only |
| RedemptionContract (DEL) | 0x899f9a04... | 206 | 2410 DEL per 1 ETH; DEL illiquid/dead |
| Rouleth | 0x18a672e1... | 91 | Wager committed upfront, hash-based RNG, no ability to reject losing bets |
| auto_pool (P3D clone) | 0x9b4ea303... | 128 | ~40% buy fees, no profitable round-trip |
| Klein (IKB NFT) | 0x88ae96845... | 128 | No sell/redeem function |
| ArbitrageETHStaking | 0x5eee354e... | 216 | owner renounced, user-balance staking, no exploit |
| DavyJones | 0xaba51309... | 348 | safetyRelease=year 33658, publicSwap frozen |
| LiquidityPoolV2 (Kollateral) | 0x35ffd6e2... | 413 | kETH ratio 1.081; no known DEX price discount |
| VeilEther | 0x53b04999... | 57 | WETH clone |
| WrapperLockEth | 0x50cb61af... | 81 | Signature-gated, no leaked sig |
| InsightsNetworkContributions | 0x97ec9bfb... | 208 | Owner-extracted only |
| AhooleeTokenSale | 0x575cb87a... | 191 | ICO refund, softCap not reached |
| LIQUID (KittenSwap) | 0xc618d56b... | 91 | govAddr-gated, whitelist |
| EtherFlip (already noted) | 0xe5a04d98... | 753 | Oraclize dead, already found frozen in prior sessions |

## Conclusion
No novel E3 exploitable vulnerability discovered in this session beyond already-documented Hydro HBTC.
Most remaining high-ETH contracts fall into:
1. Refund-only mechanisms for original ICO participants
2. User-balance wrappers where each user can only withdraw their own balance
3. Admin/role-gated contracts with no permissionless value extraction
4. Heavily audited DeFi (Liquity, Juicebox, Kollateral)
5. Dead/frozen contracts (DavyJones, WolkExchange, Phoenix)
6. Ponzi/P3D clones with high round-trip fees

## Next discriminator (if continued)
- Scan remaining ~1450 unverified/small-balance addresses for unusual patterns
- Look at unverified contracts' bytecode via evm-bytecode-lab
- Cross-protocol composition: use multiple of these dead contracts together

## Fork-Tested Hypotheses

### H1: XVIX/Floor arbitrage — FALSIFIED on mainnet fork (block 24910815)

**Test:** `foundry/test/XVIXFloorArb.t.sol::test_arb_small`
**Setup:** wrap ETH → WETH, send to Uniswap V2 pair (0x619aAa52...), swap for XVIX, immediately burn on Floor (0x40ED3699...), measure ETH delta.

| WETH in | XVIX out | Net result |
|---|---|---|
| 0.01 ETH | 1.044 | LOSS 6.4e9 wei (~0.0000064 ETH) |
| 0.05 ETH | 5.212 | LOSS 1.1e11 wei |
| 0.1 ETH  | 10.333 | LOSS 1.1e12 wei |
| 0.5 ETH  | 49.935 | LOSS 2.2e13 wei |
| 1 ETH    | 91.940 | LOSS 1.2e17 wei (0.12 ETH) |
| 5 ETH    | 344.3  | LOSS 1.7e18 wei (1.7 ETH) |

**Why it fails:**
- XVIX transfer receiver tax = 0.5% (receiverBurn 0.43% + receiverFund 0.07%)
- Uniswap V2 swap fee = 0.3%
- Slippage on a 17 WETH / 1814 XVIX pair is devastating above tiny sizes
- The pair market price (~0.009478 ETH/XVIX) sits below the Floor refund rate (~0.009573 ETH/XVIX), but 0.5% + 0.3% + slippage always exceeds that ~1% gross margin

Conclusion: no profitable arbitrage at this fork block.
