#!/usr/bin/env bash
# Invoked by contract-it before writing contract documents.
# Exit codes: 0 (directory ready), non-zero on permission error (set -e propagates).
# Output: prints "ready: <DIR>" on success.
set -euo pipefail

show_help() {
  cat <<'EOF'
Usage: scripts/ensure-contracts-dir.sh

Ensure docs/contracts directory exists.

Examples:
  scripts/ensure-contracts-dir.sh
EOF
}

if [[ "${1:-}" == "--help" || "${1:-}" == "-h" ]]; then
  show_help
  exit 0
fi

mkdir -p docs/contracts
echo "ready: docs/contracts"
