from telethon import events, Button
import logging
import requests, bs4
import pandas as pd
import json
import handlers.BaseHandler as BaseHandler


URL_TEST_TODO_REMOVE = "https://www.fipav.mo.it/fipav/new/calendari.jsp?cat=1DM&girone=B&descr=PRIMA+DIVISIONE+MASCHILE+&squadra=MARKING+PRODUCTS+ARTIGLIO"

"""
    Ranking row
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


class Artiglio(BaseHandler.BaseHandler):
    def create_tables(self, teams_data, image: bool = False, local: bool = True):
        data = {
            "#": [
                team.local_rank if local else team.global_rank for team in teams_data
            ],
            "Nome": [team.name for team in teams_data],
            "# Girone": [team.local_rank for team in teams_data],
            "Punti": [team.points for team in teams_data],
            " G ": [team.played for team in teams_data],
            " V ": [team.won for team in teams_data],
            " P ": [team.lost for team in teams_data],
            "P/G": [round(team.points / team.played, 3) for team in teams_data],
            "QS": [team.set_ratio for team in teams_data],
            "QP": [team.points_ratio for team in teams_data],
        }
        if local:
            scale_factor = 3.5
            data.pop("# Girone")
            data.pop("P/G")
        else:
            scale_factor = 1.75
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

            plt.savefig(
                f"{'girone' if local else 'avulsa'}.png",
                bbox_inches="tight",
                pad_inches=0.1,
            )
        else:
            return df.to_string()

    def load_teams(self, url: str):
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

    def get_full_ranks(self, local: bool = True):
        teams = load_teams(URL_TEST_TODO_REMOVE)
        teams = teams + load_teams(
            URL_TEST_TODO_REMOVE.split("girone=B")[0] + "girone=A"
        )
        if local:
            # sort the teams based on (order is important): points, number of wins, QS, QP
            # get only the teams in the same round as artiglio
            artiglio_round = [
                team for team in teams if "artiglio" in team.name.lower()
            ][0].round
            teams = [team for team in teams if team.round == artiglio_round]
            teams.sort(
                key=lambda x: (x.points, x.won, x.set_ratio, x.points_ratio),
                reverse=True,
            )
        else:
            # sort the teams based on (order is important): local rank, points/played, QS, QP
            teams.sort(
                key=lambda x: (
                    x.local_rank,
                    -x.points / x.played,
                    -x.set_ratio,
                    -x.points_ratio,
                )
            )
        for i, team in enumerate(teams):
            team.global_rank = i + 1
        return teams

    def get_matches(self):
        res = requests.get(URL_TEST_TODO_REMOVE)
        res.raise_for_status()
        soup = bs4.BeautifulSoup(res.text, "html.parser")
        matches = []
        for match in soup.select("table")[1].select("tr"):
            if not "dispari" in match.get("class", []) and not "pari" in match.get(
                "class", []
            ):
                continue
            cols = match.select("td")
            if len(cols) == 0:
                continue
            matches.append(Match(*[col.getText() for col in cols]))
            matches[-1].result = matches[-1].result[0:5]
        return matches

    async def ranking(self, event: events.newmessage.NewMessage.Event, local: bool):
        logging.info(f"received: ranking: {'girone' if local else 'avulsa'}")
        loading_msg = await event.client.send_message(event.chat, "Loading...")
        teams = get_full_ranks(local)
        # open teams.json and check if the teams are the same as the ones in the ranking
        json_team_data = [team.to_json() for team in teams]
        reuse_table = False
        try:
            with open("teams.json", "r") as f:
                old_teams = json.load(f)

                # check if the new teams are a subset of the old ones
                test = [team in old_teams for team in json_team_data]
                if all(test):
                    logging.info("reusing old table")
                    reuse_table = True
        except FileNotFoundError:
            pass
        if not reuse_table:
            logging.info("creating new table")
            with open("teams.json", "w") as f:
                json.dump(json_team_data, f, indent=4)
            # hardcode the image for now
            create_tables(teams, image=True, local=local)
        await loading_msg.delete()
        await event.client.send_file(
            event.chat,
            f"{'girone' if local else 'avulsa'}.png",
            caption=f"Classifica {'Girone' if local else 'Avulsa'}",
        )

    def artiglio_stats(self, event: events.newmessage.NewMessage.Event):
        teams = get_full_ranks()
        matches = get_matches()

        info_artiglio = [team for team in teams if "artiglio" in team.name.lower()][0]

        last_match = Match("", "", "", "", "", "", "", "", "", "")
        next_match = Match("", "", "", "", "", "", "", "", "", "")

        for ix, match in enumerate(matches[:-1]):
            if matches[ix + 1].result == "":
                last_match = match
                next_match = matches[ix + 1]
                break

        # Mobile friendly output
        output = f"""
            Informazioni su **Artiglio**:
            ⬤ **Rank Girone {info_artiglio.round}**: {info_artiglio.local_rank}
            ⬤ **Rank Generale**: {info_artiglio.global_rank}
            ⬤ **Punti**: {info_artiglio.points}
            ⬤ **% Vittorie**: {round(info_artiglio.won / info_artiglio.played * 100, 2)}% ({info_artiglio.won}/{info_artiglio.played})
            ⬤ **Prossima partita**:
                {next_match.week_day + " " + next_match.date + " " + next_match.time}
                vs {next_match.away_team if "artiglio" in next_match.home_team.lower() else next_match.home_team} 
                ({"casa" if "artiglio" in next_match.home_team.lower() else "ospiti"})
            ⬤ **Ultima partita**: 
                {last_match.week_day + " " + last_match.date + " " + last_match.time}
                vs {last_match.away_team if "artiglio" in last_match.home_team.lower() else last_match.home_team}
                ({last_match.result}) ({"casa" if "artiglio" in last_match.home_team.lower() else "ospiti"})
        """
        # All this shit is needed because i use multiline strings. I know there are better methods, i simply don't care
        # strip trailing whitespaces for every line if start with "⬤"
        output = "\n".join(
            [
                line.strip() if line.strip().startswith("⬤") else line
                for line in output.split("\n")
            ]
        )
        # also cap every line starting with whitespaces to a max of 4 trailing whitespaces
        output = "\n".join(
            [
                4 * " " + line.strip() if line.startswith(" ") else line
                for line in output.split("\n")
            ]
        )
        return output

    @events.register(events.CallbackQuery)
    async def callback(event):
        if not event.data.startswith(b"artiglio__"):
            return
        output = ""
        html_parse = False
        if event.data == b"artiglio__local_rank":
            output = await self.ranking(event, local=True)
            html_parse = True
        elif event.data == b"artiglio__global_rank":
            output = await self.ranking(event, local=False)
            html_parse = True
        elif event.data == b"artiglio__stats":
            output = self.artiglio_stats(event)
        elif event.data == b"artiglio__close_menu":
            return await event.delete()
        if output:
            return await event.client.send_message(
                event.chat, output[:4000], parse_mode="html" if html_parse else "md"
            )

    @events.register(events.NewMessage(pattern="/artiglio"))
    async def handle(event: events.newmessage.NewMessage):
        bot = event.client
        await bot.send_message(
            event.chat,
            message="Select one of the options below",
            buttons=[
                [
                    Button.inline(
                        f"🥇 Classifica Girone", data=b"artiglio__local_rank"
                    ),
                    Button.inline(
                        "🥇 Classifica Avulsa", data=b"artiglio__global_rank"
                    ),
                ],
                [Button.inline("📊 Info & next match", data=b"artiglio__stats")],
                [Button.url("🔗 Pagina web FIPAV 🔗", url=URL_TEST_TODO_REMOVE)],
                [Button.inline("❌ Close Menu ❌", data=b"artiglio__close_menu")],
            ],
        )
