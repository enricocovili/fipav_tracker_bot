#!/usr/bin/env bash
# Adds a new championship and runs the same team/match scraping logic used
# by the scheduled DbUpdater scan, to populate teams/matches/standings
# automatically.
#
# Copies the latest src/ files into the running app container (the image
# bakes src/ in at build time, it isn't a live volume mount) and runs the
# script there so it uses the app's environment and network access.
#
# Usage:
#   ./add_championship.sh --name "PRIMA DIVISIONE MASCHILE" \
#       --url "https://www.fipav.mo.it/fipav/new/calendari.jsp?cat=1DM&girone=A&descr=...&classifica=1" \
#       --start-year 2025 --end-year 2026 --group-name A
set -euo pipefail

cd "$(dirname "${BASH_SOURCE[0]}")"

if [ "$#" -eq 0 ]; then
    echo "Usage: $0 --name NAME --url URL --start-year YYYY --end-year YYYY [--group-name G]" >&2
    exit 1
fi

CONTAINER="fipav_tracker_telegram_bot"

docker cp src/add_championship.py "$CONTAINER":/app/src/add_championship.py
docker cp src/db/crud.py "$CONTAINER":/app/src/db/crud.py
docker exec "$CONTAINER" python src/add_championship.py "$@"
