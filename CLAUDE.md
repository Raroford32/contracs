# CLAUDE.md v4.0 — Compositional Exploit Discovery Engine
## For Mature, Battle-Tested Protocols on Ethereum Mainnet (2026)
*(Evidence-only • Protocol-complete • Cross-contract • Feasibility-gated • Zero-tolerance for trivia)*

---

# ABSOLUTE BANS (Override Everything)

## BANNED PATTERNS — Never Investigate, Never Reason About

These patterns are **completely banned** from all analysis. Any hypothesis involving them is immediately rejected. Do not waste compute on them.

```
BANNED_PATTERN_001: FIRST_DEPOSITOR / EMPTY_VAULT
- Reason: Mitigated in all production contracts via minimum shares, virtual reserves, or dead shares
- Action: Skip immediately. Do not write hypothesis. Do not mention in reasoning.

BANNED_PATTERN_002: UNINITIALIZED_PROXY / IMPLEMENTATION_TAKEOVER
- Reason: OpenZeppelin's _disableInitializers() is standard since 2021. All audited contracts use it.
- Action: Skip immediately. Do not probe initialization functions.

BANNED_PATTERN_003: SIMPLE_REENTRANCY
- Reason: ReentrancyGuard or CEI pattern is universal. Auditors catch these on day one.
- Action: Skip immediately. Only investigate READ-ONLY reentrancy in complex cross-contract scenarios.

BANNED_PATTERN_004: BASIC_ACCESS_CONTROL_MISSING
- Reason: onlyOwner/role-based access is standard. This is not a 2016 contract.
- Action: Skip immediately.

BANNED_PATTERN_005: TIMESTAMP_MANIPULATION
- Reason: PoS blocks are slot-based (12s). Proposers cannot manipulate timestamps.
- Action: Skip immediately. Only investigate slot/epoch boundary effects.

BANNED_PATTERN_006: SIMPLE_OVERFLOW_UNDERFLOW
- Reason: Solidity 0.8+ has checked math. unchecked blocks are rare and intentional.
- Action: Skip immediately unless analyzing unchecked assembly.

BANNED_PATTERN_007: DONATION_ATTACKS_ON_VAULTS
- Reason: Modern vaults use internal accounting, not balanceOf(). ERC4626 has virtual assets.
- Action: Skip immediately.

BANNED_PATTERN_008: SIMPLE_FRONTRUNNING
- Reason: MEV protection (Flashbots, private mempools) is standard. Not novel.
- Action: Skip immediately unless part of a complex multi-step sequence.

BANNED_PATTERN_009: KNOWN_TOKEN_QUIRKS_WITHOUT_CONTEXT
- Reason: Fee-on-transfer, rebasing, pausable tokens are documented. Protocols handle them.
- Action: Only investigate if protocol claims to support these but doesn't.

BANNED_PATTERN_010: ORACLE_MANIPULATION_WITHOUT_COST_MODEL
- Reason: "Oracle can be manipulated" is useless without proving cost < profit.
- Action: Only proceed if you have computed manipulation cost vs. extractable value.
```

**Enforcement**: Before creating any hypothesis, verify it does not match a BANNED_PATTERN. If it does, discard it and move on. Do not log it. Do not discuss it.

---

# GLOBAL RULES

## Rule 1: E3-Only Stop Condition

**NEVER STOP until one of these conditions is met:**
1. **SUCCESS**: A validated, economically feasible exploit exists with:
   - Fork execution proof
   - Net profit > $10,000 USD (after gas, fees, market impact)
   - Minimum attacker tier identified
   - Robustness verified under perturbation
2. **EXTERNAL INTERRUPT**: Emit `resume_pack.md` and continue next session.

## Rule 2: Protocol-Complete Analysis

**Every contract MUST be analyzed in its full protocol context:**
- Map to parent protocol (Uniswap, Aave, Curve, etc.)
- Identify all related contracts (factory, router, oracle, token, governance)
- Understand protocol state machine and phase transitions
- Build cross-contract call graphs
- Map all external dependencies (oracles, bridges, other protocols)

**Single-contract analysis is insufficient.** Exploits in mature protocols emerge from cross-contract interactions, not single-function bugs.

## Rule 3: Evidence-First Progress

- Progress requires **experiments** with **measured deltas**
- Every iteration MUST append to `experiments.jsonl`
- Every experiment MUST include: `convergence_delta`, `net_profit`, `attacker_tier`, `gas_cost`
- Artifact completion without experiments is NOT progress

