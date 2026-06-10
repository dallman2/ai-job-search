#!/bin/bash
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
FAILED=0
EXCLUDE_DIRS="--exclude-dir=.git --exclude-dir=node_modules --exclude-dir=__pycache__ --exclude-dir=data"
EXCLUDE_FILES="--exclude=*.pdf --exclude=*.ttf --exclude=*.otf --exclude=*.gif --exclude=*.png --exclude=*.jpg --exclude=*.jpeg"

check_pattern() {
  local pattern="$1"
  local label="$2"
  local hits
  hits=$(grep -rI $EXCLUDE_DIRS $EXCLUDE_FILES "$pattern" "$REPO_ROOT" 2>/dev/null \
    | grep -v "Binary file" \
    | grep -v "scripts/" \
    | grep -v "\.gitignore" \
    | grep -v "Docs/epics/v1.3-open-source-release/" \
    || true)
  if [ -n "$hits" ]; then
    echo "FAIL: $label"
    echo "$hits" | head -10
    FAILED=1
  else
    echo "PASS: $label"
  fi
}

echo "=== Personal Data Audit ==="
echo

check_pattern "Daniel Robert Allman"   "Full name"
check_pattern "dannyallman4@gmail"     "Personal email"
check_pattern "daniel\.allman@capx"    "Work email"
check_pattern "412-848-0206"           "Phone number"

echo
if [ "$FAILED" -eq 1 ]; then
  echo "=== AUDIT FAILED — personal data detected ==="
  exit 1
else
  echo "=== AUDIT PASSED ==="
  exit 0
fi
