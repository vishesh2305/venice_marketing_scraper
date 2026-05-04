# Role Assignment Matrix

Authoritative mapping from on-chain roles to off-chain organisational
holders. This is the document the CODEOWNERS file enforces and the
Timelock proposals reference.

## On-chain roles

| Role hash (keccak256) | Solidity constant | Held by | Backend |
|---|---|---|---|
| `0x00...00` | `DEFAULT_ADMIN_ROLE` | `SettlementTimelock` | Self-administered (admin = address(0)) |
| `MINTER_ROLE` | `keccak256("MINTER_ROLE")` | Treasury issuance service | KMS asymmetric |
| `BURNER_ROLE` | `keccak256("BURNER_ROLE")` | Redemption service | KMS asymmetric |
| `PAUSER_ROLE` | `keccak256("PAUSER_ROLE")` | SOC on-call (rotating) | KMS asymmetric |
| `COMPLIANCE_ROLE` | `keccak256("COMPLIANCE_ROLE")` | Compliance service | Vault Transit |
| `CONFIGURATOR_ROLE` | `keccak256("CONFIGURATOR_ROLE")` | Currently unassigned (admin handles) | n/a |

## How a role is granted

1. Engineering opens a CR ticket with the proposed role and recipient.
2. CODEOWNERS approval requires Eng-Blockchain + Security.
3. Engineering runs `node scripts/grant_roles.js --network mainnet --target token --role MINTER_ROLE --account T...` to produce the Timelock payload (off-chain artefact only — the script does not broadcast).
4. The four-eyes counter-signer reviews the payload diff against the CR.
5. Multi-sig PROPOSER submits `Timelock.schedule(target, 0, calldata, 0, salt, delay)`.
6. Wait the minimum delay (48h on mainnet).
7. Multi-sig EXECUTOR submits `Timelock.execute(...)`.
8. SOC verifies via `node scripts/verify.js --network mainnet`.

## How a role is revoked

Same pipeline, but with `revokeRole(...)` calldata. In an incident, see
`docs/security/incident_response.md` — the pause is the immediate control;
the revocation goes through the same Timelock for chain-of-custody integrity.

## What about emergency grants?

There is no "emergency grant" path. The 48h delay is **the** governance
control on mainnet. If a faster grant is required, the system is being
operated outside its design and the multi-sig should consider whether the
underlying issue is actually an incident requiring pause + v2 migration
rather than a new role grant.

## Non-token roles

Operational roles inside the bank's estate (KMS IAM, GitHub teams, on-call
schedules) are out of scope of this document and are governed by the
bank's standard IAM controls.
