# Tokens: Bridge Finality Gap

## Token Semantics (Bridge-Relevant)

Tokens flowing through fast bridges are standard L1 tokens. The finality gap attack
does not depend on token semantics (fee-on-transfer, rebasing, etc.) because:
- The attack creates a phantom DEPOSIT on L2 (token already received by L2 contract)
- The extraction is via standard WITHDRAWAL on L1 (standard ERC20 transfer)

Token-specific risks are orthogonal to the finality gap vector.

## Across Protocol Token Handling
- outputToken: address from relayData (must be deployed on destination chain)
- wrappedNativeToken: special handling with unwrap before send
- Standard ERC20: safeTransfer / safeTransferFrom
- No fee-on-transfer handling visible in fill path (potential secondary issue but not finality-related)

## Metis Bridge Token Handling
- ETH: direct call{value} transfer
- ERC20: SafeERC20.safeTransfer
- Metis token: specific handler
