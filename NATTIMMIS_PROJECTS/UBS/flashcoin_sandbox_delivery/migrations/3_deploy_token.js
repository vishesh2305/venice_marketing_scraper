/**
 * 3_deploy_token.js
 *
 * Deploys the InternalSettlementToken with the previously deployed Timelock
 * as its DEFAULT_ADMIN_ROLE and the previously deployed ComplianceAllowlist
 * as its initial allowlist.
 *
 * Cap and rate-limit values:
 *   - mintCap and rateLimitPerBlock are denominated in smallest units.
 *     The token uses 6 decimals (see InternalSettlementToken.decimals()).
 *   - Defaults below are SIMULATION-SCALE values. Production values are
 *     set through governance after deploy in migration 4.
 */

const SettlementTimelock = artifacts.require('SettlementTimelock');
const ComplianceAllowlist = artifacts.require('ComplianceAllowlist');
const InternalSettlementToken = artifacts.require('InternalSettlementToken');

module.exports = async function (deployer, network) {
  const timelock = await SettlementTimelock.deployed();
  const allowlist = await ComplianceAllowlist.deployed();

  // 100,000,000 IST cap with 6 decimals = 100_000_000 * 1e6
  const initialMintCap = '100000000000000';
  // 1,000,000 IST per block (very generous; tightened post-deploy via gov)
  const initialRateLimit = '1000000000000';

  const name = process.env.TOKEN_NAME || 'Internal Settlement Token';
  const symbol = process.env.TOKEN_SYMBOL || 'IST';

  console.log('[migration 3] Deploying InternalSettlementToken...');
  console.log('  name              :', name);
  console.log('  symbol            :', symbol);
  console.log('  mintCap           :', initialMintCap);
  console.log('  rateLimit/block   :', initialRateLimit);
  console.log('  admin (Timelock)  :', timelock.address);
  console.log('  allowlist         :', allowlist.address);

  await deployer.deploy(
    InternalSettlementToken,
    name,
    symbol,
    initialMintCap,
    initialRateLimit,
    timelock.address,
    allowlist.address
  );
  const token = await InternalSettlementToken.deployed();
  console.log('  -> IST at', token.address);

  console.log(`
==============================================================================
 NEXT STEP — grant operational roles via the Timelock.

 Roles to grant (on the IST token):
   - MINTER_ROLE      -> Treasury issuance service signer
   - BURNER_ROLE      -> Redemption service signer
   - PAUSER_ROLE      -> SOC / incident-response on-call
   - COMPLIANCE_ROLE  -> Compliance team signer (on the allowlist contract)
   - CONFIGURATOR_ROLE -> Engineering operator (rate-limit tuning)

 Each grantRole() call must be queued through the Timelock by the multi-sig
 PROPOSER, wait the minimum delay, and be executed by the multi-sig
 EXECUTOR. See docs/governance/raci.md and scripts/grant_roles.js for the
 exact procedure.
==============================================================================
  `);
};
