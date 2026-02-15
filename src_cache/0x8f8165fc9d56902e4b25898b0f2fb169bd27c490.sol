/**
 *Submitted for verification at Arbiscan.io on 2024-12-30
*/

// SPDX-License-Identifier: MIT

// File @openzeppelin/contracts/utils/introspection/IERC165.sol@v4.9.3

// Original license: SPDX_License_Identifier: MIT
// OpenZeppelin Contracts v4.4.1 (utils/introspection/IERC165.sol)

pragma solidity ^0.8.0;

/**
 * @dev Interface of the ERC165 standard, as defined in the
 * https://eips.ethereum.org/EIPS/eip-165[EIP].
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
     * https://eips.ethereum.org/EIPS/eip-165#how-interfaces-are-identified[EIP section]
     * to learn more about how these ids are created.
     *
     * This function call must use less than 30 000 gas.
     */
    function supportsInterface(bytes4 interfaceId) external view returns (bool);
}


// File @openzeppelin/contracts/token/ERC1155/IERC1155.sol@v4.9.3

// Original license: SPDX_License_Identifier: MIT
// OpenZeppelin Contracts (last updated v4.9.0) (token/ERC1155/IERC1155.sol)

pragma solidity ^0.8.0;

/**
 * @dev Required interface of an ERC1155 compliant contract, as defined in the
 * https://eips.ethereum.org/EIPS/eip-1155[EIP].
 *
 * _Available since v3.1._
 */
interface IERC1155 is IERC165 {
    /**
     * @dev Emitted when `value` tokens of token type `id` are transferred from `from` to `to` by `operator`.
     */
    event TransferSingle(address indexed operator, address indexed from, address indexed to, uint256 id, uint256 value);

    /**
     * @dev Equivalent to multiple {TransferSingle} events, where `operator`, `from` and `to` are the same for all
     * transfers.
     */
    event TransferBatch(
        address indexed operator,
        address indexed from,
        address indexed to,
        uint256[] ids,
        uint256[] values
    );

    /**
     * @dev Emitted when `account` grants or revokes permission to `operator` to transfer their tokens, according to
     * `approved`.
     */
    event ApprovalForAll(address indexed account, address indexed operator, bool approved);

    /**
     * @dev Emitted when the URI for token type `id` changes to `value`, if it is a non-programmatic URI.
     *
     * If an {URI} event was emitted for `id`, the standard
     * https://eips.ethereum.org/EIPS/eip-1155#metadata-extensions[guarantees] that `value` will equal the value
     * returned by {IERC1155MetadataURI-uri}.
     */
    event URI(string value, uint256 indexed id);

    /**
     * @dev Returns the amount of tokens of token type `id` owned by `account`.
     *
     * Requirements:
     *
     * - `account` cannot be the zero address.
     */
    function balanceOf(address account, uint256 id) external view returns (uint256);

    /**
     * @dev xref:ROOT:erc1155.adoc#batch-operations[Batched] version of {balanceOf}.
     *
     * Requirements:
     *
     * - `accounts` and `ids` must have the same length.
     */
    function balanceOfBatch(
        address[] calldata accounts,
        uint256[] calldata ids
    ) external view returns (uint256[] memory);

    /**
     * @dev Grants or revokes permission to `operator` to transfer the caller's tokens, according to `approved`,
     *
     * Emits an {ApprovalForAll} event.
     *
     * Requirements:
     *
     * - `operator` cannot be the caller.
     */
    function setApprovalForAll(address operator, bool approved) external;

    /**
     * @dev Returns true if `operator` is approved to transfer ``account``'s tokens.
     *
     * See {setApprovalForAll}.
     */
    function isApprovedForAll(address account, address operator) external view returns (bool);

    /**
     * @dev Transfers `amount` tokens of token type `id` from `from` to `to`.
     *
     * Emits a {TransferSingle} event.
     *
     * Requirements:
     *
     * - `to` cannot be the zero address.
     * - If the caller is not `from`, it must have been approved to spend ``from``'s tokens via {setApprovalForAll}.
     * - `from` must have a balance of tokens of type `id` of at least `amount`.
     * - If `to` refers to a smart contract, it must implement {IERC1155Receiver-onERC1155Received} and return the
     * acceptance magic value.
     */
    function safeTransferFrom(address from, address to, uint256 id, uint256 amount, bytes calldata data) external;

    /**
     * @dev xref:ROOT:erc1155.adoc#batch-operations[Batched] version of {safeTransferFrom}.
     *
     * Emits a {TransferBatch} event.
     *
     * Requirements:
     *
     * - `ids` and `amounts` must have the same length.
     * - If `to` refers to a smart contract, it must implement {IERC1155Receiver-onERC1155BatchReceived} and return the
     * acceptance magic value.
     */
    function safeBatchTransferFrom(
        address from,
        address to,
        uint256[] calldata ids,
        uint256[] calldata amounts,
        bytes calldata data
    ) external;
}


// File @openzeppelin/contracts/token/ERC721/IERC721.sol@v4.9.3

// Original license: SPDX_License_Identifier: MIT
// OpenZeppelin Contracts (last updated v4.9.0) (token/ERC721/IERC721.sol)

pragma solidity ^0.8.0;

/**
 * @dev Required interface of an ERC721 compliant contract.
 */
interface IERC721 is IERC165 {
    /**
     * @dev Emitted when `tokenId` token is transferred from `from` to `to`.
     */
    event Transfer(address indexed from, address indexed to, uint256 indexed tokenId);

    /**
     * @dev Emitted when `owner` enables `approved` to manage the `tokenId` token.
     */
    event Approval(address indexed owner, address indexed approved, uint256 indexed tokenId);

    /**
     * @dev Emitted when `owner` enables or disables (`approved`) `operator` to manage all of its assets.
     */
    event ApprovalForAll(address indexed owner, address indexed operator, bool approved);

    /**
     * @dev Returns the number of tokens in ``owner``'s account.
     */
    function balanceOf(address owner) external view returns (uint256 balance);

    /**
     * @dev Returns the owner of the `tokenId` token.
     *
     * Requirements:
     *
     * - `tokenId` must exist.
     */
    function ownerOf(uint256 tokenId) external view returns (address owner);

    /**
     * @dev Safely transfers `tokenId` token from `from` to `to`.
     *
     * Requirements:
     *
     * - `from` cannot be the zero address.
     * - `to` cannot be the zero address.
     * - `tokenId` token must exist and be owned by `from`.
     * - If the caller is not `from`, it must be approved to move this token by either {approve} or {setApprovalForAll}.
     * - If `to` refers to a smart contract, it must implement {IERC721Receiver-onERC721Received}, which is called upon a safe transfer.
     *
     * Emits a {Transfer} event.
     */
    function safeTransferFrom(address from, address to, uint256 tokenId, bytes calldata data) external;

    /**
     * @dev Safely transfers `tokenId` token from `from` to `to`, checking first that contract recipients
     * are aware of the ERC721 protocol to prevent tokens from being forever locked.
     *
     * Requirements:
     *
     * - `from` cannot be the zero address.
     * - `to` cannot be the zero address.
     * - `tokenId` token must exist and be owned by `from`.
     * - If the caller is not `from`, it must have been allowed to move this token by either {approve} or {setApprovalForAll}.
     * - If `to` refers to a smart contract, it must implement {IERC721Receiver-onERC721Received}, which is called upon a safe transfer.
     *
     * Emits a {Transfer} event.
     */
    function safeTransferFrom(address from, address to, uint256 tokenId) external;

    /**
     * @dev Transfers `tokenId` token from `from` to `to`.
     *
     * WARNING: Note that the caller is responsible to confirm that the recipient is capable of receiving ERC721
     * or else they may be permanently lost. Usage of {safeTransferFrom} prevents loss, though the caller must
     * understand this adds an external call which potentially creates a reentrancy vulnerability.
     *
     * Requirements:
     *
     * - `from` cannot be the zero address.
     * - `to` cannot be the zero address.
     * - `tokenId` token must be owned by `from`.
     * - If the caller is not `from`, it must be approved to move this token by either {approve} or {setApprovalForAll}.
     *
     * Emits a {Transfer} event.
     */
    function transferFrom(address from, address to, uint256 tokenId) external;

    /**
     * @dev Gives permission to `to` to transfer `tokenId` token to another account.
     * The approval is cleared when the token is transferred.
     *
     * Only a single account can be approved at a time, so approving the zero address clears previous approvals.
     *
     * Requirements:
     *
     * - The caller must own the token or be an approved operator.
     * - `tokenId` must exist.
     *
     * Emits an {Approval} event.
     */
    function approve(address to, uint256 tokenId) external;

    /**
     * @dev Approve or remove `operator` as an operator for the caller.
     * Operators can call {transferFrom} or {safeTransferFrom} for any token owned by the caller.
     *
     * Requirements:
     *
     * - The `operator` cannot be the caller.
     *
     * Emits an {ApprovalForAll} event.
     */
    function setApprovalForAll(address operator, bool approved) external;

    /**
     * @dev Returns the account approved for `tokenId` token.
     *
     * Requirements:
     *
     * - `tokenId` must exist.
     */
    function getApproved(uint256 tokenId) external view returns (address operator);

    /**
     * @dev Returns if the `operator` is allowed to manage all of the assets of `owner`.
     *
     * See {setApprovalForAll}
     */
    function isApprovedForAll(address owner, address operator) external view returns (bool);
}


// File contracts/lib/BasicStorageLib.sol

// Original license: SPDX_License_Identifier: MIT

pragma solidity ^0.8.18;

library BasicStorageLib {

    struct UintData {
        mapping(bytes => mapping(bytes => uint))           _storage;
    }

    struct BoolData {
        mapping(bytes => mapping(bytes => bool))           _storage;
    }

    struct AddressData {
        mapping(bytes => mapping(bytes => address))        _storage;
    }

    struct BytesData {
        mapping(bytes => mapping(bytes => bytes))          _storage;
    }

    struct StringData {
        mapping(bytes => mapping(bytes => string))         _storage;
    }

    /* uintStorage */

    function setStorage(UintData storage self, bytes memory key, bytes memory innerKey, uint value) internal {
        self._storage[key][innerKey] = value;
    }

    function getStorage(UintData storage self, bytes memory key, bytes memory innerKey) internal view returns (uint) {
        return self._storage[key][innerKey];
    }

    function delStorage(UintData storage self, bytes memory key, bytes memory innerKey) internal {
        delete self._storage[key][innerKey];
    }

    /* boolStorage */

    function setStorage(BoolData storage self, bytes memory key, bytes memory innerKey, bool value) internal {
        self._storage[key][innerKey] = value;
    }

    function getStorage(BoolData storage self, bytes memory key, bytes memory innerKey) internal view returns (bool) {
        return self._storage[key][innerKey];
    }

    function delStorage(BoolData storage self, bytes memory key, bytes memory innerKey) internal {
        delete self._storage[key][innerKey];
    }

    /* addressStorage */

    function setStorage(AddressData storage self, bytes memory key, bytes memory innerKey, address value) internal {
        self._storage[key][innerKey] = value;
    }

    function getStorage(AddressData storage self, bytes memory key, bytes memory innerKey) internal view returns (address) {
        return self._storage[key][innerKey];
    }

    function delStorage(AddressData storage self, bytes memory key, bytes memory innerKey) internal {
        delete self._storage[key][innerKey];
    }

    /* bytesStorage */

    function setStorage(BytesData storage self, bytes memory key, bytes memory innerKey, bytes memory value) internal {
        self._storage[key][innerKey] = value;
    }

    function getStorage(BytesData storage self, bytes memory key, bytes memory innerKey) internal view returns (bytes memory) {
        return self._storage[key][innerKey];
    }

    function delStorage(BytesData storage self, bytes memory key, bytes memory innerKey) internal {
        delete self._storage[key][innerKey];
    }

    /* stringStorage */

    function setStorage(StringData storage self, bytes memory key, bytes memory innerKey, string memory value) internal {
        self._storage[key][innerKey] = value;
    }

    function getStorage(StringData storage self, bytes memory key, bytes memory innerKey) internal view returns (string memory) {
        return self._storage[key][innerKey];
    }

    function delStorage(StringData storage self, bytes memory key, bytes memory innerKey) internal {
        delete self._storage[key][innerKey];
    }

}


// File contracts/components/BasicStorage.sol

// Original license: SPDX_License_Identifier: MIT

pragma solidity ^0.8.18;

contract BasicStorage {
    /************************************************************
     **
     ** VARIABLES
     **
     ************************************************************/

    //// basic variables
    using BasicStorageLib for BasicStorageLib.UintData;
    using BasicStorageLib for BasicStorageLib.BoolData;
    using BasicStorageLib for BasicStorageLib.AddressData;
    using BasicStorageLib for BasicStorageLib.BytesData;
    using BasicStorageLib for BasicStorageLib.StringData;

    BasicStorageLib.UintData    internal uintData;
    BasicStorageLib.BoolData    internal boolData;
    BasicStorageLib.AddressData internal addressData;
    BasicStorageLib.BytesData   internal bytesData;
    BasicStorageLib.StringData  internal stringData;
}


// File contracts/components/Owned.sol

// Original license: SPDX_License_Identifier: MIT

/*

  Copyright 2023 Wanchain Foundation.

  Licensed under the Apache License, Version 2.0 (the "License");
  you may not use this file except in compliance with the License.
  You may obtain a copy of the License at

  http://www.apache.org/licenses/LICENSE-2.0

  Unless required by applicable law or agreed to in writing, software
  distributed under the License is distributed on an "AS IS" BASIS,
  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
  See the License for the specific language governing permissions and
  limitations under the License.

*/

//                            _           _           _
//  __      ____ _ _ __   ___| |__   __ _(_)_ __   __| | _____   __
//  \ \ /\ / / _` | '_ \ / __| '_ \ / _` | | '_ \@/ _` |/ _ \ \ / /
//   \ V  V / (_| | | | | (__| | | | (_| | | | | | (_| |  __/\ V /
//    \_/\_/ \__,_|_| |_|\___|_| |_|\__,_|_|_| |_|\__,_|\___| \_/
//
//

pragma solidity ^0.8.18;

