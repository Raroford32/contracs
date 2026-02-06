#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'USAGE'
Traverse full scan (sol2bnd, sol2cg, sol-storage-analyzer, storage-trace, sol2test).

Usage:
  traverse_full_scan.sh --project <path> [options]

Required:
  --project <path>           Project root directory

Options:
  --out <dir>                Output directory (default: analysis/traverse)
  --bindings <file>          Use existing bindings.yaml (skip sol2bnd)
  --manifest <file>          Use existing manifest.yaml
  --storage-pairs <file>     CSV file with func pairs for storage-trace
  --cg-overview-config <kv>  sol2cg config for overview
  --cg-deep-config <kv>      sol2cg config for deep analysis
  --cg-external-config <kv>  sol2cg config for external-only
  --test-config <kv>         sol2test config
  --use-foundry              Use Foundry for compilation/validation
  --validate-compilation     Validate generated tests compile
  --dry-run                  Print commands without executing
  -h, --help                 Show help

Storage pairs CSV format:
  func1,func2,paths(optional; use ';' to separate multiple paths)

Example:
  traverse_full_scan.sh --project . --use-foundry --validate-compilation \
    --storage-pairs analysis/storage-pairs.csv
USAGE
}

project=""
out_dir="analysis/traverse"
bindings_file=""
manifest_file=""
storage_pairs=""
# Defaults aim for "do not miss any EOA/contract-callable surface":
# - deep: include internal + modifiers + external calls, high depth
# - external: focus view, but still include modifier edges
# - overview: shallow and hides internals but keeps modifiers/external calls visible
cg_overview_config="max_depth=2,include_internal=false,include_modifiers=true,show_external_calls=true"
cg_deep_config="max_depth=50,include_internal=true,include_modifiers=true,show_external_calls=true"
cg_external_config="max_depth=50,include_internal=false,include_modifiers=true,show_external_calls=true"
test_config="include_reverts=true,include_events=true,test_edge_cases=true"
use_foundry=false
validate_compilation=false
dry_run=false

while [[ $# -gt 0 ]]; do
  case "$1" in
    --project) project="$2"; shift 2 ;;
    --out) out_dir="$2"; shift 2 ;;
    --bindings) bindings_file="$2"; shift 2 ;;
    --manifest) manifest_file="$2"; shift 2 ;;
    --storage-pairs) storage_pairs="$2"; shift 2 ;;
    --cg-overview-config) cg_overview_config="$2"; shift 2 ;;
    --cg-deep-config) cg_deep_config="$2"; shift 2 ;;
    --cg-external-config) cg_external_config="$2"; shift 2 ;;
    --test-config) test_config="$2"; shift 2 ;;
    --use-foundry) use_foundry=true; shift ;;
    --validate-compilation) validate_compilation=true; shift ;;
    --dry-run) dry_run=true; shift ;;
    -h|--help) usage; exit 0 ;;
    *) echo "Unknown argument: $1" >&2; usage >&2; exit 1 ;;
  esac
done

if [[ -z "$project" ]]; then
  echo "Error: --project is required" >&2
  usage >&2
  exit 1
fi

if [[ ! -d "$project" ]]; then
  echo "Error: --project must be a directory: $project" >&2
  exit 1
fi

run_cmd() {
  if $dry_run; then
    printf '[dry-run]'
    printf ' %q' "$@"
    printf '\n'
  else
    "$@"
  fi
}

