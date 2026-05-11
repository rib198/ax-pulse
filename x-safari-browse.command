#!/usr/bin/env bash
# Run the Safari-driven X collector.
# Double-click in Finder to launch. Or run from terminal:
#   ./x-safari-browse.command --max 5            # quick test on 5 handles
#   ./x-safari-browse.command --pipeline         # collect + run agents
#   ./x-safari-browse.command --only sama,karpathy
set -e
cd "$(dirname "$0")"
exec /usr/bin/env python3 tools/x_safari_browse.py "$@"
