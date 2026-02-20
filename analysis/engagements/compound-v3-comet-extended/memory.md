# Memory (compound-v3-comet-extended)

## Pinned Reality
- chain_id: 1 (Ethereum Mainnet)
- fork_block: 24497000
- upgrade_block: 24427127
- attacker_tier: public mempool (default assumption)
- capital_model: flash loans allowed; Aave/Balancer/Uniswap flash available

## Contract Map Summary
- core: 0x3afdc9bca9213a35503b077a6072f3d0d5ab0840 (Compound V3 USDT market, TransparentUpgradeableProxy)
- proxies -> implementations:
  - 0x3afd...0840 -> 0xda54...ed6 (CometWithExtendedAssetList, NEW, 15 assets)
  - 0x3afd...0840 -> 0xdf68...634d (CometWithExtendedAssetList, OLD, 14 assets)
- admin: 0x1ec63b5883c3481134fd50d5daebc83ecd2e8779 (CometProxyAdmin)
- governor: 0x6d903f6003cca6255d85cca4d3b5e5146dc33925 (Timelock)
- factory: 0x1fa408992e74a42d1787e28b880c451452e8c958 (CometFactoryWithExtendedAssetList)
- oracles: XAU/USD Chainlink 0x214e...0d6, ETH/USD 0xc005...3ad, BTC/USD 0xc8e4...8fc, + 12 more
- baseToken: 0xdac17f958d2ee523a2206206994597c13d831ec7 (USDT, 6 decimals)
- baseTokenPriceFeed: 0x3e7d1eab13ad0104d2750b8863b489d65364e32d (USDT/USD)
- TVL: ~$342M (WBTC $94M, USDT $75M, wstETH $59M, WETH $41M, sFRAX $37M, tBTC $25M, etc.)

## Alert Resolution
- risk_level: CRITICAL_MISMATCH_RUSH → **FALSE POSITIVE**
- deployer mismatch: EXPLAINED — CometFactory deploys impls, governance upgrades proxy
- rush (0 hours): EXPLAINED — atomic governance execution (deploy+upgrade in same tx/block)
- code diff: **ZERO** — identical Solidity source; only constructor args differ
- config change: **numAssets 14→15** — added XAUt (Tether Gold) as asset index 14

## Upgrade Change Summary
- **Only change**: Added XAUt (0x68749665ff8d2d112fa859aa293f07a622782f38) as collateral asset #14
- XAUt config: borrowCF=0.70, liqCF=0.75, liqFactor=0.90, supplyCap=200 XAUt (~$1M), 6 decimals
- Price feed: Chainlink XAU/USD EACAggregatorProxy (0x214e...0d6), ~$5039/oz
- All other 14 asset configs: UNCHANGED

## Control Plane & Auth
- auth: immutable governor + pauseGuardian in bytecode; TransparentUpgradeableProxy + CometProxyAdmin
- upgrade path: Timelock → CometProxyAdmin → proxy.upgradeAndCall()
- bypass attempts: all major families checked and falsified (see notes/control-plane.md)
- no attacker-reachable path to change privileged auth state

## Coverage Status (all complete)
- entrypoints: notes/entrypoints.md ✓
- control plane: notes/control-plane.md ✓
- taint map: notes/taint-map.md ✓
- tokens: notes/tokens.md ✓ (XAUt: blocklist, upgradeable, no fees, standard OZ ERC20)
- numeric boundaries: notes/numeric-boundaries.md ✓
- feasibility: notes/feasibility.md ✓
- value flows: notes/value-flows.md ✓
- assumptions: notes/assumptions.md ✓
- hypotheses: notes/hypotheses.md ✓

## Value Model Summary
- custody: WBTC, USDT, wstETH, WETH, sFRAX, tBTC, cbBTC, weETH, COMP, LINK, UNI, mETH, + XAUt (new)
- entitlements: supply/borrow positions tracked via principal + index
- key measurements: Chainlink feeds for all 15 assets
- solvency equation: `reserves = USDT_balance - total_supply_present_value + total_borrow_present_value ≥ 0`
- XAUt contribution: max ~$1M at supply cap → 0.3% of TVL

## Top 3 Hypotheses (all deprioritized/falsified)
1) XAUt peg deviation arbitrage → DEPRIORITIZED (bounded by $1M supply cap; current deviation 0.49%)
2) Storage bitmap confusion → FALSIFIED (bit 14 never set before upgrade)
3) Reentrancy via XAUt hooks → FALSIFIED (standard OZ ERC20, nonReentrant on all ops)

## Last Experiment
- command: RPC oracle query + DeBank market price + Comet XAUt balance
- result: Oracle $5039.15, Market $5014.20, deviation 0.49%, XAUt in Comet = 0
- belief change: No actionable exploit. XAUt listing is standard, unused, well-bounded.

## Next Discriminator
- No further discriminators needed for this upgrade analysis
- All hypotheses exhausted or bounded below E3 threshold

## Open Unknowns
- extensionDelegate address (not critical for this upgrade analysis)
- Long-term XAUt peg stability (monitoring, not acute risk)
