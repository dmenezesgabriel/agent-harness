#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

npx skills add "$PROJECT_DIR" --skill '*' -y

# Copy skill scripts to scripts/ so agents can call them as
# `bash scripts/<name>.sh` from the project root.
for f in "$PROJECT_DIR"/skills/*/scripts/*.sh; do
  [[ -f "$f" ]] || continue
  dest="$SCRIPT_DIR/$(basename "$f")"
  cp "$f" "$dest"
  chmod +x "$dest"
done
