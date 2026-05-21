# implement-it/scripts/ensure-implementation-dir.sh
#!/usr/bin/env bash
# Invoked by implement-it before writing implementation summaries to `tasks/implementation/`.
# Exit codes: 0 (directory ready), non-zero on permission error (set -e propagates).
# Output: prints "ready: <DIR>" on success.
set -euo pipefail

show_help() {
  cat <<'EOF'
Usage: scripts/ensure-implementation-dir.sh [DIR]

Ensure an implementation summary directory exists.

Arguments:
  DIR   Directory to create. Defaults to: tasks/implementation

Examples:
  scripts/ensure-implementation-dir.sh
  scripts/ensure-implementation-dir.sh tasks/implementation
EOF
}

if [[ "${1:-}" == "--help" || "${1:-}" == "-h" ]]; then
  show_help
  exit 0
fi

IMPLEMENTATION_DIR="${1:-tasks/implementation}"

mkdir -p "$IMPLEMENTATION_DIR"
echo "ready: $IMPLEMENTATION_DIR"
