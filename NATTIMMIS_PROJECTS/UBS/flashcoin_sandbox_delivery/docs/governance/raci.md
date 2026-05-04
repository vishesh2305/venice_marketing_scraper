# RACI — Who is responsible for what

R = Responsible (does the work). A = Accountable (signs off, owns outcome).
C = Consulted. I = Informed.

## Smart contract changes

| Activity | Eng-Blockchain | Security | Compliance | Treasury Ops | SOC | Multi-sig |
|---|---|---|---|---|---|---|
| Author Solidity change | R, A | C | I | I | I | I |
| Code review | C | R | I | I | C | I |
| Slither / solhint review | R | A | I | I | I | I |
| External audit (annual) | C | A, R | C | I | I | I |
| Mainnet deploy approval | C | C | I | C | C | A, R |

## Day-2 operational actions

| Activity | Eng-Blockchain | Security | Compliance | Treasury Ops | SOC | Multi-sig |
|---|---|---|---|---|---|---|
| Mint (issuance) | I | I | I | R, A | C | I (proposes if rate-limit-adjacent) |
| Burn (redemption) | I | I | I | R, A | C | I |
| Pause (incident) | C | C | I | I | R, A | I |
| Allowlist add | I | I | R, A | C | I | I |
| Allowlist revoke | I | C | R, A | I | I | I |
| Mint rate-limit change | C | C | I | C | I | R, A |
| Allowlist enforcement toggle | C | A | C | I | C | R |

## Multi-sig roster management

| Activity | Eng-Blockchain | Security | Compliance | Treasury Ops | SOC | Multi-sig |
|---|---|---|---|---|---|---|
| Add a signer | I | A | I | I | I | R (m-of-n quorum) |
| Remove a signer | I | A | I | I | I | R |
| Rotate a signer share | I | A | I | I | I | R |
| Recover from compromise | C | A, R | I | I | C | R |

## Incident response

| Activity | Eng-Blockchain | Security | Compliance | Treasury Ops | SOC | Multi-sig |
|---|---|---|---|---|---|---|
| Initial detection + page | I | C | I | I | R, A | I |
| Pause execution | C | C | I | I | R, A | I |
| Forensics + KMS audit pull | I | R, A | C | I | C | I |
| Post-mortem authorship | C | R, A | C | C | C | I |
| Decide v2 migration | C | C | C | C | C | A, R |

## Why two roles can't collapse into one

* `MINTER_ROLE` (Treasury Ops) and `COMPLIANCE_ROLE` (Compliance) MUST be
  separate. If the same entity could allowlist an address AND credit it,
  there is no four-eyes barrier on issuance.
* `PAUSER_ROLE` (SOC) and `DEFAULT_ADMIN_ROLE` (multi-sig + Timelock) MUST
  be separate. SOC must be able to act in seconds; admin actions must take
  48h. Collapsing them either makes admin too fast or pause too slow.
* See `segregation_of_duties.md` for the full rule set.
