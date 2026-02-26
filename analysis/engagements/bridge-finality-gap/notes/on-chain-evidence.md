# On-Chain Evidence: Bridge State at Block 24,539,674

## Across Protocol — Real Numbers

### HubPool (0xc186fA914353c44b2E33eBE05f21846F1048bEda)
- Owner: 0xb524735356985d2f267fa010d681f061dff03715
- **Liveness: 1800 seconds (30 minutes)** — reduced from default 7200s
- Bond token: 0xee1dc6bcf1ee967a350e9ac6caaaa236109002ea ("Across Bond Token" / ABT)
- Bond amount: 0.45 ABT
- Paused: false
- ETH balance: 7.51 ETH
- WETH balance: 1,400.89 WETH (~$3.5M at $2500)
- USDC balance: $1,427,707.89
- Root bundle proposals: ~311 in last 50,000 blocks (~every 32 minutes)
- **Zero disputes observed in sampled window**

### SpokePool Ethereum (0x5c7BCd6E7De5423a257D81B442095A1a6ced35C5)
- Implementation: 0x5e5b726c81f43b953a62ad87e2835c85c4d9dd3b (Ethereum_SpokePool)
- ETH balance: 0.91 ETH
- WETH balance: 75.21 WETH (~$188K)
- USDC balance: $79,100.17
- USDT balance: $111,112.74
- DAI balance: ~$0
- **Total value: ~$380K on Ethereum SpokePool**

### Fill Activity (Last 100 Blocks)
- 41 fills in ~20 minutes (1 fill every ~28 seconds)
- 9 unique relayers
- Top 2 relayers: 61% of volume
  - 0xcad97616f91872c02ba3553db315db4015cbe850 (31.7%)
  - 0x394311a6aaa0d8e3411d8b62de4578d41322d1bd (29.3%)
- Origin chains: Base (22%), Polygon (20%), Arbitrum (17%), BSC (17%)
- Token volume: USDC dominant (18 fills, ~$43K), WETH (16 fills, ~1 WETH), USDT (6 fills, ~$5K)

### Root Bundle Lifecycle (Observed)
- Proposal frequency: every ~32 minutes (~159 blocks)
- Liveness period: 30 minutes
- This means: new proposal roughly every liveness period
- Zero disputes in observed window → dispute mechanism appears dormant

## Synapse FastBridge (0x5523D3c98809DdDB82C686E152F5C58B1B0fB59E)
- NOT a proxy (directly deployed, Solidity 0.8.20)
- ETH balance: 1.97 ETH
- Architecture: role-based (RELAYER_ROLE, GUARD_ROLE, GOVERNOR_ROLE)
- DISPUTE_PERIOD: 30 minutes
- REFUND_DELAY: 7 days
- Relayer fronts own capital, then proves + claims after dispute period

## Celer cBridge V2 (0x5427FEFA711Eff984124bfBB1AB6fbf5E3DA1820)
- 2/3+1 stake-weighted ECDSA multi-sig (SGN validators)
- Uses ecrecover for signature verification
- DelayedTransfer + VolumeControl safeguards for large amounts
- No finality concept — instant on quorum

## Hop L1 ETH Bridge (0xb8901acB165ed027E32754E0FFe830802919727f)
- Bonder-based (onlyBonder modifier)
- Merkle proofs for batch settlement
- Challenge period: 1 day (configurable)
- Challenge resolution: 10 days
