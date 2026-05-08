// SPDX-License-Identifier: BUSL-1.1
pragma solidity ^0.8.28;

import {IDepositModule} from "../../../interfaces/IDepositModule.sol";
import {IMarketHub} from "../../../interfaces/IMarketHub.sol";
import {ApprovedCall, IPDepositBox} from "../../../interfaces/IPDepositBox.sol";
import {IPDepositBoxFactory} from "../../../interfaces/IPDepositBoxFactory.sol";
import {IWETH} from "../../../interfaces/IWETH.sol";
import {Err} from "../../../lib/Errors.sol";
import {TokenHelper} from "../../../lib/TokenHelper.sol";
import {PMath} from "../../../lib/math/PMath.sol";
import {AccountLib, MarketAcc} from "../../../types/Account.sol";
import {TokenId} from "../../../types/MarketTypes.sol";
import {AuthBase} from "../auth-base/AuthBase.sol";

contract DepositModule is IDepositModule, AuthBase, TokenHelper {
    using AccountLib for address;

    address internal immutable _WETH;
    IMarketHub internal immutable _MARKET_HUB;

    IPDepositBoxFactory public immutable DEPOSIT_BOX_FACTORY;

    uint32 public constant DIRECT_DEPOSIT_BOX_ID = 0;
    uint32 public constant CASH_SWAP_BOX_ID = type(uint32).max;

    constructor(address weth_, address marketHub_, address depositBoxFactory_) {
        _WETH = weth_;
        _MARKET_HUB = IMarketHub(marketHub_);
        DEPOSIT_BOX_FACTORY = IPDepositBoxFactory(depositBoxFactory_);
    }

    /// @dev must not use setAuth/setNonAuth because this function handles execution to user-specified swap router
    function depositFromBox(DepositFromBoxMessage memory message, bytes memory signature) external onlyRelayer {
        _verifyIntentSigAndMarkExecuted(message.root, message.expiry, _hashDepositFromBoxMessage(message), signature);

        (uint256 actualSpent, uint256 netTokenReceived) = _swapForDeposit(message);

        uint256 payTreasuryAmount = message.payTreasuryAmount;
        uint256 depositAmount = netTokenReceived - payTreasuryAmount;
        require(depositAmount >= message.minDepositAmount, Err.InsufficientDepositAmount());

        if (depositAmount > 0) {
            MarketAcc acc = AccountLib.from(message.root, message.accountId, message.tokenId, message.marketId);
            _MARKET_HUB.vaultDeposit(acc, depositAmount);
        }

        if (payTreasuryAmount > 0) {
            _MARKET_HUB.vaultPayTreasury(message.root, message.tokenId, payTreasuryAmount);
        }

        emit DepositFromBox(
            message.root,
            message.boxId,
            message.tokenSpent,
            actualSpent,
            message.accountId,
            message.tokenId,
            message.marketId,
            depositAmount,
            payTreasuryAmount
        );
    }

    /// @dev no setAuth because this function does not delegate call
    function directDepositFromBox(address root, address tokenSpent, TokenId tokenId) external onlyRelayer {
        IPDepositBox box = DEPOSIT_BOX_FACTORY.deployDepositBox(root, DIRECT_DEPOSIT_BOX_ID);
        uint256 amount = _balanceOf(address(box), tokenSpent);

        address tokenDeposit = _MARKET_HUB.tokenIdToAddress(tokenId);
        if (tokenSpent == NATIVE && tokenDeposit == _WETH) {
            _wrapEthInBox(box, amount);
        } else {
            require(tokenSpent == tokenDeposit, Err.InvalidDepositToken());
        }
        box.withdrawTo(address(this), tokenDeposit, amount);

        MarketAcc acc = root.toMainCross(tokenId);
        _MARKET_HUB.vaultDeposit(acc, amount);

        emit DepositFromBox(
            root,
            DIRECT_DEPOSIT_BOX_ID,
            tokenSpent,
            amount, // amountSpent
            acc.accountId(),
            acc.tokenId(),
            acc.marketId(),
            amount, // depositAmount
            0 // payTreasuryAmount
        );
    }

    /// @dev no setAuth because this function does not delegate call
    function withdrawFromBox(WithdrawFromBoxMessage memory message, bytes memory signature) external onlyRelayer {
        _verifyIntentSigAndMarkExecuted(message.root, message.expiry, _hashWithdrawFromBoxMessage(message), signature);

        IPDepositBox box = DEPOSIT_BOX_FACTORY.deployDepositBox(message.root, message.boxId);
        box.withdrawTo(message.root, message.token, message.amount);

        emit WithdrawFromBox(message.root, message.boxId, message.token, message.amount);
    }

    /// @dev must not use setAuth/setNonAuth because this function handles execution to user-specified swap router
    function executeCashSwap(address agent, CashSwapMessage memory ms, bytes memory sig) external onlyRelayer {
        require(ms.from.account() == ms.to.account(), Err.CashSwapDenied());
        _verifyAgentSigAndIncreaseNonce(ms.from.account(), agent, ms.nonce, _hashCashSwapMessage(ms), sig);

        IPDepositBox box = DEPOSIT_BOX_FACTORY.deployDepositBox(ms.from.root(), CASH_SWAP_BOX_ID);

        _MARKET_HUB.cashInstantWithdraw(ms.from, ms.amountSpent, address(box));
        uint256 amountReceived = _cashSwap(box, ms);
        _MARKET_HUB.vaultDeposit(ms.to, amountReceived);

        emit CashSwapExecuted(ms.from, ms.to, ms.amountSpent, amountReceived);
    }

    function _swapForDeposit(
        DepositFromBoxMessage memory message
    ) internal returns (uint256 actualSpent, uint256 netTokenReceived) {
        IPDepositBox box = DEPOSIT_BOX_FACTORY.deployDepositBox(message.root, message.boxId);
        address tokenReceived = _MARKET_HUB.tokenIdToAddress(message.tokenId);

        actualSpent = PMath.min(message.maxAmountSpent, _balanceOf(address(box), message.tokenSpent));

        if (tokenReceived == message.tokenSpent) {
            box.withdrawTo(address(this), message.tokenSpent, actualSpent);
            netTokenReceived = actualSpent;
        } else {
            ApprovedCall memory call = ApprovedCall({
                token: message.tokenSpent,
                amount: actualSpent,
                approveTo: message.swapApprove,
                callTo: message.swapExtRouter,
                data: message.swapCalldata
            });

            uint256 preBalance = _selfBalance(tokenReceived);
            box.approveAndCall(call, address(box));
            netTokenReceived = _selfBalance(tokenReceived) - preBalance;
        }
    }

    function _cashSwap(IPDepositBox box, CashSwapMessage memory ms) internal returns (uint256 amountReceived) {
        address tokenSpent = _MARKET_HUB.tokenIdToAddress(ms.from.tokenId());
        address tokenReceived = _MARKET_HUB.tokenIdToAddress(ms.to.tokenId());

        ApprovedCall memory call = ApprovedCall({
            token: tokenSpent,
            amount: ms.amountSpent,
            approveTo: ms.swapApprove,
            callTo: ms.swapExtRouter,
            data: ms.swapCalldata
        });

        uint256 preBalance = _selfBalance(tokenReceived);
        box.approveAndCall(call, address(box));
        amountReceived = _selfBalance(tokenReceived) - preBalance;

        require(amountReceived >= ms.minAmountReceived, Err.InsufficientReceivedAmount());
    }

    function _wrapEthInBox(IPDepositBox box, uint256 amount) internal {
        ApprovedCall memory call = ApprovedCall({
            token: NATIVE,
            amount: amount,
            approveTo: address(0),
            callTo: _WETH,
            data: abi.encodeCall(IWETH.deposit, ())
        });

        box.approveAndCall(call, address(box));
    }
}
