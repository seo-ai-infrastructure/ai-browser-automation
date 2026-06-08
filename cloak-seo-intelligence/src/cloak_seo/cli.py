"""Command-line interface for the Letta multi-agent backend.

Usage:
    python -m cloak_seo.cli bootstrap
    python -m cloak_seo.cli list
    python -m cloak_seo.cli chat <agent> "<message>"
    python -m cloak_seo.cli rl-record --url U --keyword K --description D [...]
    python -m cloak_seo.cli rl-evaluate [--no-reinforce]
    python -m cloak_seo.cli rl-export <out.jsonl> [--min-reward 0.0]

(Use the ``run.sh`` wrapper to get the virtualenv + PYTHONPATH for free.)
"""

from __future__ import annotations

import argparse
import sys

from cloak_seo.agents.definitions import resolve_name
from cloak_seo.client import LettaGateway
from cloak_seo.logging_config import get_logger
from cloak_seo.orchestration import bootstrap
from config import get_settings

logger = get_logger(__name__)


def _cmd_bootstrap(_: argparse.Namespace) -> int:
    result = bootstrap()
    print(result.summary())
    return 0


def _cmd_list(_: argparse.Namespace) -> int:
    gateway = LettaGateway.connect()
    agents = gateway.list_agents()
    if not agents:
        print("No agents found. Run `bootstrap` first.")
        return 0
    for agent in agents:
        tags = ", ".join(getattr(agent, "tags", []) or [])
        print(f"{agent.name:<18} {agent.id}  [{tags}]")
    return 0


def _cmd_chat(args: argparse.Namespace) -> int:
    gateway = LettaGateway.connect()
    name = resolve_name(args.agent)
    agent = gateway.find_agent(name)
    if agent is None:
        print(f"Agent {name!r} not found. Run `bootstrap` first.", file=sys.stderr)
        return 1

    print(f"→ {name}: {args.message}")
    response = gateway.send_message(agent.id, args.message)
    reply = gateway.extract_reply(response)
    print(f"← {name}: {reply or '(no assistant text in response)'}")
    return 0


def _cmd_rl_record(args: argparse.Namespace) -> int:
    from cloak_seo.rl.action_store import QUEUE_KEY, get_action_store
    from cloak_seo.rl.models import ActionMetrics, TrackedAction

    action = TrackedAction(
        target_url=args.url,
        keyword=args.keyword,
        description=args.description,
        agent=args.agent,
        baseline=ActionMetrics(
            avg_rank=None if args.baseline_rank < 0 else args.baseline_rank,
            clicks=args.baseline_clicks,
            impressions=args.baseline_impressions,
            aio_cited=args.baseline_aio,
            aio_citation_count=1 if args.baseline_aio else 0,
        ),
    )
    store = get_action_store()
    store.save(action)
    print(f"Recorded action {action.id} (due in {get_settings().rl_eval_window_days}d)")
    return 0


def _cmd_rl_evaluate(args: argparse.Namespace) -> int:
    from cloak_seo.rl import run_evaluation

    results = run_evaluation(reinforce=not args.no_reinforce)
    if not results:
        print("No matured actions had usable outcome data this run.")
        return 0
    print(f"Evaluated {len(results)} action(s):")
    for result in results:
        print(result.summary_line())
    return 0


def _cmd_rl_export(args: argparse.Namespace) -> int:
    from cloak_seo.rl import build_training_dataset

    count = build_training_dataset(args.output, min_reward=args.min_reward)
    print(f"Wrote {count} training example(s) to {args.output}")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="cloak_seo", description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("bootstrap", help="Create/sync shared memory, tools, agents.")
    sub.add_parser("list", help="List managed agents.")

    chat = sub.add_parser("chat", help="Send a message to an agent.")
    chat.add_argument("agent", help="Agent name or alias (e.g. supervisor).")
    chat.add_argument("message", help="Message text to send.")

    rec = sub.add_parser("rl-record", help="Manually record an action for the RL loop.")
    rec.add_argument("--url", required=True, help="Target page URL.")
    rec.add_argument("--keyword", required=True, help="Target keyword/query.")
    rec.add_argument("--description", required=True, help="What was changed.")
    rec.add_argument("--agent", default="manual", help="Recording agent name.")
    rec.add_argument("--baseline-rank", type=float, default=-1.0, help="Avg rank (-1=unknown).")
    rec.add_argument("--baseline-clicks", type=int, default=0)
    rec.add_argument("--baseline-impressions", type=int, default=0)
    rec.add_argument("--baseline-aio", action="store_true", help="Currently AIO-cited.")

    ev = sub.add_parser("rl-evaluate", help="Evaluate matured actions and write rewards.")
    ev.add_argument("--no-reinforce", action="store_true", help="Skip RL-agent reinforcement.")

    ex = sub.add_parser("rl-export", help="Export evaluated actions as JSONL (QLoRA).")
    ex.add_argument("output", help="Destination .jsonl path.")
    ex.add_argument("--min-reward", type=float, default=None, help="Filter by min reward.")

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    handlers = {
        "bootstrap": _cmd_bootstrap,
        "list": _cmd_list,
        "chat": _cmd_chat,
        "rl-record": _cmd_rl_record,
        "rl-evaluate": _cmd_rl_evaluate,
        "rl-export": _cmd_rl_export,
    }
    try:
        return handlers[args.command](args)
    except Exception as exc:  # noqa: BLE001 - surface a clean message to the CLI
        logger.error("Command %r failed: %s", args.command, exc, exc_info=True)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
