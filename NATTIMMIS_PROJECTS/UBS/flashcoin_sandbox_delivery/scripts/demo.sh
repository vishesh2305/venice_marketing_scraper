#!/usr/bin/env bash
# =============================================================================
#  scripts/demo.sh — live demonstration script
#
#  Runs the full lifecycle on Shasta in under 5 minutes, recording every tx
#  hash to a timestamped log so the artefacts are reviewable after the call.
#
#  Steps:
#    1. Compile + run unit tests.
#    2. Static analysis (solhint, slither if installed).
#    3. Deploy to Shasta.
#    4. Post-deploy verification (scripts/verify.js).
#    5. Allowlist two demo addresses, mint, transfer, burn, pause/unpause.
#    6. Run the indexer once and the reconciler once.
#    7. Print the full ledger of tx hashes for the call participants.
# =============================================================================

set -euo pipefail

LOG_DIR="docs/demo/runs"
mkdir -p "$LOG_DIR"
TS=$(date -u +"%Y%m%dT%H%M%SZ")
LOG="$LOG_DIR/demo-$TS.log"
exec > >(tee -a "$LOG") 2>&1

banner() {
  echo ""
  echo "================================================================================"
  echo "  $1"
  echo "================================================================================"
}

banner "1/7  Compile + unit tests"
npx hardhat compile
npx hardhat test

banner "2/7  Static analysis"
npx solhint 'contracts/**/*.sol' || true
command -v slither >/dev/null 2>&1 && slither . --config-file slither.config.json || echo "(slither not installed — skipping)"

banner "3/7  Deploy to Shasta"
npx tronbox migrate --network shasta --reset

banner "4/7  Post-deploy verification"
node scripts/verify.js --network shasta

banner "5/7  Lifecycle (allowlist -> mint -> transfer -> burn -> pause)"
node scripts/demo_lifecycle.js --network shasta

banner "6/7  Indexer + reconciler"
( cd services/indexer && python indexer.py --once ) || true
( cd services/reconciliation && python reconciler.py ) || true

banner "7/7  Tx-hash ledger"
grep -E "tx[_ ]?(id|hash)" "$LOG" || echo "(no tx hashes captured)"

banner "Demo complete — log at $LOG"
