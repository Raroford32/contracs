// Contract: FinanceHubOUSGv2 (0x16205e58126580383e5e0461720e336ae77c670e)
// Multi-file source


// ===== FILE: @openzeppelin/contracts-upgradeable/access/Ownable2StepUpgradeable.sol =====
// SPDX-License-Identifier: MIT
// OpenZeppelin Contracts (last updated v5.0.0) (access/Ownable2Step.sol)

pragma solidity ^0.8.20;

import {OwnableUpgradeable} from "./OwnableUpgradeable.sol";
import {Initializable} from "../proxy/utils/Initializable.sol";

/**
 * @dev Contract module which provides access control mechanism, where
 * there is an account (an owner) that can be granted exclusive access to
 * specific functions.
 *
 * The initial owner is specified at deployment time in the constructor for `Ownable`. This
 * can later be changed with {transferOwnership} and {acceptOwnership}.
 *
 * This module is used through inheritance. It will make available all functions
 * from parent (Ownable).
 */
abstract contract Ownable2StepUpgradeable is Initializable, OwnableUpgradeable {
    /// @custom:storage-location erc7201:openzeppelin.storage.Ownable2Step
    struct Ownable2StepStorage {
        address _pendingOwner;
    }

    // keccak256(abi.encode(uint256(keccak256("openzeppelin.storage.Ownable2Step")) - 1)) & ~bytes32(uint256(0xff))
    bytes32 private constant Ownable2StepStorageLocation = 0x237e158222e3e6968b72b9db0d8043aacf074ad9f650f0d1606b4d82ee432c00;

    function _getOwnable2StepStorage() private pure returns (Ownable2StepStorage storage $) {
        assembly {
            $.slot := Ownable2StepStorageLocation
        }
    }

    event OwnershipTransferStarted(address indexed previousOwner, address indexed newOwner);

    function __Ownable2Step_init() internal onlyInitializing {
    }

    function __Ownable2Step_init_unchained() internal onlyInitializing {
    }
    /**
     * @dev Returns the address of the pending owner.
     */
    function pendingOwner() public view virtual returns (address) {
        Ownable2StepStorage storage $ = _getOwnable2StepStorage();
        return $._pendingOwner;
    }

    /**
     * @dev Starts the ownership transfer of the contract to a new account. Replaces the pending transfer if there is one.
     * Can only be called by the current owner.
     */
    function transferOwnership(address newOwner) public virtual override onlyOwner {
        Ownable2StepStorage storage $ = _getOwnable2StepStorage();
        $._pendingOwner = newOwner;
        emit OwnershipTransferStarted(owner(), newOwner);
    }

    /**
     * @dev Transfers ownership of the contract to a new account (`newOwner`) and deletes any pending owner.
     * Internal function without access restriction.
     */
    function _transferOwnership(address newOwner) internal virtual override {
        Ownable2StepStorage storage $ = _getOwnable2StepStorage();
        delete $._pendingOwner;
        super._transferOwnership(newOwner);
    }

    /**
     * @dev The new owner accepts the ownership transfer.
     */
    function acceptOwnership() public virtual {
        address sender = _msgSender();
        if (pendingOwner() != sender) {
            revert OwnableUnauthorizedAccount(sender);
        }
        _transferOwnership(sender);
    }
}


// ===== FILE: @openzeppelin/contracts-upgradeable/access/OwnableUpgradeable.sol =====
// SPDX-License-Identifier: MIT
// OpenZeppelin Contracts (last updated v5.0.0) (access/Ownable.sol)

pragma solidity ^0.8.20;

import {ContextUpgradeable} from "../utils/ContextUpgradeable.sol";
import {Initializable} from "../proxy/utils/Initializable.sol";

/**
 * @dev Contract module which provides a basic access control mechanism, where
 * there is an account (an owner) that can be granted exclusive access to
 * specific functions.
 *
 * The initial owner is set to the address provided by the deployer. This can
 * later be changed with {transferOwnership}.
 *
 * This module is used through inheritance. It will make available the modifier
 * `onlyOwner`, which can be applied to your functions to restrict their use to
 * the owner.
 */
