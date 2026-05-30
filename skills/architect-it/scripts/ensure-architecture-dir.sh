#!/usr/bin/env bash
# Invoked by architect-it before writing architecture documents and ADR stubs.
# Exit codes: 0 (directories ready), non-zero on permission error (set -e propagates).
# Output: prints "ready: <DIR>" for each directory created or confirmed.
set -euo pipefail

show_help() {
  cat <<'EOF'
Usage: scripts/ensure-architecture-dir.sh

Ensure docs/architecture and docs/adrs directories exist.

Examples:
  scripts/ensure-architecture-dir.sh
EOF
}

if [[ "${1:-}" == "--help" || "${1:-}" == "-h" ]]; then
  show_help
  exit 0
fi

mkdir -p docs/architecture docs/adrs
echo "ready: docs/architecture"
echo "ready: docs/adrs"