/// @dev `Owned` is a base level contract that assigns an `owner` that can be
///  later changed
contract Owned {

    event OwnershipTransferred(address indexed previousOwner, address indexed newOwner);

    /// @dev `owner` is the only address that can call a function with this
    /// modifier
    modifier onlyOwner() {
        require(msg.sender == owner, "Not owner");
        _;
    }

    address public owner;

    /// @notice The Constructor assigns the message sender to be `owner`
    constructor() {
        owner = msg.sender;
    }

    address public newOwner;

    function transferOwner(address _newOwner) public onlyOwner {
        require(_newOwner != address(0), "New owner is the zero address");
        emit OwnershipTransferred(owner, _newOwner);
        owner = _newOwner;
    }

    /// @notice `owner` can step down and assign some other address to this role
    /// @param _newOwner The address of the new owner. 0x0 can be used to create
    ///  an unowned neutral vault, however that cannot be undone
    function changeOwner(address _newOwner) public onlyOwner {
        newOwner = _newOwner;
    }

    function acceptOwnership() public {
        if (msg.sender == newOwner) {
            owner = newOwner;
        }
    }

    function renounceOwnership() public onlyOwner {
        owner = address(0);
    }
}


// File contracts/components/Halt.sol

// Original license: SPDX_License_Identifier: MIT

/*

  Copyright 2023 Wanchain Foundation.

  Licensed under the Apache License, Version 2.0 (the "License");
  you may not use this file except in compliance with the License.
  You may obtain a copy of the License at

  http://www.apache.org/licenses/LICENSE-2.0

  Unless required by applicable law or agreed to in writing, software
  distributed under the License is distributed on an "AS IS" BASIS,
  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
  See the License for the specific language governing permissions and
  limitations under the License.

*/

//                            _           _           _
//  __      ____ _ _ __   ___| |__   __ _(_)_ __   __| | _____   __
//  \ \ /\ / / _` | '_ \ / __| '_ \ / _` | | '_ \@/ _` |/ _ \ \ / /
//   \ V  V / (_| | | | | (__| | | | (_| | | | | | (_| |  __/\ V /
//    \_/\_/ \__,_|_| |_|\___|_| |_|\__,_|_|_| |_|\__,_|\___| \_/
//
//

pragma solidity ^0.8.18;

contract Halt is Owned {

    bool public halted = false;

    modifier notHalted() {
        require(!halted, "Smart contract is halted");
        _;
    }

    modifier isHalted() {
        require(halted, "Smart contract is not halted");
        _;
    }

    /// @notice function Emergency situation that requires
    /// @notice contribution period to stop or not.
    function setHalt(bool halt)
        public
        onlyOwner
    {
        halted = halt;
    }
}


// File contracts/components/Proxy.sol

// Original license: SPDX_License_Identifier: MIT

/*

  Copyright 2023 Wanchain Foundation.

  Licensed under the Apache License, Version 2.0 (the "License");
  you may not use this file except in compliance with the License.
  You may obtain a copy of the License at

  http://www.apache.org/licenses/LICENSE-2.0

  Unless required by applicable law or agreed to in writing, software
  distributed under the License is distributed on an "AS IS" BASIS,
  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
  See the License for the specific language governing permissions and
  limitations under the License.

*/

//                            _           _           _
//  __      ____ _ _ __   ___| |__   __ _(_)_ __   __| | _____   __
//  \ \ /\ / / _` | '_ \ / __| '_ \ / _` | | '_ \@/ _` |/ _ \ \ / /
//   \ V  V / (_| | | | | (__| | | | (_| | | | | | (_| |  __/\ V /
//    \_/\_/ \__,_|_| |_|\___|_| |_|\__,_|_|_| |_|\__,_|\___| \_/
//
//

pragma solidity ^0.8.18;

/**
 * Math operations with safety checks
 */


contract Proxy {

    event Upgraded(address indexed implementation);

    address internal _implementation;

    function implementation() public view returns (address) {
        return _implementation;
    }

    function _fallback() internal {
        address _impl = _implementation;
        require(_impl != address(0), "implementation contract not set");

        assembly {
            let ptr := mload(0x40)
            calldatacopy(ptr, 0, calldatasize())
            let result := delegatecall(gas(), _impl, ptr, calldatasize(), 0, 0)
            let size := returndatasize()
            returndatacopy(ptr, 0, size)

            switch result
            case 0 { revert(ptr, size) }
            default { return(ptr, size) }
        }
    }
    fallback() external payable {
        return _fallback();
    }
    receive() external payable {
        return _fallback();
    }
}


// File contracts/components/ReentrancyGuard.sol

// Original license: SPDX_License_Identifier: MIT

pragma solidity ^0.8.18;

/**
 * @dev Contract module that helps prevent reentrant calls to a function.
 *
 * Inheriting from `ReentrancyGuard` will make the {nonReentrant} modifier
 * available, which can be applied to functions to make sure there are no nested
 * (reentrant) calls to them.
 *
 * Note that because there is a single `nonReentrant` guard, functions marked as
 * `nonReentrant` may not call one another. This can be worked around by making
 * those functions `private`, and then adding `external` `nonReentrant` entry
 * points to them.
 *
 * TIP: If you would like to learn more about reentrancy and alternative ways
 * to protect against it, check out our blog post
 * https://blog.openzeppelin.com/reentrancy-after-istanbul/[Reentrancy After Istanbul].
 */
abstract contract ReentrancyGuard {
    bool private _notEntered;

    constructor () {
        // Storing an initial non-zero value makes deployment a bit more
        // expensive, but in exchange the refund on every call to nonReentrant
        // will be lower in amount. Since refunds are capped to a percetange of
        // the total transaction's gas, it is best to keep them low in cases
        // like this one, to increase the likelihood of the full refund coming
        // into effect.
        _notEntered = true;
    }

    /**
     * @dev Prevents a contract from calling itself, directly or indirectly.
     * Calling a `nonReentrant` function from another `nonReentrant`
     * function is not supported. It is possible to prevent this from happening
     * by making the `nonReentrant` function external, and make it call a
     * `private` function that does the actual work.
     */
    modifier nonReentrant() {
        // On the first call to nonReentrant, _notEntered will be true
        require(_notEntered, "ReentrancyGuard: reentrant call");

        // Any calls to nonReentrant after this point will fail
        _notEntered = false;

        _;

        // By storing the original value once again, a refund is triggered (see
        // https://eips.ethereum.org/EIPS/eip-2200)
        _notEntered = true;
    }
}


// File @openzeppelin/contracts/utils/math/SafeMath.sol@v4.9.3

// Original license: SPDX_License_Identifier: MIT
// OpenZeppelin Contracts (last updated v4.9.0) (utils/math/SafeMath.sol)

pragma solidity ^0.8.0;

// CAUTION
// This version of SafeMath should only be used with Solidity 0.8 or later,
// because it relies on the compiler's built in overflow checks.

/**
 * @dev Wrappers over Solidity's arithmetic operations.
 *
 * NOTE: `SafeMath` is generally not needed starting with Solidity 0.8, since the compiler
 * now has built in overflow checking.
 */
library SafeMath {
    /**
     * @dev Returns the addition of two unsigned integers, with an overflow flag.
     *
     * _Available since v3.4._
     */
    function tryAdd(uint256 a, uint256 b) internal pure returns (bool, uint256) {
        unchecked {
            uint256 c = a + b;
            if (c < a) return (false, 0);
            return (true, c);
        }
    }

    /**
     * @dev Returns the subtraction of two unsigned integers, with an overflow flag.
     *
     * _Available since v3.4._
     */
    function trySub(uint256 a, uint256 b) internal pure returns (bool, uint256) {
        unchecked {
            if (b > a) return (false, 0);
            return (true, a - b);
        }
    }

    /**
     * @dev Returns the multiplication of two unsigned integers, with an overflow flag.
     *
     * _Available since v3.4._
     */
    function tryMul(uint256 a, uint256 b) internal pure returns (bool, uint256) {
        unchecked {
            // Gas optimization: this is cheaper than requiring 'a' not being zero, but the
            // benefit is lost if 'b' is also tested.
            // See: https://github.com/OpenZeppelin/openzeppelin-contracts/pull/522
            if (a == 0) return (true, 0);
            uint256 c = a * b;
            if (c / a != b) return (false, 0);
            return (true, c);
        }
    }

    /**
     * @dev Returns the division of two unsigned integers, with a division by zero flag.
     *
     * _Available since v3.4._
     */
    function tryDiv(uint256 a, uint256 b) internal pure returns (bool, uint256) {
        unchecked {
            if (b == 0) return (false, 0);
            return (true, a / b);
        }
    }

    /**
     * @dev Returns the remainder of dividing two unsigned integers, with a division by zero flag.
     *
     * _Available since v3.4._
     */
    function tryMod(uint256 a, uint256 b) internal pure returns (bool, uint256) {
        unchecked {
            if (b == 0) return (false, 0);
            return (true, a % b);
        }
    }

    /**
     * @dev Returns the addition of two unsigned integers, reverting on
     * overflow.
     *
     * Counterpart to Solidity's `+` operator.
     *
     * Requirements:
     *
     * - Addition cannot overflow.
     */
    function add(uint256 a, uint256 b) internal pure returns (uint256) {
        return a + b;
    }

    /**
     * @dev Returns the subtraction of two unsigned integers, reverting on
     * overflow (when the result is negative).
     *
     * Counterpart to Solidity's `-` operator.
     *
     * Requirements:
     *
     * - Subtraction cannot overflow.
     */
    function sub(uint256 a, uint256 b) internal pure returns (uint256) {
        return a - b;
    }

    /**
     * @dev Returns the multiplication of two unsigned integers, reverting on
     * overflow.
     *
     * Counterpart to Solidity's `*` operator.
     *
     * Requirements:
     *
     * - Multiplication cannot overflow.
     */
    function mul(uint256 a, uint256 b) internal pure returns (uint256) {
        return a * b;
    }

    /**
     * @dev Returns the integer division of two unsigned integers, reverting on
     * division by zero. The result is rounded towards zero.
     *
     * Counterpart to Solidity's `/` operator.
     *
     * Requirements:
     *
     * - The divisor cannot be zero.
     */
    function div(uint256 a, uint256 b) internal pure returns (uint256) {
        return a / b;
    }

    /**
     * @dev Returns the remainder of dividing two unsigned integers. (unsigned integer modulo),
     * reverting when dividing by zero.
     *
     * Counterpart to Solidity's `%` operator. This function uses a `revert`
     * opcode (which leaves remaining gas untouched) while Solidity uses an
     * invalid opcode to revert (consuming all remaining gas).
     *
     * Requirements:
     *
     * - The divisor cannot be zero.
     */
    function mod(uint256 a, uint256 b) internal pure returns (uint256) {
        return a % b;
    }

    /**
     * @dev Returns the subtraction of two unsigned integers, reverting with custom message on
     * overflow (when the result is negative).
     *
     * CAUTION: This function is deprecated because it requires allocating memory for the error
     * message unnecessarily. For custom revert reasons use {trySub}.
     *
     * Counterpart to Solidity's `-` operator.
     *
     * Requirements:
     *
     * - Subtraction cannot overflow.
     */
    function sub(uint256 a, uint256 b, string memory errorMessage) internal pure returns (uint256) {
        unchecked {
            require(b <= a, errorMessage);
            return a - b;
        }
    }

    /**
     * @dev Returns the integer division of two unsigned integers, reverting with custom message on
     * division by zero. The result is rounded towards zero.
     *
     * Counterpart to Solidity's `/` operator. Note: this function uses a
     * `revert` opcode (which leaves remaining gas untouched) while Solidity
     * uses an invalid opcode to revert (consuming all remaining gas).
     *
     * Requirements:
     *
     * - The divisor cannot be zero.
     */
    function div(uint256 a, uint256 b, string memory errorMessage) internal pure returns (uint256) {
        unchecked {
            require(b > 0, errorMessage);
            return a / b;
        }
    }

    /**
     * @dev Returns the remainder of dividing two unsigned integers. (unsigned integer modulo),
     * reverting with custom message when dividing by zero.
     *
     * CAUTION: This function is deprecated because it requires allocating memory for the error
     * message unnecessarily. For custom revert reasons use {tryMod}.
     *
     * Counterpart to Solidity's `%` operator. This function uses a `revert`
     * opcode (which leaves remaining gas untouched) while Solidity uses an
     * invalid opcode to revert (consuming all remaining gas).
     *
     * Requirements:
     *
     * - The divisor cannot be zero.
     */
    function mod(uint256 a, uint256 b, string memory errorMessage) internal pure returns (uint256) {
        unchecked {
            require(b > 0, errorMessage);
            return a % b;
        }
    }
}


// File contracts/crossApproach/lib/HTLCTxLib.sol

// Original license: SPDX_License_Identifier: MIT

/*

  Copyright 2023 Wanchain Foundation.

  Licensed under the Apache License, Version 2.0 (the "License");
  you may not use this file except in compliance with the License.
  You may obtain a copy of the License at

  http://www.apache.org/licenses/LICENSE-2.0

  Unless required by applicable law or agreed to in writing, software
  distributed under the License is distributed on an "AS IS" BASIS,
  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
  See the License for the specific language governing permissions and
  limitations under the License.

*/

//                            _           _           _
//  __      ____ _ _ __   ___| |__   __ _(_)_ __   __| | _____   __
//  \ \ /\ / / _` | '_ \ / __| '_ \ / _` | | '_ \@/ _` |/ _ \ \ / /
//   \ V  V / (_| | | | | (__| | | | (_| | | | | | (_| |  __/\ V /
//    \_/\_/ \__,_|_| |_|\___|_| |_|\__,_|_|_| |_|\__,_|\___| \_/
//
//

pragma solidity ^0.8.18;

