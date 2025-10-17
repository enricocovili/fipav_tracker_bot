import db.crud
from db.models import Team, Championship, Standing


class TeamInfoManager:
    @staticmethod
    def team_stats(team: Team, championship: Championship) -> str:
        standings = db.crud.get_standings_in_championship(
            championship_id=championship.id
        )
        standing = [
            _standing for _standing in standings if _standing.team.id == team.id
        ][0]
        matches = [
            match
            for match in db.crud.get_matches_for_team(team.id)
            if match.championship.id == championship.id
        ]

        # data calculation
        matches_played = standing.matches_won + standing.matches_lost
        won_percentage = round(standing.matches_won / (matches_played) * 100, 2)

        # Mobile friendly output
        output = f"""
            Informazioni su **{team.name}**:
            ⬤ **Rank Girone {championship.group_name}**: {standing.rank}
            ⬤ **Rank Avulsa**: Non funziona per ora {standing.rank}
            ⬤ **Punti**: {standing.points}
            ⬤ **% Vittorie**: {won_percentage}% ({standing.matches_won}/{matches_played})
        """
        """
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