abstract contract OwnableUpgradeable is Initializable, ContextUpgradeable {
    /// @custom:storage-location erc7201:openzeppelin.storage.Ownable
    struct OwnableStorage {
        address _owner;
    }

    // keccak256(abi.encode(uint256(keccak256("openzeppelin.storage.Ownable")) - 1)) & ~bytes32(uint256(0xff))
    bytes32 private constant OwnableStorageLocation = 0x9016d09d72d40fdae2fd8ceac6b6234c7706214fd39c1cd1e609a0528c199300;

    function _getOwnableStorage() private pure returns (OwnableStorage storage $) {
        assembly {
            $.slot := OwnableStorageLocation
        }
    }

    /**
     * @dev The caller account is not authorized to perform an operation.
     */
    error OwnableUnauthorizedAccount(address account);

    /**
     * @dev The owner is not a valid owner account. (eg. `address(0)`)
     */
    error OwnableInvalidOwner(address owner);

    event OwnershipTransferred(address indexed previousOwner, address indexed newOwner);

    /**
     * @dev Initializes the contract setting the address provided by the deployer as the initial owner.
     */
    function __Ownable_init(address initialOwner) internal onlyInitializing {
        __Ownable_init_unchained(initialOwner);
    }

    function __Ownable_init_unchained(address initialOwner) internal onlyInitializing {
        if (initialOwner == address(0)) {
            revert OwnableInvalidOwner(address(0));
        }
        _transferOwnership(initialOwner);
    }

    /**
     * @dev Throws if called by any account other than the owner.
     */
    modifier onlyOwner() {
        _checkOwner();
        _;
    }

    /**
     * @dev Returns the address of the current owner.
     */
    function owner() public view virtual returns (address) {
        OwnableStorage storage $ = _getOwnableStorage();
        return $._owner;
    }

    /**
     * @dev Throws if the sender is not the owner.
     */
    function _checkOwner() internal view virtual {
        if (owner() != _msgSender()) {
            revert OwnableUnauthorizedAccount(_msgSender());
        }
    }

    /**
     * @dev Leaves the contract without owner. It will not be possible to call
     * `onlyOwner` functions. Can only be called by the current owner.
     *
     * NOTE: Renouncing ownership will leave the contract without an owner,
     * thereby disabling any functionality that is only available to the owner.
     */
    function renounceOwnership() public virtual onlyOwner {
        _transferOwnership(address(0));
    }

    /**
     * @dev Transfers ownership of the contract to a new account (`newOwner`).
     * Can only be called by the current owner.
     */
    function transferOwnership(address newOwner) public virtual onlyOwner {
        if (newOwner == address(0)) {
            revert OwnableInvalidOwner(address(0));
        }
        _transferOwnership(newOwner);
    }

    /**
     * @dev Transfers ownership of the contract to a new account (`newOwner`).
     * Internal function without access restriction.
     */
    function _transferOwnership(address newOwner) internal virtual {
        OwnableStorage storage $ = _getOwnableStorage();
        address oldOwner = $._owner;
        $._owner = newOwner;
        emit OwnershipTransferred(oldOwner, newOwner);
    }
}


// ===== FILE: @openzeppelin/contracts-upgradeable/proxy/utils/Initializable.sol =====
// SPDX-License-Identifier: MIT
// OpenZeppelin Contracts (last updated v5.0.0) (proxy/utils/Initializable.sol)

pragma solidity ^0.8.20;

/**
 * @dev This is a base contract to aid in writing upgradeable contracts, or any kind of contract that will be deployed
 * behind a proxy. Since proxied contracts do not make use of a constructor, it's common to move constructor logic to an
 * external initializer function, usually called `initialize`. It then becomes necessary to protect this initializer
 * function so it can only be called once. The {initializer} modifier provided by this contract will have this effect.
 *
 * The initialization functions use a version number. Once a version number is used, it is consumed and cannot be
 * reused. This mechanism prevents re-execution of each "step" but allows the creation of new initialization steps in
 * case an upgrade adds a module that needs to be initialized.
 *
 * For example:
 *
 * [.hljs-theme-light.nopadding]
 * ```solidity
 * contract MyToken is ERC20Upgradeable {
 *     function initialize() initializer public {
 *         __ERC20_init("MyToken", "MTK");
 *     }
 * }
 *
 * contract MyTokenV2 is MyToken, ERC20PermitUpgradeable {
 *     function initializeV2() reinitializer(2) public {
 *         __ERC20Permit_init("MyToken");
 *     }
 * }
 * ```
 *
 * TIP: To avoid leaving the proxy in an uninitialized state, the initializer function should be called as early as
 * possible by providing the encoded function call as the `_data` argument to {ERC1967Proxy-constructor}.
 *
 * CAUTION: When used with inheritance, manual care must be taken to not invoke a parent initializer twice, or to ensure
 * that all initializers are idempotent. This is not verified automatically as constructors are by Solidity.
 *
 * [CAUTION]
 * ====
 * Avoid leaving a contract uninitialized.
 *
 * An uninitialized contract can be taken over by an attacker. This applies to both a proxy and its implementation
 * contract, which may impact the proxy. To prevent the implementation contract from being used, you should invoke
 * the {_disableInitializers} function in the constructor to automatically lock it when it is deployed:
 *
 * [.hljs-theme-light.nopadding]
 * ```
 * /// @custom:oz-upgrades-unsafe-allow constructor
 * constructor() {
 *     _disableInitializers();
 * }
 * ```
 * ====
 */
