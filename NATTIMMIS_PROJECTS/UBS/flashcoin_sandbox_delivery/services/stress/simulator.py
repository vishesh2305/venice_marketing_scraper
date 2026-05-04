"""
============================================================================
  FlashCoin Attack Simulator
  ⚠️  TEST / SANDBOX ONLY — DO NOT RUN AGAINST MAINNET OR REAL FUNDS  ⚠️

  Red-team bot that exercises a deployed FlashCoin contract in three modes:
      * BURST   — fire N transfers as fast as the node accepts them
      * LOOP    — pipe tokens A -> B -> C -> A across a ring of wallets
      * SYBIL   — have every wallet call claimTranche() simultaneously

  Target networks:
      - TRON Shasta testnet (default, https://api.shasta.trongrid.io)
      - TRON Nile testnet   (https://nile.trongrid.io)
      - Local tron-quickstart / java-tron private node

  NEVER point this at api.trongrid.io. The config has an `allow_mainnet`
  guard that defaults to False; do not flip it.
============================================================================
"""

from __future__ import annotations

import argparse
import json
import logging
import os
import random
import secrets
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional

try:
    from tronpy import Tron
    from tronpy.keys import PrivateKey
    from tronpy.providers import HTTPProvider
    from tronpy.exceptions import TransactionError
except ImportError:
    print("tronpy is not installed. Run: pip install -r requirements.txt", file=sys.stderr)
    raise


# ---------------------------------------------------------------------------
# Config + safety
# ---------------------------------------------------------------------------

MAINNET_HOST_MARKERS = ("api.trongrid.io",)  # excludes 'api.shasta.trongrid.io' / 'nile.trongrid.io'
TESTNET_HOST_MARKERS = ("shasta", "nile", "localhost", "127.0.0.1", "0.0.0.0")


@dataclass
class SimConfig:
    network: str = "shasta"
    full_node: str = "https://api.shasta.trongrid.io"
    solidity_node: str = "https://api.shasta.trongrid.io"
    event_server: str = "https://api.shasta.trongrid.io"
    api_key: str = ""

    contract_address: str = ""
    funder_private_key: str = ""

    number_of_wallets: int = 50
    transactions_per_second: int = 5
    tranche_amount: int = 1000          # informational; real value is set on-chain
    delay_between_calls: float = 0.2
    burst_count: int = 1000
    loop_hops: int = 3
    fund_trx_per_wallet: int = 50
    max_workers: int = 16

    wallets_file: str = "wallets.json"
    log_file: str = "simulation.log"

    allow_mainnet: bool = False

    @classmethod
    def load(cls, path: str) -> "SimConfig":
        with open(path, "r", encoding="utf-8") as f:
            raw = json.load(f)
        raw.pop("_comment", None)
        known = {k: raw[k] for k in raw if k in cls.__dataclass_fields__}
        return cls(**known)


def abort_if_mainnet(cfg: SimConfig) -> None:
    """Hard safety gate. Refuse to run anything that even smells like mainnet."""
    host = (cfg.full_node or "").lower()

    looks_mainnet = any(m in host for m in MAINNET_HOST_MARKERS) and not any(
        m in host for m in TESTNET_HOST_MARKERS
    )
    if looks_mainnet and not cfg.allow_mainnet:
        raise RuntimeError(
            f"SAFETY: full_node '{cfg.full_node}' appears to be mainnet. "
            "Refusing to run. Use Shasta/Nile/local node, or set allow_mainnet=True "
            "only if you have explicit authorization (you almost certainly do not)."
        )

    if cfg.allow_mainnet:
        logging.warning("allow_mainnet=True — proceeding against %s. You have been warned.", host)


# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------

