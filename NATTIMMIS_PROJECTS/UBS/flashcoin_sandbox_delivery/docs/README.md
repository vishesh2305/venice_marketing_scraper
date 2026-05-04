# Internal Settlement Token — Documentation Index

This directory is the canonical engineering and governance reference for the
Internal Settlement Token (IST) infrastructure deployed (or planned) on TRON.
Each subdirectory below corresponds to one of the seven validation areas
called out in the client's Internal Technical Due Diligence Review.

| Section | Path | What it answers |
|---|---|---|
| 1. Architecture | [`architecture/`](architecture/) | What the system is, what its components are, how they talk. |
| 2. Security | [`security/`](security/) | Threat model, smart-contract risks, key management policy, incident response. |
| 3. Governance | [`governance/`](governance/) | Who can do what, multi-sig roster, RACI, segregation of duties. |
| 4. Operations | [`operations/`](operations/) | Daily/weekly runbook, monitoring spec, on-call procedure. |
| 5. Audit | [`audit/`](audit/) | Test plan, test report, static analysis, coverage. |
| 6. Deployment | [`deployment/`](deployment/) | Staged rollout (Shasta → Nile → Mainnet), preflight, rollback. |
| 7. Demo | [`demo/`](demo/) | Live demo script, expected on-chain artefacts, recorded run logs. |
| Diligence response | [`diligence/`](diligence/) | Point-by-point reply to the client's seven-section TDD memo. |

## Reading order for a reviewer who has 30 minutes

1. **`diligence/response_to_tdd.md`** — direct answers to the client's memo.
2. **`architecture/01_overview.md`** — C4 L1 + L2.
3. **`security/threat_model.md`** — STRIDE + risk register.
4. **`governance/raci.md`** — who has which key and what they can do with it.
5. **`audit/test_report.md`** — what's been tested, what's known to be open.
6. **`deployment/staged_rollout.md`** — how mainnet actually happens.

## Reading order for a reviewer who has 4 hours

Read everything in `architecture/`, then `security/`, then walk through
`audit/test_plan.md` next to the actual test files in
[`../test/`](../test/). Then read `governance/` and `operations/` in order.

## Conventions

* Every doc that names a contract, address, role, or function uses the
  exact identifier from the source — no paraphrasing. If a doc and the
  code disagree, the **code is correct** and the doc is a bug.
* Mermaid diagrams render natively in GitHub. Local rendering: install the
  Mermaid CLI or use the VS Code extension.
* All examples use **testnet** addresses. Any document that lists a
  mainnet address has been reviewed and signed off through the change
  control process (`docs/operations/runbook.md`).