library HTLCTxLib {
    using SafeMath for uint;

    /**
     *
     * ENUMS
     *
     */

    /// @notice tx info status
    /// @notice uninitialized,locked,redeemed,revoked
    enum TxStatus {None, Locked, Redeemed, Revoked, AssetLocked, DebtLocked}

    /**
     *
     * STRUCTURES
     *
     */

    /// @notice struct of HTLC user mint lock parameters
    struct HTLCUserParams {
        bytes32 xHash;                  /// hash of HTLC random number
        bytes32 smgID;                  /// ID of storeman group which user has selected
        uint tokenPairID;               /// token pair id on cross chain
        uint value;                     /// exchange token value
        uint lockFee;                   /// exchange token value
        uint lockedTime;                /// HTLC lock time
    }

    /// @notice HTLC(Hashed TimeLock Contract) tx info
    struct BaseTx {
        bytes32 smgID;                  /// HTLC transaction storeman ID
        uint lockedTime;                /// HTLC transaction locked time
        uint beginLockedTime;           /// HTLC transaction begin locked time
        TxStatus status;                /// HTLC transaction status
    }

    /// @notice user  tx info
    struct UserTx {
        BaseTx baseTx;
        uint tokenPairID;
        uint value;
        uint fee;
        address userAccount;            /// HTLC transaction sender address for the security check while user's revoke
    }
    /// @notice storeman  tx info
    struct SmgTx {
        BaseTx baseTx;
        uint tokenPairID;
        uint value;
        address  userAccount;          /// HTLC transaction user address for the security check while user's redeem
    }
    /// @notice storeman  debt tx info
    struct DebtTx {
        BaseTx baseTx;
        bytes32 srcSmgID;              /// HTLC transaction sender(source storeman) ID
    }

    struct Data {
        /// @notice mapping of hash(x) to UserTx -- xHash->htlcUserTxData
        mapping(bytes32 => UserTx) mapHashXUserTxs;

        /// @notice mapping of hash(x) to SmgTx -- xHash->htlcSmgTxData
        mapping(bytes32 => SmgTx) mapHashXSmgTxs;

        /// @notice mapping of hash(x) to DebtTx -- xHash->htlcDebtTxData
        mapping(bytes32 => DebtTx) mapHashXDebtTxs;

    }

    /**
     *
     * MANIPULATIONS
     *
     */

    /// @notice                     add user transaction info
    /// @param params               parameters for user tx
    function addUserTx(Data storage self, HTLCUserParams memory params)
        public
    {
        UserTx memory userTx = self.mapHashXUserTxs[params.xHash];
        // UserTx storage userTx = self.mapHashXUserTxs[params.xHash];
        // require(params.value != 0, "Value is invalid");
        require(userTx.baseTx.status == TxStatus.None, "User tx exists");

        userTx.baseTx.smgID = params.smgID;
        userTx.baseTx.lockedTime = params.lockedTime;
        userTx.baseTx.beginLockedTime = block.timestamp;
        userTx.baseTx.status = TxStatus.Locked;
        userTx.tokenPairID = params.tokenPairID;
        userTx.value = params.value;
        userTx.fee = params.lockFee;
        userTx.userAccount = msg.sender;

        self.mapHashXUserTxs[params.xHash] = userTx;
    }

    /// @notice                     refund coins from HTLC transaction, which is used for storeman redeem(outbound)
    /// @param x                    HTLC random number
    function redeemUserTx(Data storage self, bytes32 x)
        external
        returns(bytes32 xHash)
    {
        xHash = sha256(abi.encodePacked(x));

        UserTx storage userTx = self.mapHashXUserTxs[xHash];
        require(userTx.baseTx.status == TxStatus.Locked, "Status is not locked");
        require(block.timestamp < userTx.baseTx.beginLockedTime.add(userTx.baseTx.lockedTime), "Redeem timeout");

        userTx.baseTx.status = TxStatus.Redeemed;

        return xHash;
    }

    /// @notice                     revoke user transaction
    /// @param  xHash               hash of HTLC random number
    function revokeUserTx(Data storage self, bytes32 xHash)
        external
    {
        UserTx storage userTx = self.mapHashXUserTxs[xHash];
        require(userTx.baseTx.status == TxStatus.Locked, "Status is not locked");
        require(block.timestamp >= userTx.baseTx.beginLockedTime.add(userTx.baseTx.lockedTime), "Revoke is not permitted");

        userTx.baseTx.status = TxStatus.Revoked;
    }

    /// @notice                    function for get user info
    /// @param xHash               hash of HTLC random number
    /// @return smgID              ID of storeman which user has selected
    /// @return tokenPairID        token pair ID of cross chain
    /// @return value              exchange value
    /// @return fee                exchange fee
    /// @return userAccount        HTLC transaction sender address for the security check while user's revoke
    function getUserTx(Data storage self, bytes32 xHash)
        external
        view
        returns (bytes32, uint, uint, uint, address)
    {
        UserTx storage userTx = self.mapHashXUserTxs[xHash];
        return (userTx.baseTx.smgID, userTx.tokenPairID, userTx.value, userTx.fee, userTx.userAccount);
    }

    /// @notice                     add storeman transaction info
    /// @param  xHash               hash of HTLC random number
    /// @param  smgID               ID of the storeman which user has selected
    /// @param  tokenPairID         token pair ID of cross chain
    /// @param  value               HTLC transfer value of token
    /// @param  userAccount            user account address on the destination chain, which is used to redeem token
    function addSmgTx(Data storage self, bytes32 xHash, bytes32 smgID, uint tokenPairID, uint value, address userAccount, uint lockedTime)
        external
    {
        SmgTx memory smgTx = self.mapHashXSmgTxs[xHash];
        // SmgTx storage smgTx = self.mapHashXSmgTxs[xHash];
        require(value != 0, "Value is invalid");
        require(smgTx.baseTx.status == TxStatus.None, "Smg tx exists");

        smgTx.baseTx.smgID = smgID;
        smgTx.baseTx.status = TxStatus.Locked;
        smgTx.baseTx.lockedTime = lockedTime;
        smgTx.baseTx.beginLockedTime = block.timestamp;
        smgTx.tokenPairID = tokenPairID;
        smgTx.value = value;
        smgTx.userAccount = userAccount;

        self.mapHashXSmgTxs[xHash] = smgTx;
    }

    /// @notice                     refund coins from HTLC transaction, which is used for users redeem(inbound)
    /// @param x                    HTLC random number
    function redeemSmgTx(Data storage self, bytes32 x)
        external
        returns(bytes32 xHash)
    {
        xHash = sha256(abi.encodePacked(x));

        SmgTx storage smgTx = self.mapHashXSmgTxs[xHash];
        require(smgTx.baseTx.status == TxStatus.Locked, "Status is not locked");
        require(block.timestamp < smgTx.baseTx.beginLockedTime.add(smgTx.baseTx.lockedTime), "Redeem timeout");

        smgTx.baseTx.status = TxStatus.Redeemed;

        return xHash;
    }

    /// @notice                     revoke storeman transaction
    /// @param  xHash               hash of HTLC random number
    function revokeSmgTx(Data storage self, bytes32 xHash)
        external
    {
        SmgTx storage smgTx = self.mapHashXSmgTxs[xHash];
        require(smgTx.baseTx.status == TxStatus.Locked, "Status is not locked");
        require(block.timestamp >= smgTx.baseTx.beginLockedTime.add(smgTx.baseTx.lockedTime), "Revoke is not permitted");

        smgTx.baseTx.status = TxStatus.Revoked;
    }

    /// @notice                     function for get smg info
    /// @param xHash                hash of HTLC random number
    /// @return smgID               ID of storeman which user has selected
    /// @return tokenPairID         token pair ID of cross chain
    /// @return value               exchange value
    /// @return userAccount            user account address for redeem
    function getSmgTx(Data storage self, bytes32 xHash)
        external
        view
        returns (bytes32, uint, uint, address)
    {
        SmgTx storage smgTx = self.mapHashXSmgTxs[xHash];
        return (smgTx.baseTx.smgID, smgTx.tokenPairID, smgTx.value, smgTx.userAccount);
    }

    /// @notice                     add storeman transaction info
    /// @param  xHash               hash of HTLC random number
    /// @param  srcSmgID            ID of source storeman group
    /// @param  destSmgID           ID of the storeman which will take over of the debt of source storeman group
    /// @param  lockedTime          HTLC lock time
    /// @param  status              Status, should be 'Locked' for asset or 'DebtLocked' for debt
    function addDebtTx(Data storage self, bytes32 xHash, bytes32 srcSmgID, bytes32 destSmgID, uint lockedTime, TxStatus status)
        external
    {
        DebtTx memory debtTx = self.mapHashXDebtTxs[xHash];
        // DebtTx storage debtTx = self.mapHashXDebtTxs[xHash];
        require(debtTx.baseTx.status == TxStatus.None, "Debt tx exists");

        debtTx.baseTx.smgID = destSmgID;
        debtTx.baseTx.status = status;//TxStatus.Locked;
        debtTx.baseTx.lockedTime = lockedTime;
        debtTx.baseTx.beginLockedTime = block.timestamp;
        debtTx.srcSmgID = srcSmgID;

        self.mapHashXDebtTxs[xHash] = debtTx;
    }

    /// @notice                     refund coins from HTLC transaction
    /// @param x                    HTLC random number
    /// @param status               Status, should be 'Locked' for asset or 'DebtLocked' for debt
    function redeemDebtTx(Data storage self, bytes32 x, TxStatus status)
        external
        returns(bytes32 xHash)
    {
        xHash = sha256(abi.encodePacked(x));

        DebtTx storage debtTx = self.mapHashXDebtTxs[xHash];
        // require(debtTx.baseTx.status == TxStatus.Locked, "Status is not locked");
        require(debtTx.baseTx.status == status, "Status is not locked");
        require(block.timestamp < debtTx.baseTx.beginLockedTime.add(debtTx.baseTx.lockedTime), "Redeem timeout");

        debtTx.baseTx.status = TxStatus.Redeemed;

        return xHash;
    }

    /// @notice                     revoke debt transaction, which is used for source storeman group
    /// @param  xHash               hash of HTLC random number
    /// @param  status              Status, should be 'Locked' for asset or 'DebtLocked' for debt
    function revokeDebtTx(Data storage self, bytes32 xHash, TxStatus status)
        external
    {
        DebtTx storage debtTx = self.mapHashXDebtTxs[xHash];
        // require(debtTx.baseTx.status == TxStatus.Locked, "Status is not locked");
        require(debtTx.baseTx.status == status, "Status is not locked");
        require(block.timestamp >= debtTx.baseTx.beginLockedTime.add(debtTx.baseTx.lockedTime), "Revoke is not permitted");

        debtTx.baseTx.status = TxStatus.Revoked;
    }

    /// @notice                     function for get debt info
    /// @param xHash                hash of HTLC random number
    /// @return srcSmgID            ID of source storeman
    /// @return destSmgID           ID of destination storeman
    function getDebtTx(Data storage self, bytes32 xHash)
        external
        view
        returns (bytes32, bytes32)
    {
        DebtTx storage debtTx = self.mapHashXDebtTxs[xHash];
        return (debtTx.srcSmgID, debtTx.baseTx.smgID);
    }

    function getLeftTime(uint endTime) private view returns (uint) {
        if (block.timestamp < endTime) {
            return endTime.sub(block.timestamp);
        }
        return 0;
    }

    /// @notice                     function for get debt info
    /// @param xHash                hash of HTLC random number
    /// @return leftTime            the left lock time
    function getLeftLockedTime(Data storage self, bytes32 xHash)
        external
        view
        returns (uint leftTime)
    {
        UserTx storage userTx = self.mapHashXUserTxs[xHash];
        if (userTx.baseTx.status != TxStatus.None) {
            return getLeftTime(userTx.baseTx.beginLockedTime.add(userTx.baseTx.lockedTime));
        }
        SmgTx storage smgTx = self.mapHashXSmgTxs[xHash];
        if (smgTx.baseTx.status != TxStatus.None) {
            return getLeftTime(smgTx.baseTx.beginLockedTime.add(smgTx.baseTx.lockedTime));
        }
        DebtTx storage debtTx = self.mapHashXDebtTxs[xHash];
        if (debtTx.baseTx.status != TxStatus.None) {
            return getLeftTime(debtTx.baseTx.beginLockedTime.add(debtTx.baseTx.lockedTime));
        }
        require(false, 'invalid xHash');
    }
}


// File contracts/crossApproach/lib/RapidityTxLib.sol

// Original license: SPDX_License_Identifier: MIT

/*

  Copyright 2023 Wanchain Foundation.

  Licensed under the Apache License, Version 2.0 (the "License");
  you may not use this file except in compliance with the License.
  You may obtain a copy of the License at

  http://www.apache.org/licenses/LICENSE-2.0

  Unless required by applicable law or agreed to in writing, software
  distributed under the License is distributed on an "AS IS" BASIS,
  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
  See the License for the specific language governing permissions and
  limitations under the License.

*/

//                            _           _           _
//  __      ____ _ _ __   ___| |__   __ _(_)_ __   __| | _____   __
//  \ \ /\ / / _` | '_ \ / __| '_ \ / _` | | '_ \@/ _` |/ _ \ \ / /
//   \ V  V / (_| | | | | (__| | | | (_| | | | | | (_| |  __/\ V /
//    \_/\_/ \__,_|_| |_|\___|_| |_|\__,_|_|_| |_|\__,_|\___| \_/
//
//

pragma solidity ^0.8.18;

library RapidityTxLib {

    /**
     *
     * ENUMS
     *
     */

    /// @notice tx info status
    /// @notice uninitialized,Redeemed
    enum TxStatus {None, Redeemed}

    /**
     *
     * STRUCTURES
     *
     */
    struct Data {
        /// @notice mapping of uniqueID to TxStatus -- uniqueID->TxStatus
        mapping(bytes32 => TxStatus) mapTxStatus;

    }

    /**
     *
     * MANIPULATIONS
     *
     */

    /// @notice                     add user transaction info
    /// @param  uniqueID            Rapidity random number
    function addRapidityTx(Data storage self, bytes32 uniqueID)
        internal
    {
        TxStatus status = self.mapTxStatus[uniqueID];
        require(status == TxStatus.None, "Rapidity tx exists");
        self.mapTxStatus[uniqueID] = TxStatus.Redeemed;
    }
}


// File contracts/interfaces/IQuota.sol

// Original license: SPDX_License_Identifier: MIT

/*

  Copyright 2023 Wanchain Foundation.

  Licensed under the Apache License, Version 2.0 (the "License");
  you may not use this file except in compliance with the License.
  You may obtain a copy of the License at

  http://www.apache.org/licenses/LICENSE-2.0

  Unless required by applicable law or agreed to in writing, software
  distributed under the License is distributed on an "AS IS" BASIS,
  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
  See the License for the specific language governing permissions and
  limitations under the License.

*/

//                            _           _           _
//  __      ____ _ _ __   ___| |__   __ _(_)_ __   __| | _____   __
//  \ \ /\ / / _` | '_ \ / __| '_ \ / _` | | '_ \@/ _` |/ _ \ \ / /
//   \ V  V / (_| | | | | (__| | | | (_| | | | | | (_| |  __/\ V /
//    \_/\_/ \__,_|_| |_|\___|_| |_|\__,_|_|_| |_|\__,_|\___| \_/
//
//

pragma solidity ^0.8.18;

interface IQuota {
  function userLock(uint tokenId, bytes32 storemanGroupId, uint value) external;
  function userBurn(uint tokenId, bytes32 storemanGroupId, uint value) external;

  function smgRelease(uint tokenId, bytes32 storemanGroupId, uint value) external;
  function smgMint(uint tokenId, bytes32 storemanGroupId, uint value) external;

  function upgrade(bytes32 storemanGroupId) external;

  function transferAsset(bytes32 srcStoremanGroupId, bytes32 dstStoremanGroupId) external;
  function receiveDebt(bytes32 srcStoremanGroupId, bytes32 dstStoremanGroupId) external;

