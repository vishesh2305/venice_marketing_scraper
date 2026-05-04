# Threat Model — STRIDE

Scope: the on-chain contracts (`InternalSettlementToken`, `ComplianceAllowlist`,
`SettlementTimelock`), the off-chain services (signer, indexer, reconciler,
stress simulator), and the human + procedural surface that controls them.

## Assumptions

A. The TRON Mainnet validator set is treated as trusted for liveness and
   safety. We do not model a hostile chain.
B. AWS KMS / HashiCorp Vault are treated as trusted for key custody. A
   compromise of the custodian is a catastrophic event and is handled by
   the incident-response runbook (`incident_response.md`), not by code.
C. Multi-sig signers' workstations are managed endpoints with FDE, MDM,
   YubiKey-bound SSO, and EDR. Phishing is in scope; uncontrolled malware
   on a signer's laptop is in scope.

## Asset inventory

| Asset | Where it lives | Loss impact |
|---|---|---|
| Multi-sig private key shares | KMS / Vault / YubiKeys | Existential — full system compromise |
| `MINTER_ROLE` operator key | KMS / Vault | High — unauthorised supply increase up to per-block rate limit |
| `PAUSER_ROLE` operator key | KMS / Vault | Medium — denial of service via pause |
| `COMPLIANCE_ROLE` operator key | KMS / Vault | High — unauthorised allowlisting |
| Indexer database | Postgres in prod | Medium — audit-trail integrity |
| Reconciler config + book CSV | Internal share | Medium — break detection bypass |

## Threats

| ID | Category | Threat | Mitigation | Residual risk |
|---|---|---|---|---|
| S-1 | Spoofing | Attacker submits a transaction impersonating a privileged role | Every state-changing function requires the role hash to be present on `msg.sender` (via `onlyRole`). Roles are granted only via Timelock + multi-sig. | Low — keys are HSM-bound. |
| S-2 | Spoofing | Allowlisted address is impersonated by an attacker after key theft | Allowlist applies to the current owner of the key, not the identity. Lost-key recovery: revoke address, re-allowlist new one, ceremonial burn-and-remint of stranded balance. Procedure in `incident_response.md`. | Low if HSM, Medium if soft key. |
| T-1 | Tampering | Indexer DB is tampered with to mask reconciliation breaks | Indexer is append-only; reconciler also reads on-chain `balanceOf` independently and compares. A doctored DB shows up as event/balance divergence. DB user has INSERT-only permissions; admin actions are audited. | Low. |
| T-2 | Tampering | Slither / solhint output is bypassed in CI | CI runs are reproducible; `security.yml` blocks merge on findings ≥ medium; `.github/CODEOWNERS` requires security team review on contracts/. | Low. |
| R-1 | Repudiation | Operator denies running a privileged action | KMS/Vault audit log records every `Sign` call with caller identity; on-chain emits a typed event with the role-bearing `msg.sender`. The two are reconcilable post hoc. | Very low. |
| I-1 | Information disclosure | PII appears on a public chain via the allowlist | The allowlist stores ONLY `keccak256(case_id)`, never the case ID itself. The off-chain compliance store is the source of identity. Reviewed in `key_management_policy.md` §6. | Negligible. |
| I-2 | Information disclosure | Mainnet private key leaks via developer laptop | EnvSigner refuses to sign mainnet (`signer.py: if ctx.network == "mainnet": raise`). Mainnet uses KMS exclusively. `.gitignore` blocks `.env` and `wallets.json`. | Low. |
| D-1 | Denial of service | Pauser key is compromised and pauses indefinitely | PAUSER_ROLE is held by m-of-n on-call signers. Admin can revoke any individual pauser via Timelock. | Low. |
| D-2 | Denial of service | Mint cap exhausted by hostile mint within rate limit | Per-block rate limit caps blast radius of a compromised minter. Once detected, PAUSER stops transfers; cap reached without governance intent triggers an incident. | Medium. |
| E-1 | Elevation of privilege | Bug in `_beforeTokenTransfer` skips allowlist | Defence in depth: pause check, allowlist check, role check on mint/burn. Unit tests cover non-allowlisted transfer reverts in three locations. | Low. |
| E-2 | Elevation of privilege | Re-entrancy from a malicious downstream caller | `mint`, `burn`, `burnFrom` carry `nonReentrant`. ERC20 internal `_transfer` uses checks-effects-interactions. No external calls in the privileged path beyond the allowlist's `isAllowed` (a view function). | Low. |
| E-3 | Elevation of privilege | Owner-key recovery path used as a backdoor | There is **no recovery path**. Lost admin = the system migrates to v2. This is an explicit design tradeoff documented in `smart_contract_risks.md` §4. | Accepted. |

## Out of model (with rationale)

* **Validator collusion on TRON Mainnet** — a non-byzantine fault we treat
  as a force-majeure incident, not a coding problem. Contingency in
  `incident_response.md`.
* **Smart-contract upgrades** — there are none, deliberately. So upgrade-
  pattern attacks (storage collision, init re-run, proxy admin takeover)
  are not applicable.
* **Reentrancy via `transferFrom` callbacks** — TRC20 has no callback
  hooks (unlike ERC777). Verified in tests.

## Periodic review

This document is reviewed every quarter, and within 5 working days of:

* Any change to a privileged code path.
* Any addition or removal of a role.
* Any incident classified ≥ severity 3.
* Any change to the multi-sig roster.

Last reviewed: see git history of this file.
