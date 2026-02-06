# sol2test - Foundry Test Generator

Purpose:
- Generate comprehensive Foundry test suites from Solidity source code.
- Create deployment scripts, setup functions, and test stubs for public/external functions.
- Provide helper functions and parameterized tests.

Prerequisites:
- Foundry installed for compilation/validation.

Install Foundry:
```bash
curl -L https://foundry.paradigm.xyz | bash
foundryup
```

Installation:
```bash
# Install via Homebrew
brew install traverse

# Or download binary
curl -sSfL -o /usr/local/bin/sol2test \
  https://github.com/calltrace/traverse/releases/latest/download/sol2test-macos-arm64
chmod +x /usr/local/bin/sol2test
```

Basic usage:
```bash
# Generate tests for single contract
sol2test Token.sol

# Generate tests for multiple contracts
sol2test contracts/Token.sol contracts/Vault.sol

# Process entire directory
sol2test src/

# Specify output directory
sol2test contracts/ -o test/
```

Command line options:
Required arguments
- `[INPUT_PATHS]...`: Solidity files to analyze (optional if using `--project`)

Project options
- `--project <PROJECT>`: Process a Foundry project directory instead of individual files
- `--foundry-root <FOUNDRY_ROOT>`: Root directory of Foundry project (default: auto-detect)

Output options
- `-o, --output-dir <OUTPUT_DIR>`: Output directory for generated tests (default: `foundry-tests/test`)
- `-t, --template-dir <TEMPLATE_DIR>`: Custom template directory (default: built-in templates)

Foundry integration
- `--use-foundry`: Use Foundry for compilation and validation
- `--validate-compilation`: Validate that generated tests compile
- `--deployer-only`: Generate only deployment tests

Analysis control
- `--disable-steps <DISABLE_STEPS>`: Disable specific pipeline steps
- `--enable-steps <ENABLE_STEPS>`: Enable specific pipeline steps
- `--config <CONFIG>`: Configuration parameters (format: `key=value,key2=value2`)

Interface resolution
- `--bindings <BINDINGS>`: Path to binding.yaml file for interface resolution
- `--manifest-file <MANIFEST_FILE>`: Path to pre-generated manifest.yaml

General
- `-v, --verbose`: Enable verbose output
- `-h, --help`: Show help information
- `-V, --version`: Show version information

Working with Foundry projects:
Project mode
```bash
# Analyze entire Foundry project
sol2test --project . --use-foundry

# Process specific project directory
sol2test --project ./my-protocol --use-foundry

# Generate with compilation validation
sol2test --project . --use-foundry --validate-compilation
```

Standard directory structure:
```
my-foundry-project/
├── src/
│   ├── Token.sol
│   ├── Vault.sol
│   └── interfaces/
│       └── IVault.sol
├── test/
│   └── (generated tests will go here)
├── foundry.toml
└── lib/
    └── forge-std/
```

Generated test structure (example):
```solidity
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

import "forge-std/Test.sol";
import "../src/Token.sol";

contract TokenTest is Test {
    Token token;

    function setUp() public {
        token = new Token("Test Token", "TEST", 18);
    }

    function test_constructor() public {
        // TODO: Test constructor initialization
        assertEq(token.name(), "Test Token");
        assertEq(token.symbol(), "TEST");
        assertEq(token.decimals(), 18);
    }

    function test_transfer() public {
        // TODO: Test transfer functionality
        address recipient = address(0x123);
        uint256 amount = 100 * 10**18;

        // Arrange: Mint tokens to this contract
        // TODO: Setup initial state

        // Act: Transfer tokens
        // TODO: Call transfer function

        // Assert: Verify transfer
        // TODO: Check balances
    }

    function test_transfer_insufficientBalance() public {
        // TODO: Test transfer with insufficient balance
        // Should revert with appropriate error
    }

    function test_approve() public {
        // TODO: Test approval functionality
    }

    function test_transferFrom() public {
        // TODO: Test transferFrom functionality
    }
}
```

Deployment tests (with `--deployer-only`):
```solidity
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

import "forge-std/Test.sol";
import "../src/Token.sol";

contract TokenDeployerTest is Test {
    function test_deployToken() public {
        Token token = new Token("Test Token", "TEST", 18);

        assertTrue(address(token) != address(0));
        assertEq(token.name(), "Test Token");
        assertEq(token.symbol(), "TEST");
        assertEq(token.decimals(), 18);
    }

    function test_deployTokenWithZeroName() public {
        // TODO: Test deployment with empty name
        // Should handle appropriately
    }
}
```

Configuration options:
Use `--config` with comma-separated `key=value` pairs.

