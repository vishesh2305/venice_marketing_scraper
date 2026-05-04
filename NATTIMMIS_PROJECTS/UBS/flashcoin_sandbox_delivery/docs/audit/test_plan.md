# Test Plan

The test suite is the gating control for any merge to `main`. It is
designed for two consumers: the engineer making a change (fast feedback)
and the auditor reading post hoc (every privileged path is exercised).

## Test taxonomy

| Layer | Tool | Source | What it covers |
|---|---|---|---|
| Unit — token | Hardhat + Mocha + Chai | `test/unit/token.test.js` | TRC20 surface, mint, burn, pause |
| Unit — access | Hardhat | `test/unit/access.test.js` | Role independence, admin cannot move balances |
| Unit — compliance | Hardhat | `test/unit/compliance.test.js` | Allowlist correctness and gating |
| Integration — lifecycle | Hardhat | `test/integration/lifecycle.test.js` | End-to-end mint→transfer→burnFrom→pause→resume + rate-limit + cap |
| Static — solhint | npm script | `.solhint.json` | Style + safety rules on `contracts/` |
| Static — slither | crytic/slither-action | `slither.config.json` | Known anti-patterns |
| Secret scan — gitleaks | GitHub Action | `.gitleaks.toml` | Block keys / mnemonics / TronGrid keys |
| Coverage | solidity-coverage | hardhat coverage | Line / branch coverage |

## Coverage targets

* Line coverage ≥ 95% on `contracts/` (excluding `Migrations.sol`,
  `contracts/stress/`).
* Branch coverage ≥ 90%.
* Every `revert` / `require` reachable from a test.

## Required negative tests

For every privileged function, a test asserts that calling it without the
required role reverts. For every check (`require`, `revert`), at least one
test that triggers the check.

| Function | Negative tests present | Source |
|---|---|---|
| `mint` | non-allowlisted recipient, no role, mint cap, rate limit, zero address | `token.test.js` |
| `burn` | no role, insufficient balance | `token.test.js` |
| `burnFrom` | no role, no allowance | `token.test.js` |
| `pause` | no role | `token.test.js` |
| `setAllowlist` | no role, zero address | `compliance.test.js` |
| `setAllowlistEnforced` | no role | `compliance.test.js` |
| `allowlist.allow` | no role, zero address, double-allow | `compliance.test.js` |
| `allowlist.revoke` | no role, not allowed | `compliance.test.js` |

## Fuzz / property tests

Out of scope for v0.1. Planned for v0.2 with a foundry-equivalent
property-test harness (TODO `OPEN-TEST-1`):

* Property: `totalSupply == sum(balanceOf) over all addresses`.
* Property: `mintedInBlock(b) <= mintRateLimitPerBlock for all b`.
* Property: `paused() == false implies _beforeTokenTransfer never reverts on allowlisted parties`.

## Manual test cases

These tests are part of release acceptance and are not automated:

1. Tronbox compile + Shasta deploy clean (no warnings).
2. Tronbox migrate `--reset` runs all four migrations to completion.
3. `node scripts/verify.js --network shasta` returns all-PASS.
4. Demo lifecycle script runs end-to-end (`scripts/demo.sh`).

## CI gating

`.github/workflows/ci.yml` runs compile + unit + integration + coverage.
`.github/workflows/security.yml` runs slither + gitleaks + dependency
review. A merge to `main` requires both green, plus 2 CODEOWNERS approvals
on any change to `contracts/`, `migrations/`, or `services/keymanagement/`.
