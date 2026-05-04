# Smart Contract Risk Register

Mapped against the SCSVS / OWASP Smart Contract Top 10 (2025) plus
TRON-specific findings.

## 1. Access control failures

**Mitigation.** OpenZeppelin `AccessControl` with a closed role enumeration
(`contracts/access/Roles.sol`). Every privileged function uses `onlyRole`.
Roles are granted ONLY by `DEFAULT_ADMIN_ROLE`, which is held by the
Timelock (verified by `migrations/4_post_deploy_verify.js`).

**Tests.**
* `test/unit/access.test.js` — admin holds DEFAULT_ADMIN_ROLE alone, a
  single role does not imply other roles, and `DEFAULT_ADMIN_ROLE` cannot
  move balances.
* `test/unit/token.test.js: rejects mint by a caller without MINTER_ROLE`.

## 2. Price oracle / integer arithmetic

**Mitigation.** No oracle. All arithmetic is in Solidity 0.8.21 with default
overflow checks. The only `unchecked` block is the supply increment in
`_mint`, where the cap check above provably prevents overflow.

## 3. Re-entrancy

**Mitigation.** `mint`, `burn`, `burnFrom` are `nonReentrant`. The token
contract makes no external calls during balance mutation other than reading
`allowlist.isAllowed`, a view-only call to a contract we own.

## 4. Why no proxy / upgradeability

**Tradeoff accepted.** Upgradeability is a meaningful attack surface
(storage-layout collisions, init re-runs, proxy admin takeover). We
deliberately ship a non-upgradeable contract. The cost is that bug fixes
must ship as v2 with a ceremonial migration. The benefit is a much smaller
audit boundary, a frozen storage layout, and a simpler review for the
security team.

The migration procedure for a v2 release is:

1. Multi-sig pauses v1 via Timelock.
2. Multi-sig deploys v2 with the same allowlist, new immutable cap.
3. For each non-zero-balance address on v1, multi-sig calls
   `v1.burnFrom(addr, balance)` (allowance pre-granted via on-chain
   ceremony) and `v2.mint(addr, balance)`. Each step is logged and
   reconciled against the v1 event stream before the next.
4. Publish a "v1 sunset" notice; v1 contract address is recorded in
   `docs/deployment/staged_rollout.md` under "retired contracts".

This is the same pattern used by Centre / USDC and is the operational
posture our internal audit prefers.

## 5. Front-running / MEV

**Risk.** Privileged transactions (mint, allowlist updates) submitted
publicly can be observed before confirmation.

**Mitigation.** Operations that change the allowlist are not commercially
exploitable on their own. Mint operations within the rate limit are
bounded. We do NOT use a private mempool because TRON does not have
established infrastructure for one — the mitigation is the rate limit.

## 6. Denial-of-service via griefing

**Mitigation.** No unbounded loops in privileged paths. `allowBatch` is
the only batched operation; gas limits cap practical batch size and the
caller is the trusted compliance team.

## 7. Source-code authenticity

**Mitigation.** Source verification on TronScan immediately after deploy
(`scripts/verify.js` will produce the hash; manual TronScan submission
documented in `docs/deployment/staged_rollout.md`). `solc` version pinned to
`0.8.21` in `tronbox-config.js` and `hardhat.config.js`. Build is reproducible.

## 8. Allowlist bypass

**Mitigation.** `_beforeTokenTransfer` checks the allowlist on every path
including ERC20's `transferFrom`. Mint and burn use the zero-address
counterparty exemption deliberately, gated by their respective roles.

**Tests.** `test/unit/compliance.test.js: blocks transfer between non-
allowlisted addresses` and integration `lifecycle.test.js`.

## 9. TRON-specific: energy / bandwidth exhaustion

**Risk.** A privileged operator could be DoS'd by lack of energy or
bandwidth, blocking legitimate operations.

**Mitigation.** Multi-sig holders pre-stake TRX for energy. Operations
runbook (`docs/operations/runbook.md`) documents the daily energy check.

## 10. TRON-specific: TVM ↔ EVM divergence

**Risk.** Code that compiles on EVM may behave differently on TVM (e.g.
gas semantics, precompile availability).

**Mitigation.** Hardhat tests give us EVM-level confidence. Tronbox-deploy
to Shasta is required before any mainnet promotion (`docs/deployment/
staged_rollout.md`). The `evmVersion` is pinned to `istanbul` in both
configs to avoid relying on post-Istanbul opcodes that TRON may not have.

## Known open items

| ID | Severity | Item | Owner | Target |
|---|---|---|---|---|
| OPEN-1 | Medium | KMS signer adapter is interface + spec only; full impl during production hardening (`signer.py: AwsKmsSigner._derive_address` raises NotImplementedError). | Eng | Pre-mainnet |
| OPEN-2 | Low | No on-chain registry of role-grant rationale. Off-chain ticket suffices for now. | Gov | Quarter +1 |
| OPEN-3 | Low | Mainnet TronScan source-verification automation not yet scripted. | Eng | Pre-mainnet |
