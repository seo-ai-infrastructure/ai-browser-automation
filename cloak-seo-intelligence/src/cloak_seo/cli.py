"""Command-line interface for the Letta multi-agent backend.

Usage:
    python -m cloak_seo.cli bootstrap
    python -m cloak_seo.cli list
    python -m cloak_seo.cli chat <agent> "<message>"

(Use the ``run.sh`` wrapper to get the virtualenv + PYTHONPATH for free.)
"""

from __future__ import annotations

import argparse
import sys

from cloak_seo.agents.definitions import resolve_name
from cloak_seo.client import LettaGateway
from cloak_seo.logging_config import get_logger
from cloak_seo.orchestration import bootstrap

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


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="cloak_seo", description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("bootstrap", help="Create/sync shared memory, tools, agents.")
    sub.add_parser("list", help="List managed agents.")

    chat = sub.add_parser("chat", help="Send a message to an agent.")
    chat.add_argument("agent", help="Agent name or alias (e.g. supervisor).")
    chat.add_argument("message", help="Message text to send.")

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    handlers = {
        "bootstrap": _cmd_bootstrap,
        "list": _cmd_list,
        "chat": _cmd_chat,
    }
    try:
        return handlers[args.command](args)
    except Exception as exc:  # noqa: BLE001 - surface a clean message to the CLI
        logger.error("Command %r failed: %s", args.command, exc, exc_info=True)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
