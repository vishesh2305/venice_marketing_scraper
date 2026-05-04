"""
services.keymanagement.signer

Signer abstraction for the InternalSettlementToken operational tooling.

In production, a private key MUST never appear in process memory in plaintext
for longer than the duration of a single broadcast. The signer adapters below
implement that contract by delegating signing to a key custodian (AWS KMS,
HashiCorp Vault) and returning the signed transaction without ever exposing
the underlying key material.

For development and CI, an `env` adapter reads a key from an environment
variable. This adapter is gated on `network != "mainnet"` and refuses to sign
mainnet transactions — a defence-in-depth check that complements the multi-sig
governance gate at the contract layer.

Usage:

    from services.keymanagement import build_signer
    signer = build_signer(network="shasta")
    signed = signer.sign(tron_transaction)
    tx_id = signer.broadcast(signed)
"""

from __future__ import annotations

import abc
import logging
import os
from dataclasses import dataclass
from enum import Enum
from typing import Optional

logger = logging.getLogger("kms.signer")


class SignerBackend(str, Enum):
    ENV = "env"
    AWS_KMS = "aws_kms"
    HASHICORP_VAULT = "hashicorp_vault"


@dataclass
class SignerContext:
    network: str  # "development" | "shasta" | "nile" | "mainnet"
    backend: SignerBackend


class Signer(abc.ABC):
    """Interface for any backend that can sign and broadcast a TRON tx."""

    def __init__(self, ctx: SignerContext):
        self.ctx = ctx

    @abc.abstractmethod
    def address(self) -> str:
        """Return the Base58 address that this signer will sign as."""

    @abc.abstractmethod
    def sign(self, tx) -> object:
        """Sign a tronpy TransactionBuilder/Transaction. Return signed tx."""

    @abc.abstractmethod
    def broadcast(self, signed_tx) -> str:
        """Broadcast and return tx_id. The signed_tx must come from sign()."""


# ---------------------------------------------------------------------------
# Env-backed signer — DEVELOPMENT AND CI ONLY.
# ---------------------------------------------------------------------------

class EnvSigner(Signer):
    """
    Reads a hex private key from an environment variable. Refuses mainnet
    explicitly so a misconfigured operator cannot accidentally sign a mainnet
    transaction with a developer key.
    """

    def __init__(self, ctx: SignerContext):
        super().__init__(ctx)
        if ctx.network == "mainnet":
            raise RuntimeError(
                "EnvSigner refuses mainnet. Use AwsKmsSigner or VaultSigner. "
                "See docs/security/key_management_policy.md."
            )
        var = f"PK_{ctx.network.upper()}"
        pk_hex = os.environ.get(var, "").strip()
        if not pk_hex:
            raise RuntimeError(f"Missing {var} for env signer on {ctx.network}")

        # Late import so this module is importable without tronpy in dev tools
        from tronpy.keys import PrivateKey  # type: ignore

        self._pk = PrivateKey(bytes.fromhex(pk_hex))
        logger.info("EnvSigner loaded for %s as %s", ctx.network, self._pk.public_key.to_base58check_address())

    def address(self) -> str:
        return self._pk.public_key.to_base58check_address()

    def sign(self, tx):
        return tx.build().sign(self._pk)

    def broadcast(self, signed_tx) -> str:
        result = signed_tx.broadcast().wait()
        return result.get("id") or result.get("txid") or ""


# ---------------------------------------------------------------------------
# AWS KMS-backed signer — production.
# ---------------------------------------------------------------------------

