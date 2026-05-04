// SPDX-License-Identifier: MIT
pragma solidity ^0.8.21;

import "@openzeppelin/contracts/access/AccessControl.sol";
import "./Roles.sol";

/**
 * @title ComplianceAllowlist
 * @notice On-chain registry of addresses authorised to hold or transact in the
 *         Internal Settlement Token. Deployed as a separate contract so the
 *         compliance team can manage it without touching the token contract,
 *         and so audit logs of compliance actions are isolated and easy to
 *         export.
 *
 *         Token transfers consult this contract via {isAllowed}. An address
 *         not on the list cannot send or receive tokens.
 *
 *         Adding the zero address is forbidden so that mint/burn flows
 *         (which use address(0) as the counterparty) cannot be falsely
 *         attributed to a "real" allowlisted entity.
 */
contract ComplianceAllowlist is AccessControl {
    /// @dev address => allowlisted
    mapping(address => bool) private _allowed;

    /// @dev address => optional opaque reference (e.g. KYC/AML case ID hash).
    ///      We store only a hash on-chain; the off-chain compliance system
    ///      retains the underlying record. Never put PII on-chain.
    mapping(address => bytes32) private _referenceHash;

    uint256 private _allowedCount;

    event AddressAllowed(address indexed account, bytes32 referenceHash, address indexed by);
    event AddressRevoked(address indexed account, address indexed by);
    event ReferenceUpdated(address indexed account, bytes32 oldHash, bytes32 newHash, address indexed by);

    error ZeroAddress();
    error AlreadyAllowed(address account);
    error NotAllowed(address account);

    /**
     * @param admin Address that receives DEFAULT_ADMIN_ROLE. In production this
     *              MUST be the Timelock contract, never an EOA.
     */
    constructor(address admin) {
        if (admin == address(0)) revert ZeroAddress();
        _grantRole(Roles.DEFAULT_ADMIN_ROLE, admin);
        _grantRole(Roles.COMPLIANCE_ROLE, admin);
    }

    function isAllowed(address account) external view returns (bool) {
        return _allowed[account];
    }

    function referenceHashOf(address account) external view returns (bytes32) {
        return _referenceHash[account];
    }

    function allowedCount() external view returns (uint256) {
        return _allowedCount;
    }

    /**
     * @notice Add an address to the allowlist.
     * @param account The address being authorised.
     * @param referenceHash keccak256 of the off-chain compliance case
     *        identifier. Pass bytes32(0) only if no off-chain record exists,
     *        which should be vanishingly rare in production.
     */
    function allow(address account, bytes32 referenceHash) external onlyRole(Roles.COMPLIANCE_ROLE) {
        if (account == address(0)) revert ZeroAddress();
        if (_allowed[account]) revert AlreadyAllowed(account);
        _allowed[account] = true;
        _referenceHash[account] = referenceHash;
        unchecked {
            _allowedCount += 1;
        }
        emit AddressAllowed(account, referenceHash, _msgSender());
    }

    /**
     * @notice Bulk-add addresses. Reverts on first duplicate so partial
     *         success is impossible — caller deduplicates upstream.
     */
    function allowBatch(address[] calldata accounts, bytes32[] calldata referenceHashes)
        external
        onlyRole(Roles.COMPLIANCE_ROLE)
    {
        uint256 len = accounts.length;
        require(len == referenceHashes.length, "Allowlist: length mismatch");
        for (uint256 i = 0; i < len; i++) {
            address a = accounts[i];
            if (a == address(0)) revert ZeroAddress();
            if (_allowed[a]) revert AlreadyAllowed(a);
            _allowed[a] = true;
            _referenceHash[a] = referenceHashes[i];
            emit AddressAllowed(a, referenceHashes[i], _msgSender());
        }
        unchecked {
            _allowedCount += len;
        }
    }

    /**
     * @notice Remove an address. Existing balances are NOT clawed back —
     *         clawback requires a separate governance action.
     */
    function revoke(address account) external onlyRole(Roles.COMPLIANCE_ROLE) {
        if (!_allowed[account]) revert NotAllowed(account);
        _allowed[account] = false;
        // Reference hash is preserved deliberately for audit trail.
        unchecked {
            _allowedCount -= 1;
        }
        emit AddressRevoked(account, _msgSender());
    }

    /**
     * @notice Update the off-chain reference hash for an already-allowed
     *         address (e.g. when the compliance case is re-reviewed).
     */
    function updateReference(address account, bytes32 newHash) external onlyRole(Roles.COMPLIANCE_ROLE) {
        if (!_allowed[account]) revert NotAllowed(account);
        bytes32 old = _referenceHash[account];
        _referenceHash[account] = newHash;
        emit ReferenceUpdated(account, old, newHash, _msgSender());
    }
}
