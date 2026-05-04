const { expect } = require('chai');
const { ethers } = require('hardhat');
const { loadFixture, mine } = require('@nomicfoundation/hardhat-toolbox/network-helpers');

const { deployWithAllowedAliceAndBob } = require('../helpers/fixtures');

describe('Lifecycle — issuance, transfer, redemption, incident', function () {
  it('end-to-end: mint -> transfer -> burnFrom -> pause incident', async function () {
    const { token, signers } = await loadFixture(deployWithAllowedAliceAndBob);

    const issued = ethers.parseUnits('10000', 6);
    await token.connect(signers.minter).mint(signers.alice.address, issued);
    expect(await token.totalSupply()).to.equal(issued);

    // Alice settles 4,000 IST to Bob.
    const settled = ethers.parseUnits('4000', 6);
    await token.connect(signers.alice).transfer(signers.bob.address, settled);
    expect(await token.balanceOf(signers.bob.address)).to.equal(settled);

    // Redemption: Bob authorises burner to retire the 4,000.
    await token.connect(signers.bob).approve(signers.burner.address, settled);
    await token.connect(signers.burner).burnFrom(signers.bob.address, settled);
    expect(await token.totalSupply()).to.equal(issued - settled);

    // Incident: SOC pauses.
    await token.connect(signers.pauser).pause();
    await expect(
      token.connect(signers.alice).transfer(signers.bob.address, 1n)
    ).to.be.revertedWith('IST: paused');

    // Resume.
    await token.connect(signers.pauser).unpause();
    await token.connect(signers.alice).transfer(signers.bob.address, 1n);
  });

  it('per-block rate limit resets the next block', async function () {
    const { token, signers, rateLimit } = await loadFixture(deployWithAllowedAliceAndBob);
    await token.connect(signers.minter).mint(signers.alice.address, rateLimit);
    // Same block — anything more should fail.
    await expect(
      token.connect(signers.minter).mint(signers.alice.address, 1n)
    ).to.be.revertedWithCustomError(token, 'MintRateLimitExceeded');
    // Mine a block and the limit resets.
    await mine(1);
    await token.connect(signers.minter).mint(signers.alice.address, 1n);
  });

  it('global cap is hard — no mint past it even across blocks', async function () {
    const { token, signers, mintCap } = await loadFixture(deployWithAllowedAliceAndBob);
    // Lower the rate limit fixture to one block of mintCap to keep the test fast
    // by using the configurator role surface (admin has it).
    const halfCap = mintCap / 2n;
    await token.connect(signers.admin).setMintRateLimitPerBlock(mintCap);
    await token.connect(signers.minter).mint(signers.alice.address, halfCap);
    await mine(1);
    await token.connect(signers.minter).mint(signers.alice.address, halfCap);
    await mine(1);
    await expect(
      token.connect(signers.minter).mint(signers.alice.address, 1n)
    ).to.be.revertedWithCustomError(token, 'MintCapExceeded');
  });
});
