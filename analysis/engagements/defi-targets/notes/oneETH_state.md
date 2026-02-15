# oneETH Protocol On-Chain State Probe

**Generated:** 2026-02-15T04:46:59+00:00  
**Contract:** `0x6fcbbb527fb2954bed2b224a5bb7c23c5aeeb6e1`  
**Chain:** Ethereum Mainnet (chain_id=1)  
**Block:** 24459904  

---

## Block Info
- Current block: 24459904
- Current timestamp: 1771130819 (2026-02-15T04:46:59+00:00)

## oneETH Contract: `0x6fcbbb527fb2954bed2b224a5bb7c23c5aeeb6e1`

### Token Info
- Name: oneETH
- Symbol: oneETH
- Decimals: 9
- Total Supply (raw): 228705980158991
- Total Supply: 228,705.980159 oneETH

### Protocol Parameters
- reserveRatio (raw): 99800000000
- MIN_RESERVE_RATIO (raw): 100000000000
- withdrawFee (raw): 100000000000
  - withdrawFee (1e18 scale): 0.000000
- mintFee (raw): 100000000000
  - mintFee (1e18 scale): 0.000000
- minimumRefreshTime (raw): 3600
  - minimumRefreshTime: 3600 seconds = 1.00 hours
- reserveStepSize (raw): 100000000
  - reserveStepSize (if /1e6): 100.0000
- lastRefreshReserve (raw): 1769972939
  - lastRefreshReserve (timestamp): 2026-02-01T19:08:59+00:00
  - Time since last refresh: 1,157,880 seconds = 321.6 hours = 13.4 days

### Key Addresses
- stimulus: `0xc02aaa39b223fe8d0a0e5c4f27ead9083c756cc2`
- gov: `0xff7b5e167c9877f2b9f65d19d9c8c9aa651fe19f`
- lpGov: `0xff7b5e167c9877f2b9f65d19d9c8c9aa651fe19f`
- oneTokenOracle: `0x188c65138b72b2581aca13225c49ecd5029f0aed`
- stimulusOracle: `0x0000000000000000000000000000000000000000`
- chainLink: `0x0000000000000000000000000000000000000001`
- owner: `0x11111d16485aa71d2f2bffbd294dcacbae79c1d4`
- paused: None (N/A (no such function))

### Oracle Return Values
- getStimulusOracle() (raw): 2079970000000
  - (1e18 interpretation): 0.0000020800
  - (1e9 interpretation):  2079.9700000000
  - (1e6 interpretation):  2079970.0000000000
- getOneTokenUsd() (raw): 600473338
  - (1e18 interpretation): 0.0000000006
  - (1e9 interpretation):  0.6004733380
  - (1e6 interpretation):  600.4733380000
- globalCollateralValue() (raw): 162508974195418
  - (1e18 interpretation): 0.0001625090
  - (1e9 interpretation):  162,508.9741954180
  - (1e6 interpretation):  162,508,974.1954180002

### Collateral Array
- collateralArray(0): `0xa0b86991c6218b36c1d19d4a2e9eb0ce3606eb48`
- collateralArray(1): REVERTED (index out of bounds)
- collateralArray(2): REVERTED (index out of bounds)
- collateralArray(3): REVERTED (index out of bounds)
- collateralArray(4): REVERTED (index out of bounds)
- collateralArray(5): REVERTED (index out of bounds)

### Collateral Details

#### Collateral: `0xa0b86991c6218b36c1d19d4a2e9eb0ce3606eb48` (USDC)
  - Name: USD Coin
  - Symbol: USDC
  - Token Decimals: 6
  - acceptedCollateral: 1 (YES)
  - collateralDecimals (oneETH view): 6
  - collateralOracle: `0x25d4ba0b43ce3b1805906060f8bd74868d37388e`
  - getCollateralUsd (raw): 710042468
    - (1e18): 0.0000000007
    - (1e9):  0.7100424680
    - (1e6):  710.0424680000
  - Balance in oneETH contract (raw): 228872189368
  - Balance in oneETH contract: 228,872.189368 USDC

### Key Token Balances in oneETH Contract
- WETH (`0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2`):
  - Raw: 33660737000000000
  - Human: 0.033661 WETH
- USDC (`0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48`):
  - Raw: 228872189368
  - Human: 228,872.189368 USDC

## Oracle Pair Analysis

