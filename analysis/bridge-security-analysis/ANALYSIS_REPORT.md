# Bridge & Protocol Security Analysis Report

## Executive Summary

Systematic security analysis across multiple high-TVL DeFi protocols, searching for exploitable vulnerabilities. Analysis covered Balancer V2, Curve LlamaLend, Morpho Blue vault oracles, Abracadabra/DegenBox, and various ERC4626 vault attack patterns.

## Investigation 1: Balancer V2 Rounding Vulnerability

### Background
The Balancer V2 vault (`0xBA12222222228d8Ba445958a75a0704d566BF2C8`) was exploited on November 3, 2025 for $128M across multiple chains. The vulnerability was a rounding direction mismatch in `_upscale()` using `mulDown()` in Composable Stable Pools.

### Findings
- **Vault is NOT paused** — pause window expired in 2021 (immutable code)
- **$67M+ in real assets remain** (1,692 WETH, 3,546 wstETH, 30.4M BAL, etc.)
- **BUT**: All remaining assets are in **non-vulnerable pool types** (Weighted, Gyro, standard Stable)
- Composable Stable Pools (CSPv5) were fully drained during the November exploit
- Meta-stable pools were whitehat-recovered ($4.1M) by Certora/SEAL911
- Access control on `manageUserBalance` is working (BAL#401 on cross-user withdrawal)
- Balancer V2 forks total only $4.53M TVL across 27 forks

### Conclusion
**NOT EXPLOITABLE** — The vulnerable pool types (Composable Stable) have already been drained. Remaining assets are in pool types with different math that is not vulnerable to the rounding attack.

## Investigation 2: Morpho Blue Vault-Backed Oracle Manipulation

### Background
Investigated whether the ResupplyFi donation attack pattern ($9.8M, June 2025) could be applied to Morpho Blue markets using ERC4626 vault tokens as collateral.

### Findings
- Scanned all Morpho Blue markets with vault-backed oracles
- Found 5 markets with BASE_VAULT oracles
- Two had extremely low vault TVL: svZCHF (1.12 tokens) and ysUSDS (419 tokens)
- **BUT**: Both have ZERO market supply — nothing to borrow against
- Larger markets (sUSDe, etc.) have massive vault TVL making donation infeasible

### Conclusion
**NOT EXPLOITABLE** — No Morpho Blue markets have both low-TVL vaults AND significant borrowable supply.

## Investigation 3: Curve LlamaLend Donation Attack (sDOLA Pattern)

### Background
The sDOLA/crvUSD LlamaLend market was exploited on March 2, 2026 ($240K profit). The attacker used a $30M flash loan to donate to the sDOLA vault, inflating the exchange rate and triggering mass liquidations.

### Key Technical Finding: Oracle Design Vulnerability
LlamaLend markets can use two types of price oracles:

1. **Type A (1197 bytes)**: Directly calls `convertToAssets()` on the vault — **VULNERABLE to donation attacks**
2. **Type B (1850 bytes)**: Uses Curve pool price / EMA — **NOT vulnerable to donation attacks**

### Systematic Scan Results
Scanned all 46 LlamaLend markets on Ethereum mainnet. Found 14 markets using vault tokens as collateral.

**Markets with Type A oracle (convertToAssets) + active debt + donation susceptibility:**

| Market | Collateral | Oracle Type | Debt | Vault TVL | Exploitable? |
|--------|-----------|-------------|------|-----------|-------------|
| 15 | sFRAX/crvUSD | Type A | $5,641 | $65.3M | NO — debt too small |
| 17 | sDOLA/crvUSD | Type A | $816 | $5.78M | NO — already exploited, debt fled |
| 28 | sfrxUSD/crvUSD | Type A | $2.94M | $25.7M | NO — not donation susceptible |
| 30 | sDOLA/crvUSD | Type A | $56 | $5.78M | NO — negligible debt |
| 32 | sUSDS/crvUSD | Type A | $18K | $5.82B | NO — vault too large |

**The largest market with Type B oracle (NOT vulnerable):**
- Market 41: sreUSD/crvUSD — $14.25M debt, $17.26M vault, 100% donation susceptible, BUT oracle does NOT use convertToAssets

### Conclusion
**NOT CURRENTLY EXPLOITABLE** — The vulnerability pattern exists (confirmed in 2 markets), but economic conditions are not met:
- sFRAX: $5.6K debt against $65M vault (attack cost >> profit)
- sUSDS: $18K debt against $5.82B vault (impossible to manipulate)
- sDOLA: Post-exploit, borrowers fled, only $816 remaining

## Investigation 4: Other Protocols Examined

### Abracadabra/DegenBox ($11.9M TVL)
- Multiple past exploits (Jan 2024, Mar 2025, Oct 2025)
- October 2025 cook([5,0]) bypass was patched
- Current TVL too low for significant extraction

### BentoBox batch()+delegatecall Pattern
- Known vulnerability class, but Abracadabra has been repeatedly patched

### Recent Exploits (Jan-Mar 2026)
- Step Finance ($28.9M) — social engineering/key compromise, not smart contract
- YieldBlox ($10.6M) — Stellar-based oracle manipulation, not applicable to Ethereum
- Solv Protocol ($2.7M, March 6 2026) — double-minting reentrancy, already patched
- CrossCurve ($3M) — bridge validation bypass

## Vulnerability Discovery: LlamaLend Oracle Design Flaw (Unpatched)

### Description
A class of LlamaLend price oracles (Type A, 1197 bytes bytecode) directly reads vault exchange rates via `convertToAssets()`. When the vault's underlying assets are held directly (100% donation susceptibility), an attacker can:

1. Flash loan the underlying token
2. Donate to the vault, inflating `convertToAssets()` return value
3. The oracle reports an inflated collateral price
4. This triggers the LLAMMA soft-liquidation mechanism to misbehave
5. Borrowers are liquidated (counterintuitively, collateral value going UP triggers liquidation)
6. Attacker profits from liquidation proceeds

### Status
- **Proven**: The sDOLA exploit (March 2, 2026) demonstrated this exact pattern
- **Unpatched**: LlamaLend V2 fix not yet deployed
- **Not Currently Exploitable on Mainnet**: No remaining markets have both (a) convertToAssets oracle + (b) significant debt + (c) reasonably-sized vault
- **Risk Remains**: Any new market created with a Type A oracle and low-TVL vault collateral would be immediately vulnerable

### Responsible Disclosure Note
The vulnerability class was publicly disclosed by Curve Finance on March 2, 2026. The Curve team is developing mitigations for LlamaLend V2.

## E3 Proof: sDOLA LlamaLend Exploit Replay (Fork-Grounded)

### Proof Location
`exploit_test/test/SDolaExploit.t.sol`

### E3 Gate Results

**Fork block**: 24566936 (one block before exploit at 24566937)
**Exploit TX**: `0xb93506af8f1a39f6a31e2d34f5f6a262c2799fef6e338640f42ab8737ed3d8a4`

#### Pre-exploit state (block 24566936):
- sDOLA exchange rate: 1.189042
- Market 30 active loans: 30
- Market 30 total debt: 11,276,657 crvUSD
- totalAssets: 13,996,116 DOLA
- totalSupply: 11,770,912 sDOLA

#### Post-exploit state (replayed on fork):
- sDOLA exchange rate: 1.353066 (+13.79%)
- Market 30 active loans: 4 (26 liquidated)
- Market 30 total debt: 11,273,909 crvUSD
- totalAssets: 13,768,791 DOLA (-227,325)
- totalSupply: 10,175,991 sDOLA (-1,594,920)

#### Value Extracted:
- **Gross profit: 227,325 DOLA** (~$227K)
- **Costs**: Gas (~0.024 ETH at 2 gwei), flash loan fees (negligible for Curve pools)
- **Net profit: ~227,300 DOLA** after costs
- **Repeatability**: One-time per market state (borrowers flee after exploit)

#### Attack Mechanism (Corrected from Initial Analysis):
The attack is NOT a simple donation. The attacker used Curve pool swaps involving:
1. **savedola pool** (scrvUSD/sDOLA) at `0x76a962ba6770068bcf454d34dde17175611e6637`
2. **alUSDsDOLA pool** (sDOLA/alUSD) at `0x460638e6f7605b866736e38045c0de8294d7d87f`
3. **sDOLA deposit/withdraw** to manipulate the totalSupply/totalAssets ratio

The key insight: by swapping through pools that hold sDOLA, the attacker causes sDOLA shares to be burned (totalSupply decreases) faster than underlying assets decrease (totalAssets). This inflates `convertToAssets()`, which the oracle reads directly.

When the oracle reports the inflated sDOLA price to the LLAMMA AMM:
- The AMM shifts active bands (sDOLA appears more valuable)
- Borrowers in soft-liquidation bands have their sDOLA converted back to crvUSD
- The conversion happens at the manipulated (inflated) rate
- When the rate normalizes, borrowers have lost value
- 26 of 30 positions were liquidated in a single transaction

#### Oracle Root Cause:
- Oracle contract `0x88822eE517Bfe9A1b97bf200b0b6D3F356488fF2` contains selector `0x07a2d13a` (`convertToAssets(uint256)`) in its bytecode
- Oracle's `price()` function calls `sDOLA.convertToAssets(1e18)` and multiplies by a DOLA/crvUSD peg factor
- This makes the oracle's output directly controllable by anyone who can manipulate the sDOLA exchange rate

#### Robustness:
- Gas +20%: Still profitable (gas cost is ~$60 vs $227K profit)
- Liquidity -20%: Still profitable (the attack uses dedicated Curve pools, not open market)
- Timing +1 block: Attacker was tx index 0 in the block (builder submission), but the attack works regardless of position since the oracle reads spot rate, not TWAP

### Reproduction Command
```bash
forge test --match-test test_replay_sdola_exploit -vvv \
  --fork-url https://mainnet.infura.io/v3/<KEY> \
  --fork-block-number 24566936
```

## Scripts Developed
- `scripts/scan_llamalend_markets.py` — Scans all LlamaLend markets for vault-token collateral
- `scripts/analyze_sreusd_market.py` — Deep analysis of sreUSD market oracle
- `scripts/analyze_sreusd_oracle.py` — Oracle contract reverse engineering
- `scripts/oracle_deep_probe.py` — Bytecode analysis of oracle contracts
- `scripts/check_oracle_types.py` — Systematic scan of all oracle types for convertToAssets
- `scripts/check_balancer_v2.py` — Balancer V2 vault status check
- `scripts/check_balancer_v2_assets.py` — Balancer V2 token balance analysis
- `scripts/scan_vault_oracles_v2.py` — Morpho Blue vault oracle scan
- `scripts/check_low_tvl_markets.py` — Low-TVL Morpho market analysis
- `scripts/sdola_exploit_lookup.py` — sDOLA exploit transaction lookup and state analysis
- `scripts/sdola_exploit_deep.py` — Deep Market 30 analysis with attacker token flows
- `scripts/sdola_exploit_trace.py` — Full exploit TX log/transfer analysis
- `scripts/scan_llamalend_arbitrum.py` — LlamaLend Arbitrum market scan
- `scripts/scan_euler_v2_vaults.py` — Euler V2 vault-backed collateral scan
- `exploit_test/test/SDolaExploit.t.sol` — Foundry fork test proving the sDOLA exploit (E3)
