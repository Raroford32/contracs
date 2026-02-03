# AGENTS.md v3.0 — Intelligence-Grade Counterexample Discovery System
## Maximum-Coverage Operating Manual for Novel Exploit Detection in Battle-Tested Smart Contract Protocols
*(Solver-driven • Feasibility-constrained • Evidence-only • Composition-first • 2026 Ethereum PoS Reality)*

---

# GLOBAL PRECEDENCE RULES (Override Everything)

## Override 1: E3-Only Stop Policy

**NEVER STOP until one of these conditions is met:**
1. **SUCCESS**: An E3-promoted scenario exists with measurable economic delta (net profit > feasibility threshold).
2. **EXTERNAL INTERRUPT**: Emit `resume_pack.md` and continue next session.

Coverage thresholds (PART VII) are **checkpoint-only**—they do not terminate the investigation.

## Override 2: Feasibility is Required for Findings, Not for Exploration

- A "finding" requires economic feasibility (net profit > costs under realistic conditions).
- An **infeasible counterexample** is still valuable as a solver signal—it guides constraint expansion.
- Never discard a witness just because it's infeasible; log it with feasibility analysis and use it to mutate hypotheses.

## Override 3: No Narrative Progress

- Progress requires **experiments** (fork reads, fuzz runs, falsifiers) with **measured deltas**.
- Artifact completion without experiments is not progress.
- Every iteration must append to `experiments.jsonl` or the iteration does not count.

## Override 3b: Continuous Convergence (No Stagnant Iterations)

- **Every iteration must measurably move closer to a valid exploit scenario.** At least one convergence metric must improve:
  - **mode_reachability**: new boundary mode reached or newly reachable path discovered
  - **feasibility**: higher net profit or lower cost for the same target
  - **constraint_tightening**: feasible region reduced (variables narrowed or new constraints added)
  - **search_space_reduction**: action space pruned or permutation coverage increased
- **Progress claims require `convergence_delta > 0`** in `experiments.jsonl`.
- Every experiment entry must include: `decision_id`, `ordering_power`, `liquidity_assumptions`, `gas_price_gwei`, `gross_profit`, `net_profit`, `robustness`, and `convergence_delta`.
- Decision-making must be logged to `memory/decision_trace.jsonl` with the scoring inputs used.

## Override 4: Purpose Lock + Memory Lock (Never Get Lost)

This system fails when it **forgets the goal** or loses the **working context** mid‑analysis. Prevent that with two non‑negotiable locks:

### Purpose Lock (goal cannot drift)

- The only mission is: **produce an E3‑promoted, economically feasible exploit counterexample on a fork**.
- Every action MUST be explainable as one of:
  1. **Improve semantic model** (boundary/graphs/state machine)
  2. **Improve solvability** (constraint programs, vars/constraints expansion)
  3. **Run experiments** (append to `experiments.jsonl`; try to produce witnesses)
  4. **Promote evidence** (candidate → minimized falsifier → E2/E3)
- **No orphan work rule**: If you cannot name the **next skill** and the **expected artifact delta**, you are drifting. Stop and rehydrate.

### Memory Lock (context cannot evaporate)

- `focus.md` is the single “working set pointer.” It MUST always state:
  - the invariant goal (E3)
  - the current target (protocol_name/chain_id/fork_block)
  - the active hypothesis (scenarioId/status/targetStateX)
  - the next skill + why
- When you feel lost (or after any long action), rehydrate in this order:
  1. `focus.md`
  2. `resume_pack.md`
  3. `boundary/manifest.json` + `deployment_snapshot.md`
  4. `hypothesis_ledger.md`
  5. tail `experiments.jsonl` + `questions.jsonl`
  6. `coverage/scoreboard.json`

## Override 5: Read These Sections First (Bootstrap Order)

For efficient operationalization, read sections in this order:
0. `focus.md` + `resume_pack.md` — restore goal + working context
1. **PART I** (Threat Model) — understand attacker envelope
2. **PART II** (Feasibility) — understand cost kernel
3. **PART XII** (Execution Rules) — understand quality gates
4. **SKILL ROUTING** (end of doc) — understand how to invoke skills
5. **CONTINUOUS QUESTION LOOP** (Section XIII) — understand how to drive discovery

---

# TARGET REALITY

**Heavily-audited, high-TVL, high-composition EVM protocols on Ethereum mainnet where:**
- Failures are **never** "one bad function"
- Exploits exist as **kernel contradictions** requiring **precondition machines** to reach
- Boundaries are **numeric/temporal** and must be **solved**, not guessed
- **Economic feasibility** separates theoretical violations from real exploits
- All asset types: ERC20, LP tokens, pool shares, protocol tokens, rebasing tokens, fee-on-transfer, native ETH, wrapped ETH, receipt tokens, debt tokens, synthetic assets

---

# PART I: THREAT MODEL AS EXECUTABLE SPECIFICATION

## 1.1 Attacker Capability Envelope (Parameterized Tiers)

The attacker is modeled as an **adaptive agent** with **configurable capability tiers**. Every finding must specify the **minimum attacker tier** required for execution.

### Capability Vector Schema

```json
{
  "attacker_model": {
    "tier_name": "TIER_2_MEV_SEARCHER",
    
    "identity": {
      "max_addresses": 10,
      "can_deploy_contracts": true,
      "contract_complexity": "arbitrary"
    },
    
    "ordering_power": {
      "level": "weak|medium|strong|builder",
      "weak": "no ordering guarantees, public mempool only",
      "medium": "can use flashbots protect, private mempool",
      "strong": "can reliably backrun specific txs",
      "builder": "can control full block ordering, include/exclude txs"
    },
    
    "flash_liquidity": {
      "max_eth": "100000",
      "max_usdc": "500000000",
      "max_dai": "500000000",
      "sources": ["aave_v3", "balancer", "uniswap_v3", "maker"],
      "can_combine_sources": true
    },
    
    "multi_block": {
      "enabled": true,
      "max_block_span": 10,
      "can_guarantee_inclusion": false,
      "twap_manipulation_window": 30
    },
    
    "market_impact": {
      "max_spot_move_percent": 5.0,
      "max_capital_for_manipulation": "10000000",
      "liquidity_model": "realistic_mainnet"
    },
    
    "timing": {
      "model": "ethereum_pos_slots",
      "slot_duration_seconds": 12,
      "can_miss_slots": false,
      "can_exploit_missed_slots": true
    }
  }
}
```

### Predefined Attacker Tiers

```
TIER_0_BASIC:
  - Single EOA, no flash loans, no ordering power
  - Public mempool only
  - Useful baseline for "anyone can exploit"

TIER_1_DEFI_USER:
  - Multiple addresses, basic flash loans (single source)
  - Flashbots Protect (private mempool)
  - Can sequence within single tx

TIER_2_MEV_SEARCHER:
  - Unlimited addresses, combined flash loans
  - Reliable backrunning via MEV-share/Flashbots
  - Multi-block strategies possible
  - Moderate market manipulation budget

TIER_3_SOPHISTICATED:
  - Builder-level ordering (or builder relationship)
  - Large capital for market manipulation
  - Can coordinate multi-block attacks
  - Can exploit timing across epochs

TIER_4_STATE_LEVEL:
  - Near-unlimited capital
  - Can influence multiple validators
  - Long-horizon attacks
  - (Theoretical upper bound, rarely realistic)
```

### Identity & Access Capabilities

```
CAPABILITY: IDENTITY_SYBIL
- Deploy unlimited helper contracts with arbitrary logic
- Control unlimited EOA addresses
- Execute from any msg.sender that is not explicitly privileged
- Interact as contract or EOA depending on what bypasses checks
- Use CREATE2 for deterministic address pre-computation
- Exploit tx.origin vs msg.sender discrepancies

CAPABILITY: CONTRACT_DEPLOYMENT
- Deploy arbitrary bytecode
- Deploy with predictable addresses (CREATE2)
- Deploy proxy patterns
- Deploy minimal proxies (clones)
```

### Execution Control Capabilities

```
CAPABILITY: CALL_SEQUENCING
- Call any public/external function with arbitrary inputs
- Call functions in any order within transactions
- Create arbitrary call depth
- Control gas forwarding patterns

CAPABILITY: REENTRANCY_INJECTION
- Direct reentrancy at external call points
- Indirect reentrancy through intermediary contracts
- Cross-function reentrancy (reenter different function)
- Cross-contract reentrancy
- Read-only reentrancy exploitation (see Section 1.2)

CAPABILITY: CALLBACK_EXPLOITATION
- ERC777 tokensReceived/tokensToSend hooks
- ERC721 onERC721Received callbacks
- ERC1155 onERC1155Received/onERC1155BatchReceived
- Uniswap V3 flash callback
- Balancer flash loan callback
- Custom protocol callbacks

CAPABILITY: RETURN_DATA_MANIPULATION
- Control return data from attacker-controlled contracts
- Exploit unchecked return values
- Exploit return data length assumptions
```

### Timing Capabilities (Ethereum PoS Correct)

