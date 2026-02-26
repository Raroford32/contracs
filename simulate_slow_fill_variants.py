#!/usr/bin/env python3
"""
Test multiple fabricated requestSlowFill variants to confirm no validation exists.
"""

import time
import requests
from web3 import Web3
from eth_abi import encode

RPC_URL = "http://15.235.183.30:8545"
SPOKEPOOL_PROXY = "0x5c7BCd6E7De5423a257D81B442095A1a6ced35C5"
CALLER = "0x000000000000000000000000000000000000dEaD"

w3 = Web3(Web3.HTTPProvider(RPC_URL, request_kwargs={"timeout": 30}))
latest = w3.eth.get_block("latest")
block_timestamp = latest["timestamp"]
block_number = latest["number"]

func_sig = "requestSlowFill((bytes32,bytes32,bytes32,bytes32,bytes32,uint256,uint256,uint256,uint256,uint32,uint32,bytes))"
selector = Web3.keccak(text=func_sig)[:4].hex()

def addr_to_bytes32(addr_hex):
    addr_clean = addr_hex.lower().replace("0x", "")
    return bytes.fromhex(addr_clean.zfill(64))

def simulate(label, relay_data_tuple):
    encoded_params = encode(
        ["(bytes32,bytes32,bytes32,bytes32,bytes32,uint256,uint256,uint256,uint256,uint32,uint32,bytes)"],
        [relay_data_tuple]
    )
    calldata_hex = "0x" + selector + encoded_params.hex()

    payload = {
        "jsonrpc": "2.0",
        "method": "eth_call",
        "params": [
            {"from": CALLER, "to": SPOKEPOOL_PROXY, "data": calldata_hex, "gas": hex(1_000_000)},
            "latest",
        ],
        "id": 1,
    }
    resp = requests.post(RPC_URL, json=payload, timeout=30)
    result = resp.json()

    if "error" in result:
        error = result["error"]
        error_data = error.get("data", "")
        reason = error.get("message", "unknown")

        if error_data and isinstance(error_data, str) and len(error_data) >= 10:
            sel = error_data[:10]
            across_errors = [
                "FillsArePaused()", "NoSlowFillsInExclusivityWindow()",
                "ExpiredFillDeadline()", "InvalidSlowFillRequest()",
                "NotExclusiveRelayer()", "RemovedFunction()",
                "InvalidOutputToken()", "DisabledRoute()",
            ]
            for err in across_errors:
                err_sel = "0x" + Web3.keccak(text=err)[:4].hex()
                if err_sel == sel:
                    reason = err
                    break
            else:
                reason = f"selector={sel}"

        print(f"  [{label}] REVERTED: {reason}")
        return False
    else:
        print(f"  [{label}] SUCCESS (accepted)")
        return True

fill_deadline = block_timestamp + 7200
ZERO32 = b'\x00' * 32
WETH_ARB = addr_to_bytes32("0x82aF49447D8a07e3bd95BD0d56f35241523fBab1")
WETH_ETH = addr_to_bytes32("0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2")
USDC_ETH = addr_to_bytes32("0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48")

print(f"Block: {block_number}, Timestamp: {block_timestamp}")
print(f"Fill deadline: {fill_deadline}")
print()
print("=" * 70)
print("VARIANT TESTS: requestSlowFill with various fabricated parameters")
print("=" * 70)
print()

# Variant 1: Base case (1 ETH)
print("--- Variant 1: Base case (1 ETH, Arbitrum origin, fabricated depositId) ---")
simulate("1 ETH", (
    addr_to_bytes32("0x0000000000000000000000000000000000000001"),
    addr_to_bytes32("0x0000000000000000000000000000000000000002"),
    ZERO32, WETH_ARB, WETH_ETH,
    1_000_000_000_000_000_000, 990_000_000_000_000_000,
    42161, 999_999_999, fill_deadline, 0, b""
))

# Variant 2: Massive amount (10,000 ETH)
print("--- Variant 2: Massive amount (10,000 ETH) ---")
simulate("10k ETH", (
    addr_to_bytes32("0x0000000000000000000000000000000000000001"),
    addr_to_bytes32("0x0000000000000000000000000000000000000002"),
    ZERO32, WETH_ARB, WETH_ETH,
    10_000 * 10**18, 9_900 * 10**18,
    42161, 888_888_888, fill_deadline, 0, b""
))

# Variant 3: Different origin chain (made up chainId)
print("--- Variant 3: Fake origin chain (chainId=99999) ---")
simulate("fake chain", (
    addr_to_bytes32("0x0000000000000000000000000000000000000001"),
    addr_to_bytes32("0x0000000000000000000000000000000000000002"),
    ZERO32, WETH_ARB, WETH_ETH,
    1_000_000_000_000_000_000, 990_000_000_000_000_000,
    99999, 777_777_777, fill_deadline, 0, b""
))

