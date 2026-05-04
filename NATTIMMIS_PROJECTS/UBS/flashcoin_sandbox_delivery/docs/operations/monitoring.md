# Monitoring + Alerting Specification

What we observe, where the signal comes from, and what triggers a page.

## Signals

| Signal | Source | Frequency | Owner |
|---|---|---|---|
| Indexer lag (latest block vs head) | Indexer metric | 30s | SOC |
| Reconciliation breaks | Reconciler exit code | on-pass | SOC |
| `Paused` event emitted | TronGrid event stream | event | SOC + Eng |
| `RoleGranted` / `RoleRevoked` event | TronGrid event stream | event | Security |
| `Minted` event with amount > X | TronGrid event stream | event | Treasury + SOC |
| `Burned` event with amount > X | TronGrid event stream | event | Treasury + SOC |
| `AllowlistEnforcementChanged(false)` | TronGrid event stream | event | SOC + Eng (P0) |
| KMS `Sign` calls | CloudTrail | minute | Security |
| KMS key policy changes | CloudTrail | event | Security (P0) |
| GitHub branch-protection bypass | GitHub audit log | event | Security (P0) |

## Alerting policy (severity → page → owner)

| Severity | Definition | Page | Owner |
|---|---|---|---|
| P0 | Allowlist enforcement disabled, KMS key policy weakened, mainnet pause emitted, multi-sig roster change | Yes, immediate | SOC + Sec Lead |
| P1 | Reconciliation break, indexer lag > 5 min, mint > daily threshold | Yes, business-hours | SOC |
| P2 | Indexer lag > 1 min, slither finding ≥ medium on `main`, GitHub action red on `main` | No (ticket) | Eng |
| P3 | TronGrid 5xx rate elevated, hardhat coverage drop > 5pp | No (digest) | Eng |

## Dashboards

The bank's standard Grafana stack consumes the indexer's `/metrics`
Prometheus endpoint (TODO: implement — open as `OPEN-MET-1`). Pre-built
panels:

* IST total supply over time.
* IST mint/burn cumulative per day.
* Allowlist size and additions/revocations per day.
* Reconciliation pass/fail history.
* Indexer lag.
* Multi-sig proposal age (helps spot stuck Timelock items).

## SOC integration

Events of P0 / P1 severity are forwarded to the bank's SIEM via a Lambda
that subscribes to TronGrid event push (or polls in fallback mode). The
SIEM rule-set lives in the SIEM repo; the trigger field maps directly to
the event names emitted by the contracts.

## What we do NOT alert on

* Routine `Transfer` events. Volume too high for paging.
* `Approval` events.
* `RoleGranted` events that match a Timelock-scheduled proposal (the
  alert fires on the Timelock proposal, not on its execution).
