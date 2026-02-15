# DeFi Target Scan Results
Generated: 2026-02-15T04:21:44.394691
Scan range: lines 200-1568 of contracts.txt
Unique addresses scanned: 1369

## Top DeFi Targets (Not Previously Analyzed)

| # | Address | Name | Category | ETH | WETH | USDC | USDT | DAI | Total USD | Proxy |
|---|---------|------|----------|-----|------|------|------|-----|-----------|-------|
| 1 | `0x755cdba6ae4f479f7164792b318b2a06c759833b` | WithdrawDAO | withdraw | 1258.2 | - | - | - | - | $3,397,057 | No |
| 2 | `0x737901bea3eeb88459df9ef1be8ff3ae1b42a2ba` | RollupProcessor | abi-signal:deposit | 1158.8 | - | - | 50 | 150,096 | $3,278,797 | No |
| 3 | `0xa62142888aba8370742be823c1782d17a0389da1` | FoMo3Dlong | abi-signal:deposit | 1119.4 | - | - | - | - | $3,022,352 | No |
| 4 | `0x2d3cd7b81c93f188f3cb8ad87c8acc73d6226e3a` | CollateralJoin1 | lending | - | 1115.3 | - | - | - | $3,011,350 | No |
| 5 | `0x6bfad42cfc4efc96f529d786d643ff4a8b89fa52` | EthCustodian | abi-signal:deposit | 998.6 | - | - | 10,064 | - | $2,706,256 | No |
| 6 | `0xaa7427d8f17d87a28f5e1ba3adbb270badbe1011` | WrapperLockEth | wrapper | 950.9 | - | - | 76 | - | $2,567,601 | No |
| 7 | `0x283af0b28c62c092c9727f1ee09c02ca627eb7f5` | ETHRegistrarController | controller | 771.9 | 17.6 | 2,686 | 1,144 | 398 | $2,135,952 | No |
| 8 | `0x09403fd14510f8196f7879ef514827cd76960b5d` | PerpetualProxy | perps | - | 698.3 | - | - | - | $1,885,360 | Yes |
| 9 | `0x167cb3f2446f829eb327344b66e271d1a7efec9a` | GandhiJi | abi-signal:withdraw | 664.2 | - | - | - | 4 | $1,793,277 | No |
| 10 | `0xfceaaaeb8d564a9d0e71ef36f027b9d162bc334e` | CrossProxy | proxy | 7.4 | - | 1,194,009 | 537,447 | - | $1,751,528 | Yes |
| 11 | `0xb8901acb165ed027e32754e0ffe830802919727f` | L1_ETH_Bridge | bridge | 613.0 | - | 45 | - | - | $1,655,270 | No |
| 12 | `0xdc1664458d2f0b6090bea60a8793a4e66c2f1c00` | L1ChugSplashProxy | proxy | - | - | 1,179,317 | 132,499 | 161,050 | $1,472,866 | Yes |
| 13 | `0xd216153c06e857cd7f72665e0af1d7d82172f494` | RelayHub | abi-signal:deposit | 521.7 | - | - | - | - | $1,408,561 | No |
| 14 | `0xe1237aa7f535b0cc33fd973d66cbf830354d16c7` | yVault | vault/yield | - | 495.9 | - | - | - | $1,338,859 | No |
| 15 | `0x35ffd6e268610e764ff6944d07760d0efe5e40e5` | LiquidityPoolV2 | pool/dex | 413.1 | 13.3 | 64,085 | - | 77,607 | $1,292,967 | No |
| 16 | `0x1a2a1c938ce3ec39b6d47113c7955baa9dd454f2` | MainchainGatewayProxy | proxy | 469.4 | - | - | 14,615 | 50 | $1,282,028 | Yes |
| 17 | `0x367e59b559283c8506207d75b0c5d8c66c4cd4b7` | Router | router | - | 91.2 | 721,515 | 222,910 | 7,161 | $1,197,848 | Yes |
| 18 | `0x3fda67f7583380e67ef93072294a7fac882fd7e7` | MoneyMarket | market | - | 426.6 | - | - | - | $1,151,849 | No |
| 19 | `0x5934807cc0654d46755ebd2848840b616256c6ef` | MarginPool | pool/dex | - | 418.0 | 19,952 | - | - | $1,148,686 | No |
| 20 | `0xd18475521245a127a933a4fcaf99e8c45a416f7e` | QDT | abi-signal:deposit | 417.9 | - | - | - | - | $1,128,230 | No |
| 21 | `0x12ed69359919fc775bc2674860e8fe2d2b6a7b5d` | AdminUpgradeabilityProxy | proxy | - | - | 1,061 | 1,080,518 | 46,362 | $1,127,954 | Yes |
| 22 | `0x25751853eab4d0eb3652b5eb6ecb102a2789644b` | AdminUpgradeabilityProxy | proxy | - | 405.7 | - | - | - | $1,095,476 | Yes |
| 23 | `0xf786c34106762ab4eeb45a51b42a62470e9d5332` | fETH | abi-signal:deposit | 404.1 | - | - | - | - | $1,090,957 | No |
| 24 | `0xaba513097f04d637727fdcda0246636e0d5d6833` | DavyJones | abi-signal:deposit | 348.2 | - | - | - | - | $940,247 | No |
| 25 | `0xe5c405c5578d84c5231d3a9a29ef4374423fa0c2` | Custodian | abi-signal:withdraw | 304.8 | - | 21,513 | 15,893 | 396 | $860,867 | No |
| 26 | `0x7b4a7fd41c688a7cb116534e341e44126ef5a0fd` | CEther | abi-signal:borrow | 313.7 | - | - | - | - | $847,020 | No |
| 27 | `0x6f400810b62df8e13fded51be75ff5393eaa841f` | BatchExchange | dex | - | 170.9 | 294,834 | 12,320 | 26,001 | $794,477 | Yes |
| 28 | `0xf74bf048138a2b8f825eccabed9e02e481a0f6c0` | AdminUpgradeabilityProxy | proxy | 291.7 | - | - | - | - | $787,614 | Yes |
| 29 | `0xe9778e69a961e64d3cdbb34cf6778281d34667c2` | WorkLock | abi-signal:deposit | 291.2 | - | - | - | - | $786,209 | No |
| 30 | `0xd3d13a578a53685b4ac36a1bab31912d2b2a2f36` | TransparentUpgradeableProxy | proxy | - | 280.8 | - | 9,945 | - | $768,172 | Yes |
| 31 | `0xd48b633045af65ff636f3c6edd744748351e020d` | Zethr | abi-signal:withdraw | 280.8 | - | - | - | - | $758,288 | No |
| 32 | `0xa7d9e842efb252389d613da88eda3731512e40bd` | BondedECDSAKeepFactory | abi-signal:stake | 258.6 | - | - | - | - | $698,104 | No |
| 33 | `0x60cd862c9c687a9de49aecdc3a99b74a4fc54ab6` | MoonCatRescue | abi-signal:withdraw | 246.7 | - | - | - | - | $666,065 | No |
| 34 | `0x27321f84704a599ab740281e285cc4463d89a3d5` | KeepBonding | abi-signal:deposit | 234.4 | - | - | - | - | $632,930 | No |
| 35 | `0x2e8a97c62cc644adcd108b9bebcb9b32c9c58a1c` | EternalStorageProxy | proxy | - | - | - | 614,747 | - | $614,747 | Yes |
| 36 | `0x5eee354e36ac51e9d3f7283005cab0c55f423b23` | ArbitrageETHStaking | staking | 216.3 | - | - | - | - | $583,981 | No |
| 37 | `0x8754f54074400ce745a7ceddc928fb1b7e985ed6` | EulerBeats | abi-signal:withdraw | 215.2 | - | - | - | - | $580,981 | No |
| 38 | `0x899f9a0440face1397a1ee1e3f6bf3580a6633d1` | RedemptionContract | abi-signal:deposit | 206.3 | - | - | - | - | $556,885 | No |
| 39 | `0xd619c8da0a58b63be7fa69b4cc648916fe95fa1b` | CycloneV2dot2 | abi-signal:deposit | 200.0 | - | - | - | - | $540,000 | No |
| 40 | `0x9149c59f087e891b659481ed665768a57247c79e` | KyberReserve | abi-signal:deposit | 197.0 | - | - | - | - | $531,769 | No |
| 41 | `0x7488451db91df618759b8af15e36f70c0fdd529e` | XifraICO2 | abi-signal:withdraw | 193.6 | - | 42 | 3 | - | $522,740 | No |
| 42 | `0xcd18eaa163733da39c232722cbc4e8940b1d8888` | Sablier | abi-signal:deposit | - | 102.8 | 160,205 | 30,752 | 8,069 | $476,650 | No |
| 43 | `0x7cd5e2d0056a7a7f09cbb86e540ef4f6dccc97dd` | xSNXAdminProxy | proxy | 175.5 | - | - | - | - | $473,870 | Yes |
| 44 | `0xe470198cda121da5b6ad349d3577b166e5985917` | EternalStorageProxy | proxy | - | - | - | 458,893 | - | $458,893 | Yes |
| 45 | `0x6467e807db1e71b9ef04e0e3afb962e4b0900b2b` | FeeReceiver | abi-signal:withdraw | - | 161.7 | 1,860 | 664 | 1,745 | $440,931 | No |
| 46 | `0x33c0d33a0d4312562ad622f91d12b0ac47366ee1` | AdminUpgradeabilityProxy | proxy | 9.3 | - | 118,934 | 178,225 | 98,174 | $420,524 | Yes |
| 47 | `0xc88f47067db2e25851317a2fdae73a22c0777c37` | oneBTC | abi-signal:deposit | - | - | 402,170 | - | - | $402,170 | No |
| 48 | `0xa38b6742cef9573f7f97c387278fa31482539c3d` | CycloneV2dot3 | abi-signal:deposit | 0.8 | - | - | 400,000 | - | $402,160 | No |
| 49 | `0x1180c114f7fadcb6957670432a3cf8ef08ab5354` | TransparentUpgradeableProxy | proxy | - | - | - | 401,696 | - | $401,696 | Yes |
| 50 | `0x256c8919ce1ab0e33974cf6aa9c71561ef3017b6` | BridgePoolProd | pool/dex | - | - | 400,335 | - | - | $400,335 | No |
| 51 | `0xacd43e627e64355f1861cec6d3a6688b31a6f952` | yVault | vault/yield | - | - | - | - | 398,944 | $398,944 | No |
| 52 | `0x587a07ce5c265a38dd6d42def1566ba73eeb06f5` | YAMETHPool | pool/dex | - | 145.7 | - | - | - | $393,484 | No |
| 53 | `0x4547a86ca6a84b9d60dc57af908472074de7af5f` | PASTAPool | pool/dex | - | 145.0 | - | - | - | $391,429 | No |
| 54 | `0xd64b1bf6fcab5add75041c89f61816c2b3d5e711` | OrbsGuardians | abi-signal:deposit | 144.0 | - | - | - | - | $388,800 | No |
| 55 | `0x04bda0cf6ad025948af830e75228ed420b0e860d` | TransparentUpgradeableProxy | proxy | - | - | 386,201 | - | - | $386,201 | Yes |
| 56 | `0x4570b4faf71e23942b8b9f934b47ccedf7540162` | Moloch | abi-signal:deposit | - | 105.3 | 84,801 | 14,361 | 751 | $384,197 | No |
| 57 | `0x6a39909e805a3eadd2b61fff61147796ca6abb47` | UpgradeBeaconProxy | proxy | - | 43.8 | 100,346 | 112,450 | 46,943 | $378,018 | Yes |
| 58 | `0x0ad3227eb47597b566ec138b3afd78cfea752de5` | FoMo3Dshort | abi-signal:deposit | 136.8 | - | - | - | - | $369,268 | No |
| 59 | `0xe5bfab544eca83849c53464f85b7164375bdaac1` | Market | market | - | 124.6 | 8,557 | - | 17,892 | $362,896 | No |
| 60 | `0x9b4ea303ca6302dfa46b73bc660598c65de96b3d` | auto_pool | pool/dex | 128.7 | - | - | - | - | $347,576 | No |
| 61 | `0x773a58c0ae122f56d6747bc1264f00174b3144c3` | KyberReserve | abi-signal:deposit | 120.0 | - | - | - | - | $324,097 | No |
| 62 | `0x67e0eb8557437ab7393243c88a11f3c7e424ca3d` | wethMerkleDistributor | distributor | - | 120.0 | - | - | - | $323,894 | No |
| 63 | `0x8fb1a35bb6fb9c47fb5065be5062cb8dc1687669` | TransparentUpgradeableProxy | proxy | - | - | 280,786 | 31,857 | 3,017 | $315,660 | Yes |
| 64 | `0xd8ee69652e4e4838f2531732a46d1f7f584f0b7f` | bZxProtocol | abi-signal:deposit | - | 111.7 | 2,188 | 3,805 | 2,111 | $309,755 | Yes |
| 65 | `0x1a26ef6575b7bbb864d984d9255c069f6c361a14` | Proxy__L1LiquidityPoolArguments | pool/dex | 113.9 | - | - | 92 | 71 | $307,738 | Yes |
| 66 | `0xb9ab8eed48852de901c13543042204c6c569b811` | Zethr | abi-signal:withdraw | 113.5 | - | - | - | - | $306,481 | No |
| 67 | `0x05fbd3b849a87c9608a2252d095d8cb818d0d239` | TokenICBX | abi-signal:withdraw | - | - | - | 300,000 | - | $300,000 | No |
| 68 | `0x6822aaf4ab22e6cca8352a927b9ae0a8fdb58d9d` | ProfitSharing | abi-signal:deposit | 111.0 | - | - | - | - | $299,772 | No |
| 69 | `0xd2bfceeab8ffa24cdf94faa2683df63df4bcbdc8` | DailyDivs | abi-signal:withdraw | 109.8 | - | - | - | - | $296,407 | No |
| 70 | `0xa33c4a314faa9684eeffa6ba334688001ea99bbc` | Phoenix | abi-signal:deposit | 108.8 | - | - | - | - | $293,707 | No |
| 71 | `0x728781e75735dc0962df3a51d7ef47e798a7107e` | WolkExchange | dex | 107.3 | - | - | - | - | $289,643 | No |
| 72 | `0xe14ab3ee81abe340b45bb26b1b166a7d2df22585` | TweetMarket | market | 105.5 | - | 755 | - | - | $285,620 | No |
| 73 | `0xe01e2a3ceafa8233021fc759e5a69863558326b6` | EKS | abi-signal:deposit | 105.5 | - | - | - | - | $284,831 | No |
| 74 | `0xa45b966996374e9e65ab991c6fe4bfce3a56dde8` | MaticWETH | abi-signal:deposit | 104.7 | - | - | - | - | $282,791 | No |
| 75 | `0xc8c1b41713761281a520b7ad81544197bc85a4ce` | ETHBurgerTransit | abi-signal:withdraw | - | 91.6 | 4,068 | 26,516 | 3,397 | $281,307 | No |
| 76 | `0xb8ff313d33b0e841b6b83243f6e2935166de87c1` | AdminUpgradeabilityProxy | proxy | 101.0 | - | - | - | - | $272,780 | Yes |
| 77 | `0xab5cffaaec03efc94ab5c0c4c0bc85ae2b2b65ac` | EtherkingJackpot | abi-signal:deposit | 101.0 | - | - | - | - | $272,700 | No |
| 78 | `0x9aca6abfe63a5ae0dc6258cefb65207ec990aa4d` | DigiPulse | abi-signal:withdraw | 100.6 | - | - | - | - | $271,575 | No |
| 79 | `0x1fd169a4f5c59acf79d0fd5d91d1201ef1bce9f1` | Moloch | abi-signal:deposit | - | 100.0 | - | - | - | $270,000 | No |
| 80 | `0x25a06d4e1f804ce62cf11b091180a5c84980d93a` | Treasure | abi-signal:withdraw | 98.3 | - | - | - | - | $265,356 | No |
| 81 | `0x6fcbbb527fb2954bed2b224a5bb7c23c5aeeb6e1` | oneETH | abi-signal:deposit | 12.0 | - | 228,872 | - | - | $261,259 | No |
| 82 | `0x59f54eed3e1ea731adbfb0e417490f9b50e31b10` | EternalStorageProxy | proxy | - | 40.5 | 51,686 | 1,328 | 98,745 | $261,243 | Yes |
| 83 | `0x0fabaf48bbf864a3947bdd0ba9d764791a60467a` | AdminUpgradeabilityProxy | proxy | - | 96.3 | - | - | - | $260,202 | Yes |

