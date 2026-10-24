#!/usr/bin/env bash
# Validates every skills/<name>/ against the Agent Skills spec (see CLAUDE.md).
# Usage: scripts/validate-skills.sh [skill-dir ...]   (default: all of skills/*/)
set -euo pipefail

root="$(cd "$(dirname "$0")/.." && pwd)"
validator="$root/research_repos/skills-ref/.venv/bin/skills-ref"

if [[ ! -x "$validator" ]]; then
  echo "skills-ref not installed at $validator; follow 'Validator setup' in CLAUDE.md" >&2
  exit 2
fi

targets=("$@")
[[ ${#targets[@]} -eq 0 ]] && targets=("$root"/skills/*/)

failed=0
for dir in "${targets[@]}"; do
  "$validator" validate "$dir" || failed=1
done
exit "$failed"
