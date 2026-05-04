# Operations Runbook

Day-2 procedures for running the IST infrastructure. Every procedure here
is something the SOC and Treasury Ops teams expect to perform monthly or
more often. Less common procedures (incident response, v2 migration) are
in their own documents.

## Daily checks (SOC)

1. **Indexer lag.** `services/indexer/indexer.py --once` should complete
   under 30s and report a `highest_block` within 5 minutes of mainnet head.
2. **Reconciliation.** `services/reconciliation/reconciler.py` returns 0.
3. **Energy / bandwidth.** Each role-bearing operator address has at
   least 24h of energy. Rebalance if not.
4. **Multi-sig signer health.** Each signer's YubiKey is online; KMS
   audit log shows no unauthorised use.

## Weekly checks (Engineering)

1. CI green on `main` for at least 3 consecutive runs.
2. `slither` produces no new findings ≥ medium.
3. Open `SEV-3+` incidents reviewed.
4. `docs/security/smart_contract_risks.md` open items reviewed.

## Monthly checks (Compliance + Internal Audit)

1. Allowlist audit: every entry traceable to a current KYC/AML case.
2. Sample 10 mints; trace each end-to-end (CR → KMS audit → on-chain →
   indexer → reconciler).
3. Sample 10 burns; same trace.

## Common procedures

### Allowlist a new principal

```bash
# Compliance team operator, network=mainnet:
SIGNER_BACKEND=hashicorp_vault \
  node scripts/grant_roles.js --network mainnet --target allowlist \
    --role COMPLIANCE_ROLE --account T...   # only if granting
# For a one-off allow, use the operator CLI (TODO: scripts/allow.js — Q2).
```

### Mint to an allowlisted principal

```bash
SIGNER_BACKEND=aws_kms \
  node scripts/mint.js --network mainnet --to T... --amount 1000_000000
# (--amount is in smallest units. 1000 IST = 1000 * 10^6 = 1000_000000.)
```

### Pause in an incident

```bash
SIGNER_BACKEND=aws_kms \
  node scripts/pause.js --network mainnet
```

### Rotate a role key

1. Generate new KMS key.
2. Derive TRON address (`docs/security/key_management_policy.md` §3.2).
3. Multi-sig proposes `grantRole(<ROLE>, <new_addr>)`.
4. Wait Timelock delay.
5. Multi-sig executes.
6. Multi-sig proposes `revokeRole(<ROLE>, <old_addr>)`.
7. Wait Timelock delay.
8. Multi-sig executes.
9. Old KMS key scheduled for deletion (7-day window for forensics).

### Multi-sig signer onboarding

1. New signer's YubiKey is provisioned (FIPS 140-2 L2 minimum).
2. KMS asymmetric key created with the signer's IAM identity in the
   key policy.
3. TRON address derived from the KMS public key.
4. 4-of-5 quorum proposes `grantRole(MULTISIG_PROPOSER, <addr>)` on the
   Timelock and `grantRole(MULTISIG_EXECUTOR, <addr>)` likewise.
5. Wait delay; execute.
6. `docs/governance/multisig_roster.md` updated; `docs/governance/
   roster_changelog.md` appended.

### Multi-sig signer offboarding

Same as onboarding but with `revokeRole` and the 4-of-5 quorum requirement
includes the departing signer if they are still able and willing. If they
are not, 3-of-4 of the remaining signers approves; the change-log records
the reason.

## Endpoint switching

If TronGrid is degraded, switch the indexer to a fallback:

```bash
INDEXER_BASE_URL=https://api.example-fallback.io \
  python services/indexer/indexer.py
```

For mainnet, the only currently-validated fallback is running our own
java-tron full node — see infrastructure ticket INFRA-NN.

## Backup and restore

* **Indexer DB.** Postgres logical backups every 6h, 30-day retention,
  encrypted at rest. Tested restore monthly into the staging cluster.
* **Reconciler config.** Stored in version control alongside the
  internal book CSV (the CSV itself is in a separate, access-controlled
  repo).
* **KMS keys.** Backed by AWS — no separate backup procedure; key
  deletion has a 7-day window.