## Rule 4: Intelligence Routing

Use external intelligence sources for every contract:
- **DeBank API**: Asset holdings, protocol exposure, historical activity
- **Traverse.tools**: Cross-contract relationships, protocol topology
- **ItyFuzz**: Intelligent coverage-guided fuzzing when parameter space is large
- **Chain state**: Direct RPC queries for current balances, rates, and oracle prices

---

# PART I: TARGET INTELLIGENCE GATHERING

## 1.1 Contract-to-Protocol Mapping (Mandatory)

Before analyzing any contract, establish its protocol context:

```
FOR EACH CONTRACT ADDRESS:

STEP 1: Identify Protocol
  - Query DeBank: GET /v1/user/protocol_list?id=<address>
  - Query Traverse: Get contract relationships
  - Check deployment factory (CREATE2 patterns, proxy admin)
  - Read contract name/symbol/comments

STEP 2: Map Related Contracts
  - Factory contracts (who deployed this?)
  - Router contracts (how do users interact?)
  - Oracle contracts (price feeds, TWAP sources)
  - Token contracts (underlying assets, receipt tokens)
  - Governance contracts (timelock, multisig, DAO)
  - Peripheral contracts (rewards, staking, bridges)

STEP 3: Build Protocol State Machine
  - What are the major phases? (deposit, active, withdrawal)
  - What triggers phase transitions?
  - Where does value flow between phases?
  - What invariants must hold across transitions?

STEP 4: Assess Extractable Value
  - Query DeBank: GET /v1/user/total_balance?id=<address>
  - Check token balances directly via RPC
  - Identify claimable rewards, pending withdrawals
  - Calculate TVL at risk

OUTPUT: protocol_context.json with all mappings
```

## 1.2 Intelligence Source Integration

### DeBank Cloud API

```
BASE_URL: https://pro-openapi.debank.com
ACCESS_KEY: <from rpc-etherscan.md>

ENDPOINTS:
- /v1/user/total_balance?id=<address>     # Total value held
- /v1/user/token_list?id=<address>        # Token breakdown
- /v1/user/protocol_list?id=<address>     # Protocol exposure
- /v1/user/history_list?id=<address>      # Transaction history
- /v1/protocol/list                        # All known protocols
- /v1/token?id=<address>&chain_id=eth     # Token metadata

USE CASES:
- Identify high-value targets (TVL > $1M)
- Map protocol relationships
- Understand asset composition
- Track historical activity patterns
```

### Traverse.tools

```
PURPOSE: Cross-contract relationship mapping

USE FOR:
- Building call graphs from on-chain data
- Identifying protocol boundaries
- Finding commonly called contracts
- Mapping upgrade proxy relationships
- Discovering factory-child patterns

INTEGRATION:
- Feed contract addresses from contracts.txt
- Export relationship graphs as JSON
- Cross-reference with DeBank protocol data
```

### ItyFuzz (Intelligent Fuzzing)

```
DOCUMENTATION: https://docs.ityfuzz.rs/

WHEN TO USE:
- Parameter spaces too large for manual search
- Complex invariants requiring coverage-guided exploration
- Multi-step sequences with many permutations
- When static analysis suggests an issue but parameters are unclear

CONFIGURATION:
- Set up Foundry integration
- Define invariants as ItyFuzz assertions
- Configure corpus with protocol-specific seeds
- Run with coverage tracking

DO NOT USE FOR:
- Simple function probing (use Foundry directly)
- Known exploit patterns (test manually first)
- Contracts without source code
```

## 1.3 Triage Decision Matrix

```
IMMEDIATELY SKIP (do not analyze):
- TVL < $100,000 (not worth compute)
- Timelock > 1 year on all funds
- Multisig with 3+ owners for all operations
- Bridge contracts requiring ZK proofs
- Pure view/query contracts with no state changes
- Abandoned contracts (no activity > 6 months, no rewards)

PRIORITIZE (analyze first):
- TVL > $10M
- Recent activity (< 7 days)
- Complex state machines (vaults, lending, staking)
- Cross-protocol integrations
- Novel mechanism designs
- Upgradeable with recent implementations

DEPRIORITIZE (analyze later):
- Simple token transfers
- Crowdsale contracts (usually finished)
- NFT contracts (value in tokens, not contract)
- Pure governance (no direct value extraction)
```

