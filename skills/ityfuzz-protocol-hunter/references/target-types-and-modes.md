# Target Types and Modes (EVM)

ItyFuzz’s EVM CLI has multiple “target modes” that decide **where contracts come from** and
**how the initial state is built**. The authoritative flag list is in `cli-ityfuzz-evm-help.txt`.

## Quick decision tree

- **You have deployed contract address(es) and want real chain state**:
  - Use **Onchain / Address mode**: `-t 0x..,0x.. -c <chain> -b <block> ...`
- **You have compiled `.abi/.bin` files and want a clean local chain**:
  - Use **Offchain / Glob mode**: `-t './build/*' ...`
- **You have a Foundry/Hardhat project and need complex initialization**:
  - Use **Setup mode** (`--deployment-script`) with a build command (e.g. `-- forge test`)
- **You need fixed addresses + ABI-encoded constructor args (advanced)**:
  - Use **Config mode** (`--offchain-config-file`) with build artifacts
- **You want to fuzz on a fork but with local build artifacts for coverage/srcmaps**:
  - Use **Anvil fork mode** (requires onchain config + build artifacts / build command)

## How target type is selected

ItyFuzz can infer the target type, but **build artifacts / build commands** and **onchain flags**
can force a different mode:

- `--target-type <glob|address|anvil_fork|config|setup>` can set the target type explicitly.
- If you provide `BUILDER_ARTIFACTS_*` or a `BUILD_COMMAND`:
  - If you also provide onchain config (`-c ...` or `--onchain-url ...`), ItyFuzz uses `anvil_fork`.
  - Else if you provide `--deployment-script ...`, ItyFuzz uses `setup`.
  - Else if you provide `--offchain-config-file/url ...`, ItyFuzz uses `config`.

## Mode details

### Glob (offchain)

Inputs:
- `-t/--target` is a glob like `./build/*`
- Directory contains `*.abi` and `*.bin` (see `official-quickstart.md`)
- Optional:
  - `.address` files if correlation inference fails
  - `--constructor-args` for human-readable constructor args

Behavior:
- Deploys artifacts into a clean local VM and fuzzes reachable calls.

### Address (onchain)

Inputs:
- `-t/--target` is comma-separated addresses (`0x..,0x..`)
- Requires onchain config:
  - `-c/--chain-type` (preferred) or
  - `--onchain-url`, `--onchain-chain-id`, `--onchain-explorer-url`, `--onchain-chain-name`
- Optional: `-k/--onchain-etherscan-api-key` (or `ETHERSCAN_API_KEY` env var)

Behavior (from official docs):
- Pulls ABI from explorer; pulls unknown storage slots via RPC; pulls unknown external bytecode/ABI and may decompile if needed.

### Setup (Foundry-style deployment/invariant harness)

Inputs:
- `-m/--deployment-script <file.sol:ContractName>`
- A build command after `--` (e.g. `-- forge test`)

Behavior:
- Builds the project (Foundry/solc/Hardhat-style supported) into build-info JSON.
- Deploys the `deployment-script` contract, calls `setUp()`, then queries:
  - `excludeContracts`, `excludeSenders`, `targetContracts`, `targetSenders`, `targetSelectors`, `v2Pairs`, `constantPairs`
- Uses these to drive which contracts/functions/senders are fuzzed.

See `foundry-setup-harness.md`.

### Config (advanced offchain deployment config)

Inputs:
- `--offchain-config-file <json>` (or `--offchain-config-url <url>`)
- Also requires build artifacts (via `--builder-artifacts-*` or `BUILD_COMMAND`)

Behavior:
- Uses a JSON mapping to pin **addresses** and **ABI-encoded constructor args** per contract.

See `offchain-config-schema.md`.

### Anvil fork (onchain + build artifacts)

Inputs:
- Onchain config (`-c/-b` or custom `--onchain-url/...`)
- Build artifacts (`--builder-artifacts-*` or `BUILD_COMMAND`)
- `-t` is a comma-separated list of onchain addresses to map against your build artifacts.

Behavior:
- Fetches onchain bytecode and heuristically matches it to local artifacts (bytecode similarity).
- Uses local build artifacts (ABI/srcmaps) for coverage and higher-quality reporting.

