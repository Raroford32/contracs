pragma solidity ^0.8.20;

/**
 * @dev External interface of AccessControl declared to support ERC165 detection.
 */
interface IAccessControl {
    /**
     * @dev The `account` is missing a role.
     */
    error AccessControlUnauthorizedAccount(address account, bytes32 neededRole);

    /**
     * @dev The caller of a function is not the expected one.
     *
     * NOTE: Don't confuse with {AccessControlUnauthorizedAccount}.
     */
    error AccessControlBadConfirmation();

    /**
     * @dev Emitted when `newAdminRole` is set as ``role``'s admin role, replacing `previousAdminRole`
     *
     * `DEFAULT_ADMIN_ROLE` is the starting admin for all roles, despite
     * {RoleAdminChanged} not being emitted signaling this.
     */
    event RoleAdminChanged(
        bytes32 indexed role,
        bytes32 indexed previousAdminRole,
        bytes32 indexed newAdminRole
    );

    /**
     * @dev Emitted when `account` is granted `role`.
     *
     * `sender` is the account that originated the contract call, an admin role
     * bearer except when using {AccessControl-_setupRole}.
     */
    event RoleGranted(
        bytes32 indexed role,
        address indexed account,
        address indexed sender
    );

    /**
     * @dev Emitted when `account` is revoked `role`.
     *
     * `sender` is the account that originated the contract call:
     *   - if using `revokeRole`, it is the admin role bearer
     *   - if using `renounceRole`, it is the role bearer (i.e. `account`)
     */
    event RoleRevoked(
        bytes32 indexed role,
        address indexed account,
        address indexed sender
    );

    /**
     * @dev Returns `true` if `account` has been granted `role`.
     */
    function hasRole(
        bytes32 role,
        address account
    ) external view returns (bool);

    /**
     * @dev Returns the admin role that controls `role`. See {grantRole} and
     * {revokeRole}.
     *
     * To change a role's admin, use {AccessControl-_setRoleAdmin}.
     */
    function getRoleAdmin(bytes32 role) external view returns (bytes32);

    /**
     * @dev Grants `role` to `account`.
     *
     * If `account` had not been already granted `role`, emits a {RoleGranted}
     * event.
     *
     * Requirements:
     *
     * - the caller must have ``role``'s admin role.
     */
    function grantRole(bytes32 role, address account) external;

    /**
     * @dev Revokes `role` from `account`.
     *
     * If `account` had been granted `role`, emits a {RoleRevoked} event.
     *
     * Requirements:
     *
     * - the caller must have ``role``'s admin role.
     */
    function revokeRole(bytes32 role, address account) external;

    /**
     * @dev Revokes `role` from the calling account.
     *
     * Roles are often managed via {grantRole} and {revokeRole}: this function's
     * purpose is to provide a mechanism for accounts to lose their privileges
     * if they are compromised (such as when a trusted device is misplaced).
     *
     * If the calling account had been granted `role`, emits a {RoleRevoked}
     * event.
     *
     * Requirements:
     *
     * - the caller must be `callerConfirmation`.
     */
    function renounceRole(bytes32 role, address callerConfirmation) external;
}

pragma solidity ^0.8.20;

/**
 * @dev Provides information about the current execution context, including the
 * sender of the transaction and its data. While these are generally available
 * via msg.sender and msg.data, they should not be accessed in such a direct
 * manner, since when dealing with meta-transactions the account sending and
 * paying for execution may not be the actual sender (as far as an application
 * is concerned).
 *
 * This contract is only required for intermediate, library-like contracts.
 */
abstract contract Context {
    function _msgSender() internal view virtual returns (address) {
        return msg.sender;
    }

    function _msgData() internal view virtual returns (bytes calldata) {
        return msg.data;
    }

    function _contextSuffixLength() internal view virtual returns (uint256) {
        return 0;
    }
}

pragma solidity ^0.8.20;

/**
 * @dev Interface of the ERC165 standard, as defined in the
 * https:
 *
 * Implementers can declare support of contract interfaces, which can then be
 * queried by others ({ERC165Checker}).
 *
 * For an implementation, see {ERC165}.
 */
interface IERC165 {
    /**
     * @dev Returns true if this contract implements the interface defined by
     * `interfaceId`. See the corresponding
     * https:
     * to learn more about how these ids are created.
     *
     * This function call must use less than 30 000 gas.
     */
    function supportsInterface(bytes4 interfaceId) external view returns (bool);
}

