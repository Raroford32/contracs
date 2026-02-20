# Control Plane — Compound V3 USDT Market

## Auth Mechanisms

| Gate | Type | Protects | Storage Location |
|---|---|---|---|
| governor | immutable address | `pause`, `withdrawReserves`, `approveThis` | immutable (in bytecode) |
| pauseGuardian | immutable address | `pause` | immutable (in bytecode) |
| hasPermission(owner, operator) | `isAllowed[owner][manager]` mapping | `supplyFrom`, `transferFrom`, `transferAssetFrom`, `withdrawFrom` | storage mapping `isAllowed` |
| nonReentrant | reentrancy guard slot | all state-modifying user ops | `REENTRANCY_GUARD_FLAG_SLOT` |
| paused | `pauseFlags` packed uint8 | supply, transfer, withdraw, absorb, buy | storage `pauseFlags` |
| initializeStorage | `lastAccrualTime != 0` | one-time init | storage `lastAccrualTime` |

## Auth State Writers

| Writer | Target | Reachable by Attacker? |
|---|---|---|
| `pause()` | `pauseFlags` | No (governor/pauseGuardian only) |
| `withdrawReserves()` | none (token transfer) | No (governor only) |
| `approveThis()` | ERC20 approval | No (governor only) |
| `allow(manager, isAllowed)` | `isAllowed[msg.sender][manager]` | Yes (users set their own permissions) |
| `allowBySig(...)` | `isAllowed[owner][manager]` | Yes (with valid signature) |

## Upgrade Authority

- Proxy admin: `0x1ec63b5883c3481134fd50d5daebc83ecd2e8779` (CometProxyAdmin)
- Governor (Timelock): `0x6d903f6003cca6255d85cca4d3b5e5146dc33925`
- Factory: `0x1fa408992e74a42d1787e28b880c451452e8c958` (CometFactoryWithExtendedAssetList)
- Upgrade path: Timelock → CometProxyAdmin → proxy.upgradeAndCall()
- All immutable config changes require full redeployment + proxy upgrade via governance

## Bypass Hypothesis Matrix

| Bypass Family | Attempted? | Result |
|---|---|---|
| init/reinit paths | N/A | `initializeStorage` is one-shot (`lastAccrualTime != 0`); already initialized |
| proxy/impl confusion | N/A | TransparentUpgradeableProxy prevents admin fallback; can't call impl directly through proxy |
| upgrade authority drift | No | Timelock has 2-day delay; would require governance compromise |
| signature/permit issues | Checked | `allowBySig` uses EIP-712 domain with contract address; nonce-protected |
| callback/hook trust | N/A | No hooks/callbacks in Comet that trust external callers |
| delegatecall clobber | Checked | `extensionDelegate` is immutable; cannot be changed without full redeployment |
| boolean/logic slips | Checked | Auth checks are straightforward `msg.sender == governor` |

## Conclusion
All privileged operations are immutable-gated (governor/pauseGuardian baked into bytecode).
No attacker-reachable writer path exists to change auth state for privileged functions.
The only user-writable auth state is `isAllowed[owner][manager]` (per-user permissions).