# Variant 4: Output token = USDC (different from input)
print("--- Variant 4: Cross-token (WETH in, USDC out) ---")
simulate("cross-token", (
    addr_to_bytes32("0x0000000000000000000000000000000000000001"),
    addr_to_bytes32("0x0000000000000000000000000000000000000002"),
    ZERO32, WETH_ARB, USDC_ETH,
    1_000_000_000_000_000_000, 2_500_000_000,  # 2500 USDC
    42161, 666_666_666, fill_deadline, 0, b""
))

# Variant 5: With a non-empty message (arbitrary calldata)
print("--- Variant 5: With arbitrary message bytes ---")
simulate("with msg", (
    addr_to_bytes32("0x0000000000000000000000000000000000000001"),
    addr_to_bytes32("0x0000000000000000000000000000000000000002"),
    ZERO32, WETH_ARB, WETH_ETH,
    1_000_000_000_000_000_000, 990_000_000_000_000_000,
    42161, 555_555_555, fill_deadline, 0,
    bytes.fromhex("deadbeef0123456789abcdef")
))

# Variant 6: With exclusive relayer (should be blocked if exclusivity not expired)
print("--- Variant 6: With exclusiveRelayer and exclusivityDeadline in far future ---")
simulate("exclusive", (
    addr_to_bytes32("0x0000000000000000000000000000000000000001"),
    addr_to_bytes32("0x0000000000000000000000000000000000000002"),
    addr_to_bytes32("0x0000000000000000000000000000000000000099"),  # non-zero exclusive relayer
    WETH_ARB, WETH_ETH,
    1_000_000_000_000_000_000, 990_000_000_000_000_000,
    42161, 444_444_444,
    fill_deadline,
    block_timestamp + 3600,  # exclusivity deadline 1h in future -> should block
    b""
))

# Variant 7: With exclusive relayer but exclusivity deadline already passed
print("--- Variant 7: With exclusiveRelayer but exclusivityDeadline = 1 (expired) ---")
simulate("excl expired", (
    addr_to_bytes32("0x0000000000000000000000000000000000000001"),
    addr_to_bytes32("0x0000000000000000000000000000000000000002"),
    addr_to_bytes32("0x0000000000000000000000000000000000000099"),
    WETH_ARB, WETH_ETH,
    1_000_000_000_000_000_000, 990_000_000_000_000_000,
    42161, 333_333_333,
    fill_deadline,
    1,  # exclusivity deadline = 1 (long expired)
    b""
))

# Variant 8: fillDeadline in the past (should revert)
print("--- Variant 8: fillDeadline in the past (should revert) ---")
simulate("past deadline", (
    addr_to_bytes32("0x0000000000000000000000000000000000000001"),
    addr_to_bytes32("0x0000000000000000000000000000000000000002"),
    ZERO32, WETH_ARB, WETH_ETH,
    1_000_000_000_000_000_000, 990_000_000_000_000_000,
    42161, 222_222_222,
    block_timestamp - 3600,  # 1 hour in the past
    0, b""
))

# Variant 9: Zero output amount
print("--- Variant 9: Zero output amount ---")
simulate("zero out", (
    addr_to_bytes32("0x0000000000000000000000000000000000000001"),
    addr_to_bytes32("0x0000000000000000000000000000000000000002"),
    ZERO32, WETH_ARB, WETH_ETH,
    1_000_000_000_000_000_000, 0,  # zero output
    42161, 111_111_111, fill_deadline, 0, b""
))

# Variant 10: Zero input AND output
print("--- Variant 10: Zero input and output ---")
simulate("zero both", (
    addr_to_bytes32("0x0000000000000000000000000000000000000001"),
    addr_to_bytes32("0x0000000000000000000000000000000000000002"),
    ZERO32, WETH_ARB, WETH_ETH,
    0, 0,
    42161, 100_000_000, fill_deadline, 0, b""
))

print()
print("=" * 70)
print("SUMMARY")
print("=" * 70)
print()
print("The requestSlowFill function on the Ethereum SpokePool:")
print("  - ACCEPTS any fabricated relay data where:")
print("    1. fillDeadline > block.timestamp")
print("    2. exclusivityDeadline < block.timestamp OR exclusiveRelayer = 0x0")
print("    3. The relay hash has not been used before (fill status = Unfilled)")
print("  - Does NOT verify:")
print("    - Whether the deposit actually exists on the origin chain")
print("    - Whether the depositId is valid")
print("    - Whether the originChainId is a real Across-supported chain")
print("    - Whether the amounts make sense")
print("    - Whether the tokens are valid")
print("    - Whether the depositor/recipient are real")
print()
print("SECURITY MODEL: The SpokePool is intentionally permissive.")
print("Anyone can call requestSlowFill with arbitrary data.")
print("The Across Dataworker (off-chain) validates deposits against")
print("origin chain data before including slow fills in root bundles.")
print("Only executeSlowRelayLeaf (which requires a valid Merkle proof")
print("from a validated root bundle) actually moves funds.")
