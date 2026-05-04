# On-Call Procedure

## Rotations

| Rotation | Coverage | Members | Tooling |
|---|---|---|---|
| SOC primary | 24/7 | SOC team | PagerDuty |
| SOC secondary | 24/7 | SOC team | PagerDuty (escalates after 5 min) |
| Eng-Blockchain | Business hours + best-effort weekend | Eng-Blockchain team | PagerDuty |
| Security Lead | 24/7 escalation | Sec Lead + 1 backup | PagerDuty |
| Compliance | Business hours | Compliance team | Email + on-call phone |
| Multi-sig signers | At all times — 3-of-5 reachable within 1h | Per `docs/governance/multisig_roster.md` | Phone + YubiKey |

## What the on-call SOC engineer does on a page

1. Acknowledge the page within 5 min.
2. Open the incident channel and summarise the trigger.
3. Pull the relevant dashboard panel.
4. If the trigger is P0:
   * Determine if `pause()` is warranted. If yes, execute via the SOC
     KMS key (single-sig, fast).
   * Page the Security Lead and Eng-Blockchain on-call.
   * Page Compliance and Legal if the trigger touches allowlist or
     multi-sig.
5. If the trigger is P1:
   * Triage. If reconciliation break, run the reconciler again with
     fresh data; the most common false positive is a TronGrid lag.
   * Open a SEV-3 ticket if the break persists.
6. Update the incident channel every 15 min until the trigger clears.

## Handover

End of every on-call shift, the outgoing engineer files a handover note:

* Active alerts.
* Open tickets touched.
* Anything that looked weird but didn't page.
* Anything to watch for in the next shift.

## Escalation paths

| Trigger | Page who |
|---|---|
| Reconciliation break that persists > 30 min | Eng-Blockchain on-call |
| Mainnet pause executed | Sec Lead + Eng-Blockchain on-call |
| KMS audit anomaly | Sec Lead |
| Compliance violation suspected | Compliance Lead + Legal |
| Multi-sig signer key compromise suspected | Sec Lead + Multi-sig (all signers) |

## Anti-patterns the on-call must NOT do

* Do not bypass the multi-sig under time pressure.
* Do not use a personal key to sign anything.
* Do not modify a contract or rerun a migration during an incident.
* Do not export KMS audit logs to anywhere except the forensic share.
* Do not discuss incident specifics outside the incident channel until
  Comms releases a stakeholder note.
