# Contributing

This repository operates under institutional-banking change-management
discipline. Read this in full before opening your first PR.

## Branch model

* `main` is the deployable branch. Every commit on `main` corresponds to
  a state that has passed CI + security scans + 2 CODEOWNERS approvals.
* `develop` (optional) is the integration branch for in-flight work.
  Merges from `develop` to `main` require a release note in
  `CHANGELOG.md`.
* Feature branches: `feat/<scope>-<short-name>` or
  `fix/<scope>-<short-name>`.

## Commit hygiene

* Commits are GPG-signed. `git commit -S` (or set
  `commit.gpgsign = true` globally). The bank's GitHub Enterprise rejects
  unsigned commits on `main`.
* Subject line: imperative, ≤ 72 chars, scoped:
  `contracts: enforce per-block mint rate limit`.
* Body: explain the *why*. The diff explains the *what*.
* Reference the CR ticket: `Refs: CR-1234`.
* No `--no-verify`. If the pre-commit hook fails, fix the underlying
  issue.

## PR checklist

Every PR must:

- [ ] Be linked to a CR ticket.
- [ ] Pass `ci.yml` and `security.yml`.
- [ ] Have ≥ 1 CODEOWNERS approval (≥ 2 for `contracts/`,
      `migrations/`, `services/keymanagement/`, `.github/`).
- [ ] Update tests if a privileged code path changes.
- [ ] Update docs if a documented behaviour changes.
- [ ] Have a `## Test plan` section in the description.

## Solidity style

* Pinned to `solc 0.8.21`. Do not change without a security-team review.
* `pragma solidity ^0.8.21;` at the top of every file.
* Custom errors over `require` strings for new code.
* NatSpec on every public/external function; minimal NatSpec on internal
  functions where the *why* is non-obvious.
* No `selfdestruct`, no inline assembly without a CODEOWNERS approval
  noting the justification.

## Python style

* Python 3.11+. `ruff check services/` must pass.
* Type hints on public surfaces.
* Logging via the `logging` module, not `print`.

## When NOT to open a PR here

* Hot-fixes to mainnet that cannot wait for the Timelock delay → see
  `docs/security/incident_response.md`. The pause is the immediate
  control. Code changes still go through this PR process.
* Documentation changes that touch `docs/governance/multisig_roster.md`
  → those go through the multi-sig itself, not a PR.
* Anything classified above the bank's standard "internal" tier — file
  it in the secure document store, not here.

## What gets blocked

Branch protection blocks:

* Direct push to `main`.
* Force-push to `main`.
* Merges without required reviews.
* Merges with red CI / security checks.
* Unsigned commits on `main`.

We do not enable a "skip checks" admin override. If a check is broken,
we fix the check.