abstract contract Initializable {
    /**
     * @dev Storage of the initializable contract.
     *
     * It's implemented on a custom ERC-7201 namespace to reduce the risk of storage collisions
     * when using with upgradeable contracts.
     *
     * @custom:storage-location erc7201:openzeppelin.storage.Initializable
     */
    struct InitializableStorage {
        /**
         * @dev Indicates that the contract has been initialized.
         */
        uint64 _initialized;
        /**
         * @dev Indicates that the contract is in the process of being initialized.
         */
        bool _initializing;
    }

    // keccak256(abi.encode(uint256(keccak256("openzeppelin.storage.Initializable")) - 1)) & ~bytes32(uint256(0xff))
    bytes32 private constant INITIALIZABLE_STORAGE = 0xf0c57e16840df040f15088dc2f81fe391c3923bec73e23a9662efc9c229c6a00;

    /**
     * @dev The contract is already initialized.
     */
    error InvalidInitialization();

    /**
     * @dev The contract is not initializing.
     */
    error NotInitializing();

    /**
     * @dev Triggered when the contract has been initialized or reinitialized.
     */
    event Initialized(uint64 version);

    /**
     * @dev A modifier that defines a protected initializer function that can be invoked at most once. In its scope,
     * `onlyInitializing` functions can be used to initialize parent contracts.
     *
     * Similar to `reinitializer(1)`, except that in the context of a constructor an `initializer` may be invoked any
     * number of times. This behavior in the constructor can be useful during testing and is not expected to be used in
     * production.
     *
     * Emits an {Initialized} event.
     */
    modifier initializer() {
        // solhint-disable-next-line var-name-mixedcase
        InitializableStorage storage $ = _getInitializableStorage();

        // Cache values to avoid duplicated sloads
        bool isTopLevelCall = !$._initializing;
        uint64 initialized = $._initialized;

        // Allowed calls:
        // - initialSetup: the contract is not in the initializing state and no previous version was
        //                 initialized
        // - construction: the contract is initialized at version 1 (no reininitialization) and the
        //                 current contract is just being deployed
        bool initialSetup = initialized == 0 && isTopLevelCall;
        bool construction = initialized == 1 && address(this).code.length == 0;

        if (!initialSetup && !construction) {
            revert InvalidInitialization();
        }
        $._initialized = 1;
        if (isTopLevelCall) {
            $._initializing = true;
        }
        _;
        if (isTopLevelCall) {
            $._initializing = false;
            emit Initialized(1);
        }
    }

    /**
     * @dev A modifier that defines a protected reinitializer function that can be invoked at most once, and only if the
     * contract hasn't been initialized to a greater version before. In its scope, `onlyInitializing` functions can be
     * used to initialize parent contracts.
     *
     * A reinitializer may be used after the original initialization step. This is essential to configure modules that
     * are added through upgrades and that require initialization.
     *
     * When `version` is 1, this modifier is similar to `initializer`, except that functions marked with `reinitializer`
     * cannot be nested. If one is invoked in the context of another, execution will revert.
     *
     * Note that versions can jump in increments greater than 1; this implies that if multiple reinitializers coexist in
     * a contract, executing them in the right order is up to the developer or operator.
     *
     * WARNING: Setting the version to 2**64 - 1 will prevent any future reinitialization.
     *
     * Emits an {Initialized} event.
     */
    modifier reinitializer(uint64 version) {
        // solhint-disable-next-line var-name-mixedcase
        InitializableStorage storage $ = _getInitializableStorage();

        if ($._initializing || $._initialized >= version) {
            revert InvalidInitialization();
        }
        $._initialized = version;
        $._initializing = true;
        _;
        $._initializing = false;
        emit Initialized(version);
    }

    /**
     * @dev Modifier to protect an initialization function so that it can only be invoked by functions with the
     * {initializer} and {reinitializer} modifiers, directly or indirectly.
     */
    modifier onlyInitializing() {
        _checkInitializing();
        _;
    }

    /**
     * @dev Reverts if the contract is not in an initializing state. See {onlyInitializing}.
     */
    function _checkInitializing() internal view virtual {
        if (!_isInitializing()) {
            revert NotInitializing();
        }
    }

    /**
     * @dev Locks the contract, preventing any future reinitialization. This cannot be part of an initializer call.
     * Calling this in the constructor of a contract will prevent that contract from being initialized or reinitialized
     * to any version. It is recommended to use this to lock implementation contracts that are designed to be called
     * through proxies.
     *
     * Emits an {Initialized} event the first time it is successfully executed.
     */
    function _disableInitializers() internal virtual {
        // solhint-disable-next-line var-name-mixedcase
        InitializableStorage storage $ = _getInitializableStorage();

        if ($._initializing) {
            revert InvalidInitialization();
        }
        if ($._initialized != type(uint64).max) {
            $._initialized = type(uint64).max;
            emit Initialized(type(uint64).max);
        }
    }

    /**
     * @dev Returns the highest version that has been initialized. See {reinitializer}.
     */
    function _getInitializedVersion() internal view returns (uint64) {
        return _getInitializableStorage()._initialized;
    }

    /**
     * @dev Returns `true` if the contract is currently initializing. See {onlyInitializing}.
     */
    function _isInitializing() internal view returns (bool) {
        return _getInitializableStorage()._initializing;
    }

    /**
     * @dev Returns a pointer to the storage namespace.
     */
    // solhint-disable-next-line var-name-mixedcase
    function _getInitializableStorage() private pure returns (InitializableStorage storage $) {
        assembly {
            $.slot := INITIALIZABLE_STORAGE
        }
    }
}


// ===== FILE: @openzeppelin/contracts-upgradeable/utils/ContextUpgradeable.sol =====
// SPDX-License-Identifier: MIT
// OpenZeppelin Contracts (last updated v5.0.1) (utils/Context.sol)

