// SPDX-License-Identifier: MIT
pragma solidity ^0.8.19;

import "forge-std/Test.sol";

interface IERC20 {
    function balanceOf(address) external view returns (uint256);
    function approve(address, uint256) external returns (bool);
    function transfer(address, uint256) external returns (bool);
}

interface IUniV3Pool {
    function flash(address recipient, uint256 amount0, uint256 amount1, bytes calldata data) external;
    function liquidity() external view returns (uint128);
    function token0() external view returns (address);
    function token1() external view returns (address);
    function fee() external view returns (uint24);
    function slot0() external view returns (uint160, int24, uint16, uint16, uint16, uint8, bool);
}

interface IUniV2Pair {
    function swap(uint256 amount0Out, uint256 amount1Out, address to, bytes calldata data) external;
    function getReserves() external view returns (uint112, uint112, uint32);
    function token0() external view returns (address);
    function token1() external view returns (address);
}

interface IUniV2Factory {
    function getPair(address, address) external view returns (address);
}

interface IUniV3Factory {
    function getPool(address, address, uint24) external view returns (address);
}

/// Probe every flash-primitive path for HBTC:
///   UniV3 flash() on each fee tier (uses pool reserves, not active liquidity)
///   UniV2 flash-swap on the canonical HBTC pair (if any)
///   Balancer flash loan for HBTC (negative control)
contract HBTCFlashSwap is Test {
    address constant HBTC = 0x0316EB71485b0Ab14103307bf65a021042c6d380;
    address constant WBTC = 0x2260FAC5E5542a773Aa44fBCfeDf7C193bc2C599;
    address constant USDT = 0xdAC17F958D2ee523a2206206994597C13D831ec7;
    address constant WETH = 0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2;

    address constant UNIV3_FACTORY = 0x1F98431c8aD98523631AE4a59f267346ea31F984;
    address constant UNIV2_FACTORY = 0x5C69bEe701ef814a2B6a3EDD4B1652CB9cc5aA6f;
    address constant SUSHI_FACTORY  = 0xC0AEe478e3658e2610c5F7A4A2E1777cE9e4f2Ac;
    address constant BALANCER_VAULT = 0xBA12222222228d8Ba445958a75a0704d566BF2C8;

    function setUp() public { vm.createSelectFork("mainnet"); }

    // -------- UniV3 flash probes --------

    /// flash() succeeds if the pool holds token reserves regardless of active liquidity.
    /// Repay requirement: fee only (amount * fee/1e6).
    function test_univ3_flash_probe_all_fee_tiers() public {
        uint24[4] memory fees = [uint24(100), uint24(500), uint24(3000), uint24(10000)];
        for (uint256 i = 0; i < 4; i++) {
            address pool = IUniV3Factory(UNIV3_FACTORY).getPool(HBTC, WBTC, fees[i]);
            console2.log("=== UniV3 HBTC/WBTC fee ===", fees[i]);
            console2.log("pool:", pool);
            if (pool == address(0)) { console2.log("no pool"); continue; }
            console2.log("HBTC reserve:", IERC20(HBTC).balanceOf(pool));
            console2.log("WBTC reserve:", IERC20(WBTC).balanceOf(pool));
            console2.log("active liquidity:", IUniV3Pool(pool).liquidity());
        }
        // Also test HBTC/USDT and HBTC/WETH
        address[2] memory others = [USDT, WETH];
        for (uint256 j = 0; j < 2; j++) {
            for (uint256 i = 0; i < 4; i++) {
                address pool = IUniV3Factory(UNIV3_FACTORY).getPool(HBTC, others[j], fees[i]);
                if (pool == address(0)) continue;
                console2.log("=== UniV3 HBTC/other fee ===", fees[i]);
                console2.log("other:", others[j]);
                console2.log("pool:", pool);
                console2.log("HBTC reserve:", IERC20(HBTC).balanceOf(pool));
                console2.log("other reserve:", IERC20(others[j]).balanceOf(pool));
                console2.log("active liquidity:", IUniV3Pool(pool).liquidity());
            }
        }
    }

    /// Actually attempt flash on any UniV3 pool that holds HBTC.
    function test_univ3_flash_execute() public {
        uint24[4] memory fees = [uint24(100), uint24(500), uint24(3000), uint24(10000)];
        for (uint256 i = 0; i < 4; i++) {
            address pool = IUniV3Factory(UNIV3_FACTORY).getPool(HBTC, WBTC, fees[i]);
            if (pool == address(0)) continue;
            uint256 hbtcRes = IERC20(HBTC).balanceOf(pool);
            if (hbtcRes == 0) continue;
            address t0 = IUniV3Pool(pool).token0();
            uint256 amt0; uint256 amt1;
            uint256 want = hbtcRes; // try max
            if (t0 == HBTC) { amt0 = want; amt1 = 0; } else { amt0 = 0; amt1 = want; }
            console2.log("attempting UniV3 flash on pool:", pool);
            console2.log("requesting HBTC amount:", want);
            _flashCallbackFee = fees[i];
            try IUniV3Pool(pool).flash(address(this), amt0, amt1, abi.encode(pool)) {
                console2.log("FLASH OK fee:", fees[i]);
            } catch Error(string memory r) {
                console2.log("flash reverted:", r);
            } catch (bytes memory) {
                console2.log("flash reverted (no data)");
            }
        }
    }

    uint24 _flashCallbackFee;

    function uniswapV3FlashCallback(uint256 fee0, uint256 fee1, bytes calldata data) external {
        address pool = abi.decode(data, (address));
        require(msg.sender == pool, "auth");
        console2.log("flash callback fee0:", fee0);
        console2.log("flash callback fee1:", fee1);
        // repay: transfer back amount + fee (we don't actually have funds so this will revert)
        // but the point is to prove the call entered the callback with HBTC delivered
        uint256 hbtcHeld = IERC20(HBTC).balanceOf(address(this));
        console2.log("HBTC delivered to borrower:", hbtcHeld);
        // Revert cleanly so state is unchanged; the log above is what we need.
        revert("probe-only");
    }

    // -------- UniV2 flash-swap probes --------

    function test_univ2_hbtc_pairs() public view {
        address[4] memory counters = [WBTC, USDT, WETH, 0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48];
        string[4] memory names = ["WBTC", "USDT", "WETH", "USDC"];
        for (uint256 i = 0; i < 4; i++) {
            address p = IUniV2Factory(UNIV2_FACTORY).getPair(HBTC, counters[i]);
            address ps = IUniV2Factory(SUSHI_FACTORY).getPair(HBTC, counters[i]);
            console2.log("=== UniV2 HBTC/X ===");
            console2.log("counter:", names[i]);
            console2.log("univ2:", p);
            console2.log("sushi:", ps);
            if (p != address(0)) {
                console2.log("  v2 HBTC bal:", IERC20(HBTC).balanceOf(p));
                console2.log("  v2 X    bal:", IERC20(counters[i]).balanceOf(p));
            }
            if (ps != address(0)) {
                console2.log("  sushi HBTC bal:", IERC20(HBTC).balanceOf(ps));
                console2.log("  sushi X    bal:", IERC20(counters[i]).balanceOf(ps));
            }
        }
    }

    // -------- Balancer (negative control) --------

    function test_balancer_hbtc_balance() public view {
        uint256 bal = IERC20(HBTC).balanceOf(BALANCER_VAULT);
        console2.log("Balancer HBTC balance:", bal);
        console2.log("Balancer WBTC balance:", IERC20(WBTC).balanceOf(BALANCER_VAULT));
    }
}
