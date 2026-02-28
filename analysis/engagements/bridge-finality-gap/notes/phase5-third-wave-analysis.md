# Phase 5: Third Wave Analysis — Fluid, EulerSwap, Morpho Full Scan, Uni V4, Recent Exploits

## Date: 2026-02-28
## Chain: Ethereum Mainnet (block ~24554470)

## Summary

After exhausting all 6 Phase 4 targets, Phase 5 expanded investigation to: Fluid Protocol composition, EulerSwap calcLimits quantification, full 1216-market Morpho oracle scan, Uniswap V4 hooks, Aave e-mode oracle analysis, and recent 2026 exploit patterns. No immediately exploitable, permissionless composition vulnerability found on Ethereum mainnet.

---

## 1. Fluid Protocol — NOT EXPLOITABLE

### Architecture
- **Shared Liquidity Layer** (`0x52Aa...`) holds ALL protocol funds
- 163 lending vaults, multiple DEX pools
- Novel "Smart Collateral" (LP positions as collateral) and "Smart Debt" (debt positions as DEX liquidity)
- TVL: ~$3.3B across all chains

### Oracle Design
- Uses **Chainlink + Redstone** external oracles (NOT Fluid DEX prices)
- UniV3CheckCLRSOracle cross-references Uniswap V3 TWAP at 3+ time windows against Chainlink/Redstone
- Flash loan oracle manipulation is NOT feasible via DEX

### Security Posture
- 7+ years with zero smart contract exploits (Instadapp heritage)
- Cantina competition: 13 issues (no critical drain)
- MixBytes audit: no dangerous vulnerabilities
- Statemind audit: TWAP revert-based DoS (not drain)
- Immunefi bug bounty: up to $500K
- **Liquidity Layer circuit breakers**: restrict abnormal large withdrawals/borrows per block

### Why Not Exploitable
1. Oracle reads are external (Chainlink/Redstone), not from Fluid DEX → DEX manipulation doesn't affect lending valuations
2. Circuit breakers throttle large operations → even if a vulnerability existed, extraction is rate-limited
3. Governance multisig can pause → adds another layer of defense
4. Extensive audit coverage with no critical findings surviving

### Residual Risk (NOT immediately actionable)
- Smart Collateral composition drift under adversarial swaps (theoretical, requires deep vault valuation analysis)
- Cross-vault reentrancy (MixBytes flagged, but at Liquidity Layer level)
- Tick-based liquidation edge cases (novel, complex, but CTF-tested)

---

## 2. EulerSwap calcLimits() — NOT EXPLOITABLE

### The Bug (ChainSecurity CS-EULSWP-015)
- `calcLimits()` double-counts LP's vault balance when computing output limits
- Occurs in the borrow cap section where `supplyBalance` is added again
- Affects quoted limits, NOT enforced swap limits
- Severity: **Low** (acknowledged, not fixed)

### Why Not Exploitable
1. `calcLimits()` is a **VIEW function** used by periphery to report available swap limits
2. Actual `swap()` function enforces limits independently via vault `withdraw()`/`borrow()` calls
3. Bonding curve invariant verified in `SwapLib.finish()` prevents value extraction
4. A swap attempting to exceed real limits simply **reverts**
5. **$500K live CTF on mainnet**: no funds compromised despite 600+ participants

### EulerSwap Architecture Notes
- No "cool-off period" exists in the source code or documentation
- Single-LP pools with JIT borrowing from Euler V2 vaults
- 5 audits + CTF, 40+ broader Euler audits
- Active $7.5M bug bounty (Cantina)

---

## 3. Full Morpho Market Oracle Scan — NO NEW TARGETS

### Scan Results (all 1216 markets)
- Active markets (supply > 0): **948**
- Anomalies found: **2**

### Anomaly 1: PAXG/USDC (KNOWN — already exploited Oct 2024)
- Oracle: `0xDd1778F71a4a1C6A0eFebd8AE9f8848634CE1101`
- SCALE_FACTOR off by 10^12 (PAXG has 18 decimals, oracle assumed 8)
- Price ratio: 5.2e15x expected → massively overvalues PAXG
- Market still has supply/borrow (accumulated bad debt)
- **NOT a new finding** — this was the known $230K exploit

### Anomaly 2: BOBO/USDS (~$5K supply)
- Custom oracle (746 bytes, NOT MorphoChainlinkOracleV2)
- Price implies 1 BOBO = 0.0000000762 USDS (memecoin)
- Supply: ~$5K, Borrow: ~$72
- **Not economically viable** — nothing meaningful to extract

### Conclusion
After scanning all 1216 markets with 948 having active supply, only the already-known PAXG misconfiguration and a negligible memecoin market flagged. **No new exploitable oracle misconfiguration found.**

---

## 4. Uniswap V4 Hooks — NO IMMEDIATE COMPOSITION DRAIN

### Status
- Live on Ethereum mainnet since Jan 30, 2025
- $1B+ TVL, 150+ hooks deployed
- $15.5M bug bounty (largest in DeFi history)

