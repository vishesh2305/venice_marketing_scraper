# 03 — Deployment Topology

```mermaid
flowchart TB
    subgraph chains[TRON networks]
        dev[(Local java-tron / tron-quickstart)]
        shasta[(Shasta testnet)]
        nile[(Nile testnet)]
        main[(Mainnet)]
    end

    subgraph dev_estate[Developer workstation]
        d_signer[EnvSigner + .env]
        d_node[Hardhat / tronbox]
    end

    subgraph ci[CI estate — GitHub Actions]
        ci_compile[hardhat compile + test]
        ci_slither[slither + solhint + gitleaks]
        ci_deploy[(testnet deploy on tag)]
    end

    subgraph prod[Production estate — internal banking infra]
        kms[AWS KMS / HashiCorp Vault]
        ms[Multi-sig signers]
        idx[Indexer service<br/>Postgres-backed]
        rec[Reconciler service]
        soc[SOC dashboards + alerts]
        ops[Operator CLI inside bastion]
    end

    d_signer --> dev
    d_signer --> shasta
    d_node --> shasta

    ci_compile --> ci_slither
    ci_slither --> ci_deploy
    ci_deploy --> shasta
    ci_deploy --> nile

    ms --> kms
    ops --> kms
    kms --> main
    kms --> nile
    main --> idx
    nile --> idx
    idx --> rec
    rec --> soc
```

## Network promotion path

| Stage | Network | Purpose | Signer | Approval needed |
|---|---|---|---|---|
| 1 | local | Developer iteration | EnvSigner / Hardhat default | None |
| 2 | Shasta | CI integration tests, automation | EnvSigner via CI secret | PR merge to main |
| 3 | Nile | Dress rehearsal, multi-sig drill | KMS (testnet key) | Engineering Lead + Security |
| 4 | Mainnet | Production simulation | KMS (mainnet key) | Multi-sig (m-of-n) + Timelock |

A production deploy is gated by completing the
[`../deployment/preflight_checklist.md`](../deployment/preflight_checklist.md).
The promotion from Nile → Mainnet is also recorded in the change-management
ticket; no purely-engineering action triggers a mainnet move.

## Network endpoints

| Network | Full host | Network ID |
|---|---|---|
| development | `http://127.0.0.1:9090` | 9 |
| Shasta | `https://api.shasta.trongrid.io` | 2 |
| Nile | `https://nile.trongrid.io` | 3 |
| Mainnet | `https://api.trongrid.io` | 1 |

Endpoint values live in `tronbox-config.js` and are not configurable per
deploy.
