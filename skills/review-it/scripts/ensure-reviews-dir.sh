#!/usr/bin/env bash
# Invoked by review-it before writing review reports to `reviews/`.
# Exit codes: 0 (directory ready), non-zero on permission error (set -e propagates).
# Output: prints "ready: <DIR>" on success.
set -euo pipefail

show_help() {
  cat <<'EOF'
Usage: scripts/ensure-reviews-dir.sh [DIR]

Ensure a reviews directory exists.

Arguments:
  DIR   Directory to create. Defaults to: reviews

Examples:
  scripts/ensure-reviews-dir.sh
  scripts/ensure-reviews-dir.sh reviews
EOF
}

if [[ "${1:-}" == "--help" || "${1:-}" == "-h" ]]; then
  show_help
  exit 0
fi

REVIEWS_DIR="${1:-reviews}"

mkdir -p "$REVIEWS_DIR"
echo "ready: $REVIEWS_DIR"
