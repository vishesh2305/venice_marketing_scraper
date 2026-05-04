// SPDX-License-Identifier: MIT
pragma solidity ^0.8.21;

/**
 * @title ITRC20
 * @notice TRC20 standard interface. ABI-compatible with ERC20, which is what
 *         the TRON Virtual Machine (TVM) expects from a TRC20 token. The
 *         interface is identical to ERC20 — TRC20 differs only in the deploy
 *         and runtime environment, not the function set.
 *
 *         All settlement-track integrations (TronGrid event listeners,
 *         exchange connectors, custody vendors) are written against this
 *         interface. Any change here is a breaking API change and requires
 *         a governance proposal.
 */
interface ITRC20 {
    function totalSupply() external view returns (uint256);
    function balanceOf(address account) external view returns (uint256);
    function transfer(address to, uint256 amount) external returns (bool);
    function allowance(address owner, address spender) external view returns (uint256);
    function approve(address spender, uint256 amount) external returns (bool);
    function transferFrom(address from, address to, uint256 amount) external returns (bool);

    event Transfer(address indexed from, address indexed to, uint256 value);
    event Approval(address indexed owner, address indexed spender, uint256 value);
}

/**
 * @title ITRC20Metadata
 * @notice Optional metadata extension. Wallets and explorers rely on this.
 */
interface ITRC20Metadata is ITRC20 {
    function name() external view returns (string memory);
    function symbol() external view returns (string memory);
    function decimals() external view returns (uint8);
}
