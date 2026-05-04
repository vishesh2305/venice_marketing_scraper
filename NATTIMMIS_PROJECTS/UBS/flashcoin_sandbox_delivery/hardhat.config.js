/**
 * Hardhat is used here ONLY for the test suite and coverage tooling.
 * Production deployment runs through tronbox against TRON nodes.
 *
 * The contracts under test are TRC20-compatible Solidity that compile and
 * execute identically on Hardhat's EVM, so we get fast unit/integration tests
 * without spinning up a TRON node. Tronbox is still the source of truth for
 * deployment to Shasta / Nile / Mainnet (see tronbox-config.js).
 */

require('@nomicfoundation/hardhat-toolbox');
require('solidity-coverage');

module.exports = {
  solidity: {
    version: '0.8.21',
    settings: {
      optimizer: { enabled: true, runs: 200 },
      evmVersion: 'istanbul',
    },
  },
  paths: {
    sources: './contracts',
    tests: './test',
    cache: './cache',
    artifacts: './artifacts',
  },
  mocha: {
    timeout: 60000,
  },
};
