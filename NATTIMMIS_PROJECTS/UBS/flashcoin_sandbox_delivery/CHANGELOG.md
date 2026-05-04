# Changelog

All notable changes to the IST infrastructure are recorded here. Format
follows Keep-a-Changelog. The repository adheres to semantic versioning
once a `v1.0.0` is cut on mainnet.

## [Unreleased]

### Added

* `contracts/InternalSettlementToken.sol` — institutional TRC20 with
  AccessControl, Pausable, ReentrancyGuard, mint cap, per-block rate
  limit, allowlist gate.
* `contracts/access/ComplianceAllowlist.sol` — per-address registry.
* `contracts/access/Roles.sol` — closed role enumeration.
* `contracts/governance/Timelock.sol` — OZ TimelockController.
* Tronbox migrations (1..4) including post-deploy verification.
* Hardhat test suite — unit + integration; coverage ≥ 95% line.
* `services/keymanagement/signer.py` — env / AWS KMS / Vault adapters.
* `services/indexer/` — TronGrid event poller into SQL.
* `services/reconciliation/` — three-way reconciliation.
* CI: `ci.yml` (compile + test + coverage + ruff) and `security.yml`
  (slither + gitleaks + dependency review).
* `.github/CODEOWNERS` and branch-protection guidance.
* Full doc set in `docs/` covering architecture, security, governance,
  operations, audit, deployment, demo, and the diligence response.

### Changed

* `contracts/stress/FlashCoin.sol` — repositioned from "the deliverable"
  to "stress-harness counterpart, testnet-only". Header comment updated.
* `services/stress/simulator.py` — moved from `simulator/` and
  repositioned as the SOC stress tool. Mainnet refusal preserved.

### Removed

* Broken `truffle-config.js` (had a syntax error and pointed at
  Ethereum/Infura).
* Stale `build/contracts/FlashCoin.json` artefact.
* Empty `simulator/` directory.

### Fixed

* `package.json` — replaced bare `bip39` + `dotenv` with full Hardhat /
  tronbox / OpenZeppelin / solhint dependency set.

## v0.0.1 (legacy)

* Pre-restructure: red-team fraud-detection sandbox with FlashCoin TRC20
  on Shasta. Retired in favour of the institutional structure above.
