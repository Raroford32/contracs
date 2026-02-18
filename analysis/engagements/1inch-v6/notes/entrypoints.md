# Entrypoints — 1inch V6 AggregationRouter

Source: AggregationRouterV6.mainnet.sol (5786 lines, flattened)
Contract hierarchy: AggregationRouterV6 is EIP712, Ownable, Pausable, ClipperRouter, GenericRouter, UnoswapRouter, PermitAndCall, OrderMixin

## External/Public Functions

### GenericRouter (swap)
| Function | Selector | Callable by | Auth | External calls |
|---|---|---|---|---|
| `swap(executor, desc, data)` | - | EOA/Contract | whenNotPaused | executor.execute() via call |

### UnoswapRouter (unoswap family)
| Function | Selector | Callable by | Auth | External calls |
|---|---|---|---|---|
| `unoswap(token, amount, minReturn, dex)` | - | EOA/Contract | whenNotPaused | pool.swap() or pool.getReserves()+pool.swap() |
| `unoswapTo(to, token, amount, minReturn, dex)` | - | EOA/Contract | whenNotPaused | same |
| `ethUnoswap(minReturn, dex)` | - | EOA/Contract | whenNotPaused | same + WETH deposit |
| `ethUnoswapTo(to, minReturn, dex)` | - | EOA/Contract | whenNotPaused | same |
| `unoswap2(...)` / `unoswapTo2(...)` | - | EOA/Contract | whenNotPaused | 2-hop chained |
| `ethUnoswap2(...)` / `ethUnoswapTo2(...)` | - | EOA/Contract | whenNotPaused | 2-hop + WETH |
| `unoswap3(...)` / `unoswapTo3(...)` | - | EOA/Contract | whenNotPaused | 3-hop chained |
| `ethUnoswap3(...)` / `ethUnoswapTo3(...)` | - | EOA/Contract | whenNotPaused | 3-hop + WETH |
| `uniswapV3SwapCallback(...)` | - | Contract (pool callback) | **SEE TAINT-MAP: no validation when payer==self** | token.transfer or token.transferFrom |
| `curveSwapCallback(...)` | - | **ANY** | **NONE** | token.safeTransfer(msg.sender, dx) |

### ClipperRouter
| Function | Selector | Callable by | Auth | External calls |
|---|---|---|---|---|
| `clipperSwap(...)` | - | EOA/Contract | whenNotPaused | clipper.sellEthForToken/sellTokenForEth/swap |
| `clipperSwapTo(...)` | - | EOA/Contract | whenNotPaused | same |

### OrderMixin (limit orders)
| Function | Selector | Callable by | Auth | External calls |
|---|---|---|---|---|
| `fillOrder(order, r, vs, amount, takerTraits)` | - | EOA/Contract | whenNotPaused | pre/post interaction, taker interaction |
| `fillOrderArgs(order, r, vs, amount, takerTraits, args)` | - | EOA/Contract | whenNotPaused | same + args-specified interactions |
| `fillContractOrder(order, sig, amount, takerTraits)` | - | EOA/Contract | whenNotPaused | same + ERC1271 validation |
| `fillContractOrderArgs(...)` | - | EOA/Contract | whenNotPaused | same |
| `cancelOrder(makerTraits, orderHash)` | - | EOA/Contract | none | state-only |
| `cancelOrders(...)` | - | EOA/Contract | none | state-only |
| `bitsInvalidateForOrder(...)` | - | EOA/Contract | none | state-only |
| `hashOrder(order)` | - | EOA/Contract | view | none |
| `checkPredicate(predicate)` | - | EOA/Contract | view | staticcall to self |
| `simulate(target, data)` | - | EOA/Contract | none | **delegatecall(target, data) but always reverts** |
| `rawRemainingInvalidatorForOrder(...)` | - | EOA/Contract | view | none |
| `remainingInvalidatorForOrder(...)` | - | EOA/Contract | view | none |

### PermitAndCall
| Function | Selector | Callable by | Auth | External calls |
|---|---|---|---|---|
| `permitAndCall(permit, action)` | - | EOA/Contract | none | token.tryPermit() + delegatecall(self, action) |

### Predicate helpers (OrderLib)
| Function | Selector | Callable by | Auth | External calls |
|---|---|---|---|---|
| `and(offsets, data)` | - | EOA/Contract | view | staticcall(self, subdata) |
| `or(offsets, data)` | - | EOA/Contract | view | staticcall(self, subdata) |
| `not(data)` | - | EOA/Contract | view | staticcall(self, data) |
| `eq(value, data)` | - | EOA/Contract | view | staticcall(self, data) |
| `lt(value, data)` | - | EOA/Contract | view | staticcall(self, data) |
| `gt(value, data)` | - | EOA/Contract | view | staticcall(self, data) |
| `arbitraryStaticCall(target, data)` | - | EOA/Contract | view | staticcall(target, data) |
| `timestampBelow(time)` | - | EOA/Contract | view | none |
| `timestampBelowAndNonceEquals(...)` | - | EOA/Contract | view | state read |
| `epochEquals(...)` | - | EOA/Contract | view | state read |

### Admin (Ownable)
| Function | Selector | Callable by | Auth | External calls |
|---|---|---|---|---|
| `rescueFunds(token, amount)` | - | Owner only | onlyOwner | token.uniTransfer |
| `pause()` | - | Owner only | onlyOwner | none |
| `unpause()` | - | Owner only | onlyOwner | none |
| `transferOwnership(newOwner)` | - | Owner only | onlyOwner | none |
| `renounceOwnership()` | - | Owner only | onlyOwner | none |

### EthReceiver
| Function | Selector | Callable by | Auth | External calls |
|---|---|---|---|---|
| `receive()` | - | Any | none (intended for WETH unwrap) | none |

## Fallback
No fallback function defined. Calls to unknown selectors revert.
