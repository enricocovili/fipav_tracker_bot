from db.models import Standing, Championship
import db.crud
import pandas as pd
import io


class StandingManager:
    def __init__(self, championship: Championship, is_avulsa: bool = False):
        self.championship = championship
        self.is_avulsa = is_avulsa
        self.standings: list[Standing] = self.get_standings()
        self.sort_standings()

    def get_standings(self) -> list[Standing]:
        if not self.is_avulsa:
            standings = db.crud.get_standings_in_championship(
                championship_id=self.championship.id
            )  # only specific standings
        else:
            total_championships = db.crud.get_championships_by_name(
                self.championship.name
            )
            standings = []
            for championship in total_championships:
                for standing in db.crud.get_standings_in_championship(
                    championship_id=championship.id
                ):
                    standings.append(standing)
        return standings

    def sort_standings(self) -> None:
        self.standings.sort(
            key=lambda s: (
                s.rank,
                -s.points,
                -(s.matches_won + s.matches_lost),
                -s.sets_won / (s.sets_lost if s.sets_lost > 0 else 1),
                -s.points_scored /
                (s.points_conceded if s.points_conceded > 0 else 1)
            )
        )

    def _dataframe(self) -> pd.DataFrame:
        data = {
            "#": [],
            "Nome": [],
            "# Girone": [],
            "Punti": [],
            " G ": [],
            " V ": [],
            " P ": [],
            "Punti %": [],
            "QS": [],
            "QP": [],
        }
        for index, standing in enumerate(self.standings):
            data["#"].append(index + 1)
            data["Nome"].append(standing.team.name)
            data["# Girone"].append(standing.rank)
            data["Punti"].append(standing.points)
            data[" G "].append(standing.matches_won + standing.matches_lost)
            data[" V "].append(standing.matches_won)
            data[" P "].append(standing.matches_lost)
            total_matches = standing.matches_won + standing.matches_lost
            data["Punti %"].append(
                round((standing.points / (total_matches*3))
                      * 100, 3) if total_matches > 0 else 0
            )
            data["QS"].append(
                round(standing.sets_won / standing.sets_lost, 3)
                if standing.sets_lost > 0
                else 0
            )
            data["QP"].append(
                round(standing.points_scored / standing.points_conceded, 3)
                if standing.points_conceded > 0
                else 0
            )

        if not self.is_avulsa:
            data.pop("# Girone")
            data.pop("Punti %")
        else:
            data.pop(" G ")
            data.pop(" V ")
            data.pop(" P ")

        return pd.DataFrame(data)

    def create_table(self) -> str:
        return self._dataframe().to_string()

    @property
    def title(self) -> str:
        if self.is_avulsa:
            return f"{self.championship.name}\nClassifica avulsa"
        group = self.championship.group_name
        return f"{self.championship.name}\nClassifica girone {group}" if group else (
            f"{self.championship.name}\nClassifica girone")

    def create_image(self, highlight_team_ids: set[int] = frozenset()) -> bytes:
        """Render the standings as a PNG sized after the number of teams.

        Rows of the teams in highlight_team_ids get a light yellow background.
        """
        import matplotlib.pyplot as plt

        df = self._dataframe()
        rows = len(df) + 1  # header included

        # column widths proportional to their longest text
        chars = [
            max(len(str(c)) for c in [col, *df[col]]) + 2 for col in df.columns
        ]
        fontsize = 14
        char_width = fontsize * 0.72 / 72  # inches, wide enough for uppercase
        row_height = 0.45  # inches
        fig = plt.figure(figsize=(sum(chars) * char_width, rows * row_height), dpi=200)
        ax = fig.add_axes([0, 0, 1, 1])
        ax.axis("off")
        table = ax.table(
            cellText=df.values,
            colLabels=df.columns,
            cellLoc="center",
            colWidths=[c / sum(chars) for c in chars],
            bbox=[0, 0, 1, 1],  # fill the whole figure
        )
        table.auto_set_font_size(False)
        table.set_fontsize(fontsize)
        ax.set_title(self.title, fontsize=fontsize + 4, weight="bold", pad=14)

        highlighted = {
            i for i, standing in enumerate(self.standings)
            if standing.team_id in highlight_team_ids
        }
        for (i, j), cell in table.get_celld().items():
            if i == 0:
                cell.set_text_props(color="red", weight="bold")
                cell.set_facecolor("white")
                continue
            if j == 0 or (i - 1) in highlighted:
                cell.set_text_props(weight="bold")
            if (i - 1) in highlighted:
                cell.set_facecolor("lightyellow")
            else:
                cell.set_facecolor("white" if i % 2 == 0 else "lightgray")

        buf = io.BytesIO()
        fig.savefig(buf, format="png", bbox_inches="tight", pad_inches=0.1)
        plt.close(fig)
        return buf.getvalue()

    @staticmethod
    def as_file(png: bytes) -> io.BytesIO:
        """Wrap PNG bytes so Telethon sends them as a photo."""
        file = io.BytesIO(png)
        file.name = "classifica.png"
        return file
