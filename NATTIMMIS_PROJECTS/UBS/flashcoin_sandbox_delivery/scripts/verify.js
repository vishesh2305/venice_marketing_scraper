#!/usr/bin/env node
/**
 * scripts/verify.js
 *
 * Post-deploy on-chain verification. Reads the deployed contracts and
 * asserts the same invariants checked by 4_post_deploy_verify.js, but
 * runnable independently of the migration sequence — used by the SOC team
 * during their daily check and by CI on a Shasta deployment after every
 * merge to main.
 *
 * Usage:
 *   node scripts/verify.js --network shasta
 *   node scripts/verify.js --network mainnet
 */

require('dotenv').config();
const TronWeb = require('tronweb');

const argv = require('minimist')(process.argv.slice(2));
const network = argv.network || process.env.DEFAULT_NETWORK || 'shasta';

const HOSTS = {
  development: 'http://127.0.0.1:9090',
  shasta: 'https://api.shasta.trongrid.io',
  nile: 'https://nile.trongrid.io',
  mainnet: 'https://api.trongrid.io',
};

const tokenAddr = process.env[`TOKEN_ADDRESS_${network.toUpperCase()}`];
const timelockAddr = process.env[`TIMELOCK_ADDRESS_${network.toUpperCase()}`];
const allowlistAddr = process.env[`ALLOWLIST_ADDRESS_${network.toUpperCase()}`];

if (!tokenAddr || !timelockAddr || !allowlistAddr) {
  console.error(
    `Missing one or more deployment addresses in .env for network=${network}.\n` +
      'Expected TOKEN_ADDRESS_*, TIMELOCK_ADDRESS_*, ALLOWLIST_ADDRESS_*.'
  );
  process.exit(2);
}

const DEFAULT_ADMIN_ROLE = '0x' + '0'.repeat(64);

(async () => {
  const tronWeb = new TronWeb({
    fullHost: HOSTS[network],
    headers: process.env.TRONGRID_API_KEY
      ? { 'TRON-PRO-API-KEY': process.env.TRONGRID_API_KEY }
      : {},
  });
  // Read-only — no signer needed. Set a dummy address for tronWeb internal use.
  tronWeb.setAddress('TLsV52sRDL79HXGGm9yzwKibb6BeruhUzy');

  const checks = [];
  const pass = (m) => checks.push({ status: 'PASS', m });
  const fail = (m) => checks.push({ status: 'FAIL', m });

  const token = await tronWeb.contract().at(tokenAddr);
  const allowlist = await tronWeb.contract().at(allowlistAddr);

  const timelockHasAdminOnToken = await token.hasRole(DEFAULT_ADMIN_ROLE, timelockAddr).call();
  timelockHasAdminOnToken
    ? pass('token DEFAULT_ADMIN_ROLE = Timelock')
    : fail('token DEFAULT_ADMIN_ROLE is NOT the Timelock');

  const timelockHasAdminOnAllowlist = await allowlist
    .hasRole(DEFAULT_ADMIN_ROLE, timelockAddr)
    .call();
  timelockHasAdminOnAllowlist
    ? pass('allowlist DEFAULT_ADMIN_ROLE = Timelock')
    : fail('allowlist DEFAULT_ADMIN_ROLE is NOT the Timelock');

  const enforced = await token.allowlistEnforced().call();
  enforced ? pass('allowlistEnforced = true') : fail('allowlistEnforced is FALSE');

  const wiredAllowlist = (await token.allowlist().call()).toString();
  wiredAllowlist.toLowerCase() === allowlistAddr.toLowerCase()
    ? pass('token.allowlist == deployed ComplianceAllowlist')
    : fail(`token.allowlist=${wiredAllowlist} != ${allowlistAddr}`);

  console.log(`\nverify --network ${network}`);
  for (const c of checks) console.log(`  ${c.status}  ${c.m}`);

  const failed = checks.filter((c) => c.status === 'FAIL');
  if (failed.length) {
    console.error(`\nFAILED: ${failed.length} check(s) did not pass.`);
    process.exit(1);
  }
  console.log('\nAll checks passed.');
})().catch((e) => {
  console.error('verify failed:', e);
  process.exit(1);
});