---

# PART II: SEMANTIC MODEL CONSTRUCTION

## 2.1 The Three Graphs (Protocol-Level)

### Graph A: Cross-Contract Call Graph

```json
{
  "node_schema": {
    "contract": "0x...",
    "protocol": "Aave V3",
    "role": "Pool|Oracle|Token|Router|Governance",
    "functions": [
      {
        "selector": "0x...",
        "name": "supply(address,uint256,address,uint16)",
        "visibility": "external",
        "state_changes": ["userBalance", "totalSupply"],
        "external_calls": ["IERC20.transferFrom", "Oracle.getPrice"],
        "value_flow": "user -> pool"
      }
    ]
  },
  "edge_schema": {
    "source": "Pool.supply",
    "target": "Oracle.getAssetPrice",
    "call_type": "STATICCALL",
    "data_flow": ["assetAddress"],
    "timing": "synchronous",
    "failure_mode": "revert propagates"
  }
}
```

### Graph B: Value Flow Graph

```json
{
  "node_schema": {
    "address": "0x...",
    "type": "protocol|user|external|treasury|rewards",
    "assets": {
      "ETH": "1000000000000000000",
      "USDC": "5000000000"
    },
    "claimable": {
      "rewards": "500000000000000000"
    }
  },
  "edge_schema": {
    "type": "transfer|mint|burn|claim|stake|unstake",
    "asset": "0x...",
    "amount_derivation": "input|computed|oracle_dependent",
    "authority": "msg.sender|approval|signature",
    "timing": "immediate|delayed|epoch_based"
  }
}
```

### Graph C: Constraint/Invariant Graph

```json
{
  "invariant_schema": {
    "id": "INV-001",
    "protocol": "Aave V3",
    "scope": "global|per_user|per_asset",
    "predicate": "totalDebt <= totalCollateral * ltv",
    "enforcement": "checked in liquidation",
    "violation_consequence": "bad_debt|liquidation|revert"
  },
  "constraint_edge": {
    "invariant": "INV-001",
    "depends_on": ["Oracle.getAssetPrice", "Pool.getUserAccountData"],
    "attack_surface": "oracle staleness|price manipulation"
  }
}
```

## 2.2 Protocol State Machine

```
FOR EACH PROTOCOL:

DEFINE PHASES:
  - DEPOSIT_PHASE: User adds assets, receives shares/tokens
  - ACTIVE_PHASE: Assets earn yield, can be borrowed against
  - WITHDRAWAL_PHASE: User exits, receives assets
  - LIQUIDATION_PHASE: Unhealthy positions closed
  - EMERGENCY_PHASE: Protocol paused, limited operations

FOR EACH PHASE TRANSITION:
  - Trigger conditions (who/what can trigger)
  - State changes (what variables update)
  - Value flows (where do assets move)
  - Reentrancy windows (external calls during transition)
  - Timing constraints (timelocks, epochs, cooldowns)

IDENTIFY INCONSISTENCY WINDOWS:
  - Where is state temporarily inconsistent?
  - What view functions read during inconsistency?
  - Can an attacker exploit the inconsistency?
```

---

# PART III: HYPOTHESIS GENERATION (Complex Only)

## 3.1 Valid Hypothesis Categories

Only these categories are valid for mature protocols:

```
CATEGORY: CROSS_CONTRACT_SEMANTIC_MISMATCH
- Two contracts interpret shared state differently
- Arbitrage opportunity between interpretations
- Example: Pool A reads stale oracle, Pool B reads fresh

CATEGORY: ACCOUNTING_DIVERGENCE_OVER_TIME
- Internal ledger slowly diverges from actual balances
- Divergence accumulates across many operations
- Harvesting divergence is profitable after threshold

CATEGORY: ORACLE_ECONOMIC_ATTACK
- Cost to manipulate oracle < profit from manipulation
- Requires full cost modeling (liquidity depth, TWAP window)
- Must prove feasibility with real mainnet liquidity

CATEGORY: TIMING_WINDOW_EXPLOITATION
- Protocol assumes certain timing guarantees
- Attacker can create conditions where guarantees fail
- Example: Stale reward rate during epoch boundary

CATEGORY: CROSS_PROTOCOL_COMPOSITION
- Protocol A interacts with Protocol B
- Combined behavior creates unintended state
- Neither protocol is buggy alone, only together

CATEGORY: GOVERNANCE_MANIPULATION
- Flash loan voting power (if not protected)
- Proposal timing attacks
- Requires economic model of voting power cost

CATEGORY: LIQUIDATION_MECHANICS
- Bad debt creation under extreme conditions
- Liquidation cascade scenarios
- Oracle delay exploitation in liquidations
```

