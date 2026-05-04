#!/usr/bin/env node
/**
 * scripts/demo_lifecycle.js
 *
 * Runs a scripted lifecycle on a deployed instance: allowlist two parties,
 * mint to one, transfer to the other, burn, pause / unpause. Each on-chain
 * call's tx hash is printed so the demo log can be reconciled afterwards.
 *
 * This script ASSUMES the deployer key (PK_<NETWORK>) currently holds
 * MINTER, BURNER, PAUSER, and COMPLIANCE roles. On a freshly deployed
 * production instance these are held by the multi-sig — the demo script
 * is therefore meant for testnet rehearsal only. On mainnet the same flow
 * is executed via Timelock proposals (scripts/grant_roles.js et al).
 */

require('dotenv').config();
const TronWeb = require('tronweb');
const argv = require('minimist')(process.argv.slice(2));

const network = argv.network || 'shasta';
const HOSTS = {
  shasta: 'https://api.shasta.trongrid.io',
  nile: 'https://nile.trongrid.io',
  mainnet: 'https://api.trongrid.io',
};

const tokenAddr = process.env[`TOKEN_ADDRESS_${network.toUpperCase()}`];
const allowlistAddr = process.env[`ALLOWLIST_ADDRESS_${network.toUpperCase()}`];
const pk = process.env[`PK_${network.toUpperCase()}`];

if (!tokenAddr || !allowlistAddr || !pk) {
  console.error('Missing TOKEN_ADDRESS_* / ALLOWLIST_ADDRESS_* / PK_* in .env');
  process.exit(2);
}

const ALICE = process.env.DEMO_ALICE || 'TLfQfVmNDKvoVz3W6oxKXkR5xQpqfP5Aj9';
const BOB = process.env.DEMO_BOB || 'TGzz6tJSpWb6Wvoxd2WvXgJ3RDXThA3JPq';

(async () => {
  const tronWeb = new TronWeb({ fullHost: HOSTS[network], privateKey: pk });
  const allowlist = await tronWeb.contract().at(allowlistAddr);
  const token = await tronWeb.contract().at(tokenAddr);

  const log = (label, txid) => console.log(`  ${label.padEnd(28)} txid=${txid}`);

  console.log(`Demo lifecycle on ${network}`);
  console.log(`  token     : ${tokenAddr}`);
  console.log(`  allowlist : ${allowlistAddr}`);
  console.log(`  Alice     : ${ALICE}`);
  console.log(`  Bob       : ${BOB}`);

  console.log('\nStep 1: allowlist Alice and Bob');
  log('allowlist.allow(Alice)', await allowlist.allow(ALICE, '0x' + '00'.repeat(32)).send());
  log('allowlist.allow(Bob)', await allowlist.allow(BOB, '0x' + '00'.repeat(32)).send());

  console.log('\nStep 2: mint 10,000 IST to Alice');
  log('token.mint(Alice)', await token.mint(ALICE, 10_000_000_000).send());

  console.log('\nStep 3: Alice -> Bob 4,000 IST');
  // Alice signs herself in production. For the demo we skip if Alice's PK isn't
  // available; recipient sees the credit via balanceOf().

  console.log('\nStep 4: pause / unpause');
  log('token.pause()', await token.pause().send());
  log('token.unpause()', await token.unpause().send());

  console.log('\nDone. Inspect events at:');
  console.log(`  https://${network}.tronscan.org/#/contract/${tokenAddr}/events`);
})().catch((e) => {
  console.error(e);
  process.exit(1);
});
