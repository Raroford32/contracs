// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

/**
 * @title VulnerableVault - Complex DeFi Protocol with Multiple Sophisticated Vulnerabilities
 * @author Security Research Team
 * @notice WARNING: DO NOT USE IN PRODUCTION - FOR EDUCATIONAL PURPOSES ONLY
 * 
 * This contract demonstrates multiple complex, real-world vulnerabilities that require
 * deep understanding of DeFi mechanics, MEV, and protocol composition.
 * 
 * COMPLEX VULNERABILITIES DEMONSTRATED (2026 Level):
 * 
 * 1. CROSS-FUNCTION REENTRANCY WITH STATE INCONSISTENCY
 *    - Not a simple same-function reentrancy
 *    - Exploits state dependencies across withdraw() and borrow()
 *    - Requires precise timing and state manipulation
 * 
 * 2. READ-ONLY REENTRANCY PATTERN
 *    - During withdraw, attacker can call view functions that read stale state
 *    - Inflated collateral value used to borrow excess funds
 *    - Multi-contract exploitation vector
 * 
 * 3. ORACLE MANIPULATION VIA FLASH LOAN
 *    - Spot price oracle can be manipulated
 *    - Requires understanding of AMM mechanics
 *    - Multi-step attack: flash loan → manipulate → borrow → repay
 * 
 * 4. ERC-4626 INFLATION ATTACK
 *    - First depositor can manipulate share price
 *    - Donation attack to inflate share value
 *    - Subsequent depositors lose funds due to rounding
 * 
 * 5. PRECISION LOSS IN COMPLEX CALCULATIONS
 *    - Division before multiplication in share calculations
 *    - Accumulates across multiple operations
 *    - Can be exploited to drain vault over time
 * 
 * 6. MEV-EXPLOITABLE LIQUIDATIONS
 *    - Predictable liquidation triggers
 *    - Fixed bonus creates frontrunning opportunity
 *    - No slippage protection or partial liquidation
 * 
 * 7. FLASH LOAN GOVERNANCE ATTACK
 *    - Borrow tokens, vote, return in same transaction
 *    - No snapshot mechanism or time-lock
 *    - Can execute proposals immediately
 * 
 * 8. UNCHECKED EXTERNAL CALL RETURNS
 *    - State changes despite failed transfers
 *    - Can be exploited with malicious ERC20 tokens
 */

interface IERC20 {
    function totalSupply() external view returns (uint256);
    function balanceOf(address account) external view returns (uint256);
    function transfer(address recipient, uint256 amount) external returns (bool);
    function allowance(address owner, address spender) external view returns (uint256);
    function approve(address spender, uint256 amount) external returns (bool);
    function transferFrom(address sender, address recipient, uint256 amount) external returns (bool);
}

interface IOracle {
    function getPrice(address token) external view returns (uint256);
}

