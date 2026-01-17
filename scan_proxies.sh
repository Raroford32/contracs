#!/bin/bash
RPC="https://mainnet.infura.io/v3/bfc7283659224dd6b5124ebbc2b14e2c"
IMPL_SLOT="0x360894a13ba1a3210667c828492db98dca3e2076cc3735a920a3ca505d382bbc"

echo "=== SCANNING FOR EIP-1967 PROXIES ===" 

while read addr; do
  impl=$(/root/.foundry/bin/cast storage $addr $IMPL_SLOT --rpc-url $RPC 2>/dev/null)
  if [ -n "$impl" ] && [ "$impl" != "0x0000000000000000000000000000000000000000000000000000000000000000" ]; then
    impl_addr=$(echo $impl | sed 's/0x000000000000000000000000/0x/')
    echo ""
    echo "PROXY: $addr"
    echo "IMPL:  $impl_addr"
    
    # Check if implementation has owner
    owner=$(/root/.foundry/bin/cast call $impl_addr "owner()(address)" --rpc-url $RPC 2>/dev/null)
    if [ -n "$owner" ]; then
      echo "OWNER: $owner"
      if [ "$owner" = "0x0000000000000000000000000000000000000000" ]; then
        echo "!!! POSSIBLE UNINITIALIZED !!!"
      fi
    fi
    
    # Check balance on proxy
    bal=$(/root/.foundry/bin/cast balance $addr --rpc-url $RPC 2>/dev/null)
    if [ -n "$bal" ] && [ "$bal" != "0" ]; then
      eth_bal=$(echo "scale=4; $bal / 1000000000000000000" | bc 2>/dev/null)
      echo "ETH:   $eth_bal"
    fi
  fi
done < contracts.txt
