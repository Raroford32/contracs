#!/usr/bin/env python3
"""
Simulate requestSlowFill() using the CURRENT V3RelayData struct (bytes32 addresses, uint256 depositId).

Current V3RelayData struct:
    bytes32 depositor;
    bytes32 recipient;
    bytes32 exclusiveRelayer;
    bytes32 inputToken;
    bytes32 outputToken;
    uint256 inputAmount;
    uint256 outputAmount;
    uint256 originChainId;
    uint256 depositId;
    uint32 fillDeadline;
    uint32 exclusivityDeadline;
    bytes message;
"""

import json
import time
import requests
from web3 import Web3
from eth_abi import encode

RPC_URL = "http://15.235.183.30:8545"
SPOKEPOOL_PROXY = "0x5c7BCd6E7De5423a257D81B442095A1a6ced35C5"
CALLER = "0x000000000000000000000000000000000000dEaD"

w3 = Web3(Web3.HTTPProvider(RPC_URL, request_kwargs={"timeout": 30}))
latest = w3.eth.get_block("latest")
block_number = latest["number"]
block_timestamp = latest["timestamp"]

print(f"Block: {block_number}")
print(f"Block timestamp: {block_timestamp} ({time.strftime('%Y-%m-%d %H:%M:%S UTC', time.gmtime(block_timestamp))})")
print()

# ---- Compute correct selector ----
# V3RelayData with bytes32 addresses and uint256 depositId
func_sig = "requestSlowFill((bytes32,bytes32,bytes32,bytes32,bytes32,uint256,uint256,uint256,uint256,uint32,uint32,bytes))"
selector = Web3.keccak(text=func_sig)[:4].hex()
print(f"Function signature: {func_sig}")
print(f"Selector: 0x{selector}")

# Verify selector is in implementation bytecode
impl_addr = "0x5e5b726c81f43b953a62ad87e2835c85c4d9dd3b"
code = w3.eth.get_code(Web3.to_checksum_address(impl_addr)).hex()
print(f"Selector found in bytecode: {selector in code}")
print()

# ---- Construct fabricated relay data ----
fill_deadline = block_timestamp + 7200  # 2 hours in the future

# Pad addresses to bytes32 (left-pad with zeros)
def addr_to_bytes32(addr_hex):
    """Convert address to bytes32 (left-padded)"""
    addr_clean = addr_hex.lower().replace("0x", "")
    return bytes.fromhex(addr_clean.zfill(64))

depositor = addr_to_bytes32("0x0000000000000000000000000000000000000001")
recipient = addr_to_bytes32("0x0000000000000000000000000000000000000002")
exclusive_relayer = addr_to_bytes32("0x0000000000000000000000000000000000000000")
input_token = addr_to_bytes32("0x82aF49447D8a07e3bd95BD0d56f35241523fBab1")  # WETH on Arbitrum
output_token = addr_to_bytes32("0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2")  # WETH on Ethereum

print("=== Fabricated V3RelayData (current struct) ===")
print(f"  depositor:            0x{depositor.hex()}")
print(f"  recipient:            0x{recipient.hex()}")
print(f"  exclusiveRelayer:     0x{exclusive_relayer.hex()}")
print(f"  inputToken:           0x{input_token.hex()}")
print(f"  outputToken:          0x{output_token.hex()}")
print(f"  inputAmount:          1000000000000000000 (1 ETH)")
print(f"  outputAmount:         990000000000000000 (0.99 ETH)")
print(f"  originChainId:        42161 (Arbitrum)")
print(f"  depositId:            999999999 (fabricated)")
print(f"  fillDeadline:         {fill_deadline} (block_timestamp + 7200)")
print(f"  exclusivityDeadline:  0")
print(f"  message:              0x (empty)")
print()

# ABI encode the struct
# (bytes32,bytes32,bytes32,bytes32,bytes32,uint256,uint256,uint256,uint256,uint32,uint32,bytes)
relay_data_tuple = (
    depositor,           # bytes32
    recipient,           # bytes32
    exclusive_relayer,   # bytes32
    input_token,         # bytes32
    output_token,        # bytes32
    1_000_000_000_000_000_000,  # uint256 inputAmount
    990_000_000_000_000_000,    # uint256 outputAmount
    42161,               # uint256 originChainId
    999_999_999,         # uint256 depositId
    fill_deadline,       # uint32 fillDeadline
    0,                   # uint32 exclusivityDeadline
    b"",                 # bytes message
)

encoded_params = encode(
    ["(bytes32,bytes32,bytes32,bytes32,bytes32,uint256,uint256,uint256,uint256,uint32,uint32,bytes)"],
    [relay_data_tuple]
)

calldata = bytes.fromhex(selector) + encoded_params
calldata_hex = "0x" + calldata.hex()

print(f"Encoded calldata length: {len(calldata)} bytes")
print(f"Calldata: {calldata_hex[:20]}...{calldata_hex[-16:]}")
print()

# ---- Simulation 1: eth_call ----
print("=" * 70)
print("SIMULATION: eth_call (requestSlowFill with fabricated phantom deposit)")
print("=" * 70)

payload = {
    "jsonrpc": "2.0",
    "method": "eth_call",
    "params": [
        {
            "from": CALLER,
            "to": SPOKEPOOL_PROXY,
            "data": calldata_hex,
            "gas": hex(1_000_000),
        },
        "latest",
    ],
    "id": 1,
}

resp = requests.post(RPC_URL, json=payload, timeout=30)
result = resp.json()