```
CAPABILITY: TIMING_EXPLOITATION

ETHEREUM POS TIMING MODEL:
- Blocks arrive every 12 seconds (1 slot)
- Timestamps advance in 12-second increments
- Missed slots create gaps (timestamp jumps by 24s, 36s, etc.)
- NO arbitrary timestamp manipulation by proposers
- Proposer cannot backdate or significantly forward-date

ATTACKER TIMING POWERS:
1. Transaction Ordering Within Block:
   - Weak: No control, subject to builder ordering
   - Medium: Can use private mempools, some priority
   - Strong: Can reliably position tx relative to others
   - Builder: Full control of tx ordering in block

2. Multi-Block Orchestration:
   - Can sequence actions across multiple blocks
   - Can exploit TWAP windows that span blocks
   - Can wait for specific oracle update patterns
   - Can exploit epoch boundaries (32 slots = 6.4 minutes)

3. Missed Slot Exploitation:
   - Can observe missed slots
   - Can act on timestamp gaps
   - Can exploit staleness checks that assume 12s blocks

4. MEV Timing:
   - Can backrun oracle updates
   - Can backrun large trades
   - Can frontrun (with builder cooperation or private flow)
   - Can sandwich (requires strong ordering power)

WHAT ATTACKERS CANNOT DO:
- Arbitrarily set block.timestamp
- Create blocks faster than 12s
- Reorder finalized blocks
- Control multiple consecutive blocks (without validator collusion)
```

### Numeric & Precision Capabilities

```
CAPABILITY: NUMERIC_EXPLOITATION
- Use extreme values: 0, 1, 2, type(uint256).max, type(uint256).max - 1
- Exploit all decimal regimes: 0, 2, 6, 8, 18, 24+ decimals
- Target rounding boundaries and precision loss accumulation
- Exploit overflow/underflow in unchecked blocks
- Create division by zero or division by small number scenarios
- Exploit WAD/RAY/precision conversion errors
- Target first depositor and last withdrawer edge cases
- Exploit empty state transitions (totalSupply=0, totalAssets=0)
```

---

## 1.2 Corrected Static Context Semantics

```
STATICCALL SECURITY MODEL (CORRECTED):

WHAT STATICCALL ENFORCES:
- State writes revert (SSTORE, LOG*, CREATE*, SELFDESTRUCT)
- Cannot send ETH via CALL with value
- Context is genuinely read-only

WHAT STATICCALL DOES NOT PROTECT AGAINST:

1. Read-Only Reentrancy:
   - Attacker reenters during callback
   - Calls view functions that return stale/inconsistent state
   - Protocol makes decisions based on inconsistent reads
   - Example: Read share price mid-deposit, before accounting update

2. TOCTOU via View Functions:
   - Protocol reads state via view call
   - State changes between read and use
   - Decision based on stale data
   - Example: Check balance → (attacker moves funds) → act on stale balance

3. Return Data Manipulation:
   - Attacker-controlled contract returns arbitrary data from view calls
   - Protocol trusts return data without validation
   - Attacker can return malicious values

4. Oracle Read Manipulation:
   - Protocol reads oracle in static context
   - Attacker manipulates oracle between reads
   - Different parts of protocol see different prices

5. Cross-Contract State Assumptions:
   - Contract A calls Contract B.view()
   - Assumes B's state is consistent with A's
   - Attacker creates inconsistency before A acts

MODELING RULE:
When analyzing static calls, ask:
- What state is being read?
- Can that state change during the transaction?
- What decisions depend on the read value?
- Can an attacker influence the read value?
```

---

## 1.3 Asset Universe (Complete Taxonomy)

```
ASSET CLASS: NATIVE_ETH
- Direct balance via address.balance
- Transfer via CALL with value
- Wrap/unwrap with WETH
- Vulnerabilities: reentrancy on receive, gas limits

ASSET CLASS: ERC20_STANDARD
- balance, transfer, approve, transferFrom
- Vulnerabilities: approval race, return value handling

ASSET CLASS: ERC20_FEE_ON_TRANSFER
- Actual received < sent amount
- Protocol must track actual vs expected
- Vulnerabilities: accounting mismatch

ASSET CLASS: ERC20_REBASING
- Balance changes without transfer
- Share-based vs balance-based accounting
- Vulnerabilities: yield capture, share dilution

ASSET CLASS: ERC20_WITH_HOOKS (ERC777)
- tokensReceived/tokensToSend callbacks
- Vulnerabilities: reentrancy, callback ordering

ASSET CLASS: ERC721/ERC1155
- onReceived callbacks
- Batch operations
- Vulnerabilities: reentrancy, batch handling

ASSET CLASS: LP_TOKENS
- Represent pool shares
- Value tied to underlying reserves
- Vulnerabilities: share inflation, donation attacks

ASSET CLASS: DEBT_TOKENS
- Represent borrowed amounts
- Interest accrual
- Vulnerabilities: interest rate manipulation, liquidation

ASSET CLASS: SYNTHETIC_ASSETS
- Collateral-backed
- Price oracle dependent
- Vulnerabilities: oracle manipulation, undercollateralization
```

---

# PART II: FEASIBILITY & COST KERNEL (Critical Addition)

## 2.1 The Net Profit Function

Every counterexample must satisfy economic feasibility. Define:

```
NetProfit(sequence, state, environment) = ValueExtracted - ValueInvested - ExecutionCosts

Where:
  ValueExtracted = sum of all assets gained by attacker
  ValueInvested = sum of all assets spent by attacker (excluding recoverable)
  ExecutionCosts = GasCosts + ProtocolFees + MEVCosts + MarketImpactCosts + OpportunityCosts
```

### 2.1.1 Cost Components (Formal Definitions)

```
COST COMPONENT: GAS
{
  "formula": "gasUsed * baseFee + priorityFee",
  "baseFee_model": "fetch_from_block | estimate_range",
  "priorityFee_model": "market_rate | builder_minimum",
  "gas_limit_constraint": "30_000_000 per block",
  
  "pricing": {
    "eth_price_usd": "fetch_current | parameter",
    "gas_price_gwei": "dynamic | fixed_estimate"
  }
}

COST COMPONENT: PROTOCOL_FEES
{
  "types": [
    "swap_fees": "0.01% - 1% depending on pool",
    "flash_loan_fees": "0.05% - 0.09% typically",
    "borrow_fees": "origination + interest",
    "withdrawal_fees": "protocol specific",
    "liquidation_penalties": "5-15% typically"
  ],
  "accumulation": "sum across all operations in sequence"
}

COST COMPONENT: MEV_COSTS
{
  "inclusion_cost": {
    "public_mempool": 0,
    "flashbots_protect": 0,
    "priority_ordering": "priority_fee_premium",
    "builder_bribe": "negotiated | auction_based"
  },
  "sandwich_risk": {
    "if_exposed": "potential_loss_from_being_sandwiched",
    "mitigation": "private_mempool | small_size | slippage_protection"
  }
}

COST COMPONENT: MARKET_IMPACT
{
  "model": "constant_product | concentrated_liquidity | order_book",
  
  "constant_product_impact": {
    "formula": "amount / (reserve + amount)",
    "reserves": "fetch_from_pool",
    "fee_tier": "pool_specific"
  },
  
  "concentrated_liquidity_impact": {
    "formula": "integrate_across_ticks",
    "liquidity_distribution": "fetch_from_pool",
    "tick_spacing": "pool_specific"
  },
  
  "slippage_bounds": {
    "small_trade": "< 0.1% for < $100k",
    "medium_trade": "0.1-1% for $100k-$1M",
    "large_trade": "> 1% for > $1M"
  }
}

COST COMPONENT: OPPORTUNITY_COST
{
  "capital_lockup": {
    "duration": "blocks or seconds",
    "risk_free_rate": "staking_yield | lending_rate",
    "cost": "capital * rate * duration"
  },
  "inventory_risk": {
    "if_multi_block": "price_volatility * exposure * duration",
    "hedging_cost": "if_hedged"
  }
}
```

### 2.1.2 Feasibility Thresholds

```json
{
  "feasibility_thresholds": {
    "absolute_minimum": {
      "net_profit_wei": "1000000000000000",
      "net_profit_usd": "10.00",
      "rationale": "Must exceed minimum viable profit"
    },
    
    "risk_adjusted": {
      "profit_to_capital_ratio": 0.001,
      "profit_to_risk_ratio": 0.01,
      "rationale": "Profit must justify capital at risk"
    },
    
    "robustness": {
      "profit_under_10pct_cost_increase": "> 0",
      "profit_under_adverse_timing": "> 0",
      "profit_under_partial_fill": "> 0",
      "rationale": "Exploit must work under realistic variance"
    },
    
    "tier_specific": {
      "TIER_0": {"min_profit_usd": 100, "max_gas_eth": 0.1},
      "TIER_1": {"min_profit_usd": 1000, "max_gas_eth": 1},
      "TIER_2": {"min_profit_usd": 10000, "max_gas_eth": 10},
      "TIER_3": {"min_profit_usd": 100000, "max_gas_eth": 100}
    }
  }
}
```

### 2.1.3 Liquidity Constraint Modeling

