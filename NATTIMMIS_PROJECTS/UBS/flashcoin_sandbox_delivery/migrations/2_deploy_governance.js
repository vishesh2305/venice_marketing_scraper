/**
 * 2_deploy_governance.js
 *
 * Deploys the SettlementTimelock and ComplianceAllowlist.
 *
 * Sequencing rationale:
 *   - Timelock first: it is the eventual admin of every other contract.
 *   - Allowlist second: receives the Timelock as its DEFAULT_ADMIN_ROLE.
 *
 * Constants:
 *   - MIN_DELAY_SECONDS depends on network. Testnet runs with 1h to keep
 *     rehearsal cycles short; mainnet runs with 48h. Edit the network
 *     branch below before mainnet migration; the value is also recorded
 *     in docs/deployment/staged_rollout.md.
 *
 * Multi-sig assignment:
 *   - On testnets we use a single deployer key as the proposer/executor
 *     to keep CI fast. On mainnet, PROPOSERS and EXECUTORS must be the
 *     production multi-sig addresses (set via MULTISIG_PROPOSERS env).
 */

const SettlementTimelock = artifacts.require('SettlementTimelock');
const ComplianceAllowlist = artifacts.require('ComplianceAllowlist');

module.exports = async function (deployer, network, accounts) {
  const isMainnet = network === 'mainnet';

  const minDelay = isMainnet ? 48 * 60 * 60 : 60 * 60; // 48h vs 1h

  // On mainnet, signers come from env vars sourced from the multi-sig roster.
  // On testnets, default to the deployer key for convenience.
  const proposers = isMainnet
    ? (process.env.MULTISIG_PROPOSERS || '').split(',').filter(Boolean)
    : [accounts[0]];

  const executors = isMainnet
    ? (process.env.MULTISIG_EXECUTORS || '').split(',').filter(Boolean)
    : [accounts[0]];

  if (isMainnet && (proposers.length === 0 || executors.length === 0)) {
    throw new Error(
      'MULTISIG_PROPOSERS and MULTISIG_EXECUTORS must be set for mainnet ' +
        'migration. See docs/governance/multisig_roster.md.'
    );
  }

  // admin = address(0) — Timelock administers itself via queued ops.
  const admin = '0x0000000000000000000000000000000000000000';

  console.log('[migration 2] Deploying SettlementTimelock...');
  console.log('  minDelay  :', minDelay, 'seconds');
  console.log('  proposers :', proposers);
  console.log('  executors :', executors);

  await deployer.deploy(SettlementTimelock, minDelay, proposers, executors, admin);
  const timelock = await SettlementTimelock.deployed();
  console.log('  -> Timelock at', timelock.address);

  console.log('[migration 2] Deploying ComplianceAllowlist...');
  console.log('  admin (Timelock):', timelock.address);
  await deployer.deploy(ComplianceAllowlist, timelock.address);
  const allowlist = await ComplianceAllowlist.deployed();
  console.log('  -> Allowlist at', allowlist.address);
};
