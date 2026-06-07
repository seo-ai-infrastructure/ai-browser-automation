# cloak-seo-intelligence

A **local-first, multi-agent SEO intelligence platform** for local/geo SEO work
(built around the Fort Lauderdale, FL market as the reference deployment).

This repository implements the system incrementally. **This first milestone is the
Letta multi-agent backend** — the stateful agent runtime, shared memory, and
orchestration that everything else (data pipeline, RL feedback loop, Next.js
dashboard) plugs into.

> Status of major sections
>
> | Section | Status |
> |---|---|
> | 1. Multi-agent system (Letta) | ✅ This milestone |
> | 2. Data pipeline (DataForSEO + CloakBrowser) | 🟡 Tool interfaces stubbed, wiring next |
> | 3. RL / 30-day feedback loop | 🟡 Agent + reward scaffold present, logic next |
> | 4. Shared memory & messaging | ✅ This milestone |
> | 5. Next.js dashboard | ⬜ Not started |
> | 6. QLoRA fine-tuning (MLX) | ⬜ Not started |

## Architecture (this milestone)

A **supervisor + worker** topology on the [Letta](https://docs.letta.com)
runtime. All agents are stateful and persist in Postgres (Letta's DB). Agents
coordinate through **shared memory blocks** — the most important being the
*Fort Lauderdale market knowledge* block, which every agent can read and the
analyzer/optimizer/RL agents can write.

```
                         ┌─────────────────────────┐
                         │   Supervisor Agent       │
                         │  (plans & delegates)     │
                         └───────────┬─────────────┘
            send_message_to_agent_*  │  (Letta multi-agent messaging)
        ┌──────────────┬─────────────┼──────────────┬──────────────┐
        ▼              ▼             ▼              ▼              ▼
  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────────┐
  │Researcher│  │ Executor │  │ Analyzer │  │Optimizer │  │ RL Feedback  │
  │SERP/AIO/ │  │CloakBrwsr│  │citations │  │ proposes │  │ 30-day reward│
  │LocalFind │  │ GBP ops  │  │ patterns │  │ changes  │  │ calculation  │
  └──────────┘  └──────────┘  └──────────┘  └──────────┘  └──────────────┘
        └──────────────┴──────── shared memory blocks ──────┴──────────────┘
                 (fort_lauderdale_knowledge, serp_patterns, rl_rewards)
```

## Tech stack

- **Runtime:** [Letta](https://docs.letta.com) server (Docker), Postgres-backed.
- **Models:** Local-first via an OpenAI-compatible endpoint (vMLX / MLX on Mac
  Mini). Configured on the Letta server through `OPENAI_API_BASE`; agents
  reference a model *handle* (`CLOAK_LLM_MODEL`).
- **Hot data / queues:** Redis.
- **History / agent state:** Postgres.
- **SDK:** `letta-client` (Python).

## Quick start

```bash
cd cloak-seo-intelligence

# 1. Configure environment
cp .env.example .env
$EDITOR .env            # set LETTA_BASE_URL, model handle, API keys, etc.

# 2. Start infra (Letta server + Postgres + Redis)
docker compose up -d

# 3. Install the Python package + deps
./setup.sh

# 4. Create / sync all agents and shared memory (idempotent)
./run.sh bootstrap

# 5. Send a task to the supervisor
./run.sh chat supervisor "Plan today's Fort Lauderdale SERP pull"
```

The Letta **Agent Development Environment (ADE)** is available at
http://localhost:8283 for inspecting agents, memory, and message history.

## Project layout

```
cloak-seo-intelligence/
├── docker-compose.yml         # Letta server + Postgres + Redis
├── .env.example               # All configuration (copy to .env)
├── requirements.txt
├── setup.sh / run.sh
├── config/
│   └── settings.py            # Typed, env-driven settings (pydantic-settings)
└── src/cloak_seo/
    ├── client.py              # Letta client factory (single integration point)
    ├── logging_config.py
    ├── memory/
    │   └── shared_blocks.py   # Shared memory block definitions + sync
    ├── agents/
    │   ├── definitions.py     # Persona / role / tool config for the 6 agents
    │   └── factory.py         # Idempotent create-or-update of agents
    ├── tools/
    │   └── dataforseo.py      # Custom Letta tool (interface; pipeline next)
    └── orchestration/
        └── bootstrap.py       # Wire blocks + agents together; messaging helpers
```

## Design notes

- **Single integration point.** Every call into the Letta SDK goes through
  `src/cloak_seo/client.py`. If the SDK API drifts, fix it in one place.
- **Idempotent bootstrap.** Re-running `bootstrap` updates existing agents and
  blocks in place (matched by name/label) instead of creating duplicates.
- **Local-first.** No cloud calls are required; point `OPENAI_API_BASE` at your
  vMLX endpoint and set `CLOAK_LLM_MODEL` to the served model handle.

See the repository root `LETTA_SETUP.md` for the full step-by-step setup guide.
```