```
LIQUIDITY MODEL: REALISTIC_MAINNET
{
  "principle": "All value extraction requires market operations that have real costs",
  
  "flash_loan_constraints": {
    "max_single_source": "bounded by pool liquidity",
    "max_combined": "sum of available sources",
    "fee_accumulation": "sum of all flash loan fees"
  },
  
  "price_manipulation_constraints": {
    "cost_to_move_price": "function of liquidity depth",
    "sustainable_duration": "until arbitrageurs restore",
    "arbitrage_latency": "~1-3 blocks typically"
  },
  
  "oracle_manipulation_constraints": {
    "twap_window": "protocol specific",
    "cost_to_skew_twap": "integral of manipulation cost over window",
    "detection_risk": "if price deviates significantly"
  }
}
```

## 2.2 Feasibility Verification Protocol

```
FOR EVERY CANDIDATE COUNTEREXAMPLE:

STEP 1: Calculate Gross Profit
  gross_profit = attacker_balance_after - attacker_balance_before
  (across all assets, converted to common denomination)

STEP 2: Calculate All Costs
  gas_cost = simulate_gas() * current_gas_price
  protocol_fees = sum(fees_in_sequence)
  mev_cost = estimate_inclusion_cost(ordering_required)
  market_impact = simulate_trades_with_real_liquidity()
  
STEP 3: Calculate Net Profit
  net_profit = gross_profit - gas_cost - protocol_fees - mev_cost - market_impact

STEP 4: Robustness Check
  for perturbation in [gas+20%, liquidity-20%, timing+1block]:
    perturbed_profit = recalculate(perturbation)
    if perturbed_profit <= 0:
      mark_as_fragile()

STEP 5: Tier Classification
  min_tier = lowest_tier_where_attack_is_feasible()
  if net_profit < tier_threshold[min_tier]:
    reject_as_economically_infeasible()

STEP 6: Report
  include in finding:
    - gross_profit
    - itemized_costs
    - net_profit
    - minimum_attacker_tier
    - robustness_assessment
```

---

# PART III: SEMANTIC MODEL CONSTRUCTION

## 3.1 The Three Graphs (Mandatory Construction)

### Graph A: Call Graph (Dynamic + Static)

```
NODE SCHEMA:
{
  "contract": "0x...",
  "function": "functionName(args)",
  "visibility": "public|external",
  "mutability": "view|pure|payable|nonpayable",
  "modifiers": ["modifier1", "modifier2"],
  "estimated_gas": 50000,
  "state_reads": ["slot1", "slot2"],
  "state_writes": ["slot3"],
  "return_data": "type"
}

EDGE SCHEMA:
{
  "source": "Contract.function",
  "target": "Contract.function | EXTERNAL",
  "call_type": "CALL|DELEGATECALL|STATICCALL|INTERNAL",
  
  "target_derivation": {
    "type": "hardcoded|storage|input|computed",
    "source_slot": "0x...",
    "input_index": 0,
    "computation": "...",
    "attacker_controllable": true|false
  },
  
  "calldata_derivation": {
    "type": "constant|derived|user_controlled|mixed",
    "controlled_params": [0, 2],
    "validation_present": true|false
  },
  
  "value_derivation": {
    "type": "zero|constant|input|computed",
    "source": "..."
  },
  
  "reentrancy_surface": {
    "can_reenter": true|false,
    "reentrant_functions": ["func1", "func2"],
    "guard_present": true|false,
    "guard_type": "mutex|CEI|other",
    "read_only_reentry_risk": true|false
  },
  
  "static_context_risks": {
    "reads_during_callback": ["slot1", "slot2"],
    "toctou_potential": true|false,
    "return_data_trusted": true|false
  },
  
  "gas_forwarding": "all|limited|fixed",
  "return_handling": "checked|unchecked|ignored"
}
```

### Graph B: Asset Flow Graph

```
NODE SCHEMA (ACCOUNTS):
{
  "address": "0x...",
  "type": "protocol|user|external|attacker",
  "assets_held": ["token1", "token2", "ETH"],
  "approvals_given": [...],
  "approvals_received": [...]
}

EDGE SCHEMA (FLOWS):
{
  "type": "transfer|mint|burn|approve|debt_increase|debt_decrease|wrap|unwrap",
  "token": "0x...",
  "from": "0x...",
  "to": "0x...",
  
  "amount_derivation": {
    "type": "input|computed|storage|oracle_dependent",
    "formula": "...",
    "rounding": {
      "direction": "up|down|nearest|truncate",
      "precision": "WAD|RAY|custom",
      "max_error_per_op": "1 wei",
      "bias_potential": true|false
    }
  },
  
  "authority_source": {
    "type": "msg.sender|approval|signature|protocol_logic",
    "function": "ContractA.functionX"
  },
  
  "accounting_reference": {
    "internal_variable": "balances[user]",
    "slot": "0x...",
    "update_timing": "before_transfer|after_transfer|atomic",
    "divergence_risk": true|false
  },
  
  "fee_model": {
    "fee_on_transfer": true|false,
    "fee_rate": "dynamic|fixed|zero",
    "fee_recipient": "0x...",
    "handled_correctly": true|false|unknown
  },
  
  "oracle_dependency": {
    "present": true|false,
    "oracle": "0x...",
    "staleness_check": true|false,
    "manipulation_surface": "..."
  }
}
```

### Graph C: Capability/Authority Graph

```
CAPABILITY NODE SCHEMA:
{
  "id": "CAP-001",
  "type": "asset_movement|parameter_change|role_assignment|external_call|state_mutation",
  "description": "Move token X from A to B",
  "value_at_risk": "quantified in USD",
  "frequency": "how often this capability is exercised normally"
}

CAPABILITY EDGE SCHEMA:
{
  "function": "Contract.function",
  "capability": "CAP-001",
  "direction": "creates|consumes|modifies",
  
  "gating_conditions": [
    {
      "type": "msg.sender_check|state_condition|time_condition|signature|amount_limit",
      "requirement": "formal predicate",
      "attacker_satisfiable": true|false|conditional,
      "satisfaction_method": "how attacker can satisfy",
      "satisfaction_cost": "cost to satisfy"
    }
  ],
  
  "composability": {
    "same_tx_composable": true|false,
    "requires_prior": ["CAP-000"],
    "enables_subsequent": ["CAP-002"],
    "flash_loan_enabling": true|false
  }
}
```

---

## 3.2 Protocol State Machine

### Phase Schema

```json
{
  "phase_id": "PHASE-001",
  "name": "deposit_lifecycle",
  
  "entry_conditions": [
    {"predicate": "vault.paused == false", "type": "state"},
    {"predicate": "msg.sender.balance >= amount", "type": "caller"}
  ],
  
  "sub_phases": [
    {
      "name": "pre_transfer",
      "invariants_must_hold": ["total_assets_consistent"],
      "reentrancy_window": false
    },
    {
      "name": "asset_transfer",
      "external_calls": ["token.transferFrom"],
      "reentrancy_window": true,
      "read_only_reentry_risk": true,
      "state_inconsistent_during": ["shares_not_yet_minted"]
    },
    {
      "name": "share_mint",
      "state_changes": ["totalSupply++", "shares[user]++"],
      "rounding_critical": true,
      "reentrancy_window": false
    }
  ],
  
  "exit_conditions": [
    {"success": "shares_minted > 0"},
    {"failure": "revert with reason"}
  ],
  
  "invariants_after": [
    "convertToAssets(shares_minted) >= assets_deposited - max_rounding_loss"
  ]
}
```

---

## 3.3 Mode Discovery (Boundary States)

```
CRITICAL MODES (with feasibility context):

EMPTY_STATE_MODES:
{
  "totalSupply == 0": {
    "attack_surface": "first depositor inflation",
    "typical_profit": "proportional to subsequent deposits",
    "feasibility": "high - low capital required",
    "detection": "check if vault is newly deployed or emptied"
  },
  "totalAssets == 0 && totalSupply > 0": {
    "attack_surface": "share price collapse",
    "typical_profit": "existing shares become worthless",
    "feasibility": "requires specific conditions"
  }
}

RATIO_BOUNDARY_MODES:
{
  "exchangeRate approaching 0": {
    "attack_surface": "division issues, share worthlessness"
  },
  "exchangeRate approaching max": {
    "attack_surface": "overflow on multiplication"
  },
  "utilizationRate == 100%": {
    "attack_surface": "withdrawal blocked, interest spike"
  }
}

ORACLE_BOUNDARY_MODES:
{
  "price == 0": {
    "attack_surface": "division by zero, incorrect valuations"
  },
  "price stale by > threshold": {
    "attack_surface": "outdated liquidations, arbitrage"
  },
  "price deviation > X% from other sources": {
    "attack_surface": "oracle disagreement exploitation"
  }
}

TIMING_BOUNDARY_MODES:
{
  "block.timestamp == epoch_boundary": {
    "attack_surface": "reward calculation boundaries"
  },
  "time_since_last_accrual > expected": {
    "attack_surface": "interest calculation jumps"
  }
}
```

---

# PART IV: PROPERTY PORTFOLIO (FALSIFICATION TARGETS)

## 4.1 Accounting/Conservation Properties

