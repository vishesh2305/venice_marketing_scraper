# Multi-sig Roster — Template

This document is the **template** for the production multi-sig roster.
The actual filled-in roster lives in the bank's secure document store
(NOT in this repo) and is referenced here by document ID. Names of
signers and their key custody material are not on git, by policy.

## Signing model

* `m-of-n` threshold, where `n = 5` and `m = 3` for the production
  multi-sig. Both values are configurable on day one and changeable only
  through the multi-sig itself (cannot be raised or lowered by an
  individual signer).
* Each signer holds:
  1. A YubiKey-resident secp256k1 key share, **and**
  2. A KMS-encrypted backup of the same share, escrowed under that
     signer's IAM identity.
* Loss of a YubiKey is recoverable from the KMS backup. Loss of both
  triggers the rotation procedure (`security/key_management_policy.md` §5).

## Production roster (filled in offline)

| Slot | Role / Title | Custody backend | KMS alias | YubiKey serial | Joined | Confidential record |
|---|---|---|---|---|---|---|
| 1 | Head of Treasury Engineering | KMS + YubiKey | alias/ist-multisig-1-mainnet | _redacted_ | _date_ | DOC-MS-001 |
| 2 | Head of Security Engineering | KMS + YubiKey | alias/ist-multisig-2-mainnet | _redacted_ | _date_ | DOC-MS-002 |
| 3 | Head of Compliance Technology | KMS + YubiKey | alias/ist-multisig-3-mainnet | _redacted_ | _date_ | DOC-MS-003 |
| 4 | Head of Internal Audit | KMS + YubiKey | alias/ist-multisig-4-mainnet | _redacted_ | _date_ | DOC-MS-004 |
| 5 | Head of Treasury Operations | KMS + YubiKey | alias/ist-multisig-5-mainnet | _redacted_ | _date_ | DOC-MS-005 |

## Quorum rules

* **Routine operations** (e.g. role grant after a Timelock proposal):
  3-of-5 quorum.
* **Roster changes** (add / remove / rotate a signer): 4-of-5 quorum.
* **Emergency revocation** (compromised signer): any 2 signers can
  PROPOSE; quorum to EXECUTE remains 3-of-5. The PAUSER role can stop
  transfers immediately while the proposal matures.

## Conflict of interest

A signer recuses themselves from any proposal touching their own role,
their own employment, or a counterparty they have a personal interest
in. Recusal is logged with the proposal.

## Rotation

* On signer departure: revoke share within 1 business day.
* On suspicion of compromise: revoke share within 1 hour.
* Annual rotation: schedule once per year; no incident pre-required.

## Change log

This roster is versioned. Any change is recorded in
`docs/governance/roster_changelog.md` with the date, the change, the
quorum that approved it, and a link to the multi-sig transaction.

## Reference

* Onboarding procedure: `docs/operations/runbook.md` §"Multi-sig signer onboarding".
* Offboarding procedure: `docs/operations/runbook.md` §"Multi-sig signer offboarding".
* Key custody policy: `docs/security/key_management_policy.md`.
