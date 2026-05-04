// SPDX-License-Identifier: MIT
pragma solidity ^0.8.21;

/**
 * @title Migrations
 * @notice Tronbox/Truffle migration tracking contract. Records which numbered
 *         migration script has last completed on each network. The contract
 *         carries no business logic and holds no value — its sole role is to
 *         let `tronbox migrate` know what work has already been done so a
 *         partial deploy can resume.
 */
contract Migrations {
    address public owner;
    uint256 public lastCompletedMigration;

    modifier restricted() {
        require(msg.sender == owner, "Migrations: not owner");
        _;
    }

    constructor() {
        owner = msg.sender;
    }

    function setCompleted(uint256 completed) external restricted {
        lastCompletedMigration = completed;
    }
}