pragma solidity ^0.8.20;

/**
 * @dev Implementation of the {IERC165} interface.
 *
 * Contracts that want to implement ERC165 should inherit from this contract and override {supportsInterface} to check
 * for the additional interface id that will be supported. For example:
 *
 * ```solidity
 * function supportsInterface(bytes4 interfaceId) public view virtual override returns (bool) {
 *     return interfaceId == type(MyInterface).interfaceId || super.supportsInterface(interfaceId);
 * }
 * ```
 */
abstract contract ERC165 is IERC165 {
    /**
     * @dev See {IERC165-supportsInterface}.
     */
    function supportsInterface(
        bytes4 interfaceId
    ) public view virtual returns (bool) {
        return interfaceId == type(IERC165).interfaceId;
    }
}

pragma solidity ^0.8.20;

/**
 * @dev Contract module that allows children to implement role-based access
 * control mechanisms. This is a lightweight version that doesn't allow enumerating role
 * members except through off-chain means by accessing the contract event logs. Some
 * applications may benefit from on-chain enumerability, for those cases see
 * {AccessControlEnumerable}.
 *
 * Roles are referred to by their `bytes32` identifier. These should be exposed
 * in the external API and be unique. The best way to achieve this is by
 * using `public constant` hash digests:
 *
 * ```solidity
 * bytes32 public constant MY_ROLE = keccak256("MY_ROLE");
 * ```
 *
 * Roles can be used to represent a set of permissions. To restrict access to a
 * function call, use {hasRole}:
 *
 * ```solidity
 * function foo() public {
 *     require(hasRole(MY_ROLE, msg.sender));
 *     ...
 * }
 * ```
 *
 * Roles can be granted and revoked dynamically via the {grantRole} and
 * {revokeRole} functions. Each role has an associated admin role, and only
 * accounts that have a role's admin role can call {grantRole} and {revokeRole}.
 *
 * By default, the admin role for all roles is `DEFAULT_ADMIN_ROLE`, which means
 * that only accounts with this role will be able to grant or revoke other
 * roles. More complex role relationships can be created by using
 * {_setRoleAdmin}.
 *
 * WARNING: The `DEFAULT_ADMIN_ROLE` is also its own admin: it has permission to
 * grant and revoke this role. Extra precautions should be taken to secure
 * accounts that have been granted it. We recommend using {AccessControlDefaultAdminRules}
 * to enforce additional security measures for this role.
 */