pragma solidity ^0.8.20;
import {Initializable} from "../proxy/utils/Initializable.sol";

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
abstract contract ContextUpgradeable is Initializable {
    function __Context_init() internal onlyInitializing {
    }

    function __Context_init_unchained() internal onlyInitializing {
    }
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


// ===== FILE: @openzeppelin/contracts-upgradeable/utils/PausableUpgradeable.sol =====
// SPDX-License-Identifier: MIT
// OpenZeppelin Contracts (last updated v5.0.0) (utils/Pausable.sol)

pragma solidity ^0.8.20;

import {ContextUpgradeable} from "../utils/ContextUpgradeable.sol";
import {Initializable} from "../proxy/utils/Initializable.sol";

/**
 * @dev Contract module which allows children to implement an emergency stop
 * mechanism that can be triggered by an authorized account.
 *
 * This module is used through inheritance. It will make available the
 * modifiers `whenNotPaused` and `whenPaused`, which can be applied to
 * the functions of your contract. Note that they will not be pausable by
 * simply including this module, only once the modifiers are put in place.
 */
abstract contract PausableUpgradeable is Initializable, ContextUpgradeable {
    /// @custom:storage-location erc7201:openzeppelin.storage.Pausable
    struct PausableStorage {
        bool _paused;
    }

    // keccak256(abi.encode(uint256(keccak256("openzeppelin.storage.Pausable")) - 1)) & ~bytes32(uint256(0xff))
    bytes32 private constant PausableStorageLocation = 0xcd5ed15c6e187e77e9aee88184c21f4f2182ab5827cb3b7e07fbedcd63f03300;

    function _getPausableStorage() private pure returns (PausableStorage storage $) {
        assembly {
            $.slot := PausableStorageLocation
        }
    }

    /**
     * @dev Emitted when the pause is triggered by `account`.
     */
    event Paused(address account);

    /**
     * @dev Emitted when the pause is lifted by `account`.
     */
    event Unpaused(address account);

    /**
     * @dev The operation failed because the contract is paused.
     */
    error EnforcedPause();

    /**
     * @dev The operation failed because the contract is not paused.
     */
    error ExpectedPause();

    /**
     * @dev Initializes the contract in unpaused state.
     */
    function __Pausable_init() internal onlyInitializing {
        __Pausable_init_unchained();
    }

    function __Pausable_init_unchained() internal onlyInitializing {
        PausableStorage storage $ = _getPausableStorage();
        $._paused = false;
    }

    /**
     * @dev Modifier to make a function callable only when the contract is not paused.
     *
     * Requirements:
     *
     * - The contract must not be paused.
     */
    modifier whenNotPaused() {
        _requireNotPaused();
        _;
    }

    /**
     * @dev Modifier to make a function callable only when the contract is paused.
     *
     * Requirements:
     *
     * - The contract must be paused.
     */
    modifier whenPaused() {
        _requirePaused();
        _;
    }

    /**
     * @dev Returns true if the contract is paused, and false otherwise.
     */
    function paused() public view virtual returns (bool) {
        PausableStorage storage $ = _getPausableStorage();
        return $._paused;
    }

    /**
     * @dev Throws if the contract is paused.
     */
    function _requireNotPaused() internal view virtual {
        if (paused()) {
            revert EnforcedPause();
        }
    }

    /**
     * @dev Throws if the contract is not paused.
     */
    function _requirePaused() internal view virtual {
        if (!paused()) {
            revert ExpectedPause();
        }
    }

    /**
     * @dev Triggers stopped state.
     *
     * Requirements:
     *
     * - The contract must not be paused.
     */
    function _pause() internal virtual whenNotPaused {
        PausableStorage storage $ = _getPausableStorage();
        $._paused = true;
        emit Paused(_msgSender());
    }

    /**
     * @dev Returns to normal state.
     *
     * Requirements:
     *
     * - The contract must be paused.
     */
    function _unpause() internal virtual whenPaused {
        PausableStorage storage $ = _getPausableStorage();
        $._paused = false;
        emit Unpaused(_msgSender());
    }
}


// ===== FILE: @openzeppelin/contracts/token/ERC20/IERC20.sol =====
// SPDX-License-Identifier: MIT
// OpenZeppelin Contracts (last updated v5.0.0) (token/ERC20/IERC20.sol)

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
    event Approval(address indexed owner, address indexed spender, uint256 value);

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
    function allowance(address owner, address spender) external view returns (uint256);

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
     * https://github.com/ethereum/EIPs/issues/20#issuecomment-263524729
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
    function transferFrom(address from, address to, uint256 value) external returns (bool);
}


// ===== FILE: contracts/FinanceHubOUSGv2.sol =====
// SPDX-License-Identifier: MIT
pragma solidity 0.8.24;

import "@openzeppelin/contracts/token/ERC20/IERC20.sol";
import "@openzeppelin/contracts-upgradeable/proxy/utils/Initializable.sol";
import "@openzeppelin/contracts-upgradeable/access/Ownable2StepUpgradeable.sol";
import "@openzeppelin/contracts-upgradeable/utils/PausableUpgradeable.sol";
import "./IUSDO.sol";
import "./IPricer.sol";
import "./IOUSGManager.sol";
import "./IOUSG_InstantManager.sol";

/// @title Interface for the Ondo Oracle
/// @notice Provides a function to get the price of an asset.
interface IOndoOracle {
    /// @notice Returns the price of the specified asset.
    /// @param asset The address of the asset.
    /// @return The price of the asset in USD with 6 decimals.
    function getAssetPrice(address asset) external view returns (uint256);
}

