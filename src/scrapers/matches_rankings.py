import requests
import bs4

"""
    Ranking page row

    0. Rank
    1. Name
    2. Points
    3. Played
    4. Won
    5. Lost
    6. 3-0
    7. 3-1
    8. 3-2
    9. 2-3
    10. 1-3
    11. 0-3
    12. SW (Sets won)
    13. SS (Sets lost)
    14. QS (Set ratio)
    15. PS (Points won)
    16. PR (Points lost)
    17. QR (Points ratio)
    18. Pen (Penalties)
"""


class Team:
    def __init__(
        self,
        round,
        rank,
        name,
        points,
        played,
        won,
        lost,
        three_zero,
        three_one,
        three_two,
        two_three,
        one_three,
        zero_three,
        sets_won,
        sets_lost,
        set_ratio,
        points_won,
        points_lost,
        points_ratio,
        penalties,
    ):
        self.round = round
        self.local_rank = int(rank)
        self.name = name
        self.points = int(points)
        self.played = int(played)
        self.won = int(won)
        self.lost = int(lost)
        self.three_zero = int(three_zero)
        self.three_one = int(three_one)
        self.three_two = int(three_two)
        self.two_three = int(two_three)
        self.one_three = int(one_three)
        self.zero_three = int(zero_three)
        self.sets_won = int(sets_won)
        self.sets_lost = int(sets_lost)
        self.set_ratio = float(set_ratio.replace(",", "."))
        self.points_won = int(points_won)
        self.points_lost = int(points_lost)
        self.points_ratio = float(points_ratio.replace(",", "."))
        self.penalties = int(penalties)
        self.global_rank = -1

    def to_json(self):
        # get all attributes except global_rank and return json formatted string
        return {k: v for k, v in self.__dict__.items() if k != "global_rank"}

    def __str__(self):
        return f"{self.name}"

    def __repr__(self):
        return f"{self.round} | {self.name}"

    def __eq__(self, value):
        # compare json representation of the object
        if isinstance(value, Team):
            return self.to_json() == value.to_json()
        if isinstance(value, dict):
            # exclude global_rank from value
            temp_val = {k: v for k, v in value.items() if k != "global_rank"}
            return self.to_json() == temp_val


class Match:
    """
    Match row
    0. Skip
    1. Code
    2. Date
    3. Week day
    4. Time
    5. Home team
    6. Away team
    7. Skip
    8. Result
    9. Skip
    """

    def __init__(
        self,
        __a,
        code,
        date,
        week_day,
        time,
        home_team,
        away_team,
        __b,
        result,
        __c,
    ):
        self.code = code
        self.date = date
        self.week_day = week_day
        self.time = time
        self.home_team = home_team
        self.away_team = away_team
        self.result = result

    def __str__(self):
        return f"{self.home_team} vs {self.away_team}"

    def __repr__(self):
        return f"{self.home_team} vs {self.away_team}"


class MatchesRankingsScraper:
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
            matches.append(Match(*[col.getText() for col in cols]))
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
            team = Team(
                "A" if "girone=A" in url else "B", *[col.getText() for col in cols]
            )
            teams.append(team)
        return teams
