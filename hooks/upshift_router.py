#!/usr/bin/env python3
"""upshift — UserPromptSubmit hook.

Reads the prompt from stdin JSON, classifies the *shape* of the work, and prints
a SOFT gear hint that Claude Code injects as context. Never blocks, never says
"MANDATORY" — a router that cries wolf gets ignored. Silent on no match and on
meta/config prompts, to keep the signal trustworthy and the context lean.

Gears (see SKILL.md):
  1 Inline            — small/single (no hint; the default)
  2 Parallel agents   — multi independent concerns
  3 Workflow/ultracode— large, repetitive, parallelisable
  4 Background        — long-running, independent
  5 Scheduled/cron    — polling / recurring / time-triggered

Exit 0 always. Designed to be portable: no machine- or user-specific paths.
"""
from __future__ import annotations

import json
import re
import sys

# ── Meta / self-referential / config prompts: talking ABOUT upshift or the
# harness is not a job to upshift. Suppress all hints here.
META_RX = re.compile(
    r"\b(upshift|claude code|skill[_ ]?router|settings\.json|output style|"
    r"hooks?\.(py|sh|json)|\.claude/|claude\.md|the gear|which gear|"
    r"this skill|the hook|your (output|setup|prompt|behaviou?r))\b",
    re.IGNORECASE,
)

# ── Gear 5 — scheduled / recurring / polling.
GEAR5_RX = re.compile(
    r"\b(every (morning|day|night|hour|week|\d+\s*(min|m|h|hours?|minutes?))|"
    r"todos os dias|todas as (manh[ãa]s|noites)|de \d+ em \d+\s*(min|m|h|hora)|"
    r"cada \d+\s*(min|m|h|hora)|keep (checking|watching|polling|an eye)|"
    r"continua a (verificar|checar|monitorizar)|poll(ing)?\b|monitor(ize|ise)?\b|"
    r"when the (deploy|build|ci|run|job) (finishes|is done|completes)|"
    r"quando (o |a )?(deploy|build|ci|corrida|job) (acabar|terminar)|"
    r"remind me|lembra[- ]me|recurring|recorrente|peri[óo]dic|on a schedule|"
    r"agenda(r)? (para|todos|isto para)|cron\b|daily|di[áa]ri[oa])\b",
    re.IGNORECASE,
)

# ── Gear 4 — long-running, independent (background).
GEAR4_RX = re.compile(
    r"\b(in the background|em segundo plano|background (this|it|the)|"
    r"run (the )?[\w ]{0,25}?(test suite|tests? suite|suite|build|benchmark)|"
    r"corre (toda |a )?[\w ]{0,20}?(suite|bateria) de testes|full test run|"
    r"(deep|thorough) research|investiga[çc][ãa]o (profunda|aprofundada)|"
    r"scrape|crawl|long[- ]running|demora[r]? (muito|minutos|imenso)|"
    r"while (i|we|you) (do|work|continue)|enquanto (eu |fa[çc]o |trabalho))\b",
    re.IGNORECASE,
)

# ── Gear 3 — large, repetitive, parallelisable (Workflow / ultracode).
GEAR3_RX = re.compile(
    r"\b(workflow|ultracode|orquestra[çc][ãa]o|orchestrat\w*|"
    r"(todos|todas) os? .{0,24}(ficheiros|files|m[óo]dulos|modules|componentes|"
    r"components|endpoints|rotas|routes|testes|tests|p[áa]ginas|pages)|"
    r"every (file|module|component|endpoint|route|test|page)\b|"
    r"across the (whole |entire )?(codebase|repo(sitory)?|project)|"
    r"(migra(r)?|migrate) (todos|tudo|all|the (whole|entire))|"
    r"refactor (all|every|the (whole|entire))|refactoriza(r)? tudo|"
    r"audita(r)? (tudo|todo o|a totalidade|todos)|"
    r"comprehensive (audit|review|sweep|refactor)|exhaustiv\w*|exaustiv\w*|"
    r"em massa|in bulk|bulk\b|"
    r"(dezenas|centenas|d[úu]zias) de|the same way|da mesma (forma|maneira)|"
    r"\b\d{2,}\s+(ficheiros|files|items|itens|casos|cases|m[óo]dulos|modules|"
    r"registos|registros|records|rows|entradas|entries))\b",
    re.IGNORECASE,
)

# ── Gear 2 — multiple independent concerns (light heuristic).
# Two distinct work verbs joined by "and / e" → likely multi-concern.
GEAR2_RX = re.compile(
    r"\b(review|rev[êe]|test|testa|document|documenta|refactor|refactoriza|"
    r"explore|explora|design|desenha|audit|audita|debug|fix|corrige|"
    r"benchmark|profile|validate|valida)\b"
    r".{0,40}\b(and|e|then|depois|tamb[ée]m|plus|\+)\b.{0,40}"
    r"\b(review|rev[êe]|test|testa|document|documenta|refactor|refactoriza|"
    r"explore|explora|design|desenha|audit|audita|debug|fix|corrige|"
    r"benchmark|profile|validate|valida|write|escreve|add|adiciona)\b",
    re.IGNORECASE,
)


def classify(prompt: str) -> list[tuple[int, str]]:
    """Return matched gears as (gear_number, hint_line), highest-value first."""
    hits: list[tuple[int, str]] = []
    if GEAR5_RX.search(prompt):
        hits.append((
            5,
            "Gear 5 (scheduled/recurring): this is a watch/poll/recurring task. "
            "Reach for `/loop` (in-session interval), `ScheduleWakeup`/`send_later` "
            "(one-shot resume), or `CronCreate`/scheduled triggers (recurring) — pick "
            "the cadence from the task. Don't re-run the same check by hand each turn.",
        ))
    if GEAR4_RX.search(prompt):
        hits.append((
            4,
            "Gear 4 (background): this job is long-running and independent. Spawn it "
            "with `run_in_background: true` (Agent or Bash) so the main thread keeps "
            "moving — you'll be notified on completion. Don't stall on a foreground spinner.",
        ))
    if GEAR3_RX.search(prompt):
        hits.append((
            3,
            "Gear 3 (workflow): this is large, repetitive, parallelisable work (many "
            "units / an exhaustive sweep). Prefer `ultracode` (Claude decides to run a "
            "Workflow) or the `Workflow` tool — scout the work-list inline first, then "
            "pipeline()/parallel() over it. Beats hand-spawning agents one by one. "
            "Say the cost shape in one line when you launch it.",
        ))
    if GEAR2_RX.search(prompt):
        hits.append((
            2,
            "Gear 2 (fan out): ≥2 independent concerns here. Spawn parallel sub-agents "
            "in ONE Agent block (multiple tool_use entries), one concern each, then "
            "aggregate. Don't serialize independent agents or do it all inline.",
        ))
    hits.sort(key=lambda h: -h[0])
    return hits


def main() -> int:
    try:
        payload = json.load(sys.stdin)
    except (json.JSONDecodeError, ValueError):
        return 0
    prompt = (payload.get("prompt") or "").strip()
    if not prompt or prompt.startswith("/"):
        return 0
    if META_RX.search(prompt):
        return 0
    hits = classify(prompt)
    if not hits:
        return 0
    # Emit the single highest-value gear as the primary nudge; if a second,
    # lower gear also fired, mention it in one trailing line. Soft, never binding.
    print("upshift — gear hint (soft; ignore if the shape doesn't fit):")
    print(f"  • {hits[0][1]}")
    if len(hits) > 1:
        g = hits[1][0]
        print(f"  • (also reads as Gear {g}; use judgement — pick ONE gear for the job.)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
