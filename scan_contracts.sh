#!/bin/bash
# Scan contracts for high-value targets

CAST=~/.foundry/bin/cast
RPC="https://mainnet.infura.io/v3/bfc7283659224dd6b5124ebbc2b14e2c"

WETH="0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2"
USDC="0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48"

# Read contracts from file
echo "Scanning contracts for high value..."

while read -r addr; do
    # Skip empty lines
    [ -z "$addr" ] && continue

    # Get ETH balance
    eth_bal=$($CAST balance $addr --rpc-url $RPC 2>/dev/null)

    # Convert to ETH
    eth_wei=$(echo $eth_bal | sed 's/[^0-9]//g')

    if [ ! -z "$eth_wei" ] && [ "$eth_wei" -gt "100000000000000000000" ] 2>/dev/null; then
        eth_amount=$(echo "scale=2; $eth_wei / 1000000000000000000" | bc 2>/dev/null)
        echo "HIGH VALUE: $addr - $eth_amount ETH"

        # Check contract code
        code=$($CAST code $addr --rpc-url $RPC 2>/dev/null)
        if [ ! -z "$code" ] && [ "$code" != "0x" ]; then
            echo "  Has contract code"

            # Try owner()
            owner=$($CAST call $addr "owner()(address)" --rpc-url $RPC 2>/dev/null)
            [ ! -z "$owner" ] && echo "  Owner: $owner"

            # Try totalSupply()
            supply=$($CAST call $addr "totalSupply()(uint256)" --rpc-url $RPC 2>/dev/null)
            [ ! -z "$supply" ] && echo "  TotalSupply: $supply"
        fi
    fi
done < contracts.txt