  function getUserMintQuota(uint tokenId, bytes32 storemanGroupId) external view returns (uint);
  function getSmgMintQuota(uint tokenId, bytes32 storemanGroupId) external view returns (uint);

  function getUserBurnQuota(uint tokenId, bytes32 storemanGroupId) external view returns (uint);
  function getSmgBurnQuota(uint tokenId, bytes32 storemanGroupId) external view returns (uint);

  function getAsset(uint tokenId, bytes32 storemanGroupId) external view returns (uint asset, uint asset_receivable, uint asset_payable);
  function getDebt(uint tokenId, bytes32 storemanGroupId) external view returns (uint debt, uint debt_receivable, uint debt_payable);

  function isDebtClean(bytes32 storemanGroupId) external view returns (bool);
}


// File contracts/interfaces/IRC20Protocol.sol

// Original license: SPDX_License_Identifier: MIT

/*

  Copyright 2023 Wanchain Foundation.

  Licensed under the Apache License, Version 2.0 (the "License");
  you may not use this file except in compliance with the License.
  You may obtain a copy of the License at

  http://www.apache.org/licenses/LICENSE-2.0

  Unless required by applicable law or agreed to in writing, software
  distributed under the License is distributed on an "AS IS" BASIS,
  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
  See the License for the specific language governing permissions and
  limitations under the License.

*/

//                            _           _           _
//  __      ____ _ _ __   ___| |__   __ _(_)_ __   __| | _____   __
//  \ \ /\ / / _` | '_ \ / __| '_ \ / _` | | '_ \@/ _` |/ _ \ \ / /
//   \ V  V / (_| | | | | (__| | | | (_| | | | | | (_| |  __/\ V /
//    \_/\_/ \__,_|_| |_|\___|_| |_|\__,_|_|_| |_|\__,_|\___| \_/
//
//

pragma solidity ^0.8.18;

interface IRC20Protocol {
    function transfer(address, uint) external returns (bool);
    function transferFrom(address, address, uint) external returns (bool);
    function balanceOf(address _owner) external view returns (uint);
}


// File contracts/interfaces/ISignatureVerifier.sol

// Original license: SPDX_License_Identifier: MIT

/*

  Copyright 2023 Wanchain Foundation.

  Licensed under the Apache License, Version 2.0 (the "License");
  you may not use this file except in compliance with the License.
  You may obtain a copy of the License at

  http://www.apache.org/licenses/LICENSE-2.0

  Unless required by applicable law or agreed to in writing, software
  distributed under the License is distributed on an "AS IS" BASIS,
  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
  See the License for the specific language governing permissions and
  limitations under the License.

*/

//                            _           _           _
//  __      ____ _ _ __   ___| |__   __ _(_)_ __   __| | _____   __
//  \ \ /\ / / _` | '_ \ / __| '_ \ / _` | | '_ \@/ _` |/ _ \ \ / /
//   \ V  V / (_| | | | | (__| | | | (_| | | | | | (_| |  __/\ V /
//    \_/\_/ \__,_|_| |_|\___|_| |_|\__,_|_|_| |_|\__,_|\___| \_/
//
//

pragma solidity ^0.8.18;

interface ISignatureVerifier {
  function verify(
        uint curveId,
        bytes32 signature,
        bytes32 groupKeyX,
        bytes32 groupKeyY,
        bytes32 randomPointX,
        bytes32 randomPointY,
        bytes32 message
    ) external returns (bool);
}


// File contracts/interfaces/IStoremanGroup.sol

// Original license: SPDX_License_Identifier: MIT

/*

  Copyright 2023 Wanchain Foundation.

  Licensed under the Apache License, Version 2.0 (the "License");
  you may not use this file except in compliance with the License.
  You may obtain a copy of the License at

  http://www.apache.org/licenses/LICENSE-2.0

  Unless required by applicable law or agreed to in writing, software
  distributed under the License is distributed on an "AS IS" BASIS,
  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
  See the License for the specific language governing permissions and
  limitations under the License.

*/

//                            _           _           _
//  __      ____ _ _ __   ___| |__   __ _(_)_ __   __| | _____   __
//  \ \ /\ / / _` | '_ \ / __| '_ \ / _` | | '_ \@/ _` |/ _ \ \ / /
//   \ V  V / (_| | | | | (__| | | | (_| | | | | | (_| |  __/\ V /
//    \_/\_/ \__,_|_| |_|\___|_| |_|\__,_|_|_| |_|\__,_|\___| \_/
//
//

pragma solidity ^0.8.18;

interface IStoremanGroup {
    function getSelectedSmNumber(bytes32 groupId) external view returns(uint number);
    function getStoremanGroupConfig(bytes32 id) external view returns(bytes32 groupId, uint8 status, uint deposit, uint chain1, uint chain2, uint curve1, uint curve2,  bytes memory gpk1, bytes memory gpk2, uint startTime, uint endTime);
    function getDeposit(bytes32 id) external view returns(uint);
    function getStoremanGroupStatus(bytes32 id) external view returns(uint8 status, uint startTime, uint endTime);
    function setGpk(bytes32 groupId, bytes memory gpk1, bytes memory gpk2) external;
    function setInvalidSm(bytes32 groupId, uint[] memory indexs, uint8[] memory slashTypes) external returns(bool isContinue);
    function getThresholdByGrpId(bytes32 groupId) external view returns (uint);
    function getSelectedSmInfo(bytes32 groupId, uint index) external view returns(address wkAddr, bytes memory PK, bytes memory enodeId);
    function recordSmSlash(address wk) external;
}


// File contracts/interfaces/ITokenManager.sol

// Original license: SPDX_License_Identifier: MIT

/*

  Copyright 2023 Wanchain Foundation.

  Licensed under the Apache License, Version 2.0 (the "License");
  you may not use this file except in compliance with the License.
  You may obtain a copy of the License at

  http://www.apache.org/licenses/LICENSE-2.0

  Unless required by applicable law or agreed to in writing, software
  distributed under the License is distributed on an "AS IS" BASIS,
  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
  See the License for the specific language governing permissions and
  limitations under the License.

*/

//                            _           _           _
//  __      ____ _ _ __   ___| |__   __ _(_)_ __   __| | _____   __
//  \ \ /\ / / _` | '_ \ / __| '_ \ / _` | | '_ \@/ _` |/ _ \ \ / /
//   \ V  V / (_| | | | | (__| | | | (_| | | | | | (_| |  __/\ V /
//    \_/\_/ \__,_|_| |_|\___|_| |_|\__,_|_|_| |_|\__,_|\___| \_/
//
//

pragma solidity ^0.8.18;

interface ITokenManager {
    function getTokenPairInfo(uint id) external view
      returns (uint origChainID, bytes memory tokenOrigAccount, uint shadowChainID, bytes memory tokenShadowAccount);

    function getTokenPairInfoSlim(uint id) external view
      returns (uint origChainID, bytes memory tokenOrigAccount, uint shadowChainID);

    function getAncestorInfo(uint id) external view
      returns (bytes memory account, string memory name, string memory symbol, uint8 decimals, uint chainId);

    function mintToken(address tokenAddress, address to, uint value) external;

    function burnToken(address tokenAddress, address from, uint value) external;

    function mapTokenPairType(uint tokenPairID) external view
      returns (uint8 tokenPairType);

    // erc1155
    function mintNFT(uint tokenCrossType, address tokenAddress, address to, uint[] calldata ids, uint[] calldata values, bytes calldata data) external;
    function burnNFT(uint tokenCrossType, address tokenAddress, address from, uint[] calldata ids, uint[] calldata values) external;
}


// File contracts/crossApproach/lib/CrossTypes.sol

// Original license: SPDX_License_Identifier: MIT

/*

  Copyright 2023 Wanchain Foundation.

  Licensed under the Apache License, Version 2.0 (the "License");
  you may not use this file except in compliance with the License.
  You may obtain a copy of the License at

  http://www.apache.org/licenses/LICENSE-2.0

  Unless required by applicable law or agreed to in writing, software
  distributed under the License is distributed on an "AS IS" BASIS,
  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
  See the License for the specific language governing permissions and
  limitations under the License.

*/

//                            _           _           _
//  __      ____ _ _ __   ___| |__   __ _(_)_ __   __| | _____   __
//  \ \ /\ / / _` | '_ \ / __| '_ \ / _` | | '_ \@/ _` |/ _ \ \ / /
//   \ V  V / (_| | | | | (__| | | | (_| | | | | | (_| |  __/\ V /
//    \_/\_/ \__,_|_| |_|\___|_| |_|\__,_|_|_| |_|\__,_|\___| \_/
//
//

pragma solidity ^0.8.18;







library CrossTypes {
    using SafeMath for uint;

    /**
     *
     * STRUCTURES
     *
     */

    struct Data {

        /// map of the htlc transaction info
        HTLCTxLib.Data htlcTxData;

        /// map of the rapidity transaction info
        RapidityTxLib.Data rapidityTxData;

        /// quota data of storeman group
        IQuota quota;

        /// token manager instance interface
        ITokenManager tokenManager;

        /// storemanGroup admin instance interface
        IStoremanGroup smgAdminProxy;

        /// storemanGroup fee admin instance address
        address smgFeeProxy;

        ISignatureVerifier sigVerifier;

        /// @notice transaction fee, smgID => fee
        mapping(bytes32 => uint) mapStoremanFee;

        /// @notice transaction fee, origChainID => shadowChainID => fee
        mapping(uint => mapping(uint =>uint)) mapContractFee;

        /// @notice transaction fee, origChainID => shadowChainID => fee
        mapping(uint => mapping(uint =>uint)) mapAgentFee;

    }

    /**
     *
     * MANIPULATIONS
     *
     */

    /// @notice       convert bytes to address
    /// @param b      bytes
    function bytesToAddress(bytes memory b) internal pure returns (address addr) {
        assembly {
            addr := mload(add(b,20))
        }
    }

    function transfer(address tokenScAddr, address to, uint value)
        internal
        returns(bool)
    {
        uint beforeBalance;
        uint afterBalance;
        IRC20Protocol token = IRC20Protocol(tokenScAddr);
        beforeBalance = token.balanceOf(to);
        (bool success,) = tokenScAddr.call(abi.encodeWithSelector(token.transfer.selector, to, value));
        require(success, "transfer failed");
        afterBalance = token.balanceOf(to);
        return afterBalance == beforeBalance.add(value);
    }

    function transferFrom(address tokenScAddr, address from, address to, uint value)
        internal
        returns(bool)
    {
        uint beforeBalance;
        uint afterBalance;
        IRC20Protocol token = IRC20Protocol(tokenScAddr);
        beforeBalance = token.balanceOf(to);
        (bool success,) = tokenScAddr.call(abi.encodeWithSelector(token.transferFrom.selector, from, to, value));
        require(success, "transferFrom failed");
        afterBalance = token.balanceOf(to);
        return afterBalance == beforeBalance.add(value);
    }
}


// File contracts/crossApproach/CrossStorage.sol

// Original license: SPDX_License_Identifier: MIT

/*

  Copyright 2023 Wanchain Foundation.

  Licensed under the Apache License, Version 2.0 (the "License");
  you may not use this file except in compliance with the License.
  You may obtain a copy of the License at

  http://www.apache.org/licenses/LICENSE-2.0

  Unless required by applicable law or agreed to in writing, software
  distributed under the License is distributed on an "AS IS" BASIS,
  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
  See the License for the specific language governing permissions and
  limitations under the License.

*/

//                            _           _           _
//  __      ____ _ _ __   ___| |__   __ _(_)_ __   __| | _____   __
//  \ \ /\ / / _` | '_ \ / __| '_ \ / _` | | '_ \@/ _` |/ _ \ \ / /
//   \ V  V / (_| | | | | (__| | | | (_| | | | | | (_| |  __/\ V /
//    \_/\_/ \__,_|_| |_|\___|_| |_|\__,_|_|_| |_|\__,_|\___| \_/
//
//

pragma solidity ^0.8.18;




contract CrossStorage is BasicStorage {
    using HTLCTxLib for HTLCTxLib.Data;
    using RapidityTxLib for RapidityTxLib.Data;

    /************************************************************
     **
     ** VARIABLES
     **
     ************************************************************/

    CrossTypes.Data internal storageData;

    /// @notice locked time(in seconds)
    uint public lockedTime = uint(3600*36);

    /// @notice Since storeman group admin receiver address may be changed, system should make sure the new address
    /// @notice can be used, and the old address can not be used. The solution is add timestamp.
    /// @notice unit: second
    uint public smgFeeReceiverTimeout = uint(10*60);

    enum GroupStatus { none, initial, curveSeted, failed, selected, ready, unregistered, dismissed }

}


// File contracts/crossApproach/CrossStorageV2.sol

// Original license: SPDX_License_Identifier: MIT

/*

  Copyright 2023 Wanchain Foundation.

  Licensed under the Apache License, Version 2.0 (the "License");
  you may not use this file except in compliance with the License.
  You may obtain a copy of the License at

  http://www.apache.org/licenses/LICENSE-2.0

  Unless required by applicable law or agreed to in writing, software
  distributed under the License is distributed on an "AS IS" BASIS,
  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
  See the License for the specific language governing permissions and
  limitations under the License.

*/

//                            _           _           _
//  __      ____ _ _ __   ___| |__   __ _(_)_ __   __| | _____   __
//  \ \ /\ / / _` | '_ \ / __| '_ \ / _` | | '_ \@/ _` |/ _ \ \ / /
//   \ V  V / (_| | | | | (__| | | | (_| | | | | | (_| |  __/\ V /
//    \_/\_/ \__,_|_| |_|\___|_| |_|\__,_|_|_| |_|\__,_|\___| \_/
//
//

pragma solidity ^0.8.18;




contract CrossStorageV2 is CrossStorage, ReentrancyGuard, Halt, Proxy {

    /************************************************************
     **
     ** VARIABLES
     **
     ************************************************************/

    /** STATE VARIABLES **/
    uint256 public currentChainID;
    address public admin;

    /** STRUCTURES **/
    struct SetFeesParam {
        uint256 srcChainID;
        uint256 destChainID;
        uint256 contractFee;
        uint256 agentFee;
    }

    struct GetFeesParam {
        uint256 srcChainID;
        uint256 destChainID;
    }

    struct GetFeesReturn {
        uint256 contractFee;
        uint256 agentFee;
    }
}


// File contracts/crossApproach/CrossStorageV3.sol

// Original license: SPDX_License_Identifier: MIT

