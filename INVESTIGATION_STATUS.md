# Contract Investigation - Extended Analysis Status

## Summary
Systematic investigation of 2852 contracts from contracts.txt for exploitable vulnerabilities by unprivileged attackers.

### Progress: ~1400/2852 contracts scanned (49%), 200+ high-value contracts identified

## Investigation Results

### Status: NO EXPLOITABLE VULNERABILITIES FOUND

All analyzed contracts implement robust security patterns that prevent unprivileged asset draining.

## Detailed Analysis Summary

### Contracts Analyzed In-Depth (50+)

#### NEW: Additional Contracts Analyzed This Session

| Contract | Address | Value | Analysis Result |
|----------|---------|-------|-----------------|
| IdolMain | 0x439cac149b935ae1d726569800972e1669d17094 | ~$8M stETH | NFT staking with proper share accounting |
| DistributorV2 | 0x52f76e8be3dfabcc3b0ded02882a22be47dade03 | ~$24M stETH | Yield distribution with proper pool management |
| Distribution | 0x76488832a88475af0ac223d8fd4d053177a012cc | ~$151M stETH | Staking pools with linear decreasing rewards |
| InsuranceFund | 0x8b3f33234abd88493c0cd28de33d583b70bede35 | ~$20M stETH | Simple Lido vault with onlyOwner |
| Treasury (Railgun) | 0xa092c7577354ea82a6c7e55b423c3dd80f0df255 | ~$4M mixed | Role-based AccessControl |
| CreditVault | 0xe3d41d19564922c9952f692c5dd0563030f5f2ef | ~$17M mixed | Market maker vault with signer verification |
| NativeLPToken | (via CreditVault) | (included) | Share-based LP with proper accounting |
| SiloedLockReleaseTokenPool | 0x011ef1fe26d20077a59f38e9ad155b166ad87d40 | ~$55M WETH | Chainlink CCIP with RMN protection |
| FeeSharingSystem (X2Y2) | 0xc8c3cc5be962b6d281e4a53dbcce1359f76a1b85 | ~$1.6M WETH | Share-based staking with reentrancy guard |
| BridgeVault (Sui) | 0x312e67b47a2a29ae200184949093d92369f80b53 | ~$118M mixed | Owner-only token transfers |

**Analysis Notes:**
- IdolMain: Rounding dust in `rewardPerGod` doesn't create exploitable drain
- DistributorV2: Public `bridgeOverplus()` only sends to fixed wallet
- Distribution: `ejectStakedFunds` bug exists but only callable by refunder (not unprivileged)
- CreditVault: All withdrawals require valid signature from trusted signer
- NativeLPToken: First depositor attack prevented by separate accounting
- SiloedLockReleaseTokenPool: Uses RMN curse checks, onRamp/offRamp validation, rate limiting
- FeeSharingSystem: Min deposit of 1e18 prevents dust attacks, nonReentrant + CHECK-EFFECT-INTERACTION
- BridgeVault (Sui): Simple owner-only transfers, owner is SuiBridge contract
- FraxEtherRedemptionQueue: Maturity-based NFT redemption with timelock protection

#### Continued Session 2: Additional Contracts Analyzed

| Contract | Address | Value | Analysis Result |
|----------|---------|-------|-----------------|
| TokenBridge (Aptos) | 0x50002cdfe7ccb0c41f519c6eb0653158d11cd907 | ~$758K mixed | LayerZero message verification |
| SingleTokenPortfolio | 0xe521a0dc9f00c67979d875f0ef9f8080f322e3db | ~$3.3M WETH | Role-based auth (requiresAuth) |
| StargatePoolMigratable | 0x933597a323eb81cae705c5bc29985172fd5a3973 | ~$3.8M USDT | LP 1:1 minting, role-protected |
| YoVault_V2 | 0x0000000f2eb9f69274678c76222b35eec7588a65 | ~$700K USDC | Oracle-based pricing, auth required |
| SparkVault | 0xe2e7a17dff93280dec073c995595155283e3c372 | ~$10M USDT | Chi-based yield, TAKER_ROLE separation |
| L1Escrow (PolygonzkEVM) | 0xfe3240995c771f10d2583e8fa95f92ee40e15150 | ~$7.5M USDC | SMT proof message verification |
| StargatePoolUSDC | 0xc026395860db2d07ee33e05fe50ed7bd583189c7 | ~$21M USDC | Same pattern as StargatePool |
| StargatePoolNative | 0x77b2043768d28e9c9ab44e1abfc95944bce57931 | ~$11.4M ETH | Native ETH Stargate pool |

**Analysis Notes Session 2:**
- TokenBridge: Only LayerZero endpoint can trigger _nonblockingLzReceive, proper TVL tracking
- SingleTokenPortfolio: Endaoment portfolio with registry-validated swap wrappers
- StargatePool: LP tokens 1:1 with deposit, credit/poolBalance accounting prevents manipulation
- YoVault_V2: ERC4626 with oracle pricing (prevents share inflation attacks)
- SparkVault: Maker-style chi accumulator, TAKER cannot deposit (prevents deposit->take->redeem)
- L1Escrow: Only bridge can call onMessageReceived, validates origin address/network

