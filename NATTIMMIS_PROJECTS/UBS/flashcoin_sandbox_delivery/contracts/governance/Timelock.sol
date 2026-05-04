// SPDX-License-Identifier: MIT
pragma solidity ^0.8.21;

import "@openzeppelin/contracts/governance/TimelockController.sol";

/**
 * @title SettlementTimelock
 * @notice OpenZeppelin TimelockController, parameterised for institutional
 *         use. Every privileged action on the InternalSettlementToken or
 *         ComplianceAllowlist that touches DEFAULT_ADMIN_ROLE must be queued
 *         here, wait the minimum delay, then be executed by the multi-sig.
 *
 *         Role layout (mirrors OZ defaults):
 *
 *           PROPOSER_ROLE  : the multi-sig (e.g. TRON multi-sig account or
 *                            Gnosis-Safe-equivalent). Proposes operations.
 *           EXECUTOR_ROLE  : the multi-sig, OR a wider set if you want
 *                            anyone to execute already-queued + matured ops.
 *           CANCELLER_ROLE : SOC / Risk team. Can cancel a queued op before
 *                            execution if a security issue is discovered.
 *           DEFAULT_ADMIN  : address(0) after deploy. Set in the deploy
 *                            script. The timelock administers itself via
 *                            queued operations — no human admin override.
 *
 *         Minimum delay is set per-environment:
 *           - testnet rehearsal : 1 hour
 *           - mainnet           : 48 hours (configurable up via timelock)
 *
 *         See docs/governance/raci.md for who can propose / approve / cancel.
 */
contract SettlementTimelock is TimelockController {
    constructor(
        uint256 minDelay,
        address[] memory proposers,
        address[] memory executors,
        address admin
    ) TimelockController(minDelay, proposers, executors, admin) {}
}