contract VulnerableVault {
    IERC20 public immutable asset;
    IOracle public oracle;
    
    string public name = "Vulnerable Vault Shares";
    string public symbol = "vVAULT";
    uint8 public constant decimals = 18;
    
    mapping(address => uint256) public shareBalances;
    uint256 public totalShares;
    
    mapping(address => uint256) public borrowed;
    uint256 public totalBorrowed;
    
    mapping(address => uint256) public lastDepositTime;
    mapping(address => bool) public isWithdrawing;
    
    uint256 public constant LIQUIDATION_THRESHOLD = 150; // 150%
    uint256 public constant LIQUIDATION_BONUS = 110; // 110%
    uint256 public constant BORROW_RATE = 5; // 5%
    
    event Deposit(address indexed user, uint256 assets, uint256 shares);
    event Withdraw(address indexed user, uint256 assets, uint256 shares);
    event Borrow(address indexed user, uint256 amount);
    event Repay(address indexed user, uint256 amount);
    event Liquidate(address indexed liquidator, address indexed user, uint256 amount);
    
    constructor(address _asset, address _oracle) {
        asset = IERC20(_asset);
        oracle = IOracle(_oracle);
    }
    
    /**
     * @notice VULNERABILITY 1: ERC-4626 Inflation Attack
     * @dev First depositor can manipulate share price by donating assets
     * 
     * Attack: 
     * 1. Attacker deposits 1 wei, gets 1 share
     * 2. Attacker donates 1000 ether directly to vault
     * 3. Next depositor deposits 999 ether, gets 0 shares (rounds down)
     * 4. Attacker withdraws, steals the 999 ether
     */
    function deposit(uint256 assets) external returns (uint256 shares) {
        require(assets > 0, "Cannot deposit 0");
        
        // VULNERABLE: No minimum shares requirement
        if (totalShares == 0) {
            shares = assets;
        } else {
            // VULNERABLE: Uses balanceOf which includes donations
            uint256 totalAssets = asset.balanceOf(address(this)) - totalBorrowed;
            // VULNERABLE: Division before multiplication
            shares = (assets * totalShares) / totalAssets;
        }
        
        require(shares > 0, "Shares must be > 0");
        
        shareBalances[msg.sender] += shares;
        totalShares += shares;
        lastDepositTime[msg.sender] = block.timestamp;
        
        // State updated before external call
        require(asset.transferFrom(msg.sender, address(this), assets), "Transfer failed");
        
        emit Deposit(msg.sender, assets, shares);
    }
    
    /**
     * @notice VULNERABILITY 2 & 3: Cross-Function Reentrancy + Read-Only Reentrancy
     * @dev While withdrawing, attacker can reenter via borrow() using inflated collateral
     * 
     * Attack Flow:
     * 1. User calls withdraw()
     * 2. During asset.transfer(), attacker's contract is called
     * 3. In receive(), attacker calls borrow()
     * 4. getCollateralValue() reads stale shareBalances (not yet decremented)
     * 5. Attacker borrows more than they should be able to
     * 6. Withdraw completes, shares are decremented
     * 7. Attacker now has excess borrowed funds with insufficient collateral
     */
    function withdraw(uint256 shares) external returns (uint256 assets) {
        require(shares > 0, "Cannot withdraw 0");
        require(shareBalances[msg.sender] >= shares, "Insufficient shares");
        require(!isWithdrawing[msg.sender], "Reentrant call");
        
        isWithdrawing[msg.sender] = true;
        
        uint256 totalAssets = asset.balanceOf(address(this)) - totalBorrowed;
        assets = (shares * totalAssets) / totalShares;
        
        // VULNERABLE: Shares decremented but external call allows reentry
        shareBalances[msg.sender] -= shares;
        totalShares -= shares;
        
        // VULNERABLE: External call while state is inconsistent
        // getCollateralValue() in borrow() will read OLD shareBalances
        require(asset.transfer(msg.sender, assets), "Transfer failed");
        
        isWithdrawing[msg.sender] = false;
        
        emit Withdraw(msg.sender, assets, shares);
    }
    
    /**
     * @notice VULNERABILITY 4: Oracle Manipulation via Flash Loan
     * @dev Borrow amount is based on oracle price that can be manipulated
     * 
     * Attack:
     * 1. Flash loan large amount of tokens
     * 2. Swap to manipulate oracle spot price upward
     * 3. Deposit collateral (now worth more due to manipulated price)
     * 4. Borrow maximum based on inflated price
     * 5. Let price return to normal
     * 6. Undercollateralized position, profit from borrowed funds
     * 7. Repay flash loan
     */
    function borrow(uint256 amount) external {
        require(amount > 0, "Cannot borrow 0");
        require(!isWithdrawing[msg.sender], "Cannot borrow while withdrawing");
        
        // VULNERABLE: Oracle price can be manipulated with flash loan
        uint256 collateralValue = getCollateralValue(msg.sender);
        uint256 borrowedValue = borrowed[msg.sender] + amount;
        
        require(
            collateralValue * 100 >= borrowedValue * LIQUIDATION_THRESHOLD,
            "Insufficient collateral"
        );
        
        borrowed[msg.sender] += amount;
        totalBorrowed += amount;
        
        // VULNERABLE: No reentrancy guard - can be called during withdraw
        require(asset.transfer(msg.sender, amount), "Transfer failed");
        
        emit Borrow(msg.sender, amount);
    }
    
    function repay(uint256 amount) external {
        require(amount > 0, "Cannot repay 0");
        require(borrowed[msg.sender] >= amount, "Repaying too much");
        
        borrowed[msg.sender] -= amount;
        totalBorrowed -= amount;
        
        require(asset.transferFrom(msg.sender, address(this), amount), "Transfer failed");
        
        emit Repay(msg.sender, amount);
    }
    
    /**
     * @notice VULNERABILITY 5: MEV-Exploitable Liquidation
     * @dev Liquidations are predictable and can be front-run
     * 
     * MEV Attack:
     * 1. Monitor mempool for liquidatable positions
     * 2. Front-run liquidation transaction with higher gas
     * 3. Capture 10% liquidation bonus
     * 4. Fixed bonus regardless of market conditions
     * 5. No partial liquidation - entire position liquidated at once
     */
    function liquidate(address user) external {
        require(user != msg.sender, "Cannot liquidate self");
        
        uint256 collateralValue = getCollateralValue(user);
        uint256 borrowedValue = getBorrowedValueWithInterest(user);
        
        require(
            collateralValue * 100 < borrowedValue * LIQUIDATION_THRESHOLD,
            "User is not liquidatable"
        );
        
        // VULNERABLE: Fixed 10% bonus creates MEV opportunity
        uint256 liquidationAmount = borrowed[user];
        uint256 collateralToSeize = (liquidationAmount * LIQUIDATION_BONUS) / 100;
        
        // VULNERABLE: No slippage protection
        uint256 sharesToSeize = (collateralToSeize * totalShares) / 
            (asset.balanceOf(address(this)) - totalBorrowed);
        
        require(shareBalances[user] >= sharesToSeize, "Insufficient shares");
        
        shareBalances[user] -= sharesToSeize;
        shareBalances[msg.sender] += sharesToSeize;
        
        totalBorrowed -= borrowed[user];
        borrowed[user] = 0;
        
        // VULNERABLE: No verification liquidator paid the debt
        emit Liquidate(msg.sender, user, liquidationAmount);
    }
    
    /**
     * @notice View function that reads state during reentrancy
     * @dev This is called by borrow() during withdraw reentrancy attack
     */
    function getCollateralValue(address user) public view returns (uint256) {
        if (totalShares == 0) return 0;
        
        uint256 userShares = shareBalances[user];
        uint256 totalAssets = asset.balanceOf(address(this)) - totalBorrowed;
        uint256 userAssets = (userShares * totalAssets) / totalShares;
        
        // VULNERABLE: Spot price from oracle
        uint256 price = oracle.getPrice(address(asset));
        return userAssets * price / 1e18;
    }
    
    /**
     * @notice VULNERABILITY 6: Precision Loss in Interest Calculation
     * @dev Simple interest can be manipulated via timing
     */
    function getBorrowedValueWithInterest(address user) public view returns (uint256) {
        uint256 principal = borrowed[user];
        if (principal == 0) return 0;
        
        // VULNERABLE: No compound interest tracking
        uint256 timeBorrowed = block.timestamp - lastDepositTime[user];
        uint256 interest = (principal * BORROW_RATE * timeBorrowed) / (365 days * 100);
        
        return principal + interest;
    }
    
    /**
     * @notice VULNERABILITY 7: No Access Control on Emergency Function
     * @dev Anyone can drain any token from the contract
     */
    function emergencyWithdraw(address token, uint256 amount) external {
        // VULNERABLE: No access control!
        IERC20(token).transfer(msg.sender, amount);
    }
}

/**
 * @title ManipulableOracle
 * @notice Oracle using spot price from DEX - vulnerable to flash loan manipulation
 */
contract ManipulableOracle is IOracle {
    mapping(address => uint256) public prices;
    
    /**
     * @notice VULNERABLE: Spot price without TWAP protection
     * @dev In production, this would read from pool reserves
     * Can be manipulated in single transaction via flash loan
     */
    function getPrice(address token) external view override returns (uint256) {
        return prices[token];
    }
    
    // VULNERABLE: No access control on price updates
    function setPrice(address token, uint256 price) external {
        prices[token] = price;
    }
}