## High-Value Unclassified Contracts (>$500K, Not Analyzed)

| # | Address | Name | ETH | WETH | USDC | USDT | DAI | Total USD | Proxy |
|---|---------|------|-----|------|------|------|-----|-----------|-------|
| 1 | `0x9fa8fa61a10ff892e4ebceb7f4e0fc684c2ce0a9` | HONG | 1003.6 | - | - | - | - | $2,709,785 | No |
| 2 | `0xd5524179cb7ae012f5b642c1d6d700bbaa76b96b` | Delegator | 772.0 | - | - | - | - | $2,084,474 | Yes |
| 3 | `0x230731528a32a11122426e7688e8d9050a484a77` | ColdWallet | 493.9 | - | - | - | - | $1,333,490 | No |
| 4 | `0x40ed3699c2ffe43939ecf2f3d11f633b522820ad` | Floor | 336.0 | - | - | - | - | $907,319 | No |
| 5 | `0x3a3fba79302144f06f49ffde69ce4b7f6ad4dd3d` | SuperBunnies | 284.3 | - | - | - | - | $767,497 | No |
| 6 | `0x6fb8aa6fc6f27e591423009194529ae126660027` | DerivaDEX | - | - | 459,847 | 246,308 | - | $706,154 | Yes |
| 7 | `0xe5859f4efc09027a9b718781dcb2c6910cac6e91` | Root | - | - | 85,983 | 435,370 | 147,379 | $668,732 | Yes |
| 8 | `0x24f0bb6c9b2c3db66603fa0ec07ab0cf55cdd387` | Holder | 174.7 | - | 72,622 | 65,222 | 58,569 | $668,037 | No |
| 9 | `0x97ec9bfb0f6672c358620615a1e4de0348aea05c` | InsightsNetworkContributions | 208.6 | - | - | - | - | $563,342 | No |
| 10 | `0xbd3af18e0b7ebb30d49b253ab00788b92604552c` | HashesDAO | 205.8 | 0.2 | - | - | - | $556,396 | No |
| 11 | `0xb9fbe1315824a466d05df4882ffac592ce9c009a` | InstantListingV2 | 200.0 | - | - | - | - | $540,000 | No |
| 12 | `0x3666f603cc164936c1b87e207f36beba4ac5f18a` | L1_ERC20_Bridge | - | - | 538,298 | - | - | $538,298 | No |

