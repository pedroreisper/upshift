# Worked examples — one per gear, plus two down-shifts

## Gear 1 — inline (correct down-shift)
> "Fix the typo in the site header."

One file, one edit. `Grep` the string, `Edit` it, done. **No agents.** Spawning a
sub-agent here would cost more context than the fix. Staying in Gear 1 is the win.

## Gear 2 — fan out
> "Review the auth module and write tests for the new validation logic."

Two independent concerns. One `Agent` block with two `tool_use` entries: a
`code-reviewer` on the module + a `test-writer` on the validation. They run in
parallel, return summaries, main thread aggregates. Serializing them would waste
half the wall-clock.

## Gear 3 — workflow
> "Migrate every page in `app/` from the old router to the new one."

Many units, same treatment. **Scout first** (`ls app/**/*.tsx`, find the import
sites), then a `Workflow`: `pipeline(pages, migrateOne, verifyOne)` — each page
migrates and self-verifies independently, worktree-isolated so parallel edits don't
collide. Or just turn on `ultracode` and let Claude escalate. One line on launch:
"~40 pages, one agent each, verify pass on every file."

## Gear 4 — background
> "Run the full integration suite and tell me what fails."

Minutes-long, nothing depends on it immediately. `Bash(run_in_background: true)` or a
background `Agent`. The conversation keeps moving; you're pinged when it exits with
the failure summary. Foregrounding it would freeze the thread for 15 minutes.

## Gear 5 — scheduled
> "Keep an eye on the deploy and ping me when it's live."

A watch loop, not a one-shot. `ScheduleWakeup` every few minutes polling the deploy
status (cache-warm cadence under 5 min), or `/loop`. When status flips to live,
report and stop. Re-running the check by hand each turn is the anti-pattern.

---

## Down-shift example A — resist the workflow reflex
> "Audit this one function for security issues."

"Audit" + "security" tempts Gear 3. But the scope is **one function** — that's Gear 1
(read it, reason, report) or at most a single `code-reviewer` agent. The word "audit"
is not a license to spawn a fleet. Shape, not keywords, picks the gear.

## Down-shift example B — named feature, no routing needed
> "Run a workflow that refactors all the API handlers."

The user already named the capability. Don't deliberate — the routing decision is
made. Go straight to the `Workflow` tool. `upshift` is for when they *didn't* name it.