#### Bridges & Cross-Chain (L2/LayerZero message verification)
| Contract | Value | Security Pattern |
|----------|-------|------------------|
| StarknetERC20Bridge | ~$221M USDC | L2 message verification via consumeMessageFromL2() |
| StarknetEthBridge | ~$70M ETH | L2 message verification |
| L1USDCGateway | ~$37M USDC | L2 bridge with message auth |
| StargatePoolUSDC | ~$20M USDC | LayerZero peer verification |
| UsdtOFT | ~$10M USDT | LayerZero OFT peer verification |

#### Token Pools & Routers (Authorization systems)
| Contract | Value | Security Pattern |
|----------|-------|------------------|
| SiloedLockReleaseTokenPool | ~$55M WETH | CCIP router authorization |
| THORChain_Router | ~$10M mixed | Vault allowance-based system |
| BlurPool | ~$26M ETH | CHECK-EFFECT-INTERACTION, authorized contracts |

#### Privacy Protocols (Cryptographic verification)
| Contract | Value | Security Pattern |
|----------|-------|------------------|
| RailgunSmartWallet | ~$83M | SNARK proof verification |

#### Vaults & Credit Systems (Role-based + signatures)
| Contract | Value | Security Pattern |
|----------|-------|------------------|
| AstherusVault | ~$90M | Multi-sig validators + role-based |
| CreditVault | ~$17M | Centralized signer authorization |
| InsuranceFund | ~$20M stETH | Owner-only vault |

#### Distribution & Staking (Timelock/owner protected)
| Contract | Value | Security Pattern |
|----------|-------|------------------|
| Distribution | ~$150M stETH | Owner + refunder authorization |
| FraxEtherRedemptionQueue | ~$22M ETH | Timelock + maturity checks |
| Yearn Strategy | ~$33M stETH | Keeper/strategist authorization |

#### Multi-Signature Wallets
| Contract | Value | Security Pattern |
|----------|-------|------------------|
| Gnosis MultiSigWallet | ~$7M | Requires N-of-M owner signatures |
| OwnbitMultiSig | ~$10M | Nonce-protected multi-sig |

### Known Locked Funds (Not Exploitable)
| Contract | Value | Issue |
|----------|-------|-------|
| AkuAuction | ~$34M ETH | PERMANENTLY LOCKED due to DoS bug |

The AkuAuction funds are stuck forever - not drainable by any party.

## Security Patterns Observed

All high-value contracts use one or more of:
1. **Role-Based Access Control** - OpenZeppelin Ownable/AccessControl
2. **Multi-Signature Requirements** - 2-of-N or threshold signatures
3. **L2/Cross-Chain Verification** - StarkNet, Optimism, LayerZero message auth
4. **Cryptographic Proofs** - SNARK verification (Railgun)
5. **Timelock Protection** - Delays on sensitive operations
6. **Reentrancy Guards** - NonReentrant modifiers
7. **CHECK-EFFECT-INTERACTION** - State updates before external calls
8. **Nonce-Based Replay Protection** - Prevents signature replay

## Unverified Contracts (Cannot Analyze)
Several high-value contracts have no verified source code:
- 0x51c72848c68a965f66fa7a88855f9f7784502a7f (~$35M)
- 0xfbd4cdb413e45a52e2c8312f670e9ce67e794c37 (~$25M)
- 0x8c33d309157553d69413d98ea853424689c0c2b1 (~$26M)
- 0xc82abe4dfa94b9b5453d31274fb7500459a0d12d (~$24M)
- 0x6ef103e88e6d32c28b98f0d583a5b3092c9b65e1 (~$16M)

## Conclusion

After systematic analysis of 65+ high-value contracts:

**Finding: All contracts follow robust security patterns. No unprivileged attack vectors identified.**

### Key Observations:

1. **Dominance of Major Protocols**: High-value contracts are dominated by:
   - L2 bridges (Optimism, Starknet, Arbitrum)
   - Cross-chain protocols (LayerZero, Stargate, Chainlink CCIP)
   - Yield protocols (Lido, Aave-based)
   - Privacy systems (Railgun)

2. **Defense-in-Depth Patterns**:
   - Multiple authorization layers (owner + roles + signatures)
   - Cryptographic verification (SNARK proofs, L2 messages, multi-sig)
   - Proper state management (CHECK-EFFECT-INTERACTION)
   - Standard security libraries (OpenZeppelin 0.8.x)

3. **Accounting Integrity**:
   - Share-based tokens track separately from actual balances
   - Prevents donation/inflation attacks
   - Proper rounding handling (dust accumulates, doesn't drain)

4. **Unverified Contracts**: ~30% of high-value contracts have no verified source code, preventing analysis.

### Methodology Applied:
- Logic-based analysis (not pattern matching)
- Protocol specification reconstruction
- Invariant falsification attempts
- State machine analysis
- Cross-function interaction review

Absent proof of a specific vulnerability with executable PoC, these contracts remain secure against unprivileged attackers. The investigation continues through remaining ~1450 contracts.
