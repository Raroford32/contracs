# Control Plane: Bridge Finality Gap — Across Protocol Focus

## Updated With Live On-Chain Evidence (Block 24,539,741)

### Security Architecture Overview

```
Layer 1: ABT Proposer Whitelist (who can propose)
Layer 2: Dataworker Validation (what gets proposed)
Layer 3: UMA OO Dispute Window (who can challenge)
Layer 4: Multisig Admin (who controls parameters)
```

### ABT BondToken Whitelist (Layer 1)
- Contract: 0xee1dc6bcf1ee967a350e9ac6caaaa236109002ea
- Key function: transferFrom() blocks non-whitelisted proposers
- setProposer(address, bool) — onlyOwner
- Owner: 0xb524735356985d2f267fa010d681f061dff03715 (3/5 Gnosis Safe)

### Whitelisted Proposers
| Address | Type | ABT Balance | Status |
|---------|------|-------------|--------|
| 0xf7bac63fc7ceacf0589f25454ecf5c2ce904997c | **EOA** | 14.706 ABT | **ONLY ACTIVE** |

### HubPool Admin (Layer 4)
- Owner: 3/5 Gnosis Safe (same as ABT owner)
- 5 owners, threshold 3, 407 txs executed
- GnosisSafe v1.3.0

### Dispute Mechanism (Layer 3)
- **ZERO disputes EVER** in RootBundleDisputed events
- Liveness: 1800s (30 min)
- disputeRootBundle() — permissionless with ABT bond

### Auth Gate Bypass Analysis
| Gate | Bypass Feasibility |
|------|-------------------|
| ABT proposer whitelist | Requires 3/5 multisig |
| requestSlowFill | **NO GATE** — permissionless, confirmed via eth_call |
| executeSlowRelayLeaf | Requires merkle proof against posted root |
| disputeRootBundle | **NO GATE** — permissionless with bond |

### Critical Single Points of Failure
1. **Single EOA proposer** — if key compromised, can propose malicious roots
2. **Dormant dispute mechanism** — zero disputes ever, unclear validator count
3. **3/5 multisig** — if 3 keys compromised, full protocol control

### Previously Analyzed (Lower Priority)

**Metis L1 Bridge (0x3980c9ed79d2c191a89e02fa3529c60ed6e9c04b):**
- Auth: CrossDomainEnabled.onlyFromCrossDomainAccount(l2TokenBridge)
- Trust: L1 contract → CrossDomainMessenger → L2 Bridge

**Celer cBridge (0x5427FEFA711Eff984124bfBB1AB6fbf5E3DA1820):**
- Auth: 2/3+1 stake-weighted ECDSA multi-sig (SGN validators)
- ecrecover + DelayedTransfer + VolumeControl

**Hop L1 ETH Bridge (0xb8901acB165ed027E32754E0FFe830802919727f):**
- Auth: onlyBonder + merkle proof settlement
- challengePeriod: 1 day, resolution: 10 days
