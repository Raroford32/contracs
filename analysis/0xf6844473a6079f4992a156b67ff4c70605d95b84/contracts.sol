// SPDX-License-Identifier: UNLICENSED
pragma solidity 0.8.30;

import {OwnableRoles} from "solady/auth/OwnableRoles.sol";
import {SafeTransferLib} from "solady/utils/SafeTransferLib.sol";

interface IERC20 {
    function totalSupply() external view returns (uint256);
    function balanceOf(address account) external view returns (uint256);
    function transfer(address to, uint256 amount) external returns (bool);
    function allowance(address owner, address spender) external view returns (uint256);
    function approve(address spender, uint256 amount) external returns (bool);
    function transferFrom(address from, address to, uint256 amount) external returns (bool);
    function name() external view returns (string memory);
    function symbol() external view returns (string memory);
    function decimals() external view returns (uint8);
}

interface IPutManager {
    function invest(address token, uint256 amount, address recipient, uint256 proofAmount, bytes32[] calldata proofWl)
        external
        returns (uint256);
}

interface ITokenSaleFund {
    event Committed(address indexed user, bytes32 indexed option, address indexed token, uint256 amount);
    event Remitted(address indexed user, bytes32 indexed option, address indexed token, uint256 amount);
    event BatchFail(uint256 kind, address indexed user, bytes32 indexed option, address indexed token, uint256 amount);
    event Batched(uint256 kind, uint256 succeeded, uint256 failed);
    event Transferred(address indexed to, address indexed token, uint256 amount);
    event Approved(address indexed spender, address indexed token, uint256 amount);
    event Toggled(bool previous, bool next);

    function fundingTokenBalance(address token) external view returns (uint256);
    function commitBalance(address user, bytes32 option, address token) external view returns (uint256);
    function commit(address user, bytes32 option, address token, uint256 amount) external returns (bool);
    function commit(address[] calldata users, bytes32[] calldata options, address[] calldata tokens, uint256[] calldata amounts) external returns (bool);
    function remit(address user, bytes32 option, address token, uint256 amount) external returns (bool);
    function remit(address[] calldata users, bytes32 option, address token, uint256[] calldata amounts) external returns (bool);
    function approve(address spender, address token, uint256 amount) external returns (bool);
    function transfer(address to, address token, uint256 amount) external returns (bool);
    function toggle() external returns (bool);

    error InsufficientAmount(uint256 amount, uint256 minimum);
    error InsufficientCommitment(address user, bytes32 option, address token);
    error NonEquivalentListLength();
    error CommitFailed(address user, bytes32 option, address token);
    error Stopped();
}

interface IFlyingTulipFund {
    event Invested(address indexed user, address indexed token, uint256 amount);
    function isProofWlSet() external view returns (bool);
    function investFor(address user, bytes32 option, address token, uint256 amount) external returns (bool);
    function investFor(address[] calldata users, bytes32[] calldata options, address[] calldata tokens, uint256[] calldata amounts) external returns (bool);
    function setProofWl(bytes32[] calldata pwl) external returns (bool);
    error PutManagerIsZero();
    error ProofWlNotSet();
}