abstract contract AccessControl is Context, IAccessControl, ERC165 {
    struct RoleData {
        mapping(address account => bool) hasRole;
        bytes32 adminRole;
    }

    mapping(bytes32 role => RoleData) private _roles;

    bytes32 public constant DEFAULT_ADMIN_ROLE = 0x00;

    /**
     * @dev Modifier that checks that an account has a specific role. Reverts
     * with an {AccessControlUnauthorizedAccount} error including the required role.
     */
    modifier onlyRole(bytes32 role) {
        _checkRole(role);
        _;
    }

    /**
     * @dev See {IERC165-supportsInterface}.
     */
    function supportsInterface(
        bytes4 interfaceId
    ) public view virtual override returns (bool) {
        return
            interfaceId == type(IAccessControl).interfaceId ||
            super.supportsInterface(interfaceId);
    }

    /**
     * @dev Returns `true` if `account` has been granted `role`.
     */
    function hasRole(
        bytes32 role,
        address account
    ) public view virtual returns (bool) {
        return _roles[role].hasRole[account];
    }

    /**
     * @dev Reverts with an {AccessControlUnauthorizedAccount} error if `_msgSender()`
     * is missing `role`. Overriding this function changes the behavior of the {onlyRole} modifier.
     */
    function _checkRole(bytes32 role) internal view virtual {
        _checkRole(role, _msgSender());
    }

    /**
     * @dev Reverts with an {AccessControlUnauthorizedAccount} error if `account`
     * is missing `role`.
     */
    function _checkRole(bytes32 role, address account) internal view virtual {
        if (!hasRole(role, account)) {
            revert AccessControlUnauthorizedAccount(account, role);
        }
    }

    /**
     * @dev Returns the admin role that controls `role`. See {grantRole} and
     * {revokeRole}.
     *
     * To change a role's admin, use {_setRoleAdmin}.
     */
    function getRoleAdmin(bytes32 role) public view virtual returns (bytes32) {
        return _roles[role].adminRole;
    }

    /**
     * @dev Grants `role` to `account`.
     *
     * If `account` had not been already granted `role`, emits a {RoleGranted}
     * event.
     *
     * Requirements:
     *
     * - the caller must have ``role``'s admin role.
     *
     * May emit a {RoleGranted} event.
     */
    function grantRole(
        bytes32 role,
        address account
    ) public virtual onlyRole(getRoleAdmin(role)) {
        _grantRole(role, account);
    }

    /**
     * @dev Revokes `role` from `account`.
     *
     * If `account` had been granted `role`, emits a {RoleRevoked} event.
     *
     * Requirements:
     *
     * - the caller must have ``role``'s admin role.
     *
     * May emit a {RoleRevoked} event.
     */
    function revokeRole(
        bytes32 role,
        address account
    ) public virtual onlyRole(getRoleAdmin(role)) {
        _revokeRole(role, account);
    }

    /**
     * @dev Revokes `role` from the calling account.
     *
     * Roles are often managed via {grantRole} and {revokeRole}: this function's
     * purpose is to provide a mechanism for accounts to lose their privileges
     * if they are compromised (such as when a trusted device is misplaced).
     *
     * If the calling account had been revoked `role`, emits a {RoleRevoked}
     * event.
     *
     * Requirements:
     *
     * - the caller must be `callerConfirmation`.
     *
     * May emit a {RoleRevoked} event.
     */
    function renounceRole(
        bytes32 role,
        address callerConfirmation
    ) public virtual {
        if (callerConfirmation != _msgSender()) {
            revert AccessControlBadConfirmation();
        }

        _revokeRole(role, callerConfirmation);
    }

    /**
     * @dev Sets `adminRole` as ``role``'s admin role.
     *
     * Emits a {RoleAdminChanged} event.
     */
    function _setRoleAdmin(bytes32 role, bytes32 adminRole) internal virtual {
        bytes32 previousAdminRole = getRoleAdmin(role);
        _roles[role].adminRole = adminRole;
        emit RoleAdminChanged(role, previousAdminRole, adminRole);
    }

    /**
     * @dev Attempts to grant `role` to `account` and returns a boolean indicating if `role` was granted.
     *
     * Internal function without access restriction.
     *
     * May emit a {RoleGranted} event.
     */
    function _grantRole(
        bytes32 role,
        address account
    ) internal virtual returns (bool) {
        if (!hasRole(role, account)) {
            _roles[role].hasRole[account] = true;
            emit RoleGranted(role, account, _msgSender());
            return true;
        } else {
            return false;
        }
    }

    /**
     * @dev Attempts to revoke `role` to `account` and returns a boolean indicating if `role` was revoked.
     *
     * Internal function without access restriction.
     *
     * May emit a {RoleRevoked} event.
     */
    function _revokeRole(
        bytes32 role,
        address account
    ) internal virtual returns (bool) {
        if (hasRole(role, account)) {
            _roles[role].hasRole[account] = false;
            emit RoleRevoked(role, account, _msgSender());
            return true;
        } else {
            return false;
        }
    }
}

pragma solidity ^0.8.20;

/**
 * @dev Interface of the ERC20 standard as defined in the EIP.
 */
interface IERC20 {
    /**
     * @dev Emitted when `value` tokens are moved from one account (`from`) to
     * another (`to`).
     *
     * Note that `value` may be zero.
     */
    event Transfer(address indexed from, address indexed to, uint256 value);

    /**
     * @dev Emitted when the allowance of a `spender` for an `owner` is set by
     * a call to {approve}. `value` is the new allowance.
     */
    event Approval(
        address indexed owner,
        address indexed spender,
        uint256 value
    );

    /**
     * @dev Returns the value of tokens in existence.
     */
    function totalSupply() external view returns (uint256);

    /**
     * @dev Returns the value of tokens owned by `account`.
     */
    function balanceOf(address account) external view returns (uint256);

    /**
     * @dev Moves a `value` amount of tokens from the caller's account to `to`.
     *
     * Returns a boolean value indicating whether the operation succeeded.
     *
     * Emits a {Transfer} event.
     */
    function transfer(address to, uint256 value) external returns (bool);

