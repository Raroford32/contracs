// SPDX-License-Identifier: UNLICENSED
pragma solidity ^0.8.13;

// Minimal harness interface consumed by ItyFuzz `--deployment-script`.
// Fill `setUp()` and the target lists/selectors for your protocol.

contract ItyFuzzHarness {
    // (address addr, bytes4[] selectors)[]
    struct TargetSelector {
        address addr;
        bytes4[] selectors;
    }

    // (address token, address faucet, uint256 ratio)[]
    struct ConstantPairMetadata {
        address token;
        address faucet;
        uint256 ratio;
    }

    function setUp() public {
        // Deploy and initialize your protocol + dependencies here.
    }

    function excludeContracts() external view returns (address[] memory out) {
        out = new address[](0);
    }

    function excludeSenders() external view returns (address[] memory out) {
        out = new address[](0);
    }

    function targetContracts() external view returns (address[] memory out) {
        out = new address[](0);
    }

    function targetSenders() external view returns (address[] memory out) {
        out = new address[](0);
    }

    function targetSelectors() external view returns (TargetSelector[] memory out) {
        out = new TargetSelector[](0);
    }

    function v2Pairs() external view returns (address[] memory out) {
        out = new address[](0);
    }

    function constantPairs() external view returns (ConstantPairMetadata[] memory out) {
        out = new ConstantPairMetadata[](0);
    }

    // Optional deep-logic invariants:
    // If `--detectors` includes `invariant`, ItyFuzz calls `invariant_*()` (no args).
    // Report a bug by reverting (e.g., `require(cond, "msg")`).
    // function invariant_example() external view {
    //     require(false, "invariant violated");
    // }
}