contract TokenSaleFund is ITokenSaleFund, OwnableRoles {
    uint256 public constant VERSION = 1;
    uint256 public constant COMMIT_LEVEL = 2;
    uint256 public constant REMIT_LEVEL = 4;
    uint256 public constant MIN_REMIT = 1;
    uint256 public minCommit;
    bytes32 public id;
    bool public stopped;
    mapping(address => mapping(bytes32 => mapping(address => Total))) public totals;

    struct Total {
        uint256 commitCount;
        uint256 commitSum;
        uint256 remitCount;
        uint256 remitSum;
    }

    enum BatchType { Commit, Remit }

    constructor(uint256 min, bytes32 saleId) {
        require(min > 0, InsufficientAmount(min, 0));
        _initializeOwner(msg.sender);
        minCommit = min;
        id = saleId;
    }

    function fundingTokenBalance(address token) external view returns (uint256) {
        return IERC20(token).balanceOf(address(this));
    }

    function commitBalance(address user, bytes32 option, address token) external view returns (uint256) {
        Total memory data = totals[user][option][token];
        return data.commitSum - data.remitSum;
    }

    function commit(address user, bytes32 option, address token, uint256 amount) external started onlyRoles(COMMIT_LEVEL) returns (bool) {
        require(amount >= minCommit, InsufficientAmount(amount, minCommit));
        if (!SafeTransferLib.trySafeTransferFrom(token, user, address(this), amount)) {
            revert CommitFailed(user, option, token);
        }
        _commit(user, option, token, amount);
        return true;
    }

    function commit(address[] calldata users, bytes32[] calldata options, address[] calldata tokens, uint256[] calldata amounts) external started onlyRoles(COMMIT_LEVEL) returns (bool) {
        uint256 batched = 0;
        uint256 len = users.length;
        require(len == options.length && len == tokens.length && len == amounts.length, NonEquivalentListLength());
        for (uint256 i = 0; i < len; ++i) {
            address user = users[i];
            bytes32 option = options[i];
            address token = tokens[i];
            uint256 amount = amounts[i];
            if (amount >= minCommit && SafeTransferLib.trySafeTransferFrom(token, user, address(this), amount)) {
                _commit(user, option, token, amount);
                unchecked { batched += 1; }
            } else {
                emit BatchFail(uint256(BatchType.Commit), user, option, token, amount);
            }
        }
        emit Batched(uint256(BatchType.Commit), batched, len - batched);
        return true;
    }

    function _commit(address user, bytes32 option, address token, uint256 amount) internal {
        Total storage data = totals[user][option][token];
        data.commitCount += 1;
        data.commitSum += amount;
        emit Committed(user, option, token, amount);
    }

    function remit(address user, bytes32 option, address token, uint256 amount) external started onlyRoles(REMIT_LEVEL) returns (bool) {
        _remit(user, option, token, amount);
        return true;
    }

    function remit(address[] calldata users, bytes32 option, address token, uint256[] calldata amounts) external started onlyRoles(REMIT_LEVEL) returns (bool) {
        uint256 len = users.length;
        require(len == amounts.length, NonEquivalentListLength());
        for (uint256 i = 0; i < len; ++i) {
            _remit(users[i], option, token, amounts[i]);
        }
        emit Batched(uint256(BatchType.Remit), len, 0);
        return true;
    }

    function _remit(address user, bytes32 option, address token, uint256 amount) internal {
        require(amount >= MIN_REMIT, InsufficientAmount(amount, MIN_REMIT));
        Total storage data = totals[user][option][token];
        require(data.commitSum - data.remitSum >= amount, InsufficientCommitment(user, option, token));
        data.remitCount += 1;
        data.remitSum += amount;
        SafeTransferLib.safeTransfer(token, user, amount);
        emit Remitted(user, option, token, amount);
    }

    function approve(address spender, address token, uint256 amount) external onlyOwner returns (bool) {
        SafeTransferLib.safeApproveWithRetry(token, spender, amount);
        emit Approved(spender, token, amount);
        return true;
    }

    function transfer(address to, address token, uint256 amount) external onlyOwner returns (bool) {
        SafeTransferLib.safeTransfer(token, to, amount);
        emit Transferred(to, token, amount);
        return true;
    }

    function toggle() external onlyOwner returns (bool) {
        stopped = !stopped;
        emit Toggled(!stopped, stopped);
        return true;
    }

    modifier started() {
        _started();
        _;
    }

    function _started() internal view {
        require(!stopped, Stopped());
    }
}

contract FlyingTulipFund is IFlyingTulipFund, TokenSaleFund {
    uint256 private constant PROOF_AMOUNT = 0;
    uint256 public ftBatchType;
    bytes32[] private _proofWl;
    address public putManagerAddress;
    bool public commitBalanceOverride;

    constructor(uint256 min, bytes32 saleId, address pma) TokenSaleFund(min, saleId) {
        require(pma != address(0), PutManagerIsZero());
        ftBatchType = uint256(saleId);
        putManagerAddress = pma;
    }

    function isProofWlSet() external view returns (bool) {
        return _proofWl.length > 0;
    }

    function investFor(address user, bytes32 option, address token, uint256 amount) external started onlyRoles(REMIT_LEVEL) returns (bool) {
        require(_proofWl.length > 0, ProofWlNotSet());
        require(amount >= minCommit, InsufficientAmount(amount, minCommit));
        if (!commitBalanceOverride) {
            Total memory data = totals[user][option][token];
            require(data.commitSum - data.remitSum >= amount, InsufficientCommitment(user, option, token));
        }
        IPutManager(putManagerAddress).invest(token, amount, user, PROOF_AMOUNT, _proofWl);
        emit Invested(user, token, amount);
        return true;
    }

    function investFor(address[] calldata users, bytes32[] calldata options, address[] calldata tokens, uint256[] calldata amounts) external started onlyRoles(REMIT_LEVEL) returns (bool) {
        require(_proofWl.length > 0, ProofWlNotSet());
        uint256 batched = 0;
        uint256 len = users.length;
        require(len == options.length && len == tokens.length && len == amounts.length, NonEquivalentListLength());
        for (uint256 i = 0; i < len; ++i) {
            address user = users[i];
            bytes32 option = options[i];
            address token = tokens[i];
            uint256 amount = amounts[i];
            Total memory data = totals[user][option][token];
            if (amount >= minCommit && (commitBalanceOverride || (data.commitSum - data.remitSum >= amount))) {
                try IPutManager(putManagerAddress).invest(token, amount, user, PROOF_AMOUNT, _proofWl) {
                    unchecked { batched += 1; }
                    emit Invested(user, token, amount);
                } catch {
                    emit BatchFail(ftBatchType, user, option, token, amount);
                }
            } else {
                emit BatchFail(ftBatchType, user, option, token, amount);
            }
        }
        emit Batched(ftBatchType, batched, len - batched);
        return true;
    }

    function setProofWl(bytes32[] calldata pwl) external onlyOwner returns (bool) {
        _proofWl = pwl;
        return true;
    }

    function toggleCommitBalanceOverride() external onlyOwner returns (bool) {
        commitBalanceOverride = !commitBalanceOverride;
        emit Toggled(!commitBalanceOverride, commitBalanceOverride);
        return true;
    }
}