/*

  Copyright 2023 Wanchain Foundation.

  Licensed under the Apache License, Version 2.0 (the "License");
  you may not use this file except in compliance with the License.
  You may obtain a copy of the License at

  http://www.apache.org/licenses/LICENSE-2.0

  Unless required by applicable law or agreed to in writing, software
  distributed under the License is distributed on an "AS IS" BASIS,
  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
  See the License for the specific language governing permissions and
  limitations under the License.

*/

//                            _           _           _
//  __      ____ _ _ __   ___| |__   __ _(_)_ __   __| | _____   __
//  \ \ /\ / / _` | '_ \ / __| '_ \ / _` | | '_ \@/ _` |/ _ \ \ / /
//   \ V  V / (_| | | | | (__| | | | (_| | | | | | (_| |  __/\ V /
//    \_/\_/ \__,_|_| |_|\___|_| |_|\__,_|_|_| |_|\__,_|\___| \_/
//
//

pragma solidity ^0.8.18;

contract CrossStorageV3 is CrossStorageV2 {

    /************************************************************
     **
     ** VARIABLES
     **
     ************************************************************/

    /** STATE VARIABLES **/
    // tokenPairID => fee
    mapping(uint256 => uint256) mapTokenPairContractFee;

    struct SetTokenPairFeesParam {
        uint256 tokenPairID;
        uint256 contractFee;
    }

}


// File contracts/crossApproach/CrossStorageV4.sol

// Original license: SPDX_License_Identifier: MIT

/*

  Copyright 2023 Wanchain Foundation.

  Licensed under the Apache License, Version 2.0 (the "License");
  you may not use this file except in compliance with the License.
  You may obtain a copy of the License at

  http://www.apache.org/licenses/LICENSE-2.0

  Unless required by applicable law or agreed to in writing, software
  distributed under the License is distributed on an "AS IS" BASIS,
  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
  See the License for the specific language governing permissions and
  limitations under the License.

*/

//                            _           _           _
//  __      ____ _ _ __   ___| |__   __ _(_)_ __   __| | _____   __
//  \ \ /\ / / _` | '_ \ / __| '_ \ / _` | | '_ \@/ _` |/ _ \ \ / /
//   \ V  V / (_| | | | | (__| | | | (_| | | | | | (_| |  __/\ V /
//    \_/\_/ \__,_|_| |_|\___|_| |_|\__,_|_|_| |_|\__,_|\___| \_/
//
//

pragma solidity ^0.8.18;

contract CrossStorageV4 is CrossStorageV3 {

    /************************************************************
     **
     ** VARIABLES
     **
     ************************************************************/
    uint internal maxBatchSize;
    uint internal etherTransferGasLimit;
    uint public hashType; // 0: sha256, 1: keccak256
    mapping(address => bool) public isAdmin;
    mapping(address => bool) public isOperator;
}


// File contracts/crossApproach/lib/EtherTransfer.sol

// Original license: SPDX_License_Identifier: MIT

pragma solidity ^0.8.1;

library EtherTransfer {
    /**
     * @dev Replacement for Solidity's `transfer`: sends `amount` wei to
     * `recipient`, forwarding all available gas and reverting on errors.
     *
     * https://eips.ethereum.org/EIPS/eip-1884[EIP1884] increases the gas cost
     * of certain opcodes, possibly making contracts go over the 2300 gas limit
     * imposed by `transfer`, making them unable to receive funds via
     * `transfer`. {sendValue} removes this limitation.
     *
     * https://consensys.net/diligence/blog/2023/09/stop-using-soliditys-transfer-now/[Learn more].
     *
     * IMPORTANT: because control is transferred to `recipient`, care must be
     * taken to not create reentrancy vulnerabilities. Consider using
     * {ReentrancyGuard} or the
     * https://solidity.readthedocs.io/en/v0.8.0/security-considerations.html#use-the-checks-effects-interactions-pattern[checks-effects-interactions pattern].
     */
    function sendValue(address payable recipient, uint256 amount, uint256 gasLimit) internal {
        require(address(this).balance >= amount, "EtherTransfer: insufficient balance");

        (bool success, ) = recipient.call{value: amount, gas: gasLimit}("");
        require(success, "EtherTransfer: unable to send value, recipient may have reverted");
    }
}


// File contracts/crossApproach/lib/NFTLibV1.sol

// Original license: SPDX_License_Identifier: MIT

/*

  Copyright 2023 Wanchain Foundation.

  Licensed under the Apache License, Version 2.0 (the "License");
  you may not use this file except in compliance with the License.
  You may obtain a copy of the License at

  http://www.apache.org/licenses/LICENSE-2.0

  Unless required by applicable law or agreed to in writing, software
  distributed under the License is distributed on an "AS IS" BASIS,
  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
  See the License for the specific language governing permissions and
  limitations under the License.

*/

//                            _           _           _
//  __      ____ _ _ __   ___| |__   __ _(_)_ __   __| | _____   __
//  \ \ /\ / / _` | '_ \ / __| '_ \ / _` | | '_ \@/ _` |/ _ \ \ / /
//   \ V  V / (_| | | | | (__| | | | (_| | | | | | (_| |  __/\ V /
//    \_/\_/ \__,_|_| |_|\___|_| |_|\__,_|_|_| |_|\__,_|\___| \_/
//
//

pragma solidity ^0.8.18;






library NFTLibV1 {
    using SafeMath for uint;
    using RapidityTxLib for RapidityTxLib.Data;

    enum TokenCrossType {ERC20, ERC721, ERC1155}

    /// @notice struct of Rapidity storeman mint lock parameters
    struct RapidityUserLockNFTParams {
        bytes32                 smgID;                  /// ID of storeman group which user has selected
        uint                    tokenPairID;            /// token pair id on cross chain
        uint[]                  tokenIDs;               /// NFT token Ids
        uint[]                  tokenValues;            /// NFT token values
        uint                    currentChainID;         /// current chain ID
        uint                    tokenPairContractFee;   /// fee of token pair
        uint                    etherTransferGasLimit;  /// exchange token fee
        bytes                   destUserAccount;        /// account of shadow chain, used to receive token
        address                 smgFeeProxy;            /// address of the proxy to store fee for storeman group
    }

    /// @notice struct of Rapidity storeman mint lock parameters
    struct RapiditySmgMintNFTParams {
        bytes32                 uniqueID;               /// Rapidity random number
        bytes32                 smgID;                  /// ID of storeman group which user has selected
        uint                    tokenPairID;            /// token pair id on cross chain
        uint[]                  tokenIDs;               /// NFT token Ids
        uint[]                  tokenValues;            /// NFT token values
        bytes                   extData;                /// storeman data
        address                 destTokenAccount;       /// shadow token account
        address                 destUserAccount;        /// account of shadow chain, used to receive token
    }

    /// @notice struct of Rapidity user burn lock parameters
    struct RapidityUserBurnNFTParams {
        bytes32                 smgID;                  /// ID of storeman group which user has selected
        uint                    tokenPairID;            /// token pair id on cross chain
        uint[]                  tokenIDs;               /// NFT token Ids
        uint[]                  tokenValues;            /// NFT token values
        uint                    currentChainID;         /// current chain ID
        uint                    tokenPairContractFee;   /// fee of token pair
        uint                    etherTransferGasLimit;  /// exchange token fee
        address                 srcTokenAccount;        /// shadow token account
        bytes                   destUserAccount;        /// account of token destination chain, used to receive token
        address                 smgFeeProxy;            /// address of the proxy to store fee for storeman group
    }

    /// @notice struct of Rapidity user burn lock parameters
    struct RapiditySmgReleaseNFTParams {
        bytes32                 uniqueID;               /// Rapidity random number
        bytes32                 smgID;                  /// ID of storeman group which user has selected
        uint                    tokenPairID;            /// token pair id on cross chain
        uint[]                  tokenIDs;               /// NFT token Ids
        uint[]                  tokenValues;            /// NFT token values
        address                 destTokenAccount;       /// original token/coin account
        address                 destUserAccount;        /// account of token original chain, used to receive token
    }

    event UserLockNFT(bytes32 indexed smgID, uint indexed tokenPairID, address indexed tokenAccount, string[] keys, bytes[] values);

    event UserBurnNFT(bytes32 indexed smgID, uint indexed tokenPairID, address indexed tokenAccount, string[] keys, bytes[] values);

    event SmgMintNFT(bytes32 indexed uniqueID, bytes32 indexed smgID, uint indexed tokenPairID, string[] keys, bytes[] values);

    event SmgReleaseNFT(bytes32 indexed uniqueID, bytes32 indexed smgID, uint indexed tokenPairID, string[] keys, bytes[] values);

    function getTokenScAddrAndContractFee(CrossTypes.Data storage storageData, uint tokenPairID, uint tokenPairContractFee, uint currentChainID, uint batchLength)
        public
        view
        returns (address, uint)
    {
        ITokenManager tokenManager = storageData.tokenManager;
        uint fromChainID;
        uint toChainID;
        bytes memory fromTokenAccount;
        bytes memory toTokenAccount;
        (fromChainID,fromTokenAccount,toChainID,toTokenAccount) = tokenManager.getTokenPairInfo(tokenPairID);
        require(fromChainID != 0, "Token does not exist");

        uint contractFee = tokenPairContractFee;
        address tokenScAddr;
        if (currentChainID == fromChainID) {
            if (contractFee == 0) {
                contractFee = storageData.mapContractFee[fromChainID][toChainID];
            }
            if (contractFee == 0) {
                contractFee = storageData.mapContractFee[fromChainID][0];
            }
            tokenScAddr = CrossTypes.bytesToAddress(fromTokenAccount);
        } else if (currentChainID == toChainID) {
            if (contractFee == 0) {
                contractFee = storageData.mapContractFee[toChainID][fromChainID];
            }
            if (contractFee == 0) {
                contractFee = storageData.mapContractFee[toChainID][0];
            }
            tokenScAddr = CrossTypes.bytesToAddress(toTokenAccount);
        } else {
            require(false, "Invalid token pair");
        }
        if (contractFee > 0) {
            contractFee = contractFee.mul(9 + batchLength).div(10);
        }
        return (tokenScAddr, contractFee);
    }

    /// @notice                         mintBridge, user lock token on token original chain
    /// @notice                         event invoked by user mint lock
    /// @param storageData              Cross storage data
    /// @param params                   parameters for user mint lock token on token original chain
    function userLockNFT(CrossTypes.Data storage storageData, RapidityUserLockNFTParams memory params)
        public
    {
        address tokenScAddr;
        uint contractFee;
        (tokenScAddr, contractFee) = getTokenScAddrAndContractFee(storageData, params.tokenPairID, params.tokenPairContractFee, params.currentChainID, params.tokenIDs.length);

        if (contractFee > 0) {
            EtherTransfer.sendValue(payable(params.smgFeeProxy), contractFee, params.etherTransferGasLimit);
        }

        uint left = (msg.value).sub(contractFee);

        uint8 tokenCrossType = storageData.tokenManager.mapTokenPairType(params.tokenPairID);
        if (tokenCrossType == uint8(TokenCrossType.ERC721)) {
            for(uint idx = 0; idx < params.tokenIDs.length; ++idx) {
                IERC721(tokenScAddr).safeTransferFrom(msg.sender, address(this), params.tokenIDs[idx], "");
            }
        } else if(tokenCrossType == uint8(TokenCrossType.ERC1155)) {
            IERC1155(tokenScAddr).safeBatchTransferFrom(msg.sender, address(this), params.tokenIDs, params.tokenValues, "");
        }
        else{
            require(false, "Invalid NFT type");
        }

        if (left != 0) {
            EtherTransfer.sendValue(payable(msg.sender), left, params.etherTransferGasLimit);
        }

        string[] memory keys = new string[](4);
        bytes[] memory values = new bytes[](4);

        keys[0] = "tokenIDs:uint256[]";
        values[0] = abi.encode(params.tokenIDs);

        keys[1] = "tokenValues:uint256[]";
        values[1] = abi.encode(params.tokenValues);

        keys[2] = "userAccount:bytes";
        values[2] = params.destUserAccount;

        keys[3] = "contractFee:uint256";
        values[3] = abi.encodePacked(contractFee);

        emit UserLockNFT(params.smgID, params.tokenPairID, tokenScAddr, keys, values);
    }

    /// @notice                         burnBridge, user lock token on token original chain
    /// @notice                         event invoked by user burn lock
    /// @param storageData              Cross storage data
    /// @param params                   parameters for user burn lock token on token original chain
    function userBurnNFT(CrossTypes.Data storage storageData, RapidityUserBurnNFTParams memory params)
        public
    {
        address tokenScAddr;
        uint contractFee;
        (tokenScAddr, contractFee) = getTokenScAddrAndContractFee(storageData, params.tokenPairID, params.tokenPairContractFee, params.currentChainID, params.tokenIDs.length);

        ITokenManager tokenManager = storageData.tokenManager;
        uint8 tokenCrossType = tokenManager.mapTokenPairType(params.tokenPairID);
        require((tokenCrossType == uint8(TokenCrossType.ERC721) || tokenCrossType == uint8(TokenCrossType.ERC1155)), "Invalid NFT type");
        ITokenManager(tokenManager).burnNFT(uint(tokenCrossType), tokenScAddr, msg.sender, params.tokenIDs, params.tokenValues);

        if (contractFee > 0) {
            EtherTransfer.sendValue(payable(params.smgFeeProxy), contractFee, params.etherTransferGasLimit);
        }

        uint left = (msg.value).sub(contractFee);
        if (left != 0) {
            EtherTransfer.sendValue(payable(msg.sender), left, params.etherTransferGasLimit);
        }

        string[] memory keys = new string[](4);
        bytes[] memory values = new bytes[](4);

        keys[0] = "tokenIDs:uint256[]";
        values[0] = abi.encode(params.tokenIDs);

        keys[1] = "tokenValues:uint256[]";
        values[1] = abi.encode(params.tokenValues);

        keys[2] = "userAccount:bytes";
        values[2] = params.destUserAccount;

        keys[3] = "contractFee:uint256";
        values[3] = abi.encodePacked(contractFee);
        emit UserBurnNFT(params.smgID, params.tokenPairID, tokenScAddr, keys, values);
    }

    /// @notice                         mintBridge, storeman mint lock token on token shadow chain
    /// @notice                         event invoked by user mint lock
    /// @param storageData              Cross storage data
    /// @param params                   parameters for storeman mint lock token on token shadow chain
    function smgMintNFT(CrossTypes.Data storage storageData, RapiditySmgMintNFTParams memory params)
        public
    {
        storageData.rapidityTxData.addRapidityTx(params.uniqueID);

        ITokenManager tokenManager = storageData.tokenManager;
        uint8 tokenCrossType = tokenManager.mapTokenPairType(params.tokenPairID);
        require((tokenCrossType == uint8(TokenCrossType.ERC721) || tokenCrossType == uint8(TokenCrossType.ERC1155)), "Invalid NFT type");
        ITokenManager(tokenManager).mintNFT(uint(tokenCrossType), params.destTokenAccount, params.destUserAccount, params.tokenIDs, params.tokenValues, params.extData);

        string[] memory keys = new string[](5);
        bytes[] memory values = new bytes[](5);

        keys[0] = "tokenIDs:uint256[]";
        values[0] = abi.encode(params.tokenIDs);

        keys[1] = "tokenValues:uint256[]";
        values[1] = abi.encode(params.tokenValues);

        keys[2] = "tokenAccount:address";
        values[2] = abi.encodePacked(params.destTokenAccount);

        keys[3] = "userAccount:address";
        values[3] = abi.encodePacked(params.destUserAccount);

        keys[4] = "extData:bytes";
        values[4] = params.extData;

        emit SmgMintNFT(params.uniqueID, params.smgID, params.tokenPairID, keys, values);
    }

    /// @notice                         burnBridge, storeman burn lock token on token shadow chain
    /// @notice                         event invoked by user burn lock
    /// @param storageData              Cross storage data
    /// @param params                   parameters for storeman burn lock token on token shadow chain
    function smgReleaseNFT(CrossTypes.Data storage storageData, RapiditySmgReleaseNFTParams memory params)
        public
    {
        storageData.rapidityTxData.addRapidityTx(params.uniqueID);

        uint8 tokenCrossType = storageData.tokenManager.mapTokenPairType(params.tokenPairID);
        if (tokenCrossType == uint8(TokenCrossType.ERC721)) {
            for(uint idx = 0; idx < params.tokenIDs.length; ++idx) {
                IERC721(params.destTokenAccount).safeTransferFrom(address(this), params.destUserAccount, params.tokenIDs[idx], "");
            }
        }
        else if(tokenCrossType == uint8(TokenCrossType.ERC1155)) {
            IERC1155(params.destTokenAccount).safeBatchTransferFrom(address(this), params.destUserAccount, params.tokenIDs, params.tokenValues, "");
        }
        else {
            require(false, "Invalid NFT type");
        }

        string[] memory keys = new string[](4);
        bytes[] memory values = new bytes[](4);

        keys[0] = "tokenIDs:uint256[]";
        values[0] = abi.encode(params.tokenIDs);

        keys[1] = "tokenValues:uint256[]";
        values[1] = abi.encode(params.tokenValues);

        keys[2] = "tokenAccount:address";
        values[2] = abi.encodePacked(params.destTokenAccount);

        keys[3] = "userAccount:address";
        values[3] = abi.encodePacked(params.destUserAccount);

        emit SmgReleaseNFT(params.uniqueID, params.smgID, params.tokenPairID, keys, values);
    }
}


