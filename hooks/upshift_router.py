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
# Bare nouns (cron / poll / monitor / daily / recurring) are common CODE words, so
# every term is anchored to a scheduling INTENT — never matched on its own.
GEAR5_RX = re.compile(
    r"\b(every (morning|day|night|hour|week|\d+\s*(min|m|h|hours?|minutes?))|"
    r"todos os dias|todas as (manh[ãa]s|noites)|de \d+ em \d+\s*(min|m|h|hora)|"
    r"cada \d+\s*(min|m|h|hora)|keep (checking|watching|polling|monitoring|an eye)|"
    r"continua a (verificar|checar|monitorizar)|"
    r"poll(ing)? (the|every|until|for|it)|monitor(ing)? (the|until|for changes|every|it)|"
    r"watch (the |this )?(pr|deploy|build|run|ci|job|pipeline|status)|"
    r"when (the |it |this )?(deploy|build|ci|run|job|pr|pipeline)?\s*"
    r"(finishes|is done|completes|passes|is green|goes green|merges|lands)|"
    r"quando (o |a )?(deploy|build|ci|corrida|job|pr) (acabar|terminar|passar|ficar verde)|"
    r"remind me (to|about|when|in|tomorrow|at|every)|lembra[- ]me (de|que|quando|amanh)|"
    r"recurring (task|job|check|run|reminder)|recorrente|periodic(ally|amente)?|"
    r"on a (schedule|timer|cron)|(set ?up|schedule|create|run) (a )?cron|cron ?job|"
    r"agenda(r)? (para|todos|isto para|um)|(daily|nightly|weekly|hourly) "
    r"(digest|report|run|check|job|summary|at)|di[áa]ri[oa] (relat[óo]rio|resumo|check))\b",
    re.IGNORECASE,
)

# ── Gear 4 — long-running, independent (background). Duration/size is the signal;
# scrape/crawl are anchored to an object so the bare verbs don't over-fire.
GEAR4_RX = re.compile(
    r"\b(in the background|em segundo plano|background (this|it|the)|run .{0,20}async|"
    r"run (the )?[\w ]{0,25}?(test suite|tests? suite|suite|build|benchmark)|"
    r"corre (toda |a )?[\w ]{0,20}?(suite|bateria) de testes|full test run|"
    r"(deep|thorough) research|investiga[çc][ãa]o (profunda|aprofundada)|"
    r"scrap(e|ing) (all|every|the|a |\d|every )|crawl (the|all|every|\d|a )|"
    r"takes? \d+\s*(min|mins|minutes?|h|hours?|hrs?)|\d+\s*(min|minutes?|hours?) to run|"
    r"long[- ]?(running|build|run|job)|slow (build|test|suite)|"
    r"demora[r]? (muito|minutos|imenso|horas)|"
    r"while (i|we|you) (do|work|continue|carry)|enquanto (eu |fa[çc]o |trabalho))\b",
    re.IGNORECASE,
)

# ── Gear 3 — large, repetitive, parallelisable (Workflow / ultracode).
_G3_NOUN = (r"ficheiros?|files?|m[óo]dulos?|modules?|componentes?|components?|"
            r"endpoints?|rotas?|routes?|testes?|tests?|p[áa]ginas?|pages?|"
            r"handlers?|languages?|locales?|l[íi]nguas?|translations?|tradu[çc][õo]es|"
            r"customers?|clientes?|users?|utilizadores|registos?|registros?|records?|"
            r"rows?|entradas?|entries|casos?|cases?|items?|itens")
GEAR3_RX = re.compile(
    r"\b(workflow|ultracode|orquestra[çc][ãa]o|orchestrat\w*|"
    r"(todos|todas) os? .{0,24}(" + _G3_NOUN + r")|"
    r"(every|each) (file|module|component|endpoint|route|test|page|handler|language|one)\b|"
    r"(go through|for) (each|every) \w+|across the (whole |entire )?(codebase|repo(sitory)?|project)|"
    r"(migra(r)?|migrate) (todos|tudo|all|the (whole|entire))|"
    r"refactor (all|every|the (whole|entire))|refactoriza(r)? tudo|"
    r"audita(r)? (tudo|todo o|a totalidade|todos)|"
    r"comprehensive (audit|review|sweep|refactor)|exhaustiv\w*|exaustiv\w*|"
    r"em massa|in bulk|bulk\b|faz tudo|trata de tudo|de forma aut[óo]noma|"
    r"(dezenas|centenas|d[úu]zias|a dozen|dozens?|twelve|twenty|thirty|forty|fifty|"
    r"sixty|seventy|eighty|ninety|hundreds?) (de |of )?\w*|the same way|da mesma (forma|maneira)|"
    r"all \d+ (of |de )?|\d{2,}\s+(of (these|them|those)|" + _G3_NOUN + r")|"
    r"\d+\s+(" + _G3_NOUN + r"))\b",
    re.IGNORECASE,
)

# ── Gear 2 — multiple independent concerns. Two work verbs joined by and/e/then,
# but only fires when the verbs are DISTINCT concerns (capture both → checked in
# classify()), so "debug and fix" (one concern) doesn't trip it.
_G2_VERB = (r"review|rev[êe]|test|testa|document|documenta|refactor|refactoriza|"
            r"explore|explora|design|desenha|audit|audita|debug|fix|corrige|"
            r"benchmark|profile|validate|valida|write|escreve|add|adiciona|"
            r"implement|implementa|migrate|migra|optimi[sz]e|optimiza")
GEAR2_RX = re.compile(
    r"\b(" + _G2_VERB + r")\b.{0,40}\b(and|e|then|depois|tamb[ée]m|plus|\+)\b.{0,40}"
    r"\b(" + _G2_VERB + r")\b",
    re.IGNORECASE,
)
# Verbs that mean the same concern — a pair from the same group is NOT two concerns.
_G2_SYNONYMS = [
    {"debug", "fix", "corrige", "corrigir"},
    {"refactor", "refactoriza", "optimi[sz]e", "optimiza", "simplify"},
    {"document", "documenta", "write", "escreve"},
    {"test", "testa", "validate", "valida"},
    {"review", "revê", "reve", "audit", "audita"},
]


def _two_distinct_concerns(v1: str, v2: str) -> bool:
    """True only when the two Gear-2 verbs are different concerns (not synonyms like
    debug/fix), so single-concern phrasings don't trigger a fan-out nudge."""
    a, b = v1.lower(), v2.lower()
    if a == b:
        return False
    for grp in _G2_SYNONYMS:
        if any(re.fullmatch(s, a) for s in grp) and any(re.fullmatch(s, b) for s in grp):
            return False
    return True


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
    g2 = GEAR2_RX.search(prompt)
    if g2 and _two_distinct_concerns(g2.group(1), g2.group(3)):
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
