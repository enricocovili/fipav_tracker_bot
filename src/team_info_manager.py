import db.crud


class TeamInfoManager():
    @staticmethod
    def team_stats(team_id: int, championship_id: int):
        # TODO: insert here db crud operations
        info_artiglio = [
            team for team in teams if "artiglio" in team.name.lower()][0]

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
