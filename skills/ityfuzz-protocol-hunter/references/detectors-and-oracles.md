# Detectors / Oracles (`--detectors`)

ItyFuzz’s `--detectors` flag selects which “oracles” run to decide whether a trace is a bug.
The CLI help is authoritative (`cli-ityfuzz-evm-help.txt`), and the official docs describe
the common-vuln detectors at a high level (`official-docs-evm-contract-detecting-common-vulns.md`).

## Built-in presets

- `--detectors high_confidence` (default)
  - Fast, low false-positive; may exclude some experimental detectors.
- `--detectors all`
  - Broad set, but **does not include** the `invariant` oracle in current upstream source.

Important: the preset tokens `all` and `high_confidence` **short-circuit** parsing.
If you want a custom mix, list detectors explicitly.

## Explicit detector strings (current upstream)

Supported detector tokens (comma-separated):

- `erc20`
  - balance/token extraction style bugs (includes liquidation heuristics)
- `pair`
  - Uniswap V2 pair misuse / pair-balance issues
- `reentrancy`
  - reentrancy opportunity detection (used to explore more paths)
- `arbitrary_call`
  - arbitrary external call style bugs (suspicious call surfaces)
- `math_calculate`
  - arithmetic / calculation anomalies (overflow/underflow-style; confidence may vary)
- `echidna`
  - runs `echidna_*()` no-arg functions; bug when returns `false` / reverts
- `invariant`
  - runs `invariant_*()` no-arg functions; bug when call **fails** (reverts)
- `typed_bug`
  - detects `bug()` / `typed_bug(string)` style bug markers
- `selfdestruct`
  - arbitrary selfdestruct detection
- `state_comparison`
  - state comparison oracle (advanced/experimental)

## Recommended profiles for “deep protocol logic” bugs

1) Start with default:
   - `--detectors high_confidence -f`
2) Add concolic when stuck on conditions:
   - `--concolic --concolic-caller`
3) If you added invariants to your codebase:
   - Keep `invariant` enabled (default high_confidence includes it)
4) If you want “everything including invariants”:
   - list explicitly:

```text
erc20,pair,reentrancy,arbitrary_call,math_calculate,echidna,state_comparison,typed_bug,selfdestruct,invariant
```

## `panic_on_bug`

If you’re using `typed_bug(...)` in Solidity, `--panic-on-bug` can be useful for CI-style runs
where you want an immediate hard failure at the first `typed_bug`.