/// @title FinanceHubOUSGv2 Contract
/// @notice Manages the minting and redemption of omUSD using USDC and OUSG via the OUSG Instant Manager.
/// @dev This contract integrates with OpenZeppelin upgradeable contracts for ownership, pausing, and initialization.
/// It interacts with USDC, OUSG, omUSD (IUSDO), OUSGManager, Pricer, OUSG_InstantManager, and OndoOracle.
/// Version 2 utilizes the OUSG Instant Manager for subscriptions and redemptions. State variables and functions related to V1 OUSG Manager interactions are deprecated.
contract FinanceHubOUSGv2 is
    Initializable,
    Ownable2StepUpgradeable,
    PausableUpgradeable
{
    /// @notice The USDC token contract instance (6 decimals). Used for purchasing OUSG.
    IERC20 public constant USDC =
        IERC20(0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48); // USDC is the stablecoin used to buy the collateral decimals = 6
    /// @notice The OUSG token contract instance (18 decimals). The collateral backing omUSD.
    IERC20 public constant OUSG =
        IERC20(0x1B19C19393e2d034D8Ff31ff34c81252FcBbee92); // OUSG is the collateral decimals = 18
    /// @notice The omUSD (IUSDO) token contract instance (6 decimals). The managed stablecoin. Must be set, likely via a separate function post-initialization.
    IUSDO public USDO; // omUSD is the stablecoin that is managed by the DAO decimals = 6
    /// @notice The OUSG Manager contract instance (V1). Likely deprecated in V2.
    IOUSGManager public constant OUSGManager =
        IOUSGManager(0xF16c188c2D411627d39655A60409eC6707D3d5e8);
    /// @notice The Pricer contract instance (V1). Likely deprecated in V2.
    IPricer public constant pricer =
        IPricer(0xEc547E5aEf5Ce2e888604B1B6EC98A69fFDeaF2B);
    /// @notice The previous OUSG balance of this contract. Used for tracking changes (potentially related to V1).
    uint256 public previousOUSGBalance; // previous OUSG balance of contract
    /// @notice Flag indicating if OUSG deposit/redemption via OUSGManager (V1) is enabled. Likely deprecated in V2.
    bool public OUSGEnabled; // true if ONDO OUSG is enabled
    /// @notice The address of the DAO treasury receiving fees. Likely related to V1 and deprecated in V2.
    address public treasury; // Address of the DAO treasury receiving fees
    /// @notice The minimum deposit limit for USDC or omUSD. Likely related to V1 and deprecated in V2.
    uint256 public minDepositLimit; // Minimum amount of USDC or omUSD that can be deposited
    /// @notice The number of deposits/redemptions to process in a single batch transaction (V1). Likely deprecated.
    uint256 public batch_size; // Number of deposits/redemptions to process in a single transaction
    /// @notice The address authorized to pause the contract in emergencies.
    address public defender; // Address of the defender entity

    /// @notice Structure representing a DAO deposit related to V1 OUSG Manager interactions.
    struct DaoDeposit {
        uint256 amountDepositedMinusFees; // Amount potentially after fees
        uint256 timestamp; // Timestamp of the deposit
        bool claimed; // Whether the deposit has been claimed
    }

    /// @notice Structure representing a user's OUSG deposit related to V1 OUSG Manager interactions.
    struct UserOUSGDeposit {
        address depositor; // Address of the depositor
        uint256 amount; // Amount deposited
    }

    /// @notice Structure representing a DAO request related to V1 OUSG Manager redemptions.
    struct OUSGRequestDAO {
        bytes32 id; // Unique identifier for the request
        uint256 requestedDate; // Timestamp when the request was made
        uint256 requestedAmount; // Amount requested for redemption
        bool executed; // Whether the redemption request has been executed by the DAO
    }

    /// @notice Structure representing a user's OUSG redemption request related to V1 OUSG Manager interactions.
    struct UserOUSGRedemption {
        address requester; // Address of the requester
        uint256 amount; // Amount requested for redemption
    }

    /// @notice Structure representing a DAO redemption request related to V1 OUSG Manager redemptions.
    struct OUSGRedemptionDAO {
        bytes32 id; // Unique identifier for the request
        uint256 requestedDate; // Timestamp when the request was made
        uint256 requestedAmount; // Amount requested for redemption
        bool executed; // Whether the redemption request has been executed by the DAO
    }

    /// @notice Current deposit index for V1 OUSG Manager interactions. Likely deprecated.
    uint256 public depositIndexOUSG; // current ondo deposit index
    /// @notice Latest processed deposit index for V1 OUSG Manager interactions. Likely deprecated.
    /// @custom:oz-renamed-from latestPrceededDepositIndexOUSG
    uint256 public latestProcessedDepositIndexOUSG; // latest processed deposit index
    /// @notice Current redemption index for V1 OUSG Manager interactions. Likely deprecated.
    uint256 public redemptionOUSGIndex; // current ondo redemption index
    /// @notice Latest processed redemption index for V1 OUSG Manager interactions. Likely deprecated.
    /// @custom:oz-renamed-from latestPrceededRedemptionIndexOUSG
    uint256 public latestProcessedRedemptionIndexOUSG; // latest processed redemption index
    /// @notice Flag indicating a pending deposit to be processed via V1 OUSG Manager. Likely deprecated.
    bool public pendingDepositOUSG; // true if there is a pending deposit to be processed
    /// @notice Flag indicating a pending redemption to be processed via V1 OUSG Manager. Likely deprecated.
    bool public pendingRedemptionOUSG; // true if there is a pending redemption to be processed
    /// @notice Identifier for the pending deposit via V1 OUSG Manager. Likely deprecated.
    bytes32 public pendingDepositIdOUSG;
    /// @notice Identifier for the pending redemption via V1 OUSG Manager. Likely deprecated.
    bytes32 public pendingRedemptionIdOUSG;

    /// @notice Mapping from DAO deposit ID (V1) to DaoDeposit details. Likely deprecated.
    mapping(bytes32 => DaoDeposit) public daoDepositsOUSG; // Mapping of DAO deposits
    /// @notice Mapping from deposit index (V1) to UserOUSGDeposit details. Likely deprecated.
    mapping(uint256 => UserOUSGDeposit) public usersOUSGDeposits; // Mapping of user deposits
    /// @notice Mapping from batch deposit ID (V1) to an array of UserOUSGDeposit details. Likely deprecated.
    mapping(bytes32 => UserOUSGDeposit[]) public batchDepositsOUSG; // Batch deposits are used to group multiple deposits into a single transaction
    /// @notice Mapping from redemption index (V1) to UserOUSGRedemption details. Used by `migrateToInstantManager`.
    mapping(uint256 => UserOUSGRedemption) public usersOUSGRedemptionRequests;
    /// @notice Mapping from DAO redemption ID (V1) to OUSGRedemptionDAO details. Likely deprecated.
    mapping(bytes32 => OUSGRedemptionDAO) public daoRedemptionRequestsOUSG;
    /// @notice Mapping from batch redemption ID (V1) to an array of UserOUSGRedemption details. Likely deprecated.
    mapping(bytes32 => UserOUSGRedemption[]) public batchRedemptionsOUSG; // Batch redemptions are used to group multiple redemptions into a single transaction
    /// @notice Mapping from user address to the amount of USDC to be redeemed (V1). Likely deprecated.
    mapping(address => uint256) public usdcAmountTobeRedeemed; // USDC amount to be redeemed by user

    // V2 version state
    /// @notice The OUSG Instant Manager contract instance (V2). Handles subscriptions and redemptions.
    IOUSG_InstantManager public constant instantManager =
        IOUSG_InstantManager(0x93358db73B6cd4b98D89c8F5f230E81a95c2643a);
    /// @notice The Ondo Oracle contract instance. Used to fetch the OUSG price.
    IOndoOracle public constant ondoOracle =
        IOndoOracle(0x9Cad45a8BF0Ed41Ff33074449B357C7a1fAb4094);

    // Events for minting and redeeming
    /// @notice Emitted when omUSD is minted.
    /// @param to The recipient of the omUSD.
    /// @param omUSDamount The amount of omUSD minted (6 decimals).
    event MintOMUSD(address indexed to, uint256 omUSDamount);
    /// @notice Emitted when USDC is redeemed.
    /// @param to The recipient of the USDC.
    /// @param usdcAmount The amount of omUSD burned (6 decimals), corresponding to the amount requested for redemption.
    event RedeemUSDC(address indexed to, uint256 usdcAmount);

    /// @dev Disables initialization during construction for upgradeable contracts.
    /// @custom:oz-upgrades-unsafe-allow constructor
    constructor() {
        _disableInitializers();
    }

    /// @notice Initializes the contract, setting the owner and initializing Pausable state.
    /// @dev Called once after deployment or upgrade.
    function initialize(address _treasury) external initializer {
        require(_treasury != address(0), "Invalid treasury address");
        treasury = _treasury;

        batch_size = 100;

        // min 1000 USDC
        minDepositLimit = 1000 * 1e6; // 1000 USDC

        // ONDO
        depositIndexOUSG = 1;
        redemptionOUSGIndex = 1;

        latestProcessedDepositIndexOUSG = 1;
        latestProcessedRedemptionIndexOUSG = 1;

        pendingDepositOUSG = false;
        pendingRedemptionOUSG = false;

        OUSGEnabled = true;

        __Ownable_init(_treasury);
        __Pausable_init();
    }

    /// @notice Initializes the contract, setting the owner and initializing Pausable state.
    /// @dev Called once after deployment or upgrade.
    function initializeV2() public reinitializer(2) {
        // only admin proxy can call this function
        require(msg.sender == 0x72996e3634CABf9B1DA0A05FB6297c10E8035E67, "Not admin proxy");
        USDO.mint(
            usersOUSGRedemptionRequests[2].requester,
            usersOUSGRedemptionRequests[2].amount
        );
        delete usersOUSGRedemptionRequests[2];
    }

    /// @notice Mints omUSD by subscribing to OUSG using USDC via the Instant Manager.
    /// @dev Requires USDC allowance from the caller. Transfers USDC from the caller,
    /// approves the Instant Manager, calls `instantManager.subscribe`, checks minimum OUSG received,
    /// and mints omUSD to the recipient. Assumes `USDO` address is set. Contract should not be paused (implicit check via Ownable/Pausable).
    /// Instant Manager subscription must not be paused.
    /// @param to The address to receive the minted omUSD.
    /// @param amount The amount of USDC (6 decimals) to deposit.
    // Subscription Section: send USDC and receive omUSD
    function mintOMUSD(address to, uint256 amount) external {
        require(
            USDC.allowance(msg.sender, address(this)) >= amount,
            "Allowance not enough"
        );
        require(amount > 0, "Amount must be greater than 0");
        require(to != address(0), "Invalid recipient address");
        require(!instantManager.subscribePaused(), "Subscribing is disabled");

        USDC.transferFrom(msg.sender, address(this), amount);

        // Calculate minimum OUSG to receive based on Oracle price
        uint256 ousgPrice = ondoOracle.getAssetPrice(address(OUSG));
        require(ousgPrice > 0, "Invalid OUSG price");

        // Convert USDC amount (6 decimals) to expected OUSG amount (18 decimals)
        uint256 minimumOusgReceived = (amount * 1e30) / ousgPrice;

        // approve instantManager to spend USDC
        USDC.approve(address(instantManager), amount);

        // Call instantManager to buy OUSG
        uint256 ousgAmountOut = instantManager.subscribe(
            address(USDC),
            amount,
            minimumOusgReceived
        );

        require(
            ousgAmountOut >= minimumOusgReceived,
            "Minimum OUSG received not met"
        );

        // mint omUSD to the user
        USDO.mint(to, amount);

        emit MintOMUSD(to, amount);
    }

    /**
     * @notice Redeems a specified amount of OUSG for USDC. (Original comment, kept for history)
     * @param to The address to receive the USDC.
     * @param amount The amount of omUSD to be burned. is in omUSD decimals (6)
     */
    function redeemUSDC(address to, uint256 amount) external {
        require(
            USDO.allowance(msg.sender, address(this)) >= amount,
            "Allowance not enough"
        );
        require(amount > 0, "Amount must be greater than 0");
        require(to != address(0), "Invalid recipient address");
        require(!instantManager.redeemPaused(), "Redeeming is disabled");

        USDO.burnFrom(msg.sender, amount);

        // Get current OUSG price from Oracle (USDC per OUSG, 6 decimals)
        uint256 ousgPrice = ondoOracle.getAssetPrice(address(OUSG));
        require(ousgPrice > 0, "Invalid OUSG price");

        // Calculate OUSG amount to redeem based on omUSD amount burned
        uint256 ousgAmountToRedeem = (amount * 1e30) / ousgPrice;

        // Calculate minimum USDC to receive (same as input amount with small slippage tolerance)
        uint256 minimumUSDCReceived = (amount * 995) / 1000; // 0.5% slippage tolerance

        // approve instantManager to spend OUSG
        // Ensure contract has sufficient OUSG balance
        require(
            OUSG.balanceOf(address(this)) >= ousgAmountToRedeem,
            "Insufficient OUSG balance in contract"
        );
        OUSG.approve(address(instantManager), ousgAmountToRedeem);

        // Call instantManager to redeem OUSG for USDC
        uint256 usdcAmountOut = instantManager.redeem(
            ousgAmountToRedeem, // Amount of OUSG to redeem (18 decimals)
            address(USDC), // Token to receive (USDC)
            minimumUSDCReceived // Minimum USDC to receive (6 decimals)
        );

        require(
            usdcAmountOut >= minimumUSDCReceived,
            "Minimum USDC not received"
        );

        USDC.transfer(to, usdcAmountOut);

        emit RedeemUSDC(to, amount);
    }

    // DAO CONFIGURATION SECTION

    /// @notice Sets the address of the defender entity, which can pause the contract. Only callable by the owner.
    /// @param _defender The address of the defender contract or EOA.
    // Set the address of the defender entity (Original Comment)
    // @param _defender The address of the defender contract (Original Comment)
    function setDefender(address _defender) external onlyOwner {
        require(_defender != address(0), "Invalid defender address");
        defender = _defender;
    }

    /// @notice Pauses the contract operations (state changes via _pause()). Only callable by the defender.
    /// @dev Emits a Paused event. Requires defender address to be set and msg.sender must be defender.
    // @notice Pauses the contract in case of emergency (Original Comment)
    function pause() external {
        require(msg.sender == defender, "Not defender");
        _pause();
    }

    /// @notice Unpauses the contract operations (state changes via _unpause()). Only callable by the owner (likely via DAO proposal).
    /// @dev Emits an Unpaused event.
    // @notice Unpause contract by DAO proposal (Original Comment)
    function unpause() external onlyOwner {
        _unpause();
    }

    /// @notice Withdraws the entire USDC balance of this contract to a specified address. Only callable by the owner.
    /// @dev Used to withdraw accrued fees or residual USDC.
    /// @param to The address to receive the withdrawn USDC.
    // withdraw all USDC from contract, accrued fees (Original Comment)
    function withdrawUSDC(address to) external onlyOwner {
        require(
            USDC.balanceOf(address(this)) > 0,
            "Not enough USDC to withdraw"
        );
        bool success = USDC.transfer(to, USDC.balanceOf(address(this)));
        require(success, "USDC transfer failed");
    }
}


