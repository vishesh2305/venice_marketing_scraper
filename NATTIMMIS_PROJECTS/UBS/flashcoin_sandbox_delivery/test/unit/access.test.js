const { expect } = require('chai');
const { loadFixture } = require('@nomicfoundation/hardhat-toolbox/network-helpers');

const { deployBasic, ROLES } = require('../helpers/fixtures');

describe('Role hierarchy invariants', function () {
  it('admin holds DEFAULT_ADMIN_ROLE; nobody else does at deploy', async function () {
    const { token, signers } = await loadFixture(deployBasic);
    expect(await token.hasRole(ROLES.DEFAULT_ADMIN, signers.admin.address)).to.equal(true);
    expect(await token.hasRole(ROLES.DEFAULT_ADMIN, signers.alice.address)).to.equal(false);
    expect(await token.hasRole(ROLES.DEFAULT_ADMIN, signers.minter.address)).to.equal(false);
  });

  it('operational roles are independently grantable and revocable', async function () {
    const { token, signers } = await loadFixture(deployBasic);
    expect(await token.hasRole(ROLES.MINTER, signers.minter.address)).to.equal(true);
    await token.connect(signers.admin).revokeRole(ROLES.MINTER, signers.minter.address);
    expect(await token.hasRole(ROLES.MINTER, signers.minter.address)).to.equal(false);
  });

  it('a single role does not imply other roles', async function () {
    const { token, signers } = await loadFixture(deployBasic);
    // minter must NOT be able to pause, even though they're "operational"
    await expect(token.connect(signers.minter).pause()).to.be.reverted;
    // pauser must NOT be able to mint
    await expect(token.connect(signers.pauser).mint(signers.alice.address, 1n)).to.be.reverted;
  });

  it('admin cannot move balances via DEFAULT_ADMIN_ROLE alone', async function () {
    const { token, allowlist, signers } = await loadFixture(deployBasic);
    const { ethers } = require('hardhat');
    await allowlist.connect(signers.compliance).allow(signers.alice.address, ethers.ZeroHash);
    await token.connect(signers.minter).mint(signers.alice.address, 100n);
    // Admin holds DEFAULT_ADMIN_ROLE but not BURNER. So burnFrom must revert.
    await expect(token.connect(signers.admin).burnFrom(signers.alice.address, 100n)).to.be.reverted;
  });
});