```json
{
  "P-ACCOUNTING-001": {
    "name": "Total Asset Conservation",
    "predicate": "sum(user_redeemable) <= protocol_balance + tolerance",
    "tolerance": "1e-6 * total_assets",
    "modes": ["all"],
    "violation_type": "theft_of_funds",
    "feasibility_note": "Direct profit to attacker"
  },
  
  "P-ACCOUNTING-002": {
    "name": "No Free Value Cycles",
    "predicate": "NetProfit(any_cycle) <= max_favorable_rounding + fees_paid",
    "test_method": "cycle_search_with_feasibility",
    "feasibility_note": "Must account for all costs in cycle"
  },
  
  "P-ACCOUNTING-003": {
    "name": "Rounding Bias Bounds",
    "predicate": "cumulative_rounding_bias < threshold over N operations",
    "threshold": "0.01% of volume",
    "N": 1000,
    "feasibility_note": "High-frequency required, gas costs may dominate"
  }
}
```

## 4.2 Capability/Authority Properties

```json
{
  "P-AUTHORITY-001": {
    "name": "External Call Target Integrity",
    "predicate": "all external call targets in allowlist OR hardcoded",
    "modes": ["all"],
    "violation_type": "arbitrary_call",
    "feasibility_note": "Often leads to full drain"
  },
  
  "P-AUTHORITY-002": {
    "name": "Approval Scope Limitation",
    "predicate": "protocol approvals only usable for intended operations",
    "modes": ["protocol_has_token_approvals"],
    "feasibility_note": "Profit = min(approval_amount, attacker_can_route)"
  }
}
```

## 4.3 Temporal/Trace Properties

```json
{
  "P-TEMPORAL-001": {
    "name": "Read-Only Reentrancy Safety",
    "predicate": "view functions during callbacks return consistent state",
    "modes": ["has_external_calls_before_state_update"],
    "violation_type": "read_only_reentrancy",
    "feasibility_note": "Depends on what decisions use the stale read"
  },
  
  "P-TEMPORAL-002": {
    "name": "Slot Timing Consistency",
    "predicate": "12-second slot assumptions hold under missed slots",
    "modes": ["has_time_dependent_logic"],
    "feasibility_note": "Missed slots are observable, not controllable"
  }
}
```

## 4.4 Oracle/Signal Properties

```json
{
  "P-ORACLE-001": {
    "name": "Manipulation Cost Exceeds Profit",
    "predicate": "cost_to_manipulate_oracle > profit_from_manipulation",
    "variables": {
      "liquidity_depth": "from_chain",
      "twap_window": "from_protocol",
      "affected_value": "from_protocol"
    },
    "feasibility_note": "Must model realistic liquidity constraints"
  }
}
```

## 4.5 Token Behavior Properties

```json
{
  "P-TOKEN-001": {
    "name": "Fee-on-Transfer Handling",
    "predicate": "actual_received == expected OR protocol handles delta",
    "modes": ["interacts_with_fot_tokens"],
    "feasibility_note": "Accounting mismatch accumulates"
  },
  
  "P-TOKEN-002": {
    "name": "Rebase Safety",
    "predicate": "share accounting insensitive to balance changes",
    "modes": ["interacts_with_rebasing_tokens"],
    "feasibility_note": "Yield capture possible"
  },
  
  "P-TOKEN-003": {
    "name": "Callback Reentrancy Safety",
    "predicate": "no state inconsistency during token callbacks",
    "modes": ["interacts_with_hook_tokens"],
    "feasibility_note": "ERC777/ERC1155 hooks are attacker-controlled"
  }
}
```

## 4.6 Ordering/MEV Properties

```json
{
  "P-ORDERING-001": {
    "name": "Sandwich Resistance",
    "predicate": "user_outcome_variance < threshold under adversarial ordering",
    "threshold": "1% slippage",
    "feasibility_note": "Requires ordering_power >= medium"
  },
  
  "P-ORDERING-002": {
    "name": "Sequence Independence",
    "predicate": "protocol_state_after(A,B) == protocol_state_after(B,A) for independent users",
    "feasibility_note": "Non-commutativity often reveals value"
  }
}
```

## 4.7 Liveness/Gas Properties

```json
{
  "P-LIVENESS-001": {
    "name": "Withdrawal Always Possible",
    "predicate": "solvent user can exit under bounded gas",
    "gas_bound": "1_000_000",
    "feasibility_note": "DoS is not value extraction but may enable it"
  },
  
  "P-LIVENESS-002": {
    "name": "No Unbounded Loops",
    "predicate": "all loops bounded by constants or caller-controlled inputs",
    "feasibility_note": "Gas griefing may trap funds"
  }
}
```

## 4.8 Environment/Chain Properties

```json
{
  "P-ENV-001": {
    "name": "Timestamp Assumption Safety",
    "predicate": "12-second slot assumptions handle missed slots",
    "feasibility_note": "Missed slots create timestamp jumps"
  },
  
  "P-ENV-002": {
    "name": "L2 Sequencer Awareness",
    "predicate": "protocol handles sequencer downtime",
    "modes": ["deployed_on_l2"],
    "feasibility_note": "Stale prices during downtime"
  }
}
```

---

# PART V: KERNEL CONTRADICTION TEMPLATES

## 5.1 The Seven Archetypes (With Feasibility Analysis)

```
TEMPLATE 1: NON-COMMUTATIVITY EXPLOITATION
{
  "pattern": "A∘B ≠ B∘A on watched property",
  "feasibility_factors": [
    "Can attacker control ordering? (requires ordering_power >= medium)",
    "What is delta between orderings?",
    "Is delta greater than ordering cost?"
  ],
  "typical_profit_range": "small per instance, may need repetition"
}

TEMPLATE 2: ACCOUNTING DIVERGENCE
{
  "pattern": "Internal ledger diverges from actual balance",
  "feasibility_factors": [
    "How fast does divergence accumulate?",
    "Can divergence be harvested in single tx?",
    "Gas cost of operations vs divergence gained"
  ],
  "typical_profit_range": "can be large if protocol holds significant assets"
}

TEMPLATE 3: BOUNDARY DISCONTINUITY
{
  "pattern": "Property fails at mode boundaries",
  "feasibility_factors": [
    "Can attacker force system into boundary state?",
    "Cost to reach boundary state?",
    "Profit once in boundary state?"
  ],
  "typical_profit_range": "first depositor attacks can be very profitable"
}

TEMPLATE 4: CYCLIC AMPLIFICATION
{
  "pattern": "Closed loop increases attacker metric",
  "feasibility_factors": [
    "Per-cycle profit vs per-cycle cost (gas + fees)",
    "Maximum cycles before constraint hit",
    "Total profit = cycles * (per_cycle_profit - per_cycle_cost)"
  ],
  "typical_profit_range": "depends heavily on cycle efficiency"
}

TEMPLATE 5: PRECISION BIAS
{
  "pattern": "Consistent rounding direction accumulates",
  "feasibility_factors": [
    "Bias per operation (typically 1 wei)",
    "Gas cost per operation",
    "Operations needed: profit_target / bias_per_op",
    "Often NOT feasible due to gas"
  ],
  "typical_profit_range": "usually economically infeasible alone"
}

TEMPLATE 6: TEMPORAL MISMATCH
{
  "pattern": "Timing windows create inconsistency",
  "feasibility_factors": [
    "Window duration and predictability",
    "Attacker timing capabilities required",
    "Value accessible during window"
  ],
  "typical_profit_range": "varies widely"
}

TEMPLATE 7: CROSS-MODULE SEMANTIC MISMATCH
{
  "pattern": "Two modules interpret state differently",
  "feasibility_factors": [
    "Can attacker interact with both modules in same tx?",
    "What value can be arbitraged between interpretations?"
  ],
  "typical_profit_range": "can be large if significant value in mismatched state"
}
```

---

# PART VI: DEPENDENCY SEMANTICS LIBRARY (Modular)

## 6.1 Token Models (Pluggable)

```python
# Token Behavior Model Interface
class TokenModel:
    def transfer(self, from_addr, to_addr, amount) -> (actual_received, events):
        """Returns actual amount received and events emitted"""
        raise NotImplementedError
    
    def balanceOf(self, addr, block_context) -> uint256:
        """Returns balance, may change between calls for rebasing"""
        raise NotImplementedError
    
    def reentrancy_hooks(self) -> List[HookSpec]:
        """Returns list of hooks that enable reentrancy"""
        raise NotImplementedError

# Standard ERC20
class StandardERC20(TokenModel):
    fee_on_transfer = False
    rebasing = False
    hooks = []
    
    def transfer(self, from_addr, to_addr, amount):
        return (amount, [Transfer(from_addr, to_addr, amount)])

# Fee-on-Transfer
class FeeOnTransferToken(TokenModel):
    fee_on_transfer = True
    fee_rate = 0.01  # 1%
    
    def transfer(self, from_addr, to_addr, amount):
        fee = amount * self.fee_rate
        received = amount - fee
        return (received, [Transfer(from_addr, to_addr, received)])

# Rebasing Token
class RebasingToken(TokenModel):
    rebasing = True
    shares_to_balance_ratio = Variable()
    
    def balanceOf(self, addr, block_context):
        shares = self.shares[addr]
        return shares * self.get_ratio(block_context)

# ERC777 with Hooks
class ERC777Token(TokenModel):
    hooks = ["tokensReceived", "tokensToSend"]
    
    def reentrancy_hooks(self):
        return [
            HookSpec("tokensToSend", timing="before_transfer", controllable=True),
            HookSpec("tokensReceived", timing="after_transfer", controllable=True)
        ]
```

