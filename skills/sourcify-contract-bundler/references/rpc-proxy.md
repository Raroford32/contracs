# RPC proxy resolution (EIP-1967)

Use JSON-RPC to detect implementation and beacon addresses when Explorer/Sourcify data is missing.

EIP-1967 slots (bytes32 hex):
- Implementation slot: 0x360894a13ba1a3210667c828492db98dca3e2076cc3735a920a3ca505d382bbc
- Beacon slot:        0xa3f0ad74e5423aebfd80d3ef4346578335a9a72aeaee59ff6cb3582b35133d50

RPC methods:
- `eth_getStorageAt` to read slots for implementation/beacon addresses.
- `eth_call` to call `implementation()` on the beacon (selector: 0x5c60da1b).

Behavior:
- If the implementation slot is non-zero, treat it as the implementation address.
- If the beacon slot is non-zero, call `implementation()` on the beacon to resolve.
- Always normalize zero/empty values and avoid re-adding already visited addresses.
