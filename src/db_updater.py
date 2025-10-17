import db.crud
import sqlalchemy.exc
import scrapers.matches_rankings as rankings
import scrapers.match_details as match_details
import logging
import main
import random
import os

# Set up logging: DEBUG and up to file, INFO and up to console
log_formatter = logging.Formatter(
    "%(asctime)s %(levelname)s %(message)s", "%Y-%m-%d %H:%M:%S"
)

os.makedirs("logs", exist_ok=True)
file_handler = logging.FileHandler("logs/updater.log")
file_handler.setLevel(logging.INFO)
file_handler.setFormatter(log_formatter)

console_handler = logging.StreamHandler()
console_handler.setLevel(logging.DEBUG)
console_handler.setFormatter(log_formatter)

logging.basicConfig(level=logging.DEBUG, handlers=[file_handler, console_handler])


class DbUpdater:
    def __init__(self) -> None:
        self.match_scraper = rankings.MatchesRankingsScraper()
        self.details_scraper = match_details.InfoMatchScraper()
        self.notify: bool = False

    def _populate_teams_matches(self, championship) -> None:
        for data in self.match_scraper.load_teams(championship.url):
            data["championship_id"] = str(championship.id)
            existing_names = []
            try:
                standings = db.crud.get_standings_in_championship(
                    championship_id=championship.id
                )
                for standing in standings:
                    try:
                        name = standing.team.name
                    except Exception:
                        name = None
                    if name:
                        existing_names.append(name)
            except ZeroDivisionError:
                logging.warning(
                    "Division by zero occurred while computing standings; skipping standings for %s",
                    championship.id,
                )
            if data["name"] in existing_names:
                logging.debug(f"Skipping {data['name']} as already present in db")
                continue

            _team = db.crud.create_team(data.get("name"))
            _standing = db.crud.create_standing(_team.id, championship.id)
            logging.debug(f"adding {data.get('name', 'None')} to db")

            if _standing != db.crud.update_standing(_standing.id, **data):
                self.notify = True

        for match in self.match_scraper.get_matches(championship.url):
            try:
                # flip day - year position to match db yyyy-mm-dd
                match["match_date"] = "/".join(reversed(match["match_date"].split("/")))
                match_timestamp = f"{match.get('match_date')} {match.get('time'):00}"

                # retrieve matches info
                home_team_id = db.crud.get_team_by_name(match.get("home_team"))[0].id
                away_team_id = db.crud.get_team_by_name(match.get("away_team"))[0].id

                _match = db.crud.create_match(
                    championship_id=championship.id,
                    match_date=match_timestamp,
                    home_team_id=home_team_id,
                    away_team_id=away_team_id,
                    weekday=match.get("week_day"),
                    result=match.get("result"),
                )

                details = self.details_scraper.get_details(match.get("info_link"))

                db.crud.update_match(
                    _match.id,
                    **{
                        "city": details.get("Citta"),
                        "address": details.get("Indirizzo"),
                        "maps_url": details.get("maps_url"),
                    },
                )

            except sqlalchemy.exc.IntegrityError:
                logging.debug("skipping match as already present in db")
                continue

            logging.debug("created match")

    def perform_scan(self) -> None:
        """
        Perform a scan based on the selection provided by the database
        """
        for championship in db.crud.get_all_championships():
            self._populate_teams_matches(championship)
            if self.notify:
                self.notify_subscribed_users(championship.id)

    async def notify_subscribed_users(self, championship_id: int) -> None:
        await main.bot.start(bot_token=main.bot_token)

        for user in db.crud.get_users():
            if user.tracked_championship == championship_id:
                int_random = random.randint(0, 100)
                if int_random == 69 or int_random == 88:
                    text = "FU-FU-FU-FURRY, C'È UN AGGIORNAMENTO!"
                else:
                    text = "🍔 AGGIORNAMENTO JUST DROPPED 🍔"
                main.bot.send_message(user.id, text)


if __name__ == "__main__":
    scanner = DbUpdater()
    scanner.perform_scan()