// ===== FILE: contracts/IOUSG_InstantManager.sol =====
// SPDX-License-Identifier: BUSL-1.1
/*
      ▄▄█████████▄
   ╓██▀└ ,╓▄▄▄, '▀██▄
  ██▀ ▄██▀▀╙╙▀▀██▄ └██µ           ,,       ,,      ,     ,,,            ,,,
 ██ ,██¬ ▄████▄  ▀█▄ ╙█▄      ▄███▀▀███▄   ███▄    ██  ███▀▀▀███▄    ▄███▀▀███,
██  ██ ╒█▀'   ╙█▌ ╙█▌ ██     ▐██      ███  █████,  ██  ██▌    └██▌  ██▌     └██▌
██ ▐█▌ ██      ╟█  █▌ ╟█     ██▌      ▐██  ██ └███ ██  ██▌     ╟██ j██       ╟██
╟█  ██ ╙██    ▄█▀ ▐█▌ ██     ╙██      ██▌  ██   ╙████  ██▌    ▄██▀  ██▌     ,██▀
 ██ "██, ╙▀▀███████████⌐      ╙████████▀   ██     ╙██  ███████▀▀     ╙███████▀`
  ██▄ ╙▀██▄▄▄▄▄,,,                ¬─                                    '─¬
   ╙▀██▄ '╙╙╙▀▀▀▀▀▀▀▀
      ╙▀▀██████R⌐
 */
