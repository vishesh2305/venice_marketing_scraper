/**
 * tronbox-config.js
 *
 * Tronbox network and compiler configuration.
 *
 * Conventions:
 *   - Private keys are NEVER hardcoded. They are loaded from environment
 *     variables, which in turn are sourced from a KMS, Vault, or HSM in
 *     production deployments. See docs/security/key_management_policy.md.
 *   - The `mainnet` network is intentionally last and requires
 *     PK_MAINNET to be set explicitly. Migration to mainnet must be
 *     proposed via the timelock and executed through the multi-sig.
 *     See docs/deployment/staged_rollout.md.
 *   - Fee limits are conservative; tune per migration if necessary.
 */

require('dotenv').config();

const required = (name) => {
  const v = process.env[name];
  if (!v || v.trim() === '') {
    // Throw lazily — only when the network is actually selected — so that
    // running e.g. `tronbox compile` does not require all networks' keys.
    return () => {
      throw new Error(
        `Missing required env var ${name}. ` +
          `Source it from your KMS/Vault before running this network.`
      );
    };
  }
  return () => v;
};

module.exports = {
  networks: {
    // Local development node — tron-quickstart / java-tron private net.
    development: {
      privateKey:
        process.env.PK_DEVELOPMENT ||
        // Default tron-quickstart genesis key. Local-only. Never reused.
        '0000000000000000000000000000000000000000000000000000000000000001',
      userFeePercentage: 100,
      feeLimit: 1_500_000_000,
      fullHost: 'http://127.0.0.1:9090',
      network_id: '9',
    },

    // Public testnets — used for CI/CD, integration testing, dress rehearsal.
    shasta: {
      privateKey: required('PK_SHASTA'),
      userFeePercentage: 50,
      feeLimit: 1_500_000_000,
      fullHost: 'https://api.shasta.trongrid.io',
      network_id: '2',
    },

    nile: {
      privateKey: required('PK_NILE'),
      userFeePercentage: 50,
      feeLimit: 1_500_000_000,
      fullHost: 'https://nile.trongrid.io',
      network_id: '3',
    },

    // Mainnet — requires multi-sig governance proposal and timelock execution.
    // See docs/governance/multisig_roster.md and docs/deployment/staged_rollout.md.
    mainnet: {
      privateKey: required('PK_MAINNET'),
      userFeePercentage: 100,
      feeLimit: 1_500_000_000,
      fullHost: 'https://api.trongrid.io',
      network_id: '1',
    },
  },

  compilers: {
    solc: {
      version: '0.8.21',
      settings: {
        optimizer: { enabled: true, runs: 200 },
        evmVersion: 'istanbul',
      },
    },
  },

  mocha: {
    timeout: 100000,
  },
};
