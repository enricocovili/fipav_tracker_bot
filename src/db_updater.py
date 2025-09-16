import db.crud
import sqlalchemy.exc
import scrapers.matches_rankings as rankings
import scrapers.match_details as match_details
import logging

# Set up logging: DEBUG and up to file, INFO and up to console
log_formatter = logging.Formatter(
    "%(asctime)s %(levelname)s %(message)s", "%Y-%m-%d %H:%M:%S"
)

file_handler = logging.FileHandler("logs/updater.log")
file_handler.setLevel(logging.INFO)
file_handler.setFormatter(log_formatter)

console_handler = logging.StreamHandler()
console_handler.setLevel(logging.DEBUG)
console_handler.setFormatter(log_formatter)

logging.basicConfig(level=logging.DEBUG, handlers=[
                    file_handler, console_handler])


class DbUpdater:
    def __init__(self) -> None:
        self.match_scraper = rankings.MatchesRankingsScraper()
        self.details_scraper = match_details.InfoMatchScraper()

    def _populate_teams_matches(self, championship) -> None:
        for team in self.match_scraper.load_teams(championship.url):
            team['championship_id'] = str(championship.id)
            try:
                _team = db.crud.create_team(
                    team.get('name'), team.get('championship_id'))
            except sqlalchemy.exc.IntegrityError as e:
                logging.debug(
                    f"Not adding team {team.get('name')} as it\'s already existent")
                continue
            logging.debug(f"adding {team.get('name', 'None')} to db")
            db.crud.update_team_stats(_team.id, **team)

        for match in self.match_scraper.get_matches(championship.url):
            try:
                # flip day - year position to match db yyyy-mm-dd
                match['match_date'] = "/".join(
                    reversed(match['match_date'].split("/")))
                match_timestamp = f"{match.get('match_date')} {match.get('time'):00}"

                # retrieve matches info
                home_team_id = db.crud.get_team_by_name(
                    match.get('home_team'))[0].id
                away_team_id = db.crud.get_team_by_name(
                    match.get('away_team'))[0].id

                _match = db.crud.create_match(
                    championship_id=championship.id,
                    match_date=match_timestamp,
                    home_team_id=home_team_id,
                    away_team_id=away_team_id,
                    weekday=match.get('week_day'),
                    result=match.get('result')
                )

                details = self.details_scraper.get_details(
                    match.get("info_link"))

                db.crud.update_match(_match.id, **{'city': details.get(
                    'Citta'), 'address': details.get('Indirizzo'), 'maps_url': details.get('maps_url')})

            except sqlalchemy.exc.IntegrityError as e:
                logging.debug("skipping match as already present in db")
                continue

            logging.debug("created match")

    def perform_scan(self) -> None:
        """
        Perform a scan based on the selection provided by the database
        """
        for championship in db.crud.get_championships():
            self._populate_teams_matches(championship)

    def notify_subscribed_users(self) -> None:
        """
        Notify users if a new result is dropped
        """
        pass


if __name__ == "__main__":
    scanner = DbUpdater()
    scanner.perform_scan()
    scanner.notify_subscribed_users()
