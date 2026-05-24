#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

# Uninstall skills that have been moved to _deprecated or _on_revision
for subdir in _deprecated _on_revision; do
  if [[ -d "$PROJECT_DIR/skills/$subdir" ]]; then
    mapfile -t stale < <(find "$PROJECT_DIR/skills/$subdir" -maxdepth 1 -mindepth 1 -type d -exec basename {} \;)
    if [[ ${#stale[@]} -gt 0 ]]; then
      npx skills remove "${stale[@]}" -y 2>/dev/null || true
    fi
  fi
done

# Install skills; npx skills add only discovers root-level skills (excludes _* dirs by convention)
npx skills add "$PROJECT_DIR" --skill '*' -y

# Copy skill scripts to scripts/ so agents can call them as
# `bash scripts/<name>.sh` from the project root.
for f in "$PROJECT_DIR"/skills/*/scripts/*.sh; do
  [[ -f "$f" ]] || continue
  dest="$SCRIPT_DIR/$(basename "$f")"
  cp "$f" "$dest"
  chmod +x "$dest"
done
