# upshift

[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Claude Code skill](https://img.shields.io/badge/Claude%20Code-skill-8A63D2.svg)](https://code.claude.com/docs/en/skills)

**A Claude Code skill that makes Claude match the execution gear to the shape of the work — and reach for it without being told the feature's name.**

Claude Code has a deep capability surface: parallel sub-agents, the Workflow tool, background jobs, scheduled/cron runs. But most of it sits idle, because using it requires the *user* to name it first — "use a workflow", "run it in the background", "fan out agents", "schedule it". People rarely do. So a 200-file migration gets ground through one inline loop, a 20-minute test run freezes the thread, and "keep checking the deploy" becomes you re-typing the same command every turn.

`upshift` removes the naming requirement. It teaches Claude to read the *shape* of each request and shift into the right gear on its own.

> It's the **driver**, not the gearbox. The Workflow tool, `run_in_background`, `/loop` and Cron are the engine — `upshift` is the policy layer that picks the gear.

---

## The five gears

| Gear | Shape | Reaches for |
|---|---|---|
| **1 — Inline** | one file, one edit, one fact | `Read`/`Edit`/`Bash` directly |
| **2 — Fan out** | ≥2 independent concerns | parallel sub-agents, one `Agent` block |
| **3 — Workflow** | many units, same treatment (migrate/audit/refactor *all*) | `ultracode` or the `Workflow` tool |
| **4 — Background** | one long-running, independent job | `run_in_background: true` |
| **5 — Scheduled** | polling / recurring / time-triggered | `/loop`, `ScheduleWakeup`, Cron |

Shift **up** as the work gets larger / more parallel / longer-running. Shift **down** so you never spawn a fleet for a typo. **One gear per job.**

---

## Before / after

**Before** — user has to name the feature, or Claude grinds it inline:
> **You:** migrate every page in `app/` to the new router
> **Claude:** *(opens page 1, edits, opens page 2, edits, … 40 times, in one thread, until it runs low on context)*

**After** — Claude reads the shape and shifts to Gear 3:
> **You:** migrate every page in `app/` to the new router
> **Claude:** This is a sweep across ~40 pages — running it as a workflow, one agent per page with a verify pass on each. *(scouts the file list, pipelines over it, reports)*

You never said "workflow". That's the point.

---

## Install

Inspect first, then run:

```bash
git clone https://github.com/pedroreisper/upshift
less upshift/install.sh        # read it
bash upshift/install.sh        # installs to ~/.claude/skills/upshift
```

Or the one-liner:

```bash
curl -fsSL https://raw.githubusercontent.com/pedroreisper/upshift/main/install.sh | bash
```

Flags: `--project` (install into `./.claude/skills/`), `--hook` (also wire the proactive hint hook), `--uninstall`.

Then restart Claude Code (or `/reload`) and verify:

```bash
bash ~/.claude/skills/upshift/scripts/doctor.sh
```

---

## Two modes

**Manual** — invoke `/upshift` (or a trigger phrase like "be thorough", "do all of these", "faz tudo") to force an explicit gear decision before a big task.

**Proactive** — a `UserPromptSubmit` hook (`hooks/upshift_router.py`) scans each prompt for shape signals and injects a **soft** gear hint:

```
upshift — gear hint (soft; ignore if the shape doesn't fit):
  • Gear 3 (workflow): this is large, repetitive, parallelisable work …
```

Enable it:

```bash
bash ~/.claude/skills/upshift/hooks/install_hook.sh
```

The hook **never blocks and never says "MANDATORY"**. That's deliberate — see below.

---

## Why the hints are soft (the lesson baked in)

A proactive router is only useful if its signal is trusted. Over-eager fan-out mandates that fire on every keyword get tuned out — and once you're trained to ignore the nudge, it fails on the cases that mattered. So `upshift`:

- emits **soft hints only**, never a hard block;
- fires on **strong shape signals**, not any keyword ("audit the whole codebase" → Gear 3; "audit this function" → silent);
- **suppresses** meta/config/self-referential prompts (talking *about* upshift is not a job to upshift);
- biases toward the **lowest gear that fits** — over-shifting a one-liner into a workflow is treated as a failure, equal to under-shifting.

---

## Relationship to native features

Claude Code's `ultracode` already lets Claude decide when a single task warrants a Workflow. `upshift` leans on it for Gear 3 and extends the same *"decide by shape, don't make the user ask"* principle to the gears `ultracode` doesn't cover — background (Gear 4) and scheduling (Gear 5) — plus the multi-domain fan-out (Gear 2). It's the unifying policy layer over the whole surface.

## Composes with

- **[`did-it-actually`](https://github.com/pedroreisper/did-it-actually)** — upshift picks the *execution mode*; did-it-actually verifies the *output* matches the request. Shift, then verify.
- **[`resourceful`](https://github.com/pedroreisper/resourceful)** — resourceful governs *how hard you look* before answering; upshift governs *how you execute* once you know the work. Input depth vs execution shape.

## What's in the box

```
upshift/
├── SKILL.md                     # the gear map + decision rules (what Claude reads)
├── hooks/
│   ├── upshift_router.py        # UserPromptSubmit hook — soft gear hints
│   └── install_hook.sh          # wires it into ~/.claude/settings.json
├── references/
│   ├── gear-map.md              # full shape→gear→primitive table
│   ├── shape-signals.md         # the signals the hook keys on (EN + PT)
│   └── examples.md              # one worked job per gear + two down-shifts
├── scripts/doctor.sh            # verify install + hook wiring
├── tests/                       # fixture-based classification tests (run in CI)
└── install.sh
```

## When NOT to use

- Trivial single-tool tasks — Gear 1 needs no skill.
- When the user already named the capability ("run a workflow for X") — just do it.
- Pure conversation, where there's no work shape to classify.

## License

MIT © 2026 Pedro Reis Pereira