## All Verified High-Value Contracts (Full List)

1. `0x05b34bf3562c61715f70240104abc6ae8c80055c` - **Wallet** - $4,521,001 [ALREADY ANALYZED]
2. `0x3fcb02a27dc60573a0cb9bff9528fcd77e78d734` - **Wallet** - $4,234,447 [ALREADY ANALYZED]
3. `0xd31a34d621122bebe0dee360e33bbe61193d5b90` - **Wallet** - $3,823,459 [ALREADY ANALYZED]
4. `0xf6e51ae30705cd7248d4d9ac602cb58cc4b61a52` - **Wallet** - $3,780,000 [ALREADY ANALYZED]
5. `0x755cdba6ae4f479f7164792b318b2a06c759833b` - **WithdrawDAO** - $3,397,057 [WITHDRAW]
6. `0xc6aebfc53c5d8be6f19b3d270a322b81b47f3305` - **Wallet** - $3,337,146 [ALREADY ANALYZED]
7. `0x737901bea3eeb88459df9ef1be8ff3ae1b42a2ba` - **RollupProcessor** - $3,278,797 [ABI-SIGNAL:DEPOSIT]
8. `0x55ca4b396927c323326eaa4a3a2743c59b231d06` - **Wallet** - $3,240,000 [ALREADY ANALYZED]
9. `0xd7dfc49e5d13f77830029134fb06f5fa6d5e8ec4` - **Wallet** - $3,176,391 [ALREADY ANALYZED]
10. `0xa62142888aba8370742be823c1782d17a0389da1` - **FoMo3Dlong** - $3,022,352 [ABI-SIGNAL:DEPOSIT]
11. `0x2d3cd7b81c93f188f3cb8ad87c8acc73d6226e3a` - **CollateralJoin1** - $3,011,350 [LENDING]
12. `0xebacd5907d96b80e7d0f94af0292e4e50742d813` - **Wallet** - $2,996,946 [ALREADY ANALYZED]
13. `0x91bd62e48282ea188998d04570ed8a3e237d3a6a` - **MultiSigWallet** - $2,987,021 [ALREADY ANALYZED]
14. `0x1b3de683a4ff93457b0a27986361a5090e3fbb50` - **Wallet** - $2,865,449 [ALREADY ANALYZED]
15. `0x9fa8fa61a10ff892e4ebceb7f4e0fc684c2ce0a9` - **HONG** - $2,709,785
16. `0x6bfad42cfc4efc96f529d786d643ff4a8b89fa52` - **EthCustodian** - $2,706,256 [ABI-SIGNAL:DEPOSIT]
17. `0x1c0e9b714da970e6466ba8e6980c55e7636835a6` - **Wallet** - $2,700,000 [ALREADY ANALYZED]
18. `0xaa7427d8f17d87a28f5e1ba3adbb270badbe1011` - **WrapperLockEth** - $2,567,601 [WRAPPER]
19. `0xdac17f958d2ee523a2206206994597c13d831ec7` - **TetherToken** - $2,486,354 [ALREADY ANALYZED]
20. `0x9a2d163ab40f88c625fd475e807bbc3556566f80` - **Dex** - $2,317,159 [ALREADY ANALYZED]
21. `0xa34edd0e0223c2151b8408e3043b2f6edc564fce` - **Wallet** - $2,290,089 [ALREADY ANALYZED]
22. `0x283af0b28c62c092c9727f1ee09c02ca627eb7f5` - **ETHRegistrarController** - $2,135,952 [CONTROLLER]
23. `0x7693f7100a671d0cbfca63bd766fd698c17d6f04` - **Wallet** - $2,103,541 [ALREADY ANALYZED]
24. `0xd5524179cb7ae012f5b642c1d6d700bbaa76b96b` - **Delegator** - $2,084,474
25. `0x4de05b00797b11ae43e08ad0068fbd0689a0e041` - **Wallet** - $2,075,760 [ALREADY ANALYZED]
26. `0xe5a04d98538231b0fab9aba60cd73ce4ff3039df` - **EtherFlip** - $2,033,391 [ALREADY ANALYZED]
27. `0x5f3ce3907e7e4c5b5b8d04dd3211ca8b81a64733` - **Wallet** - $2,001,854 [ALREADY ANALYZED]
28. `0x8ff920020c8ad673661c8117f2855c384758c572` - **MultiSigWallet** - $1,960,943 [ALREADY ANALYZED]
29. `0x09403fd14510f8196f7879ef514827cd76960b5d` - **PerpetualProxy** - $1,885,360 [PERPS]
30. `0xc59b0e4de5f1248c1140964e0ff287b192407e0c` - **ConditionalTokens** - $1,831,561 [ALREADY ANALYZED]
31. `0x94bd4150e41c717b7e7564484693073239715376` - **Wallet** - $1,813,575 [ALREADY ANALYZED]
32. `0x58d3178fc815678aa7e700a4911837542b6b56ab` - **Wallet** - $1,804,974 [ALREADY ANALYZED]
33. `0x167cb3f2446f829eb327344b66e271d1a7efec9a` - **GandhiJi** - $1,793,277 [ABI-SIGNAL:WITHDRAW]
34. `0x227b7656129bc07eef947d3c019a7a8f36a24e74` - **Wallet** - $1,768,770 [ALREADY ANALYZED]
35. `0xfceaaaeb8d564a9d0e71ef36f027b9d162bc334e` - **CrossProxy** - $1,751,528 [PROXY]
36. `0x1ce7ae555139c5ef5a57cc8d814a867ee6ee33d8` - **TokenStore** - $1,713,769 [ALREADY ANALYZED]
37. `0x9dafec62c3ef9cf8add8532ff339b991a30f421d` - **TristersLightMinterV2** - $1,674,731 [ALREADY ANALYZED]
38. `0xb8901acb165ed027e32754e0ffe830802919727f` - **L1_ETH_Bridge** - $1,655,270 [BRIDGE]
39. `0x0397453bb7db560a039d474c5693578fdb6096c4` - **Wallet** - $1,620,000 [ALREADY ANALYZED]
40. `0xa14703b1da572e3ddf4803113eb32159209199db` - **Wallet** - $1,620,000 [ALREADY ANALYZED]
41. `0x47c663ba238fb5c66fa7ac92c33a86a41da261de` - **Wallet** - $1,603,800 [ALREADY ANALYZED]
42. `0x4f32ab778e85c4ad0cead54f8f82f5ee74d46904` - **Curve** - $1,502,212 [ALREADY ANALYZED]
43. `0xdc1664458d2f0b6090bea60a8793a4e66c2f1c00` - **L1ChugSplashProxy** - $1,472,866 [PROXY]
44. `0xd216153c06e857cd7f72665e0af1d7d82172f494` - **RelayHub** - $1,408,561 [ABI-SIGNAL:DEPOSIT]
45. `0x12d66f87a04a9e220743712ce6d9bb1b5616b8fc` - **TornadoCash_Eth_01** - $1,378,080 [ALREADY ANALYZED]
46. `0x6941627cba3518385e75de75d25a189185672bfe` - **MultiSigWallet** - $1,369,299 [ALREADY ANALYZED]
47. `0xa2201234a4652a704f5539058ccb9ab6ebcd486b` - **MultiSigWallet** - $1,355,367 [ALREADY ANALYZED]
48. `0x6e314220258a6fa41c2d50cd98f123ffff247d9e` - **Wallet** - $1,352,700 [ALREADY ANALYZED]
49. `0xdb46b29957b3021a5ea79c49f443083aba994a33` - **Wallet** - $1,350,000 [ALREADY ANALYZED]
50. `0x1426c1f91b923043f7c5fbabc6e369e7cbaef3f0` - **Wallet** - $1,349,340 [ALREADY ANALYZED]
51. `0xe1237aa7f535b0cc33fd973d66cbf830354d16c7` - **yVault** - $1,338,859 [VAULT/YIELD]
52. `0x230731528a32a11122426e7688e8d9050a484a77` - **ColdWallet** - $1,333,490
53. `0x35ffd6e268610e764ff6944d07760d0efe5e40e5` - **LiquidityPoolV2** - $1,292,967 [POOL/DEX]
54. `0x1a2a1c938ce3ec39b6d47113c7955baa9dd454f2` - **MainchainGatewayProxy** - $1,282,028 [PROXY]
55. `0x0b7dc5a43ce121b4eaaa41b0f4f43bba47bb8951` - **EtherToken** - $1,278,934 [ALREADY ANALYZED]
56. `0xac48c3712cc677d59566c37e6eb5eccccd207d1b` - **OwnbitMultiSig** - $1,227,640 [ALREADY ANALYZED]
57. `0x241e82c79452f51fbfc89fac6d912e021db1a3b7` - **Hydro** - $1,224,588 [ALREADY ANALYZED]
58. `0x367e59b559283c8506207d75b0c5d8c66c4cd4b7` - **Router** - $1,197,848 [ROUTER]
59. `0x3fda67f7583380e67ef93072294a7fac882fd7e7` - **MoneyMarket** - $1,151,849 [MARKET]
60. `0x5934807cc0654d46755ebd2848840b616256c6ef` - **MarginPool** - $1,148,686 [POOL/DEX]
61. `0xd18475521245a127a933a4fcaf99e8c45a416f7e` - **QDT** - $1,128,230 [ABI-SIGNAL:DEPOSIT]
62. `0x12ed69359919fc775bc2674860e8fe2d2b6a7b5d` - **AdminUpgradeabilityProxy** - $1,127,954 [PROXY]
63. `0x71331c46fba44d85e293d63d1d5a8cdadf264451` - **Wallet** - $1,106,096 [ALREADY ANALYZED]
64. `0x25751853eab4d0eb3652b5eb6ecb102a2789644b` - **AdminUpgradeabilityProxy** - $1,095,476 [PROXY]
65. `0xf786c34106762ab4eeb45a51b42a62470e9d5332` - **fETH** - $1,090,957 [ABI-SIGNAL:DEPOSIT]
66. `0xf9250f22e4f6ef528aec6bf1cd4cb012dd5169d4` - **Wallet** - $1,088,922 [ALREADY ANALYZED]
67. `0x22ef5434cc2deb6c760c7ebbc88777d1f32757f6` - **Wallet** - $1,080,000 [ALREADY ANALYZED]
68. `0x35bd14e205251f3ee0405bc543ceac1d776e5736` - **Wallet** - $1,080,000 [ALREADY ANALYZED]
69. `0x05cf82965cc412494c5de53bf107ec631accf03e` - **Wallet** - $1,077,300 [ALREADY ANALYZED]
70. `0x39d46c1824dfc32ad4e80c28a825296a8ac52437` - **Wallet** - $1,071,900 [ALREADY ANALYZED]
71. `0x0b7ffc1f4ad541a4ed16b40d8c37f0929158d101` - **EasyAuction** - $1,042,315 [ALREADY ANALYZED]
72. `0xa6cd930fc92f1634d8183af2fb86bd1766f2f82a` - **CelerWallet** - $1,037,287 [ALREADY ANALYZED]
73. `0x043dae09e7f51d02b8745bcf82c4c5ee86e4bc96` - **Wallet** - $972,000 [ALREADY ANALYZED]
74. `0x4d8006dc86d6015d5cb1f33c4e98ca12c39fcba2` - **Wallet** - $972,000 [ALREADY ANALYZED]
75. `0x072b4b3008eb2177cce628123d24e75a8e34b9b0` - **MultiSigWalletWithDailyLimit** - $971,349 [ALREADY ANALYZED]
76. `0xdef545eeac0bd8b55a9e9c6b461f96ddd0fdd0de` - **Wallet** - $946,077 [ALREADY ANALYZED]
77. `0xcf46cc20deba6b802707961ca3c6f3602566c2cf` - **Wallet** - $945,068 [ALREADY ANALYZED]
78. `0xe4aa399ac8c2c636c3f084f8176c01c5c73ed90e` - **Wallet** - $945,000 [ALREADY ANALYZED]
79. `0x53ea709e81eefa48a311b2a582ad8057d45d4acc` - **Wallet** - $945,000 [ALREADY ANALYZED]
80. `0x728dbf45456de6b51b1227d5cd5e2507167688c0` - **Wallet** - $945,000 [ALREADY ANALYZED]
81. `0xaba513097f04d637727fdcda0246636e0d5d6833` - **DavyJones** - $940,247 [ABI-SIGNAL:DEPOSIT]
82. `0xef5da7752c084df1cc719c64bbe06fa98b2c554c` - **Wallet** - $932,849 [ALREADY ANALYZED]
83. `0x4ebcf8a133cce749ee07d4c764e10d1916f84f5c` - **Wallet** - $925,614 [ALREADY ANALYZED]
84. `0xe705daf2f65228aade8c8ac4f60a586b1391228d` - **Wallet** - $919,080 [ALREADY ANALYZED]
85. `0xc32050abac7dbfef4fc8dc7b96d9617394cb4e1b` - **Wallet** - $918,617 [ALREADY ANALYZED]
86. `0x40ed3699c2ffe43939ecf2f3d11f633b522820ad` - **Floor** - $907,319
87. `0x160b24a430bca05262a98a07027dd2dd1802ca18` - **Wallet** - $899,127 [ALREADY ANALYZED]
88. `0x28ff414bb944b81053389f22113ad305c8ac69fa` - **Wallet** - $896,400 [ALREADY ANALYZED]
89. `0x7100c7ce94607ef68983f133cfd59cc1833a115d` - **Wallet** - $884,347 [ALREADY ANALYZED]
90. `0x94e638aef49c74cfda16272b283362e72cca91ee` - **MultiSigWallet** - $882,944 [ALREADY ANALYZED]
91. `0xa08c1134cdd73ad41889f7f914ecc4d3b30c1333` - **Wallet** - $878,040 [ALREADY ANALYZED]
92. `0x2f9f02f2ba99ff5c750f95cf27d25352f71cd6a9` - **Wallet** - $864,003 [ALREADY ANALYZED]
93. `0xe5c405c5578d84c5231d3a9a29ef4374423fa0c2` - **Custodian** - $860,867 [ABI-SIGNAL:WITHDRAW]
94. `0x4a14347083b80e5216ca31350a2d21702ac3650d` - **AMMWrapperWithPath** - $852,346 [ALREADY ANALYZED]
95. `0x7b4a7fd41c688a7cb116534e341e44126ef5a0fd` - **CEther** - $847,020 [ABI-SIGNAL:BORROW]
96. `0x6f400810b62df8e13fded51be75ff5393eaa841f` - **BatchExchange** - $794,477 [DEX]
97. `0xf74bf048138a2b8f825eccabed9e02e481a0f6c0` - **AdminUpgradeabilityProxy** - $787,614 [PROXY]
98. `0xe9778e69a961e64d3cdbb34cf6778281d34667c2` - **WorkLock** - $786,209 [ABI-SIGNAL:DEPOSIT]
99. `0x83d0d842e6db3b020f384a2af11bd14787bec8e7` - **GuildBank** - $775,764 [ALREADY ANALYZED]
100. `0x0f30c808069315b3b7dfbfe149c87448b50c6d8b` - **Wallet** - $771,506 [ALREADY ANALYZED]
101. `0x7e5b6dd9ba1abf42bfb41e5ae8f46fe5e01aae14` - **Wallet** - $769,544 [ALREADY ANALYZED]
102. `0xd3d13a578a53685b4ac36a1bab31912d2b2a2f36` - **TransparentUpgradeableProxy** - $768,172 [PROXY]
103. `0x3a3fba79302144f06f49ffde69ce4b7f6ad4dd3d` - **SuperBunnies** - $767,497
104. `0xd48b633045af65ff636f3c6edd744748351e020d` - **Zethr** - $758,288 [ABI-SIGNAL:WITHDRAW]
105. `0x6fb8aa6fc6f27e591423009194529ae126660027` - **DerivaDEX** - $706,154
106. `0xa7d9e842efb252389d613da88eda3731512e40bd` - **BondedECDSAKeepFactory** - $698,104 [ABI-SIGNAL:STAKE]
107. `0xe5859f4efc09027a9b718781dcb2c6910cac6e91` - **Root** - $668,732
108. `0x24f0bb6c9b2c3db66603fa0ec07ab0cf55cdd387` - **Holder** - $668,037
109. `0x60cd862c9c687a9de49aecdc3a99b74a4fc54ab6` - **MoonCatRescue** - $666,065 [ABI-SIGNAL:WITHDRAW]
110. `0x8d90113a1e286a5ab3e496fbd1853f265e5913c6` - **PMM** - $634,446 [ALREADY ANALYZED]
111. `0x27321f84704a599ab740281e285cc4463d89a3d5` - **KeepBonding** - $632,930 [ABI-SIGNAL:DEPOSIT]
112. `0x2e8a97c62cc644adcd108b9bebcb9b32c9c58a1c` - **EternalStorageProxy** - $614,747 [PROXY]
113. `0x4aea7cf559f67cedcad07e12ae6bc00f07e8cf65` - **EtherDelta** - $596,996 [ALREADY ANALYZED]
114. `0x5eee354e36ac51e9d3f7283005cab0c55f423b23` - **ArbitrageETHStaking** - $583,981 [STAKING]
115. `0x8754f54074400ce745a7ceddc928fb1b7e985ed6` - **EulerBeats** - $580,981 [ABI-SIGNAL:WITHDRAW]
116. `0x97ec9bfb0f6672c358620615a1e4de0348aea05c` - **InsightsNetworkContributions** - $563,342
117. `0x899f9a0440face1397a1ee1e3f6bf3580a6633d1` - **RedemptionContract** - $556,885 [ABI-SIGNAL:DEPOSIT]
118. `0xbd3af18e0b7ebb30d49b253ab00788b92604552c` - **HashesDAO** - $556,396
119. `0x05276c19f670ffe7ba6b3bdc94e70c36b4b9dad5` - **Wallet** - $545,731 [ALREADY ANALYZED]
120. `0xd619c8da0a58b63be7fa69b4cc648916fe95fa1b` - **CycloneV2dot2** - $540,000 [ABI-SIGNAL:DEPOSIT]
121. `0xb9fbe1315824a466d05df4882ffac592ce9c009a` - **InstantListingV2** - $540,000
122. `0x3666f603cc164936c1b87e207f36beba4ac5f18a` - **L1_ERC20_Bridge** - $538,298
123. `0x9149c59f087e891b659481ed665768a57247c79e` - **KyberReserve** - $531,769 [ABI-SIGNAL:DEPOSIT]
124. `0x7488451db91df618759b8af15e36f70c0fdd529e` - **XifraICO2** - $522,740 [ABI-SIGNAL:WITHDRAW]
125. `0x575cb87ab3c2329a0248c7d70e0ead8e57f3e3f7` - **AhooleeTokenSale** - $517,076 [ALREADY ANALYZED]
126. `0x112918a54e3ada863cf694970da0756f1eecc68d` - **JavvyMultiSig** - $515,426 [ALREADY ANALYZED]
127. `0xcd18eaa163733da39c232722cbc4e8940b1d8888` - **Sablier** - $476,650 [ABI-SIGNAL:DEPOSIT]
128. `0x2468160c241a9fed936ee1e3ceb8b2f7e2e01987` - **Wallet** - $475,200 [ALREADY ANALYZED]
129. `0xf8f12fe1b51d1398019c4facd4d00adab5fef746` - **TeleportCustody** - $474,515
130. `0x7cd5e2d0056a7a7f09cbb86e540ef4f6dccc97dd` - **xSNXAdminProxy** - $473,870 [PROXY]
131. `0x2956356cd2a2bf3202f771f50d3d14a367b48070` - **EtherToken** - $473,292 [ALREADY ANALYZED]
132. `0xe470198cda121da5b6ad349d3577b166e5985917` - **EternalStorageProxy** - $458,893 [PROXY]
133. `0x7600977eb9effa627d6bd0da2e5be35e11566341` - **Dex2** - $447,652 [ALREADY ANALYZED]
134. `0x0f69f08f872f366ad8edde03dae8812619a17536` - **CErc20** - $446,813
135. `0x6467e807db1e71b9ef04e0e3afb962e4b0900b2b` - **FeeReceiver** - $440,931 [ABI-SIGNAL:WITHDRAW]
136. `0x63658cc84a5b2b969b8df9bea129a1c933e1439f` - **kleee002** - $434,439
137. `0x33c0d33a0d4312562ad622f91d12b0ac47366ee1` - **AdminUpgradeabilityProxy** - $420,524 [PROXY]
138. `0xd95a6aa3e20397211e487b231211e16790a21ac9` - **Wallet** - $406,295 [ALREADY ANALYZED]
139. `0xc7c9b856d33651cc2bcd9e0099efa85f59f78302` - **R1Exchange** - $405,979 [ALREADY ANALYZED]
140. `0xc88f47067db2e25851317a2fdae73a22c0777c37` - **oneBTC** - $402,170 [ABI-SIGNAL:DEPOSIT]
141. `0xa38b6742cef9573f7f97c387278fa31482539c3d` - **CycloneV2dot3** - $402,160 [ABI-SIGNAL:DEPOSIT]
142. `0x1180c114f7fadcb6957670432a3cf8ef08ab5354` - **TransparentUpgradeableProxy** - $401,696 [PROXY]
143. `0x256c8919ce1ab0e33974cf6aa9c71561ef3017b6` - **BridgePoolProd** - $400,335 [POOL/DEX]
144. `0xacd43e627e64355f1861cec6d3a6688b31a6f952` - **yVault** - $398,944 [VAULT/YIELD]
145. `0x7b6bce3cf38ee602030662fa24ac2ed5a32d0a02` - **Wallet** - $395,411 [ALREADY ANALYZED]
146. `0x587a07ce5c265a38dd6d42def1566ba73eeb06f5` - **YAMETHPool** - $393,484 [POOL/DEX]
147. `0x4547a86ca6a84b9d60dc57af908472074de7af5f` - **PASTAPool** - $391,429 [POOL/DEX]
148. `0xd64b1bf6fcab5add75041c89f61816c2b3d5e711` - **OrbsGuardians** - $388,800 [ABI-SIGNAL:DEPOSIT]
149. `0x04bda0cf6ad025948af830e75228ed420b0e860d` - **TransparentUpgradeableProxy** - $386,201 [PROXY]
150. `0x4570b4faf71e23942b8b9f934b47ccedf7540162` - **Moloch** - $384,197 [ABI-SIGNAL:DEPOSIT]
151. `0x57a8865cfb1ecef7253c27da6b4bc3daee5be518` - **Timelock** - $379,020 [ALREADY ANALYZED]
152. `0x6a39909e805a3eadd2b61fff61147796ca6abb47` - **UpgradeBeaconProxy** - $378,018 [PROXY]
153. `0x20018893c7d8e38b14a10a00c70023c45d528fba` - **Wallet** - $369,873 [ALREADY ANALYZED]
154. `0x0ad3227eb47597b566ec138b3afd78cfea752de5` - **FoMo3Dshort** - $369,268 [ABI-SIGNAL:DEPOSIT]
155. `0x62ca869bafea0c77234e48018d9c67f7c0cd197a` - **Wallet** - $365,375 [ALREADY ANALYZED]
156. `0xe5bfab544eca83849c53464f85b7164375bdaac1` - **Market** - $362,896 [MARKET]
157. `0x6e5e0ef477db8e26cd64f87522a1997f6dda64fb` - **Wallet** - $356,425 [ALREADY ANALYZED]
158. `0xa150de0e6998e05d6e19fca736ab758e698da21a` - **Wallet** - $351,864 [ALREADY ANALYZED]
159. `0x38b78904a6b44f63eb81d98937fc6614870cfbb9` - **MultiSigWalletWithDailyLimit** - $348,832 [ALREADY ANALYZED]
160. `0x6f35a5e6a7301627a090822895e5e7209ed72f77` - **SavingAccount** - $348,813 [ALREADY ANALYZED]
161. `0x9b4ea303ca6302dfa46b73bc660598c65de96b3d` - **auto_pool** - $347,576 [POOL/DEX]
162. `0x88ae96845e157558ef59e9ff90e766e22e480390` - **Klein** - $346,953
163. `0x373c55c277b866a69dc047cad488154ab9759466` - **EtherDelta** - $333,071 [ALREADY ANALYZED]
164. `0x773a58c0ae122f56d6747bc1264f00174b3144c3` - **KyberReserve** - $324,097 [ABI-SIGNAL:DEPOSIT]
165. `0x67e0eb8557437ab7393243c88a11f3c7e424ca3d` - **wethMerkleDistributor** - $323,894 [DISTRIBUTOR]
166. `0x8fb1a35bb6fb9c47fb5065be5062cb8dc1687669` - **TransparentUpgradeableProxy** - $315,660 [PROXY]
167. `0xd8ee69652e4e4838f2531732a46d1f7f584f0b7f` - **bZxProtocol** - $309,755 [ABI-SIGNAL:DEPOSIT]
168. `0x1a26ef6575b7bbb864d984d9255c069f6c361a14` - **Proxy__L1LiquidityPoolArguments** - $307,738 [POOL/DEX]
169. `0xb9812e2fa995ec53b5b6df34d21f9304762c5497` - **DutchExchangeProxy** - $307,265 [ALREADY ANALYZED]
170. `0xb9ab8eed48852de901c13543042204c6c569b811` - **Zethr** - $306,481 [ABI-SIGNAL:WITHDRAW]
171. `0x05fbd3b849a87c9608a2252d095d8cb818d0d239` - **TokenICBX** - $300,000 [ABI-SIGNAL:WITHDRAW]
172. `0x6822aaf4ab22e6cca8352a927b9ae0a8fdb58d9d` - **ProfitSharing** - $299,772 [ABI-SIGNAL:DEPOSIT]
173. `0x7ea1950d7fa5167d5dc92c26e537d7875553b88e` - **Wallet** - $296,898 [ALREADY ANALYZED]
174. `0xa365c183dd416f3eedf91fbda6bef30bd8d596c5` - **Wallet** - $296,588 [ALREADY ANALYZED]
175. `0xd2bfceeab8ffa24cdf94faa2683df63df4bcbdc8` - **DailyDivs** - $296,407 [ABI-SIGNAL:WITHDRAW]
176. `0x0514afd47f635e9304028bd0dcdaed2168773ec1` - **Wallet** - $295,771 [ALREADY ANALYZED]
177. `0xa33c4a314faa9684eeffa6ba334688001ea99bbc` - **Phoenix** - $293,707 [ABI-SIGNAL:DEPOSIT]
178. `0xc1bd4f07421571364617adce98a8d657f52498b7` - **Wallet** - $292,860 [ALREADY ANALYZED]
179. `0x728781e75735dc0962df3a51d7ef47e798a7107e` - **WolkExchange** - $289,643 [DEX]
180. `0xe40e1531a4b56fb65571ad2ca43dc0048a316a2d` - **EthPrime** - $288,592 [ALREADY ANALYZED]
181. `0xb1cff81b9305166ff1efc49a129ad2afcd7bcf19` - **Vault** - $286,485 [ALREADY ANALYZED]
182. `0xe14ab3ee81abe340b45bb26b1b166a7d2df22585` - **TweetMarket** - $285,620 [MARKET]
183. `0xe01e2a3ceafa8233021fc759e5a69863558326b6` - **EKS** - $284,831 [ABI-SIGNAL:DEPOSIT]
184. `0xa45b966996374e9e65ab991c6fe4bfce3a56dde8` - **MaticWETH** - $282,791 [ABI-SIGNAL:DEPOSIT]
185. `0xaec2e87e0a235266d9c5adc9deb4b2e29b54d009` - **SingularDTVToken** - $281,957
186. `0xc8c1b41713761281a520b7ad81544197bc85a4ce` - **ETHBurgerTransit** - $281,307 [ABI-SIGNAL:WITHDRAW]
187. `0x04ab1ae22add9b0d991aca80a0eb74de14fd2a8d` - **Wallet** - $278,643 [ALREADY ANALYZED]
188. `0xb8ff313d33b0e841b6b83243f6e2935166de87c1` - **AdminUpgradeabilityProxy** - $272,780 [PROXY]
189. `0xab5cffaaec03efc94ab5c0c4c0bc85ae2b2b65ac` - **EtherkingJackpot** - $272,700 [ABI-SIGNAL:DEPOSIT]
190. `0x0d6630648e6740d2d96c562543d4e0c7bbb46577` - **Wallet** - $272,616 [ALREADY ANALYZED]
191. `0x228b015ab09c32906e4b98cfc2761b96842d8724` - **Wallet** - $272,321 [ALREADY ANALYZED]
192. `0x9aca6abfe63a5ae0dc6258cefb65207ec990aa4d` - **DigiPulse** - $271,575 [ABI-SIGNAL:WITHDRAW]
193. `0x73f09b50960f87af26ff4817a93c0f5efd0aa9e2` - **DualSig** - $270,675
194. `0x9122e2cfab13d30237ebeef0c0521d64bf0b06dc` - **cEthereumlotteryNet** - $270,027
195. `0x1fd169a4f5c59acf79d0fd5d91d1201ef1bce9f1` - **Moloch** - $270,000 [ABI-SIGNAL:DEPOSIT]
196. `0x3e4a3a4796d16c0cd582c382691998f7c06420b6` - **L1_ERC20_Bridge** - $266,664
197. `0x25a06d4e1f804ce62cf11b091180a5c84980d93a` - **Treasure** - $265,356 [ABI-SIGNAL:WITHDRAW]
198. `0x6fcbbb527fb2954bed2b224a5bb7c23c5aeeb6e1` - **oneETH** - $261,259 [ABI-SIGNAL:DEPOSIT]
199. `0x59f54eed3e1ea731adbfb0e417490f9b50e31b10` - **EternalStorageProxy** - $261,243 [PROXY]
200. `0x0fabaf48bbf864a3947bdd0ba9d764791a60467a` - **AdminUpgradeabilityProxy** - $260,202 [PROXY]
201. `0xe65f525ec48c7e95654b9824ecc358454ea9185e` - **AceDapp** - $258,690 [ALREADY ANALYZED]
