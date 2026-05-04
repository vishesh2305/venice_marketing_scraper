# Staged Rollout — Shasta → Nile → Mainnet

A new deployment of the IST infrastructure passes through three TRON
networks in order. Each stage has a different signer, a different review
bar, and a different set of acceptance criteria. Skipping a stage is
forbidden.

## Stage 1 — Shasta

| Property | Value |
|---|---|
| Purpose | CI integration tests, automation rehearsal |
| Signer | EnvSigner via CI secret |
| Multi-sig | n/a (deployer key holds all roles) |
| Approval | PR merge to `main` |
| Acceptance | `scripts/verify.js --network shasta` returns all-PASS |

Procedure:

```bash
PK_SHASTA=<testnet key>
make migrate-shasta
make verify
```

Outcome recorded in `docs/deployment/runs/<date>-shasta.md` (auto-generated
by `scripts/demo.sh` and curated for the run-book).

## Stage 2 — Nile

| Property | Value |
|---|---|
| Purpose | Multi-sig dress rehearsal, KMS smoke test |
| Signer | KMS (Nile-specific key) |
| Multi-sig | Optional — recommended |
| Approval | Eng Lead + Sec Lead |
| Acceptance | Multi-sig successfully proposes and executes one role grant |

This stage is the first place where the KMS adapter is exercised against
a real TRON network. Any KMS configuration drift will surface here, not
on mainnet.

## Stage 3 — Mainnet

| Property | Value |
|---|---|
| Purpose | Production simulation environment |
| Signer | KMS (mainnet key) |
| Multi-sig | Required (3-of-5) |
| Approval | Multi-sig + Internal Audit + Risk |
| Acceptance | All preflight items in `preflight_checklist.md` cleared; reconciliation pass on day 1, 7, 30 |

### Mainnet promotion preconditions

All of the below MUST be true:

1. Stage 2 completed cleanly within the last 30 days.
2. `docs/deployment/preflight_checklist.md` items 1–N all checked,
   with sign-offs recorded.
3. Multi-sig roster (`docs/governance/multisig_roster.md`) has at least
   `n` signers configured AND at least `m+1` signers reachable for the
   deployment window.
4. KMS mainnet key `alias/ist-multisig-1-mainnet` through
   `alias/ist-multisig-N-mainnet` exist and have CloudTrail enabled.
5. Engineering has dry-run the migration on Nile within the last 7 days.
6. SOC has a paged on-call covering the deployment window.

### Mainnet promotion procedure

```bash
# 1. Set environment from KMS-derived addresses (NOT raw keys).
SIGNER_BACKEND=aws_kms
KMS_KEY_ID_MAINNET=<key id>

# 2. Run the migration. The signer adapter calls KMS for every signature.
make migrate-mainnet

# 3. Post-deploy verify.
node scripts/verify.js --network mainnet

# 4. Manually verify on TronScan that the contract source matches the
#    repo. Verification is a separate step on TRON; instructions in §
#    "TronScan source verification" below.

# 5. Update .env in the bank's secret store with the deployed addresses.
#    Do NOT commit them to this repo (they are environment-specific).

# 6. Begin the multi-sig role-grant ceremony per
#    docs/governance/role_assignment.md.
```

### TronScan source verification

1. Open the contract page on TronScan: `https://tronscan.org/#/contract/<addr>/code`.
2. Click "Verify and Publish".
3. Compiler: `0.8.21+commit.<...>`.
4. Optimizer: enabled, runs 200, evmVersion `istanbul`.
5. Source: paste the flattened `InternalSettlementToken.sol` produced by
   `npx hardhat flatten contracts/InternalSettlementToken.sol`.
6. Constructor arguments: ABI-encoded; produced by
   `node scripts/print_constructor_args.js --network mainnet` (TODO).

Verification on TronScan must complete within 24h of deploy.

## Retired contracts

When a v2 supersedes v1, v1 is recorded here for historical reference:

| Version | Network | Address | Deploy date | Sunset date | Successor |
|---|---|---|---|---|---|
| (none yet) | | | | | |
