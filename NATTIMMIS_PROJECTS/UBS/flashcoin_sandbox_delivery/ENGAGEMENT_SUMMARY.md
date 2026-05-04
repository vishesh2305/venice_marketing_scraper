# Engagement Summary

**Engagement:** TRON Mainnet internal token infrastructure for tokenised
settlement simulation, treasury modelling, and controlled operational
testing.

**Status:** pre-mainnet. Awaiting client review of the restructured
delivery, after which we proceed through the Shasta → Nile → Mainnet
staged rollout.

**Reviewer's first read:** [`docs/diligence/response_to_tdd.md`](docs/diligence/response_to_tdd.md)
— direct point-by-point response to the client's Internal Technical Due
Diligence Review.

---

## What changed since the previous delivery

The previous deliverable — a TRC20 fraud-detection sandbox hard-blocked
from mainnet — was rejected by the client's TDD team as inappropriate
for the engagement's scope. This delivery replaces it with an
institutional TRON Mainnet internal token infrastructure that meets each
of the seven concerns raised in the TDD memo.

| Aspect | Before | After |
|---|---|---|
| Scope | Testnet red-team fraud sandbox | Mainnet institutional settlement token (testnet-rehearsal staged) |
| Contract | Single-file `FlashCoin` with deliberate abuse vectors | `InternalSettlementToken` with AccessControl, Pausable, ReentrancyGuard, mint cap, rate limit, allowlist |
| Governance | Single `owner` modifier | OZ TimelockController + multi-sig (3-of-5) |
| Key management | Raw private key in JSON | KMS / Vault signer abstraction; raw keys impossible on mainnet |
| Tests | None — empty `test/` directory | Hardhat unit + integration + coverage |
| Static analysis | None | solhint + slither + gitleaks in CI |
| Architecture docs | None | C4 L1/L2/L3 with Mermaid in `docs/architecture/` |
| Security docs | None | STRIDE + risk register + key management policy + incident response |
| Governance docs | None | RACI + multi-sig roster + role assignment + segregation of duties |
| Operations docs | None | Runbook + monitoring spec + on-call procedure |
| Audit docs | None | Test plan + report + static analysis report |
| Deployment | Broken truffle config pointing at Ethereum/Infura | Working tronbox config with Shasta/Nile/Mainnet networks |
| Distribution | ZIP download | Git repository with CODEOWNERS + branch protection |
| AI-generated paperwork | Yes, by the client's account | Replaced with claims that are defensible against source / chain |

---

## Where to look for what

| Concern | Path |
|---|---|
| Client's diligence concerns | `docs/diligence/response_to_tdd.md` |
| What the system is | `docs/architecture/01_overview.md` |
| What can go wrong | `docs/security/threat_model.md` and `docs/security/smart_contract_risks.md` |
| Who can do what | `docs/governance/raci.md` |
| How keys are protected | `docs/security/key_management_policy.md` |
| How incidents are handled | `docs/security/incident_response.md` |
| How we deploy | `docs/deployment/staged_rollout.md` and `preflight_checklist.md` |
| How we demo it live | `docs/demo/live_demo_script.md` |
| Source of truth | `contracts/` and `services/` |

## Open items at delivery

These are tracked openly so the reviewer can see what is and is not
done. None of these block a *review* of the design; some block the
mainnet *deployment*.

| ID | Severity | Item | Owner | Target |
|---|---|---|---|---|
| OPEN-1 | Medium | KMS signer adapter is interface + spec only; full implementation during pre-mainnet hardening | Eng | Pre-mainnet |
| OPEN-2 | Low | No on-chain registry of role-grant rationale (CR ticket suffices) | Gov | Quarter +1 |
| OPEN-3 | Low | Mainnet TronScan source-verification not yet scripted | Eng | Pre-mainnet |
| OPEN-MET-1 | Low | Indexer Prometheus `/metrics` endpoint | Eng | Pre-mainnet |
| OPEN-OPS-1 | Low | Pre-commit path-allowlist hook | Eng | Quarter +1 |
| OPEN-TEST-1 | Low | Property / fuzz tests for ERC20 invariants | Eng | Quarter +1 |
| OPEN-TEST-2 | Low | Indexer reorg simulation | Eng | Quarter +1 |
| OPEN-TEST-3 | Low | KMS signer integration test against LocalStack | Eng | Pre-mainnet |

---

## Ask of the reviewer

1. Read `docs/diligence/response_to_tdd.md`.
2. Identify which sections still don't satisfy the original concern.
3. Schedule a 60-minute live demo using `docs/demo/live_demo_script.md`.
4. Co-author the preflight checklist sign-off when ready to promote to
   mainnet.

We expect remaining concerns. We will respond with code or document
changes — tracked as PRs in this repository — not with narrative.