## 6.2 Oracle Models (Pluggable)

```python
class OracleModel:
    def get_price(self, block_context) -> (price, timestamp, round_id):
        raise NotImplementedError
    
    def manipulation_cost(self, target_price, duration) -> uint256:
        """Cost to move price to target for duration"""
        raise NotImplementedError
    
    def staleness_behavior(self, stale_seconds) -> Behavior:
        """What happens when oracle is stale"""
        raise NotImplementedError

# Chainlink Oracle
class ChainlinkOracle(OracleModel):
    heartbeat = 3600  # 1 hour
    deviation_threshold = 0.005  # 0.5%
    
    def staleness_behavior(self, stale_seconds):
        if stale_seconds > self.heartbeat * 2:
            return "likely_reverts"  # if protocol checks
        return "returns_stale_price"
    
    def manipulation_cost(self, target_price, duration):
        # Cannot directly manipulate Chainlink
        return INFINITY

# TWAP Oracle
class TWAPOracle(OracleModel):
    window = 1800  # 30 minutes
    source_pool = "0x..."
    
    def manipulation_cost(self, target_price_delta, duration):
        # Cost = integral of price impact over window
        liquidity = get_pool_liquidity(self.source_pool)
        return estimate_twap_manipulation_cost(
            liquidity, target_price_delta, self.window
        )

# Spot Price Oracle
class SpotOracle(OracleModel):
    source_pool = "0x..."
    
    def manipulation_cost(self, target_price, duration):
        liquidity = get_pool_liquidity(self.source_pool)
        # Single block manipulation
        return calculate_price_impact(liquidity, target_price)
```

## 6.3 AMM Models (Pluggable)

```python
class AMMModel:
    def quote(self, token_in, token_out, amount_in) -> (amount_out, price_impact):
        raise NotImplementedError
    
    def liquidity_depth(self, price_range) -> uint256:
        raise NotImplementedError

# Uniswap V2 (Constant Product)
class UniswapV2Pool(AMMModel):
    fee = 0.003  # 0.3%
    
    def quote(self, amount_in):
        amount_in_with_fee = amount_in * (1 - self.fee)
        amount_out = (self.reserve_out * amount_in_with_fee) / (self.reserve_in + amount_in_with_fee)
        price_impact = amount_in / (self.reserve_in + amount_in)
        return (amount_out, price_impact)

# Uniswap V3 (Concentrated Liquidity)
class UniswapV3Pool(AMMModel):
    def quote(self, amount_in):
        # Integrate across ticks
        return simulate_v3_swap(self.liquidity_distribution, amount_in)
    
    def liquidity_depth(self, price_range):
        return sum(tick.liquidity for tick in self.ticks if tick.price in price_range)

# Curve (StableSwap)
class CurvePool(AMMModel):
    A = 100  # Amplification parameter
    
    def quote(self, amount_in):
        # Curve invariant calculation
        return curve_swap_simulation(self.balances, self.A, amount_in)
```

---

# PART VII: COVERAGE SCOREBOARD (Measurable Completeness)

## 7.1 Coverage Dimensions

```json
{
  "coverage_scoreboard": {
    "sink_coverage": {
      "description": "Every sink has at least one property + one adversarial path",
      "categories": {
        "asset_sinks": {
          "total": 0,
          "covered_by_property": 0,
          "covered_by_search": 0,
          "coverage_percent": 0
        },
        "authority_sinks": {
          "total": 0,
          "covered_by_property": 0,
          "covered_by_search": 0,
          "coverage_percent": 0
        },
        "external_call_sinks": {
          "total": 0,
          "covered_by_property": 0,
          "covered_by_search": 0,
          "coverage_percent": 0
        }
      },
      "target": "100% of sinks covered"
    },
    
    "mode_coverage": {
      "description": "Which modes were reached under adversarial sequences",
      "modes_defined": 0,
      "modes_reached_normal": 0,
      "modes_reached_adversarial": 0,
      "transitions_defined": 0,
      "transitions_traversed": 0,
      "boundary_modes_hit": 0,
      "target": ">80% modes reached, 100% boundary modes"
    },
    
    "domain_coverage": {
      "description": "Numeric domain exploration",
      "categories": {
        "rounding_boundaries": {
          "tested": ["n", "n-1", "n+1", "powers_of_2"],
          "coverage": 0
        },
        "decimal_regimes": {
          "tested": [0, 2, 6, 8, 18, 24],
          "coverage": 0
        },
        "extreme_values": {
          "tested": ["0", "1", "2", "max-1", "max"],
          "coverage": 0
        },
        "discontinuities": {
          "empty_supply": false,
          "near_zero_denominator": false,
          "utilization_boundaries": false
        }
      }
    },
    
    "sequence_coverage": {
      "description": "Operation sequence exploration",
      "max_depth_tested": 0,
      "unique_sequences_tested": 0,
      "permutation_coverage": {
        "pairs_tested": 0,
        "pairs_total": 0
      },
      "cycle_coverage": {
        "cycles_found": 0,
        "cycles_tested": 0
      },
      "multi_actor_coverage": {
        "max_actors_tested": 0,
        "actor_interaction_pairs": 0
      }
    },
    
    "property_coverage": {
      "description": "Which properties were actually tested",
      "properties_defined": 0,
      "properties_instantiated": 0,
      "properties_with_counterexample_search": 0,
      "properties_with_formal_verification": 0,
      "violations_found": 0
    },
    
    "assumption_coverage": {
      "description": "Which assumptions were stress-tested",
      "assumptions_identified": 0,
      "assumptions_with_adversarial_test": 0,
      "assumptions_violated": 0
    }
  }
}
```

## 7.2 Coverage Thresholds for "Complete" (Checkpoint Only, Not Stop Condition)

```
MINIMUM THRESHOLDS FOR CHECKPOINT (not termination):

TIER_BASIC (Initial Pass):
- Sink coverage: 100% of asset sinks, 100% of external call sinks
- Mode coverage: All boundary modes reached
- Sequence depth: At least 5
- Properties: All accounting properties instantiated

TIER_STANDARD (Production):
- Sink coverage: 100% all categories
- Mode coverage: >90% modes, 100% boundaries
- Domain coverage: All decimal regimes, all extreme values
- Sequence depth: At least 10
- Permutation coverage: >50% of high-priority pairs
- Properties: Full portfolio instantiated

TIER_EXHAUSTIVE (High-Value Targets):
- Everything in STANDARD plus:
- Sequence depth: Up to 20
- Permutation coverage: >90%
- Cycle coverage: All identified cycles tested
- Multi-actor: Up to 5 actors
- Formal verification on critical properties

NOTE: These thresholds are CHECKPOINT markers. Investigation continues until E3.
```

## 7.3 Coverage Report Format

```
═══════════════════════════════════════════════════════════════════════════════
COVERAGE REPORT: [Protocol Name]
Fork Block: [Number] | Chain: [ID] | Date: [ISO8601]
═══════════════════════════════════════════════════════════════════════════════

SINK COVERAGE                                                    [██████████] 100%
├── Asset Sinks:        45/45 covered                           [██████████] 100%
├── Authority Sinks:    12/12 covered                           [██████████] 100%
└── External Calls:     23/23 covered                           [██████████] 100%

MODE COVERAGE                                                    [████████░░] 85%
├── Modes Reached:      17/20                                   [████████░░] 85%
├── Boundary Modes:     8/8                                     [██████████] 100%
└── Transitions:        34/45                                   [███████░░░] 75%

DOMAIN COVERAGE                                                  [█████████░] 92%
├── Decimal Regimes:    6/6                                     [██████████] 100%
├── Extreme Values:     5/5                                     [██████████] 100%
├── Rounding Bounds:    4/5                                     [████████░░] 80%
└── Discontinuities:    3/4                                     [███████░░░] 75%

SEQUENCE COVERAGE                                                [███████░░░] 73%
├── Max Depth:          15
├── Sequences Tested:   12,847
├── Permutations:       156/234 pairs                           [██████░░░░] 67%
└── Cycles Tested:      8/8                                     [██████████] 100%

PROPERTY COVERAGE                                                [██████████] 100%
├── Defined:            42
├── Instantiated:       42                                      [██████████] 100%
├── With Search:        42                                      [██████████] 100%
└── Violations Found:   1

FINDINGS SUMMARY
├── Critical:           0
├── High:               1 (economically feasible)
├── Medium:             2 (economically marginal)
└── Low:                5 (theoretical only)

GAPS IDENTIFIED
├── Mode "migration_in_progress" not reached (requires governance)
├── Oracle failover path not tested (requires oracle failure)
└── 3-actor MEV scenario not fully explored (compute budget)

═══════════════════════════════════════════════════════════════════════════════
```

---

# PART VIII: CONTRADICTIONSPEC GENERATION

## 8.1 Complete Schema (With Feasibility)

