#!/usr/bin/env bash
# Prints the next available issue number (zero-padded, 3 digits) and reserves it
# in issues-lock.json. Call once per issue file before writing it.
#
# Usage: bash scripts/next-issue-number.sh [LOCK_FILE] [ISSUES_DIR] [ARCHIVE_DIR]
#
# Exit codes: 0 on success, non-zero on write failure.
# Output: exactly one line — the padded number, e.g. "004"
set -euo pipefail

show_help() {
  cat <<'EOF'
Usage: scripts/next-issue-number.sh [LOCK_FILE] [ISSUES_DIR] [ARCHIVE_DIR]

Print the next available issue number and reserve it in the lock file.

Arguments:
  LOCK_FILE    Path to the JSON counter file. Default: issues-lock.json
  ISSUES_DIR   Active issues directory.  Default: issues
  ARCHIVE_DIR  Archived issues directory. Default: issues/_archive

Output:
  A single zero-padded 3-digit number, e.g. "004"

Examples:
  NUM=$(bash scripts/next-issue-number.sh)
  bash scripts/next-issue-number.sh issues-lock.json issues issues/_archive
EOF
}

if [[ "${1:-}" == "--help" || "${1:-}" == "-h" ]]; then
  show_help
  exit 0
fi

LOCK_FILE="${1:-issues-lock.json}"
ISSUES_DIR="${2:-issues}"
ARCHIVE_DIR="${3:-issues/_archive}"

if [[ -f "$LOCK_FILE" ]]; then
  next_id=$(jq '.next_id' "$LOCK_FILE")
else
  # No lock file yet — derive ceiling from existing files so we never reuse a number.
  highest=0
  for dir in "$ISSUES_DIR" "$ARCHIVE_DIR"; do
    if [[ -d "$dir" ]]; then
      while IFS= read -r f; do
        num=$(basename "$f" | grep -oP '^\d+' || true)
        if [[ -n "$num" ]]; then
          n=$((10#$num))
          (( n > highest )) && highest=$n
        fi
      done < <(find "$dir" -maxdepth 1 -name '*.md' 2>/dev/null)
    fi
  done
  next_id=$(( highest + 1 ))
fi

printf -v padded "%03d" "$next_id"

# Reserve the number: write next_id + 1 back to the lock file.
if [[ -f "$LOCK_FILE" ]]; then
  tmp=$(mktemp)
  jq ".next_id = $(( next_id + 1 ))" "$LOCK_FILE" > "$tmp"
  mv "$tmp" "$LOCK_FILE"
else
  printf '{"next_id": %d}\n' "$(( next_id + 1 ))" | jq . > "$LOCK_FILE"
fi

echo "$padded"
