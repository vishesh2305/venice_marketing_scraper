#!/usr/bin/env node
/**
 * scripts/grant_roles.js
 *
 * Generates the Timelock proposal payload for granting an operational
 * role on the InternalSettlementToken or ComplianceAllowlist.
 *
 * This script does NOT broadcast on-chain. It produces:
 *   1. The encoded calldata.
 *   2. The Timelock schedule() arguments.
 *   3. The expected execute() arguments after the delay matures.
 *
 * The multi-sig PROPOSER then submits schedule(); after the minimum delay,
 * the EXECUTOR submits execute(). Producing the payloads off-chain allows
 * dry-run review by the four-eyes counter-signer before anything reaches
 * the chain. See docs/governance/segregation_of_duties.md.
 *
 * Usage:
 *   node scripts/grant_roles.js \
 *     --network mainnet \
 *     --target token \
 *     --role MINTER_ROLE \
 *     --account TQrZ...
 */

require('dotenv').config();
const TronWeb = require('tronweb');
const argv = require('minimist')(process.argv.slice(2));

const ROLE_LABELS = ['MINTER_ROLE', 'BURNER_ROLE', 'PAUSER_ROLE', 'COMPLIANCE_ROLE', 'CONFIGURATOR_ROLE'];

function usage() {
  console.error(
    'Usage: node scripts/grant_roles.js --network <net> --target <token|allowlist> ' +
      '--role <ROLE_NAME> --account <T...>'
  );
  process.exit(2);
}

if (!argv.network || !argv.target || !argv.role || !argv.account) usage();
if (!['token', 'allowlist'].includes(argv.target)) usage();
if (!ROLE_LABELS.includes(argv.role)) {
  console.error(`Unknown role ${argv.role}. Allowed: ${ROLE_LABELS.join(', ')}`);
  process.exit(2);
}

const tronWeb = new TronWeb({ fullHost: 'https://api.trongrid.io' });
const network = argv.network;
const targetAddr =
  argv.target === 'token'
    ? process.env[`TOKEN_ADDRESS_${network.toUpperCase()}`]
    : process.env[`ALLOWLIST_ADDRESS_${network.toUpperCase()}`];
const timelockAddr = process.env[`TIMELOCK_ADDRESS_${network.toUpperCase()}`];

if (!targetAddr || !timelockAddr) {
  console.error('Missing TARGET / TIMELOCK address in .env for network=' + network);
  process.exit(2);
}

const roleHash = '0x' + tronWeb.sha3(argv.role).slice(2);

// Encode grantRole(bytes32,address)
const grantRoleSelector = tronWeb.sha3('grantRole(bytes32,address)').slice(0, 10);
const param1 = roleHash.slice(2).padStart(64, '0');
const param2 = tronWeb.address.toHex(argv.account).replace(/^41/, '').padStart(64, '0');
const calldata = grantRoleSelector + param1 + param2;

// Timelock.schedule(target, value, data, predecessor, salt, delay)
const salt = '0x' + 'aa'.repeat(32);
const predecessor = '0x' + '00'.repeat(32);

console.log('\n=== Timelock proposal payload ===');
console.log('network         :', network);
console.log('target          :', targetAddr, `(${argv.target})`);
console.log('timelock        :', timelockAddr);
console.log('role            :', argv.role, '(', roleHash, ')');
console.log('account         :', argv.account);
console.log('calldata        :', calldata);
console.log('schedule args   :');
console.log('  target        :', targetAddr);
console.log('  value         : 0');
console.log('  data          :', calldata);
console.log('  predecessor   :', predecessor);
console.log('  salt          :', salt);
console.log('  delay         :  <network minimum>');
console.log('\nNext steps:');
console.log('  1. PROPOSER submits Timelock.schedule(...) with the args above.');
console.log('  2. Wait the minimum delay (testnet 1h, mainnet 48h).');
console.log('  3. EXECUTOR submits Timelock.execute(...) with the same args.');
console.log('  4. Verify with: node scripts/verify.js --network ' + network);
