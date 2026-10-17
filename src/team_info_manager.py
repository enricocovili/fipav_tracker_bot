import logging
from datetime import datetime

import db.crud
import scrapers.matches_rankings as rankings
from db.models import Team, Championship, Match
from standing_manager import StandingManager

WEEKDAYS = ["Lun", "Mar", "Mer", "Gio", "Ven", "Sab", "Dom"]


class TeamInfoManager:
    @staticmethod
    def _score(match: Match) -> tuple[int, int] | None:
        """Sets won by (home, away), None if the result is not parseable."""
        try:
            home, away = match.result.strip().split("-")
            return int(home), int(away)
        except ValueError:
            return None

    @staticmethod
    def _won(match: Match, team: Team) -> bool | None:
        score = TeamInfoManager._score(match)
        if score is None or score[0] == score[1]:
            return None
        home_won = score[0] > score[1]
        return home_won if match.home_team_id == team.id else not home_won

    @staticmethod
    def _when(date: datetime) -> str:
        return f"{WEEKDAYS[date.weekday()]} {date:%d/%m %H:%M}"

    @staticmethod
    def _avulsa_rank(team: Team, championship: Championship) -> int | None:
        standings = StandingManager(championship, is_avulsa=True).standings
        for position, standing in enumerate(standings, start=1):
            if standing.team_id == team.id:
                return position
        return None

    @staticmethod
    def _next_match(team: Team, championship: Championship) -> str | None:
        """Earliest unplayed match, read from the FIPAV site (not stored in the db)."""
        try:
            upcoming = []
            for match in rankings.MatchesRankingsScraper().get_matches(
                championship.url
            ):
                if match.get("result") != "" or team.name not in (
                    match["home_team"].strip(),
                    match["away_team"].strip(),
                ):
                    continue
                date = datetime.strptime(
                    f"{match['match_date']} {match['time'].strip()}", "%d/%m/%Y %H:%M"
                )
                upcoming.append((date, match))
        except Exception as e:
            logging.warning(f"could not fetch next match of {team.name}: {e}")
            return None
        if not upcoming:
            return None
        date, match = min(upcoming, key=lambda m: m[0])
        at_home = match["home_team"].strip() == team.name
        opponent = match["away_team" if at_home else "home_team"].strip()
        return (
            f"{TeamInfoManager._when(date)}\n"
            f"vs {opponent} ({'casa' if at_home else 'trasferta'})"
        )

    @staticmethod
    def _played_match_line(match: Match, team: Team) -> str:
        at_home = match.home_team_id == team.id
        opponent = match.away_team if at_home else match.home_team
        won = TeamInfoManager._won(match, team)
        outcome = {True: "✅", False: "❌", None: ""}[won]
        return (
            f"{TeamInfoManager._when(match.match_date)}\n"
            f"vs {opponent.name} ({'casa' if at_home else 'trasferta'}) "
            f"· {match.result.strip()} {outcome}".rstrip()
        )

    @staticmethod
    def team_stats(team: Team, championship: Championship) -> str:
        standing = next(
            (
                s
                for s in db.crud.get_standings_in_championship(
                    championship_id=championship.id
                )
                if s.team_id == team.id
            ),
            None,
        )
        if standing is None:
            return f"Nessuna informazione disponibile per **{team.name}**."

        matches = sorted(
            (
                m
                for m in db.crud.get_matches_for_team(team.id)
                if m.championship_id == championship.id
            ),
            key=lambda m: m.match_date,
        )

        played = standing.matches_won + standing.matches_lost
        win_pct = round(standing.matches_won / played * 100) if played else 0
        set_ratio = (
            f" (QS {standing.sets_won / standing.sets_lost:.2f})"
            if standing.sets_lost
            else ""
        )
        point_ratio = (
            f" (QP {standing.points_scored / standing.points_conceded:.2f})"
            if standing.points_conceded
            else ""
        )
        avulsa_rank = TeamInfoManager._avulsa_rank(team, championship)

        lines = [
            f"🏐 **{team.name}**",
            f"__{championship.name} - Girone {championship.group_name}__",
            "",
            "📊 **Classifica**",
            f"• Girone: **{standing.rank}°**"
            + (f" · Avulsa: **{avulsa_rank}°**" if avulsa_rank else ""),
            f"• Punti: **{standing.points}**",
            f"• Partite: {played} giocate · {standing.matches_won}V "
            f"{standing.matches_lost}P ({win_pct}%)",
            f"• Set: {standing.sets_won}-{standing.sets_lost}{set_ratio}",
            f"• Punti fatti/subiti: {standing.points_scored}-"
            f"{standing.points_conceded}{point_ratio}",
        ]

        form = "".join(
            {True: "✅", False: "❌", None: "➖"}[TeamInfoManager._won(m, team)]
            for m in matches[-5:]
        )
        if form:
            lines += ["", f"📈 **Ultime {min(len(matches), 5)}**: {form}"]

        if matches:
            lines += [
                "",
                "⏮ **Ultima partita**",
                TeamInfoManager._played_match_line(matches[-1], team),
            ]

        next_match = TeamInfoManager._next_match(team, championship)
        if next_match:
            lines += ["", "⏭ **Prossima partita**", next_match]

        return "\n".join(lines)
