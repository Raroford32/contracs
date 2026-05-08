// SPDX-License-Identifier: BUSL-1.1
pragma solidity ^0.8.28;

import {TokenId} from "../types/MarketTypes.sol";
import {IPDepositBoxFactory} from "./IPDepositBoxFactory.sol";
import {IRouterEventsAndTypes} from "./IRouterEventsAndTypes.sol";

interface IDepositModule is IRouterEventsAndTypes {
    function depositFromBox(DepositFromBoxMessage memory message, bytes memory signature) external;

    function directDepositFromBox(address root, address tokenSpent, TokenId tokenId) external;

    function withdrawFromBox(WithdrawFromBoxMessage memory message, bytes memory signature) external;

    function executeCashSwap(address agent, CashSwapMessage memory message, bytes memory signature) external;

    function DEPOSIT_BOX_FACTORY() external view returns (IPDepositBoxFactory);

    function DIRECT_DEPOSIT_BOX_ID() external pure returns (uint32);

    function CASH_SWAP_BOX_ID() external pure returns (uint32);
}
