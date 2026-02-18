# Assumptions — Liquity V1

## Critical Assumptions

### A1: Chainlink Oracle Price Accuracy
ASSUMPTION: fetchPrice() returns a price within ~1% of true market price
EVIDENCE IN CODE: PriceFeed.sol uses Chainlink as primary, Tellor as fallback
VIOLATION CONDITION: Chainlink oracle manipulation, stale beyond heartbeat
CONSEQUENCE: Incorrect ICR calculations → invalid liquidations or missed liquidations
VIOLATION FEASIBILITY: VERY LOW — Chainlink ETH/USD has 1% deviation threshold, 1-hour heartbeat, multi-node aggregation. Flash loans cannot manipulate.

### A2: LUSD Peg Stability ($1)
ASSUMPTION: 1 LUSD ≈ $1 for economic incentive alignment
EVIDENCE IN CODE: Redemption mechanism (LUSD→ETH at $1 face value) provides floor
VIOLATION CONDITION: LUSD depegs significantly above or below $1
CONSEQUENCE: If LUSD > $1: borrowers get cheap ETH leverage. If LUSD < $1: redemptions create peg floor
VIOLATION FEASIBILITY: MEDIUM — LUSD historically traded at slight premium during high demand

### A3: Solidity 0.6.11 SafeMath Prevents Overflow
ASSUMPTION: All arithmetic operations are checked by SafeMath
EVIDENCE IN CODE: `using SafeMath for uint` everywhere; Solidity 0.6.11 doesn't have built-in overflow checks
VIOLATION CONDITION: Any arithmetic operation NOT using SafeMath wrapper
CONSEQUENCE: Silent overflow → incorrect values → fund loss
VIOLATION FEASIBILITY: LOW — code review shows consistent SafeMath usage. No unchecked blocks (0.6.11 doesn't support them).

### A4: StabilityPool P Never Reaches 0 Without Epoch Reset
ASSUMPTION: Error correction ensures P stays positive until pool is truly emptied
EVIDENCE IN CODE: Scale factor mechanism, `assert(newP > 0)` at line 618
VIOLATION CONDITION: Rounding drives P to 0 despite non-zero deposits remaining
CONSEQUENCE: All deposits would compute to 0; ETH gains would be unclaimable
VIOLATION FEASIBILITY: EXTREMELY LOW — scale factor prevents premature P→0; assertion would revert

### A5: CEI Pattern Prevents Reentrancy
ASSUMPTION: State updates before external calls prevent reentrancy exploitation
EVIDENCE IN CODE: All functions update state (deposits, snapshots, P, S, G) before ETH transfers
VIOLATION CONDITION: State dependency that crosses the external call boundary
CONSEQUENCE: Double-claiming or state corruption
VIOLATION FEASIBILITY: NONE — code review confirms strict CEI pattern in all value-transferring functions

### A6: setAddresses Can Only Be Called Once (Ownership Renounced)
ASSUMPTION: Contract addresses are immutable after initialization
EVIDENCE IN CODE: `_renounceOwnership()` called at end of setAddresses()
VIOLATION CONDITION: Ability to call setAddresses again
CONSEQUENCE: Redirect trusted contracts → complete protocol takeover
VIOLATION FEASIBILITY: NONE — ownership is permanently renounced; no proxy, no upgradeability

### A7: ActivePool/DefaultPool ETH Tracking = Real Balance
ASSUMPTION: Internal `ETH` tracker accurately reflects available ETH
EVIDENCE IN CODE: receive() only from authorized senders; sendETH deducts tracker
VIOLATION CONDITION: ETH sent without incrementing tracker (selfdestruct) or tracker deducted without sending
CONSEQUENCE: Accounting mismatch; stuck ETH or insufficient funds for withdrawals
VIOLATION FEASIBILITY: NONE for exploitation — selfdestruct creates extra balance but internal tracker is unaffected

### A8: SortedTroves List Integrity
ASSUMPTION: Doubly linked list maintains correct ordering by NICR
EVIDENCE IN CODE: Insert/remove/reInsert operations maintain list invariants
VIOLATION CONDITION: Concurrent operations corrupt prev/next pointers
CONSEQUENCE: Liquidation/redemption skip troves or process wrong order
VIOLATION FEASIBILITY: NONE — Ethereum is single-threaded; no concurrent state modification within a tx

### A9: Flash Loan Cannot Manipulate Chainlink Oracle
ASSUMPTION: Chainlink ETH/USD price cannot be moved by flash loan actions
EVIDENCE IN CODE: PriceFeed reads from Chainlink aggregator (off-chain price feed)
VIOLATION CONDITION: Chainlink aggregator price responds to on-chain actions
CONSEQUENCE: Attacker could trigger liquidations at manipulated prices
VIOLATION FEASIBILITY: NONE — Chainlink is an off-chain oracle; on-chain swaps don't affect it

### A10: Minimum Debt (2000 LUSD) Prevents Dust Trove Exploitation
ASSUMPTION: MIN_NET_DEBT prevents economically insignificant troves
EVIDENCE IN CODE: `_requireAtLeastMinNetDebt(vars.netDebt)` in openTrove; `MIN_NET_DEBT = 1800e18`
VIOLATION CONDITION: Creating trove with less than min debt
CONSEQUENCE: Could create dust troves that are expensive to liquidate relative to their value
VIOLATION FEASIBILITY: NONE — minimum debt check enforced in all trove creation paths