## 3.2 Hypothesis Schema

```yaml
hypothesis_id: H-001
protocol: Aave V3
category: CROSS_CONTRACT_SEMANTIC_MISMATCH
status: E0 # E0=idea, E1=constraints defined, E2=witness found, E3=validated

target_state:
  description: "Oracle price stale by 2+ hours while Pool still allows borrows"
  predicate: "oracle.timestamp < block.timestamp - 7200"
  reachability: "external" # external=wait for condition, internal=we can create it

attacker_model:
  minimum_tier: TIER_2_MEV_SEARCHER
  ordering_power: medium
  flash_liquidity:
    max_eth: 100000
    sources: [aave_v3, balancer]
  multi_block: false

economic_model:
  gross_profit_estimate: "price_delta * borrow_amount"
  gas_cost_estimate: "500000 * gas_price"
  oracle_manipulation_cost: "N/A - waiting for natural staleness"
  flash_loan_fees: "0.05% of borrowed"
  market_impact: "depends on exit liquidity"

constraints:
  - "oracle.price != spot_price"
  - "oracle.timestamp + heartbeat < block.timestamp"
  - "pool.paused == false"
  - "attacker.collateral >= borrow_amount * ltv"

solver_approach:
  method: monitor_and_execute
  monitoring_criteria: "oracle staleness > 2 hours"
  execution_sequence: [deposit_collateral, borrow_max, swap_to_spot, repay_partial]
```

---

# PART IV: EXPERIMENTATION ENGINE

## 4.1 Experiment Types

```
TYPE: FORK_PROBE
- Create mainnet fork at current block
- Query state variables
- Test function calls
- OUTPUT: state_snapshot.json

TYPE: SEQUENCE_SEARCH
- Define action space (functions that can be called)
- Search for sequences that violate invariants
- Use ItyFuzz for coverage-guided search
- OUTPUT: candidate_sequences.json

TYPE: PARAMETER_OPTIMIZATION
- Given a promising sequence, optimize parameters
- Maximize net_profit
- Use Bayesian optimization or grid search
- OUTPUT: optimal_params.json

TYPE: ECONOMIC_VALIDATION
- Execute sequence on fork
- Calculate exact costs (gas, fees, impact)
- Verify net_profit > threshold
- OUTPUT: economic_report.json
```

## 4.2 Experiment Logging (Mandatory)

```json
// experiments.jsonl - append only
{
  "timestamp": "2026-02-03T12:00:00Z",
  "hypothesis_id": "H-001",
  "experiment_type": "sequence_search",
  "fork_block": 21000000,
  "inputs": {
    "sequence": ["deposit", "borrow", "swap"],
    "params": {"deposit_amount": "1000000000000000000"}
  },
  "outputs": {
    "success": true,
    "gross_profit": "50000000000000000",
    "gas_used": 450000,
    "gas_cost": "9000000000000000",
    "net_profit": "41000000000000000"
  },
  "attacker_tier": "TIER_1",
  "ordering_power": "weak",
  "convergence_delta": {
    "metric": "net_profit",
    "previous": 0,
    "current": 41000000000000000,
    "delta": 41000000000000000
  },
  "decision_id": "D-2026-02-03-001"
}
```

## 4.3 Convergence Requirements

Every experiment MUST show progress on at least one metric:

```
CONVERGENCE METRICS:
- net_profit: Higher profit than previous attempt
- feasibility: Lower attacker tier requirement
- robustness: Profit maintained under perturbation
- reachability: New target state reached
- constraint_tightening: Narrower parameter bounds

IF convergence_delta == 0:
  - Expand variable ranges
  - Add new actions to sequence
  - Try different hypothesis
  - DO NOT repeat same experiment
```

---

# PART V: VALIDATION PROTOCOL

## 5.1 Pre-Validation Checklist

Before claiming any finding:

```
□ Hypothesis does NOT match any BANNED_PATTERN
□ Protocol context fully mapped (all related contracts identified)
□ Economic model complete (all costs accounted)
□ Net profit > $10,000 USD
□ Attacker tier is realistic (TIER_0 to TIER_3)
□ No privileged roles assumed (owner, admin, pauser)
□ Sequence executed successfully on mainnet fork
□ Result is deterministic (same outcome on repeated runs)
□ Robustness verified (profit survives ±20% perturbations)
```

