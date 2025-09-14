import requests
import bs4
import db.models


class MatchesRankingsScraper:
    RANKING_ROW_FIELDS = {
        0: "rank",
        1: "name",
        2: "points",
        3: None,  # matches_played
        4: "matches_won",
        5: "matches_lost",
        6: "num_3_0",
        7: "num_3_1",
        8: "num_3_2",
        9: "num_2_3",
        10: "num_1_3",
        11: "num_0_3",
        12: "sets_won",
        13: "sets_lost",
        14: None,  # set ratio
        15: "points_won",
        16: "points_scored",
        17: "points_conceded",
        18: None,  # penalties
    }

    MATCH_ROW_FIELDS = {
        0: "info_link",
        1: None,  # match code
        2: "match_date",
        3: "week_day",
        4: "time",
        5: "home_team",
        6: "away_team",
        7: None,         # Skip
        8: "result",
        9: None          # Skip
    }

    @staticmethod
    def get_matches(url: str):
        res = requests.get(url)
        res.raise_for_status()
        soup = bs4.BeautifulSoup(res.text, "html.parser")
        matches = []
        for match in soup.select("table")[1].select("tr"):
            if "dispari" not in match.get("class", []) and not "pari" in match.get(
                "class", []
            ):
                continue
            cols = match.select("td")
            if len(cols) == 0:
                continue
            matches.append(db.models.Match(*[col.getText() for col in cols]))
            matches[-1].result = matches[-1].result[0:5]
        return matches

    @staticmethod
    def load_teams(url: str):
        teams = []
        res = requests.get(url)
        res.raise_for_status()
        soup = bs4.BeautifulSoup(res.text, "html.parser")
        table = soup.select("table")[0]
        rows = table.select("tr")
        for row in rows:
            cols = row.select("td")
            if len(cols) == 0:
                continue
            team = db.models.Team()
            for idx, col in enumerate(cols):
                field = MatchesRankingsScraper.RANKING_ROW_FIELDS.get(idx)
                if field:
                    setattr(team, field, col.getText())
            teams.append(team)
        return teams
