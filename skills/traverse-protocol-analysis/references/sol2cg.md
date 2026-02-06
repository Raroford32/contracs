# sol2cg - Call Graph Generator

Purpose:
- Generate call graphs (DOT) and sequence diagrams (Mermaid) from Solidity source code.
- Support deep or shallow analysis via config options.
- Use bindings/manifest for accurate interface resolution.

Installation:
```bash
brew install traverse
# or download binary
curl -sSfL -o /usr/local/bin/sol2cg \
  https://github.com/calltrace/traverse/releases/latest/download/sol2cg-macos-arm64
chmod +x /usr/local/bin/sol2cg
```

Basic usage:
```bash
sol2cg contracts/*.sol -o graph.dot
dot -Tsvg graph.dot -o graph.svg
```

Options:
Output
- `-o, --output-file`: Output file (default: stdout)
- `-f, --format`: `dot` or `mermaid`

Analysis
- `--exclude-isolated-nodes`: Remove orphaned nodes (DOT only)
- `--chunk-dir`: Directory for chunked Mermaid output
- `--config`: Pipeline settings in `key=value` list (example: `max_depth=3,skip_internals=true`)

Interface resolution
- `--bindings`: Path to binding.yaml
- `--manifest-file`: Pre-generated manifest

Output formats:
DOT (default)
```bash
sol2cg contracts/*.sol -o graph.dot
dot -Tpng graph.dot -o graph.png
```

Mermaid
```bash
sol2cg -f mermaid contracts/*.sol -o diagram.mmd
```

Configuration:
Example configs
```bash
# High-level overview
sol2cg --config "max_depth=2,include_internal=false,include_modifiers=true,show_external_calls=true" contracts/

# Deep analysis (full surface)
sol2cg --config "max_depth=50,include_internal=true,include_modifiers=true,show_external_calls=true" contracts/

# External calls only
sol2cg --config "max_depth=50,include_internal=false,include_modifiers=true,show_external_calls=true" contracts/
```

Config options:
| Option | Default | Description |
| --- | --- | --- |
| `max_depth` | 10 | Maximum call depth |
| `include_internal` | true | Include private/internal functions |
| `include_modifiers` | true | Include modifier calls |
| `show_external_calls` | true | Show external contract calls |

Notes for completeness:
- Keep `include_modifiers=true` even in "external-only" graphs; modifiers can hide external calls and state writes.
- If a protocol uses proxies heavily, pair sol2cg with bindings (`sol2bnd`) so interface calls resolve to implementations instead of staying opaque.
