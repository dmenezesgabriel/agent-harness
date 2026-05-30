#!/usr/bin/env bash
# Invoked by prd-it before writing PRD documents.
# Exit codes: 0 (directory ready), non-zero on permission error (set -e propagates).
# Output: prints "ready: <DIR>" on success.
set -euo pipefail

show_help() {
  cat <<'EOF'
Usage: scripts/ensure-prd-dir.sh

Ensure docs/prd directory exists.

Examples:
  scripts/ensure-prd-dir.sh
EOF
}

if [[ "${1:-}" == "--help" || "${1:-}" == "-h" ]]; then
  show_help
  exit 0
fi

mkdir -p docs/prd
echo "ready: docs/prd"