def setup_logging(log_file: str) -> logging.Logger:
    logger = logging.getLogger("flashcoin-sim")
    logger.setLevel(logging.INFO)
    logger.handlers.clear()

    fmt = logging.Formatter(
        "%(asctime)s  %(levelname)-7s  %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    sh = logging.StreamHandler(sys.stdout)
    sh.setFormatter(fmt)
    logger.addHandler(sh)

    try:
        fh = logging.FileHandler(log_file, encoding="utf-8")
        fh.setFormatter(fmt)
        logger.addHandler(fh)
    except OSError as e:
        logger.warning("File log disabled: %s", e)

    return logger


# ---------------------------------------------------------------------------
# Wallet management
# ---------------------------------------------------------------------------

@dataclass
class Wallet:
    address: str
    private_key: str  # hex, no 0x prefix

    def pk(self) -> PrivateKey:
        return PrivateKey(bytes.fromhex(self.private_key))


def generate_wallet() -> Wallet:
    pk = PrivateKey(secrets.token_bytes(32))
    return Wallet(address=pk.public_key.to_base58check_address(), private_key=pk.hex())


def load_or_create_wallets(path: str, n: int, logger: logging.Logger) -> List[Wallet]:
    p = Path(path)
    if p.exists():
        with p.open("r", encoding="utf-8") as f:
            data = json.load(f)
        existing = [Wallet(**w) for w in data]
        if len(existing) >= n:
            logger.info("Loaded %d wallets from %s (using first %d)", len(existing), path, n)
            return existing[:n]
        logger.info("Extending wallets file from %d to %d wallets", len(existing), n)
        while len(existing) < n:
            existing.append(generate_wallet())
        _save_wallets(path, existing)
        return existing

    logger.info("Generating %d fresh sandbox wallets -> %s", n, path)
    wallets = [generate_wallet() for _ in range(n)]
    _save_wallets(path, wallets)
    return wallets


def _save_wallets(path: str, wallets: List[Wallet]) -> None:
    with open(path, "w", encoding="utf-8") as f:
        json.dump([w.__dict__ for w in wallets], f, indent=2)
    try:
        os.chmod(path, 0o600)
    except OSError:
        pass  # non-POSIX


# ---------------------------------------------------------------------------
# Tron client
# ---------------------------------------------------------------------------

class FlashCoinClient:
    """Thin wrapper over tronpy + the FlashCoin contract."""

    def __init__(self, cfg: SimConfig, logger: logging.Logger):
        self.cfg = cfg
        self.logger = logger
        provider = HTTPProvider(cfg.full_node, api_key=cfg.api_key or None)
        self.tron = Tron(provider=provider, network=cfg.network if cfg.network in ("mainnet", "shasta", "nile") else "shasta")
        if not cfg.contract_address:
            raise ValueError("config.contract_address is required")
        self.contract = self.tron.get_contract(cfg.contract_address)
        self.funder = PrivateKey(bytes.fromhex(cfg.funder_private_key)) if cfg.funder_private_key else None

    # ----- reads -------------------------------------------------------------
    def balance_of(self, address: str) -> int:
        return int(self.contract.functions.balanceOf(address))

    def total_supply(self) -> int:
        return int(self.contract.functions.totalSupply())

    def trx_balance(self, address: str) -> int:
        try:
            return self.tron.get_account_balance(address)
        except Exception:
            return 0

    # ----- writes ------------------------------------------------------------
    def _send(self, tx, pk: PrivateKey) -> Dict:
        built = tx.build().sign(pk)
        return built.broadcast().wait()

    def start_distribution(self) -> Dict:
        assert self.funder, "funder_private_key required for owner ops"
        tx = self.contract.functions.startDistribution()
        txb = tx.with_owner(self.funder.public_key.to_base58check_address())
        return self._send(txb, self.funder)

    def set_tranche_size(self, raw_amount: int) -> Dict:
        assert self.funder, "funder_private_key required"
        tx = self.contract.functions.setTrancheSize(raw_amount).with_owner(
            self.funder.public_key.to_base58check_address()
        )
        return self._send(tx, self.funder)

    def toggle_minting(self) -> Dict:
        assert self.funder, "funder_private_key required"
        tx = self.contract.functions.toggleMinting().with_owner(
            self.funder.public_key.to_base58check_address()
        )
        return self._send(tx, self.funder)

    def fund_trx(self, to_address: str, trx_amount: int) -> Dict:
        assert self.funder, "funder_private_key required"
        sun = trx_amount * 1_000_000
        tx = (
            self.tron.trx.transfer(
                self.funder.public_key.to_base58check_address(),
                to_address,
                sun,
            )
        )
        return self._send(tx, self.funder)

    def claim_tranche(self, wallet: Wallet) -> Dict:
        tx = self.contract.functions.claimTranche().with_owner(wallet.address)
        tx = tx.fee_limit(100_000_000)
        return self._send(tx, wallet.pk())

    def transfer(self, sender: Wallet, to_address: str, raw_amount: int) -> Dict:
        tx = (
            self.contract.functions.transfer(to_address, raw_amount)
            .with_owner(sender.address)
            .fee_limit(100_000_000)
        )
        return self._send(tx, sender.pk())


# ---------------------------------------------------------------------------
# Attack modes
# ---------------------------------------------------------------------------

@dataclass
class Stats:
    sent: int = 0
    ok: int = 0
    failed: int = 0
    started_at: float = field(default_factory=time.time)
    tx_hashes: List[str] = field(default_factory=list)

    def record(self, ok: bool, tx_hash: Optional[str] = None) -> None:
        self.sent += 1
        if ok:
            self.ok += 1
            if tx_hash:
                self.tx_hashes.append(tx_hash)
        else:
            self.failed += 1

    def throughput(self) -> float:
        elapsed = max(1e-6, time.time() - self.started_at)
        return self.sent / elapsed

    def report(self, logger: logging.Logger, label: str) -> None:
        logger.info(
            "[%s] sent=%d ok=%d failed=%d tps=%.2f elapsed=%.1fs",
            label, self.sent, self.ok, self.failed,
            self.throughput(), time.time() - self.started_at,
        )


class Simulator:
    def __init__(self, cfg: SimConfig, wallets: List[Wallet], client: FlashCoinClient, logger: logging.Logger):
        self.cfg = cfg
        self.wallets = wallets
        self.client = client
        self.logger = logger

    # ---------------- helpers ----------------
    def _submit(self, fn, *args) -> Optional[str]:
        try:
            res = fn(*args)
            tx_hash = res.get("id") or res.get("txid") or res.get("tx_id") or ""
            if tx_hash:
                self.logger.info("tx ok %s", tx_hash)
            return tx_hash
        except TransactionError as e:
            self.logger.warning("tx failed: %s", e)
        except Exception as e:
            self.logger.warning("tx error: %s: %s", type(e).__name__, e)
        return None

    def _rate_limit(self) -> None:
        if self.cfg.transactions_per_second <= 0:
            return
        time.sleep(1.0 / float(self.cfg.transactions_per_second))

    # ---------------- funding ----------------
    def fund_wallets_with_trx(self) -> None:
        """Every sandbox wallet needs a bit of TRX for energy/bandwidth."""
        self.logger.info("Funding %d wallets with %d TRX each", len(self.wallets), self.cfg.fund_trx_per_wallet)
        for w in self.wallets:
            current = self.client.trx_balance(w.address)
            if current >= self.cfg.fund_trx_per_wallet * 1_000_000:
                continue
            try:
                self.client.fund_trx(w.address, self.cfg.fund_trx_per_wallet)
                self.logger.info("funded %s", w.address)
            except Exception as e:
                self.logger.warning("fund failed for %s: %s", w.address, e)
            self._rate_limit()

    # ---------------- BURST ----------------
    def burst_mode(self, count: Optional[int] = None) -> Stats:
        """Fire `count` random transfers among the wallet set as fast as possible."""
        count = count or self.cfg.burst_count
        stats = Stats()
        self.logger.info("=== BURST MODE: %d transfers, workers=%d ===", count, self.cfg.max_workers)

        raw_amount = max(1, self.cfg.tranche_amount // 100) * 10 ** 6  # 1% of tranche, 6 decimals

        def job(i: int) -> Optional[str]:
            sender = self.wallets[i % len(self.wallets)]
            receiver = random.choice([w for w in self.wallets if w.address != sender.address])
            return self._submit(self.client.transfer, sender, receiver.address, raw_amount)

        with ThreadPoolExecutor(max_workers=self.cfg.max_workers) as pool:
            futures = []
            for i in range(count):
                futures.append(pool.submit(job, i))
                if self.cfg.delay_between_calls > 0:
                    time.sleep(self.cfg.delay_between_calls)
            for fut in as_completed(futures):
                tx_hash = fut.result()
                stats.record(ok=bool(tx_hash), tx_hash=tx_hash)

        stats.report(self.logger, "BURST")
        return stats

    # ---------------- LOOP ----------------
    def loop_transfer_mode(self, hops: Optional[int] = None, cycles: int = 10) -> Stats:
        """A -> B -> C -> ... -> A, repeated `cycles` times over `hops` wallets."""
        hops = hops or self.cfg.loop_hops
        hops = max(3, min(hops, len(self.wallets)))
        ring = self.wallets[:hops]
        stats = Stats()
        self.logger.info("=== LOOP MODE: %d hops x %d cycles ===", hops, cycles)

        raw_amount = max(1, self.cfg.tranche_amount // 10) * 10 ** 6

        for cycle in range(cycles):
            for i in range(hops):
                sender = ring[i]
                receiver = ring[(i + 1) % hops]
                tx_hash = self._submit(self.client.transfer, sender, receiver.address, raw_amount)
                stats.record(ok=bool(tx_hash), tx_hash=tx_hash)
                self._rate_limit()
            self.logger.info("loop cycle %d/%d complete", cycle + 1, cycles)

        stats.report(self.logger, "LOOP")
        return stats

    # ---------------- SYBIL ----------------
    def sybil_mode(self) -> Stats:
        """Every wallet calls claimTranche() concurrently."""
        stats = Stats()
        self.logger.info("=== SYBIL MODE: %d simultaneous claimers ===", len(self.wallets))

        def job(w: Wallet) -> Optional[str]:
            return self._submit(self.client.claim_tranche, w)

        with ThreadPoolExecutor(max_workers=self.cfg.max_workers) as pool:
            futures = [pool.submit(job, w) for w in self.wallets]
            for fut in as_completed(futures):
                tx_hash = fut.result()
                stats.record(ok=bool(tx_hash), tx_hash=tx_hash)

        stats.report(self.logger, "SYBIL")
        return stats


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

BANNER = r"""
============================================================================
 FlashCoin Sandbox Simulator         ** TEST / NON-PRODUCTION **
 Any run against mainnet is blocked by default. Keep it that way.
============================================================================
"""


def main() -> int:
    parser = argparse.ArgumentParser(description="FlashCoin red-team sandbox simulator")
    parser.add_argument("--config", default="config.json", help="Path to config JSON")
    parser.add_argument(
        "--mode",
        choices=("fund", "start-distribution", "burst", "loop", "sybil", "all", "status"),
        required=True,
        help="Action to run",
    )
    parser.add_argument("--count", type=int, default=None, help="Override burst count")
    parser.add_argument("--cycles", type=int, default=10, help="Loop cycles")
    args = parser.parse_args()

    print(BANNER)

    cfg = SimConfig.load(args.config)
    logger = setup_logging(cfg.log_file)
    abort_if_mainnet(cfg)

    wallets = load_or_create_wallets(cfg.wallets_file, cfg.number_of_wallets, logger)
    client = FlashCoinClient(cfg, logger)
    sim = Simulator(cfg, wallets, client, logger)

    if args.mode == "status":
        total = client.total_supply() / 10 ** 6
        logger.info("contract=%s totalSupply=%.6f FLASH", cfg.contract_address, total)
        for w in wallets[:5]:
            bal = client.balance_of(w.address) / 10 ** 6
            trx = client.trx_balance(w.address) / 1_000_000
            logger.info("  %s  FLASH=%.6f  TRX=%.6f", w.address, bal, trx)
        return 0

    if args.mode == "fund":
        sim.fund_wallets_with_trx()
        return 0

    if args.mode == "start-distribution":
        logger.info("Starting distribution on chain...")
        res = client.start_distribution()
        logger.info("result: %s", res.get("id") or res)
        return 0

    if args.mode == "burst":
        sim.burst_mode(count=args.count)
        return 0

    if args.mode == "loop":
        sim.loop_transfer_mode(cycles=args.cycles)
        return 0

    if args.mode == "sybil":
        sim.sybil_mode()
        return 0

    if args.mode == "all":
        sim.fund_wallets_with_trx()
        try:
            client.start_distribution()
        except Exception as e:
            logger.warning("start_distribution: %s (already started?)", e)
        sim.sybil_mode()
        sim.burst_mode(count=args.count)
        sim.loop_transfer_mode(cycles=args.cycles)
        return 0

    return 2


if __name__ == "__main__":
    sys.exit(main())
