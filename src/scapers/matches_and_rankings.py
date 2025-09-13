import requests
import bs4


class MatchesRankingsScaper:
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
