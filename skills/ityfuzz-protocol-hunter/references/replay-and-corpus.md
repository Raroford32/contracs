# Replay and Corpus (Work Dir Layout)

This note documents the practical files ItyFuzz writes under `--work-dir` and how to
replay/resume runs.

The exact CLI flags are in `cli-ityfuzz-evm-help.txt`.

## Work dir: important outputs

Given `-w analysis/ityfuzz/run-1`, ItyFuzz commonly produces:

- `analysis/ityfuzz/run-1/vuln_info.jsonl`
  - newline-delimited JSON, appended for each discovered bug (oracle output objects)
- `analysis/ityfuzz/run-1/vulnerabilities/*.t.sol`
  - Foundry PoC testcases generated for discovered traces
- `analysis/ityfuzz/run-1/vulnerabilities/<bug_idxs>`
  - human-readable trace summary (written when `print_txn_corpus` is enabled; enabled by default in upstream builds)
- `analysis/ityfuzz/run-1/vulnerabilities/<bug_idxs>_replayable`
  - replayable minimized trace as newline-delimited JSON (`ConciseEVMInput`)
- `analysis/ityfuzz/run-1/relations.log`
  - only when `--write-relationship` is enabled; logs `{caller -> target selector}` pairs

## Replay a minimized trace

Use `--replay-file` with the `_replayable` file.

Example (offchain glob):

```bash
ityfuzz evm \
  -t './build/*' \
  -w analysis/ityfuzz/run-1-replay \
  --replay-file 'analysis/ityfuzz/run-1/vulnerabilities/*_replayable'
```

Example (onchain address):

```bash
ityfuzz evm \
  -t 0xTarget1,0xTarget2 \
  -c bsc -b 23695904 \
  -w analysis/ityfuzz/run-1-replay \
  --replay-file 'analysis/ityfuzz/run-1/vulnerabilities/*_replayable' \
  -k "$BSC_ETHERSCAN_API_KEY" \
  -f
```

Notes:
- Replay needs the same **mode** (onchain/offchain) and similar configuration so contract loading matches.
- If replay fails because a contract ABI differs (proxy/decompilation), use `--force-abi` for stability.

## Resume fuzzing from a corpus

Use `--load-corpus <glob>` to seed the corpus before starting the fuzz loop.

The corpus files are stored inside the work dir (exact folder names may vary by build).
When in doubt:

1) locate corpus files:
   - `find analysis/ityfuzz/run-1 -type f | head`
2) resume with a broad glob:
   - `--load-corpus 'analysis/ityfuzz/run-1/**'`

## “Run forever” campaigns

For long campaigns where you want multiple bugs:

```bash
ityfuzz evm ... --run-forever -w analysis/ityfuzz/long-run
```

Pair it with:
- `--seed` to control determinism between runs
- `--write-relationship` to keep a call-surface log

