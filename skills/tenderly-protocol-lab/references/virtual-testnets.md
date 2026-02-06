# Virtual TestNets (Multi-Block Experiment Lab)

Sources of truth:
- Virtual TestNets overview: https://docs.tenderly.co/virtual-testnets
- Admin RPC methods: https://docs.tenderly.co/virtual-testnets/admin-rpc
- State Sync: https://docs.tenderly.co/virtual-testnets/state-sync

## What to use Virtual TestNets for (security research)
- Sequences that span blocks (cooldowns, epochs, TWAP windows, auction rounds).
- Experiments that require rapid state setup and repeated resets.
- “Scientific method” loops: modify one thing, run a sequence, revert, repeat.

## Admin RPC (cheatcodes) essentials
Admin RPC is a separate RPC URL copied from the Tenderly dashboard.
Per docs: special methods only work when called through the Admin RPC.

### Commonly used methods
Time + blocks:
- `evm_increaseTime`
- `evm_setNextBlockTimestamp`
- `tenderly_setNextBlockTimestamp`
- `evm_increaseBlocks`
- `evm_mine`

Snapshots:
- `evm_snapshot`
- `evm_revert`

Balances/tokens:
- `tenderly_setBalance`
- `tenderly_addBalance`
- `tenderly_setErc20Balance`
- `tenderly_setMaxErc20Balance`

Storage/code:
- `tenderly_setStorageAt`
- `tenderly_setCode`

Other:
- `eth_sendTransaction` (unsigned tx submission on the VNet)
- `evm_getLatest` (fetch latest VNet tx id)

## State Sync (keep fork current)
State Sync keeps a VNet synced to the parent chain:
- reads track the parent chain until you write locally
- after writing to a slot/balance, sync stops for that modified slot, but continues for unmodified ones

Important caveat from docs:
- behavior of contracts that cache `block.number` can be unpredictable because VNet block numbers advance independently of mainnet.

## Recommended experiment loop
1. Create VNet and (optionally) enable State Sync.
2. Snapshot (`evm_snapshot`).
3. Use Admin RPC to set balances/storage needed for the experiment.
4. Send txs (either from your local tooling against the VNet RPC, or via Admin RPC `eth_sendTransaction`).
5. Capture evidence (traces/state changes) and summarize belief changes.
6. Revert (`evm_revert`) and iterate.

