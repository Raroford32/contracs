Read contract complete code, reasoning how it could bring error? Not talking about traditional vuln patterns - mean over complex human impossible to detect situations bringing unexpected asset draining possibility completely for an unprivileged attacker.

You can use etherscanrpc.md, and has to validate any exploit scenario that show significant loss of funds without limitations of external conditions, on foundry current mainnet fork.

You can't pause or stop till reach goal, until then route among contracts.txt till find out what needed.

## PERSISTENCE REQUIREMENTS:

1. **NEVER GIVE UP** - Keep iterating until no other possible way or try exists for a contract
2. **ON FAILURE** - Brainstorm alternative approaches, break through any walls, try different angles
3. **ITERATION** - Failed execution means try again with modified parameters, not abandon
4. **EXHAUSTIVE** - Test every function, every edge case, every parameter combination
5. **CREATIVE** - Think beyond obvious patterns, combine multiple vectors, chain interactions

## STRICT REQUIREMENTS FOR VALID EXPLOITS:

1. **IMMEDIATE EXECUTION ONLY** - No scenarios requiring time locks, waiting periods, days/weeks delays. Attack must be executable in single transaction or same block.

2. **EXACT PROFIT CALCULATION** - Must calculate exact profit in USD/ETH with real token prices. No "potential" or "probable" profits. Show exact numbers.

3. **REAL PARAMETERS REQUIRED** - Every exploit must include:
   - Exact contract addresses (checksummed)
   - Exact function signatures
   - Exact calldata/parameters
   - Exact token amounts
   - Current on-chain state values

4. **WORKING POC MANDATORY** - Every finding must have Foundry test that:
   - Runs successfully on mainnet fork
   - Shows attacker balance BEFORE and AFTER
   - Calculates exact profit = AFTER - BEFORE - gas costs
   - Profit must be > $1000 USD to be valid

5. **ZERO CAPITAL ATTACKS PREFERRED** - Focus on:
   - Flash loan attacks (Aave, Balancer, dYdX)
   - Reentrancy with borrowed funds
   - Price manipulation in single tx
   - Logic bugs exploitable without capital

6. **EXCLUDE THESE SCENARIOS**:
   - Governance attacks requiring voting periods
   - Time-locked withdrawals
   - Scenarios requiring admin keys
   - MEV that requires block builder access
   - Anything requiring > 1 block to execute

7. **VALIDATION CRITERIA**:
   ```
   VALID: Flash loan 1M USDC -> exploit -> repay -> profit 50,000 USDC (exact)
   INVALID: "If attacker waits 7 days, they could potentially profit..."
   INVALID: "Attacker might capture ~90% of rewards..."
   ```

8. **OUTPUT FORMAT FOR EACH FINDING**:
   ```
   Contract: 0x... (checksummed)
   Function: functionName(params)
   Attack Cost: X ETH (gas only) or Flash loan fee
   Exact Profit: Y tokens = $Z USD
   Execution: Single transaction
   PoC: test/ExploitName.t.sol - PASSING
   ```
