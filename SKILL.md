---
name: upshift
description: Makes Claude Code match the execution gear to the shape of the work — and reach for it WITHOUT being told the feature's name. Picks across the capability surface: inline, parallel sub-agents, Workflow/ultracode, background agent, or scheduled run. Use when the user says "be thorough", "do all of these", "migrate everything", "audit the whole codebase", "keep checking", "run this in the background", "faz tudo", "trata de tudo", "em massa", "de forma autónoma", or whenever a task is bigger than a single inline pass but no feature was named. Also fires proactively (soft UserPromptSubmit gear hint). NOT a keyword→skill router (routes execution capabilities, not skills) and NOT a verifier (that's did-it-actually).
license: MIT
metadata:
  version: "1.0.0"
  priority: "8"
  audience: "claude-code"
---

# upshift — match the gear to the road

Most of Claude Code's power sits idle because the user has to *name the feature* before Claude uses it. They have to say "use a workflow", "run it in the background", "fan out agents", "schedule it". They rarely do. So Claude grinds a 200-file migration through one inline loop, or hand-spawns five agents for work that wanted a `Workflow`, or blocks the main thread on a 20-minute test run that should have been backgrounded.

This skill removes the naming requirement. **You** read the *shape* of the request and shift into the right gear yourself — up when the road demands it, down so you never over-engineer a one-liner.

## The core rule

**Classify the shape before you act. Pick the lowest gear that fits the whole job — then commit to it.**

Before starting non-trivial work, ask one question: *what shape is this?* The answer selects the gear. You do not wait to be told "use a workflow" any more than a driver waits to be told to change gear on a hill. Reaching for the right capability on reversible work is never something to ask permission for — it's the job.

## The five gears

Shift **up** as the work gets larger / more parallel / longer-running. Shift **down** to avoid over-engineering. One gear per job; don't fan out what a single read answers, don't inline what wants a workflow.

### Gear 1 — Inline (just do it)

**Shape:** one file, one fact, one fully-specified edit. The answer fits in a few tool calls.

**Do:** `Read`/`Edit`/`Bash` directly in the main thread. No agents, no ceremony.

**Smell of the wrong gear:** spawning an agent to read a single known file. That's upshifting into noise — downshift.

### Gear 2 — Parallel sub-agents (fan out)

**Shape:** the request spans **≥2 independent concerns** — review code *and* write tests; explore *and* architect; draft copy *and* validate data. Each concern has its own context.

**Do:** one `Agent` tool block, multiple `tool_use` entries, in parallel. Each agent owns one concern, returns a summary; the main thread aggregates. Never serialize independent agents.

**Smell:** reading 8 files in the main thread when one `Explore`/`code-explorer` agent would return the map. Or running `Agent → wait → Agent → wait` for calls with no dependency between them.

### Gear 3 — Workflow / ultracode (large, repetitive, parallelisable)

**Shape:** **many units processed the same way**, or an exhaustive sweep: migrate every file, refactor across the codebase, audit N modules, review-then-verify dozens of findings, process a list of 20+ items. More units than you'd hand-spawn.

**Do:** prefer Claude Code's native escalation — turn on `ultracode` (or `/effort ultracode`), which lets Claude **decide on its own** to run a Workflow for the task. When you're authoring the orchestration yourself, use the `Workflow` tool: **scout the work-list inline first** (list the files, find the call-sites, scope the diff), then `pipeline()` / `parallel()` over it. Pipeline by default — only barrier (`parallel` between stages) when a stage genuinely needs all prior results at once.

**Why not just fan out (Gear 2)?** Past ~6–8 units, hand-spawning loses to deterministic orchestration: a workflow gives you loops, per-item isolation (worktrees), adversarial verify stages, and a clean main context. Gear 2 is for a handful of *distinct* concerns; Gear 3 is for *many* of the *same* unit.

**Cost honesty:** a workflow can spawn dozens of agents. It's the right call for genuinely large work — but say the cost shape in one line when you launch it ("~20 agents, one per module"). Don't silently fan out 100 agents.

### Gear 4 — Background agent (long-running, independent)

**Shape:** a job that takes minutes and doesn't block the next step — a full test suite, a build, a scrape, a deep-research pass, a large refactor you can verify later.

**Do:** spawn it with `run_in_background: true` (on `Agent` or `Bash`). The main thread keeps moving; you're notified on completion. Don't make the user watch a spinner for work that could run async.

**Smell:** a foreground `Bash` call you *know* will run 15 minutes while the conversation stalls. Background it.

### Gear 5 — Scheduled / recurring (polling or later)

**Shape:** "keep checking X", "every morning", "when the deploy finishes", "remind me", a watch loop, a cron-shaped chore.

