# EVM Semantics — 1inch V6 AggregationRouter

## Assembly Usage Overview

The 1inch V6 router uses extensive inline assembly across ~60% of its code. Critical assembly blocks:

### 1. _unoswapV2 (lines 5258-5310)
- V2 reserve reading via staticcall to pool.getReserves()
- AMM output calculation with unchecked mul (wrapping arithmetic)
- Pool.swap() call construction
- **Verified safe**: Address masking correct, reserves from staticcall, output validated by pool

### 2. _unoswapV3 (lines 5319-5355)
- V3 pool.swap() call construction with packed callback data
- Return value decoding (int256 negation for output amount)
- **Verified safe**: Standard Uniswap V3 interaction pattern

### 3. uniswapV3SwapCallback (lines 5621-5734)
- Token identification via staticcall to caller (token0/token1/fee)
- CREATE2 pool validation
- Transfer/transferFrom via low-level call
- **Verified safe**: CREATE2 check is structurally correct

### 4. _curfe (Curve swap) (lines 5390-5592)
- Dynamic selector loading from packed constants
- Call construction with variable-length parameters
- Balance-based output measurement for legacy pools
- **Verified safe**: Selector index bounded, memory management correct

### 5. _callTransferFromWithSuffix (lines 4149-4163)
- Manual ABI encoding of transferFrom with appended suffix bytes
- **Verified safe**: from/to/amount at correct offsets; suffix at 0x64+

### 6. ClipperRouter (lines 4577-4730)
- Clipper exchange call construction
- Signature parameter encoding
- **Verified safe**: Standard call pattern

## PUSH0 Usage

The contract is compiled with Solidity 0.8.23 (Shanghai target). PUSH0 appears throughout the bytecode. Foundry fork tests require `evm_version = "cancun"` to execute correctly (Paris EVM rejects PUSH0 → `NotActivated` error).

## Memory Safety

All assembly blocks declare `"memory-safe"`. Free memory pointer is correctly managed. Scratch space (0x00-0x3f) is used for temporary values (e.g., getReserves() output) per Solidity convention.

## Checked vs Unchecked Arithmetic

Assembly math uses wrapping arithmetic (no revert on overflow). This is intentional for gas optimization. The V2 AMM calculation has a theoretical overflow path for amount > 2^224, but this is economically infeasible and the V2 pair's own invariant check provides defense-in-depth.

Solidity-level math (fillOrder amount computation) uses OpenZeppelin Math.mulDiv which is overflow-safe.

## No Transient Storage (TSTORE/TLOAD)

The contract does not use transient storage (EIP-1153). All state is in regular storage. No Cancun-specific opcodes beyond PUSH0.

## Falsifier Results

1. **PUSH0 activation**: Confirmed that Foundry requires explicit `evm_version = "cancun"` for fork tests. The contract bytecode contains PUSH0 at offsets 0x15, 0x23, and throughout.
2. **Assembly mul overflow**: Confirmed theoretical; not practically exploitable due to V2 pair k-check.
3. **Memory safety**: No violations observed in manual review of all assembly blocks.
