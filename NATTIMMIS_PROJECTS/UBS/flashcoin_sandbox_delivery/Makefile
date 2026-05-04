# =============================================================================
#  Internal Settlement Token — operational make targets
# =============================================================================

.PHONY: help install compile test coverage lint audit migrate-shasta migrate-nile \
        migrate-mainnet verify clean indexer reconcile stress

help:
	@echo "Internal Settlement Token — available targets"
	@echo ""
	@echo "  install            Install Node and Python dependencies"
	@echo "  compile            Compile contracts (tronbox)"
	@echo "  test               Run Hardhat unit + integration test suite"
	@echo "  coverage           Run coverage report"
	@echo "  lint               solhint over contracts/"
	@echo "  audit              Static analysis: solhint + slither + gitleaks"
	@echo ""
	@echo "  migrate-shasta     Deploy to TRON Shasta testnet"
	@echo "  migrate-nile       Deploy to TRON Nile testnet"
	@echo "  migrate-mainnet    Deploy to TRON mainnet (requires multi-sig)"
	@echo "  verify             Post-deploy verification (on-chain reads + role checks)"
	@echo ""
	@echo "  indexer            Run event indexer service"
	@echo "  reconcile          Run reconciliation service"
	@echo "  stress             Run stress simulator (testnet only by default)"
	@echo ""
	@echo "  clean              Remove build artefacts"

install:
	npm ci
	cd services/keymanagement && pip install -r requirements.txt
	cd services/indexer && pip install -r requirements.txt
	cd services/reconciliation && pip install -r requirements.txt
	cd services/stress && pip install -r requirements.txt

compile:
	npx tronbox compile

test:
	npx hardhat test

coverage:
	npx hardhat coverage

lint:
	npx solhint 'contracts/**/*.sol'

audit:
	npx solhint 'contracts/**/*.sol'
	@command -v slither >/dev/null 2>&1 && slither . --config-file slither.config.json || echo "slither not installed — skipping"
	@command -v gitleaks >/dev/null 2>&1 && gitleaks detect --source . --redact --config .gitleaks.toml || echo "gitleaks not installed — skipping"

migrate-shasta:
	npx tronbox migrate --network shasta

migrate-nile:
	npx tronbox migrate --network nile

migrate-mainnet:
	@echo "Mainnet migration must follow docs/deployment/staged_rollout.md"
	@echo "Press ^C now if you have not completed the preflight checklist."
	@sleep 5
	npx tronbox migrate --network mainnet

verify:
	node scripts/verify.js

indexer:
	cd services/indexer && python indexer.py

reconcile:
	cd services/reconciliation && python reconciler.py

stress:
	cd services/stress && python simulator.py --mode status

clean:
	rm -rf build/ artifacts/ cache/ coverage/ node_modules/.cache
