// SPDX-License-Identifier: MIT
pragma solidity ^0.8.21;

import "@openzeppelin/contracts/token/ERC20/ERC20.sol";
import "@openzeppelin/contracts/security/Pausable.sol";
import "@openzeppelin/contracts/security/ReentrancyGuard.sol";
import "@openzeppelin/contracts/access/AccessControl.sol";

import "./access/Roles.sol";
import "./access/ComplianceAllowlist.sol";

/**
 * @title InternalSettlementToken (IST)
 * @notice Institutional TRC20 settlement-simulation asset deployed to TRON.
 *
 *         This is NOT a public-facing token. It is an internal instrument
 *         used by Treasury and Operations to model tokenised settlement
 *         flows under controlled conditions, with the same on-chain
 *         primitives as a production stablecoin would use.
 *
 *         Design principles:
 *
 *           1. Least privilege. Every privileged action requires a specific
 *              role. The DEFAULT_ADMIN_ROLE is held by the Timelock, never
 *              an EOA. See docs/governance/role_assignment.md.
 *
 *           2. Defence in depth. Compliance allowlist + role gating + per-
 *              block rate limit + global mint cap + Pausable + ReentrancyGuard.
 *              No single failure should permit unauthorised value movement.
 *
 *           3. Auditability. Every state transition emits a typed event.
 *              Off-chain reconciliation reads the event stream — never the
 *              storage slots — so the audit trail is the source of truth.
 *
 *           4. Reversibility of governance, not of state. We deliberately
 *              do NOT use a proxy pattern. Bug fixes ship as v2 with a
 *              ceremonial mint/burn migration. This trades upgrade ergonomics
 *              for a much cleaner audit posture and is the same model used
 *              by USDC. See docs/security/smart_contract_risks.md §4.
 *
 *           5. No backdoors. There is no owner override that can move funds
 *              without the corresponding role. Even DEFAULT_ADMIN_ROLE
 *              cannot transfer balances — it can only grant roles.
 */
