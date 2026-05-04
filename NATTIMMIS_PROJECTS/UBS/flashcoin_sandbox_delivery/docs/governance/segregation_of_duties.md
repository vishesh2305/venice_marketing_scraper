# Segregation of Duties

The four-eyes principle as it applies to the IST infrastructure.

## Hard rules

These cannot be relaxed without a multi-sig roster change:

1. **No single human can mint and allowlist.** The minter service and the
   compliance service are separate accounts in separate KMS keys held by
   separate teams. Verified at deploy time and re-verified by the daily
   reconciliation pass.
2. **No single human can pause and unpause from the same workstation in a
   single session.** SOC enforces this procedurally; the on-call rotation
   moves at least every 24h.
3. **Pull requests touching `contracts/`, `migrations/`, or
   `services/keymanagement/` require two CODEOWNERS approvals.** Enforced
   by branch protection + `.github/CODEOWNERS`.
4. **Timelock proposals are reviewed by a different signer than the one
   who authored them.** The PROPOSER and the four-eyes COUNTER-SIGNER are
   distinct multi-sig members. The COUNTER-SIGNER reviews the off-chain
   payload (`scripts/grant_roles.js` output) against the CR before
   broadcast.
5. **CI deploy keys are different from operator keys.** CI's testnet
   deploy key cannot sign mainnet (`signer.py:EnvSigner` refuses).
6. **No commit to `main` without a green build.** Branch protection
   requires `ci.yml` and `security.yml` checks to pass.

## Worked example: legitimate mint of 10,000 IST to a new counterparty

| Step | Actor | Control |
|---|---|---|
| 1 | Treasury Ops files CR-1234 with the requested mint | Internal CR system |
| 2 | Compliance reviews the new counterparty against KYC | Compliance system |
| 3 | Compliance signs `allowlist.allow(addr, hash)` (allowlist already governed by Timelock for new principals; for already-allowed addresses, COMPLIANCE_ROLE acts directly) | KMS audit log |
| 4 | Treasury issuance service signs `token.mint(addr, amount)` | KMS audit log |
| 5 | Indexer observes both events and writes them | Indexer DB |
| 6 | Reconciler asserts event-derived balance == on-chain balance == internal book | Reconciliation pass |
| 7 | Internal Audit reviews the matched CR / KMS-audit / on-chain triplet | Quarterly review |

Each row is a different actor (or service account), and every transition
is observable from at least two independent sources.

## What if the bank is small enough that the same person is on multiple
teams?

The hard rules are about *which key signs*, not which body sits in which
chair. As long as the keys are separate, the audit trail is clean. We
recommend that even a small team route every mint through a service
account whose key only the on-call holds, separate from any human's
personal credentials.

## Enforcement

* Daily: reconciler verifies no event was signed by a key that holds an
  incompatible role pair (verified by replaying KMS audit + role grants).
* Quarterly: Internal Audit samples 10% of CRs and walks the chain end-to-end.
* On incident: forensic snapshot includes the KMS audit log so role-pair
  violations can be detected post hoc.
