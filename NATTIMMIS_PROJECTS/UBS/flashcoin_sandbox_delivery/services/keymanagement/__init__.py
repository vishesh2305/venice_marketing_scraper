"""Signer abstraction. See signer.py for the interface."""
from .signer import Signer, SignerBackend, build_signer

__all__ = ["Signer", "SignerBackend", "build_signer"]