**Do:** reach for the scheduling primitives — `/loop` for in-session intervals, `ScheduleWakeup` / `send_later` for a one-shot resume, `CronCreate` / scheduled triggers for recurring cloud runs. Pick the cadence yourself from the task (poll a CI run every few minutes; a daily digest at a fixed hour).

**Smell:** manually re-running the same check turn after turn when the task is "watch until done". That's a loop — schedule it.

## The human-facing surface — surface, don't auto-run

Two capabilities are the user's to invoke, not yours. Mention them in one line at the right moment, then move on:

- **`/usage`** — when a session got expensive (a big workflow, many agents), point them at it so they can see what drove the cost.
- **`/rewind`** — if context was lost to a `/clear` or a bad compaction, tell them it can recover a prior point.

## When you may NOT stay in Gear 1

You may not grind work inline if **any** of these is true:

- The request names ≥2 independent concerns → **Gear 2**.
- The work repeats over many units (migrate/refactor/audit *all* / *every* / *each*, a list of 20+) → **Gear 3**.
- A step will run for many minutes and nothing depends on it immediately → **Gear 4**.
- The task is "keep checking" / recurring / time-triggered → **Gear 5**.

Staying inline through any of those is the same mistake as a workflow for a typo — wrong gear.

## When Gear 1 is correct (don't over-shift)

- One file, one known edit. Read it, change it, done.
- A factual question answerable from one search.
- A task the user explicitly scoped small ("just fix the typo").
- Anything where spawning agents would cost more context than the work itself.

Upshifting has a cost (tokens, latency, cognitive overhead in the transcript). The gear must be **justified by the shape**, never reached for to look thorough.

## When to use this skill

- **Proactively** — the `hooks/upshift_router.py` UserPromptSubmit hook scans each prompt for shape signals and injects a soft, non-binding gear hint ("this looks Gear 3 — consider a Workflow"). It never blocks and never mandates; it's a nudge, because a router that cries wolf gets ignored. Install with `bash hooks/install_hook.sh`.
- **Manually** — invoke `/upshift` (or a trigger phrase) when you want an explicit gear decision before a big task.
- **As a checklist** — at the start of any non-trivial request, run the shape question once before writing code.

## When NOT to use

- Trivial single-tool tasks — Gear 1 needs no skill.
- When the user has already named the capability ("run a workflow for X") — just do it; the routing decision is made.
- Pure conversation or opinion, where there is no "work shape" to classify.

## Relationship to Claude Code's native features

`upshift` does **not** reimplement the engine — it's the *driver*, not the gearbox:

- **`ultracode`** already lets Claude decide when a single task warrants a Workflow. `upshift` leans on it for Gear 3 and extends the same "decide by shape, don't make the user ask" principle to the gears `ultracode` doesn't cover — background (Gear 4) and scheduling (Gear 5).
- The **Workflow tool**, **`run_in_background`**, **`/loop`**, and **Cron/ScheduleWakeup** are the primitives. `upshift` is the policy layer that picks among them.

## Interaction with other skills

- **`did-it-actually`** verifies the *output* matches the request. `upshift` picks the *execution mode* that produces it. Compose: upshift to the right gear, then did-it-actually to confirm the result.
- **`resourceful`** governs *how hard you look* before answering (the resource ladder). `upshift` governs *how you execute* once you know the work. Resourceful is about input depth; upshift is about execution shape.
- A keyword→skill **router** (the common pattern) picks which *skill* to load. `upshift` is orthogonal: it picks which *execution capability* to run. They stack.

## Anti-noise (the lesson baked in)

A proactive router is only useful if its signal is trusted. So:

- The hook emits **soft hints only** — never a `block`, never "MANDATORY". A wrong nudge you can ignore costs nothing; a wrong hard-block trains you to ignore the whole system.
- Hints fire on **strong shape signals**, not on any keyword. "Audit the whole codebase" fires Gear 3; "audit this function" does not.
- Meta / config / self-referential prompts are **suppressed** — talking *about* upshift is not a job to upshift.
- The skill biases toward the **lowest** gear that fits. Over-shifting (a workflow for a one-liner) is treated as a failure mode, equal to under-shifting.

## Reference index

- `references/gear-map.md` — the full shape→gear table with concrete signals and the primitive to call per gear.
- `references/shape-signals.md` — the regexes/phrases the hook keys on, per gear, EN + PT.
- `references/examples.md` — worked examples: one job per gear, plus two deliberate down-shifts.
- `scripts/doctor.sh` — verifies install + hook wiring.
- `hooks/upshift_router.py` — UserPromptSubmit hook that injects the soft gear hint.
- `hooks/install_hook.sh` — wires the hook into `~/.claude/settings.json`.
