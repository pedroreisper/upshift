#!/usr/bin/env bash
# run-tests.sh — assert the upshift hook classifies each fixture prompt correctly.
# Each fixture line: <prompt><TAB><expect>  where expect = 1..5 (primary gear) or "silent".
set -uo pipefail

DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
HOOK="$DIR/../hooks/upshift_router.py"
CASES="$DIR/fixtures/cases.tsv"
pass=0; fail=0

while IFS=$'\t' read -r prompt expect; do
  [ -z "${prompt:-}" ] && continue
  case "$prompt" in \#*) continue;; esac
  out=$(printf '{"prompt":%s}' "$(python3 -c 'import json,sys; print(json.dumps(sys.argv[1]))' "$prompt")" | python3 "$HOOK" 2>/dev/null)
  if [ "$expect" = "silent" ]; then
    if [ -z "$out" ]; then pass=$((pass+1)); else
      fail=$((fail+1)); printf '\033[31mFAIL\033[0m expected silent, got hint: %s\n' "$prompt"
    fi
  else
    # Primary gear is the first "Gear N" mentioned in the output.
    got=$(printf '%s' "$out" | grep -o 'Gear [1-5]' | head -1 | grep -o '[1-5]')
    if [ "$got" = "$expect" ]; then pass=$((pass+1)); else
      fail=$((fail+1)); printf '\033[31mFAIL\033[0m expected Gear %s, got "%s": %s\n' "$expect" "${got:-none}" "$prompt"
    fi
  fi
done < "$CASES"

printf '\n%d passed, %d failed\n' "$pass" "$fail"
[ "$fail" -eq 0 ]
