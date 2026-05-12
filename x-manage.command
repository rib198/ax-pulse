#!/usr/bin/env bash
# Manage the X collection — see what's tracked, prune, tune per-handle targets.
#
# Run from terminal (double-clicking in Finder works for the no-arg case only):
#   ./x-manage.command list-accounts
#   ./x-manage.command show @sama
#   ./x-manage.command list-tweets --from @sama --top 20
#   ./x-manage.command set-target @sama 200
#   ./x-manage.command delete-account @oldhandle
#   ./x-manage.command targets
#
# With no arguments, shows a quick summary.
set -e
cd "$(dirname "$0")"
if [ $# -eq 0 ]; then
    echo "=== الرادار — X collection management ==="
    echo
    /usr/bin/env python3 tools/x_manage.py list-accounts | head -30
    echo
    echo "More commands:"
    echo "  ./x-manage.command list-accounts                  # full list"
    echo "  ./x-manage.command show @handle                   # one account"
    echo "  ./x-manage.command list-tweets --top 30           # top tweets"
    echo "  ./x-manage.command set-target @handle 200         # custom target"
    echo "  ./x-manage.command delete-account @handle         # remove"
    echo "  ./x-manage.command targets                        # show overrides"
    echo "  ./x-manage.command --help                         # full help"
    exit 0
fi
exec /usr/bin/env python3 tools/x_manage.py "$@"
