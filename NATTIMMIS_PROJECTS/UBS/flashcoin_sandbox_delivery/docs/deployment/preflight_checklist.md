# Mainnet Preflight Checklist

Every item must be checked, signed off, and dated before mainnet
migration. The signed copy lives in the bank's change-management system;
this document is the master template.

```
Engagement     : ____________________
Target version : v_____________________
Target network : mainnet
Window (UTC)   : ____________________ – ____________________
```

## A. Code

- [ ] Tag exists, signed, matches the SHA being deployed.
- [ ] CI (`ci.yml`) green on the tag.
- [ ] Security CI (`security.yml`) green on the tag.
- [ ] Coverage report attached, ≥ targets in `docs/audit/test_plan.md`.
- [ ] No open `OPEN-*` items of severity ≥ medium in
      `docs/audit/test_report.md` or `docs/security/smart_contract_risks.md`.
- [ ] Diff vs previous mainnet release is ≤ 500 lines, OR a release-note
      narrative exists explaining each contract-touching change.

      Sign-off: __________________ (Eng Lead) Date: ________

## B. Security

- [ ] External audit report (or annual review) on file, ≤ 12 months old.
- [ ] Slither scan against the tag attached, no new findings ≥ medium.
- [ ] Gitleaks scan on the tag green.
- [ ] Threat model (`docs/security/threat_model.md`) reviewed since last
      contract change.
- [ ] KMS mainnet keys exist; aliases match
      `docs/security/key_management_policy.md` §2.
- [ ] CloudTrail enabled on every KMS key in scope.

      Sign-off: __________________ (Sec Lead) Date: ________

## C. Governance

- [ ] Multi-sig roster (`docs/governance/multisig_roster.md`) up to date.
- [ ] At least `m+1` signers reachable for the deployment window.
- [ ] CR ticket open and approved by 2 CODEOWNERS.
- [ ] Internal Audit notified and acknowledged.
- [ ] Risk Committee notified for value-relevant changes.

      Sign-off: __________________ (Multi-sig) Date: ________

## D. Operations

- [ ] Indexer ready to pivot to mainnet endpoint after deploy.
- [ ] Reconciler ready with a fresh, empty internal book.
- [ ] SOC dashboard panels exist for: total supply, mints/day, burns/day,
      allowlist size, pause state.
- [ ] Paging targets configured (PagerDuty rotation, SIEM rule).
- [ ] On-call covered for deployment window + 48h post-deploy.

      Sign-off: __________________ (SOC Lead) Date: ________

## E. Compliance

- [ ] Allowlist seed list reviewed; every address has a current KYC/AML.
- [ ] Off-chain reference hashes computed and recorded in the compliance
      system.
- [ ] Legal review of any external counterparty in the seed list complete.

      Sign-off: __________________ (Compliance Lead) Date: ________

## F. Rollback

- [ ] Rollback procedure (`docs/deployment/rollback_plan.md`) reviewed.
- [ ] Pre-deployment snapshot of the indexer DB taken (in case of issues).
- [ ] v2 migration prepared in concept (not built) so we know the path
      forward if a critical bug surfaces.

      Sign-off: __________________ (Eng Lead) Date: ________

---

The deployment proceeds only when every section is signed.
