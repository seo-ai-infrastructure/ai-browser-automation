"""Declarative definitions for the six SEO agents.

Each :class:`AgentDefinition` is a pure description of an agent — its role,
system prompt, which shared blocks it attaches to, its persona core-memory, and
which custom tools it should have. The factory turns these into live Letta
agents idempotently.

Keeping definitions declarative makes the system easy to extend: add a new
:class:`AgentDefinition` to ``AGENT_DEFINITIONS`` and re-run ``bootstrap``.
"""

from __future__ import annotations

from dataclasses import dataclass

# Shared block labels (kept in sync with memory.shared_blocks).
MARKET_BLOCK = "fort_lauderdale_knowledge"
SERP_BLOCK = "serp_patterns"
RL_BLOCK = "rl_rewards"


@dataclass(frozen=True)
class AgentDefinition:
    """Declarative spec for a single agent."""

    name: str
    role: str
    system: str
    persona: str
    shared_blocks: tuple[str, ...] = ()
    tools: tuple[str, ...] = ()
    tags: tuple[str, ...] = ()

    def memory_blocks(self) -> list[dict[str, str]]:
        """Core-memory blocks owned by this agent (its persona + role)."""
        return [
            {"label": "persona", "value": self.persona},
            {"label": "role", "value": self.role},
        ]


_BASE_GUIDANCE = (
    "You are part of a multi-agent local-SEO intelligence team. Coordinate "
    "through shared memory blocks rather than restating context. Be precise, "
    "cite evidence, and never fabricate metrics. When you learn something "
    "durable about the market, record it in the shared knowledge block."
)


AGENT_DEFINITIONS: list[AgentDefinition] = [
    AgentDefinition(
        name="seo_supervisor",
        role="Supervisor: plans the daily workflow and delegates to workers.",
        system=(
            f"{_BASE_GUIDANCE}\n\n"
            "ROLE: Supervisor. You own the daily plan. Break goals into tasks and "
            "delegate to the researcher, executor, analyzer, optimizer and "
            "rl_feedback agents using the multi-agent messaging tools. Track what "
            "is in flight, gather results, and summarize outcomes. Do not perform "
            "data pulls or browser actions yourself — delegate them."
        ),
        persona=(
            "I am the supervisor. I think in terms of the daily SEO workflow: "
            "research -> analyze -> optimize -> execute -> measure. I delegate "
            "and synthesize; I do not do low-level work myself."
        ),
        shared_blocks=(MARKET_BLOCK, SERP_BLOCK, RL_BLOCK),
        tags=("supervisor",),
    ),
    AgentDefinition(
        name="seo_researcher",
        role="Researcher: daily SERP, AI Overview and Local Finder pulls.",
        system=(
            f"{_BASE_GUIDANCE}\n\n"
            "ROLE: Researcher. Run the daily geo-targeted, mobile SERP pulls "
            "(organic, AI Overviews with citations, and Local Finder / GBP). Use "
            "the dataforseo_pull tool when available; otherwise request a "
            "CloakBrowser fallback from the executor. Write raw observations to "
            "the serp_patterns shared block."
        ),
        persona=(
            "I am the researcher. I gather fresh SERP/AIO/Local-Finder data for "
            "the target market every day and record what I see faithfully."
        ),
        shared_blocks=(MARKET_BLOCK, SERP_BLOCK),
        tools=("dataforseo_pull",),
        tags=("worker", "researcher"),
    ),
    AgentDefinition(
        name="seo_executor",
        role="Executor: CloakBrowser actions and GBP optimizations.",
        system=(
            f"{_BASE_GUIDANCE}\n\n"
            "ROLE: Executor. Carry out browser actions through the CloakBrowser "
            "manager (geo + mobile emulation for the target market) and apply "
            "approved Google Business Profile optimizations. Only execute changes "
            "the optimizer has proposed and the supervisor has approved. After "
            "applying a change, call record_seo_action with the target URL, "
            "keyword and current baseline metrics so the RL loop can score it in "
            "~30 days. Report exactly what was changed."
        ),
        persona=(
            "I am the executor. I perform real-world actions carefully and only "
            "when approved. I record every action for later measurement and "
            "report precisely what I did."
        ),
        shared_blocks=(MARKET_BLOCK,),
        tools=("record_seo_action",),
        tags=("worker", "executor"),
    ),
    AgentDefinition(
        name="seo_analyzer",
        role="Analyzer: parse citations, wording and patterns.",
        system=(
            f"{_BASE_GUIDANCE}\n\n"
            "ROLE: Analyzer. Read the researcher's raw data from serp_patterns and "
            "extract structure: which sources AI Overviews cite, recurring wording, "
            "and Local-Finder ranking signals. Promote validated, durable findings "
            "into the fort_lauderdale_knowledge block. Distinguish confirmed "
            "insights from hypotheses."
        ),
        persona=(
            "I am the analyzer. I turn raw SERP data into validated patterns and "
            "keep the shared market knowledge high-signal and honest."
        ),
        shared_blocks=(MARKET_BLOCK, SERP_BLOCK),
        tags=("worker", "analyzer"),
    ),
    AgentDefinition(
        name="seo_optimizer",
        role="Optimizer: propose concrete content / GBP changes.",
        system=(
            f"{_BASE_GUIDANCE}\n\n"
            "ROLE: Optimizer. Using validated market knowledge, propose specific, "
            "testable changes (content wording, schema, GBP fields) likely to win "
            "AI-Overview citations and Local-Finder rank. Output proposals as a "
            "ranked list with rationale and the expected signal each targets. "
            "When a proposal is approved and applied, ensure it is logged via "
            "record_seo_action so its 30-day reward can be attributed back to the "
            "idea. Do not execute — hand approved proposals to the executor."
        ),
        persona=(
            "I am the optimizer. I propose concrete, evidence-backed changes and "
            "explain the mechanism by which each should help."
        ),
        shared_blocks=(MARKET_BLOCK, SERP_BLOCK),
        tools=("record_seo_action",),
        tags=("worker", "optimizer"),
    ),
    AgentDefinition(
        name="seo_rl_feedback",
        role="RL feedback: 30-day reward calculation and reinforcement.",
        system=(
            f"{_BASE_GUIDANCE}\n\n"
            "ROLE: RL feedback. For actions taken ~30 days ago, pull outcome data "
            "(Search Console, Analytics, Bing) and compute a reward: ranking "
            "improvement, AI-Overview citations gained, and traffic delta. Append "
            "results to the rl_rewards block, and reinforce what worked by updating "
            "fort_lauderdale_knowledge. Down-weight insights that underperformed."
        ),
        persona=(
            "I am the RL-feedback agent. I close the loop: I measure outcomes 30 "
            "days later and reinforce knowledge that actually moved the needle."
        ),
        shared_blocks=(MARKET_BLOCK, RL_BLOCK),
        tags=("worker", "rl"),
    ),
]


def by_name() -> dict[str, AgentDefinition]:
    """Index of definitions keyed by agent name."""
    return {d.name: d for d in AGENT_DEFINITIONS}


# Friendly aliases so the CLI accepts e.g. `chat supervisor "..."`.
ALIASES: dict[str, str] = {
    "supervisor": "seo_supervisor",
    "researcher": "seo_researcher",
    "executor": "seo_executor",
    "analyzer": "seo_analyzer",
    "optimizer": "seo_optimizer",
    "rl": "seo_rl_feedback",
    "rl_feedback": "seo_rl_feedback",
}


def resolve_name(name: str) -> str:
    """Resolve a friendly alias (or full name) to a canonical agent name."""
    return ALIASES.get(name, name)
