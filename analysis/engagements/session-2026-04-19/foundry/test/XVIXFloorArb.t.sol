// SPDX-License-Identifier: MIT
pragma solidity ^0.8.19;

import "forge-std/Test.sol";

interface IERC20 {
    function balanceOf(address) external view returns (uint256);
    function approve(address, uint256) external returns (bool);
    function transfer(address, uint256) external returns (bool);
    function totalSupply() external view returns (uint256);
}

interface IUniV2Pair {
    function swap(uint amount0Out, uint amount1Out, address to, bytes calldata data) external;
    function getReserves() external view returns (uint112, uint112, uint32);
    function token0() external view returns (address);
    function token1() external view returns (address);
}

interface IWETH is IERC20 {
    function deposit() external payable;
    function withdraw(uint256) external;
}

interface IFloor {
    function refund(address receiver, uint256 burnAmount) external returns (uint256);
    function capital() external view returns (uint256);
    function getRefundAmount(uint256) external view returns (uint256);
}

contract XVIXFloorArbTest is Test {
    address constant XVIX = 0x4bAE380B5D762D543d426331b8437926443ae9ec;
    address constant WETH = 0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2;
    address constant FLOOR = 0x40ED3699C2fFe43939ecf2F3d11F633b522820aD;
    address constant PAIR = 0x619aAa52a10F196e521F823aeD4CdeA30D45D366;

    function setUp() public {
        vm.createSelectFork("mainnet");
    }

    function test_arb_small() public {
        _tryArb(0.01 ether);
        _tryArb(0.05 ether);
        _tryArb(0.1 ether);
        _tryArb(0.5 ether);
        _tryArb(1 ether);
        _tryArb(5 ether);
    }

    function _tryArb(uint256 wethIn) internal {
        vm.deal(address(this), wethIn + 1 ether);
        uint256 ethBefore = address(this).balance;

        IWETH(WETH).deposit{value: wethIn}();
        IERC20(WETH).transfer(PAIR, wethIn);
        uint256 xvixOut = _computeOut(wethIn);
        IUniV2Pair(PAIR).swap(xvixOut, 0, address(this), "");
        uint256 xvixReceived = IERC20(XVIX).balanceOf(address(this));
        IFloor(FLOOR).refund(address(this), xvixReceived);
        uint256 ethAfter = address(this).balance;

        console2.log("===================");
        console2.log("WETH in:", wethIn);
        console2.log("XVIX received:", xvixReceived);
        _logProfit(ethBefore, ethAfter);
    }

    function _computeOut(uint256 wethIn) internal view returns (uint256) {
        (uint112 r0, uint112 r1,) = IUniV2Pair(PAIR).getReserves();
        require(IUniV2Pair(PAIR).token0() == XVIX, "tok0");
        uint256 amountInWithFee = wethIn * 997;
        uint256 numer = amountInWithFee * r0;
        uint256 denom = (uint256(r1) * 1000) + amountInWithFee;
        return numer / denom;
    }

    function _logProfit(uint256 a, uint256 b) internal view {
        console2.log("ETH before:", a);
        console2.log("ETH after:", b);
        if (b >= a) console2.log("PROFIT (wei):", b - a);
        else console2.log("LOSS (wei):", a - b);
    }

    receive() external payable {}
}