### Oracle: oneTokenOracle (`0x188c65138b72b2581aca13225c49ecd5029f0aed`)
- pair(): `None`
- owner: `0x6fcbbb527fb2954bed2b224a5bb7c23c5aeeb6e1`
- blockTimestampLast: 1769972939 (2026-02-01T19:08:59+00:00)
- Oracle data age: 1,157,880 sec = 321.6 hrs = 13.4 days
- price0CumulativeLast: 312795387172647503216585296875164948946195378854
- price1CumulativeLast: 2685386026650550828971490021019666168

### Oracle: collateralOracle(USDC) (`0x25d4ba0b43ce3b1805906060f8bd74868d37388e`)
- pair(): `None`
- owner: `0x6fcbbb527fb2954bed2b224a5bb7c23c5aeeb6e1`
- blockTimestampLast: 1769972939 (2026-02-01T19:08:59+00:00)
- Oracle data age: 1,157,880 sec = 321.6 hrs = 13.4 days
- price0CumulativeLast: 705772384096403753418302143013403506669727283791888
- price1CumulativeLast: 2158766243702667642281870146364894

## Solvency Analysis

### Supply
- Total Supply (raw): 228705980158991
- Total Supply (9 decimals): 228,705.980159 oneETH

### Collateral Value
- globalCollateralValue (raw): 162508974195418
  - 6-decimal interpretation: 162,508,974.195418
  - 9-decimal interpretation: 162,508.974195
  - 18-decimal interpretation: 0.000163

### Solvency Ratio
- Collateral / Supply ratio (raw): 71.0558%
  - This means: for every 1 oneETH of supply, there is 0.710558 units of collateral value
- **UNDERCOLLATERALIZED**: Only 71.06% backed

### Reserve Ratio Status
- Current reserve ratio: 99800000000
- Minimum reserve ratio: 100000000000
- Status: **BELOW MINIMUM** - anomalous state!

## Activity Check
- Transfer events in ~10K blocks (~1.5 days): 0
- Transfer events in ~100K blocks (~15 days): 1
  - Most recent Transfer at block 24364007 (95897 blocks / ~13.3 days ago)
    - Event 0: block 24364007 (~13.3 days ago) | value(raw)=16057594133

## Summary & Interpretation

### Key Findings

**1. Protocol Liveness:**
   - Pause status unknown (no paused() function or reverted).

**2. Supply:**
   - Total supply: 228,705.980159 oneETH

**3. Collateral Backing:**
   - Global collateral value (raw): 162508974195418

**4. Reserve Ratio:**
   - Current: 99800000000 | Min: 100000000000

**5. Fees:**
   - Withdraw fee: 100000000000
   - Mint fee: 100000000000

**6. Oracle Freshness:**
   - If TWAP oracles have not been updated in days/weeks, prices are severely stale.
   - Stale TWAP = current spot has outsized influence or price is frozen.
   - This is a critical manipulation vector if liquidity in oracle pairs is low.

**7. Oracle Manipulation Feasibility:**
   - Assess by checking oracle pair reserves above.
   - Low reserves (< $10K equivalent) = trivially manipulable with flash loans.
   - If the oracle pair has not traded in days, the TWAP is frozen at an old price.
   - If stimulus token liquidity is near zero, stimulus oracle can be moved to any price.

---
*Probe completed at 2026-02-15T04:47:15.031882+00:00*
*Total RPC calls: 93*


---

# Deep Oracle & Pair Analysis (Addendum)


======================================================================
oneETH Oracle Pair (slot1): 0x3bab83c78c30ac4c082b06bd62587f1e31172f8f
======================================================================
  Name: Ichi LP Token
  Symbol: ichiLP
  Factory: 0x7dda55bb4403aa2aa810d1ed49efa614878e353b
  token0: 0x6fcbbb527fb2954bed2b224a5bb7c23c5aeeb6e1
  token1: 0xc02aaa39b223fe8d0a0e5c4f27ead9083c756cc2
  LP totalSupply: 119561422964344416
  LP totalSupply (18dec): 0.119561
  reserve0 (raw): 225123302018870
  reserve1 (raw): 65000867719570649232
  reserve0: 225,123.302019 oneETH (9 decimals)
  reserve1: 65.000868 WETH (18 decimals)
  Spot: 1 oneETH = 0.0002887345 WETH
  Spot: 1 WETH = 3,463.3891810507 oneETH
  k: 1.4633e+34
  ~1% impact: ~1,122.816452 oneETH or ~0.324196 WETH
  ~5% impact: ~5,559.437187 oneETH or ~1.605201 WETH
  ~10% impact: ~10,988.009068 oneETH or ~3.172617 WETH
  ~50% impact: ~50,595.307559 oneETH or ~14.608612 WETH
  Last trade: 2026-02-01T19:08:59+00:00 (1,158,096 sec ago = 321.7 hrs = 13.4 days)

