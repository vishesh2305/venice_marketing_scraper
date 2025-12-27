// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import "@openzeppelin/contracts/utils/ReentrancyGuard.sol";
import "@openzeppelin/contracts/access/Ownable.sol";
import "@openzeppelin/contracts/security/Pausable.sol";

/**
 * @title F1SecurityVault
 * @dev Main DeFi vault with MEV protection and security features
 */
contract F1SecurityVault is ReentrancyGuard, Ownable, Pausable {
    
    // State variables
    mapping(address => uint256) public userBalances;
    mapping(address => uint256) public lastDepositTimestamp;
    mapping(address => uint256) public securityScore;
    
    uint256 public totalDeposits;
    uint256 public minDepositAmount = 0.001 ether;
    uint256 public withdrawalCooldown = 10 minutes;
    
    // Security tracking
    bool public auditPassed;
    address public securityAuditor;
    
    // Events
    event Deposit(address indexed user, uint256 amount, uint256 timestamp);
    event Withdrawal(address indexed user, uint256 amount, uint256 timestamp);
    event SecurityAlert(address indexed user, string alertType, uint256 timestamp);
    event AuditCompleted(address indexed auditor, bool passed, uint256 timestamp);
    
    // Custom errors (gas efficient)
    error InsufficientBalance();
    error DepositTooSmall();
    error WithdrawalOnCooldown();
    error TransferFailed();
    
    constructor() Ownable(msg.sender) {
        auditPassed = false;
    }
    
    /**
     * @dev Deposit ETH into the vault with reentrancy protection
     */
    function deposit() external payable nonReentrant whenNotPaused {
        if (msg.value < minDepositAmount) revert DepositTooSmall();
        
        // Security check: prevent flash loan attacks
        require(tx.origin == msg.sender, "EOA only");
        
        // Effects (update state before interaction)
        userBalances[msg.sender] += msg.value;
        totalDeposits += msg.value;
        lastDepositTimestamp[msg.sender] = block.timestamp;
        
        // Increase security score for safe deposits
        securityScore[msg.sender] += 10;
        
        emit Deposit(msg.sender, msg.value, block.timestamp);
    }
    
    /**
     * @dev Withdraw funds with cooldown period for MEV protection
     */
    function withdraw(uint256 amount) external nonReentrant whenNotPaused {
        if (userBalances[msg.sender] < amount) revert InsufficientBalance();
        
        // Cooldown check to prevent sandwich attacks
        if (block.timestamp < lastDepositTimestamp[msg.sender] + withdrawalCooldown) {
            revert WithdrawalOnCooldown();
        }
        
        // Effects before interaction
        userBalances[msg.sender] -= amount;
        totalDeposits -= amount;
        
        // Interaction (send funds)
        (bool success, ) = payable(msg.sender).call{value: amount}("");
        if (!success) revert TransferFailed();
        
        emit Withdrawal(msg.sender, amount, block.timestamp);
    }
    
    /**
     * @dev Get user balance
     */
    function getBalance() external view returns (uint256) {
        return userBalances[msg.sender];
    }
    
    /**
     * @dev Check if user can withdraw (cooldown passed)
     */
    function canWithdraw(address user) external view returns (bool) {
        return block.timestamp >= lastDepositTimestamp[user] + withdrawalCooldown;
    }
    
    /**
     * @dev Mark audit as completed (only auditor)
     */
    function completeAudit(bool passed) external {
        require(msg.sender == securityAuditor || msg.sender == owner(), "Not authorized");
        auditPassed = passed;
        emit AuditCompleted(msg.sender, passed, block.timestamp);
    }
    
    /**
     * @dev Set security auditor address (only owner)
     */
    function setSecurityAuditor(address auditor) external onlyOwner {
        securityAuditor = auditor;
    }
    
    /**
     * @dev Emergency pause (only owner)
     */
    function pause() external onlyOwner {
        _pause();
    }
    
    /**
     * @dev Unpause contract (only owner)
     */
    function unpause() external onlyOwner {
        _unpause();
    }
    
    /**
     * @dev Get contract security status
     */
    function getSecurityStatus() external view returns (
        bool isPaused,
        bool isAudited,
        uint256 tvl,
        address auditor
    ) {
        return (paused(), auditPassed, totalDeposits, securityAuditor);
    }
}
