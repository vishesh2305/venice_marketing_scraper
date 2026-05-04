"""SQLAlchemy ORM models for the indexer.

The schema is intentionally append-only: every observed on-chain event is
inserted as a new row. Reconciliation reads the indexed rows; it never
mutates them. Any apparent correction (e.g. a chain reorg invalidating a
previous event) is recorded as a new row with `superseded_by` set.
"""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import Column, DateTime, Integer, String, BigInteger, Index, Boolean
from sqlalchemy.orm import declarative_base

Base = declarative_base()


class IndexerCheckpoint(Base):
    """Stores the latest block number observed per (network, contract)."""
    __tablename__ = "indexer_checkpoint"
    id = Column(Integer, primary_key=True)
    network = Column(String(32), nullable=False)
    contract_address = Column(String(64), nullable=False)
    last_block = Column(BigInteger, nullable=False, default=0)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (
        Index("ix_checkpoint_network_contract", "network", "contract_address", unique=True),
    )


class TokenEvent(Base):
    """Append-only event store. Mirrors what the on-chain audit trail emits."""
    __tablename__ = "token_event"

    id = Column(Integer, primary_key=True)
    tx_id = Column(String(80), nullable=False, index=True)
    block_number = Column(BigInteger, nullable=False, index=True)
    block_timestamp = Column(BigInteger, nullable=False, index=True)
    contract_address = Column(String(64), nullable=False, index=True)
    event_name = Column(String(80), nullable=False, index=True)

    # Common payload fields — denormalised for simple SQL audit queries.
    arg_from = Column(String(64), nullable=True, index=True)
    arg_to = Column(String(64), nullable=True, index=True)
    arg_value = Column(String(80), nullable=True)         # decimal string
    arg_actor = Column(String(64), nullable=True)         # privileged caller
    raw_json = Column(String(4096), nullable=False)       # full event for forensics

    superseded_by = Column(String(80), nullable=True)     # tx_id of replacement on reorg
    observed_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    __table_args__ = (
        Index("ix_event_contract_event", "contract_address", "event_name"),
    )


class ReorgRecord(Base):
    """Tracks every detected chain reorganisation that touched indexed data."""
    __tablename__ = "reorg_record"
    id = Column(Integer, primary_key=True)
    detected_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    network = Column(String(32), nullable=False)
    from_block = Column(BigInteger, nullable=False)
    to_block = Column(BigInteger, nullable=False)
    affected_event_count = Column(Integer, nullable=False, default=0)
    notes = Column(String(2048), nullable=True)
    is_resolved = Column(Boolean, default=False, nullable=False)