    /**
     * @dev Returns the remaining number of tokens that `spender` will be
     * allowed to spend on behalf of `owner` through {transferFrom}. This is
     * zero by default.
     *
     * This value changes when {approve} or {transferFrom} are called.
     */
    function allowance(
        address owner,
        address spender
    ) external view returns (uint256);

    /**
     * @dev Sets a `value` amount of tokens as the allowance of `spender` over the
     * caller's tokens.
     *
     * Returns a boolean value indicating whether the operation succeeded.
     *
     * IMPORTANT: Beware that changing an allowance with this method brings the risk
     * that someone may use both the old and the new allowance by unfortunate
     * transaction ordering. One possible solution to mitigate this race
     * condition is to first reduce the spender's allowance to 0 and set the
     * desired value afterwards:
     * https:
     *
     * Emits an {Approval} event.
     */
    function approve(address spender, uint256 value) external returns (bool);

    /**
     * @dev Moves a `value` amount of tokens from `from` to `to` using the
     * allowance mechanism. `value` is then deducted from the caller's
     * allowance.
     *
     * Returns a boolean value indicating whether the operation succeeded.
     *
     * Emits a {Transfer} event.
     */
    function transferFrom(
        address from,
        address to,
        uint256 value
    ) external returns (bool);
}

interface ILockEpochRealTime {
    event LockEpochCreated(
        uint32 indexed epochId,
        uint128 amount,
        uint64 unlockStartPoint,
        uint64 unlockEndPoint,
        string roleName
    );
    event LockEpochUpdated(
        uint32 indexed epochId,
        uint128 amount,
        uint64 unlockStartPoint,
        uint64 unlockEndPoint,
        string roleName
    );
    event LockEpochReleased(
        uint32 indexed epochId,
        uint128 amount,
        uint64 unlockStartPoint,
        uint64 unlockEndPoint,
        string roleName
    );
    event LockEpochClaimed(
        uint32 indexed epochId,
        uint128 amount,
        uint64 unlockStartPoint,
        uint64 unlockEndPoint,
        string roleName
    );

    event RoleBindReceiverUpdated(
        string indexed roleName,
        address oldReceiver,
        address newReceiver
    );

    event RoleTransferred(
        string indexed roleName,
        address oldReceiver,
        address newReceiver
    );

    /**
     * uint96 timestamp 2**96 = 79228162514264337593543950336 as 79,228,162,514.26434 ether,
     * uint32 epochId
     * uint32 cycles
     * uint128 amount
     * if your token total supply beyond this, don't use it
     */

    function getRoleNameHash(
        string calldata roleName
    ) external pure returns (bytes32 roleHash);

    function getUnlockAmountOf(
        uint32 epochId
    ) external view returns (uint128 unlockAmount);

    function getUnclaimAmountOf(
        uint32 epochId
    ) external view returns (uint128 unclaimAmount);

    function createLockEpochs(
        uint128[] calldata totalLockAmounts,
        uint32[] calldata unlockStartPoints,
        uint32[] calldata unlockEndPoints,
        string[] calldata roleName
    ) external;

    function updateLockEpochs(
        uint32[] calldata epochIds,
        uint128[] calldata newTotalLockAmounts,
        uint64[] calldata newUnlockStartPoints,
        uint64[] calldata newUnlockEndPoints,
        string[] calldata newRoleNames
    ) external;

    function startReleaseLockEpochs(uint32[] calldata epochIds) external;

    function updateRoleBindReceivers(
        address[] calldata roleBindReceivers,
        string[] calldata roleNames
    ) external;

    function confirmRoleBindReceivers(
        address[] calldata roleBindReceivers,
        string[] calldata roleNames
    ) external;

    function transferRole(address to, string calldata roleName) external;

    function claimUnlockedFunds(uint32 epochId) external;

    function getSystemInfo() external view returns (SystemInfo memory sysInfo);

    function getLockEpochInfos(
        uint32 startEpochId,
        uint32 endEpochId
    ) external view returns (LockEpochInfo[] memory leis);

    function getLockEpochInfo(
        uint32 epochId
    ) external view returns (LockEpochInfo memory lei);

    function getRoleInfos(
        string[] calldata roleNames
    ) external view returns (RoleInfo[] memory roleInfos);

