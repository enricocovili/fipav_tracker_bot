from telethon import events, Button
import logging
import pandas as pd
import json
import handlers.base_handler as base_handler
import scrapers.matches_rankings as scraper


URL_TEST_TODO_REMOVE = "https://www.fipav.mo.it/fipav/new/calendari.jsp?cat=1DM&girone=B&descr=PRIMA+DIVISIONE+MASCHILE+&squadra=MARKING+PRODUCTS+ARTIGLIO"


class Artiglio(base_handler.BaseHandler):
    def create_tables(teams_data, image: bool = False, local: bool = True):
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

    def get_full_ranks(local: bool = True):
        teams = scraper.MatchesRankingsScraper.load_teams(URL_TEST_TODO_REMOVE)
        teams = teams + scraper.MatchesRankingsScraper.load_teams(
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

    async def ranking(event: events.newmessage.NewMessage.Event, local: bool):
        logging.info(f"received: ranking: {'girone' if local else 'avulsa'}")
        loading_msg = await event.client.send_message(event.chat, "Loading...")
        teams = Artiglio.get_full_ranks(local)
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
            Artiglio.create_tables(teams, image=True, local=local)
        await loading_msg.delete()
        await event.client.send_file(
            event.chat,
            f"{'girone' if local else 'avulsa'}.png",
            caption=f"Classifica {'Girone' if local else 'Avulsa'}",
        )

    def artiglio_stats(event: events.newmessage.NewMessage.Event):
        teams = Artiglio.get_full_ranks()
        matches = scraper.MatchesRankingsScraper.get_matches(URL_TEST_TODO_REMOVE)

        info_artiglio = [team for team in teams if "artiglio" in team.name.lower()][0]

        last_match = scraper.Match("", "", "", "", "", "", "", "", "", "")
        next_match = scraper.Match("", "", "", "", "", "", "", "", "", "")

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
            output = await Artiglio.ranking(event, local=True)
            html_parse = True
        elif event.data == b"artiglio__global_rank":
            output = await Artiglio.ranking(event, local=False)
            html_parse = True
        elif event.data == b"artiglio__stats":
            output = Artiglio.artiglio_stats(event)
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
