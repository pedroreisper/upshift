#!/usr/bin/env bash
# install_hook.sh — wire the upshift UserPromptSubmit hook into ~/.claude/settings.json
set -euo pipefail

SKILL_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
HOOK_PATH="$SKILL_DIR/hooks/upshift_router.py"
SETTINGS="${HOME}/.claude/settings.json"

if [ ! -f "$HOOK_PATH" ]; then
  printf 'hook not found: %s\n' "$HOOK_PATH" >&2
  exit 1
fi

chmod +x "$HOOK_PATH"

mkdir -p "$(dirname "$SETTINGS")"
[ -f "$SETTINGS" ] || printf '{}\n' > "$SETTINGS"

cp "$SETTINGS" "$SETTINGS.bak.$(date +%s)"

python3 - "$SETTINGS" "$HOOK_PATH" <<'PY'
import json, sys, pathlib

settings_path = pathlib.Path(sys.argv[1])
hook_cmd = sys.argv[2]

data = json.loads(settings_path.read_text() or "{}")
hooks = data.setdefault("hooks", {})
ups_hooks = hooks.setdefault("UserPromptSubmit", [])

# Remove any prior install of this same hook to avoid duplicates.
def is_ours(entry):
    if not isinstance(entry, dict):
        return False
    for h in entry.get("hooks", []):
        if isinstance(h, dict) and h.get("command", "").endswith("upshift_router.py"):
            return True
    return False

ups_hooks[:] = [e for e in ups_hooks if not is_ours(e)]

ups_hooks.append({
    "matcher": "",
    "hooks": [
        {"type": "command", "command": f"python3 {hook_cmd}"}
    ],
})

settings_path.write_text(json.dumps(data, indent=2) + "\n")
print(f"wired UserPromptSubmit hook → {hook_cmd}")
PY

printf '\n\033[32m✓\033[0m upshift UserPromptSubmit hook installed.\n'
printf '   Backup of previous settings: %s.bak.<ts>\n' "$SETTINGS"
printf '   To uninstall: edit %s and remove the UserPromptSubmit entry that points to upshift_router.py.\n' "$SETTINGS"