    function getRoleInfoByHash(
        bytes32 roleHash
    ) external view returns (RoleInfo memory roleInfo);
}
struct SystemInfo {
    uint128 totalLockedAmount;
    uint128 totalClaimedAmount;
    uint32 totalLockEpoch;
}

struct System {
    uint128 totalLockedAmount;
    uint32 totalLockEpoch;
    uint128 totalClaimedAmount;
    uint32 notUse;
}

struct RoleInfo {
    uint32[] roleBindEpochIds;
    address roleBindReceiver;
    bool confirmBindReceiver;
}

enum LockEpochState {
    notExist,
    notStart,
    releasing,
    finished
}

struct LockEpochInfo {
    LockEpochState les;
    string belongToRoleName;
    uint128 totalLockAmount;
    uint64 unlockStartPoint;
    uint64 unlockEndPoint;
    uint128 claimedAmount;
    uint128 currentUnclaimAmount;
    uint128 currentUnlockAmount;
    uint128 unReleaseAmount;
}

struct LockEpoch {
    uint128 totalLockAmount;
    uint128 claimedAmount;
    uint64 unlockStartPoint;
    uint64 unlockEndPoint;
    uint128 notUse;
    string belongToRoleName;
    LockEpochState les;
}

pragma solidity ^0.8.19;

