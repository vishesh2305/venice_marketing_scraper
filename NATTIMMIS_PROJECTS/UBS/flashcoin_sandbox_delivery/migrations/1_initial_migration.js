/**
 * 1_initial_migration.js
 *
 * Tronbox bootstrap migration. Records the deployment marker contract used
 * by tronbox itself to track which migrations have run on each network.
 */

const Migrations = artifacts.require('Migrations');

module.exports = function (deployer) {
  deployer.deploy(Migrations);
};
