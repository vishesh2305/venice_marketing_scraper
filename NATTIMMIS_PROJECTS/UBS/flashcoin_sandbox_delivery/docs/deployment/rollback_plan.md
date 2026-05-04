# Rollback Plan

What "rollback" means and does not mean for the IST infrastructure.

## TL;DR

A deployed TRC20 contract cannot be rolled back. It exists on chain
forever. "Rollback" therefore means **stopping use of the new contract
and either resuming the previous version or migrating to a v2.** This
document defines those procedures.

## When rollback is the right answer

| Situation | Rollback or fix forward? |
|---|---|
| Critical bug in v(N) discovered post-deploy, low value at risk | Fix forward (v(N+1) ceremony) |
| Critical bug, material value at risk | Pause + decide |
| Misconfiguration only (e.g. wrong rate limit) | Fix forward via Timelock |
| Wrong address granted a role | Fix forward (revoke via Timelock — pause if blast radius is unacceptable during the 48h delay) |
| Catastrophic governance failure (multi-sig compromised) | v2 migration |

## Procedure A — Pause + parameter fix (fix forward)

1. SOC pauses the contract.
2. Multi-sig queues the parameter change via Timelock.
3. Wait 48h. During the wait, transfers are blocked. Operations that
   *cannot* wait must be deferred or routed off-chain — there is no
   bypass.
4. Multi-sig executes.
5. SOC unpauses.
6. Reconciler runs and confirms no break.

## Procedure B — v2 migration

The full v2 migration procedure is in `docs/security/smart_contract_risks.md`
§4. Briefly:

1. Multi-sig pauses v1.
2. Multi-sig deploys v2.
3. Allowlist is re-seeded on v2 (compliance signer drives this).
4. For each non-zero-balance address on v1: `v1.burnFrom(addr, balance)`
   followed by `v2.mint(addr, balance)`. Both txs reconcile against the
   v1 event stream before the next pair.
5. v1 is left paused, on chain, marked retired in
   `docs/deployment/staged_rollout.md`.

## What does NOT roll back

* Allowlist additions/removals on the old contract — they remain part of
  the audit trail.
* KMS key creations — keys can be scheduled for deletion (7-day wait)
  but the historical CloudTrail log persists.
* Indexer history — append-only by design.

## Drill cadence

Procedure A is rehearsed quarterly on the testnet. Procedure B is
rehearsed annually on the testnet. The drill records are stored in
`docs/operations/drills/<date>-<procedure>.md`.

## What to communicate

If we trigger any rollback procedure on mainnet:

* Internal stakeholders: within 1h.
* Counterparties on the allowlist: within 4h, with planned-resumption ETA.
* Internal audit + Risk: same business day.
* External regulators: only as required by the bank's standard incident
  reporting policy (Legal owns this call).