## 5.2 Economic Validation Requirements

```
REQUIRED CALCULATIONS:

1. Gross Profit
   - Sum of all assets gained by attacker
   - Converted to common denomination (USD or ETH)

2. Costs
   - Gas: gasUsed * baseFee (current mainnet)
   - Flash Loan Fees: 0.05-0.09% depending on source
   - Protocol Fees: swap fees, withdrawal fees, etc.
   - Market Impact: simulate with real liquidity
   - MEV Cost: priority fee if ordering required

3. Net Profit
   net_profit = gross_profit - sum(all_costs)

4. Robustness
   - Recalculate with gas_price + 50%
   - Recalculate with liquidity - 20%
   - Recalculate with timing + 1 block
   - All must remain profitable

5. Attacker Requirements
   - Minimum tier needed
   - Capital requirements
   - Timing requirements
   - Ordering requirements
```

---

# PART VI: TOOLING INTEGRATION

## 6.1 Foundry Fork Testing

```solidity
// Standard test setup
contract ExploitTest is Test {
    function setUp() public {
        // Use RPC from rpc-etherscan.md
        vm.createSelectFork("https://mainnet.infura.io/v3/<key>", block.number);
    }

    function test_exploit() public {
        // Record initial state
        uint256 attackerBefore = address(this).balance;

        // Execute exploit sequence
        // ...

        // Verify profit
        uint256 attackerAfter = address(this).balance;
        uint256 grossProfit = attackerAfter - attackerBefore;
        uint256 gasCost = tx.gasprice * gasleft(); // approximate

        console.log("Gross Profit:", grossProfit);
        console.log("Gas Cost:", gasCost);
        console.log("Net Profit:", grossProfit - gasCost);

        // Assert profitability
        assertTrue(grossProfit > gasCost + 10 ether, "Not profitable");
    }
}
```

## 6.2 ItyFuzz Integration

```toml
# foundry.toml additions for ItyFuzz
[fuzz]
runs = 10000
max_test_rejects = 100000

[invariant]
runs = 1000
depth = 50
fail_on_revert = false

# ItyFuzz specific
[ityfuzz]
enabled = true
corpus_dir = "./corpus"
coverage_report = true
```

## 6.3 DeBank API Integration

```python
# Example: Get protocol context for a contract
import requests

DEBANK_KEY = "e0f9f5b495ec8924d0ed905a0a68f78c050fdf54"
BASE_URL = "https://pro-openapi.debank.com"

def get_protocol_context(address: str) -> dict:
    headers = {"AccessKey": DEBANK_KEY}

    # Get total balance
    balance = requests.get(
        f"{BASE_URL}/v1/user/total_balance",
        params={"id": address},
        headers=headers
    ).json()

    # Get protocol list
    protocols = requests.get(
        f"{BASE_URL}/v1/user/protocol_list",
        params={"id": address},
        headers=headers
    ).json()

    # Get token breakdown
    tokens = requests.get(
        f"{BASE_URL}/v1/user/token_list",
        params={"id": address, "is_all": True},
        headers=headers
    ).json()

    return {
        "address": address,
        "total_usd_value": balance.get("total_usd_value", 0),
        "protocols": protocols,
        "tokens": tokens
    }
```

---

# PART VII: DECISION ENGINE

## 7.1 Skill Routing

```
SKILL: protocol-mapper
  WHEN: New contract address, no protocol context
  DO: Build protocol context using DeBank, Traverse, RPC
  OUTPUT: protocol_context.json

SKILL: semantic-modeler
  WHEN: Protocol context exists, no graphs
  DO: Build call graph, value flow graph, constraint graph
  OUTPUT: graphs/*.json

SKILL: hypothesis-generator
  WHEN: Graphs exist, no active hypotheses
  DO: Generate hypotheses (NOT matching BANNED_PATTERNS)
  OUTPUT: hypotheses/*.yaml

SKILL: experiment-runner
  WHEN: Active hypothesis, needs experiments
  DO: Run fork tests, log results
  OUTPUT: experiments.jsonl

SKILL: validator
  WHEN: Promising experiment results (profit > threshold)
  DO: Validate economic model, create PoC
  OUTPUT: findings/*.json
```

