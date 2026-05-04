# Key Management Policy

This document defines how every key that can sign a TRON transaction on
behalf of the IST infrastructure is generated, stored, used, rotated, and
retired. It is binding on every team that holds a role in the system.

## 1. Principles

1. **No raw key material on disk.** Production keys live exclusively
   inside an HSM-backed custodian (AWS KMS or HashiCorp Vault Transit).
   They never appear in environment variables, source code, container
   images, or backups in plaintext form.
2. **One key per role per network.** Mixing roles across keys defeats
   blast-radius limits. Mixing networks across keys defeats the
   testnet/mainnet barrier.
3. **Audit log is mandatory and external.** The custodian's audit log
   (CloudTrail / Vault audit device) must be enabled before a key is used
   for the first time. A key whose audit log is disabled is treated as
   compromised.
4. **Multi-sig is preferred over single-key for any role with material
   blast radius** — definitively for `DEFAULT_ADMIN_ROLE`, recommended
   for `MINTER_ROLE` if the per-block rate limit is non-trivial.

## 2. Key inventory

| Key | Holder | Backend | Notes |
|---|---|---|---|
| Multi-sig signer share #1 .. #N | Named officers (per `docs/governance/multisig_roster.md`) | YubiKey + KMS-encrypted backup | m-of-n threshold |
| `MINTER_ROLE` operator | Treasury issuance service | KMS asymmetric secp256k1 | Per-block rate limit caps blast |
| `BURNER_ROLE` operator | Redemption service | KMS asymmetric secp256k1 | |
| `PAUSER_ROLE` operator | SOC on-call | KMS, with role-grant rotated weekly | Lower blast radius — DoS only |
| `COMPLIANCE_ROLE` operator | Compliance team service account | Vault Transit | |
| Testnet keys (Shasta / Nile) | CI runner | GitHub Actions secret | Disposable; rotated quarterly or on incident |
| Local dev keys | Individual developers | `.env` file in git-ignored location | Local network only |

## 3. AWS KMS adapter (production)

**Implementation entry point:** `services/keymanagement/signer.py:AwsKmsSigner`.

### 3.1 Key creation

```bash
aws kms create-key \
  --key-spec ECC_SECG_P256K1 \
  --key-usage SIGN_VERIFY \
  --description "IST MINTER_ROLE — mainnet"

aws kms create-alias --alias-name alias/ist-minter-mainnet --target-key-id <key-id>
```

The key policy MUST:

* Permit `kms:Sign` only from the issuance service IAM role.
* Deny `kms:Decrypt` (the key is never used to decrypt).
* Require `aws:MultiFactorAuthPresent=true` for `kms:ScheduleKeyDeletion`.

### 3.2 Address derivation

The TRON address corresponding to a KMS key is derived by:

1. `kms:GetPublicKey` returns the SubjectPublicKeyInfo (DER).
2. Strip the SPKI envelope to get the 64-byte uncompressed `(x, y)` point.
3. `keccak256(point)[12:]` is the 20-byte EVM address.
4. TRON Base58 address is `base58check(0x41 || evm_address)`.

This is a one-time derivation; the address is then cached in `.env` and
in the `MINTER_OPERATOR_ADDR_MAINNET` config setting.

### 3.3 Signing flow

1. Tronbox / TronWeb builds the transaction and computes its txID hash.
2. Operator calls `kms:Sign(KeyId=<id>, Message=<txID>, MessageType=DIGEST,
   SigningAlgorithm=ECDSA_SHA_256)`.
3. KMS returns a DER signature. Convert to TRON's `(r, s, v)` tuple
   (the `v` recovery byte is brute-forced from the public key).
4. Attach the signature to the transaction and broadcast.

The implementation lives in `signer.py` and is **currently a stub** marked
with `NotImplementedError`. This is tracked as `OPEN-1` in
`smart_contract_risks.md` and is the gating item for the mainnet promotion.

## 4. HashiCorp Vault adapter (alternative)

**Implementation entry point:** `services/keymanagement/signer.py:VaultSigner`.

* Vault Transit secrets engine, `secp256k1` curve, `signature_algorithm=
  pkcs1v15` (raw ECDSA via the `sign_via_pkcs1v15` API path).
* Same address-derivation and signature-conversion logic as the KMS path.
* Vault audit device must be configured to log to the bank's central SIEM.

## 5. Key rotation

| Key class | Rotation cadence | Rotation procedure |
|---|---|---|
| Multi-sig signer shares | On signer departure within 1 business day; otherwise annually | Generate new share, propose `revokeRole` + `grantRole` via Timelock |
| Operator role keys (MINTER, BURNER, PAUSER, COMPLIANCE) | Quarterly, or on suspicion within 1h | Generate new KMS key, dual-sign Timelock proposal |
| Testnet keys | Quarterly, or on incident | Auto-generate via CI; update GitHub Actions secret |
| Local dev keys | At developer discretion | `.env` regeneration |

## 6. Recovery and emergency

There is **no key-recovery escrow.** Loss of a multi-sig threshold means
the system migrates to v2 (`smart_contract_risks.md` §4). The cost is one
ceremonial mint/burn migration; the benefit is the absence of an "emergency
recovery key" that would itself be the largest single point of compromise.

## 7. Forbidden practices

* **Never** export a private key from KMS / Vault. The export API on KMS
  is disabled by key policy; on Vault by the engine configuration.
* **Never** sign a mainnet transaction with `EnvSigner`. The class refuses
  this in code (`signer.py:EnvSigner.__init__`).
* **Never** commit a private key, mnemonic, or `.env` file. `.gitignore`
  enforces this; `gitleaks` runs on every PR.
* **Never** reuse a testnet key on mainnet. Keys are network-tagged.

## 8. Periodic review

* Quarterly: this document reviewed against actual KMS / Vault state.
* On incident: within 5 business days.
* On mainnet rotation: within 1 business day of completion.
