# ItyFuzz Docs Index (Official + Source-Derived)

This folder intentionally vendors **official ItyFuzz docs/tutorials** (verbatim copies)
plus a few **source-derived notes** for advanced workflows that are only lightly documented.

## Official docs (from `fuzzland/ityfuzz-docs`)

- `official-README.md`: high-level intro + algorithm notes (concolic-assisted fuzzing, dataflow + comparisons)
- `official-installation-and-building.md`: install via `ityfuzzup`, build-from-source notes
- `official-quickstart.md`: onchain/offchain EVM usage and Move quickstart
- `official-docs-evm-contract-constructor-for-offchain-fuzzing.md`: `--constructor-args` and `--fetch-tx-data` server-forwarding flow
- `official-docs-evm-contract-writing-invariants.md`: Echidna-style invariants, Scribble support, `bug()` / `typed_bug()`
- `official-docs-evm-contract-detecting-common-vulns.md`: detector categories and confidence notes
- Tutorials:
  - `official-tutorials-exp-hacking-aes.md` (complex flashloan + price manipulation)
  - `official-tutorials-exp-hacking-bego.md` (arbitrary mint)
  - `official-tutorials-ctf-verilog-ctf-onchain.md` / `official-tutorials-ctf-verilog-ctf-offchain.md`
  - `official-tutorials-exp-known-working-hacks.md` (large list of backtests)
- `official-SUMMARY.md`: upstream table-of-contents (good starting point)

## Official repo docs (from `fuzzland/ityfuzz`)

- `repo-README.md`: feature list + Foundry invariant example (`ityfuzz evm -m ... -- forge test`)
- `repo-backtesting.md`: backtesting commands (may contain older flags; rely on CLI help for your binary)
- `repo-integration-test.md`: internal integration testing notes

## CLI reference (from the built `ityfuzz` binary)

- `cli-ityfuzz-help.txt`: top-level commands
- `cli-ityfuzz-evm-help.txt`: **authoritative** EVM flags + defaults
- `cli-ityfuzz-version.txt`: the exact version string of the binary used to generate help output

## Source-derived notes (created for this skill)

- `foundry-setup-harness.md`: write a Foundry-style setup/invariant harness that ItyFuzz can consume via `--deployment-script`
- `offchain-config-schema.md`: JSON format for `--offchain-config-file/--offchain-config-url`
- `replay-and-corpus.md`: `work_dir/` layout, `vuln_info.jsonl`, `_replayable` traces, `--replay-file`, `--load-corpus`
- `detectors-and-oracles.md`: detector strings (`--detectors`) + practical selection guidance
- `target-types-and-modes.md`: when to use `glob` vs `address` vs `setup` vs `config` vs `anvil_fork`
- `sequence-driven-vuln-taxonomy-2026.md`: modern discontinuity classes (use to generate hypotheses)
- `sequence-driven-prompt-pack.md`: prompting guide to synthesize deep, multi-step exploit sequences
