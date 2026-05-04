// SPDX-License-Identifier: MIT
pragma solidity ^0.8.21;

/**
 * @title Roles
 * @notice Centralised role identifiers used across the InternalSettlementToken
 *         system. Each role is a keccak256 hash of its label.
 *
 *         The role assignment matrix is documented in
 *         docs/governance/role_assignment.md. The four-eyes / segregation-of-
 *         duties policy is in docs/governance/segregation_of_duties.md.
 *
 *         Roles are intentionally narrow. Compound privileges are achieved
 *         through composition, not through a single super-role.
 */
library Roles {
    /// @dev Top-level admin. Held by the multi-sig + Timelock. Can grant or
    ///      revoke any other role. Never assigned to an EOA in production.
    bytes32 internal constant DEFAULT_ADMIN_ROLE = 0x00;

    /// @dev May call mint(). Subject to per-block rate limit and global cap.
    ///      Typical holder: an issuance service signed by the Treasury team.
    bytes32 internal constant MINTER_ROLE = keccak256("MINTER_ROLE");

    /// @dev May call burn() / burnFrom(). Used by the redemption service.
    bytes32 internal constant BURNER_ROLE = keccak256("BURNER_ROLE");

    /// @dev May call pause() / unpause(). Held by SOC and incident-response
    ///      operators. Pause stops all transfers immediately.
    bytes32 internal constant PAUSER_ROLE = keccak256("PAUSER_ROLE");

    /// @dev May add or remove addresses from the compliance allowlist.
    ///      Held by the Compliance team. Distinct from MINTER_ROLE so no
    ///      single role can both authorise an address and credit it.
    bytes32 internal constant COMPLIANCE_ROLE = keccak256("COMPLIANCE_ROLE");

    /// @dev May call upgrade-related parameter setters that are rate-limit-
    ///      adjacent (rate limit window/cap, allowlist address). Held by
    ///      Engineering, but every action is gated by the Timelock.
    bytes32 internal constant CONFIGURATOR_ROLE = keccak256("CONFIGURATOR_ROLE");
}