// File contracts/crossApproach/lib/RapidityLibV4.sol

// Original license: SPDX_License_Identifier: MIT

/*

  Copyright 2023 Wanchain Foundation.

  Licensed under the Apache License, Version 2.0 (the "License");
  you may not use this file except in compliance with the License.
  You may obtain a copy of the License at

  http://www.apache.org/licenses/LICENSE-2.0

  Unless required by applicable law or agreed to in writing, software
  distributed under the License is distributed on an "AS IS" BASIS,
  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
  See the License for the specific language governing permissions and
  limitations under the License.

*/

//                            _           _           _
//  __      ____ _ _ __   ___| |__   __ _(_)_ __   __| | _____   __
//  \ \ /\ / / _` | '_ \ / __| '_ \ / _` | | '_ \@/ _` |/ _ \ \ / /
//   \ V  V / (_| | | | | (__| | | | (_| | | | | | (_| |  __/\ V /
//    \_/\_/ \__,_|_| |_|\___|_| |_|\__,_|_|_| |_|\__,_|\___| \_/
//
//

pragma solidity ^0.8.18;





library RapidityLibV4 {
    using SafeMath for uint;
    using RapidityTxLib for RapidityTxLib.Data;

    enum TokenCrossType {ERC20, ERC721, ERC1155}

    /**
    *
    * STRUCTURES
    *
    */

    /// @notice struct of Rapidity storeman mint lock parameters
    struct RapidityUserLockParams {
        bytes32 smgID;                    /// ID of storeman group which user has selected
        uint tokenPairID;                 /// token pair id on cross chain
        uint value;                       /// exchange token value
        uint currentChainID;              /// current chain ID
        uint tokenPairContractFee;        /// fee of token pair
        uint etherTransferGasLimit;     /// exchange token fee
        bytes destUserAccount;            /// account of shadow chain, used to receive token
        address smgFeeProxy;              /// address of the proxy to store fee for storeman group
    }

    /// @notice struct of Rapidity storeman mint lock parameters
    struct RapiditySmgMintParams {
        bytes32 uniqueID;                 /// Rapidity random number
        bytes32 smgID;                    /// ID of storeman group which user has selected
        uint tokenPairID;                 /// token pair id on cross chain
        uint value;                       /// exchange token value
        uint fee;                         /// exchange token fee
        address destTokenAccount;         /// shadow token account
        address destUserAccount;          /// account of shadow chain, used to receive token
        address smgFeeProxy;              /// address of the proxy to store fee for storeman group
    }

    /// @notice struct of Rapidity user burn lock parameters
    struct RapidityUserBurnParams {
        bytes32 smgID;                  /// ID of storeman group which user has selected
        uint tokenPairID;               /// token pair id on cross chain
        uint value;                     /// exchange token value
        uint currentChainID;            /// current chain ID
        uint fee;                       /// exchange token fee
        uint tokenPairContractFee;      /// fee of token pair
        uint etherTransferGasLimit;     /// exchange token fee
        address srcTokenAccount;        /// shadow token account
        bytes destUserAccount;          /// account of token destination chain, used to receive token
        address smgFeeProxy;            /// address of the proxy to store fee for storeman group
    }

    /// @notice struct of Rapidity user burn lock parameters
    struct RapiditySmgReleaseParams {
        bytes32 uniqueID;               /// Rapidity random number
        bytes32 smgID;                  /// ID of storeman group which user has selected
        uint tokenPairID;               /// token pair id on cross chain
        uint value;                     /// exchange token value
        uint fee;                       /// exchange token fee
        uint etherTransferGasLimit;     /// exchange token fee
        address destTokenAccount;       /// original token/coin account
        address destUserAccount;        /// account of token original chain, used to receive token
        address smgFeeProxy;            /// address of the proxy to store fee for storeman group
    }

    /**
     *
     * EVENTS
     *
     **/


    /// @notice                         event of exchange WRC-20 token with original chain token request
    /// @notice                         event invoked by storeman group
    /// @param smgID                    ID of storemanGroup
    /// @param tokenPairID              token pair ID of cross chain token
    /// @param tokenAccount             Rapidity original token account
    /// @param value                    Rapidity value
    /// @param userAccount              account of shadow chain, used to receive token
    event UserLockLogger(bytes32 indexed smgID, uint indexed tokenPairID, address indexed tokenAccount, uint value, uint contractFee, bytes userAccount);

    /// @notice                         event of exchange WRC-20 token with original chain token request
    /// @notice                         event invoked by storeman group
    /// @param smgID                    ID of storemanGroup
    /// @param tokenPairID              token pair ID of cross chain token
    /// @param tokenAccount             Rapidity shadow token account
    /// @param value                    Rapidity value
    /// @param userAccount              account of shadow chain, used to receive token
    event UserBurnLogger(bytes32 indexed smgID, uint indexed tokenPairID, address indexed tokenAccount, uint value, uint contractFee, uint fee, bytes userAccount);

    /// @notice                         event of exchange WRC-20 token with original chain token request
    /// @notice                         event invoked by storeman group
    /// @param uniqueID                 unique random number
    /// @param smgID                    ID of storemanGroup
    /// @param tokenPairID              token pair ID of cross chain token
    /// @param value                    Rapidity value
    /// @param tokenAccount             Rapidity shadow token account
    /// @param userAccount              account of original chain, used to receive token
    event SmgMintLogger(bytes32 indexed uniqueID, bytes32 indexed smgID, uint indexed tokenPairID, uint value, address tokenAccount, address userAccount);
    event SmgMint(bytes32 indexed uniqueID, bytes32 indexed smgID, uint indexed tokenPairID, string[] keys, bytes[] values);

    /// @notice                         event of exchange WRC-20 token with original chain token request
    /// @notice                         event invoked by storeman group
    /// @param uniqueID                 unique random number
    /// @param smgID                    ID of storemanGroup
    /// @param tokenPairID              token pair ID of cross chain token
    /// @param value                    Rapidity value
    /// @param tokenAccount             Rapidity original token account
    /// @param userAccount              account of original chain, used to receive token
    event SmgReleaseLogger(bytes32 indexed uniqueID, bytes32 indexed smgID, uint indexed tokenPairID, uint value, address tokenAccount, address userAccount);
    event SmgRelease(bytes32 indexed uniqueID, bytes32 indexed smgID, uint indexed tokenPairID, string[] keys, bytes[] values);

    /**
    *
    * MANIPULATIONS
    *
    */

    /// @notice                         mintBridge, user lock token on token original chain
    /// @notice                         event invoked by user mint lock
    /// @param storageData              Cross storage data
    /// @param params                   parameters for user mint lock token on token original chain
    function userLock(CrossTypes.Data storage storageData, RapidityUserLockParams memory params)
    public
    {
        ITokenManager tokenManager = storageData.tokenManager;
        uint fromChainID;
        uint toChainID;
        bytes memory fromTokenAccount;
        bytes memory toTokenAccount;
        (fromChainID,fromTokenAccount,toChainID,toTokenAccount) = tokenManager.getTokenPairInfo(params.tokenPairID);
        require(fromChainID != 0, "Token does not exist");

        uint contractFee = params.tokenPairContractFee;
        address tokenScAddr;
        if (params.currentChainID == fromChainID) {
            if (contractFee == 0) {
                contractFee = storageData.mapContractFee[fromChainID][toChainID];
            }
            if (contractFee == 0) {
                contractFee = storageData.mapContractFee[fromChainID][0];
            }
            tokenScAddr = CrossTypes.bytesToAddress(fromTokenAccount);
        } else if (params.currentChainID == toChainID) {
            if (contractFee == 0) {
                contractFee = storageData.mapContractFee[toChainID][fromChainID];
            }
            if (contractFee == 0) {
                contractFee = storageData.mapContractFee[toChainID][0];
            }
            tokenScAddr = CrossTypes.bytesToAddress(toTokenAccount);
        } else {
            require(false, "Invalid token pair");
        }
        if (contractFee > 0) {
            EtherTransfer.sendValue(payable(params.smgFeeProxy), contractFee, params.etherTransferGasLimit);
        }

        uint left;
        if (tokenScAddr == address(0)) {
            left = (msg.value).sub(params.value).sub(contractFee);
        } else {
            left = (msg.value).sub(contractFee);

            uint8 tokenCrossType = tokenManager.mapTokenPairType(params.tokenPairID);
            require(tokenCrossType == uint8(TokenCrossType.ERC20), "Not support");
            require(CrossTypes.transferFrom(tokenScAddr, msg.sender, address(this), params.value), "Lock token failed");
        }
        if (left != 0) {
            EtherTransfer.sendValue(payable(msg.sender), left, params.etherTransferGasLimit);
        }
        emit UserLockLogger(params.smgID, params.tokenPairID, tokenScAddr, params.value, contractFee, params.destUserAccount);
    }

    /// @notice                         burnBridge, user lock token on token original chain
    /// @notice                         event invoked by user burn lock
    /// @param storageData              Cross storage data
    /// @param params                   parameters for user burn lock token on token original chain
    function userBurn(CrossTypes.Data storage storageData, RapidityUserBurnParams memory params)
    public
    {
        ITokenManager tokenManager = storageData.tokenManager;
        uint fromChainID;
        uint toChainID;
        bytes memory fromTokenAccount;
        bytes memory toTokenAccount;
        (fromChainID,fromTokenAccount,toChainID,toTokenAccount) = tokenManager.getTokenPairInfo(params.tokenPairID);
        require(fromChainID != 0, "Token does not exist");

        uint256 contractFee = params.tokenPairContractFee;
        address tokenScAddr;
        if (params.currentChainID == toChainID) {
            if (contractFee == 0) {
                contractFee = storageData.mapContractFee[toChainID][fromChainID];
            }
            if (contractFee == 0) {
                contractFee = storageData.mapContractFee[toChainID][0];
            }
            tokenScAddr = CrossTypes.bytesToAddress(toTokenAccount);
        } else if (params.currentChainID == fromChainID) {
            if (contractFee == 0) {
                contractFee = storageData.mapContractFee[fromChainID][toChainID];
            }
            if (contractFee == 0) {
                contractFee = storageData.mapContractFee[fromChainID][0];
            }
            tokenScAddr = CrossTypes.bytesToAddress(fromTokenAccount);
        } else {
            require(false, "Invalid token pair");
        }
        require(params.srcTokenAccount == tokenScAddr, "Invalid token account");

        // Reuse variable fromChainID as tokenCrossType; burn token by tokenCrossType
        fromChainID = tokenManager.mapTokenPairType(params.tokenPairID);
        require(fromChainID == uint8(TokenCrossType.ERC20), "Not support");
        require(burnShadowToken(tokenManager, tokenScAddr, msg.sender, params.value), "Burn failed");

        if (contractFee > 0) {
            EtherTransfer.sendValue(payable(params.smgFeeProxy), contractFee, params.etherTransferGasLimit);
        }

        uint left = (msg.value).sub(contractFee);
        if (left != 0) {
            EtherTransfer.sendValue(payable(msg.sender), left, params.etherTransferGasLimit);
        }

        emit UserBurnLogger(params.smgID, params.tokenPairID, tokenScAddr, params.value, contractFee, params.fee, params.destUserAccount);
    }

    /// @notice                         mintBridge, storeman mint lock token on token shadow chain
    /// @notice                         event invoked by user mint lock
    /// @param storageData              Cross storage data
    /// @param params                   parameters for storeman mint lock token on token shadow chain
    function smgMint(CrossTypes.Data storage storageData, RapiditySmgMintParams memory params)
    public
    {
        storageData.rapidityTxData.addRapidityTx(params.uniqueID);

        ITokenManager tokenManager = storageData.tokenManager;
        uint8 tokenCrossType = tokenManager.mapTokenPairType(params.tokenPairID);
        require(tokenCrossType == uint8(TokenCrossType.ERC20), "Not support");
        if (params.fee > 0) {
            require(mintShadowToken(tokenManager, params.destTokenAccount, params.smgFeeProxy, params.fee), "Mint fee failed");
        }
        require(mintShadowToken(tokenManager, params.destTokenAccount, params.destUserAccount, params.value), "Mint failed");

        string[] memory keys = new string[](4);
        bytes[] memory values = new bytes[](4);
        keys[0] = "value:uint256";
        values[0] = abi.encodePacked(params.value);
        keys[1] = "tokenAccount:address";
        values[1] = abi.encodePacked(params.destTokenAccount);
        keys[2] = "userAccount:address";
        values[2] = abi.encodePacked(params.destUserAccount);
        keys[3] = "fee:uint256";
        values[3] = abi.encodePacked(params.fee);
        emit SmgMint(params.uniqueID, params.smgID, params.tokenPairID, keys, values);
        emit SmgMintLogger(params.uniqueID, params.smgID, params.tokenPairID, params.value, params.destTokenAccount, params.destUserAccount);
    }

    /// @notice                         burnBridge, storeman burn lock token on token shadow chain
    /// @notice                         event invoked by user burn lock
    /// @param storageData              Cross storage data
    /// @param params                   parameters for storeman burn lock token on token shadow chain
    function smgRelease(CrossTypes.Data storage storageData, RapiditySmgReleaseParams memory params)
    public
    {
        storageData.rapidityTxData.addRapidityTx(params.uniqueID);

        if (params.destTokenAccount == address(0)) {
            EtherTransfer.sendValue(payable(params.destUserAccount), params.value, params.etherTransferGasLimit);
            if (params.fee > 0) {
                EtherTransfer.sendValue(payable(params.smgFeeProxy), params.fee, params.etherTransferGasLimit);
            }
        } else {
            uint8 tokenCrossType = storageData.tokenManager.mapTokenPairType(params.tokenPairID);
            require(tokenCrossType == uint8(TokenCrossType.ERC20), "Not support");
            if (params.fee > 0) {
                require(CrossTypes.transfer(params.destTokenAccount, params.smgFeeProxy, params.fee), "Transfer token fee failed");
            }
            require(CrossTypes.transfer(params.destTokenAccount, params.destUserAccount, params.value), "Transfer token failed");
        }

        string[] memory keys = new string[](4);
        bytes[] memory values = new bytes[](4);
        keys[0] = "value:uint256";
        values[0] = abi.encodePacked(params.value);
        keys[1] = "tokenAccount:address";
        values[1] = abi.encodePacked(params.destTokenAccount);
        keys[2] = "userAccount:address";
        values[2] = abi.encodePacked(params.destUserAccount);
        keys[3] = "fee:uint256";
        values[3] = abi.encodePacked(params.fee);
        emit SmgRelease(params.uniqueID, params.smgID, params.tokenPairID, keys, values);
        emit SmgReleaseLogger(params.uniqueID, params.smgID, params.tokenPairID, params.value, params.destTokenAccount, params.destUserAccount);
    }

    function burnShadowToken(ITokenManager tokenManager, address tokenAddress, address userAccount, uint value) private returns (bool) {
        uint beforeBalance;
        uint afterBalance;
        beforeBalance = IRC20Protocol(tokenAddress).balanceOf(userAccount);

        tokenManager.burnToken(tokenAddress, userAccount, value);

        afterBalance = IRC20Protocol(tokenAddress).balanceOf(userAccount);
        return afterBalance == beforeBalance.sub(value);
    }

    function mintShadowToken(ITokenManager tokenManager, address tokenAddress, address userAccount, uint value) private returns (bool) {
        uint beforeBalance;
        uint afterBalance;
        beforeBalance = IRC20Protocol(tokenAddress).balanceOf(userAccount);

        tokenManager.mintToken(tokenAddress, userAccount, value);

        afterBalance = IRC20Protocol(tokenAddress).balanceOf(userAccount);
        return afterBalance == beforeBalance.add(value);
    }
}


