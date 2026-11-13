#!/usr/bin/env bash
# Installs skills-ref, the Agent Skills reference validator, into research_repos/skills-ref
# (gitignored), pinned to agentskills commit 69ef37e. Used by CI and once per clone.
# Usage: scripts/install-validator.sh   (no-op when already installed)
set -euo pipefail

commit=69ef37e9424c0a7ea9dd2293b559e43ec8176379
root="$(cd "$(dirname "$0")/.." && pwd)"
target="$root/research_repos/skills-ref"

if [[ -x "$target/.venv/bin/skills-ref" ]]; then
  echo "skills-ref already installed at $target"
  exit 0
fi

work="$(mktemp -d)"
trap 'rm -rf "$work"' EXIT
git clone --quiet --filter=blob:none --sparse https://github.com/agentskills/agentskills.git "$work/as"
git -C "$work/as" checkout --quiet "$commit"
git -C "$work/as" sparse-checkout set skills-ref
mkdir -p "$root/research_repos"
rm -rf "$target"
mv "$work/as/skills-ref" "$target"
# --no-config: uv would otherwise apply this repo's [tool.uv] (exclude-newer, no-build)
# to the nested project, rewrite upstream's lock and refuse to build skills-ref itself.
uv sync --locked --no-config --project "$target"