trim() {
  local s="$1"
  s="${s#"${s%%[![:space:]]*}"}"
  s="${s%"${s##*[![:space:]]}"}"
  printf '%s' "$s"
}

input_path="$project"
input_paths=()
if [[ -d "$project/src" ]]; then
  input_paths+=("$project/src")
fi
if [[ -d "$project/contracts" ]]; then
  input_paths+=("$project/contracts")
fi
if [[ ${#input_paths[@]} -eq 0 ]]; then
  input_paths+=("$project")
fi
input_path="${input_paths[0]}"

default_trace_paths=""
for p in "${input_paths[@]}"; do
  if [[ -z "$default_trace_paths" ]]; then
    default_trace_paths="$p"
  else
    default_trace_paths="${default_trace_paths};$p"
  fi
done

mkdir -p "$out_dir/bindings" "$out_dir/graphs/dot" "$out_dir/graphs/mermaid" \
  "$out_dir/storage" "$out_dir/tests" "$out_dir/storage-trace"

if [[ -z "$bindings_file" ]]; then
  if command -v sol2bnd >/dev/null 2>&1; then
    bindings_file="$out_dir/bindings/bindings.yaml"
    run_cmd sol2bnd "$project" -o "$bindings_file"
  else
    echo "WARN: sol2bnd not found; skipping bindings generation" >&2
  fi
fi

resolve_args=()
if [[ -n "$bindings_file" ]]; then
  resolve_args+=(--bindings "$bindings_file")
fi
if [[ -n "$manifest_file" ]]; then
  resolve_args+=(--manifest-file "$manifest_file")
fi

if command -v sol2cg >/dev/null 2>&1; then
  run_cmd sol2cg "${resolve_args[@]}" --config "$cg_overview_config" \
    "${input_paths[@]}" -o "$out_dir/graphs/dot/callgraph-overview.dot"
  run_cmd sol2cg "${resolve_args[@]}" --config "$cg_deep_config" \
    "${input_paths[@]}" -o "$out_dir/graphs/dot/callgraph-deep.dot"
  run_cmd sol2cg "${resolve_args[@]}" --config "$cg_external_config" \
    "${input_paths[@]}" -o "$out_dir/graphs/dot/callgraph-external.dot"

  run_cmd sol2cg -f mermaid --chunk-dir "$out_dir/graphs/mermaid/chunks" \
    "${resolve_args[@]}" --config "$cg_overview_config" \
    "${input_paths[@]}" -o "$out_dir/graphs/mermaid/sequence-overview.mmd"
  run_cmd sol2cg -f mermaid --chunk-dir "$out_dir/graphs/mermaid/chunks" \
    "${resolve_args[@]}" --config "$cg_deep_config" \
    "${input_paths[@]}" -o "$out_dir/graphs/mermaid/sequence-deep.mmd"
  run_cmd sol2cg -f mermaid --chunk-dir "$out_dir/graphs/mermaid/chunks" \
    "${resolve_args[@]}" --config "$cg_external_config" \
    "${input_paths[@]}" -o "$out_dir/graphs/mermaid/sequence-external.mmd"

  if command -v dot >/dev/null 2>&1; then
    for dot_file in "$out_dir/graphs/dot"/*.dot; do
      [[ -e "$dot_file" ]] || continue
      run_cmd dot -Tsvg "$dot_file" -o "${dot_file%.dot}.svg"
    done
  else
    echo "WARN: dot (Graphviz) not found; skipping SVG generation" >&2
  fi
else
  echo "WARN: sol2cg not found; skipping call graph generation" >&2
fi

if command -v sol-storage-analyzer >/dev/null 2>&1; then
  run_cmd sol-storage-analyzer "${resolve_args[@]}" "${input_paths[@]}" \
    -o "$out_dir/storage/storage-report.md"
else
  echo "WARN: sol-storage-analyzer not found; skipping storage analysis" >&2
fi

if command -v sol2test >/dev/null 2>&1; then
  sol2test_args=()
  if [[ -f "$project/foundry.toml" ]]; then
    sol2test_args+=(--project "$project")
  else
    sol2test_args+=("$input_path")
  fi
  sol2test_args+=(-o "$out_dir/tests")
  sol2test_args+=(--config "$test_config")
  if $use_foundry; then
    sol2test_args+=(--use-foundry)
  fi
  if $validate_compilation; then
    sol2test_args+=(--validate-compilation)
  fi
  if [[ -n "$bindings_file" ]]; then
    sol2test_args+=(--bindings "$bindings_file")
  fi
  if [[ -n "$manifest_file" ]]; then
    sol2test_args+=(--manifest-file "$manifest_file")
  fi
  run_cmd sol2test "${sol2test_args[@]}"
else
  echo "WARN: sol2test not found; skipping test generation" >&2
fi

if [[ -n "$storage_pairs" ]]; then
  if [[ ! -f "$storage_pairs" ]]; then
    echo "WARN: storage pairs file not found: $storage_pairs" >&2
  elif command -v storage-trace >/dev/null 2>&1; then
    while IFS= read -r line || [[ -n "$line" ]]; do
      line="$(trim "$line")"
      [[ -z "$line" ]] && continue
      [[ "$line" =~ ^# ]] && continue

      IFS=',' read -r func1 func2 paths <<<"$line"
      func1="$(trim "$func1")"
      func2="$(trim "$func2")"
      paths="$(trim "$paths")"
      [[ -z "$paths" ]] && paths="$default_trace_paths"

      safe_name=$(printf '%s__%s' "$func1" "$func2" | sed 's/[^A-Za-z0-9_.-]/_/g')
      out_file="$out_dir/storage-trace/${safe_name}.md"

      trace_args=(--func1 "$func1" --func2 "$func2")
      if [[ -n "$bindings_file" ]]; then
        trace_args+=(--bindings "$bindings_file")
      fi
      if [[ -n "$manifest_file" ]]; then
        trace_args+=(--manifest-file "$manifest_file")
      fi

      IFS=';' read -r -a path_list <<<"$paths"
      for i in "${!path_list[@]}"; do
        path_list[$i]="$(trim "${path_list[$i]}")"
      done

      run_cmd storage-trace "${trace_args[@]}" "${path_list[@]}" -o "$out_file"
    done < "$storage_pairs"
  else
    echo "WARN: storage-trace not found; skipping storage comparisons" >&2
  fi
fi