### Known Exploit
- **Cork Protocol** ($11M, May 2025): Missing `onlyPoolManager` on `beforeSwap`
- This was a HOOK vulnerability, not core V4
- Missing upstream access control fix (Cork used stale periphery code)

### Composition Risk (Theoretical)
- Malicious hook + oracle manipulation → lending drain: theoretical but no real-world case
- Hook front-running via `beforeSwap`/`afterSwap`: possible in theory
- Flash loan within swap callbacks: possible in theory
- No confirmed lending protocol drain via V4 hook as of Feb 2026

### EulerSwap as V4 Hook
- Combined lending + AMM + V4 hook surface is large
- BUT: 5 audits, $500K CTF, $7.5M bounty
- Historical caution: Euler V1 was exploited for $197M (2023) despite 10 audit engagements

---

## 5. Aave V3 E-Mode Oracle Analysis — NO VULNERABILITY

### All 19+ e-mode categories have priceSource = 0x0000...
- No custom e-mode oracle is used on Aave V3 Ethereum
- All e-mode categories use the standard Aave oracle
- This eliminates the "e-mode prices assets at 1:1 while market disagrees" vector
- Standard Aave oracle uses CAPO-wrapped Chainlink feeds with growth caps

### Oracle Sources for Key Tokens
| Token | Aave Price | Source (CAPO adapter) |
|-------|-----------|---------------------|
| wstETH | $2,277 | 0xe1D97bF6... (3333 bytes) |
| weETH | $2,020 | 0x87625393... (3278 bytes) |
| rsETH | $1,977 | 0x72929C95... (3278 bytes) |
| sUSDe | $1.22 | 0x42bc86f2... (3333 bytes) |

All use CAPO adapters → exchange rate growth capped → no atomic manipulation possible.

---

## 6. 2026 Exploit Pattern Analysis

### Dominant Vector: Oracle Misconfiguration (Serial Attacker)
A single attacker/group is systematically scanning for lending protocols with misconfigured Chainlink feeds:
- **Moonwell** ($1.78M, Feb 15, 2026): cbETH/ETH rate used as USD price instead of multiplying by ETH/USD
- **Ploutos Money** ($388K, Feb 26, 2026): BTC/USD feed used for USDC pricing
- Both exploited within blocks of the misconfiguration being committed

### Other Notable 2026 Exploits
| Exploit | Amount | Vector | Chain |
|---------|--------|--------|-------|
| Truebit | $26.4M | Integer overflow in old contract | Ethereum |
| Aperture/SwapNet | $13.5M | Arbitrary call + infinite approvals | Base→Ethereum |
| CrossCurve | $3M | Cross-chain message spoofing | Multi-chain |
| FOOM CASH | $2.26M | Broken ZK verifier (Groth16) | Ethereum |
| Ploutos | $388K | Oracle misconfiguration | Multi-chain |
| Moonwell | $1.78M | Oracle misconfiguration (AI-coded) | Base |

### Relevance to Our Investigation
The serial oracle misconfiguration attacker confirms our investigation angle was correct — oracle misconfigs ARE exploitable when they exist. However:
1. The targets are small/new/unaudited protocols (Moonwell, Ploutos), not Morpho/Aave/Euler
2. Morpho's ecosystem has matured (Oracle Tester, warnings, curated vaults)
3. Our scan of all 1216 Morpho markets found zero new misconfigured oracles with exploitable liquidity
4. The attacker targets protocols that DON'T use Morpho Blue's oracle architecture

---

## Kill Chain Economics Summary (Updated)

Every investigated protocol's defenses hold:

| Protocol | Defense | Why Drain Fails |
|----------|---------|----------------|
| Morpho Blue | LLTV < 1, no QUOTE_VAULT | Collateral donation always costs more than extra borrow |
| Aave V3 | CAPO + external Chainlink | Exchange rate growth capped, no atomic manipulation |
| Euler V2 | Formal verification + $7.5M bounty | Core invariant proven; acknowledged bugs are low-severity |
| Fluid | External oracle + circuit breakers | DEX manipulation doesn't affect lending oracle |
| Balancer V2 | Paused/drained/disabled | No vulnerable pools remain on mainnet |
| Pendle | Deterministic oracles | No market data input to manipulate |
| Uniswap V4 | Core security + $15.5M bounty | Hook vulnerabilities are per-hook, not core V4 |

---

## Conclusion

After Phase 5 analysis covering:
- 1216 Morpho Blue markets (full scan)
- 163 Fluid vaults + DEX pools
- Aave V3 e-mode categories (19+)
- EulerSwap calcLimits() quantification
- Uniswap V4 hook security assessment
- 2026 exploit pattern analysis

**No immediately exploitable, permissionless composition vulnerability exists on Ethereum mainnet** in the investigated protocols. The DeFi ecosystem's defense layers on established protocols are effective. The exploitable targets that exist in 2026 are small, under-audited, newly launched protocols — not the established Morpho/Aave/Euler/Fluid stack.
