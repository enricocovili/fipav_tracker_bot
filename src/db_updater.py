import db.crud
import sqlalchemy.exc
from telethon.sync import TelegramClient
import scrapers.matches_rankings as rankings
import scrapers.match_details as match_details
import standing_manager
import logging
import os


class DbUpdater:
    def __init__(self, bot: TelegramClient) -> None:
        self.match_scraper = rankings.MatchesRankingsScraper()
        self.details_scraper = match_details.InfoMatchScraper()
        self.bot = bot

        self.db_logger = logging.getLogger("db_updater")

        # Set up logging: DEBUG and up to file, INFO and up to console
        log_formatter = logging.Formatter(
            "%(asctime)s %(levelname)s %(message)s", "%Y-%m-%d %H:%M:%S"
        )

        os.makedirs("logs", exist_ok=True)
        file_handler = logging.FileHandler("logs/updater.log")
        file_handler.setLevel(logging.INFO)
        file_handler.setFormatter(log_formatter)

        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        console_handler.setFormatter(log_formatter)

        self.db_logger.setLevel(logging.DEBUG)
        self.db_logger.addHandler(file_handler)
        self.db_logger.addHandler(console_handler)

        self.db_logger.propagate = False  # prevents duplication to main log

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
                self.db_logger.warning(
                    "Division by zero occurred while computing standings; skipping standings for %s",
                    championship.id,
                )
            if data["name"] not in existing_names:
                _team = db.crud.create_team(data.get("name"))
                _standing = db.crud.create_standing(_team.id, championship.id)
                db.crud.update_standing(_standing.id, **data)
                self.db_logger.debug(
                    f"adding {data.get('name', 'None')} to db")
                self.notify = True
            else:
                # check if any data changed
                standing = db.crud.get_standings_in_championship(
                    championship_id=championship.id
                )
                for s in standing:
                    if s.team.name != data["name"]:
                        continue
                    for k, v in data.items():
                        try:
                            db_val = getattr(s, k)
                        except AttributeError:
                            continue
                        if str(db_val) != str(v):
                            db.crud.update_standing(s.id, **data)
                            self.db_logger.debug(
                                f"updating {data.get('name', 'None')} in db")
                            self.notify = True
                            break

        for match in self.match_scraper.get_matches(championship.url):
            try:
                if match.get("result") == "":
                    continue  # skip not played matches
                # flip day - year position to match db yyyy-mm-dd
                match["match_date"] = "/".join(
                    reversed(match["match_date"].split("/")))
                match_timestamp = f"{match.get('match_date')} {match.get('time'):00}"

                # retrieve matches info
                home_team_id = db.crud.get_team_by_name(
                    match.get("home_team"))[0].id
                away_team_id = db.crud.get_team_by_name(
                    match.get("away_team"))[0].id

                _match = db.crud.create_match(
                    championship_id=championship.id,
                    match_date=match_timestamp,
                    home_team_id=home_team_id,
                    away_team_id=away_team_id,
                    weekday=match.get("week_day"),
                    result=match.get("result"),
                )

                details = self.details_scraper.get_details(
                    match.get("info_link"))

                db.crud.update_match(
                    _match.id,
                    **{
                        "city": details.get("Citta"),
                        "address": details.get("Indirizzo"),
                        "maps_url": details.get("maps_url"),
                    },
                )

            except sqlalchemy.exc.IntegrityError:
                self.db_logger.debug("skipping match as already present in db")
                continue

            self.db_logger.debug("created match")

    async def perform_scan(self) -> None:
        """
        Perform a scan based on the selection provided by the database
        """
        self.db_logger.info("Running FIPAV website scan")
        for championship in db.crud.get_all_championships():
            self._populate_teams_matches(championship)
            if self.notify:
                self.db_logger.info(
                    f"Updates found for championship {championship.name} - {championship.group_name}, notifying users")
                standings = standing_manager.StandingManager(
                    championship)
                filename = standings.create_table(image=True)
                await self.notify_users(championship.id, filename)
                self.notify = False
            else:
                self.db_logger.info(
                    f"No updates for championship {championship.name} - {championship.group_name}")

    async def notify_users(self, championship_id, table_filename: str) -> None:
        """Notify users about database changes"""
        users = db.crud.get_users()
        for user in users:
            if user.tracked_championship != championship_id:
                continue
            try:
                championship = db.crud.get_championship_by_id(championship_id)
                await self.bot.send_file(
                    user.id,
                    table_filename,
                    caption=f"Aggiornamento!\nPartite: {championship.url}",
                )
                self.db_logger.info(
                    f"Notified user {user.username} about updates")
            except Exception as e:
                self.db_logger.error(
                    f"Failed to notify user {user.username}: {e}")


if __name__ == "__main__":
    scanner = DbUpdater()
    scanner.perform_scan()