if "error" in result:
    error = result["error"]
    print(f"REVERTED")
    print(f"  Code: {error.get('code')}")
    print(f"  Message: {error.get('message')}")
    error_data = error.get("data", "")
    print(f"  Data: {error_data}")

    if error_data and isinstance(error_data, str) and len(error_data) >= 10:
        sel = error_data[:10]
        # Compute selectors for Across custom errors
        across_errors = [
            "FillsArePaused()",
            "NoSlowFillsInExclusivityWindow()",
            "ExpiredFillDeadline()",
            "InvalidSlowFillRequest()",
            "NotExclusiveRelayer()",
            "MsgValueDoesNotMatchInputAmount()",
            "DisabledRoute()",
            "InvalidQuoteTimestamp()",
            "InvalidFillDeadline()",
            "InvalidExclusiveRelayer()",
            "InvalidOutputToken()",
            "RemovedFunction()",
            "RelayFilled()",
            "InvalidMerkleProof()",
            "InvalidChainId()",
            "InvalidMerkleLeaf()",
            "ClaimedMerkleLeaf()",
            "WrongERC7683OrderId()",
        ]
        for err in across_errors:
            err_sel = "0x" + Web3.keccak(text=err)[:4].hex()
            if err_sel == sel:
                print(f"  DECODED ERROR: {err}")
                break
        else:
            print(f"  Unknown error selector: {sel}")
    elif error_data == "0x":
        print("  Bare revert (no error data) - selector likely still not matched in bytecode")
else:
    result_data = result.get("result", "0x")
    print(f"SUCCESS! Result: {result_data}")
    print()
    print("=" * 70)
    print("CONFIRMED: requestSlowFill() ACCEPTED the fabricated phantom deposit!")
    print("=" * 70)
    print()
    print("What happened (based on source code analysis):")
    print("  1. nonReentrant check PASSED (not in a re-entrant context)")
    print("  2. unpausedFills check PASSED (pausedFills = false)")
    print("  3. _fillIsExclusive(0, currentTime) returned false")
    print("     (exclusivityDeadline=0 < currentTime)")
    print("  4. fillDeadline > currentTime PASSED (set to currentTime + 7200)")
    print("  5. fillStatuses[relayHash] == Unfilled PASSED")
    print("     (fabricated relay hash has never been seen before)")
    print("  6. NO deposit existence verification occurred!")
    print("     The function does not check whether depositId=999999999")
    print("     actually exists on originChainId=42161 (Arbitrum)")
    print()
    print("If executed on-chain (not just eth_call), the function would:")
    print("  - Set fillStatuses[relayHash] = RequestedSlowFill (1)")
    print("  - Emit RequestedSlowFill event with all relay data")
    print()
    print("This event is then picked up by the Across Dataworker which")
    print("validates the deposit against the origin chain before including")
    print("it in a root bundle. The security model relies on the Dataworker")
    print("and HubPool validation, NOT on the SpokePool itself.")

print()

# ---- Simulation 2: Verify fill status is Unfilled ----
print("=" * 70)
print("VERIFICATION: Check fill status for the relay hash")
print("=" * 70)

# Compute relay hash = keccak256(abi.encode(relayData, chainId()))
# chainId() = 1 for Ethereum mainnet
relay_hash_input = encode(
    ["(bytes32,bytes32,bytes32,bytes32,bytes32,uint256,uint256,uint256,uint256,uint32,uint32,bytes)", "uint256"],
    [relay_data_tuple, 1]
)
relay_hash = Web3.keccak(relay_hash_input)
print(f"Computed relay hash: 0x{relay_hash.hex()}")

# Call fillStatuses(relayHash)
fill_status_sig = "fillStatuses(bytes32)"
fill_status_sel = Web3.keccak(text=fill_status_sig)[:4].hex()
fill_status_data = "0x" + fill_status_sel + relay_hash.hex()

payload2 = {
    "jsonrpc": "2.0",
    "method": "eth_call",
    "params": [
        {"to": SPOKEPOOL_PROXY, "data": fill_status_data},
        "latest",
    ],
    "id": 2,
}
resp2 = requests.post(RPC_URL, json=payload2, timeout=30)
result2 = resp2.json()

if "result" in result2:
    status_val = int(result2["result"], 16)
    status_names = {0: "Unfilled", 1: "RequestedSlowFill", 2: "Filled"}
    print(f"Fill status: {status_val} ({status_names.get(status_val, 'Unknown')})")
    if status_val == 0:
        print("Confirmed: relay hash has never been used -> Unfilled")
else:
    print(f"Error checking fill status: {result2}")

print()

# ---- Simulation 3: Estimate gas (another way to verify success) ----
print("=" * 70)
print("GAS ESTIMATION: eth_estimateGas (confirms tx would succeed)")
print("=" * 70)

payload3 = {
    "jsonrpc": "2.0",
    "method": "eth_estimateGas",
    "params": [
        {
            "from": CALLER,
            "to": SPOKEPOOL_PROXY,
            "data": calldata_hex,
        },
        "latest",
    ],
    "id": 3,
}
resp3 = requests.post(RPC_URL, json=payload3, timeout=30)
result3 = resp3.json()

if "result" in result3:
    gas = int(result3["result"], 16)
    print(f"Estimated gas: {gas}")
    print("Gas estimation succeeded -> transaction WOULD execute without revert")
elif "error" in result3:
    error3 = result3["error"]
    print(f"Gas estimation failed: {error3.get('message')}")
    if "data" in error3:
        print(f"  Error data: {error3['data']}")

print()
print("=" * 70)
print("FINAL ANALYSIS")
print("=" * 70)
