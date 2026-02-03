# PLANS.md v4.0 — Autonomous Exploit Discovery Decision Engine
## Protocol-Complete • Evidence-Only • Zero Trivia

---

# EXECUTION PHILOSOPHY

This engine operates autonomously until E3 (validated exploit) or external interrupt.
Every decision must advance toward economically feasible value extraction.
No narrative progress. No trivial patterns. No single-contract isolation.

---

# DECISION POLICY (Fully Autonomous)

When multiple valid options exist, decide automatically using this priority order:

1. **Banned Pattern Filter** - Immediately discard anything matching CLAUDE.md BANNED_PATTERNS
2. **TVL Threshold** - Skip contracts with < $100,000 extractable value
3. **Convergence Delta** - Choose option with highest measurable progress toward E3
4. **Economic Feasibility** - Prefer hypotheses with clearer profit paths
5. **Cross-Contract Coverage** - Prioritize protocol-wide analysis over single-contract
6. **Novelty** - Avoid repeating same hypothesis/experiment
7. **Attacker Tier** - Prefer lower-tier attacks (more realistic)

---

# BANNED PATTERN ENFORCEMENT (Hard Stop)

Before ANY hypothesis generation or experiment:

```python
BANNED_PATTERNS = [
    "FIRST_DEPOSITOR",
    "EMPTY_VAULT",
    "UNINITIALIZED_PROXY",
    "IMPLEMENTATION_TAKEOVER",
    "SIMPLE_REENTRANCY",
    "BASIC_ACCESS_CONTROL",
    "TIMESTAMP_MANIPULATION",
    "SIMPLE_OVERFLOW",
    "DONATION_ATTACK",
    "SIMPLE_FRONTRUNNING",
    "TOKEN_QUIRKS_WITHOUT_CONTEXT",
    "ORACLE_MANIPULATION_WITHOUT_COST"
]

def check_banned(hypothesis):
    for pattern in BANNED_PATTERNS:
        if pattern in hypothesis.category or pattern in hypothesis.description:
            return True  # REJECT IMMEDIATELY
    return False

# Enforcement: If check_banned(h) == True:
#   - Do NOT log hypothesis
#   - Do NOT run experiments
#   - Do NOT discuss in reasoning
#   - Move to next candidate immediately
```

---

# SKILL ROUTING TABLE

