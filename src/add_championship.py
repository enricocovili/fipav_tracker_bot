"""
Add a new championship and verify that teams/matches/standings get
populated automatically from it, using the same scraping logic the
scheduled DbUpdater scan uses.

Usage (from inside the app container, where PYTHONPATH already
includes src/ because it's the script's own directory):
    python src/add_championship.py --name NAME --url URL \\
        --start-year YYYY --end-year YYYY [--group-name G]

Normally invoked via ./add_championship.sh from the repo root, which
passes its arguments through to this script.
"""
import argparse
import logging

from dotenv import load_dotenv

load_dotenv()

import db.crud as crud
from db_updater import DbUpdater

logging.basicConfig(level=logging.INFO)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--name", required=True, help="Championship name")
    parser.add_argument(
        "--url", required=True, help="FIPAV calendari.jsp URL to scrape"
    )
    parser.add_argument(
        "--start-year", type=int, required=True, help="Season start year"
    )
    parser.add_argument(
        "--end-year", type=int, required=True, help="Season end year"
    )
    parser.add_argument(
        "--group-name", default=None, help="Girone/group letter (optional)"
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()

    championship = crud.create_championship(
        name=args.name,
        url=args.url,
        start_year=args.start_year,
        end_year=args.end_year,
        group_name=args.group_name,
    )
    print(
        f"Created championship id={championship.id} "
        f"{championship.name} - {championship.group_name}"
    )

    # bot=None is fine: we only exercise the scraping/population steps,
    # not the Telegram notification path.
    updater = DbUpdater(bot=None)
    updater._populate_teams(championship)
    updater._populate_matches(championship)

    teams = crud.get_teams_by_championship(championship.id)
    matches = crud.get_matches_by_championship(championship.id)
    standings = crud.get_standings_in_championship(championship_id=championship.id)

    print(f"Teams populated:     {len(teams)}")
    print(f"Matches populated:   {len(matches)}")
    print(f"Standings populated: {len(standings)}")


if __name__ == "__main__":
    main()