```json
{
  "id": "CSPEC-XXXX",
  "created": "ISO8601_timestamp",
  "template": "cyclic_amplification",
  "priority": "critical",
  
  "attacker_model": {
    "minimum_tier": "TIER_1_DEFI_USER",
    "ordering_power": "weak",
    "flash_liquidity_required": {"eth": "1000", "usdc": "0"},
    "multi_block_required": false
  },
  
  "target_mode": {
    "predicate": "totalSupply == 0",
    "reach_strategy": "MACRO-EMPTY-VAULT",
    "reach_cost_estimate": {"gas": "500000", "capital": "0"}
  },
  
  "property": {
    "id": "P-ACCOUNTING-001",
    "predicate_formal": "post.attacker_value - pre.attacker_value <= allowed_profit",
    "allowed_profit": "protocol_fees_paid + max_rounding_loss"
  },
  
  "variables": {
    "sequence": {
      "min_depth": 3,
      "max_depth": 20,
      "allowed_actions": ["deposit", "withdraw", "donate"]
    },
    "amounts": [
      {"name": "donation", "range": ["1e18", "1e24"], "distribution": "log_uniform"}
    ]
  },
  
  "feasibility_constraints": {
    "max_gas_cost_eth": "1.0",
    "max_flash_loan_fees": "0.1%",
    "max_market_impact": "1%",
    "net_profit_threshold_usd": "1000"
  },
  
  "objective": {
    "primary": "maximize(net_profit)",
    "where": "net_profit = gross_profit - gas_cost - fees - market_impact"
  },
  
  "instrumentation": {
    "track_costs": true,
    "track_all_value_flows": true,
    "simulate_with_real_liquidity": true
  }
}
```

---

# PART IX: SOLVER PORTFOLIO

## 9.1 Discrete Sequence Search

```
ALGORITHM: GUIDED_SEQUENCE_SEARCH

INPUT: ContradictionSpec, SystemModel, FeasibilityConfig
OUTPUT: Candidate sequences with feasibility scores

1. INITIALIZE action_space from capability graph
2. PRIORITIZE actions by:
   - Sink involvement (asset/authority/external)
   - Mode transition potential
   - Historical violation correlation
   - Cost efficiency (value_impact / gas_cost)

3. SEARCH with feasibility pruning:
   FOR each expansion:
     estimate_cost = gas_so_far + estimated_remaining_gas
     estimate_max_profit = upper_bound_on_profit
     IF estimate_max_profit <= estimate_cost * safety_margin:
       PRUNE (economically infeasible)
     
     IF reaches_target_mode AND violates_property:
       candidate = current_sequence
       feasibility = evaluate_full_feasibility(candidate)
       IF feasibility.net_profit > threshold:
         YIELD (candidate, feasibility)

4. RANK candidates by:
   - Net profit (after all costs)
   - Minimum attacker tier required
   - Robustness score
   - Sequence simplicity
```

## 9.2 Parameter Solving (With Economic Constraints)

```
ALGORITHM: ECONOMICALLY_CONSTRAINED_OPTIMIZATION

INPUT: Sequence skeleton, feasibility constraints
OUTPUT: Optimal parameters maximizing net profit

1. DEFINE objective:
   maximize: net_profit(params)
   subject_to:
     - all_calls_succeed(params)
     - gas_cost(params) <= max_gas
     - market_impact(params) <= max_impact
     - flash_loan_available(params)

2. OPTIMIZE using:
   - Bayesian optimization (handles noisy objectives)
   - CMA-ES (handles non-convex landscapes)
   - Grid search for discrete parameters

3. VALIDATE:
   - Execute with found parameters
   - Verify costs match estimates
   - Verify profit is real (not accounting artifact)
```

## 9.3 Ordering Power Modeling (PoS-Correct)

```
ORDERING_MODEL: ETHEREUM_POS_2026

WEAK_ORDERING:
  - Submit to public mempool
  - No guarantees on position
  - Can be frontrun/sandwiched
  - Use for baseline feasibility

MEDIUM_ORDERING:
  - Flashbots Protect / private mempool
  - Protection from sandwich
  - Some priority control
  - Most realistic for TIER_1/2 attackers

STRONG_ORDERING:
  - MEV-share backrun capability
  - Can reliably position after target tx
  - Useful for oracle backruns, liquidations
  - TIER_2+ attackers

BUILDER_ORDERING:
  - Full block control
  - Can include/exclude any tx
  - Can reorder arbitrarily within block
  - TIER_3+ attackers only

FOR EACH EXPERIMENT:
  - Tag required ordering power
  - Verify attack is feasible at that power level
  - Calculate ordering cost (priority fee, builder bribe)
```

## 9.4 Token/Oracle/AMM Model Injection

```
DEPENDENCY_INJECTION:

FOR EACH TARGET PROTOCOL:
  1. Identify all token interactions
     - Map each token to a TokenModel (Standard, FOT, Rebasing, Hook)
  2. Identify all oracle dependencies
     - Map each oracle to an OracleModel (Chainlink, TWAP, Spot)
  3. Identify all AMM interactions
     - Map each pool to an AMMModel (V2, V3, Curve)

CONFIGURE in dependencies/config.yaml:
  tokens:
    "0xA0b8...": {model: "FeeOnTransferToken", fee_rate: 0.01}
    "0xC02a...": {model: "StandardERC20"}
  oracles:
    "0x5f4e...": {model: "ChainlinkOracle", heartbeat: 3600}
    "0x8888...": {model: "TWAPOracle", window: 1800, source_pool: "0x..."}
  amms:
    "0x1234...": {model: "UniswapV3Pool", fee_tier: 500}

INJECT into solvers:
  - Replace transfer() with model.transfer()
  - Replace oracle.latestAnswer() with model.get_price()
  - Replace swap calculations with model.quote()
```

---

# PART X: EVIDENCE COMPILATION

## 10.1 Enhanced Finding Report

```json
{
  "finding_id": "FINDING-XXXX",
  "severity": "HIGH",
  "title": "First Depositor Share Inflation",
  
  "economic_summary": {
    "gross_profit": "1.5 ETH",
    "costs": {
      "gas": "0.02 ETH",
      "flash_loan_fees": "0.001 ETH",
      "protocol_fees": "0 ETH",
      "market_impact": "0 ETH"
    },
    "net_profit": "1.479 ETH",
    "net_profit_usd": "3,550.00",
    "minimum_attacker_tier": "TIER_0_BASIC",
    "capital_required": "1 wei (plus victim deposits)"
  },
  
  "feasibility_analysis": {
    "robustness_checks": [
      {"perturbation": "gas_price_+50%", "still_profitable": true, "profit": "1.47 ETH"},
      {"perturbation": "victim_deposit_-50%", "still_profitable": true, "profit": "0.74 ETH"}
    ],
    "real_world_executable": true,
    "time_sensitivity": "Must be first depositor, race condition with legitimate users",
    "detection_risk": "Low - single transaction, normal-looking operations"
  },
  
  "reproduction": {
    "fork_block": 18500000,
    "sequence": [...],
    "expected_profit": "1.479 ETH",
    "verified_runs": 10,
    "deterministic": true
  },
  
  "coverage_context": {
    "template_used": "boundary_discontinuity",
    "mode_exploited": "totalSupply == 0",
    "sinks_involved": ["asset_sink:mint", "asset_sink:transfer"],
    "property_violated": "P-ACCOUNTING-001"
  }
}
```

---

# PART XI: EXECUTION PROTOCOL

## 11.1 Phase Summary

```
PHASE 1: SYSTEM INGESTION
- Fetch contracts, ABIs, source (Sourcify v2 first)
- Build three graphs
- Identify all sinks
- OUTPUT: system_model.json
- SKILL: world-modeler

PHASE 2: MODEL CONSTRUCTION
- Enumerate modes and transitions
- Map all assumptions
- Identify rounding operations
- Build ghost accounting
- OUTPUT: semantic_model.json
- SKILL: world-modeler

PHASE 3: DEPENDENCY CONFIGURATION
- Select appropriate token models
- Select appropriate oracle models
- Configure liquidity constraints
- OUTPUT: dependencies/config.yaml
- SKILL: property-portfolio-compiler

PHASE 4: PROPERTY INSTANTIATION
- Instantiate full property portfolio
- Link to assumptions
- Configure feasibility thresholds
- OUTPUT: properties/*
- SKILL: property-portfolio-compiler

PHASE 5: CONTRADICTIONSPEC GENERATION
- Generate specs from templates
- Prioritize by feasibility potential
- OUTPUT: hypotheses/*.yaml
- SKILL: property-portfolio-compiler

PHASE 6: SOLVING (iterative, until E3)
- Run solver portfolio
- Track coverage scoreboard
- Generate findings with feasibility
- OUTPUT: experiments.jsonl, findings/*.json, coverage/
- SKILL: counterexample-solver

PHASE 7: VALIDATION (per finding)
- Re-execute on fresh fork
- Verify economic calculations
- Verify determinism
- OUTPUT: validated_findings/*.json, final_report.md
- SKILL: proofpack-builder
```

---

# PART XII: CONTINUOUS EXECUTION RULES

## 12.1 Prime Directive (Updated)

```
NEVER STOP UNTIL:
1. A FEASIBLE counterexample is found (net_profit > threshold), OR
2. External interrupt (emit resume_pack.md and continue next session)

FEASIBILITY IS NON-NEGOTIABLE:
- "Theoretical vulnerability" without feasibility analysis = NOT A FINDING
- Profit must exceed costs under realistic conditions
- Must specify minimum attacker tier
```