library Math {
    function min(uint256 x, uint256 y) internal pure returns (uint256 z) {
        z = x < y ? x : y;
    }

    function sqrt(uint256 y) internal pure returns (uint256 z) {
        if (y > 3) {
            z = y;
            uint256 x = y / 2 + 1;
            while (x < z) {
                z = x;
                x = (y / x + x) / 2;
            }
        } else if (y != 0) {
            z = 1;
        }
    }

    /**
     * @notice Calculates floor(x * y / denominator) with full precision. Throws if result overflows a uint256 or
     * denominator == 0
     * @dev Original credit to Remco Bloemen under MIT license (https:
     * with further edits by Uniswap Labs also under MIT license.
     */
    function mulDiv(
        uint256 x,
        uint256 y,
        uint256 denominator
    ) internal pure returns (uint256 result) {
        unchecked {
            uint256 prod0;
            uint256 prod1;
            assembly {
                let mm := mulmod(x, y, not(0))
                prod0 := mul(x, y)
                prod1 := sub(sub(mm, prod0), lt(mm, prod0))
            }

            if (prod1 == 0) {
                return prod0 / denominator;
            }

            require(denominator > prod1);

            uint256 remainder;
            assembly {
                remainder := mulmod(x, y, denominator)

                prod1 := sub(prod1, gt(remainder, prod0))
                prod0 := sub(prod0, remainder)
            }

            uint256 twos = denominator & (~denominator + 1);
            assembly {
                denominator := div(denominator, twos)

                prod0 := div(prod0, twos)

                twos := add(div(sub(0, twos), twos), 1)
            }

            prod0 |= prod1 * twos;

            uint256 inverse = (3 * denominator) ^ 2;

            inverse *= 2 - denominator * inverse;
            inverse *= 2 - denominator * inverse;
            inverse *= 2 - denominator * inverse;
            inverse *= 2 - denominator * inverse;
            inverse *= 2 - denominator * inverse;
            inverse *= 2 - denominator * inverse;

            result = prod0 * inverse;
            return result;
        }
    }
}
// CyberForker @ AOF 2025/01/20
contract LockerRealTime is ILockEpochRealTime, AccessControl {
    IERC20 public immutable lockedToken;
    System sys;
    mapping(uint32 => LockEpoch) epochs;
    mapping(bytes32 => RoleInfo) roleNameHashToRoleInfo;
    bytes32 public constant EPOCH_MANAGER_ROLE = bytes32("EPOCH_MANAGER_ROLE");

    constructor(address lockTokenAddress) {
        _grantRole(DEFAULT_ADMIN_ROLE, msg.sender);
        lockedToken = IERC20(lockTokenAddress);
    }

    bool private isLocked;
    modifier noReentrancy() {
        require(!isLocked, "Reentrancy is not allowed");
        isLocked = true;
        _;
        isLocked = false;
    }

    /**
     * Preseed Round
     * Seed Round
     * Team
     * Ecosystem
     * Marketing
     * Public Sale
     * Public Sale-KOL
     * Advisors
     * Inital Liquidity
     */

    function getRoleNameHash(
        string calldata roleName
    ) public pure returns (bytes32 roleHash) {
        roleHash = keccak256(abi.encode(roleName));
    }

    function _getRoleNameHash(
        string storage roleName
    ) internal pure returns (bytes32 roleHash) {
        roleHash = keccak256(abi.encode(roleName));
    }

    function getUnlockAmountOf(
        uint32 epochId
    ) public view returns (uint128 unlockAmount) {
        LockEpoch storage _le = epochs[epochId];

        require(
            epochId > 0 && epochId <= sys.totalLockEpoch,
            "LE: Invalid epoch ID"
        );

        if (_le.les < LockEpochState.releasing) return 0;

        if (block.timestamp > _le.unlockStartPoint) {
            uint256 _timePassed = block.timestamp - _le.unlockStartPoint;

            uint256 _totalLockTime = _le.unlockEndPoint - _le.unlockStartPoint;

            if (_timePassed > _totalLockTime) _timePassed = _totalLockTime;

            unlockAmount = uint128(
                Math.mulDiv(_le.totalLockAmount, _timePassed, _totalLockTime)
            );
        }
    }

    function getUnclaimAmountOf(
        uint32 epochId
    ) public view returns (uint128 unclaimAmount) {
        require(
            epochId > 0 && epochId <= sys.totalLockEpoch,
            "LE: Invalid epoch ID"
        );

        uint128 _unlockAmount = getUnlockAmountOf(epochId);
        LockEpoch storage _le = epochs[epochId];

        unclaimAmount = _unlockAmount - _le.claimedAmount;
    }

    function createLockEpochs(
        uint128[] calldata totalLockAmounts,
        uint32[] calldata unlockStartPoints,
        uint32[] calldata unlockEndPoints,
        string[] calldata roleName
    ) external onlyRole(EPOCH_MANAGER_ROLE) noReentrancy {
        require(
            totalLockAmounts.length == unlockStartPoints.length &&
                unlockStartPoints.length == unlockEndPoints.length &&
                unlockEndPoints.length == roleName.length,
            "LE: Unequal length"
        );

        for (uint256 i = 0; i < totalLockAmounts.length; i++) {
            createLockEpoch(
                totalLockAmounts[i],
                unlockStartPoints[i],
                unlockEndPoints[i],
                roleName[i]
            );
        }
    }

    function createLockEpoch(
        uint128 totalLockAmount,
        uint64 unlockStartPoint,
        uint64 unlockEndPoint,
        string calldata roleName
    ) internal {
        uint32 _epochId = ++sys.totalLockEpoch;

        LockEpoch storage _le = epochs[_epochId];

        require(
            lockedToken.transferFrom(
                msg.sender,
                address(this),
                totalLockAmount
            ),
            "LE: Token transfer failed"
        );
        require(unlockStartPoint < unlockEndPoint, "LRT: Time error.");

        _le.totalLockAmount = totalLockAmount;
        _le.unlockStartPoint = unlockStartPoint;
        _le.unlockEndPoint = unlockEndPoint;
        _le.belongToRoleName = roleName;
        _le.les = LockEpochState.notStart;

        bytes32 _belongToRoleHash = getRoleNameHash(roleName);
        roleNameHashToRoleInfo[_belongToRoleHash].roleBindEpochIds.push(
            _epochId
        );

        emit LockEpochCreated(
            _epochId,
            totalLockAmount,
            unlockStartPoint,
            unlockEndPoint,
            roleName
        );
    }

    function updateLockEpochs(
        uint32[] calldata epochIds,
        uint128[] calldata newTotalLockAmounts,
        uint64[] calldata newUnlockStartPoints,
        uint64[] calldata newUnlockEndPoints,
        string[] calldata newRoleNames
    ) external onlyRole(EPOCH_MANAGER_ROLE) noReentrancy {
        require(
            epochIds.length == newTotalLockAmounts.length &&
                newTotalLockAmounts.length == newUnlockStartPoints.length &&
                newUnlockStartPoints.length == newUnlockEndPoints.length &&
                newUnlockEndPoints.length == newRoleNames.length,
            "LE: Unequal length"
        );
        for (uint32 i = 0; i < epochIds.length; i++) {
            updateLockEpoch(
                epochIds[i],
                newTotalLockAmounts[i],
                newUnlockStartPoints[i],
                newUnlockEndPoints[i],
                newRoleNames[i]
            );
        }
    }

    function updateLockEpoch(
        uint32 epochId,
        uint128 newTotalLockAmount,
        uint64 newUnlockStartPoint,
        uint64 newUnlockEndPoint,
        string calldata newRoleName
    ) internal {
        LockEpoch storage _le = epochs[epochId];
        require(_le.les == LockEpochState.notStart, "LE: Already Started");

        if (newTotalLockAmount > _le.totalLockAmount) {
            uint128 amountToTransfer = newTotalLockAmount - _le.totalLockAmount;
            lockedToken.transferFrom(
                msg.sender,
                address(this),
                amountToTransfer
            );
            _le.totalLockAmount = newTotalLockAmount;
        } else if (newTotalLockAmount < _le.totalLockAmount) {
            uint128 amountToRefund = _le.totalLockAmount - newTotalLockAmount;
            lockedToken.transfer(msg.sender, amountToRefund);
            _le.totalLockAmount = newTotalLockAmount;
        }

        require(newUnlockStartPoint < newUnlockEndPoint, "LRT: Time error.");
        _le.unlockStartPoint = newUnlockStartPoint;
        _le.unlockEndPoint = newUnlockEndPoint;

        bytes32 _newBelongToRoleHash = getRoleNameHash(newRoleName);
        bytes32 _currentBelongToRoleHash = _getRoleNameHash(
            _le.belongToRoleName
        );

        if (_newBelongToRoleHash != _currentBelongToRoleHash) {
            RoleInfo storage oldRole = roleNameHashToRoleInfo[
                _currentBelongToRoleHash
            ];

            for (uint i = 0; i < oldRole.roleBindEpochIds.length; i++) {
                if (oldRole.roleBindEpochIds[i] == epochId) {
                    oldRole.roleBindEpochIds[i] = oldRole.roleBindEpochIds[
                        oldRole.roleBindEpochIds.length - 1
                    ];
                    oldRole.roleBindEpochIds.pop();
                    break;
                }
            }

            roleNameHashToRoleInfo[_newBelongToRoleHash].roleBindEpochIds.push(
                epochId
            );
            _le.belongToRoleName = newRoleName;
        }

        emit LockEpochUpdated(
            epochId,
            newTotalLockAmount,
            newUnlockStartPoint,
            newUnlockEndPoint,
            newRoleName
        );
    }

    function startReleaseLockEpochs(
        uint32[] calldata epochIds
    ) external onlyRole(EPOCH_MANAGER_ROLE) noReentrancy {
        for (uint32 i = 0; i < epochIds.length; i++) {
            startReleaseLockEpoch(epochIds[i]);
        }
    }

    function startReleaseLockEpoch(uint32 epochId) internal {
        require(
            epochId > 0 && epochId <= sys.totalLockEpoch,
            "LE: Invalid epoch ID"
        );
        LockEpoch storage _le = epochs[epochId];
        require(_le.les == LockEpochState.notStart, "LE: Already Started");
        _le.les = LockEpochState.releasing;
        sys.totalLockedAmount += _le.totalLockAmount;
    }

    function updateRoleBindReceivers(
        address[] calldata roleBindReceivers,
        string[] calldata roleNames
    ) external onlyRole(EPOCH_MANAGER_ROLE) noReentrancy {
        for (uint32 i = 0; i < roleNames.length; i++) {
            updateRoleBindReceiver(roleBindReceivers[i], roleNames[i]);
        }
    }

    function updateRoleBindReceiver(
        address roleBindReceiver,
        string calldata roleName
    ) internal {
        bytes32 _roleHash = getRoleNameHash(roleName);

        RoleInfo storage _ri = roleNameHashToRoleInfo[_roleHash];

        require(!_ri.confirmBindReceiver, "LE: Receiver address confirmed");

        _ri.roleBindReceiver = roleBindReceiver;

        emit RoleBindReceiverUpdated(
            roleName,
            _ri.roleBindReceiver,
            roleBindReceiver
        );
    }

    function confirmRoleBindReceivers(
        address[] calldata roleBindReceivers,
        string[] calldata roleNames
    ) external onlyRole(EPOCH_MANAGER_ROLE) noReentrancy {
        for (uint32 i = 0; i < roleNames.length; i++) {
            confirmRoleBindReceiver(roleBindReceivers[i], roleNames[i]);
        }
    }

    function confirmRoleBindReceiver(
        address roleBindReceiver,
        string calldata roleName
    ) internal {
        bytes32 _roleHash = getRoleNameHash(roleName);
        RoleInfo storage _ri = roleNameHashToRoleInfo[_roleHash];

        require(
            roleBindReceiver == _ri.roleBindReceiver &&
                roleBindReceiver != address(0),
            "LE: Double check error"
        );
        _ri.confirmBindReceiver = true;
    }

    function transferRole(
        address to,
        string calldata roleName
    ) external noReentrancy {
        bytes32 _roleHash = getRoleNameHash(roleName);
        RoleInfo storage _ri = roleNameHashToRoleInfo[_roleHash];
        require(_ri.roleBindReceiver == msg.sender, "LE: No Auth");
        require(to != address(0), "LE: Invalid receiver address");
        _ri.roleBindReceiver = to;
        emit RoleTransferred(roleName, msg.sender, to);
    }

    function claimUnlockedFunds(uint32 epochId) external noReentrancy {
        require(
            epochId > 0 && epochId <= sys.totalLockEpoch,
            "LE: Invalid epoch ID"
        );

        uint128 _toClaimAmount = getUnclaimAmountOf(epochId);

        require(_toClaimAmount > 0, "LE: No funds to claim");

        LockEpoch storage _le = epochs[epochId];
        require(
            _le.les == LockEpochState.releasing,
            "LE: Not in releasing stage"
        );

        address _receiver = roleNameHashToRoleInfo[
            _getRoleNameHash(_le.belongToRoleName)
        ].roleBindReceiver;

        _le.claimedAmount = getUnlockAmountOf(epochId);

        require(
            lockedToken.transfer(_receiver, _toClaimAmount),
            "LE: Transfer failed"
        );

        if (_le.claimedAmount == _le.totalLockAmount) {
            _le.les = LockEpochState.finished;
        }
        sys.totalClaimedAmount += _toClaimAmount;
    }

    function getSystemInfo() external view returns (SystemInfo memory sysInfo) {
        sysInfo = SystemInfo({
            totalLockedAmount: sys.totalLockedAmount,
            totalClaimedAmount: sys.totalClaimedAmount,
            totalLockEpoch: sys.totalLockEpoch
        });
    }

    function getLockEpochInfos(
        uint32 startEpochId,
        uint32 endEpochId
    ) external view returns (LockEpochInfo[] memory leis) {
        require(startEpochId <= endEpochId, "LE: Invalid epoch ID");
        leis = new LockEpochInfo[](endEpochId - startEpochId + 1);
        for (uint32 i = startEpochId; i <= endEpochId; i++) {
            leis[i - startEpochId] = getLockEpochInfo(i);
        }
    }

    function getLockEpochInfo(
        uint32 epochId
    ) public view returns (LockEpochInfo memory lei) {
        require(
            epochId > 0 && epochId <= sys.totalLockEpoch,
            "LE: Invalid epoch ID"
        );

        LockEpoch storage _le = epochs[epochId];

        uint128 _unlockAmount = getUnlockAmountOf(epochId);

        uint128 _unclaimAmount = getUnclaimAmountOf(epochId);

        uint128 _unReleaseAmount = _le.totalLockAmount - _unlockAmount;

        lei = LockEpochInfo({
            les: _le.les,
            belongToRoleName: _le.belongToRoleName,
            totalLockAmount: _le.totalLockAmount,
            unlockStartPoint: _le.unlockStartPoint,
            unlockEndPoint: _le.unlockEndPoint,
            claimedAmount: _le.claimedAmount,
            currentUnclaimAmount: _unclaimAmount,
            currentUnlockAmount: _unlockAmount,
            unReleaseAmount: _unReleaseAmount
        });
    }

    function getRoleInfos(
        string[] calldata roleNames
    ) external view returns (RoleInfo[] memory roleInfos) {
        roleInfos = new RoleInfo[](roleNames.length);
        for (uint256 i = 0; i < roleNames.length; i++) {
            roleInfos[i] = getRoleInfoByHash(getRoleNameHash(roleNames[i]));
        }
    }

    function getRoleInfoByHash(
        bytes32 roleHash
    ) public view returns (RoleInfo memory roleInfo) {
        roleInfo = roleNameHashToRoleInfo[roleHash];
    }
}
// 0xefD94041Fa3c6b1802d48057Cd6a9B0ee4276a89