// File contracts/crossApproach/CrossDelegateV4.sol

// Original license: SPDX_License_Identifier: MIT

/*

  Copyright 2023 Wanchain Foundation.

  Licensed under the Apache License, Version 2.0 (the "License");
  you may not use this file except in compliance with the License.
  You may obtain a copy of the License at

  http://www.apache.org/licenses/LICENSE-2.0

  Unless required by applicable law or agreed to in writing, software
  distributed under the License is distributed on an "AS IS" BASIS,
  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
  See the License for the specific language governing permissions and
  limitations under the License.

*/

//                            _           _           _
//  __      ____ _ _ __   ___| |__   __ _(_)_ __   __| | _____   __
//  \ \ /\ / / _` | '_ \ / __| '_ \ / _` | | '_ \@/ _` |/ _ \ \ / /
//   \ V  V / (_| | | | | (__| | | | (_| | | | | | (_| |  __/\ V /
//    \_/\_/ \__,_|_| |_|\___|_| |_|\__,_|_|_| |_|\__,_|\___| \_/
//
//

pragma solidity 0.8.18;



contract CrossDelegateV4 is CrossStorageV4 {
    using SafeMath for uint;

    /**
     *
     * EVENTS
     *
     **/

    /// @notice                         event of admin config
    /// @param adminAccount             account of admin
    event SetAdmin(address adminAccount);

    /// @notice                         event of setFee or setFees
    /// @param srcChainID               source of cross chain
    /// @param destChainID              destination of cross chain
    /// @param contractFee              contract fee
    /// @param agentFee                 agent fee
    event SetFee(uint indexed srcChainID, uint indexed destChainID, uint contractFee, uint agentFee);

    /// @notice                         event of setFee or setFees
    /// @param tokenPairID              ID of token pair
    /// @param contractFee              contract fee
    event SetTokenPairFee(uint indexed tokenPairID, uint contractFee);

    /// @notice                         event of storeman group ID withdraw the original coin to receiver
    /// @param smgID                    ID of storeman group
    /// @param timeStamp                timestamp of the withdraw
    /// @param receiver                 receiver address
    /// @param fee                      shadow coin of the fee which the storeman group pk got it
    event WithdrawHistoryFeeLogger(bytes32 indexed smgID, uint indexed timeStamp, address indexed receiver, uint fee);

    event ConfigOperator(address indexed operator, bool indexed enabled);

    event ConfigAdmin(address indexed admin, bool indexed enabled);

    /**
     *
     * MODIFIERS
     *
     */

    /// @notice                                 check the admin or not
    modifier onlyAdmin() {
        require(isAdmin[msg.sender] || msg.sender == admin || msg.sender == owner, "not admin");
        _;
    }

    modifier onlyOperator() {
        require(isOperator[msg.sender] || isAdmin[msg.sender] || msg.sender == admin || msg.sender == owner, "not operator");
        _;
    }

    /// @notice                                 check the storeman group is ready
    /// @param smgID                            ID of storeman group
    modifier onlyReadySmg(bytes32 smgID) {
        uint8 status;
        uint startTime;
        uint endTime;
        (status,startTime,endTime) = storageData.smgAdminProxy.getStoremanGroupStatus(smgID);

        require(status == uint8(GroupStatus.ready) && block.timestamp >= startTime && block.timestamp <= endTime, "PK is not ready");
        _;
    }


    /**
     *
     * MANIPULATIONS
     *
     */
    /// @notice                                 request exchange orignal coin or token with WRC20 on wanchain
    /// @param  smgID                           ID of storeman
    /// @param  tokenPairID                     token pair ID of cross chain coin/token
    /// @param  value                           exchange value
    /// @param  userAccount                     account of user, used to receive shadow chain token
    function userLock(bytes32 smgID, uint tokenPairID, uint value, bytes calldata userAccount)
    external
    payable
    notHalted
    nonReentrant
    onlyReadySmg(smgID)
    {
        address smgFeeProxy = getSmgFeeProxy();

        RapidityLibV4.RapidityUserLockParams memory params = RapidityLibV4.RapidityUserLockParams({
        smgID: smgID,
        tokenPairID: tokenPairID,
        value: value,
        currentChainID: currentChainID,
        tokenPairContractFee: mapTokenPairContractFee[tokenPairID],
        etherTransferGasLimit: getEtherTransferGasLimit(),
        destUserAccount: userAccount,
        smgFeeProxy: smgFeeProxy
        });
        RapidityLibV4.userLock(storageData, params);
    }

    /// @notice                                 request exchange RC20 token with WRC20 on wanchain
    /// @param  smgID                           ID of storeman
    /// @param  tokenPairID                     token pair ID of cross chain token
    /// @param  value                           exchange value
    /// @param  userAccount                     account of user, used to receive original chain token
    function userBurn(bytes32 smgID, uint tokenPairID, uint value, uint fee, address tokenAccount, bytes calldata userAccount)
    external
    payable
    notHalted
    nonReentrant
    onlyReadySmg(smgID)
    {
        address smgFeeProxy = getSmgFeeProxy();

        RapidityLibV4.RapidityUserBurnParams memory params = RapidityLibV4.RapidityUserBurnParams({
        smgID: smgID,
        tokenPairID: tokenPairID,
        value: value,
        fee: fee,
        currentChainID: currentChainID,
        tokenPairContractFee: mapTokenPairContractFee[tokenPairID],
        etherTransferGasLimit: getEtherTransferGasLimit(),
        srcTokenAccount: tokenAccount,
        destUserAccount: userAccount,
        smgFeeProxy: smgFeeProxy
        });
        RapidityLibV4.userBurn(storageData, params);
    }

    /// @notice                                 request exchange RC20 token with WRC20 on wanchain
    /// @param  uniqueID                        fast cross chain random number
    /// @param  smgID                           ID of storeman
    /// @param  tokenPairID                     token pair ID of cross chain token
    /// @param  value                           exchange value
    /// @param  fee                             exchange fee
    /// @param  userAccount                     address of user, used to receive WRC20 token
    /// @param  r                               signature
    /// @param  s                               signature
    function smgMint(bytes32 uniqueID, bytes32 smgID, uint tokenPairID, uint value, uint fee, address tokenAccount, address userAccount, bytes calldata r, bytes32 s)
    external
    notHalted
    {
        uint curveID;
        bytes memory PK;
        (curveID, PK) = acquireReadySmgInfo(smgID);

        RapidityLibV4.RapiditySmgMintParams memory params = RapidityLibV4.RapiditySmgMintParams({
        uniqueID: uniqueID,
        smgID: smgID,
        tokenPairID: tokenPairID,
        value: value,
        fee: fee,
        destTokenAccount: tokenAccount,
        destUserAccount: userAccount,
        smgFeeProxy: (storageData.smgFeeProxy == address(0)) ? owner : storageData.smgFeeProxy // fix: Stack too deep
        });
        RapidityLibV4.smgMint(storageData, params);

        bytes32 mHash = hashFunc(abi.encode(currentChainID, uniqueID, tokenPairID, value, fee, tokenAccount, userAccount));
        verifySignature(curveID, mHash, PK, r, s);
    }

    /// @notice                                 request exchange RC20 token with WRC20 on wanchain
    /// @param  uniqueID                        fast cross chain random number
    /// @param  smgID                           ID of storeman
    /// @param  tokenPairID                     token pair ID of cross chain token
    /// @param  value                           exchange value
    /// @param  fee                             exchange fee
    /// @param  userAccount                     address of user, used to receive original token/coin
    /// @param  r                               signature
    /// @param  s                               signature
    function smgRelease(bytes32 uniqueID, bytes32 smgID, uint tokenPairID, uint value, uint fee, address tokenAccount, address userAccount, bytes calldata r, bytes32 s)
    external
    notHalted
    {
        uint curveID;
        bytes memory PK;
        (curveID, PK) = acquireReadySmgInfo(smgID);

        RapidityLibV4.RapiditySmgReleaseParams memory params = RapidityLibV4.RapiditySmgReleaseParams({
        uniqueID: uniqueID,
        smgID: smgID,
        tokenPairID: tokenPairID,
        value: value,
        fee: fee,
        etherTransferGasLimit: getEtherTransferGasLimit(),
        destTokenAccount: tokenAccount,
        destUserAccount: userAccount,
        smgFeeProxy: (storageData.smgFeeProxy == address(0)) ? owner : storageData.smgFeeProxy // fix: Stack too deep
        });
        RapidityLibV4.smgRelease(storageData, params);

        bytes32 mHash = hashFunc(abi.encode(currentChainID, uniqueID, tokenPairID, value, fee, tokenAccount, userAccount));
        verifySignature(curveID, mHash, PK, r, s);
    }

    /// @notice                             set the fee of the storeman group should get
    /// @param param                        struct of setFee parameter
    function setFee(SetFeesParam calldata param) public virtual onlyOperator {
        storageData.mapContractFee[param.srcChainID][param.destChainID] = param.contractFee;
        storageData.mapAgentFee[param.srcChainID][param.destChainID] = param.agentFee;
        emit SetFee(param.srcChainID, param.destChainID, param.contractFee, param.agentFee);
    }

    /// @notice                             set the fee of the storeman group should get
    /// @param params                        struct of setFees parameter
    function setFees(SetFeesParam [] calldata params) public virtual onlyOperator {
        for (uint i = 0; i < params.length; ++i) {
            storageData.mapContractFee[params[i].srcChainID][params[i].destChainID] = params[i].contractFee;
            storageData.mapAgentFee[params[i].srcChainID][params[i].destChainID] = params[i].agentFee;
            emit SetFee(params[i].srcChainID, params[i].destChainID, params[i].contractFee, params[i].agentFee);
        }
    }

    /// @notice                             set the fee of the storeman group should get
    /// @param tokenPairID                  ID of token pair
    /// @param contractFee                  contractFee of token pair
    function setTokenPairFee(uint256 tokenPairID, uint256 contractFee) external virtual onlyOperator {
        mapTokenPairContractFee[tokenPairID] = contractFee;
        emit SetTokenPairFee(tokenPairID, contractFee);
    }

    /// @notice                             set the fee of the storeman group should get
    /// @param params                       struct of setTokenPairFees parameter
    function setTokenPairFees(SetTokenPairFeesParam [] calldata params) public virtual onlyOperator {
        for (uint i = 0; i < params.length; ++i) {
            mapTokenPairContractFee[params[i].tokenPairID] = params[i].contractFee;
            emit SetTokenPairFee(params[i].tokenPairID, params[i].contractFee);
        }
    }

    function setChainID(uint256 chainID) external virtual onlyAdmin {
        if (currentChainID == 0) {
            currentChainID = chainID;
        }
    }

    function hashFunc(bytes memory data) public view returns (bytes32){
        if(hashType == 1) {
            return keccak256(data);
        } else {
            return sha256(data);
        }
    }

    function setHashType(uint _hashType) external onlyOwner {
        hashType = _hashType;
    }

    function setAdmin(address adminAccount) external onlyOwner {
        admin = adminAccount;
        emit SetAdmin(adminAccount);
    }

    function setUintValue(bytes calldata key, bytes calldata innerKey, uint value) external virtual onlyAdmin {
        return BasicStorageLib.setStorage(uintData, key, innerKey, value);
    }

    function delUintValue(bytes calldata key, bytes calldata innerKey) external virtual onlyAdmin {
        return BasicStorageLib.delStorage(uintData, key, innerKey);
    }

    /// @notice                             update the initialized state value of this contract
    /// @param tokenManager                 address of the token manager
    /// @param smgAdminProxy                address of the storeman group admin
    /// @param smgFeeProxy                  address of the proxy to store fee for storeman group
    /// @param sigVerifier                  address of the signature verifier
    function setPartners(address tokenManager, address smgAdminProxy, address smgFeeProxy, address, address sigVerifier)
    external
    onlyOwner
    {
        require(tokenManager != address(0) && smgAdminProxy != address(0) && sigVerifier != address(0),
            "Parameter is invalid");

        storageData.smgAdminProxy = IStoremanGroup(smgAdminProxy);
        storageData.tokenManager = ITokenManager(tokenManager);
        // storageData.quota = IQuota(quota);
        storageData.smgFeeProxy = smgFeeProxy;
        storageData.sigVerifier = ISignatureVerifier(sigVerifier);
    }


    /// @notice                             withdraw the history fee to foundation account
    /// @param smgIDs                       array of storemanGroup ID
    function smgWithdrawHistoryFee(bytes32 [] calldata smgIDs) external {
        uint fee;
        uint currentFee;
        address smgFeeProxy = storageData.smgFeeProxy;
        if (smgFeeProxy == address(0)) {
            smgFeeProxy = owner;
        }
        require(smgFeeProxy != address(0), "invalid smgFeeProxy");

        for (uint i = 0; i < smgIDs.length; ++i) {
            currentFee = storageData.mapStoremanFee[smgIDs[i]];
            delete storageData.mapStoremanFee[smgIDs[i]];
            fee = fee.add(currentFee);
            emit WithdrawHistoryFeeLogger(smgIDs[i], block.timestamp, smgFeeProxy, currentFee);
        }
        if (fee > 0) {
            EtherTransfer.sendValue(payable(smgFeeProxy), fee, getEtherTransferGasLimit());
        }
    }


    /** Get Functions */

    function getUintValue(bytes calldata key, bytes calldata innerKey) public view returns (uint) {
        return BasicStorageLib.getStorage(uintData, key, innerKey);
    }

    /// @notice                             get the fee of the storeman group should get
    /// @param key                          key of storeman fee
    /// @return fee                         original coin the storeman group should get
    function getStoremanFee(bytes32 key) external view returns(uint fee) {
        fee = storageData.mapStoremanFee[key];
    }

    /// @notice                             get the fee of the storeman group should get
    /// @param param                        struct of getFee parameter
    /// @return fee                        struct of getFee return
    function getFee(GetFeesParam calldata param) public view returns(GetFeesReturn memory fee) {
        fee.contractFee = storageData.mapContractFee[param.srcChainID][param.destChainID];
        fee.agentFee = storageData.mapAgentFee[param.srcChainID][param.destChainID];
    }

    /// @notice                             get the fee of the storeman group should get
    /// @param params                       struct of getFees parameter
    /// @return fees                        struct of getFees return
    function getFees(GetFeesParam [] calldata params) public view returns(GetFeesReturn [] memory fees) {
        fees = new GetFeesReturn[](params.length);
        for (uint i = 0; i < params.length; ++i) {
            fees[i].contractFee = storageData.mapContractFee[params[i].srcChainID][params[i].destChainID];
            fees[i].agentFee = storageData.mapAgentFee[params[i].srcChainID][params[i].destChainID];
        }
    }

    /// @notice                             get the token pair fee of the storeman group should get
    /// @param tokenPairID                  ID of token pair
    /// @return contractFee                 contractFee of token pair
    function getTokenPairFee(uint256 tokenPairID) external view returns(uint256 contractFee) {
        contractFee = mapTokenPairContractFee[tokenPairID];
    }

    /// @notice                             get the token pair fees of the storeman group should get
    /// @param tokenPairIDs                 array of tokenPairID
    /// @return contractFees                array of tokenPair contractFee
    function getTokenPairFees(uint256[] calldata tokenPairIDs) external view returns(uint256 [] memory contractFees) {
        contractFees = new uint256[](tokenPairIDs.length);
        for (uint i = 0; i < tokenPairIDs.length; ++i) {
            contractFees[i] = mapTokenPairContractFee[tokenPairIDs[i]];
        }
    }

    /// @notice                             get the initialized state value of this contract
    /// @return tokenManager                address of the token manager
    /// @return smgAdminProxy               address of the storeman group admin
    /// @return smgFeeProxy                 address of the proxy to store fee for storeman group
    /// @return quota                       address of the quota
    /// @return sigVerifier                 address of the signature verifier
    function getPartners()
    external
    view
    returns(address tokenManager, address smgAdminProxy, address smgFeeProxy, address quota, address sigVerifier)
    {
        tokenManager = address(storageData.tokenManager);
        smgAdminProxy = address(storageData.smgAdminProxy);
        smgFeeProxy = storageData.smgFeeProxy;
        quota = address(storageData.quota);
        sigVerifier = address(storageData.sigVerifier);
    }


    /** Private and Internal Functions */

    /// @notice                                 check the storeman group is ready or not
    /// @param smgID                            ID of storeman group
    /// @return curveID                         ID of elliptic curve
    /// @return PK                              PK of storeman group
    function acquireReadySmgInfo(bytes32 smgID)
    internal
    view
    returns (uint curveID, bytes memory PK)
    {
        uint8 status;
        uint startTime;
        uint endTime;
        (,status,,,,curveID,,PK,,startTime,endTime) = storageData.smgAdminProxy.getStoremanGroupConfig(smgID);

        require(status == uint8(GroupStatus.ready) && block.timestamp >= startTime && block.timestamp <= endTime, "PK is not ready");

        return (curveID, PK);
    }

    /// @notice                                 get the unregistered storeman group info
    /// @param smgID                            ID of storeman group
    /// @return curveID                         ID of elliptic curve
    /// @return PK                              PK of storeman group
    function acquireUnregisteredSmgInfo(bytes32 smgID)
    internal
    view
    returns (uint curveID, bytes memory PK)
    {
        uint8 status;
        (,status,,,,curveID,,PK,,,) = storageData.smgAdminProxy.getStoremanGroupConfig(smgID);

        require(status == uint8(GroupStatus.unregistered), "PK is not unregistered");
    }

    /// @notice       convert bytes to bytes32
    /// @param b      bytes array
    /// @param offset offset of array to begin convert
    function bytesToBytes32(bytes memory b, uint offset) internal pure returns (bytes32 result) {
        assembly {
            result := mload(add(add(b, offset), 32))
        }
    }

    /// @notice             verify signature
    /// @param  curveID     ID of elliptic curve
    /// @param  message     message to be verified
    /// @param  r           Signature info r
    /// @param  s           Signature info s
    function verifySignature(uint curveID, bytes32 message, bytes memory PK, bytes memory r, bytes32 s) internal {
        bytes32 PKx = bytesToBytes32(PK, 0);
        bytes32 PKy = bytesToBytes32(PK, 32);

        bytes32 Rx = bytesToBytes32(r, 0);
        bytes32 Ry = bytesToBytes32(r, 32);

        require(storageData.sigVerifier.verify(curveID, s, PKx, PKy, Rx, Ry, message), "Signature verification failed");
    }

    function getSmgFeeProxy() internal view returns (address) {
        address smgFeeProxy = storageData.smgFeeProxy;
        return (smgFeeProxy == address(0)) ? owner : smgFeeProxy;
    }

    //*********************************************************************************************
    //*********************************************************************************************
    // NFT
    function onERC721Received(address, address, uint256, bytes memory)
        public
        pure
        returns(bytes4)
    {
        return this.onERC721Received.selector;
    }

    function onERC1155Received(address, address, uint256, uint256, bytes memory) 
        public 
        pure 
        returns (bytes4)
    {
        return this.onERC1155Received.selector;
    }

    function onERC1155BatchReceived(address, address, uint256[] calldata, uint256[] calldata, bytes calldata) 
        public
        pure
        returns (bytes4)
    {
        return this.onERC1155BatchReceived.selector;
    }

    // using "memory" instead of "calldata" to avoid Stakck too deep
    function userLockNFT(bytes32 smgID, uint tokenPairID, uint[] memory tokenIDs, uint[] memory tokenValues, bytes memory userAccount)
        public
        payable
        virtual
        notHalted
        nonReentrant
        onlyReadySmg(smgID)
    {
        require(tokenIDs.length > 0 && tokenIDs.length <= getMaxBatchSize(), "Invalid length");
        require(tokenIDs.length == tokenValues.length, "Length mismatch");

        NFTLibV1.RapidityUserLockNFTParams memory params = NFTLibV1.RapidityUserLockNFTParams({
            smgID: smgID,
            tokenPairID: tokenPairID,
            tokenIDs: tokenIDs,
            tokenValues: tokenValues,
            currentChainID: currentChainID,
            tokenPairContractFee: mapTokenPairContractFee[tokenPairID],
            etherTransferGasLimit: getEtherTransferGasLimit(),
            destUserAccount: userAccount,
            smgFeeProxy: getSmgFeeProxy()
        });
        NFTLibV1.userLockNFT(storageData, params);
    }

    // using "memory" instead of "calldata" to avoid Stakck too deep
    function userBurnNFT(bytes32 smgID, uint tokenPairID, uint[] memory tokenIDs, uint[] memory tokenValues, address tokenAccount, bytes memory userAccount)
        public
        payable
        notHalted
        nonReentrant
        onlyReadySmg(smgID)
    {
        require(tokenIDs.length > 0 && tokenIDs.length <= getMaxBatchSize(), "Invalid length");
        require(tokenIDs.length == tokenValues.length, "Length mismatch");

        NFTLibV1.RapidityUserBurnNFTParams memory params = NFTLibV1.RapidityUserBurnNFTParams({
            smgID: smgID,
            tokenPairID: tokenPairID,
            tokenIDs: tokenIDs,
            tokenValues: tokenValues,
            currentChainID: currentChainID,
            tokenPairContractFee: mapTokenPairContractFee[tokenPairID],
            etherTransferGasLimit: getEtherTransferGasLimit(),
            srcTokenAccount: tokenAccount,
            destUserAccount: userAccount,
            smgFeeProxy: getSmgFeeProxy()
        });
        NFTLibV1.userBurnNFT(storageData, params);
    }

    // using "memory" instead of "calldata" to avoid Stakck too deep
    function smgMintNFT(bytes32 uniqueID, bytes32 smgID, uint tokenPairID, uint[] memory tokenIDs, uint[] memory tokenValues, bytes memory extData, address tokenAccount, address userAccount, bytes memory r, bytes32 s)
        public
        notHalted
    {
        uint curveID;
        bytes memory PK;
        (curveID, PK) = acquireReadySmgInfo(smgID);

        NFTLibV1.RapiditySmgMintNFTParams memory params = NFTLibV1.RapiditySmgMintNFTParams({
            uniqueID: uniqueID,
            smgID: smgID,
            tokenPairID: tokenPairID,
            tokenIDs: tokenIDs,
            tokenValues: tokenValues,
            extData: extData,
            destTokenAccount: tokenAccount,
            destUserAccount: userAccount
        });

        NFTLibV1.smgMintNFT(storageData, params);
        bytes32 mHash = hashFunc(abi.encode(currentChainID, uniqueID, tokenPairID, tokenIDs, tokenValues, extData, tokenAccount, userAccount));
        verifySignature(curveID, mHash, PK, r, s);
    }

    // using "memory" instead of "calldata" to avoid Stakck too deep
    function smgReleaseNFT(bytes32 uniqueID, bytes32 smgID, uint tokenPairID, uint[] memory tokenIDs, uint[] memory tokenValues, address tokenAccount, address userAccount, bytes memory r, bytes32 s)
        public
        notHalted
    {
        uint curveID;
        bytes memory PK;
        (curveID, PK) = acquireReadySmgInfo(smgID);

        NFTLibV1.RapiditySmgReleaseNFTParams memory params = NFTLibV1.RapiditySmgReleaseNFTParams({
            uniqueID: uniqueID,
            smgID: smgID,
            tokenPairID: tokenPairID,
            tokenIDs: tokenIDs,
            tokenValues: tokenValues,
            destTokenAccount: tokenAccount,
            destUserAccount: userAccount
        });
        NFTLibV1.smgReleaseNFT(storageData, params);

        bytes32 mHash = hashFunc(abi.encode(currentChainID, uniqueID, tokenPairID, tokenIDs, tokenValues, tokenAccount, userAccount));
        verifySignature(curveID, mHash, PK, r, s);
    }

    function setMaxBatchSize(uint _maxBatchSize) 
      external
      virtual
      onlyAdmin
    {
      maxBatchSize = _maxBatchSize;
    }

    function getMaxBatchSize() 
      public
      view
      returns (uint)
    {
      if(maxBatchSize == 0) {
        return 20;
      }
      return maxBatchSize;
    }

    function getBatchFee(uint tokenPairID, uint batchLength) 
      external
      view
      returns (uint)
    {
      uint contractFee;
      (, contractFee) = NFTLibV1.getTokenScAddrAndContractFee(storageData, tokenPairID, mapTokenPairContractFee[tokenPairID], currentChainID, batchLength);
      return contractFee;
    }

    function setEtherTransferGasLimit(uint _etherTransferGasLimit) 
      external
      virtual
      onlyAdmin
    {
      etherTransferGasLimit = _etherTransferGasLimit;
    }

    function getEtherTransferGasLimit() 
      public
      view
      returns (uint)
    {
      if(etherTransferGasLimit == 0) {
        return 2300;
      }
      return etherTransferGasLimit;
    }

    function configOperator(address _operator, bool enabled) external onlyAdmin {
        isOperator[_operator] = enabled;
        emit ConfigOperator(_operator, enabled);
    }

    function configAdmin(address _admin, bool enabled) external onlyOwner {
        isAdmin[_admin] = enabled;
        emit ConfigAdmin(_admin, enabled);
    }
}