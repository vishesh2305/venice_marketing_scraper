# Security Policy

## Reporting a vulnerability

If you find a security issue in this repository:

* **Do not** open a public issue on the host (GitHub Enterprise) or
  mention it in any PR description.
* Email `security@<bank-domain>` with subject prefix `[IST]`.
* For high-severity issues affecting mainnet, also page the on-call
  Security Lead per `docs/operations/on_call.md`.

We acknowledge within 1 business day. We respond with a triage and ETA
within 5 business days.

## Scope

In scope:

* The Solidity contracts under `contracts/` (excluding
  `contracts/stress/`, which is testnet-only and deliberately abusable).
* The off-chain services under `services/` — particularly the signer
  adapters in `services/keymanagement/`.
* The deployment scripts under `scripts/` and `migrations/`.
* The CI configuration under `.github/`.

Out of scope:

* OpenZeppelin contracts pulled in via `node_modules/@openzeppelin/`.
  Vulnerabilities in those are reported upstream to OpenZeppelin per
  their own policy.
* Third-party RPC / event APIs (TronGrid). Those are reported to TRON
  upstream.
* Issues in test fixtures unless they reflect a real production code
  path.

## Threat model

The full STRIDE threat model is in `docs/security/threat_model.md`. The
risk register is in `docs/security/smart_contract_risks.md`.

## Coordinated disclosure

If you are an external researcher and we ask you to delay disclosure
while we deploy a fix, we will:

* Confirm a fix timeline within 5 business days of acknowledgement.
* Credit you in the postmortem if you wish (`docs/security/postmortems/`).
* Not pursue legal action for good-faith research within scope.

## What we will NOT do

* We will not pay bug bounties out of this engagement (no programme is
  attached). We will credit; we cannot pay from this scope.
* We will not silently patch a critical issue. Every fix to a privileged
  code path emits a `CHANGELOG.md` entry and a Timelock proposal record.
