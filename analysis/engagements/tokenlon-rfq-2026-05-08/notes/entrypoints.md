# Entrypoints — Tokenlon RFQ stack (chain 1, fork 25,050,789)

All public state-changing entrypoints reachable by an arbitrary EOA.

## UserProxy (0x03f34bE1BF910116595dB1b11E9d1B2cA5D59659 → impl 0x0b9f13ff…675a)
| Selector | Function | Caller gate | Forwards to |
|---|---|---|---|
| `b6f732ae` | `ammWrapperAddr() view` | none | — |
| `298a91fd` | `rfqAddr() view` | none | — |
| `93811c8a` | `rfqv2Addr() view` | none | — |
| `8014bd97` | `pmmAddr() view` | none | — |
| `994dd72e` | `limitOrderAddr() view` | none | — |
| `7f54479a` | `isPMMEnabled() view` | none | — |
| `a9dc9f69` | `isLimitOrderEnabled() view` | none | — |
| `*` | `toAMM(bytes)` payable | only enabled | AMM (call) |
| `*` | `toPMM(bytes)` payable | enabled + `tx.origin == msg.sender` | PMM |
| `*` | `toRFQ(bytes)` payable | enabled + EOA-only | RFQ |
| `*` | `toRFQv2(bytes)` payable | enabled + EOA-only | RFQv2 (currently DISABLED) |
| `*` | `toLimitOrder(bytes)` | enabled + EOA-only | LimitOrder |
| `*` | `multicall(bytes[],bool)` | none | self.delegatecall |

## RFQ (0xfd6c2d24…fab54f)
| Selector | Function | Caller gate | Net effect |
|---|---|---|---|
| `*` | `fill(Order, bytes mmSig, bytes userSig) payable` | `onlyUserProxy + nonReentrant` | spend taker token from `order.takerAddr`, spend maker token from `order.makerAddr`, settle to `order.receiverAddr` minus feeFactor |
| `*` | `setAllowance(address[], address)` | `onlyOperator` | grant MAX allowance for fee withdrawal |
| `*` | `closeAllowance(address[], address)` | `onlyOperator` | revoke allowance |
| `*` | `upgradeSpender(address)` | `onlyOperator` | rebind spender |
| `*` | `transferOwnership(address)` | `onlyOperator` | rotate operator |

## RFQv2 (0x91c98670…ea4a)  — CURRENTLY DISABLED
| Selector | Function | Caller gate | Net effect |
|---|---|---|---|
| `*` | `fillRFQ(RFQOrder, makerSig, makerTokenPermit, takerSig, takerTokenPermit) payable` | `onlyUserProxy` | TokenCollector pulls maker+taker tokens via Spender / EIP-2612 permit / Permit2 (allowance or signature transfer), settle to `order.recipient` |
| `*` | `setFeeCollector(address)` | `onlyOwner` | rotate fee sink |

## PMM (0x8d901131…3c6, source = "0x v2", v5.0.0)
| Selector | Function | Caller gate | Net effect |
|---|---|---|---|
| `*` | `fill(uint256 userSalt, bytes data, bytes userSig) payable returns(uint256)` | `onlyUserProxy + nonReentrant` | wraps `zeroExchange.executeTransaction(userSalt, address(this), data, "")` then settles maker token to receiver |
| `*` | `setAllowance / closeAllowance / transferOwnership` | `onlyOperator` |  |

## LimitOrder (0x623a6b34…f71a)
| Selector | Function | Caller gate | Net effect |
|---|---|---|---|
| `*` | `fillLimitOrderByTrader(Order, makerSig, TraderParams, CoordinatorParams)` | `onlyUserProxy + nonReentrant` | maker sig + taker sig + coordinator allowFill sig; spendFromUser(maker, makerToken) and spendFromUser(trader, takerToken); pay maker+trader minus fees |
| `*` | `fillLimitOrderByProtocol(Order, makerSig, ProtocolParams, CoordinatorParams)` | `onlyUserProxy + nonReentrant` | maker sig + coordinator sig; `_settleForProtocol` pulls maker token, swaps via UniV3/Sushi, requires `takerTokenOut >= takerTokenAmount`, pays `profitRecipient` the surplus, pays maker the takerAmount, charges fees |
| `*` | `cancelLimitOrder(Order, sig)` | `onlyUserProxy + nonReentrant` | requires maker to sign a copy of order with `takerTokenAmount = 0` |
| `*` | `setProfitFeeFactor / setMakerFeeFactor / setTakerFeeFactor / setCoordinator / setFeeCollector / upgradeSpender / setSpender` | `onlyOperator` |  |

## AMMWrapperWithPath (0x4a143470…650d)
| Selector | Function | Caller gate | Net effect |
|---|---|---|---|
| `*` | `trade(Order, uint256 _feeFactor, bytes _sig, bytes _makerSpecificData, address[] _path) payable returns(uint256)` | `onlyUserProxy + nonReentrant` | user-sig over `tradeWithPermit` (no `_path`!); pulls taker asset from `order.userAddr`; routes through `order.makerAddr ∈ {UniV2, UniV3, Sushi, Curve}`; settles to `order.receiverAddr`; collects fee on surplus, subsidizes shortfall iff `permStorage.isRelayerValid(tx.origin)` |
| `*` | `depositETH()` | `onlyOperator` | wrap stuck ETH to WETH |
| `*` | `setAllowance / closeAllowance / setSubsidyFactor / upgradeSpender / transferOwnership` | `onlyOperator` |  |

## Spender (0x3c68dfc4…57a6)
| Selector | Function | Caller gate | Net effect |
|---|---|---|---|
| `*` | `spendFromUser(address user, address token, uint256 amount)` | `onlyAuthorized` | calls `AllowanceTarget.executeCall(token, transferFrom(user, msg.sender, amount))`; reverts if balance delta != amount |
| `*` | `spendFromUserTo(address user, address token, address to, uint256 amount)` | `onlyAuthorized` | same but explicit destination |
| `*` | `authorize(address[]) / completeAuthorize() / deauthorize(address[])` | operator + 1-day timelock | mint new authorities (highest-blast-radius op) |
| `*` | `setAllowanceTarget(address)` | `onlyOperator`, one-shot | initial wiring |
| `*` | `blacklist(address[], bool[])` | `onlyOperator` | block specific tokens |

## AllowanceTarget (0x8a42d311…3073)
| Selector | Function | Caller gate | Net effect |
|---|---|---|---|
| `*` | `executeCall(address payable target, bytes calldata callData)` | `onlySpender` | `target.call(callData)`; used by Spender to perform ERC20 transferFrom on behalf of users |
| `*` | `setSpenderWithTimelock / completeSetSpender / teardown` | `onlySpender` (the *current* one) | rotate the Spender contract |

## PermanentStorage (0x6d9cc14a… → impl 0x32c1f83d…)
- `setCurvePoolInfo(makerAddr, underlyings, coins, supportGetDx)` — gated by storageId
- `setAMMTransactionSeen / setRFQTransactionSeen / setRFQOfferFilled / setLimitOrderTransactionSeen / setLimitOrderAllowFillSeen` — per-strategy gated, storageId-based
- `setRelayersValid(address[], bool[])` — gated; controls AMMWrapper subsidy eligibility
- `upgradeAMMWrapper / upgradePMM / upgradeRFQ / upgradeRFQv2 / upgradeLimitOrder / upgradeWETH` — `onlyOperator`
