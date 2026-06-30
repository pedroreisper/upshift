#!/usr/bin/env bash
# doctor.sh — verify the upshift install + hook wiring.
set -uo pipefail

SKILL_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SETTINGS="${HOME}/.claude/settings.json"
HOOK="$SKILL_DIR/hooks/upshift_router.py"
ok=0; warn=0; fail=0
green() { printf '\033[32m✓\033[0m %s\n' "$1"; ok=$((ok+1)); }
yellow(){ printf '\033[33m!\033[0m %s\n' "$1"; warn=$((warn+1)); }
red()   { printf '\033[31m✗\033[0m %s\n' "$1"; fail=$((fail+1)); }

printf 'upshift doctor — %s\n\n' "$SKILL_DIR"

# 1. Core files present
for f in SKILL.md README.md LICENSE hooks/upshift_router.py hooks/install_hook.sh \
         references/gear-map.md references/shape-signals.md references/examples.md; do
  if [ -f "$SKILL_DIR/$f" ]; then green "present: $f"; else red "missing: $f"; fi
done

# 2. Hook parses and runs
if python3 -c "import ast,sys; ast.parse(open('$HOOK').read())" 2>/dev/null; then
  green "hook parses: upshift_router.py"
else
  red "hook has a syntax error: upshift_router.py"
fi

# 3. Hook produces a hint on a Gear-3 prompt and stays silent on a trivial one
g3=$(printf '{"prompt":"migrate every file in app/ to the new router"}' | python3 "$HOOK" 2>/dev/null)
if printf '%s' "$g3" | grep -q "Gear 3"; then green "hook fires Gear 3 on a sweep prompt"; else red "hook did NOT fire on a Gear-3 prompt"; fi
triv=$(printf '{"prompt":"fix the typo in the header"}' | python3 "$HOOK" 2>/dev/null)
if [ -z "$triv" ]; then green "hook stays silent on a trivial prompt"; else yellow "hook emitted on a trivial prompt (over-firing?)"; fi
meta=$(printf '{"prompt":"how does the upshift hook work"}' | python3 "$HOOK" 2>/dev/null)
if [ -z "$meta" ]; then green "hook suppresses meta prompts"; else yellow "hook emitted on a meta prompt"; fi

# 4. Hook wired into settings.json?
if [ -f "$SETTINGS" ] && grep -q "upshift_router.py" "$SETTINGS" 2>/dev/null; then
  green "hook wired into settings.json (proactive mode ON)"
else
  yellow "hook NOT wired — proactive hints off. Enable: bash $SKILL_DIR/hooks/install_hook.sh"
fi

printf '\n%d ok, %d warn, %d fail\n' "$ok" "$warn" "$fail"
[ "$fail" -eq 0 ]
