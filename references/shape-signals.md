# Shape signals — what the hook keys on

The `upshift_router.py` hook fires **soft** hints on these signals. EN + PT. These
are deliberately conservative: strong shape words only, so the signal stays trusted.
If a gear under- or over-fires for you, edit the matching regex in the hook.

## Gear 5 — scheduled / recurring
`every morning/day/hour`, `de X em X minutos`, `cada N min`, `keep checking/watching/polling`,
`continua a verificar/monitorizar`, `when the deploy/build/CI finishes`, `quando o deploy acabar`,
`remind me`, `lembra-me`, `recurring`, `recorrente`, `daily`, `diário`, `cron`, `on a schedule`.

## Gear 4 — background
`in the background`, `em segundo plano`, `run the full test suite`, `corre toda a suite de testes`,
`deep/thorough research`, `investigação profunda`, `scrape`, `crawl`, `long-running`,
`demora muito/minutos`, `while I work/continue`, `enquanto eu trabalho`.

## Gear 3 — workflow / ultracode
`workflow`, `ultracode`, `orchestrate`, `orquestração`, `all the files/modules/components/…`,
`todos os ficheiros/módulos/…`, `every file/module/…`, `across the (whole) codebase/repo`,
`migrate all`, `migra tudo`, `refactor all/every/the whole`, `audit everything`, `audita tudo`,
`comprehensive audit/review/sweep`, `exhaustive`, `exaustivo`, `in bulk`, `em massa`,
`dozens/hundreds of`, `dezenas/centenas de`, `\d{2,} files/items/cases/…`.

## Gear 2 — fan out
Two distinct work verbs joined by `and / e / then / depois / também / plus / +`, e.g.
`review the code and write tests`, `explora e desenha a arquitectura`, `audit and refactor`.

## Suppressed (no hint)
- Anything matching the meta set: `upshift`, `claude code`, `settings.json`, `claude.md`,
  `.claude/`, `the gear / which gear`, `this skill / the hook`, `your output/setup/behaviour`.
- Prompts that start with `/` (slash commands).
- Empty or whitespace-only prompts.

## Why soft, why conservative
A proactive router earns its keep only if its hints are right often enough to trust.
A wrong **soft** hint costs one ignorable line. A wrong **hard block** trains the model
to tune the whole system out — which is exactly how over-eager fan-out mandates die.
So: soft hints, strong signals, lowest-gear bias.
