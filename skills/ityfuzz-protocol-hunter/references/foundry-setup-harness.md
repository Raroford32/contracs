# Foundry Setup / Invariant Harness (ItyFuzz `--deployment-script`)

This note documents the **exact interface** ItyFuzz queries when you run EVM fuzzing in
`setup` mode using:

```bash
ityfuzz evm -m path/to/File.sol:ContractName -- forge test
```

The official README shows this style of usage (`repo-README.md`), but the full contract
interface is easiest to understand from the source.

## What ItyFuzz does in setup mode

1) Builds your project into build artifacts (from the command after `--`).
2) Deploys the `--deployment-script` contract.
3) Calls `setUp()` on the deployed contract.
4) Calls the following **no-arg** functions on the same contract to learn what to fuzz:

- `excludeContracts()`
- `excludeSenders()`
- `targetContracts()`
- `targetSenders()`
- `targetSelectors()`
- `v2Pairs()`
- `constantPairs()`

These are inspired by Foundry invariant-test conventions but are consumed directly by ItyFuzz.

## Required Solidity ABI signatures

`targetSelectors()` must return an array of tuples:

```solidity
// (address addr, bytes4[] selectors)[]
function targetSelectors() external view returns (TargetSelector[] memory);
```

`constantPairs()` must return an array of tuples:

```solidity
// (address token, address faucet, uint256 ratio)[]
function constantPairs() external view returns (ConstantPairMetadata[] memory);
```

## Minimal harness template

This is a starting point you can paste into a Foundry project.
Fill in the deployment logic, the target contracts, and selectors.

```solidity
// SPDX-License-Identifier: UNLICENSED
pragma solidity ^0.8.13;

// Optional: import forge-std/Test.sol if you already have it in the repo.
// import "forge-std/Test.sol";

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

    // --- Your deployment state ---
    // Example:
    // MyToken token;
    // MyProtocol protocol;

    function setUp() public {
        // Deploy and initialize your protocol + required dependencies here.
        // This should result in a fully-initialized environment ready for fuzzing.
        //
        // Example patterns:
        // - Deploy ERC20 + mint balances to attacker senders
        // - Deploy pools/routers/oracles
        // - Configure protocol roles / owners / params
    }

    // Contracts you never want ItyFuzz to call (optional)
    function excludeContracts() external view returns (address[] memory) {
        address[] memory out = new address[](0);
        return out;
    }

    // Senders you never want ItyFuzz to use (optional)
    function excludeSenders() external view returns (address[] memory) {
        address[] memory out = new address[](0);
        return out;
    }

    // Contracts ItyFuzz is allowed to fuzz (recommended: keep tight)
    function targetContracts() external view returns (address[] memory) {
        address[] memory out = new address[](0);
        // out = new address[](1);
        // out[0] = address(protocol);
        return out;
    }

    // Callers (EOAs) ItyFuzz may use (recommended: include attacker-like addresses)
    function targetSenders() external view returns (address[] memory) {
        address[] memory out = new address[](0);
        // out = new address[](2);
        // out[0] = address(0xA11CE);
        // out[1] = address(0xB0B);
        return out;
    }

    // Function selectors allowed per contract
    function targetSelectors() external view returns (TargetSelector[] memory out) {
        // Example:
        // out = new TargetSelector[](1);
        // bytes4[] memory sels = new bytes4[](2);
        // sels[0] = MyProtocol.deposit.selector;
        // sels[1] = MyProtocol.withdraw.selector;
        // out[0] = TargetSelector({addr: address(protocol), selectors: sels});

        out = new TargetSelector[](0);
    }

    // Optional: V2 pairs for liquidation/oracle logic
    function v2Pairs() external view returns (address[] memory out) {
        out = new address[](0);
    }

    // Optional: constant price “faucets” metadata used by ItyFuzz token logic
    function constantPairs() external view returns (ConstantPairMetadata[] memory out) {
        out = new ConstantPairMetadata[](0);
    }

    // --- Deep-logic invariants (optional) ---
    // If you enable the `invariant` detector, ItyFuzz looks for *no-arg* functions
    // whose name starts with `invariant_`.
    //
    // The invariant oracle reports a bug when the call FAILS (reverts).
    // So write invariants using `require(...)` / `assert(...)`.
    //
    // function invariant_totalSupplyMatchesAccounting() external view {
    //     require(protocol.totalSupply() == protocol.accountingTotal(), "accounting drift");
    // }
}
```

## Selector strategy (for “maximum complexity” sequences)

To encourage deep, cross-contract sequences (instead of shallow single-call bugs):

- Include **stateful entrypoints** (mint/burn, deposit/withdraw, swap, borrow/repay, liquidate, sync, settle, harvest).
- Include **approval/permit** paths if relevant.
- Include **admin paths** only if the attacker realistically has access (or you want to test misconfig).
- Start with a **minimal** set, then widen if ItyFuzz stalls.

## Running it

From your Foundry repo root:

```bash
ityfuzz evm -m test/ItyFuzzHarness.sol:ItyFuzzHarness -w analysis/ityfuzz/harness -- forge test
```

Notes:
- Use `-w/--work-dir` to keep runs isolated and reproducible.
- Use `--detectors` to control which oracles run (see `detectors-and-oracles.md`).
- If you want flashloan/liquidation behaviors, add `-f/--flashloan` and provide `v2Pairs()/constantPairs()`.

