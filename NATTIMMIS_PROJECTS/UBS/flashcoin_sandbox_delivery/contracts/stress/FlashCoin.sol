// SPDX-License-Identifier: MIT
// =============================================================================
//  STRESS HARNESS — TESTNET ONLY
//
//  FlashCoin (stress harness)
//
//  Role within the system
//      This is the *stress counterparty* used to exercise the InternalSettlement
//      Token (IST) monitoring, indexing, reconciliation, and incident-response
//      pipeline. It is deliberately abusable — no per-user cap, short cooldown,
//      optional minting, rapid-transfer detection events — so the SOC team has
//      a signal to alert on while validating their detection rules.
//
//      It is NOT the institutional asset. The institutional asset is
//      contracts/InternalSettlementToken.sol, governed by a Timelock and
//      multi-sig. FlashCoin is intentionally separate so an audit reviewer can
//      see at a glance which contract is which.
//
//  Deployment scope
//      * Shasta / Nile testnet, or a local tron-quickstart / java-tron node.
//      * Must NEVER be deployed to TRON mainnet.
//      * The off-chain stress simulator (services/stress/simulator.py) refuses
//        to point at mainnet by default — see its safety guard.
//
//  Audit posture
//      Every abuse vector here is deliberate. Slither / solhint findings on
//      this file are EXPECTED. The slither config (slither.config.json)
//      excludes this file from the institutional audit gate; it is reviewed
//      separately as part of test-tooling.
// =============================================================================
pragma solidity ^0.8.6;

