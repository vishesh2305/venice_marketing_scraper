# 02 — Component View (C4 L3)

## InternalSettlementToken — internal structure

```mermaid
classDiagram
    class InternalSettlementToken {
      +mintCap: uint256 (immutable)
      +mintRateLimitPerBlock: uint256
      +allowlist: address
      +allowlistEnforced: bool
      +mint(to, amount)
      +burn(amount)
      +burnFrom(from, amount)
      +pause() / unpause()
      +setAllowlist(addr)
      +setAllowlistEnforced(bool)
      +setMintRateLimitPerBlock(uint)
      -_beforeTokenTransfer()
    }

    class ERC20 { +transfer / approve / transferFrom }
    class AccessControl { +hasRole / grantRole / revokeRole }
    class Pausable { +paused() / _pause() / _unpause() }
    class ReentrancyGuard { #_status }

    InternalSettlementToken --|> ERC20
    InternalSettlementToken --|> AccessControl
    InternalSettlementToken --|> Pausable
    InternalSettlementToken --|> ReentrancyGuard
    InternalSettlementToken --> ComplianceAllowlist : reads via isAllowed()
```

### Role -> capability matrix (token contract)

| Role | mint | burn / burnFrom | pause / unpause | grantRole / revokeRole | setAllowlist / setEnforced / setRateLimit |
|---|---|---|---|---|---|
| `DEFAULT_ADMIN_ROLE` (Timelock) |  |  |  | ✓ | ✓ |
| `MINTER_ROLE` | ✓ |  |  |  |  |
| `BURNER_ROLE` |  | ✓ |  |  |  |
| `PAUSER_ROLE` |  |  | ✓ |  |  |
| anyone else |  |  |  |  |  |

The admin can ONLY grant/revoke roles or change non-economic parameters.
The admin **cannot move balances** under any code path — verified by the
test `access.test.js: admin cannot move balances via DEFAULT_ADMIN_ROLE alone`.

## ComplianceAllowlist — internal structure

```mermaid
classDiagram
    class ComplianceAllowlist {
      -_allowed: mapping(address => bool)
      -_referenceHash: mapping(address => bytes32)
      -_allowedCount: uint256
      +allow(address, bytes32)
      +allowBatch(addrs, hashes)
      +revoke(address)
      +updateReference(address, bytes32)
      +isAllowed(address) view
      +referenceHashOf(address) view
    }
    ComplianceAllowlist --|> AccessControl
```

The reference-hash field is intentionally `bytes32` (a hash) rather than a
string — it stores `keccak256(<off-chain case ID>)`, never PII. The off-chain
compliance system retains the underlying record. This mirrors guidance from
EU and Swiss data-protection regulators that public-blockchain storage of
PII is unacceptable.

## SettlementTimelock — internal structure

```mermaid
classDiagram
    class SettlementTimelock {
      +constructor(minDelay, proposers[], executors[], admin)
      +schedule(target, value, data, predecessor, salt, delay)
      +execute(target, value, data, predecessor, salt)
      +cancel(id)
      +getMinDelay()
      +updateDelay(uint)
    }
    SettlementTimelock --|> TimelockController
```

* `minDelay` = 1h on testnet, 48h on mainnet.
* `admin` = `address(0)` — the timelock administers itself via queued ops.
  This is the OpenZeppelin "self-administered" pattern and removes the
  super-user override class of bug.

## Off-chain components

```mermaid
flowchart LR
    subgraph svc[services/]
        signer[keymanagement/signer.py<br/>EnvSigner / AwsKmsSigner / VaultSigner]
        indexer[indexer/indexer.py + models.py]
        reconciler[reconciliation/reconciler.py]
        stress[stress/simulator.py]
    end

    operator((Operator)) -->|env or KMS auth| signer
    signer --> Tron[TRON node]
    Tron --> tg[TronGrid events]
    tg --> indexer
    indexer --> db[(Postgres / SQLite)]
    db --> reconciler
    reconciler --> alerts[(SOC alerts)]
    stress --> Tron
```

### Signer adapter selection

```mermaid
flowchart TD
    op[Operator runs script] --> env{SIGNER_BACKEND env var?}
    env -- "env" --> dev[EnvSigner refuses mainnet]
    env -- "aws_kms" --> kms[AwsKmsSigner — production]
    env -- "hashicorp_vault" --> vault[VaultSigner — production alt]
    env -- unset --> default{network?}
    default -- "mainnet" --> kms
    default -- "testnet / dev" --> dev
```

The `EnvSigner` constructor explicitly raises if `network == "mainnet"`,
preventing a developer key from ever signing a mainnet transaction even if
an operator misconfigures `SIGNER_BACKEND`. See
[`../security/key_management_policy.md`](../security/key_management_policy.md).