## 12.2 Quality Gates (Updated)

```
BEFORE REPORTING ANY FINDING:
□ Executed on mainnet fork at specified block
□ All calls succeed
□ Gross profit calculated correctly
□ All costs itemized (gas, fees, impact)
□ Net profit > feasibility threshold
□ Minimum attacker tier identified
□ Robustness checks passed
□ Sequence shrunk to minimum
□ Reproduction is deterministic
□ No privileged roles assumed
□ Coverage context documented
```

## 12.3 Stall Detection and Recovery

```
STALL CONDITION:
- No evidence upgrade after N iterations (N configurable, default 5)
- Same targetStateX attempted multiple times without progress
- Coverage scoreboard unchanged

STALL RECOVERY:
1. Expand Vars (add more amounts, actors, state knobs)
2. Add boundary crossings:
   - module boundaries (cross-contract calls)
   - external boundaries (oracle, token interactions)
   - ordering boundaries (multi-tx, MEV scenarios)
   - control-plane boundaries (governance, admin functions)
3. Try different kernel contradiction template
4. Lower feasibility threshold temporarily for exploration
5. Force mode transitions to unreached boundary states

NEVER:
- Conclude "no bugs exist"
- Stop without E3 evidence
- Skip stall recovery
```

---

# PART XIII: CONTINUOUS QUESTION-GENERATION LOOP

## 13.1 Information-Seeking Protocol

The investigation is driven by **questions**, not tasks. Questions are recorded and resolved to mutate constraint programs.

### Question Recording

Record questions in `questions.jsonl` (append-only):

```json
{
  "qid": "Q-001",
  "timestamp": "ISO8601",
  "question": "Can the attacker reach totalSupply == 0 from current state?",
  "category": "mode_reachability",
  "related_hypothesis": "H-001",
  "related_property": "P-ACCOUNTING-001",
  "status": "open|resolved|blocked",
  "resolution_method": null,
  "answer": null
}
```

### Question Categories

```
CATEGORY: MODE_REACHABILITY
- Can attacker reach mode X from state Y?
- What is the minimum cost to reach mode X?
- Are there multiple paths to mode X?

CATEGORY: CONSTRAINT_SATISFACTION
- Can attacker satisfy constraint C?
- What parameter values satisfy constraints A, B, C simultaneously?
- Is the constraint system satisfiable?

CATEGORY: PROFIT_BOUNDARY
- What is the maximum profit given constraints?
- At what parameter value does profit become positive?
- How sensitive is profit to parameter P?

CATEGORY: ORDERING_DEPENDENCY
- Does outcome depend on tx ordering?
- What ordering power is required?
- Can attacker guarantee the required ordering?

CATEGORY: ASSUMPTION_VALIDITY
- Does assumption A hold on mainnet?
- Under what conditions does assumption A break?
- What happens if assumption A is false?

CATEGORY: COVERAGE_GAP
- Why hasn't mode X been reached?
- What blocks path to sink S?
- Which property classes have no experiments?
```

### Question Resolution

```
FOR EACH OPEN QUESTION:

1. Determine resolution method:
   - fork_read: Query chain state directly
   - fuzz_search: Search for satisfying inputs
   - symbolic_query: Use symbolic engine
   - manual_analysis: Requires human reasoning
   - experiment: Run targeted experiment

2. Execute resolution:
   - Run the chosen method
   - Record result in experiments.jsonl
   - Update question status

3. Mutate constraint programs:
   IF answer reveals new information:
     - Update Vars (new ranges, new actors)
     - Update Constraints (tighter bounds, new preconditions)
     - Update EvidencePlan (new experiment types)
     - Create new hypotheses if warranted

4. Generate follow-up questions:
   - Each answer typically spawns 0-3 new questions
   - Questions form a tree/DAG of investigation
```

### Question Priority

```
PRIORITY SCORING:
- Information gain: How much will the answer reduce uncertainty?
- E3 proximity: How close to a finding is this question?
- Cost: How expensive is resolution?
- Blocking: Is this question blocking other work?

PRIORITY = (information_gain * e3_proximity) / (cost * (1 + blocked_count))

ALWAYS RESOLVE highest priority question first.
```

## 13.2 Information Gain Metrics

```
METRIC: UNCERTAINTY_REDUCTION
- Before: Probability distribution over outcomes
- After: Updated distribution given answer
- Gain: KL divergence between distributions

METRIC: CONSTRAINT_TIGHTENING
- Before: Feasible region size
- After: Feasible region size given new constraint
- Gain: Volume reduction

METRIC: SEARCH_SPACE_REDUCTION
- Before: Number of candidate sequences
- After: Number remaining after pruning
- Gain: Candidates eliminated

PREFER questions that maximize these metrics.
```

---

# PART XIV: REQUIRED ARTIFACTS (Artifact-First Memory)

All critical state lives in explicit files. Nothing important is ephemeral.

## 14.1 Artifact Manifest

```
WORKSPACE ROOT:
├── boundary/
│   └── manifest.json           # System boundary (addresses, code hashes)
├── graphs/
│   ├── call_graph.json         # Call graph with annotations
│   ├── asset_flow.json         # Asset flow graph
│   ├── capability_graph.json   # Capability/authority graph
│   ├── sink_index.json         # Sink inventory (asset/authority/external)
│   └── dependency_index.json   # Token/oracle/AMM dependencies (model binding)
├── properties/
│   ├── portfolio.md            # Human-readable property portfolio
│   ├── portfolio.yaml          # Machine-readable properties
│   ├── assumptions.md          # Human-readable assumptions
│   └── assumptions.yaml        # Machine-readable assumptions
├── hypotheses/
│   └── <scenarioId>.yaml       # Constraint programs
├── specs/
│   └── <cSpecId>.yaml          # Contradiction specs
├── coverage/
│   ├── scoreboard.json         # Coverage metrics
│   └── report.md               # Coverage report
├── dependencies/
│   └── config.yaml             # Token/oracle/AMM model config
├── replay_bundles/
│   ├── candidates/             # Unvalidated witnesses
│   └── <scenarioId>_canonical.json  # Validated, minimized
├── test/
│   ├── utils/InvestigationUtils.sol # Minimal cheatcode helpers (no forge-std)
│   └── <scenarioId>_falsifier.t.sol # Foundry tests
├── foundry.toml                # Foundry config (fs_permissions enabled)
├── evidence/
│   ├── packets/                # Sourcify-first evidence packets (ABI/sources)
│   └── sources/                # Lossless sources (best-effort)
├── memory/
│   ├── events.jsonl            # Append-only event log (optional)
│   └── decision_trace.jsonl    # Append-only decision trace (scoring + choice)
├── hypothesis_ledger.md        # Index of all hypotheses
├── focus.md                    # Purpose + Memory Lock (working set pointer)
├── experiments.jsonl           # Append-only experiment log
├── questions.jsonl             # Append-only question log
├── attacker_model.yaml         # Active attacker tier config
├── state_machine.md            # Protocol state machine
├── deployment_snapshot.md      # Fork reality evidence
├── unknowns.md                 # Blocked items with resolution plans
├── resume_pack.md              # Checkpoint for continuation
├── rpc-etherscan.md            # RPC/explorer config (local-only; never propagate secrets)
├── system_evaluation.md        # System evaluator output
└── final_report.md             # E3 findings (only on success)
```

## 14.2 Artifact Schemas

### focus.md

`focus.md` is the short, always-current **working set pointer** that prevents goal/context loss.
It MUST be kept small and must always state the goal + target + active hypothesis + next skill.

```markdown
# Focus Card (Purpose + Memory Lock)

last_updated: 2026-02-02T00:00:00Z

## Goal (never changes)
- Discover an **E3-promoted**, economically feasible exploit counterexample on a mainnet fork.
- Stop only on **E3** or **external interrupt** (write `resume_pack.md`).

## Target (what we are analyzing)
- protocol_name: ProtocolX
- chain_id: 1
- fork_block (pinned): 19000000
- boundary: `boundary/manifest.json`
- fork reality: `deployment_snapshot.md`

## Active Focus (what we are trying right now)
- active_hypothesis: H-001 (E1)
  - targetStateX: totalSupply == 0
  - constraintProgram: `hypotheses/H-001.yaml`
- active_question: Q-003 (mode_reachability)
- questions_open: 3/10

## Next Action (MUST advance toward E3)
- next_skill: **counterexample-solver**
- why: need experiments → witnesses
- expected_artifact_delta: experiments.jsonl + convergence_delta>0
- last_decision_id: D-2026-02-02-0001
- convergence_metric: feasibility (net_profit ↑)

## Recent Evidence
- last_experiment: 2026-02-02T00:00:00Z | H-001 | fuzz | unknown

## Rehydration order (when you feel lost)
1. `focus.md`
2. `resume_pack.md`
3. `boundary/manifest.json` + `deployment_snapshot.md`
4. `hypothesis_ledger.md`
5. tail `experiments.jsonl` + `questions.jsonl`
6. `coverage/scoreboard.json`

## No-orphan-work rule
- If you cannot name the **next_skill** and the **expected artifact delta**, you are drifting.
```

