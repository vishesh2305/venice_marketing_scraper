# Live Demo Script

This is the script that the Engineering Lead reads during a live demo
call with the client. The intent is that every claim in the call has a
visible, on-chain artefact behind it. Total wall-clock time: ~25 minutes
including questions.

## Pre-call checklist

The day before:

- [ ] Latest `main` deployed to Shasta. Note the deployed addresses in a
      sticky on the demo machine.
- [ ] `node scripts/verify.js --network shasta` returns all-PASS.
- [ ] Demo addresses (Alice, Bob) funded with Shasta TRX.
- [ ] Indexer warmed up against the deployed contract.
- [ ] Recording enabled with the client's consent. Recordings stored
      under the standard retention policy.

## Section 1 — Repository walkthrough (5 min)

> "We have a single source-of-truth git repository. Every change goes
>  through PR review with two CODEOWNERS approvals on anything that
>  touches contracts or key management. CI runs compile + tests +
>  static analysis on every PR — security blocks merge on findings of
>  medium or higher."

Show:

* `.github/workflows/ci.yml` and `security.yml`.
* `.github/CODEOWNERS`.
* A recent green CI run on `main`.
* `docs/README.md` as the index.

## Section 2 — Contract architecture (5 min)

> "The token is `InternalSettlementToken`. It is a TRC20 with five
>  controls layered on top: AccessControl, Pausable, ReentrancyGuard,
>  a global mint cap, and a per-block mint rate limit. Compliance
>  is enforced by a separate ComplianceAllowlist contract that the
>  token consults on every transfer. The admin role is held by a
>  Timelock with a 48-hour delay — there is no human owner key."

Show on screen:

* `contracts/InternalSettlementToken.sol` — read the constructor and
  the `_beforeTokenTransfer` hook.
* `contracts/access/Roles.sol` — the closed enumeration.
* `docs/architecture/02_components.md` — the role/capability matrix.
* `docs/security/threat_model.md` — STRIDE table.

## Section 3 — Live deploy + lifecycle on Shasta (8 min)

Run, narrating each step:

```bash
make migrate-shasta
node scripts/verify.js --network shasta
node scripts/demo_lifecycle.js --network shasta
```

Open TronScan in the browser at the deployed address and show the
events emitted in real time. Tab through:

* `Transfer` from address(0) on mint → confirms mint.
* `AddressAllowed` events on allowlist.
* `Paused` / `Unpaused` events on pause cycle.

## Section 4 — Indexer + reconciler (3 min)

```bash
( cd services/indexer && python indexer.py --once )
( cd services/reconciliation && python reconciler.py )
```

Show:

* Indexer DB: `sqlite3 services/indexer/indexer.db ".schema"` and a
  `SELECT COUNT(*) FROM token_event;`.
* Reconciler exit code 0.

## Section 5 — Governance + key management (3 min)

> "On mainnet, the deployer key here would be replaced by the multi-sig
>  + Timelock. Privileged actions become two-step: schedule(), wait the
>  delay, execute(). The keys themselves never leave the HSM — the
>  signer abstraction in `services/keymanagement/signer.py` calls
>  KMS for the signature and reconstructs the transaction here."

Show:

* `services/keymanagement/signer.py` — read the EnvSigner mainnet
  refusal and the AwsKmsSigner stub.
* `docs/governance/raci.md`.
* `docs/security/key_management_policy.md`.

## Section 6 — Q&A (5 min)

Likely questions and the answers:

* **"Why no proxy / upgradeable contract?"** → smaller audit boundary,
  same posture as USDC. v2 migration ceremony documented in
  `docs/security/smart_contract_risks.md` §4.
* **"How fast can you respond to an incident?"** → pause is single-sig
  via SOC: ~30s. Role revocation goes through 48h Timelock — pause is
  the immediate control during the wait.
* **"How do we audit who minted what when?"** → KMS audit log + on-chain
  events + indexer DB; three independent sources triangulate every
  privileged action.
* **"What about TRON-specific risks?"** → see `smart_contract_risks.md`
  §9 and §10.

## Post-call artefacts

A demo run produces:

* `docs/demo/runs/demo-<timestamp>.log` — the full session log.
* TronScan URLs for each tx hash, copied into the run note.
* The reconciliation pass result.
