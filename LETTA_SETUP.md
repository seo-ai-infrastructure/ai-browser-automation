# Letta Multi-Agent Setup (`cloak-seo-intelligence`)

This guide walks through standing up the **Letta multi-agent backend** that lives
in [`cloak-seo-intelligence/`](./cloak-seo-intelligence). It is the foundation of
the broader local-first multi-agent SEO platform; the data pipeline, RL feedback
loop, and Next.js dashboard plug into it in later milestones.

> What you get from this milestone: a supervisor + 5 worker agents
> (researcher, executor, analyzer, optimizer, RL-feedback) running on a
> self-hosted Letta server, coordinating through shared memory blocks, with an
> idempotent bootstrap and a small CLI.

## Prerequisites

- Docker + Docker Compose
- Python 3.11+
- A local OpenAI-compatible model endpoint (vMLX / MLX on a Mac Mini), or an
  `ANTHROPIC_API_KEY` if you prefer a hosted model while developing.

## 1. Configure

```bash
cd cloak-seo-intelligence
cp .env.example .env
```

Edit `.env`. The values that matter most for the first run:

| Variable | What it does |
|---|---|
| `LETTA_BASE_URL` | `http://localhost:8283` for the local docker server. |
| `OPENAI_API_BASE` | Your vMLX/MLX endpoint (the **Letta server** calls this). |
| `OPENAI_API_KEY` | Any non-empty value for a local server (e.g. `local`). |
| `CLOAK_LLM_MODEL` | Model **handle** the agents use, e.g. `openai/local-mlx`. |
| `CLOAK_MARKET_*` | Target geo (defaults to Fort Lauderdale, FL). |

The model handle (`CLOAK_LLM_MODEL`) must match a model your Letta server can
serve. For a local vMLX server serving a model named `local-mlx`, use
`openai/local-mlx`.

## 2. Start infrastructure

```bash
docker compose up -d        # letta + postgres + redis
docker compose ps           # all three should be healthy
```

- Letta ADE / API: http://localhost:8283
- Postgres: agent state + message history
- Redis: hot daily data + queues (used by the data pipeline next milestone)

## 3. Install the Python package

```bash
./setup.sh                  # creates .venv and installs requirements
source .venv/bin/activate
```

## 4. Bootstrap agents + shared memory

```bash
./run.sh bootstrap
```

This is **idempotent** — it creates the three shared memory blocks, registers
custom tools, and creates the six agents, attaching shared blocks to each.
Re-running it syncs config in place without duplicating anything or wiping
accumulated agent knowledge.

Expected output (ids will differ):

```
Shared blocks : fort_lauderdale_knowledge, serp_patterns, rl_rewards
Tools         : dataforseo_pull
Agents        :
  - seo_supervisor  (agent-...)
  - seo_researcher  (agent-...)
  ...
```

## 5. Talk to the agents

```bash
./run.sh list
./run.sh chat supervisor "Plan today's Fort Lauderdale SERP pull and delegate it"
```

Accepted agent aliases: `supervisor`, `researcher`, `executor`, `analyzer`,
`optimizer`, `rl`.

You can also inspect everything visually in the **ADE** at
http://localhost:8283 — agents, their memory blocks, tools, and full message
history.

## How it fits together

| Concept | Where |
|---|---|
| All SDK calls | `src/cloak_seo/client.py` (single integration point) |
| Shared memory blocks | `src/cloak_seo/memory/shared_blocks.py` |
| Agent roles / prompts | `src/cloak_seo/agents/definitions.py` |
| Idempotent agent sync | `src/cloak_seo/agents/factory.py` |
| Custom tools | `src/cloak_seo/tools/` |
| Wiring | `src/cloak_seo/orchestration/bootstrap.py` |

### Extending the system

Add a new agent by appending an `AgentDefinition` to `AGENT_DEFINITIONS` and
re-running `./run.sh bootstrap`. Add a new tool by writing a self-contained
function and registering it in `src/cloak_seo/tools/registry.py`.

## What's next (not in this milestone)

- **Data pipeline:** live DataForSEO pulls + Playwright/CloakBrowser fallback,
  persisting raw + parsed data to Redis/Postgres.
- **RL feedback loop:** 30-day GSC/Analytics/Bing reward calculation.
- **Next.js dashboard:** live agent status, team chat, Kanban board, SERP
  history viewer.
- **QLoRA fine-tuning (MLX):** SEO domain adaptation of the local model.
