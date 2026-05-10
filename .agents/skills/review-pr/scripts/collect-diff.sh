#!/usr/bin/env bash
# scripts/collect-diff.sh — called by review-pr skill
# Usage: collect-diff.sh <base-ref> [<head-ref>]
set -euo pipefail
BASE="${1:?Usage: collect-diff.sh <base-ref> [<head-ref>]}"
HEAD="${2:-HEAD}"
# Structured output to stdout so the agent can parse it
git diff "${BASE}...${HEAD}" --stat --name-only \
  | jq -Rs '{
      "changed_files": split("\n") | map(select(length > 0))
    }' \
  || { printf '{"error":"git diff failed"}\n' >&2; exit 1; }
