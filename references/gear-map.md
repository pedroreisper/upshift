# Gear map — shape → gear → primitive

The full decision table. Read top-to-bottom; the **first** row whose shape matches
the *whole* job is your gear. Bias to the lowest gear that fits.

| Gear | Shape of the work | What you reach for | Don't |
|---|---|---|---|
| **1 — Inline** | One file, one fact, one fully-specified edit. Fits in a few tool calls. | `Read` / `Edit` / `Bash` directly. | Spawn an agent to read one known file. |
| **2 — Fan out** | ≥2 **independent** concerns (review + tests; explore + architect; copy + data). | One `Agent` block, multiple `tool_use`, parallel. Aggregate. | Serialize independent agents; read 8 files inline. |
| **3 — Workflow** | **Many units, same treatment**: migrate all, refactor across repo, audit N modules, review-then-verify dozens. | `ultracode` (Claude auto-decides) or the `Workflow` tool: scout list inline → `pipeline()`/`parallel()`. | Hand-spawn 30 agents; grind it inline. |
| **4 — Background** | Long-running, independent (test suite, build, scrape, deep research). | `run_in_background: true` on `Agent`/`Bash`. | Stall the main thread on a 15-min foreground job. |
| **5 — Scheduled** | Polling / recurring / time-triggered ("keep checking", "every morning", "when CI finishes"). | `/loop`, `ScheduleWakeup`/`send_later`, `CronCreate`/triggers. | Re-run the same check by hand every turn. |

## Picking between adjacent gears

- **2 vs 3** — count the units. A *handful* of *distinct* concerns → Gear 2. *Many* of the *same* unit → Gear 3. The line is roughly 6–8: past that, deterministic orchestration (loops, per-item isolation, verify stages) beats hand-spawning.
- **3 vs 4** — Gear 3 is about *breadth* (many units now); Gear 4 is about *duration* (one job, long). They compose: a workflow can itself run in the background.
- **4 vs 5** — Gear 4 runs **once**, now, async. Gear 5 runs **repeatedly** or **later** on a trigger.

## The human-facing surface (not yours to invoke)

- `/usage` — surface it after an expensive run so the user can see cost drivers.
- `/rewind` — surface it if context was lost to `/clear` or a bad compaction.

Mention in one line, then move on. Never auto-run these.

## The one rule under all of it

Reaching for the right gear on **reversible** work is the job, not a question to ask.
The only stops are genuinely destructive/irreversible actions. Otherwise: shift and go.
