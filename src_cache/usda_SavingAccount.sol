pragma solidity ^0.8.0;

import "@openzeppelin/contracts/access/AccessControl.sol";
import "@openzeppelin/contracts/token/ERC20/utils/SafeERC20.sol";
import "@openzeppelin/contracts/security/ReentrancyGuard.sol";
import "@openzeppelin/contracts/security/Pausable.sol";
import "./interface/IERC20Mintable.sol";

contract SavingAccount is AccessControl, ReentrancyGuard, Pausable {
    using SafeERC20 for IERC20;

    bytes32 public constant ADMIN_ROLE = keccak256("ADMIN_ROLE");
    bytes32 public constant POOL_MANAGER_ROLE = keccak256("POOL_MANAGER_ROLE");
    bytes32 public constant APR_MANAGER_ROLE = keccak256("APR_MANAGER_ROLE");
    bytes32 public constant PAUSE_MANAGER_ROLE =
        keccak256("PAUSE_MANAGER_ROLE");

    // It's used to calculate the interest base.
    uint256 public constant APR_COEFFICIENT = 10 ** 8;

    uint256 public totalUnderlying;
    uint256 public totalsUSDaLockedAmount;
    uint256 public lastCheckpoint;
    IERC20 public usda;
    IERC20Mintable public susda;

    // targetAPR: 0.1% => 100000 (10 ** 5)
    // targetAPR: 10% => 10000000 (10 ** 7)
    // targetAPR: 100% => 100000000 (10 ** 8)
    uint256 public targetAPR;

    // 100%
    uint256 public maxAPR = 10 ** 8;

    // Interest that has not yet been settled.
    uint256 public unpaidInterest;

    // default 7 days
    uint256 public processPeriod = 7 days;

    uint256 constant PROCESS_PERIOD_MAX = 30 days;

    struct RedeemDetail {
        uint256 id;
        uint256 timestamp;
        address user;
        uint256 underlyingAmount;
        // False not redeem, or True.
        bool isDone;
    }

    event RedeemRequested(
        uint256 id,
        uint256 timestamp,
        address indexed user,
        uint256 underlyingAmount
    );

    event Redeem(
        uint256 id,
        uint256 timestamp,
        address indexed user,
        uint256 underlyingAmount
    );

    // Mapping from redeem index to RedeemDetail.
    mapping(uint256 => RedeemDetail) public redeemDetails;
    // redeem index.
    uint256 public redeemIndex;

    event TargetAPRChanged(uint256 _new);
    event ProcessPeriodChanged(uint256 _new);

    // Constructor will be called on contract creation
    constructor(address _admin, address _usda, address _susda) {
        require(_admin != address(0), "!_admin");
        require(_usda != address(0), "!_usda");
        require(_susda != address(0), "!_susda");
        _grantRole(DEFAULT_ADMIN_ROLE, _admin);
        _grantRole(ADMIN_ROLE, _admin);
        _setRoleAdmin(APR_MANAGER_ROLE, ADMIN_ROLE);
        _setRoleAdmin(POOL_MANAGER_ROLE, ADMIN_ROLE);
        _setRoleAdmin(PAUSE_MANAGER_ROLE, ADMIN_ROLE);
        _setRoleAdmin(ADMIN_ROLE, ADMIN_ROLE);

        usda = IERC20(_usda);
        susda = IERC20Mintable(_susda);
    }

    function pause() external onlyRole(PAUSE_MANAGER_ROLE) {
        Pausable._pause();
    }

    function unpause() external onlyRole(PAUSE_MANAGER_ROLE) {
        Pausable._unpause();
    }

    /**
     * @dev to set APR
     * @param _targetAPR the amount of APR. it should be multiply 10**6
     */
    function setTargetAPR(
        uint256 _targetAPR
    ) external onlyRole(APR_MANAGER_ROLE) realizeReward {
        require(_targetAPR <= maxAPR, "target apr should be less than max apr");
        targetAPR = _targetAPR;
        emit TargetAPRChanged(_targetAPR);
    }

    /**
     * @dev to set the period of processing
     * @param _processPeriod the period of processing. it's second.
     */
    function setProcessPeriod(
        uint256 _processPeriod
    ) external onlyRole(POOL_MANAGER_ROLE) {
        require(
            _processPeriod <= PROCESS_PERIOD_MAX,
            "exceed PROCESS_PERIOD_MAX"
        );
        processPeriod = _processPeriod;
        emit ProcessPeriodChanged(_processPeriod);
    }

    /**
     * @dev get total underly token amount
     */
    function getTotalUnderlying() public view returns (uint256) {
        // need include manager fee
        uint256 totalInterest = getRPS() * (block.timestamp - lastCheckpoint);
        return totalUnderlying + totalInterest;
    }

    /**
     * @dev get amount of shares by underlying amount
     * @param _amount the amount of underlying
     */
    function getSharesByAmount(uint256 _amount) public view returns (uint256) {
        if (totalsUSDaLockedAmount == 0) {
            return 0;
        } else {
            return (_amount * totalsUSDaLockedAmount) / getTotalUnderlying();
        }
    }

    /**
     * @dev get amount by shares
     * @param _shares the amount of cToken
     */
    function getAmountByShares(uint256 _shares) public view returns (uint256) {
        if (totalsUSDaLockedAmount == 0) {
            return 0;
        } else {
            return (_shares * getTotalUnderlying()) / (totalsUSDaLockedAmount);
        }
    }

    /**
     * @dev revolutions per second
     */
    function getRPS() public view returns (uint256) {
        // TODO: If use totalUnderlying, then the interest also incurs interest, do we want to switch to principal?
        return (targetAPR * (totalUnderlying)) / (365 days) / (APR_COEFFICIENT);
    }

    modifier realizeReward() {
        if (totalsUSDaLockedAmount != 0) {
            uint256 totalInterest = getRPS() *
                (block.timestamp - lastCheckpoint);
            unpaidInterest += totalInterest;
            totalUnderlying += totalInterest;
        }
        lastCheckpoint = block.timestamp;
        _;
    }

    /**
     * @dev mint sUSDA
     * @param amount the amount of underlying token
     */
    function mint(uint256 amount) external {
        _mintFor(amount, msg.sender);
    }

    /**
     * @dev mint sUSDA
     * @param amount the amount of underlying token,
     * @param receiver the address be used to receive sUSDA
     */
    function mintFor(uint256 amount, address receiver) external {
        _mintFor(amount, receiver);
    }

    /**
     * @dev mint sUSDA
     * @param amount the amount of underlying token
     * @param receiver the address be used to receive sUSDA
     */
    function _mintFor(
        uint256 amount,
        address receiver
    ) internal realizeReward nonReentrant whenNotPaused {
        require(amount >= 1e18, "mint amount is too small");
        usda.safeTransferFrom(msg.sender, address(this), amount);

        uint256 cTokenAmount;
        if (totalsUSDaLockedAmount == 0 || totalUnderlying == 0) {
            cTokenAmount = amount;
        } else {
            cTokenAmount = (amount * totalsUSDaLockedAmount) / totalUnderlying;
        }

        susda.mint(receiver, cTokenAmount);
        totalsUSDaLockedAmount += cTokenAmount;
        totalUnderlying = totalUnderlying + amount;
    }

    /**
     * @dev redeem susda
     * @param amount the amount of sToken, 1 sToken = 10**18, which eaquals to 1 usda (if not interest).
     * error code
     * 100: redeem is less than the balance
     * 101: totalUnderlying should be greater than 0
     * 102:
     */
    function redeem(
        uint256 amount
    ) external realizeReward nonReentrant whenNotPaused {
        require(totalUnderlying > 0, "totalUnderlying = 0");
        require(totalsUSDaLockedAmount > 0, "susda total is 0");
        require(amount >= 1e18, "redeem amount is too small");

        uint256 underlyingAmount = (amount * totalUnderlying) /
            totalsUSDaLockedAmount;

        susda.burn(msg.sender, amount);
        totalsUSDaLockedAmount -= amount;

        totalUnderlying = totalUnderlying - underlyingAmount;

        redeemIndex++;
        redeemDetails[redeemIndex] = RedeemDetail({
            id: redeemIndex,
            timestamp: block.timestamp,
            user: msg.sender,
            underlyingAmount: underlyingAmount,
            isDone: false
        });

        emit RedeemRequested(
            redeemIndex,
            block.timestamp,
            msg.sender,
            underlyingAmount
        );
    }

    /**
     * @dev claim susda
     * @param idx the index of redeemDetails
     */
    function claimRedeem(
        uint256 idx
    ) external realizeReward nonReentrant whenNotPaused {
        require(redeemDetails[idx].user == msg.sender, "not yours");
        require(redeemDetails[idx].isDone == false, "is done");
        require(
            redeemDetails[idx].timestamp + processPeriod <= block.timestamp,
            "processing"
        );

        redeemDetails[idx].isDone = true;

        uint256 redeemAmount = redeemDetails[idx].underlyingAmount;

        usda.safeTransfer(msg.sender, redeemAmount);

        emit Redeem(idx, block.timestamp, msg.sender, redeemAmount);
    }

    function balanceOf(address _owner) public view returns (uint256 balance) {
        return getAmountByShares(susda.balanceOf(_owner));
    }

    function getPendingInterest() external view returns (uint256) {
        return getRPS() * (block.timestamp - lastCheckpoint);
    }

    /**
     * @dev Distribute interest
     */
    function distributeInterests()
        external
        realizeReward
        onlyRole(POOL_MANAGER_ROLE)
    {
        IERC20(usda).safeTransferFrom(
            msg.sender,
            address(this),
            unpaidInterest
        );
        unpaidInterest = 0;
    }
}