contract InternalSettlementToken is ERC20, AccessControl, Pausable, ReentrancyGuard {
    /// @notice Compliance allowlist consulted on every transfer.
    ComplianceAllowlist public allowlist;

    /// @notice Maximum total supply. Once reached, mint() reverts.
    uint256 public immutable mintCap;

    /// @notice Cap on tokens minted within a single block. Limits blast
    ///         radius of a compromised MINTER_ROLE key.
    uint256 public mintRateLimitPerBlock;

    /// @dev block.number => tokens minted in that block.
    mapping(uint256 => uint256) private _mintedInBlock;

    /// @notice Whether the allowlist gate is enforced. Default: true. May
    ///         only be flipped by DEFAULT_ADMIN_ROLE (i.e. through the
    ///         Timelock + multi-sig). Disabling is logged loudly so SOC
    ///         can alert on it.
    bool public allowlistEnforced;

    event AllowlistChanged(address indexed previous, address indexed current);
    event AllowlistEnforcementChanged(bool enforced);
    event MintRateLimitChanged(uint256 previous, uint256 current);
    event Minted(address indexed to, uint256 amount, address indexed by);
    event Burned(address indexed from, uint256 amount, address indexed by);

    error ZeroAddress();
    error MintCapExceeded(uint256 requested, uint256 remaining);
    error MintRateLimitExceeded(uint256 requested, uint256 remainingThisBlock);
    error NotAllowlisted(address account);
    error InsufficientBalance(address account, uint256 requested, uint256 actual);

    /**
     * @param name_              Token name, e.g. "Internal Settlement Token".
     * @param symbol_            Token symbol, e.g. "IST".
     * @param mintCap_           Hard cap on total supply (in smallest units).
     * @param rateLimitPerBlock_ Per-block mint cap.
     * @param admin              Address that receives DEFAULT_ADMIN_ROLE.
     *                           MUST be the Timelock in production.
     * @param allowlistAddr      Deployed ComplianceAllowlist.
     */
    constructor(
        string memory name_,
        string memory symbol_,
        uint256 mintCap_,
        uint256 rateLimitPerBlock_,
        address admin,
        address allowlistAddr
    ) ERC20(name_, symbol_) {
        if (admin == address(0)) revert ZeroAddress();
        if (allowlistAddr == address(0)) revert ZeroAddress();
        require(mintCap_ > 0, "IST: mintCap must be > 0");
        require(rateLimitPerBlock_ > 0, "IST: rateLimit must be > 0");

        mintCap = mintCap_;
        mintRateLimitPerBlock = rateLimitPerBlock_;
        allowlist = ComplianceAllowlist(allowlistAddr);
        allowlistEnforced = true;

        _grantRole(Roles.DEFAULT_ADMIN_ROLE, admin);
        // No other roles are seeded here. They are granted by the admin
        // (Timelock) via post-deploy migrations. See migrations/3_grant_roles.js.
    }

    /// @notice TRC20/ERC20 default is 18; for an institutional settlement
    ///         token we use 6 so amounts read naturally next to USD-denominated
    ///         fiat tickets. Override is intentional and documented.
    function decimals() public pure override returns (uint8) {
        return 6;
    }

    // =========================================================================
    //  Mint / Burn — the only paths that change total supply.
    // =========================================================================

    /**
     * @notice Mint new tokens to an allowlisted recipient.
     * @dev Subject to global cap, per-block rate limit, allowlist, and
     *      Pausable. Caller must hold MINTER_ROLE.
     */
    function mint(address to, uint256 amount)
        external
        whenNotPaused
        nonReentrant
        onlyRole(Roles.MINTER_ROLE)
    {
        if (to == address(0)) revert ZeroAddress();
        if (allowlistEnforced && !allowlist.isAllowed(to)) revert NotAllowlisted(to);

        uint256 newSupply = totalSupply() + amount;
        if (newSupply > mintCap) {
            revert MintCapExceeded(amount, mintCap - totalSupply());
        }

        uint256 mintedThisBlock = _mintedInBlock[block.number];
        if (mintedThisBlock + amount > mintRateLimitPerBlock) {
            revert MintRateLimitExceeded(amount, mintRateLimitPerBlock - mintedThisBlock);
        }
        _mintedInBlock[block.number] = mintedThisBlock + amount;

        _mint(to, amount);
        emit Minted(to, amount, _msgSender());
    }

    /**
     * @notice Burn tokens from caller's own balance.
     * @dev Caller must hold BURNER_ROLE. Used by the redemption service
     *      when an internal entity is redeeming IST for the off-chain
     *      counterparty asset.
     */
    function burn(uint256 amount) external whenNotPaused nonReentrant onlyRole(Roles.BURNER_ROLE) {
        uint256 bal = balanceOf(_msgSender());
        if (bal < amount) revert InsufficientBalance(_msgSender(), amount, bal);
        _burn(_msgSender(), amount);
        emit Burned(_msgSender(), amount, _msgSender());
    }

    /**
     * @notice Burn tokens from `from` using allowance — clawback path.
     * @dev Caller must hold BURNER_ROLE. The token holder must have approved
     *      the burner. This intentionally mirrors ERC20.transferFrom semantics
     *      so it inherits ERC20's allowance accounting.
     */
    function burnFrom(address from, uint256 amount)
        external
        whenNotPaused
        nonReentrant
        onlyRole(Roles.BURNER_ROLE)
    {
        if (from == address(0)) revert ZeroAddress();
        _spendAllowance(from, _msgSender(), amount);
        _burn(from, amount);
        emit Burned(from, amount, _msgSender());
    }

    // =========================================================================
    //  Pause / unpause — emergency stop.
    // =========================================================================

    function pause() external onlyRole(Roles.PAUSER_ROLE) {
        _pause();
    }

    function unpause() external onlyRole(Roles.PAUSER_ROLE) {
        _unpause();
    }

    // =========================================================================
    //  Configurator surface — gated by Timelock-held DEFAULT_ADMIN_ROLE.
    // =========================================================================

    function setAllowlist(address newAllowlist) external onlyRole(Roles.DEFAULT_ADMIN_ROLE) {
        if (newAllowlist == address(0)) revert ZeroAddress();
        address prev = address(allowlist);
        allowlist = ComplianceAllowlist(newAllowlist);
        emit AllowlistChanged(prev, newAllowlist);
    }

    function setAllowlistEnforced(bool enforced) external onlyRole(Roles.DEFAULT_ADMIN_ROLE) {
        allowlistEnforced = enforced;
        emit AllowlistEnforcementChanged(enforced);
    }

    function setMintRateLimitPerBlock(uint256 newLimit) external onlyRole(Roles.DEFAULT_ADMIN_ROLE) {
        require(newLimit > 0, "IST: rateLimit must be > 0");
        uint256 prev = mintRateLimitPerBlock;
        mintRateLimitPerBlock = newLimit;
        emit MintRateLimitChanged(prev, newLimit);
    }

    // =========================================================================
    //  Transfer hook — enforces pause + allowlist on every flow path.
    // =========================================================================

    /**
     * @dev Called by ERC20 internal _transfer/_mint/_burn. Allowlist applies
     *      to non-zero counterparties only — mint (from = 0) and burn
     *      (to = 0) are governed by their respective role gates above.
     */
    function _beforeTokenTransfer(address from, address to, uint256 amount) internal override {
        super._beforeTokenTransfer(from, to, amount);
        require(!paused(), "IST: paused");
        if (allowlistEnforced) {
            if (from != address(0) && !allowlist.isAllowed(from)) revert NotAllowlisted(from);
            if (to != address(0) && !allowlist.isAllowed(to)) revert NotAllowlisted(to);
        }
    }

    // =========================================================================
    //  Introspection helpers — used by indexer and operator tooling.
    // =========================================================================

    function mintedInBlock(uint256 blockNumber) external view returns (uint256) {
        return _mintedInBlock[blockNumber];
    }

    function remainingMintCap() external view returns (uint256) {
        return mintCap - totalSupply();
    }
}
