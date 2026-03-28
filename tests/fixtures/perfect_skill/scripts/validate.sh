#!/usr/bin/env bash
# Validate CSV data integrity
set -euo pipefail

FILE="${1:?Usage: validate.sh <file.csv>}"

if [[ ! -f "$FILE" ]]; then
    echo "Error: File not found: $FILE"
    exit 1
fi

# Check for consistent column count
head -1 "$FILE" | awk -F',' '{print NF}' > /tmp/expected_cols
awk -F',' -v expected="$(cat /tmp/expected_cols)" 'NF != expected {print "Line " NR ": expected " expected " columns, got " NF}' "$FILE"

echo "Validation complete."
