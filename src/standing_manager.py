from db.models import Standing, Championship
import db.crud
import pandas as pd


class StandingManager():
    def __init__(self, championship: Championship, is_avulsa: bool = False):
        self.championship = championship
        self.is_avulsa = is_avulsa
        self.standings: list[Standing] = self.get_standings()

    def get_standings(self) -> list[Standing]:
        if not self.is_avulsa:
            standings = db.crud.get_standings_in_championship(
                championship_id=self.championship.id)  # only specific standings
        else:
            total_championships = db.crud.get_championships_by_name(
                self.championship.name)
            standings = []
            for championship in total_championships:
                for standing in db.crud.get_standings_in_championship(championship_id=championship.id):
                    standings.append(standing)
        return standings

    def create_table(self, image: bool = False) -> str:
        data = {
            "#": [],
            "Nome": [],
            "# Girone": [],
            "Punti": [],
            " G ": [],
            " V ": [],
            " P ": [],
            "P/G": [],
            "QS": [],
            "QP": [],
        }
        for standing in self.standings:
            data["#"].append(standing.rank)
            data["Nome"].append(standing.team.name)
            data["# Girone"].append(standing.rank)
            data["Punti"].append(standing.points)
            data[" G "].append(standing.matches_won + standing.matches_lost)
            data[" V "].append(standing.matches_won)
            data[" P "].append(standing.matches_lost)
            data["P/G"].append(round(standing.points /
                               (standing.matches_won + standing.matches_lost), 3))
            data["QS"].append(round(standing.sets_won / standing.sets_lost, 3))
            data["QP"].append(round(standing.points_scored /
                              standing.points_conceded, 3))

        if not self.is_avulsa:    # bigger font
            scale_factor = 3.5
            data.pop("# Girone")
            data.pop("P/G")
        else:
            scale_factor = 1.75     # smaller font
            data.pop(" G ")
            data.pop(" V ")
            data.pop(" P ")

        df = pd.DataFrame(data)
        if image:
            import matplotlib.pyplot as plt

            fig, ax = plt.subplots(
                figsize=(10, 10), dpi=200
            )  # Increase the figure size and resolution.
            ax.axis("tight")
            ax.axis("off")
            table = ax.table(
                cellText=df.values, colLabels=df.columns, cellLoc="center", loc="center"
            )

            # Set first row text color to red and first column text weight to bold
            for (i, j), cell in table.get_celld().items():
                if i == 0:
                    cell.set_text_props(color="red")
                    cell.set_text_props(weight="bold")
                if j == 0:
                    cell.set_text_props(weight="bold")
                # Set alternating row colors
                cell.set_facecolor("white" if i % 2 == 0 else "lightgray")

            # set ARTIGLIO row to a light yellow background
            for i, row in df.iterrows():
                if "artiglio" in row["Nome"].lower():
                    for j in range(len(df.columns)):
                        table[(i + 1, j)].set_facecolor("lightyellow")

            # Adjust column widths to fit content
            table.auto_set_column_width(col=list(range(len(df.columns))))
            table.scale(1, scale_factor)  # Add some padding to the table

            if not self.is_avulsa:
                filename = f"tables_imgs/{self.championship.id}_{self.championship.group_name}.png"
            else:
                filename = f"tables_imgs/{self.championship.name}.png"

            plt.savefig(
                filename,
                bbox_inches="tight",
                pad_inches=0.1,
            )

            return filename
        else:
            return df.to_string()