======================================================================
USDC Oracle Pair (USDC/WETH UniV2): 0xb4e16d0168e52d35cacd2c6185b44281ec28c9dc
======================================================================
  Name: Uniswap V2
  Symbol: UNI-V2
  Factory: 0x5c69bee701ef814a2b6a3edd4b1652cb9cc5aa6f
  token0: 0xa0b86991c6218b36c1d19d4a2e9eb0ce3606eb48
  token1: 0xc02aaa39b223fe8d0a0e5c4f27ead9083c756cc2
  LP totalSupply: 72499239507603681
  LP totalSupply (18dec): 0.072499
  reserve0 (raw): 9224587644280
  reserve1 (raw): 4446941381609202105582
  reserve0: 9,224,587.644280 USDC (6 decimals)
  reserve1: 4,446.941382 WETH (18 decimals)
  Spot: 1 USDC = 0.0004820748 WETH
  Spot: 1 WETH = 2,074.3668181526 USDC
  k: 4.1021e+34
  ~1% impact: ~46,008.203834 USDC or ~22.179396 WETH
  ~5% impact: ~227,801.898442 USDC or ~109.817558 WETH
  ~10% impact: ~450,241.497762 USDC or ~217.050087 WETH
  ~50% impact: ~2,073,178.763754 USDC or ~999.427269 WETH
  Last trade: 2026-02-15T04:44:59+00:00 (336 sec ago = 0.1 hrs = 0.0 days)

======================================================================
Mystery addr (slot5 of oneTokenOracle): 0x36ca3af27638175e07d64c7bfb51233a44d8f2a6
======================================================================
  Name: None
  Symbol: None
  Factory: None
  token0: None
  token1: None
  LP totalSupply: None
  getReserves: 0x (not a pair or reverted)

======================================================================
ECONOMIC INTERPRETATION
======================================================================

oneETH has 9 decimals
Stimulus token = WETH
Chainlink ETH/USD = $2,079.97

getStimulusOracle() = 2079970000000 raw
  -> This is the Chainlink ETH/USD price * 1e9 = 2079.97 * 1e9
  -> Interpretation: ETH price in USD with 9-decimal precision = $2,079.97

getOneTokenUsd() = 600473338 raw
  -> With 9 decimals: 0.600473338 USD
  -> oneETH is valued at ~$0.60 by the protocol oracle
  -> This should be ~$2,080 if properly tracking ETH
  -> ** MASSIVE DEPEG: oneETH = $0.60 vs ETH = $2,080 (99.97% below peg) **

getCollateralUsd(USDC) = 710042468 raw
  -> Unclear scaling. If 9 decimals: 0.710042468 USD per unit
  -> USDC balance: 228,872 USDC

globalCollateralValue() = 162508974195418 raw
  -> If 9 decimals: 162,508.97 USD
  -> This likely represents the USD value of all USDC collateral
  -> 228,872 USDC * 0.710 = ~162,539 (close match!)
  -> The protocol values USDC at ~$0.71 instead of ~$1.00
  -> ** USDC oracle is also stale/wrong: $0.71 instead of $1.00 **

Solvency check:
  Total supply: 228,705.98 oneETH
  Global collateral value: 162,508.97 (9-dec interpretation)
  Ratio: 162508/228706 = 71.1% backing
  ** PROTOCOL IS UNDERCOLLATERALIZED **

Reserve ratio:
  Current: 99800000000 = 99.8 (if /1e9 = 99.8%)
  Minimum: 100000000000 = 100.0 (if /1e9 = 100%)
  ** Reserve ratio is BELOW minimum (anomalous) **
  This means the algorithmic mechanism has driven collateral backing
  below its own floor, likely because the protocol never adjusts upward
  when the peg breaks and the stimulus token collapses.

Key Risk Factors:
1. oneETH has massively depegged (~$0.60 vs target of ~$2,080 ETH)
2. USDC oracle shows $0.71 (stale TWAP from a pair where USDC/WETH price drifted)
3. The protocol holds 228,872 USDC but values it at only 162,509 due to stale oracle
4. Reserve ratio is below minimum (99.8% < 100%) - anomalous state
5. Last activity was 13+ days ago, last reserve refresh was 13+ days ago
6. Oracle pair for oneETH/WETH likely has near-zero liquidity
7. stimulusOracle is address(0) - disabled or not set
8. WETH balance is negligible (0.034 WETH)
