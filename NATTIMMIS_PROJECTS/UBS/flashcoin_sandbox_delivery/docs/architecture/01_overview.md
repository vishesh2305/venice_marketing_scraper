# 01 — System Overview (C4 L1 + L2)

## Purpose

The Internal Settlement Token (IST) infrastructure exists to let Treasury,
Operations, and Risk model tokenised settlement flows on a real public
blockchain (TRON Mainnet) under controlled conditions. The system uses
production primitives — real on-chain execution, multi-sig governance,
HSM-backed signing — but operates within an institutional allowlist so that
it cannot interact with public counterparties or be confused with an
externally-issued asset.

## Out of scope

* Public token sale, exchange listing, secondary-market liquidity.
* Custody of customer funds.
* Integration with Treasury's production ledger (planned in a follow-on
  engagement; out of scope for the initial sandbox).

## C4 Level 1 — System context

```mermaid
flowchart LR
    subgraph Internal[Internal Banking Estate]
        Treasury[Treasury Operator]
        SOC[SOC / Incident Response]
        Compliance[Compliance Team]
        Auditor[Internal Audit]
    end

    subgraph IST[Internal Settlement Token system]
        IST_Token[Token contract on TRON]
        IST_Off[Off-chain services]
        IST_Docs[Governance + audit docs]
    end

    Treasury -- "issuance / redemption proposals" --> IST_Off
    SOC -- "monitoring + pause" --> IST_Off
    Compliance -- "allowlist updates" --> IST_Off
    Auditor -- "read-only review" --> IST_Off

    IST_Off -- "signed txs (KMS / Vault)" --> IST_Token
    IST_Token -- "events" --> IST_Off

    TRON[TRON Mainnet validators] -. "block production" .- IST_Token
    TronGrid[TronGrid event API] --> IST_Off
```

## C4 Level 2 — Containers

```mermaid
flowchart TB
    subgraph OnChain[On-chain — TRON]
        Token[InternalSettlementToken<br/>TRC20 + AccessControl + Pausable]
        Allowlist[ComplianceAllowlist<br/>per-address registry]
        Timelock[SettlementTimelock<br/>OZ TimelockController]
        Stress[FlashCoin stress harness<br/>testnet only]
    end

    subgraph OffChain[Off-chain — internal estate]
        Signer[Signer abstraction<br/>env / AWS KMS / Vault]
        Indexer[Indexer<br/>TronGrid -> Postgres]
        Reconciler[Reconciler<br/>events vs balances vs internal book]
        StressBot[Stress simulator<br/>burst / loop / sybil]
        Operator[Operator CLI / scripts]
    end

    subgraph Governance[Governance]
        Multisig[Multi-sig signers<br/>m-of-n]
        Custody[Key custody<br/>HSM / KMS / Vault]
    end

    Operator -- "schedule()" --> Timelock
    Multisig -- "schedule + execute" --> Timelock
    Timelock -- "DEFAULT_ADMIN_ROLE actions" --> Token
    Timelock -- "DEFAULT_ADMIN_ROLE actions" --> Allowlist

    Signer -- "mint / burn / pause" --> Token
    Signer -- "allow / revoke" --> Allowlist
    Signer -- "stress txs" --> Stress

    Indexer -- "events" --> Reconciler
    Indexer -. "polls" .- Token
    Indexer -. "polls" .- Allowlist
    Indexer -. "polls" .- Stress

    Custody --> Signer
```

## Container responsibilities

| Container | Source location | Responsibility |
|---|---|---|
| `InternalSettlementToken` | `contracts/InternalSettlementToken.sol` | TRC20, mint/burn under role gating + cap + rate limit, Pausable. |
| `ComplianceAllowlist` | `contracts/access/ComplianceAllowlist.sol` | Per-address registry consulted on every transfer. |
| `SettlementTimelock` | `contracts/governance/Timelock.sol` | OZ TimelockController; queues every privileged action. |
| FlashCoin stress harness | `contracts/stress/FlashCoin.sol` | Testnet-only abuse counterparty for SOC drills. |
| Signer abstraction | `services/keymanagement/signer.py` | Env / KMS / Vault adapters. Mainnet uses KMS. |
| Indexer | `services/indexer/indexer.py` | Append-only TronGrid event poller into SQL. |
| Reconciler | `services/reconciliation/reconciler.py` | Three-way: events ↔ on-chain balances ↔ internal book. |
| Stress simulator | `services/stress/simulator.py` | Burst / loop / sybil — exercises indexer & SOC alerting. |

## Data flows

The most important property of this system is that **every state-changing
operation produces an on-chain event, and every off-chain check derives from
those events.** The reconciler intentionally does NOT trust the on-chain
`balanceOf()` view as the source of truth — it recomputes balances from the
event stream and asserts equality. A divergence is a reconciliation break.

```mermaid
sequenceDiagram
    participant Op as Operator
    participant MS as Multi-sig
    participant TL as Timelock
    participant Tk as Token
    participant Ix as Indexer
    participant Rc as Reconciler

    Op->>MS: propose grantRole(MINTER, treasurer)
    MS->>TL: schedule(target=Token, data=grantRole...)
    Note right of TL: 48h delay (mainnet)
    MS->>TL: execute(...) after delay
    TL->>Tk: grantRole(MINTER, treasurer)
    Tk-->>Ix: RoleGranted event (TronGrid poll)
    Ix-->>Rc: row inserted
    Rc-->>Op: reconciliation pass: no break
```

## Why not a proxy / upgradeable pattern?

We deliberately do NOT use UUPS or a transparent proxy. The audit and
operational reasoning is in [`../security/smart_contract_risks.md`](../security/smart_contract_risks.md#why-no-proxy)
and is summarised: a non-upgradeable contract has a smaller attack surface,
a clearer audit boundary, and matches how USDC and other regulated stable
assets are operated. Bug fixes ship as v2 with a ceremonial mint-on-v2 /
burn-on-v1 migration governed by the multi-sig.
