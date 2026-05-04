/**
 * Shared deployment fixtures used across the test suite.
 *
 * Each fixture returns a fully wired system in a fresh deployment so unit
 * tests don't accumulate state across each other. We use Hardhat's
 * `loadFixture` to snapshot/revert the EVM state — much faster than
 * redeploying for every test.
 */

const { ethers } = require('hardhat');

const ROLES = {
  DEFAULT_ADMIN: '0x' + '0'.repeat(64),
  MINTER: ethers.keccak256(ethers.toUtf8Bytes('MINTER_ROLE')),
  BURNER: ethers.keccak256(ethers.toUtf8Bytes('BURNER_ROLE')),
  PAUSER: ethers.keccak256(ethers.toUtf8Bytes('PAUSER_ROLE')),
  COMPLIANCE: ethers.keccak256(ethers.toUtf8Bytes('COMPLIANCE_ROLE')),
  CONFIGURATOR: ethers.keccak256(ethers.toUtf8Bytes('CONFIGURATOR_ROLE')),
};

/**
 * Deploys a system where the deployer is the admin (Timelock simulation).
 * For tests that need timelock semantics specifically, use deployWithTimelock.
 */
async function deployBasic() {
  const [admin, minter, burner, pauser, compliance, alice, bob, mallory] =
    await ethers.getSigners();

  const Allowlist = await ethers.getContractFactory('ComplianceAllowlist');
  const allowlist = await Allowlist.deploy(admin.address);
  await allowlist.waitForDeployment();

  const Token = await ethers.getContractFactory('InternalSettlementToken');
  const mintCap = ethers.parseUnits('100000000', 6); // 100M IST
  const rateLimit = ethers.parseUnits('1000000', 6); //   1M IST/block
  const token = await Token.deploy(
    'Internal Settlement Token',
    'IST',
    mintCap,
    rateLimit,
    admin.address,
    await allowlist.getAddress()
  );
  await token.waitForDeployment();

  // Grant operational roles directly (in real life these go via Timelock).
  await token.connect(admin).grantRole(ROLES.MINTER, minter.address);
  await token.connect(admin).grantRole(ROLES.BURNER, burner.address);
  await token.connect(admin).grantRole(ROLES.PAUSER, pauser.address);
  await allowlist.connect(admin).grantRole(ROLES.COMPLIANCE, compliance.address);

  return {
    token,
    allowlist,
    signers: { admin, minter, burner, pauser, compliance, alice, bob, mallory },
    mintCap,
    rateLimit,
  };
}

/**
 * Allowlists alice and bob via the compliance role. Convenience for the
 * many tests that need two allowlisted counterparties.
 */
async function deployWithAllowedAliceAndBob() {
  const sys = await deployBasic();
  const { allowlist, signers } = sys;
  await allowlist.connect(signers.compliance).allow(signers.alice.address, ethers.ZeroHash);
  await allowlist.connect(signers.compliance).allow(signers.bob.address, ethers.ZeroHash);
  return sys;
}

module.exports = { deployBasic, deployWithAllowedAliceAndBob, ROLES };