pragma solidity 0.8.24;

interface IOUSG_InstantManager {

    function subscribePaused() external view returns (bool);
    function redeemPaused() external view returns (bool);
    
    function subscribe(
        address depositToken,
        uint256 depositAmount,
        uint256 minimumRwaReceived
    ) external returns (uint256 rwaAmountOut);

    function subscribeRebasingOUSG(
        address depositToken,
        uint256 depositAmount,
        uint256 minimumRwaReceived
    ) external returns (uint256 rousgAmountOut);

    function redeem(
        uint256 rwaAmount,
        address receivingToken,
        uint256 minimumTokenReceived
    ) external returns (uint256 receiveTokenAmount);

    function redeemRebasingOUSG(
        uint256 rwaAmount,
        address receivingToken,
        uint256 minimumTokenReceived
    ) external returns (uint256 receiveTokenAmount);
}


// ===== FILE: contracts/IOUSGManager.sol =====
//SPDX-License-Identifier: MIT
pragma solidity ^0.8.16;

interface IOUSGManager {
    // Struct to contain the deposit information for a given depositId
    // struct Depositor {
    //     address user;
    //     uint256 amountDepositedMinusFees;
    //     uint256 priceId;
    // }

    // Struct to contain the redemption information for a given redemptionId
    // struct Redeemer {
    //     address user;
    //     uint256 amountRwaTokenBurned;
    //     uint256 priceId;
    // }

