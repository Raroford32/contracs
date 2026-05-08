// SPDX-License-Identifier: BUSL-1.1
pragma solidity ^0.8.28;

import {AuthStorage} from "./AuthStorage.sol";
import {SignatureChecker} from "./SignatureChecker.sol";
import {SigningBase} from "./SigningBase.sol";
import {Err} from "./../../../lib/Errors.sol";
import {Account} from "./../../../types/Account.sol";

abstract contract AuthBase is AuthStorage, SigningBase {
    modifier onlyRelayer() {
        require(_isAllowedRelayer(msg.sender), Err.Unauthorized());
        _;
    }

    function _isValidSignatureNow(address signer, bytes32 hash, bytes memory signature) internal view returns (bool) {
        return SignatureChecker.isValidSignatureNow(signer, hash, signature);
    }

    function _verifyIntentSigAndMarkExecuted(
        address signer,
        uint64 expiry,
        bytes32 intentHash,
        bytes memory signature
    ) internal {
        require(_isValidSignatureNow(signer, intentHash, signature), Err.AuthInvalidMessage());
        require(expiry > block.timestamp, Err.AuthIntentExpired());
        _markIntentExecuted(intentHash);
    }

    function _verifyAgentSigAndIncreaseNonce(
        address agent,
        PendleSignTx memory message,
        bytes memory signature,
        bytes32 onchainConnectedId
    ) internal {
        require(onchainConnectedId == message.connectionId, Err.AuthInvalidConnectionId());
        _verifyAgentSigAndIncreaseNonce(message.account, agent, message.nonce, _hashPendleSignTx(message), signature);
    }

    function _verifyAgentSigAndIncreaseNonce(
        Account account,
        address agent,
        uint64 nonce,
        bytes32 messageHash,
        bytes memory signature
    ) internal {
        require(_AMS().agentExpiry[account][agent] > block.timestamp, Err.AuthAgentExpired());
        _verifySignerSigAndIncreaseNonce(agent, nonce, messageHash, signature);
    }

    function _verifySignerSigAndIncreaseNonce(
        address signer,
        uint64 nonce,
        bytes32 messageHash,
        bytes memory signature
    ) internal {
        require(_isValidSignatureNow(signer, messageHash, signature), Err.AuthInvalidMessage());
        require(_AMS().signerNonce[signer] < nonce, Err.AuthInvalidNonce());
        _AMS().signerNonce[signer] = nonce;
    }

    /// @dev Loose agent check (expiry > 0, not block.timestamp). Only for messages that are verified by an off-chain validator at signing time.
    function _verifyAgentSoft(
        Account account,
        address agent,
        bytes32 messageHash,
        bytes memory signature
    ) internal view {
        require(_AMS().agentExpiry[account][agent] > 0, Err.AuthInvalidAgent());
        require(_isValidSignatureNow(agent, messageHash, signature), Err.AuthInvalidMessage());
    }

    function _markIntentExecuted(bytes32 intentHash) internal {
        require(!_AMS().isIntentExecuted[intentHash], Err.AuthIntentExecuted());
        _AMS().isIntentExecuted[intentHash] = true;
    }
}
