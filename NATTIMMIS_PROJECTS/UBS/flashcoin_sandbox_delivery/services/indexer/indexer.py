"""
services.indexer.indexer

Polls TronGrid for events emitted by the InternalSettlementToken contract
and writes them to a relational store (SQLite by default; Postgres in
production via INDEXER_DB_URL).

Design notes:
  * The indexer is the canonical audit trail. Reconciliation reads from it.
  * Append-only: rows are never updated except to mark `superseded_by` on a
    chain reorg. The reorg itself is recorded in `reorg_record`.
  * The poll loop is idempotent. Crashing and restarting from the last
    checkpoint produces the same final state — at-least-once semantics on
    insert, deduplicated by (tx_id, event_name, log_index).
"""

from __future__ import annotations

import json
import logging
import os
import sys
import time
from typing import Iterable

import requests
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session

from .models import Base, IndexerCheckpoint, TokenEvent

logger = logging.getLogger("indexer")
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-7s  %(name)s  %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)


def _trongrid_base(network: str) -> str:
    if network == "mainnet":
        return "https://api.trongrid.io"
    if network == "shasta":
        return "https://api.shasta.trongrid.io"
    if network == "nile":
        return "https://nile.trongrid.io"
    raise ValueError(f"Unknown network {network}")


def fetch_events(
    network: str, contract: str, since_block: int, api_key: str = ""
) -> Iterable[dict]:
    """Page through TronGrid events for a contract since a given block."""
    base = _trongrid_base(network)
    url = f"{base}/v1/contracts/{contract}/events"
    params = {
        "min_block_timestamp": 0,
        "limit": 200,
        "order_by": "block_timestamp,asc",
        "block_number": f"gte:{since_block}",
    }
    headers = {"TRON-PRO-API-KEY": api_key} if api_key else {}
    while True:
        r = requests.get(url, params=params, headers=headers, timeout=30)
        r.raise_for_status()
        body = r.json()
        for ev in body.get("data", []):
            yield ev
        next_link = (body.get("meta") or {}).get("links", {}).get("next")
        if not next_link:
            return
        url = next_link
        params = {}


def store_event(session: Session, network: str, contract: str, ev: dict) -> bool:
    """Insert one event. Returns True if newly inserted, False if duplicate."""
    tx_id = ev.get("transaction_id") or ev.get("transactionId") or ""
    name = ev.get("event_name") or ""
    block = int(ev.get("block_number") or 0)
    ts = int(ev.get("block_timestamp") or 0)

    # Dedupe on (tx_id, event_name, indexed_offset). For TRON, the same tx can
    # emit the same event multiple times (e.g. bulk ops); we differentiate
    # using the result_index also returned by TronGrid.
    result_index = ev.get("result_index", 0)
    dedupe_key = f"{tx_id}#{name}#{result_index}"

    # Quick existence check before insert.
    exists = session.execute(
        select(TokenEvent.id).where(TokenEvent.raw_json.like(f"%{dedupe_key}%"))
    ).first()
    if exists:
        return False

    result = ev.get("result") or {}
    record = TokenEvent(
        tx_id=tx_id,
        block_number=block,
        block_timestamp=ts,
        contract_address=contract,
        event_name=name,
        arg_from=str(result.get("from", "") or "") or None,
        arg_to=str(result.get("to", "") or "") or None,
        arg_value=str(result.get("value", "") or "") or None,
        arg_actor=str(result.get("by", "") or "") or None,
        raw_json=json.dumps({"_dedupe": dedupe_key, **ev})[:4096],
    )
    session.add(record)
    return True


def update_checkpoint(session: Session, network: str, contract: str, block: int) -> None:
    cp = session.execute(
        select(IndexerCheckpoint)
        .where(IndexerCheckpoint.network == network)
        .where(IndexerCheckpoint.contract_address == contract)
    ).scalar_one_or_none()
    if cp is None:
        cp = IndexerCheckpoint(network=network, contract_address=contract, last_block=block)
        session.add(cp)
    else:
        if block > cp.last_block:
            cp.last_block = block


def run_once(network: str, contract: str, db_url: str, api_key: str = "") -> int:
    engine = create_engine(db_url, future=True)
    Base.metadata.create_all(engine)

    inserted = 0
    with Session(engine) as session:
        cp = session.execute(
            select(IndexerCheckpoint)
            .where(IndexerCheckpoint.network == network)
            .where(IndexerCheckpoint.contract_address == contract)
        ).scalar_one_or_none()
        since = (cp.last_block + 1) if cp else 0

        max_block = since
        for ev in fetch_events(network, contract, since, api_key=api_key):
            if store_event(session, network, contract, ev):
                inserted += 1
            block = int(ev.get("block_number") or 0)
            if block > max_block:
                max_block = block

        update_checkpoint(session, network, contract, max_block)
        session.commit()

    logger.info(
        "indexer pass complete: network=%s contract=%s inserted=%d highest_block=%d",
        network, contract, inserted, max_block,
    )
    return inserted


def run_loop(network: str, contract: str, db_url: str, api_key: str, interval: int) -> None:
    logger.info("indexer loop starting (interval=%ds)", interval)
    while True:
        try:
            run_once(network=network, contract=contract, db_url=db_url, api_key=api_key)
        except Exception as e:
            logger.exception("indexer pass failed: %s", e)
        time.sleep(interval)


def main() -> int:
    network = os.environ.get("DEFAULT_NETWORK", "shasta")
    contract = os.environ.get(f"TOKEN_ADDRESS_{network.upper()}", "")
    db_url = os.environ.get("INDEXER_DB_URL", "sqlite:///./indexer.db")
    api_key = os.environ.get("TRONGRID_API_KEY", "")
    interval = int(os.environ.get("INDEXER_POLL_INTERVAL_SECONDS", "5"))

    if not contract:
        logger.error(
            "TOKEN_ADDRESS_%s is not set. Populate after deploy in .env.",
            network.upper(),
        )
        return 2

    once = "--once" in sys.argv
    if once:
        run_once(network=network, contract=contract, db_url=db_url, api_key=api_key)
    else:
        run_loop(network=network, contract=contract, db_url=db_url, api_key=api_key, interval=interval)
    return 0


if __name__ == "__main__":
    sys.exit(main())
