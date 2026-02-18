# Token Semantics — Curve Tricrypto2

## USDT (0xdac17f958d2ee523a2206206994597c13d831ec7)
- Decimals: 6
- Fee-on-transfer: NO (currently, but has fee mechanism that is set to 0)
- Rebasing: NO
- ERC777 hooks: NO
- Nonstandard return values: YES — transfer/approve return void (not bool)
- Pausable/Blacklist: YES — has pause and blacklist functionality
- Upgradeable: YES — proxy contract
- Protocol assumption: Pool uses raw_call for token transfers (handles void return)

## WBTC (0x2260fac5e5542a773aa44fbcfedf7c193bc2c599)
- Decimals: 8
- Fee-on-transfer: NO
- Rebasing: NO
- ERC777 hooks: NO
- Nonstandard return values: NO — standard bool returns
- Pausable/Blacklist: NO
- Upgradeable: NO
- Protocol assumption: Standard ERC20 behavior

## WETH (0xc02aaa39b223fe8d0a0e5c4f27ead9083c756cc2)
- Decimals: 18
- Fee-on-transfer: NO
- Rebasing: NO
- ERC777 hooks: NO
- Nonstandard return values: NO — standard bool returns
- Pausable/Blacklist: NO
- Upgradeable: NO
- Protocol assumption: Standard ERC20 behavior

## LP Token (0xc4AD29ba4B3c580e6D59105FFf484999997675Ff)
- Decimals: 18
- Minter: Pool contract (only minter can mint/burn)
- Standard ERC20 with restricted mint/burn
