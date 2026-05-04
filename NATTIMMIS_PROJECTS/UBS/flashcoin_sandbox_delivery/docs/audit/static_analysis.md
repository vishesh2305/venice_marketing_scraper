# Static Analysis — Slither + solhint

## Tool versions

| Tool | Pinned version | Where |
|---|---|---|
| solhint | 5.x | `package.json` |
| slither (CI) | crytic/slither-action@v0.4.0 | `.github/workflows/security.yml` |
| solc | 0.8.21 | `tronbox-config.js`, `hardhat.config.js` |
| optimizer runs | 200 | both configs |

## solhint configuration

`.solhint.json` extends `solhint:recommended`, with project-specific
relaxations and an explicit error on `compiler-version` to prevent a
floating pragma from silently advancing.

## Slither configuration

`slither.config.json`:

* `filter_paths` excludes `node_modules`, `test`, and `contracts/stress`
  (the FlashCoin stress harness has deliberate anti-patterns and is
  audited separately).
* All severities are visible (no `exclude_*`).
* `solc_remaps` points at the OpenZeppelin install.

## Expected findings

| Detector | Severity | Status |
|---|---|---|
| `pragma-version` | informational | suppressed by pinning |
| `solc-version` | informational | suppressed by pinning |
| `naming-convention` (constants in mixedCase) | informational | accepted on OZ-style role names |
| `low-level-calls` | informational | none in our code |
| `reentrancy-eth` | n/a | no native value transfers |
| `reentrancy-no-eth` | low | mitigated by `nonReentrant` on mint/burn paths |

## Reading the CI artefact

The slither GitHub action attaches `slither-report.md` to every run.
Compare against the previous `main` build's report; any **new** finding
≥ medium blocks the merge (configured via `fail-on: medium`).

## Manual review additions

Items that are not automatable and are part of the security review
checklist:

* Diff review for any change in `_beforeTokenTransfer` — the allowlist
  hook is the single most security-sensitive code path.
* Diff review for any change in role identifiers in `Roles.sol`. A typo
  in a role string is an undetectable governance bug.
* Diff review for any Timelock parameter change in `migrations/2_deploy_governance.js`.