Example:
```bash
sol2test --config "include_reverts=true,include_events=true" contracts/
```

Available configuration options:
| Option | Type | Default | Description |
| --- | --- | --- | --- |
| `include_reverts` | boolean | true | Generate revert test cases |
| `include_events` | boolean | true | Include event emission tests |
| `include_gas_tests` | boolean | false | Include gas usage tests |
| `parameterized_tests` | boolean | true | Generate parameterized test cases |
| `setup_initial_balance` | boolean | true | Setup initial token balances |
| `test_edge_cases` | boolean | true | Include edge case testing |
| `generate_helpers` | boolean | true | Generate helper functions |
| `custom_templates` | boolean | false | Use custom template directory |

Example configurations:
```bash
# Comprehensive test suite
sol2test --config "include_reverts=true,include_events=true,test_edge_cases=true" contracts/

# Basic test generation only
sol2test --config "include_reverts=false,include_events=false,test_edge_cases=false" contracts/

# Gas-aware testing
sol2test --config "include_gas_tests=true,parameterized_tests=true" contracts/
```

Advanced examples:
DeFi protocol testing
```bash
sol2test --project ./defi-protocol \
  --use-foundry \
  --validate-compilation \
  --config "include_reverts=true,test_edge_cases=true" \
  -o test/
```

Upgrade safety testing
```bash
sol2test --project ./upgradeable-protocol \
  --use-foundry \
  --config "test_edge_cases=true,include_events=true" \
  -o test/
```

Multi-contract integration
```bash
sol2test --bindings bindings.yaml \
  src/Vault.sol src/Token.sol src/Controller.sol \
  --config "parameterized_tests=true,include_events=true" \
  -o test/integration/
```

Template customization:
Using custom templates
```bash
mkdir -p my-templates/
sol2test --template-dir my-templates/ contracts/
```

Template structure:
```
templates/
├── test_contract.sol.hbs     # Main test contract template
├── test_function.sol.hbs     # Individual test function template
├── setup_function.sol.hbs    # setUp() function template
├── helpers.sol.hbs           # Helper functions template
└── deployment_test.sol.hbs   # Deployment test template
```

Custom template example:
```handlebars
{{!-- templates/test_function.sol.hbs --}}
function test_{{function_name}}() public {
    // Test {{function_name}} functionality

    {{#each parameters}}
    {{type}} {{name}} = {{#if (eq type "address")}}address(0x{{@index}}){{else}}{{default_value}}{{/if}};
    {{/each}}

    // TODO: Arrange
    // Setup initial state for {{function_name}}

    // TODO: Act
    // Call {{function_name}} with test parameters

    // TODO: Assert
    // Verify expected behavior
    {{#if expect_revert}}
    vm.expectRevert({{error_selector}});
    {{/if}}
}
```

Workflow integration:
Pre-commit hook
```yaml
repos:
  - repo: local
    hooks:
      - id: generate-tests
        name: Generate Foundry Tests
        entry: sol2test
        language: system
        args: ["src/", "-o", "test/", "--use-foundry"]
        files: "^src/.*\\.sol$"
        pass_filenames: false
```

Makefile integration
```makefile
.PHONY: generate-tests validate-tests clean-tests

generate-tests:
	sol2test --project . --use-foundry --validate-compilation

validate-tests:
	forge build

clean-tests:
	rm -rf test/

test-all: generate-tests
	forge test

coverage: generate-tests
	forge coverage --report lcov
```

CI/CD example (GitHub Actions)
```yaml
- name: Generate Tests
  run: |
    sol2test --project . --use-foundry --validate-compilation

- name: Run Tests
  run: forge test

- name: Generate Coverage Report
  run: forge coverage --report lcov

- name: Upload Coverage
  uses: codecov/codecov-action@v3
  with:
    file: lcov.info
```

Best practices:
Test organization
```bash
sol2test src/tokens/ -o test/tokens/
sol2test src/vaults/ -o test/vaults/
sol2test src/controllers/ -o test/controllers/
```

Incremental test generation
```bash
git diff --name-only HEAD~1 | grep "\\.sol$" | xargs sol2test -o test/updated/
```

Validation pipeline
```bash
sol2test --project . --use-foundry --validate-compilation
forge build
forge test --gas-report
forge coverage --report lcov
```

Parameter configuration
```bash
# Development: Quick feedback
sol2test --config "include_reverts=false,test_edge_cases=false" src/

# Testing: Comprehensive coverage
sol2test --config "include_reverts=true,test_edge_cases=true,include_events=true" src/

# Production: Complete validation
sol2test --config "include_reverts=true,test_edge_cases=true,include_events=true,include_gas_tests=true" src/
```
