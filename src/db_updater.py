import db.crud
import scrapers.matches_rankings as rankings
import scrapers.match_details as match_details


class DbUpdater:
    def __init__(self) -> None:
        pass

    def perform_scan(self) -> None:
        """
        Perform a scan based on the selection provided by the database
        """
        for championship in db.crud.get_championships():
            for team in rankings.MatchesRankingsScraper.load_teams(
                    championship.get("url", None)):
                a = db.crud.create_team(
                    team.name, championship.get("id", None))
                db.crud.update_team_stats(id, )
                pass
            pass
        pass

    def notify_subscribed_users(self) -> None:
        """
        Notify users if a new result is dropped
        """
        pass


if __name__ == "__main__":
    scanner = DbUpdater()
    scanner.perform_scan()
    scanner.notify_subscribed_users()
