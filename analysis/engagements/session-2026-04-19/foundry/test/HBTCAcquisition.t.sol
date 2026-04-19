// SPDX-License-Identifier: MIT
pragma solidity ^0.8.19;

import "forge-std/Test.sol";

interface IERC20 {
    function balanceOf(address) external view returns (uint256);
    function approve(address, uint256) external returns (bool);
    function transfer(address, uint256) external returns (bool);
    function allowance(address, address) external view returns (uint256);
}

interface ICurve {
    function exchange(int128, int128, uint256, uint256) external returns (uint256);
    function get_dy(int128, int128, uint256) external view returns (uint256);
}

contract HBTCAcquisition is Test {
    address constant HBTC = 0x0316EB71485b0Ab14103307bf65a021042c6d380;
    address constant WBTC = 0x2260FAC5E5542a773Aa44fBCfeDf7C193bc2C599;
    address constant CURVE = 0x4CA9b3063Ec5866A4B82E437059D2C43d1be596F;

    function setUp() public { vm.createSelectFork("mainnet"); }

    function test_actual_swap_rates() public {
        // Test actually-executable swaps (not just get_dy)
        uint256[5] memory sizes = [uint256(1e5), 1e6, 5e6, 1e7, 2e7]; // 0.001 to 0.2 WBTC
        for (uint256 i = 0; i < 5; i++) {
            uint256 snap = vm.snapshotState();
            _trySwap(sizes[i]);
            vm.revertToState(snap);
        }
    }

    // Check what 1 HBTC sells for in WBTC (reverse direction)
    // This tells us: what does Curve actually VALUE 1 HBTC at?
    function test_hbtc_to_wbtc_rate() public view {
        // exchange(0=HBTC, 1=WBTC, amount, 0)
        uint256[5] memory hbtcAmounts = [
            uint256(1e17),   // 0.1 HBTC
            uint256(5e17),   // 0.5 HBTC
            uint256(1 ether),// 1 HBTC
            uint256(15e17),  // 1.5 HBTC
            uint256(179e16)  // 1.79 HBTC (near max pool reserve)
        ];
        for (uint256 i = 0; i < 5; i++) {
            uint256 h = hbtcAmounts[i];
            uint256 wbtcOut = ICurve(CURVE).get_dy(0, 1, h);
            console2.log("=== HBTC->WBTC ===");
            console2.log("HBTC in (18dec):", h);
            console2.log("WBTC out (8dec):", wbtcOut);
            // WBTC per HBTC in 8-dec terms
            // wbtcOut/1e8 / (h/1e18) = wbtcOut * 1e18 / h / 1e8 = wbtcOut * 1e10 / h
            console2.log("WBTC per HBTC (ratio*1e4):", (wbtcOut * 1e4 * 1e10) / h);
            // Effective USDT value at $75573/WBTC: wbtcOut * 75573 / 1e8
            console2.log("USD value per HBTC (approx):", (wbtcOut * 75573) / 1e8);
        }
        // What are the pool reserves?
        console2.log("Pool HBTC reserve:", IERC20(HBTC).balanceOf(CURVE));
        console2.log("Pool WBTC reserve:", IERC20(WBTC).balanceOf(CURVE));
    }

    function _trySwap(uint256 wbtcIn) internal {
        deal(WBTC, address(this), wbtcIn);
        IERC20(WBTC).approve(CURVE, type(uint256).max);

        uint256 expected = ICurve(CURVE).get_dy(1, 0, wbtcIn);
        uint256 hbtcBefore = IERC20(HBTC).balanceOf(address(this));

        // Use low-level call to avoid ABI decode failure when old Vyper pool returns STOP
        bytes memory callData = abi.encodeWithSelector(
            bytes4(keccak256("exchange(int128,int128,uint256,uint256)")),
            int128(1), int128(0), wbtcIn, uint256(0)
        );
        (bool ok,) = CURVE.call(callData);

        uint256 hbtcAfter = IERC20(HBTC).balanceOf(address(this));
        uint256 out = hbtcAfter - hbtcBefore;

        console2.log("=== swap ===");
        console2.log("WBTC in (raw 8dec):", wbtcIn);
        if (ok) {
            console2.log("HBTC out (raw 18dec):", out);
            console2.log("expected get_dy:", expected);
            if (wbtcIn > 0) {
                // cost in HBTC-equivalent: wbtcIn scaled to 18 dec
                uint256 wbtcIn18 = wbtcIn * 1e10;
                // HBTC per WBTC ratio * 10000
                console2.log("HBTC/WBTC ratio * 1e4:", (out * 1e4) / wbtcIn18);
                // Effective WBTC cost per HBTC (8 dec): wbtcIn / (out/1e18) = wbtcIn * 1e18 / out
                if (out > 0) console2.log("Effective WBTC cost per 1 HBTC (8dec):", (wbtcIn * 1e18) / out);
            }
        } else {
            console2.log("swap reverted");
        }
    }
}
