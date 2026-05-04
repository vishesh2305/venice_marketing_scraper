/**
 * 4_post_deploy_verify.js
 *
 * Reads the deployed contracts back and asserts every invariant we expect
 * post-deploy. Any mismatch aborts the migration so a misconfigured deploy
 * never silently progresses to the role-grant ceremony.
 */

const SettlementTimelock = artifacts.require('SettlementTimelock');
const ComplianceAllowlist = artifacts.require('ComplianceAllowlist');
const InternalSettlementToken = artifacts.require('InternalSettlementToken');

const DEFAULT_ADMIN_ROLE = '0x' + '0'.repeat(64);

module.exports = async function (_deployer, network) {
  const timelock = await SettlementTimelock.deployed();
  const allowlist = await ComplianceAllowlist.deployed();
  const token = await InternalSettlementToken.deployed();

  const checks = [];
  const fail = (msg) => checks.push(['FAIL', msg]);
  const pass = (msg) => checks.push(['PASS', msg]);

  // Allowlist is administered by the Timelock.
  if (await allowlist.hasRole(DEFAULT_ADMIN_ROLE, timelock.address)) {
    pass('allowlist DEFAULT_ADMIN_ROLE = Timelock');
  } else {
    fail('allowlist DEFAULT_ADMIN_ROLE is NOT the Timelock');
  }

  // Token admin is the Timelock.
  if (await token.hasRole(DEFAULT_ADMIN_ROLE, timelock.address)) {
    pass('token DEFAULT_ADMIN_ROLE = Timelock');
  } else {
    fail('token DEFAULT_ADMIN_ROLE is NOT the Timelock');
  }

  // No operational roles seeded at deploy.
  const MINTER_ROLE = web3.utils.keccak256('MINTER_ROLE');
  const PAUSER_ROLE = web3.utils.keccak256('PAUSER_ROLE');
  if ((await token.getRoleMemberCount(MINTER_ROLE)).toString() === '0') {
    pass('token MINTER_ROLE has no members at deploy time');
  } else {
    fail('token MINTER_ROLE has members at deploy time — should be granted via Timelock only');
  }
  if ((await token.getRoleMemberCount(PAUSER_ROLE)).toString() === '0') {
    pass('token PAUSER_ROLE has no members at deploy time');
  } else {
    fail('token PAUSER_ROLE has members at deploy time — should be granted via Timelock only');
  }

  // Token wired to the deployed allowlist.
  if ((await token.allowlist()).toLowerCase() === allowlist.address.toLowerCase()) {
    pass('token.allowlist == deployed ComplianceAllowlist');
  } else {
    fail('token.allowlist mismatch');
  }

  // Allowlist enforced by default.
  if (await token.allowlistEnforced()) {
    pass('token.allowlistEnforced == true');
  } else {
    fail('token.allowlistEnforced is FALSE — must be true on deploy');
  }

  // Total supply zero at deploy.
  if ((await token.totalSupply()).toString() === '0') {
    pass('token.totalSupply == 0');
  } else {
    fail('token.totalSupply nonzero at deploy');
  }

  console.log('\n[post-deploy verification]');
  for (const [status, msg] of checks) {
    console.log(`  ${status}  ${msg}`);
  }

  const fails = checks.filter(([s]) => s === 'FAIL');
  if (fails.length > 0) {
    throw new Error(`Post-deploy verification failed: ${fails.length} check(s) did not pass.`);
  }

  console.log(`\nDeployment summary on network=${network}:`);
  console.log(`  Timelock           : ${timelock.address}`);
  console.log(`  ComplianceAllowlist: ${allowlist.address}`);
  console.log(`  InternalSettlementToken: ${token.address}`);
  console.log('\nRecord these addresses in .env (TOKEN_ADDRESS_<NETWORK>=...).');
};
