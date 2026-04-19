// SPDX-License-Identifier: MIT
pragma solidity ^0.8.19;
import "forge-std/Test.sol";

interface ICToken {
    function mint(uint256) external returns (uint256);
    function redeem(uint256) external returns (uint256);
    function redeemUnderlying(uint256) external returns (uint256);
    function exchangeRateStored() external view returns (uint256);
    function exchangeRateCurrent() external returns (uint256);
    function accrueInterest() external returns (uint256);
    function totalBorrows() external view returns (uint256);
    function totalReserves() external view returns (uint256);
    function totalSupply() external view returns (uint256);
    function balanceOf(address) external view returns (uint256);
    function getCash() external view returns (uint256);
}
interface IERC20 { function approve(address,uint256) external returns (bool); function balanceOf(address) external view returns (uint256); function transfer(address,uint256) external returns (bool); }

contract PUSDCStale is Test {
    address constant CT = 0x0f69f08f872F366AD8EDdE03DAE8812619A17536;
    address constant USDC = 0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48;

    function setUp() public { vm.createSelectFork("mainnet"); }

    function test_state() public view {
        console2.log("ER stored:", ICToken(CT).exchangeRateStored());
        console2.log("totalBorrows:", ICToken(CT).totalBorrows());
        console2.log("totalReserves:", ICToken(CT).totalReserves());
        console2.log("totalSupply:", ICToken(CT).totalSupply());
        console2.log("getCash:", ICToken(CT).getCash());
    }

    function test_can_accrue() public {
        try ICToken(CT).accrueInterest() returns (uint256 e) {
            console2.log("accrueInterest returned:", e);
            console2.log("ER after:", ICToken(CT).exchangeRateStored());
            console2.log("totalBorrows after:", ICToken(CT).totalBorrows());
        } catch {
            console2.log("accrueInterest REVERTED");
        }
    }

    function test_can_mint_redeem() public {
        deal(USDC, address(this), 100_000_000);  // 100 USDC
        IERC20(USDC).approve(CT, type(uint256).max);

        uint256 cTokensBefore = ICToken(CT).balanceOf(address(this));
        uint256 usdcBefore = IERC20(USDC).balanceOf(address(this));

        try ICToken(CT).mint(100_000_000) returns (uint256 err) {
            console2.log("mint returned err code:", err);
        } catch {
            console2.log("mint REVERTED");
            return;
        }

        uint256 cTokensAfter = ICToken(CT).balanceOf(address(this));
        console2.log("pUSDC minted:", cTokensAfter - cTokensBefore);

        // Try redeem all
        uint256 minted = cTokensAfter - cTokensBefore;
        try ICToken(CT).redeem(minted) returns (uint256 err) {
            console2.log("redeem returned err code:", err);
        } catch {
            console2.log("redeem REVERTED");
        }
        uint256 usdcAfter = IERC20(USDC).balanceOf(address(this));
        if (usdcAfter > usdcBefore) {
            console2.log("USDC PROFIT (raw):", usdcAfter - usdcBefore);
        } else {
            console2.log("USDC LOSS (raw):", usdcBefore - usdcAfter);
        }
    }
}
