# Internal Settlement Token (IST) — TRON Mainnet Infrastructure

> **Status: pre-mainnet.** Code is on Shasta; mainnet promotion is gated on
> the preflight checklist in [`docs/deployment/preflight_checklist.md`](docs/deployment/preflight_checklist.md).
>
> **Audience.** Internal banking engineering, security, compliance, and
> internal-audit teams. This is not a public deliverable. Do not share
> outside the engagement.

The Internal Settlement Token (IST) is an institutional TRC20 deployed (or
planned) on TRON Mainnet, used by Treasury, Operations, and Risk to model
tokenised settlement flows on-chain under controlled conditions. It uses
production primitives — real on-chain execution, multi-sig governance,
HSM-backed signing — and operates within an institutional allowlist so that
it cannot be confused with any externally-issued asset.

---

## Read this first

If you are reviewing this engagement: start at
[`docs/diligence/response_to_tdd.md`](docs/diligence/response_to_tdd.md).
That document responds point-by-point to the client's Internal Technical
Due Diligence Review and indexes everything else in this repository.

---

## Repository layout

```
contracts/
  InternalSettlementToken.sol     Institutional TRC20 (TRC20 + AccessControl + Pausable + cap + rate limit)
  ComplianceAllowlist.sol         (under access/)  Per-address compliance registry
  Roles.sol                       (under access/)  Closed role enumeration
  governance/Timelock.sol         OZ TimelockController (48h delay on mainnet)
  Migrations.sol                  Tronbox migration tracker
  stress/FlashCoin.sol            TESTNET-ONLY abuse counterparty for SOC drills

migrations/
  1_initial_migration.js          Tronbox bootstrap
  2_deploy_governance.js          Deploys Timelock + Allowlist
  3_deploy_token.js               Deploys IST with Timelock as DEFAULT_ADMIN_ROLE
  4_post_deploy_verify.js         Asserts on-chain invariants

services/
  keymanagement/signer.py         Signer abstraction: env / AWS KMS / HashiCorp Vault
  indexer/                        TronGrid event poller; append-only SQL store
  reconciliation/                 Three-way: events <-> on-chain balance <-> internal book
  stress/                         Refactored stress simulator (testnet-only)

scripts/
  verify.js                       Read-only post-deploy verification
  grant_roles.js                  Generates Timelock grantRole payload (off-chain only)
  demo.sh                         Live-demo end-to-end on Shasta
  demo_lifecycle.js               Allowlist -> mint -> transfer -> pause cycle

test/
  unit/                           Token / access / compliance unit tests
  integration/                    End-to-end lifecycle and rate-limit tests
  helpers/fixtures.js             Shared deployment fixtures

docs/                             Full doc set — see docs/README.md
.github/                          CI (compile + test) and security (slither + gitleaks)
```

---

## Quickstart — read-only review

```bash
# 1. Install
npm ci

# 2. Compile + run the test suite (Hardhat)
npx hardhat compile
npx hardhat test

# 3. Static analysis
npx solhint 'contracts/**/*.sol'
# slither / gitleaks installed separately — see docs/audit/static_analysis.md
```

## Quickstart — Shasta testnet deploy

```bash
# .env: PK_SHASTA=<testnet key>
make migrate-shasta
make verify              # reads .env for TOKEN_ADDRESS_SHASTA et al.
```

## Quickstart — mainnet deploy

Mainnet deployment **requires the preflight checklist to be signed off**.
See [`docs/deployment/preflight_checklist.md`](docs/deployment/preflight_checklist.md)
and [`docs/deployment/staged_rollout.md`](docs/deployment/staged_rollout.md).

```bash
SIGNER_BACKEND=aws_kms KMS_KEY_ID_MAINNET=<id> \
  make migrate-mainnet
```

The `EnvSigner` adapter refuses to sign mainnet by code
(`services/keymanagement/signer.py`); mainnet is KMS-only.

---

## Repository conventions

* **Branch protection on `main`:** 2 CODEOWNERS approvals on
  `contracts/` / `migrations/` / `services/keymanagement/` / `.github/`,
  plus green `ci.yml` and `security.yml`. Configured at the GitHub level —
  see `.github/CODEOWNERS`.
* **Commits:** signed (`gpg.sign = true` enforced server-side). No
  `--no-verify`, no skipping hooks.
* **Secrets:** never committed. `.gitignore` blocks `.env`, `wallets.json`,
  `*.pem`, `*.key`. `gitleaks` runs on every PR and on a daily schedule.
* **Solidity:** `solc 0.8.21`, optimizer 200 runs, evmVersion `istanbul`.
  Pinned in both `tronbox-config.js` and `hardhat.config.js`.
* **Solhint:** extends `solhint:recommended`. See `.solhint.json`.

---

## Hosting

This directory should be moved to its own git repository on the bank's
GitHub Enterprise instance before any external review. The current
parent directory is a personal scratch space and is not appropriate for
the engagement.

```bash
# inside flashcoin_sandbox_delivery/
git init -b main
git add -A
git commit -S -m "Initial import of IST infrastructure"
git remote add origin <bank GitHub Enterprise URL>
git push -u origin main
```

The repository name `flashcoin_sandbox_delivery` is a legacy of the
previous engagement framing; on import to GitHub Enterprise the
recommended repository name is `internal-settlement-token`.

---

## Naming history

* Pre-restructure: this engagement was scoped as a "FlashCoin sandbox" —
  a TRC20 fraud-detection red-team simulator on Shasta testnet. That
  framing did not match the client's intent (TRON Mainnet internal token
  infrastructure). After the client's Internal Technical Due Diligence
  Review, the engagement was restructured into the institutional
  `InternalSettlementToken` defined here.
* `FlashCoin.sol` is preserved at `contracts/stress/` and reused as a
  testnet-only stress harness for the SOC alerting pipeline. It is
  excluded from the institutional audit gate (`slither.config.json`).

---

## Licence

UNLICENSED. Confidential, internal use only.