## 7.2 Continuous Loop

```
WHILE NOT (E3_found OR external_interrupt):

    # Check for banned patterns
    FOR each active_hypothesis:
        IF matches_banned_pattern(hypothesis):
            discard(hypothesis)
            continue

    # Run decision engine
    IF no_protocol_context:
        invoke(protocol-mapper)
    ELIF no_graphs:
        invoke(semantic-modeler)
    ELIF no_hypotheses:
        invoke(hypothesis-generator)
    ELIF hypotheses_need_experiments:
        invoke(experiment-runner)
    ELIF promising_results:
        invoke(validator)
    ELSE:
        # Stall recovery
        expand_constraints()
        generate_new_hypotheses()

    # Check convergence
    IF last_iteration.convergence_delta == 0:
        force_constraint_expansion()

    # Update focus
    update_focus_md()

    # Log decision
    log_decision_trace()
```

---

# PART VIII: ARTIFACT MANIFEST

```
WORKSPACE:
├── contracts.txt              # Target contract addresses
├── rpc-etherscan.md          # API keys and endpoints (local only)
├── CLAUDE.md                  # This file
├── PLANS.md                   # Decision engine specification
├── focus.md                   # Current goal and next action
├── resume_pack.md             # Checkpoint for continuation
│
├── intelligence/
│   ├── protocol_contexts/     # Per-contract protocol mappings
│   └── debank_snapshots/      # Cached DeBank responses
│
├── graphs/
│   ├── call_graphs/           # Cross-contract call graphs
│   ├── value_flows/           # Asset movement graphs
│   └── constraints/           # Invariant graphs
│
├── hypotheses/
│   └── *.yaml                 # Active hypotheses
│
├── experiments.jsonl          # All experiment results (append-only)
├── decision_trace.jsonl       # Decision log (append-only)
│
├── exploit_test/
│   ├── foundry.toml           # Foundry config
│   ├── test/                  # Foundry test files
│   └── src/                   # Helper contracts
│
├── findings/
│   └── *.json                 # Validated findings
│
└── final_report.md            # E3 summary (only on success)
```

---

# APPENDIX A: Attacker Tiers

```
TIER_0: Basic User
  - Single EOA
  - No flash loans
  - No ordering power
  - Threshold: $100 profit

TIER_1: DeFi User
  - Multiple addresses
  - Single-source flash loans
  - Private mempool (Flashbots Protect)
  - Threshold: $1,000 profit

TIER_2: MEV Searcher
  - Unlimited addresses
  - Combined flash loans
  - Backrunning capability
  - Multi-block possible
  - Threshold: $10,000 profit

TIER_3: Sophisticated Actor
  - Builder relationships
  - Large capital
  - Coordinated multi-block
  - Threshold: $100,000 profit
```

---

# APPENDIX B: Quick Reference

```
ETHERSCAN V2 API:
Base: https://api.etherscan.io/v2/api
Params: chainid=1&module=contract&action=getsourcecode&address=<addr>&apikey=<key>
Key: 5UWN6DNT7UZCEJYNE3J6FCVAWH4QJW255K

RPC ENDPOINTS:
Mainnet: https://mainnet.infura.io/v3/bfc7283659224dd6b5124ebbc2b14e2c
Alchemy: https://eth-mainnet.g.alchemy.com/v2/pLXdY7rYRY10SH_UTLBGH

DEBANK API:
Base: https://pro-openapi.debank.com
Key: e0f9f5b495ec8924d0ed905a0a68f78c050fdf54

ITYFUZZ DOCS:
https://docs.ityfuzz.rs/

TRAVERSE:
https://traverse.tools/
```

---

# APPENDIX C: What This System Does NOT Do

```
- Does NOT look for trivial bugs (first depositor, uninitialized proxy)
- Does NOT analyze single contracts in isolation
- Does NOT generate hypotheses without protocol context
- Does NOT claim findings without economic validation
- Does NOT stop without E3 evidence
- Does NOT waste compute on low-TVL contracts
- Does NOT ignore cross-protocol interactions
- Does NOT assume oracles can be "manipulated" without cost modeling
```

---

END OF CLAUDE.md v4.0

This system is designed for discovering complex, economically feasible exploits
in mature, heavily-audited protocols. It requires protocol-complete analysis,
rigorous economic validation, and continuous evidence-based progress.

The only valid outcome is E3: a validated exploit with measurable profit.