### hypothesis_ledger.md

```markdown
| scenarioId | dedupKey | targetStateX | constraintProgram | status | measurableDelta | replayBundle | falsifier | lastExperiment | nextMutation | min_attacker_tier | ordering_required | expected_profit | last_costs | last_decision_id | convergence_state |
|------------|----------|--------------|-------------------|--------|-----------------|--------------|-----------|----------------|--------------|-------------------|-------------------|-----------------|-----------|------------------|-------------------|
| H-001 | vault_inflation | totalSupply==0→mint | hypotheses/H-001.yaml | E1 | pending | - | - | 2024-01-15 | expand_amounts | TIER_1_DEFI_USER | medium | 15000 | gas=0.02 ETH | D-2026-02-02-0001 | feasibility |
```

### experiments.jsonl

```json
{"scenarioId":"H-001","targetStateX":"totalSupply==0","experimentType":"fuzz","inputs":{"amounts":[1,1e18]},"outcome":"blocked","measurements":{"revert":"division by zero"},"attacker_tier":"TIER_0","ordering_power":"weak","liquidity_assumptions":{"model":"realistic_mainnet","max_move_pct":1.0},"gas_price_gwei":50,"gross_profit":"0","net_profit":"0","robustness":{"gas_price_+20%":"unprofitable"},"decision_id":"D-2026-02-02-0001","convergence_delta":{"constraint_tightening":0.2},"costs":{"gas":"50000"},"timestamp":"2024-01-15T10:00:00Z"}
```

### questions.jsonl

```json
{"qid":"Q-001","timestamp":"2024-01-15T10:00:00Z","question":"Can attacker empty vault via withdrawal?","category":"mode_reachability","related_hypothesis":"H-001","status":"open"}
```

### attacker_model.yaml

```yaml
active_tier: TIER_2_MEV_SEARCHER
identity:
  max_addresses: 10
  can_deploy_contracts: true
ordering_power: medium
flash_liquidity:
  max_eth: "100000"
  sources: [aave_v3, balancer]
multi_block:
  enabled: true
  max_block_span: 5
```

---

# PART XV: SKILL ROUTING (Canonical, Only 5 Skills)

## 15.1 Active Skills

Only these 5 skills are active. All other skills on disk are deprecated.

| Skill | Path | Purpose |
|-------|------|---------|
| system-governor | `/root/.codex/skills/system-governor/SKILL.md` | Workspace hydration, rigor gates, no-narrative enforcement |
| world-modeler | `/root/.codex/skills/world-modeler/SKILL.md` | Boundary manifest, graphs, state machine, fork reality |
| property-portfolio-compiler | `/root/.codex/skills/property-portfolio-compiler/SKILL.md` | Property portfolio, assumptions, constraint programs |
| counterexample-solver | `/root/.codex/skills/counterexample-solver/SKILL.md` | Solver portfolio, experiments, witnesses |
| proofpack-builder | `/root/.codex/skills/proofpack-builder/SKILL.md` | Replay bundles, Foundry falsifiers, E2→E3 promotion |

## 15.2 Skill Routing Table

| Gap/Need | Skill | Output |
|----------|-------|--------|
| New investigation / system files changed | system-governor | system_evaluation.md, lint results |
| Boundary / graphs / state machine missing | world-modeler | boundary/, graphs/, state_machine.md |
| Property portfolio / assumptions missing | property-portfolio-compiler | properties/* |
| Constraint programs missing | property-portfolio-compiler | hypotheses/*.yaml |
| Dependencies config missing | property-portfolio-compiler | dependencies/config.yaml |
| Coverage scoreboard missing | property-portfolio-compiler | coverage/* |
| No experiments for active hypothesis | counterexample-solver | experiments.jsonl |
| Replay bundle candidate exists | proofpack-builder | Foundry falsifier, E2/E3 |
| E3 achieved | proofpack-builder | final_report.md |

## 15.3 Skill Invocation Protocol

```
FOR EACH SKILL INVOCATION:

0. Read `focus.md` + `resume_pack.md` and restate the invariant goal (E3).
1. Update `focus.md` with **next_skill** and **why** (Purpose Lock).
2. Read the skill's SKILL.md file
3. Verify inputs exist (or trigger prerequisite skill first)
4. Execute the skill's procedure
5. Verify outputs were created
6. Run relevant lints
7. Update `focus.md` + `resume_pack.md` (Memory Lock)
8. Update hypothesis_ledger.md if applicable
9. Append to experiments.jsonl if applicable
10. Check if E3 achieved → if yes, invoke proofpack-builder

NEVER skip a skill's Completeness, Autonomy, or Complexity contracts.
```

---

# APPENDIX A: Attacker Tier Quick Reference

```
┌─────────────────────────────────────────────────────────────────────────────┐
│ TIER │ ORDERING  │ FLASH       │ MULTI-BLOCK │ MIN PROFIT  │ TYPICAL      │
│      │ POWER     │ LIQUIDITY   │             │ THRESHOLD   │ ATTACKER     │
├──────┼───────────┼─────────────┼─────────────┼─────────────┼──────────────┤
│  0   │ None      │ None        │ No          │ $100        │ Script kiddy │
│  1   │ Weak      │ Single src  │ No          │ $1,000      │ DeFi user    │
│  2   │ Medium    │ Combined    │ Limited     │ $10,000     │ MEV searcher │
│  3   │ Strong    │ Large       │ Yes         │ $100,000    │ Sophisticated│
│  4   │ Builder   │ Unlimited   │ Extended    │ $1,000,000  │ State-level  │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

# APPENDIX B: Cost Estimation Quick Reference

```
GAS COSTS (at 50 gwei, ETH=$2400):
- Simple transfer: ~21,000 gas = $2.52
- ERC20 transfer: ~65,000 gas = $7.80
- Uniswap V3 swap: ~150,000 gas = $18.00
- Complex DeFi interaction: ~500,000 gas = $60.00
- Flash loan + multi-step: ~1,000,000 gas = $120.00

PROTOCOL FEES:
- Aave flash loan: 0.05%
- Balancer flash loan: 0% (but swap fees apply)
- Uniswap V3 swap: 0.01% - 1% depending on pool
- Curve swap: 0.04% typical

MARKET IMPACT (rough estimates):
- $100k trade in major pair: <0.1%
- $1M trade in major pair: 0.1-0.5%
- $10M trade in major pair: 0.5-2%
- Illiquid pairs: significantly higher
```

---

# APPENDIX C: Coverage Checklist

```
SINK COVERAGE:
□ All transfer() calls
□ All transferFrom() calls
□ All mint() calls
□ All burn() calls
□ All external calls to user-controlled addresses
□ All delegatecall usage
□ All parameter setters
□ All role assignments

MODE COVERAGE:
□ Empty state (totalSupply=0)
□ Single unit state
□ Normal operation
□ High utilization
□ Boundary conditions
□ Oracle stale
□ Oracle extreme values

SEQUENCE COVERAGE:
□ All 2-operation permutations of critical functions
□ Deposit→Withdraw cycles
□ Borrow→Repay cycles
□ Cross-function reentrancy paths
□ Flash loan entry points

FEASIBILITY VALIDATION:
□ Gas costs calculated
□ Protocol fees included
□ Market impact modeled
□ Net profit positive
□ Robustness verified
```

---

# APPENDIX D: Non-Negotiable Posture Summary

```
1. NEVER CONCLUDE SAFETY
   - Only E3 evidence closes a hypothesis
   - Coverage is a checkpoint, not a stop condition

2. NO NARRATIVE PROGRESS
   - Progress = experiments with measured deltas
   - Artifact completion ≠ progress

3. COMPLEXITY-FIRST
   - Favor long, compositional chains
   - Favor multi-lever routes
   - Complexity = harder constraint program + more independent levers fused

4. EVIDENCE-FIRST
   - Anything important is written to artifacts
   - Nothing ephemeral matters

5. NO TAXONOMY TRAPS
   - Use open vocabulary
   - Describe real behavior, not categories

6. FEASIBILITY REQUIRED FOR FINDINGS
   - Net profit > costs under realistic conditions
   - Minimum attacker tier identified
   - Robustness verified

7. CONTINUOUS QUESTION GENERATION
   - Investigation is driven by questions
   - Questions mutate constraint programs
   - Answers spawn new questions
```

---

END OF SPECIFICATION v3.0

This document defines the complete, intelligence-grade protocol for discovering
novel, economically feasible exploits in battle-tested smart contract systems.

Key features:
1. PoS-correct timing model (slot-based, no timestamp manipulation)
2. Corrected staticcall semantics (read-only reentrancy focus)
3. First-class Feasibility & Cost Kernel
4. Parameterized attacker tiers
5. Measurable coverage scoreboard
6. Modular dependency semantics library
7. Continuous question-generation loop
8. 5-skill minimal architecture
9. E3-only stop condition

Every finding must be:
- Backed by fork execution evidence
- Economically feasible (net profit > costs)
- Labeled with minimum attacker tier
- Validated for robustness


allways for rpc and etherscan v2 api for source and abi and .. you can use rpc-etherscan.md