class AwsKmsSigner(Signer):
    """
    Signs by asking KMS for a digest signature. The key never leaves the HSM.

    KMS key requirements:
      * KeySpec: ECC_SECG_P256K1 (secp256k1 — same curve as TRON)
      * KeyUsage: SIGN_VERIFY
      * Signing algorithm: ECDSA_SHA_256

    The TRON address is derived from the KMS public key via keccak256, exactly
    like an EOA. A dedicated KMS key per network keeps blast radius small.

    NOTE: This implementation deliberately leaves the digest-conversion and
    DER-to-VRS unpacking as a clearly marked extension point. See
    docs/security/key_management_policy.md §3 for the production rollout plan.
    """

    def __init__(self, ctx: SignerContext, key_id: Optional[str] = None):
        super().__init__(ctx)
        self.key_id = key_id or os.environ.get(f"KMS_KEY_ID_{ctx.network.upper()}")
        if not self.key_id:
            raise RuntimeError(f"KMS_KEY_ID_{ctx.network.upper()} not set")

        try:
            import boto3  # type: ignore
        except ImportError as e:
            raise RuntimeError("boto3 not installed. pip install boto3") from e

        self._kms = boto3.client("kms", region_name=os.environ.get("AWS_REGION", "us-east-1"))
        # Cache the public key + derived address — never changes.
        self._address: Optional[str] = None
        logger.info("AwsKmsSigner initialised for %s (key=%s)", ctx.network, self.key_id)

    def address(self) -> str:
        if self._address is None:
            self._address = self._derive_address()
        return self._address

    def _derive_address(self) -> str:
        """Resolve KMS public key -> TRON Base58 address. Filled in during the
        production hardening phase. Tracked in
        docs/security/key_management_policy.md §3.2."""
        raise NotImplementedError(
            "AwsKmsSigner.address derivation is implemented during the "
            "production hardening phase. See docs/security/key_management_policy.md."
        )

    def sign(self, tx):
        raise NotImplementedError(
            "AwsKmsSigner.sign is implemented during the production hardening phase. "
            "See docs/security/key_management_policy.md §3.3."
        )

    def broadcast(self, signed_tx) -> str:
        result = signed_tx.broadcast().wait()
        return result.get("id") or result.get("txid") or ""


# ---------------------------------------------------------------------------
# HashiCorp Vault-backed signer — alternative production signer.
# ---------------------------------------------------------------------------

class VaultSigner(Signer):
    """
    Signs through Vault's Transit secrets engine (configured for secp256k1).
    The key never leaves Vault. Audit log of signatures is provided by Vault
    itself, which is how SOC reconstructs operator activity.
    """

    def __init__(self, ctx: SignerContext, transit_key: Optional[str] = None):
        super().__init__(ctx)
        self.transit_key = transit_key or os.environ.get(f"VAULT_TRANSIT_KEY_{ctx.network.upper()}")
        if not self.transit_key:
            raise RuntimeError(f"VAULT_TRANSIT_KEY_{ctx.network.upper()} not set")

        try:
            import hvac  # type: ignore
        except ImportError as e:
            raise RuntimeError("hvac not installed. pip install hvac") from e

        self._client = hvac.Client(
            url=os.environ.get("VAULT_ADDR", ""),
            token=os.environ.get("VAULT_TOKEN", ""),
        )
        if not self._client.is_authenticated():
            raise RuntimeError("Vault client failed to authenticate")
        logger.info("VaultSigner initialised for %s (transit_key=%s)", ctx.network, self.transit_key)

    def address(self) -> str:
        raise NotImplementedError("VaultSigner.address — production hardening phase.")

    def sign(self, tx):
        raise NotImplementedError("VaultSigner.sign — production hardening phase.")

    def broadcast(self, signed_tx) -> str:
        result = signed_tx.broadcast().wait()
        return result.get("id") or result.get("txid") or ""


# ---------------------------------------------------------------------------
# Factory
# ---------------------------------------------------------------------------

def build_signer(network: str, backend: Optional[str] = None) -> Signer:
    """
    Construct a Signer for the given network. Backend resolution order:
      1. Explicit `backend` argument (if provided).
      2. SIGNER_BACKEND environment variable.
      3. Default: env (development), aws_kms (mainnet).
    """
    chosen = backend or os.environ.get("SIGNER_BACKEND")
    if not chosen:
        chosen = "aws_kms" if network == "mainnet" else "env"

    try:
        be = SignerBackend(chosen)
    except ValueError as e:
        raise RuntimeError(f"Unknown SIGNER_BACKEND={chosen!r}") from e

    ctx = SignerContext(network=network, backend=be)
    if be is SignerBackend.ENV:
        return EnvSigner(ctx)
    if be is SignerBackend.AWS_KMS:
        return AwsKmsSigner(ctx)
    if be is SignerBackend.HASHICORP_VAULT:
        return VaultSigner(ctx)
    raise RuntimeError(f"Unhandled backend {be}")
