#!/usr/bin/env bash
# Convenience wrapper around the agent CLI.
#
#   ./run.sh bootstrap                  # create/sync all agents + shared memory
#   ./run.sh list                       # list managed agents
#   ./run.sh chat <agent> "<message>"   # send a message and print the reply
set -euo pipefail

cd "$(dirname "$0")"

if [[ -d ".venv" ]]; then
  # shellcheck disable=SC1091
  source .venv/bin/activate
fi

export PYTHONPATH="src:${PYTHONPATH:-}"
exec python -m cloak_seo.cli "$@"
