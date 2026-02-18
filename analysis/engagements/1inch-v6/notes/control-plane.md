# Control Plane — 1inch V6 AggregationRouter

## Auth Mechanisms
- **Ownable** (OpenZeppelin v5): single `owner` stored in ERC-7201 namespaced storage
- **Pausable** (OpenZeppelin v5): `whenNotPaused()` modifier on swap/fill functions
- **EIP-712 signatures**: order validation in fillOrder (ECDSA + ERC1271)
- **MakerTraits flags**: `isAllowedSender(msg.sender)` — maker can restrict who fills
- **Nonce/epoch system**: bit invalidators + remaining invalidators for order replay protection

## Auth State Locations
- Owner: OpenZeppelin Ownable storage slot (ERC-7201)
- Paused: OpenZeppelin Pausable storage slot
- Bit invalidators: `mapping(address => BitInvalidatorLib.Data) _bitInvalidator` (by maker)
- Remaining invalidators: `mapping(address => mapping(bytes32 => RemainingInvalidator)) _remainingInvalidator`
- Epoch: `mapping(address => mapping(uint256 => uint256)) private _epochs`

## Auth Writers
| Writer | Target | Reachable by |
|---|---|---|
| `transferOwnership()` | owner | current owner only |
| `renounceOwnership()` | owner | current owner only |
| `pause()` / `unpause()` | paused state | owner only |
| `rescueFunds()` | token transfers | owner only |
| `cancelOrder()` / `cancelOrders()` | invalidator state | msg.sender (own orders only) |
| `bitsInvalidateForOrder()` | bit invalidator | msg.sender (own) |
| `increaseEpoch()` | epoch counter | msg.sender (own) |

## Bypass Hypotheses
1. **No bypass found for onlyOwner**: Standard OpenZeppelin v5, no initialize/reinit path. Constructor sets owner. Not upgradeable.
2. **whenNotPaused bypass**: None — all swap functions use this modifier consistently.
3. **Order signature bypass**: fillOrder validates ECDSA.recover; fillContractOrder validates ERC1271.isValidSignature. Standard implementations.
4. **Taker interaction is NOT auth-gated**: The taker interaction target in fillOrderArgs is fully caller-controlled. This is by design — the taker uses it for their own purposes.
5. **curveSwapCallback has NO auth gate**: Confirmed exploitable for router balance drain.
6. **uniswapV3SwapCallback partial bypass**: The payer==address(this) path has no pool validation.

## Discriminator Results
- curveSwapCallback: No auth → any caller can drain router balance (see taint-map.md)
- uniswapV3SwapCallback: Conditional — no auth when payer==self, CREATE2 validation otherwise
- simulate(): Always reverts → state changes rolled back → safe despite delegatecall
- permitAndCall(): delegatecall to self → msg.sender preserved → no privilege escalation