    // Set the price id for deposits
    function setPriceIdForDeposits(
        bytes32[] calldata depositIds,
        uint256[] calldata priceIds
    ) external;

    // Claim RWA
    function claimMint(bytes32[] calldata depositIds) external;

    // Claim USDC
    function claimRedemption(bytes32[] calldata redemptionIds) external;

    // Mapping from deposit Id -> Depositor
    function depositIdToDepositor(
        bytes32 subscriptionId
    ) external view returns (address, uint256, uint256);

    // Mapping from redemption Id -> Redeemer
    function redemptionIdToRedeemer(
        bytes32 redemptionId
    ) external view returns (address, uint256, uint256);

    /// @notice Returns the minimum amount that must be deposited to mint the RWA token
    function minimumDepositAmount() external view returns (uint256);

    /// @notice Returns the minimum amount that must be redeemed for a withdraw request
    function minimumRedemptionAmount() external view returns (uint256);

    /// @notice Returns the current subscription request counter
    function subscriptionRequestCounter() external view returns (uint256);

    /// @notice Returns the current redemption request counter
    function redemptionRequestCounter() external view returns (uint256);

    /// @notice Requests subscription to the fund with a specified amount of collateral
    function requestSubscription(uint256 amount) external;

    /// @notice Requests a redemption from the fund with a specified amount of RWA tokens
    function requestRedemption(uint256 amount) external;

    function redemptionPaused() external view returns (bool);
    function subscriptionPaused() external view returns (bool);

    function setPriceIdForRedemptions(
        bytes32[] calldata redemptionIds,
        uint256[] calldata priceIds
    ) external;

    /// @notice Returns the redemption fee specified in basis points
	function redemptionFee() external view returns (uint256);

    function BPS_DENOMINATOR() external pure returns (uint256);

    function decimalsMultiplier() external view returns (uint256);

    function setAssetSender(address newAssetSender) external;

}


// ===== FILE: contracts/IPricer.sol =====
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

interface IPricer {
    /**
     * @notice Gets the latest price of the asset
     *
     * @return uint256 The latest price of the asset
     */
    function getLatestPrice() external view returns (uint256);
    
    function currentPriceId() external view returns (uint256);

    /**
     * @notice Gets the price of the asset at a specific priceId
     *
     * @param priceId The priceId at which to get the price
     *
     * @return uint256 The price of the asset with the given priceId
     */
    function getPrice(uint256 priceId) external view returns (uint256);

    function addPrice(uint256 price, uint256 timestamp) external;
}


// ===== FILE: contracts/IUSDO.sol =====
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import "@openzeppelin/contracts/token/ERC20/IERC20.sol";

interface IUSDO is IERC20 {
	function mint(address to, uint256 amount) external;

	function burnFrom(address from, uint256 amount) external;

	function balanceOf(address account) external view returns (uint256);
	
}