| Condition | Skill | Input | Output |
|-----------|-------|-------|--------|
| New contract, no protocol context | protocol-mapper | contract address | intelligence/protocol_contexts/*.json |
| Protocol context exists, no graphs | semantic-modeler | protocol_context.json | graphs/*.json |
| Graphs exist, no hypotheses | hypothesis-generator | graphs/*.json | hypotheses/*.yaml |
| Hypothesis exists, needs experiments | experiment-runner | hypothesis.yaml | experiments.jsonl |
| Promising results (profit > $10K) | validator | experiments.jsonl | findings/*.json |
| E3 achieved | report-builder | findings/*.json | final_report.md |

---

# DECISION ENGINE RULES

Execute the first matching rule:

```
RULE 0: Banned Pattern Gate
  IF hypothesis matches BANNED_PATTERNS
  THEN discard(hypothesis), continue
  NEVER proceed with banned patterns

RULE 1: TVL Gate
  IF target_contract.tvl < $100,000
  THEN skip_contract(), continue
  REASON: Not worth compute resources

RULE 2: Protocol Context Missing
  IF contract has no protocol_context.json
  THEN invoke skill: protocol-mapper
  INPUTS: contract address
  OUTPUTS: protocol_contexts/<address>.json

RULE 3: Cross-Contract Graphs Missing
  IF protocol_context exists BUT no graphs/*.json
  THEN invoke skill: semantic-modeler
  INPUTS: protocol_context.json
  OUTPUTS: graphs/call_graph.json, graphs/value_flow.json, graphs/constraints.json

RULE 4: No Active Hypotheses
  IF graphs exist BUT hypotheses/*.yaml is empty
  THEN invoke skill: hypothesis-generator
  INPUTS: graphs/*.json
  OUTPUTS: hypotheses/*.yaml (only valid categories)
  CONSTRAINT: Must NOT generate BANNED_PATTERNS

RULE 5: Hypothesis Needs Experiments
  IF hypothesis.status < E2 AND experiments.jsonl has no entries for hypothesis
  THEN invoke skill: experiment-runner
  INPUTS: hypothesis.yaml
  OUTPUTS: experiments.jsonl entries with convergence_delta

RULE 6: Convergence Stall
  IF last 3 experiments have convergence_delta == 0
  THEN force_expansion():
    - Expand variable ranges (2x)
    - Add cross-contract actions
    - Try different hypothesis category
    - Lower profit threshold temporarily for exploration

RULE 7: Promising Results
  IF experiment.net_profit > $10,000
  THEN invoke skill: validator
  INPUTS: experiment data
  OUTPUTS: findings/*.json with full economic validation

RULE 8: E3 Achieved
  IF finding.validated == true AND finding.net_profit > threshold
  THEN invoke skill: report-builder
  OUTPUTS: final_report.md
  STOP (SUCCESS)

RULE 9: External Interrupt
  IF session ending without E3
  THEN emit resume_pack.md
  CONTINUE next session
```

---

# PROTOCOL-MAPPER SKILL

```
PURPOSE: Build complete protocol context for a contract

INPUTS:
- Contract address from contracts.txt

PROCEDURE:
1. Query DeBank API for protocol relationships:
   GET /v1/user/protocol_list?id=<address>
   GET /v1/user/total_balance?id=<address>
   GET /v1/user/token_list?id=<address>

2. Fetch source code:
   - Sourcify v2 first: /v2/api/sourcify/sources/<address>
   - Fallback: Etherscan v2 API

3. Identify related contracts:
   - Parse imports and external calls from source
   - Query Traverse.tools for call graph
   - Map: Factory, Router, Oracle, Token, Governance

4. Check TVL threshold:
   IF total_value < $100,000: mark as SKIP

OUTPUTS:
- intelligence/protocol_contexts/<address>.json

SCHEMA:
{
  "address": "0x...",
  "protocol_name": "Aave V3",
  "tvl_usd": 1000000,
  "skip_reason": null,
  "related_contracts": {
    "factory": "0x...",
    "oracle": "0x...",
    "router": "0x...",
    "tokens": ["0x..."]
  },
  "source_available": true,
  "debank_data": {...}
}
```

---

# SEMANTIC-MODELER SKILL

```
PURPOSE: Build cross-contract semantic model

INPUTS:
- protocol_context.json

PROCEDURE:
1. Parse source code for all related contracts
2. Build call graph:
   - External calls between contracts
   - Callback patterns
   - Oracle dependencies
3. Build value flow graph:
   - Asset movements (transfer, mint, burn)
   - Authority chains (approvals, roles)
   - Timing constraints (timelocks, epochs)
4. Build constraint graph:
   - Protocol invariants
   - Access control predicates
   - Economic bounds

OUTPUTS:
- graphs/call_graph.json
- graphs/value_flow.json
- graphs/constraints.json

VALIDATION:
- Call graph must include ALL external calls
- Value flow must trace ALL asset movements
- Constraints must include ALL require() statements
```

---

# HYPOTHESIS-GENERATOR SKILL

```
PURPOSE: Generate valid hypotheses (NO BANNED PATTERNS)

INPUTS:
- graphs/*.json

VALID CATEGORIES ONLY:
1. CROSS_CONTRACT_SEMANTIC_MISMATCH
2. ACCOUNTING_DIVERGENCE_OVER_TIME
3. ORACLE_ECONOMIC_ATTACK (with cost model)
4. TIMING_WINDOW_EXPLOITATION
5. CROSS_PROTOCOL_COMPOSITION
6. GOVERNANCE_MANIPULATION
7. LIQUIDATION_MECHANICS

PROCEDURE:
1. Analyze call graph for cross-contract inconsistencies
2. Analyze value flow for divergence opportunities
3. Analyze constraints for boundary conditions
4. Generate hypotheses ONLY in valid categories
5. Verify each hypothesis does NOT match BANNED_PATTERNS
6. Estimate economic feasibility for each

OUTPUTS:
- hypotheses/*.yaml

HARD CONSTRAINT:
IF hypothesis.category in BANNED_PATTERNS:
    DO NOT OUTPUT
    DO NOT LOG
    DISCARD IMMEDIATELY
```

---

# EXPERIMENT-RUNNER SKILL

```
PURPOSE: Run experiments with convergence tracking

INPUTS:
- hypothesis.yaml

PROCEDURE:
1. Create mainnet fork at current block
2. Set up Foundry test environment
3. Execute hypothesis sequence
4. Measure all costs (gas, fees, impact)
5. Calculate net profit
6. Calculate convergence_delta vs previous experiment

IF using ItyFuzz:
- Define invariant assertions
- Configure corpus with protocol seeds
- Run coverage-guided search
- Extract minimum witness

OUTPUTS:
- experiments.jsonl entry with:
  - hypothesis_id
  - experiment_type
  - fork_block
  - inputs/outputs
  - gross_profit
  - gas_cost
  - net_profit
  - attacker_tier
  - convergence_delta

CONVERGENCE REQUIREMENT:
Every experiment MUST have convergence_delta > 0 on at least one metric:
- net_profit increased
- attacker_tier decreased
- robustness improved
- new state reached

IF convergence_delta == 0 for 3 consecutive experiments:
    TRIGGER stall recovery
```

---

# VALIDATOR SKILL

```
PURPOSE: Validate economic feasibility of findings

INPUTS:
- experiments.jsonl with promising results

CHECKLIST:
□ NOT a BANNED_PATTERN
□ Protocol context complete
□ All related contracts identified
□ Economic model complete:
  □ Gross profit calculated
  □ Gas costs calculated
  □ Flash loan fees calculated
  □ Protocol fees calculated
  □ Market impact simulated
□ Net profit > $10,000
□ Attacker tier realistic (TIER_0 to TIER_3)
□ No privileged roles required
□ Deterministic (same result on repeated runs)
□ Robust (profit survives ±20% perturbations)

PROCEDURE:
1. Re-execute on fresh fork
2. Verify all calculations
3. Test robustness with perturbations
4. Document minimum requirements

OUTPUTS:
- findings/<hypothesis_id>.json

SCHEMA:
{
  "finding_id": "F-001",
  "hypothesis_id": "H-001",
  "protocol": "...",
  "category": "...",
  "gross_profit_usd": 50000,
  "costs": {
    "gas": 500,
    "flash_loan_fees": 100,
    "protocol_fees": 200,
    "market_impact": 500
  },
  "net_profit_usd": 48700,
  "attacker_tier": "TIER_2",
  "robustness": {
    "gas_+50%": "profitable",
    "liquidity_-20%": "profitable",
    "timing_+1block": "profitable"
  },
  "poc_file": "test/F001_Exploit.t.sol",
  "validated": true
}
```

---

# TOOL INTEGRATION

## DeBank API

```
BASE: https://pro-openapi.debank.com
KEY: e0f9f5b495ec8924d0ed905a0a68f78c050fdf54

WHEN TO USE:
- Protocol identification (protocol-mapper)
- TVL assessment (triage)
- Asset composition (value flow)

ENDPOINTS:
- /v1/user/total_balance?id=<addr>
- /v1/user/protocol_list?id=<addr>
- /v1/user/token_list?id=<addr>
```

## Traverse.tools

```
PURPOSE: Cross-contract relationship mapping

WHEN TO USE:
- Building call graphs (semantic-modeler)
- Identifying protocol boundaries
- Finding factory-child patterns

INTEGRATION:
- Query contract relationships
- Export as JSON
- Merge with DeBank data
```

## ItyFuzz

```
DOCS: https://docs.ityfuzz.rs/

WHEN TO USE:
- Large parameter spaces (experiment-runner)
- Complex invariant testing
- Multi-step sequence search

CONFIGURATION:
- Foundry integration
- Coverage-guided mode
- Protocol-specific seeds
```

## Etherscan V2 API

```
BASE: https://api.etherscan.io/v2/api
KEY: 5UWN6DNT7UZCEJYNE3J6FCVAWH4QJW255K

WHEN TO USE:
- Source code fetch (fallback after Sourcify)
- ABI retrieval
- Transaction history

PARAMS:
- chainid=1 (mainnet)
- module=contract
- action=getsourcecode|getabi
```

---

# STOP CONDITIONS

```
SUCCESS (terminate):
- E3 finding with net_profit > $10,000
- Full economic validation passed
- PoC deterministic and robust

CHECKPOINT (continue next session):
- External interrupt
- Emit resume_pack.md with:
  - Current hypothesis state
  - Experiment progress
  - Next action

NEVER STOP FOR:
- "No bugs found" (this is never a valid conclusion)
- Coverage thresholds met
- Time elapsed
- Iterations completed
```

---

# CONTINUOUS LOOP PSEUDOCODE

```python
while True:
    # Load state
    focus = load("focus.md")
    hypotheses = load("hypotheses/*.yaml")
    experiments = load("experiments.jsonl")

    # Banned pattern enforcement
    hypotheses = [h for h in hypotheses if not check_banned(h)]

    # Decision engine
    if needs_protocol_context():
        run_skill("protocol-mapper")
    elif needs_graphs():
        run_skill("semantic-modeler")
    elif not hypotheses:
        run_skill("hypothesis-generator")
    elif hypotheses_need_experiments(hypotheses, experiments):
        run_skill("experiment-runner")
    elif has_promising_results(experiments):
        run_skill("validator")
    elif has_validated_finding():
        run_skill("report-builder")
        break  # SUCCESS
    else:
        # Stall recovery
        expand_constraints()
        generate_new_hypotheses()

    # Convergence check
    if stall_detected(experiments):
        force_expansion()

    # Update state
    update_focus()
    log_decision()

    # Checkpoint if interrupted
    if external_interrupt():
        emit_resume_pack()
        break
```

---

END OF PLANS.md v4.0
