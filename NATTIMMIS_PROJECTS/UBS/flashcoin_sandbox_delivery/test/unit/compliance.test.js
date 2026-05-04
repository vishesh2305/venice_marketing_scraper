const { expect } = require('chai');
const { ethers } = require('hardhat');
const { loadFixture } = require('@nomicfoundation/hardhat-toolbox/network-helpers');

const { deployBasic, deployWithAllowedAliceAndBob } = require('../helpers/fixtures');

describe('ComplianceAllowlist', function () {
  it('only COMPLIANCE_ROLE can allow', async function () {
    const { allowlist, signers } = await loadFixture(deployBasic);
    await expect(
      allowlist.connect(signers.alice).allow(signers.bob.address, ethers.ZeroHash)
    ).to.be.reverted;
    await expect(
      allowlist.connect(signers.compliance).allow(signers.bob.address, ethers.ZeroHash)
    ).to.emit(allowlist, 'AddressAllowed');
    expect(await allowlist.isAllowed(signers.bob.address)).to.equal(true);
  });

  it('rejects zero address and double-allow', async function () {
    const { allowlist, signers } = await loadFixture(deployBasic);
    await expect(
      allowlist.connect(signers.compliance).allow(ethers.ZeroAddress, ethers.ZeroHash)
    ).to.be.revertedWithCustomError(allowlist, 'ZeroAddress');

    await allowlist.connect(signers.compliance).allow(signers.bob.address, ethers.ZeroHash);
    await expect(
      allowlist.connect(signers.compliance).allow(signers.bob.address, ethers.ZeroHash)
    ).to.be.revertedWithCustomError(allowlist, 'AlreadyAllowed');
  });

  it('revoke removes from allowlist; reference hash retained for audit', async function () {
    const { allowlist, signers } = await loadFixture(deployBasic);
    const ref = ethers.keccak256(ethers.toUtf8Bytes('case-12345'));
    await allowlist.connect(signers.compliance).allow(signers.bob.address, ref);
    await expect(allowlist.connect(signers.compliance).revoke(signers.bob.address))
      .to.emit(allowlist, 'AddressRevoked')
      .withArgs(signers.bob.address, signers.compliance.address);
    expect(await allowlist.isAllowed(signers.bob.address)).to.equal(false);
    expect(await allowlist.referenceHashOf(signers.bob.address)).to.equal(ref);
  });
});

describe('Token integration with allowlist', function () {
  it('blocks transfer between non-allowlisted addresses', async function () {
    const { token, signers } = await loadFixture(deployBasic);
    await expect(
      token.connect(signers.alice).transfer(signers.bob.address, 1n)
    ).to.be.reverted;
  });

  it('admin can disable allowlist enforcement (loud event)', async function () {
    const { token, signers } = await loadFixture(deployBasic);
    await expect(token.connect(signers.admin).setAllowlistEnforced(false))
      .to.emit(token, 'AllowlistEnforcementChanged')
      .withArgs(false);
    expect(await token.allowlistEnforced()).to.equal(false);
  });

  it('non-admin cannot disable allowlist enforcement', async function () {
    const { token, signers } = await loadFixture(deployBasic);
    await expect(token.connect(signers.alice).setAllowlistEnforced(false)).to.be.reverted;
  });

  it('transfers work between allowlisted parties end-to-end', async function () {
    const { token, signers } = await loadFixture(deployWithAllowedAliceAndBob);
    const amt = ethers.parseUnits('25', 6);
    await token.connect(signers.minter).mint(signers.alice.address, amt);
    await token.connect(signers.alice).transfer(signers.bob.address, amt);
    expect(await token.balanceOf(signers.bob.address)).to.equal(amt);
  });
});
