const { expect } = require('chai');
const { ethers } = require('hardhat');
const { loadFixture } = require('@nomicfoundation/hardhat-toolbox/network-helpers');

const { deployBasic, deployWithAllowedAliceAndBob, ROLES } = require('../helpers/fixtures');

describe('InternalSettlementToken — TRC20 surface', function () {
  it('reports the configured name, symbol, and 6 decimals', async function () {
    const { token } = await loadFixture(deployBasic);
    expect(await token.name()).to.equal('Internal Settlement Token');
    expect(await token.symbol()).to.equal('IST');
    expect(await token.decimals()).to.equal(6);
  });

  it('starts with zero total supply (no constructor mint)', async function () {
    const { token } = await loadFixture(deployBasic);
    expect(await token.totalSupply()).to.equal(0n);
  });

  it('exposes mintCap and rate limit as immutable / configurable values', async function () {
    const { token, mintCap, rateLimit } = await loadFixture(deployBasic);
    expect(await token.mintCap()).to.equal(mintCap);
    expect(await token.mintRateLimitPerBlock()).to.equal(rateLimit);
    expect(await token.remainingMintCap()).to.equal(mintCap);
  });
});

describe('InternalSettlementToken — mint', function () {
  it('mints to an allowlisted address by a MINTER_ROLE holder', async function () {
    const { token, signers } = await loadFixture(deployWithAllowedAliceAndBob);
    const amt = ethers.parseUnits('1000', 6);
    await expect(token.connect(signers.minter).mint(signers.alice.address, amt))
      .to.emit(token, 'Minted')
      .withArgs(signers.alice.address, amt, signers.minter.address);
    expect(await token.balanceOf(signers.alice.address)).to.equal(amt);
  });

  it('rejects mint to a non-allowlisted address', async function () {
    const { token, signers } = await loadFixture(deployBasic);
    await expect(
      token.connect(signers.minter).mint(signers.alice.address, 100n)
    ).to.be.revertedWithCustomError(token, 'NotAllowlisted');
  });

  it('rejects mint by a caller without MINTER_ROLE', async function () {
    const { token, signers } = await loadFixture(deployWithAllowedAliceAndBob);
    await expect(
      token.connect(signers.alice).mint(signers.alice.address, 100n)
    ).to.be.reverted; // OZ AccessControl revert
  });

  it('rejects mint that would exceed the global cap', async function () {
    const { token, signers, mintCap } = await loadFixture(deployWithAllowedAliceAndBob);
    await expect(
      token.connect(signers.minter).mint(signers.alice.address, mintCap + 1n)
    ).to.be.revertedWithCustomError(token, 'MintCapExceeded');
  });

  it('rejects mint that would exceed the per-block rate limit', async function () {
    const { token, signers, rateLimit } = await loadFixture(deployWithAllowedAliceAndBob);
    await expect(
      token.connect(signers.minter).mint(signers.alice.address, rateLimit + 1n)
    ).to.be.revertedWithCustomError(token, 'MintRateLimitExceeded');
  });

  it('rejects mint to the zero address', async function () {
    const { token, signers } = await loadFixture(deployBasic);
    await expect(
      token.connect(signers.minter).mint(ethers.ZeroAddress, 100n)
    ).to.be.revertedWithCustomError(token, 'ZeroAddress');
  });
});

describe('InternalSettlementToken — burn', function () {
  it('burner can burn from own balance after receiving via mint', async function () {
    const { token, allowlist, signers } = await loadFixture(deployWithAllowedAliceAndBob);
    await allowlist.connect(signers.compliance).allow(signers.burner.address, ethers.ZeroHash);
    const amt = ethers.parseUnits('500', 6);
    await token.connect(signers.minter).mint(signers.burner.address, amt);
    await expect(token.connect(signers.burner).burn(amt))
      .to.emit(token, 'Burned')
      .withArgs(signers.burner.address, amt, signers.burner.address);
    expect(await token.totalSupply()).to.equal(0n);
  });

  it('burnFrom requires allowance', async function () {
    const { token, signers } = await loadFixture(deployWithAllowedAliceAndBob);
    const amt = ethers.parseUnits('100', 6);
    await token.connect(signers.minter).mint(signers.alice.address, amt);
    // No approval yet
    await expect(token.connect(signers.burner).burnFrom(signers.alice.address, amt))
      .to.be.reverted;
    await token.connect(signers.alice).approve(signers.burner.address, amt);
    await expect(token.connect(signers.burner).burnFrom(signers.alice.address, amt))
      .to.emit(token, 'Burned')
      .withArgs(signers.alice.address, amt, signers.burner.address);
  });
});

describe('InternalSettlementToken — pause', function () {
  it('pauser can pause and unpause; transfers blocked while paused', async function () {
    const { token, signers } = await loadFixture(deployWithAllowedAliceAndBob);
    const amt = ethers.parseUnits('10', 6);
    await token.connect(signers.minter).mint(signers.alice.address, amt);

    await token.connect(signers.pauser).pause();
    await expect(
      token.connect(signers.alice).transfer(signers.bob.address, amt)
    ).to.be.revertedWith('IST: paused');

    await token.connect(signers.pauser).unpause();
    await token.connect(signers.alice).transfer(signers.bob.address, amt);
    expect(await token.balanceOf(signers.bob.address)).to.equal(amt);
  });

  it('non-pauser cannot pause', async function () {
    const { token, signers } = await loadFixture(deployBasic);
    await expect(token.connect(signers.alice).pause()).to.be.reverted;
  });
});