contract FlashCoin {
    // ---------------------------------------------------------------------
    // TRC20 metadata
    // ---------------------------------------------------------------------
    string public constant name     = "FlashCoin (TEST)";
    string public constant symbol   = "FLASH";
    uint8  public constant decimals = 6;

    // ---------------------------------------------------------------------
    // TRC20 storage
    // ---------------------------------------------------------------------
    uint256 private _totalSupply;
    mapping(address => uint256) private _balances;
    mapping(address => mapping(address => uint256)) private _allowances;

    // ---------------------------------------------------------------------
    // Simulation controls
    // ---------------------------------------------------------------------
    address public owner;
    bool    public distributionActive;   // gate for claimTranche()
    bool    public enableMinting;        // true -> mint on claim, false -> draw from owner
    uint256 public trancheSize;          // amount per claim (raw units, includes decimals)
    uint256 public cooldown;             // seconds between claims per wallet
    mapping(address => uint256) public lastClaim;

    // Rapid-transfer heuristic (best-effort, per block)
    uint256 public rapidTransferThreshold = 5;
    mapping(address => uint256) private _lastTransferBlock;
    mapping(address => uint256) private _transfersInBlock;

    // ---------------------------------------------------------------------
    // Events
    // ---------------------------------------------------------------------
    event Transfer(address indexed from, address indexed to, uint256 value);
    event Approval(address indexed owner, address indexed spender, uint256 value);

    event TrancheClaimed(address indexed claimer, uint256 amount, uint256 timestamp);
    event Minted(address indexed to, uint256 amount);
    event RapidTransferDetected(address indexed from, uint256 countInBlock, uint256 blockNumber);
    event DistributionStarted(uint256 timestamp);
    event DistributionStopped(uint256 timestamp);
    event TrancheSizeChanged(uint256 newSize);
    event CooldownChanged(uint256 newCooldown);
    event MintingToggled(bool enabled);
    event OwnershipTransferred(address indexed from, address indexed to);

    modifier onlyOwner() {
        require(msg.sender == owner, "FlashCoin: not owner");
        _;
    }

    // ---------------------------------------------------------------------
    // Constructor
    //   Initial supply: 200,000,000 FLASH (with 6 decimals).
    //   Default tranche: 1,000 FLASH every 60s — intentionally abusive.
    // ---------------------------------------------------------------------
    constructor() {
        owner              = msg.sender;
        _totalSupply       = 200_000_000 * 10 ** uint256(decimals);
        _balances[owner]   = _totalSupply;
        trancheSize        = 1_000 * 10 ** uint256(decimals);
        cooldown           = 60;    // 1 minute. NOT 1 day — this is a test token.
        distributionActive = false;
        enableMinting      = false;

        emit Transfer(address(0), owner, _totalSupply);
    }

    // =====================================================================
    // TRC20 view functions
    // =====================================================================
    function totalSupply() external view returns (uint256)            { return _totalSupply; }
    function balanceOf(address a) external view returns (uint256)     { return _balances[a]; }
    function allowance(address o, address s) external view returns (uint256) { return _allowances[o][s]; }

    // =====================================================================
    // TRC20 state-changing
    // =====================================================================
    function transfer(address to, uint256 amount) external returns (bool) {
        _transfer(msg.sender, to, amount);
        return true;
    }

    function approve(address spender, uint256 amount) external returns (bool) {
        _allowances[msg.sender][spender] = amount;
        emit Approval(msg.sender, spender, amount);
        return true;
    }

    function transferFrom(address from, address to, uint256 amount) external returns (bool) {
        uint256 allowed = _allowances[from][msg.sender];
        require(allowed >= amount, "FlashCoin: allowance exceeded");
        if (allowed != type(uint256).max) {
            _allowances[from][msg.sender] = allowed - amount;
            emit Approval(from, msg.sender, _allowances[from][msg.sender]);
        }
        _transfer(from, to, amount);
        return true;
    }

    function _transfer(address from, address to, uint256 amount) internal {
        require(to != address(0), "FlashCoin: transfer to zero");
        require(_balances[from] >= amount, "FlashCoin: insufficient balance");

        unchecked {
            _balances[from] -= amount;
            _balances[to]   += amount;
        }

        // Best-effort rapid-transfer heuristic. Note: tron blocks are short
        // (~3s), so a burst inside one block is a meaningful signal.
        if (_lastTransferBlock[from] == block.number) {
            _transfersInBlock[from] += 1;
            if (_transfersInBlock[from] >= rapidTransferThreshold) {
                emit RapidTransferDetected(from, _transfersInBlock[from], block.number);
            }
        } else {
            _lastTransferBlock[from] = block.number;
            _transfersInBlock[from]  = 1;
        }

        emit Transfer(from, to, amount);
    }

    // =====================================================================
    // Tranche / distribution
    //   No per-user cap. Short cooldown. This is deliberately abusable so the
    //   back-end under test has something to alert on.
    // =====================================================================
    function claimTranche() external {
        require(distributionActive, "FlashCoin: distribution inactive");
        require(block.timestamp >= lastClaim[msg.sender] + cooldown, "FlashCoin: cooldown");

        lastClaim[msg.sender] = block.timestamp;

        if (enableMinting) {
            _totalSupply         += trancheSize;
            _balances[msg.sender] += trancheSize;
            emit Minted(msg.sender, trancheSize);
            emit Transfer(address(0), msg.sender, trancheSize);
        } else {
            require(_balances[owner] >= trancheSize, "FlashCoin: owner pool drained");
            unchecked {
                _balances[owner]      -= trancheSize;
                _balances[msg.sender] += trancheSize;
            }
            emit Transfer(owner, msg.sender, trancheSize);
        }

        emit TrancheClaimed(msg.sender, trancheSize, block.timestamp);
    }

    // =====================================================================
    // Owner controls
    // =====================================================================
    function startDistribution() external onlyOwner {
        distributionActive = true;
        emit DistributionStarted(block.timestamp);
    }

    function stopDistribution() external onlyOwner {
        distributionActive = false;
        emit DistributionStopped(block.timestamp);
    }

    function setTrancheSize(uint256 newSize) external onlyOwner {
        trancheSize = newSize;
        emit TrancheSizeChanged(newSize);
    }

    function setCooldown(uint256 newCooldownSeconds) external onlyOwner {
        cooldown = newCooldownSeconds;
        emit CooldownChanged(newCooldownSeconds);
    }

    function toggleMinting() external onlyOwner {
        enableMinting = !enableMinting;
        emit MintingToggled(enableMinting);
    }

    function setRapidTransferThreshold(uint256 n) external onlyOwner {
        rapidTransferThreshold = n;
    }

    function mint(address to, uint256 amount) external onlyOwner {
        require(enableMinting, "FlashCoin: minting disabled");
        require(to != address(0), "FlashCoin: mint to zero");
        _totalSupply      += amount;
        _balances[to]     += amount;
        emit Minted(to, amount);
        emit Transfer(address(0), to, amount);
    }

    function transferOwnership(address newOwner) external onlyOwner {
        require(newOwner != address(0), "FlashCoin: zero owner");
        address prev = owner;
        owner = newOwner;
        emit OwnershipTransferred(prev, newOwner);
    }

    // Convenience: bulk-fund many wallets from owner (used by the simulator
    // to seed Sybil wallets quickly without paying many on-chain claims).
    function bulkTransfer(address[] calldata recipients, uint256 amountEach) external onlyOwner {
        uint256 total = amountEach * recipients.length;
        require(_balances[msg.sender] >= total, "FlashCoin: insufficient for bulk");
        for (uint256 i = 0; i < recipients.length; i++) {
            address r = recipients[i];
            require(r != address(0), "FlashCoin: zero recipient");
            unchecked {
                _balances[msg.sender] -= amountEach;
                _balances[r]          += amountEach;
            }
            emit Transfer(msg.sender, r, amountEach);
        }
    }
}
