"""
Add a championship together with all of its groups (gironi) and verify that
teams/matches/standings get populated automatically, using the same scraping
logic the scheduled DbUpdater scan uses.

The URL can be the one of any group: the `girone` parameter is replaced and
every group from A on is probed until FIPAV has no standings for it.

Usage (from inside the app container, where PYTHONPATH already
includes src/ because it's the script's own directory):
    python src/add_championship.py --name NAME --url URL \\
        --start-year YYYY --end-year YYYY [--group-name G]

--group-name restricts the insertion to a single group.

Normally invoked via ./add_championship.sh from the repo root, which
passes its arguments through to this script.
"""
import argparse
import logging
import string
from urllib.parse import parse_qsl, urlencode, urlparse

from dotenv import load_dotenv

load_dotenv()

import db.crud as crud
from db_updater import DbUpdater
from scrapers.matches_rankings import MatchesRankingsScraper

logging.basicConfig(level=logging.INFO)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--name", required=True, help="Championship name")
    parser.add_argument(
        "--url", required=True, help="FIPAV calendari.jsp URL of any of its groups"
    )
    parser.add_argument(
        "--start-year", type=int, required=True, help="Season start year"
    )
    parser.add_argument(
        "--end-year", type=int, required=True, help="Season end year"
    )
    parser.add_argument(
        "--group-name",
        default=None,
        help="Only add this girone/group letter instead of all of them",
    )
    return parser.parse_args()


def group_url(url: str, group: str) -> str:
    parsed = urlparse(url)
    query = dict(parse_qsl(parsed.query, keep_blank_values=True))
    query["girone"] = group
    return parsed._replace(query=urlencode(query)).geturl()


def find_groups(url: str) -> list[tuple[str, str]]:
    """(group letter, url) for every consecutive group that exists on FIPAV."""
    scraper = MatchesRankingsScraper()
    groups = []
    for letter in string.ascii_uppercase:
        candidate = group_url(url, letter)
        if not scraper.group_exists(candidate):
            break
        groups.append((letter, candidate))
    return groups


def main() -> None:
    args = parse_args()

    if args.group_name:
        groups = [(args.group_name, group_url(args.url, args.group_name))]
    else:
        groups = find_groups(args.url)
        if not groups:
            raise SystemExit("No group with standings found for this URL")
        print(f"Groups found: {', '.join(g for g, _ in groups)}")

    # bot=None is fine: we only exercise the scraping/population steps,
    # not the Telegram notification path.
    updater = DbUpdater(bot=None)

    for group, url in groups:
        championship = crud.get_championship(
            args.name, group, args.start_year, args.end_year
        )
        if championship:
            print(f"Girone {group} already present (id={championship.id}), skipping")
            continue
        championship = crud.create_championship(
            name=args.name,
            url=url,
            start_year=args.start_year,
            end_year=args.end_year,
            group_name=group,
        )
        print(
            f"Created championship id={championship.id} "
            f"{championship.name} - {championship.group_name}"
        )

        updater._populate_teams(championship)
        updater._populate_matches(championship)

        teams = crud.get_teams_by_championship(championship.id)
        matches = crud.get_matches_by_championship(championship.id)
        standings = crud.get_standings_in_championship(
            championship_id=championship.id
        )

        print(f"  Teams populated:     {len(teams)}")
        print(f"  Matches populated:   {len(matches)}")
        print(f"  Standings populated: {len(standings)}")


if __name__ == "__main__":
    main()
