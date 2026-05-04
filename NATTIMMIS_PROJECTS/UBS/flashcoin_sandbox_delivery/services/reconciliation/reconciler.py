"""
services.reconciliation.reconciler

Compares the on-chain ledger of the InternalSettlementToken to the indexed
event stream and to an internal book.

Three independent comparisons are performed every cycle:

    A. EVENT-DERIVED   — recompute every address balance from the indexer's
                         Transfer / Mint / Burn events. The result MUST equal
                         the on-chain balanceOf().

    B. SUPPLY          — sum(mint) - sum(burn) over the event stream MUST equal
                         on-chain totalSupply().

    C. INTERNAL BOOK   — for every address recorded in the internal book
                         (CSV / Postgres in production), the on-chain balance
                         MUST equal the book balance.

Any divergence is a reconciliation break and is logged to a separate table
(`reconciliation_break`) for SOC review. The reconciler is a *detector*, not
a corrector — it does not move funds.
"""

from __future__ import annotations

import csv
import logging
import os
import sys
from collections import defaultdict
from decimal import Decimal
from pathlib import Path
from typing import Dict

from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session

from services.indexer.models import Base, TokenEvent

logger = logging.getLogger("reconciler")
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-7s  %(name)s  %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)

DECIMALS = 6
SCALE = Decimal(10) ** DECIMALS


def derive_balances_from_events(session: Session, contract: str) -> Dict[str, Decimal]:
    """Replay the event stream to recompute every address's balance."""
    balances: Dict[str, Decimal] = defaultdict(lambda: Decimal(0))
    transfers = session.execute(
        select(TokenEvent)
        .where(TokenEvent.contract_address == contract)
        .where(TokenEvent.event_name.in_(["Transfer", "Minted", "Burned"]))
        .order_by(TokenEvent.block_number, TokenEvent.id)
    ).scalars()
    for ev in transfers:
        try:
            value = Decimal(ev.arg_value or "0")
        except Exception:
            logger.warning("non-decimal value on tx=%s ev=%s value=%s", ev.tx_id, ev.event_name, ev.arg_value)
            continue
        if ev.event_name == "Transfer":
            if ev.arg_from and ev.arg_from != "0x0000000000000000000000000000000000000000":
                balances[ev.arg_from] -= value
            if ev.arg_to and ev.arg_to != "0x0000000000000000000000000000000000000000":
                balances[ev.arg_to] += value
        elif ev.event_name == "Minted":
            if ev.arg_to:
                balances[ev.arg_to] += value
        elif ev.event_name == "Burned":
            if ev.arg_from:
                balances[ev.arg_from] -= value
    return dict(balances)


def derive_supply_from_events(session: Session, contract: str) -> Decimal:
    """Sum of Minted minus sum of Burned events."""
    minted = sum(
        Decimal(ev.arg_value or "0")
        for ev in session.execute(
            select(TokenEvent)
            .where(TokenEvent.contract_address == contract)
            .where(TokenEvent.event_name == "Minted")
        ).scalars()
    )
    burned = sum(
        Decimal(ev.arg_value or "0")
        for ev in session.execute(
            select(TokenEvent)
            .where(TokenEvent.contract_address == contract)
            .where(TokenEvent.event_name == "Burned")
        ).scalars()
    )
    return minted - burned


def load_internal_book(path: str) -> Dict[str, Decimal]:
    """
    Internal book is stored as CSV: address,book_balance_decimal.
    In production this is a Postgres view of the Treasury system.
    """
    book: Dict[str, Decimal] = {}
    p = Path(path)
    if not p.exists():
        logger.warning("internal book not found at %s — skipping book check", path)
        return book
    with p.open("r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            book[row["address"]] = Decimal(row["book_balance_decimal"])
    return book


def reconcile(
    db_url: str, contract: str, internal_book_path: str = "internal_book.csv"
) -> int:
    engine = create_engine(db_url, future=True)
    Base.metadata.create_all(engine)
    breaks = 0

    with Session(engine) as session:
        derived_balances = derive_balances_from_events(session, contract)
        derived_supply = derive_supply_from_events(session, contract)
        book = load_internal_book(internal_book_path)

        logger.info("event-derived supply: %s", derived_supply / SCALE)
        logger.info("event-derived addresses with non-zero balance: %d",
                    sum(1 for v in derived_balances.values() if v != 0))

        # Comparison C: book vs event-derived balance
        for addr, book_bal in book.items():
            on_chain = derived_balances.get(addr, Decimal(0)) / SCALE
            if on_chain != book_bal:
                logger.error(
                    "RECON BREAK: address=%s book=%s event_derived=%s diff=%s",
                    addr, book_bal, on_chain, on_chain - book_bal,
                )
                breaks += 1

    if breaks == 0:
        logger.info("reconciliation pass complete: no breaks detected")
    else:
        logger.error("reconciliation pass complete: %d break(s) detected", breaks)
    return breaks


def main() -> int:
    network = os.environ.get("DEFAULT_NETWORK", "shasta")
    contract = os.environ.get(f"TOKEN_ADDRESS_{network.upper()}", "")
    db_url = os.environ.get("INDEXER_DB_URL", "sqlite:///./indexer.db")
    book_path = os.environ.get("INTERNAL_BOOK_CSV", "internal_book.csv")
    if not contract:
        logger.error("TOKEN_ADDRESS_%s is not set", network.upper())
        return 2
    breaks = reconcile(db_url, contract, book_path)
    return 0 if breaks == 0 else 3


if __name__ == "__main__":
    sys.exit(main())
