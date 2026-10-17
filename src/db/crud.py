import os
import math
from functools import wraps
from contextlib import contextmanager
from sqlalchemy import create_engine
from sqlalchemy import case
from sqlalchemy.orm import sessionmaker, scoped_session, Session

from db.models import Championship, Team, Match, Standing, User, user_championships, user_teams

# -------------------
# Database setup
# -------------------

DATABASE_URL = (
    f"postgresql+psycopg2://{os.getenv('POSTGRES_USER')}:{os.getenv('POSTGRES_PASSWORD')}"
    f"@{os.getenv('POSTGRES_HOST')}/{os.getenv('POSTGRES_DB')}"
)

engine = create_engine(DATABASE_URL, echo=False, future=True)
SessionLocal = scoped_session(
    sessionmaker(bind=engine, autoflush=False, autocommit=False)
)


@contextmanager
def get_session():
    """Provide a transactional scope."""
    session = SessionLocal()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    # finally:
    # session.close()


def with_session(func):
    """Decorator to provide a session to the function."""

    @wraps(func)
    def wrapper(*args, **kwargs):
        with get_session() as db:
            return func(db, *args, **kwargs)

    return wrapper


# -------------------
# Championships
# -------------------


@with_session
def create_championship(db, name, url, start_year, end_year, group_name=None):
    champ = Championship(
        name=name,
        url=url,
        start_year=start_year,
        end_year=end_year,
        group_name=group_name,
    )
    db.add(champ)
    db.flush()
    db.refresh(champ)
    return champ


@with_session
def get_all_championships(db):
    return db.query(Championship).all()


@with_session
def get_championship_by_id(db, ch_id):
    return db.get(Championship, ch_id)


@with_session
def get_championships_by_name(db, name):
    q = db.query(Championship).filter_by(name=name)
    return q.all()


@with_session
def get_championship(db, name, group_name, start_year, end_year):
    return (
        db.query(Championship)
        .filter_by(
            name=name, group_name=group_name, start_year=start_year, end_year=end_year
        )
        .first()
    )


@with_session
def update_championship(db, ch_id, **fields):
    champ = db.get(Championship, ch_id)
    if not champ:
        return None
    for k, v in fields.items():
        setattr(champ, k, v)
    db.flush()
    db.refresh(champ)
    return champ


@with_session
def delete_championship(db, ch_id):
    champ = db.get(Championship, ch_id)
    if champ:
        db.delete(champ)


# -------------------
# Teams
# -------------------


@with_session
def create_team(db, name):
    team = Team(name=name)
    db.add(team)
    db.flush()
    db.refresh(team)
    return team


@with_session
def get_team_by_id(db, team_id):
    return db.get(Team, team_id)


@with_session
def get_team_by_name(db, team_name):
    return db.query(Team).filter_by(name=team_name).all()


@with_session
def get_teams_by_championship(db, championship_id):
    return (
        db.query(Team)
        .join(Standing, Team.id == Standing.team_id)
        .filter(Standing.championship_id == championship_id)
        .all()
    )


@with_session
def delete_team(db, team_id):
    team = db.get(Team, team_id)
    if team:
        db.delete(team)


# -------------------
# Matches
# -------------------


@with_session
def create_match(
    db,
    championship_id,
    match_date,
    home_team_id,
    away_team_id,
    result,
    weekday=None,
    city=None,
    address=None,
):
    match = Match(
        championship_id=championship_id,
        match_date=match_date,
        weekday=weekday,
        home_team_id=home_team_id,
        away_team_id=away_team_id,
        result=result,
        city=city,
        address=address,
    )
    db.add(match)
    db.flush()
    db.refresh(match)
    return match


@with_session
def get_match_by_id(db, match_id):
    return db.get(Match, match_id)


@with_session
def get_matches_by_championship(db, championship_id):
    return db.query(Match).filter_by(championship_id=championship_id).all()


@with_session
def get_matches_for_team(db, team_id):
    return (
        db.query(Match)
        .filter((Match.home_team_id == team_id) | (Match.away_team_id == team_id))
        .all()
    )


@with_session
def update_match(db, match_id, **fields):
    match = db.get(Match, match_id)
    if not match:
        return None
    for k, v in fields.items():
        setattr(match, k, v)
    db.flush()
    db.refresh(match)
    return match


@with_session
def delete_match(db, match_id):
    match = db.get(Match, match_id)
    if match:
        db.delete(match)


# -------------------
# Standings
# -------------------


@with_session
def create_standing(db, team_id, championship_id):
    standing = Standing(championship_id=championship_id, team_id=team_id)
    db.add(standing)
    db.flush()
    db.refresh(standing)
    return standing


@with_session
def get_standing_by_id(db, standing_id):
    return db.get(Standing, standing_id)


@with_session
def get_standings_in_championship(
    db, championship_id: int = None, championship_name: str = "", sorted=True
):
    if championship_id:
        q = db.query(Standing).filter_by(championship_id=championship_id)
    else:
        q = (
            db.query(Standing)
            .filter_by(championship_name=championship_name)
            .distinct(Standing.team_id)
        )
    if sorted:
        set_ratio = case(
            (Standing.sets_lost == 0, math.inf),
            else_=Standing.sets_won / Standing.sets_lost,
        )
        point_ratio = case(
            (Standing.points_conceded == 0, math.inf),
            else_=Standing.points_scored / Standing.points_conceded,
        )

        q = q.order_by(
            Standing.points.desc(),
            Standing.matches_won.desc(),
            set_ratio.desc(),
            point_ratio.desc(),
        )
    return q.all()


@with_session
def update_standing(db, standing_id, **fields):
    standing = db.get(Standing, standing_id)
    if not standing:
        return None
    for k, v in fields.items():
        setattr(standing, k, v)
    db.flush()
    db.refresh(standing)
    return standing


@with_session
def delete_standing(db, standing_id):
    standing = db.get(Standing, standing_id)
    if standing:
        db.delete(standing)


# -------------------
# Users
# -------------------


@with_session
def create_user(
    db: Session,
    id: int,
    username: str,
):
    user = User(id=id, username=username)
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@with_session
def get_user(db: Session, user_id: int):
    return db.query(User).filter(User.id == user_id).first()


@with_session
def get_users(db: Session):
    return db.query(User).all()


@with_session
def update_user(db: Session, user_id: int, **kwargs):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        return None
    for key, value in kwargs.items():
        setattr(user, key, value)
    db.commit()
    db.refresh(user)
    return user


@with_session
def delete_user(db: Session, user_id: int):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        return None
    db.delete(user)
    db.commit()
    return user


# -------------------
# User championship tracking
# -------------------


@with_session
def get_user_championships(db: Session, user_id: int):
    return (
        db.query(Championship)
        .join(user_championships, Championship.id == user_championships.c.championship_id)
        .filter(user_championships.c.user_id == user_id)
        .all()
    )


@with_session
def is_tracking_championship(db: Session, user_id: int, championship_id: int) -> bool:
    return (
        db.query(user_championships)
        .filter_by(user_id=user_id, championship_id=championship_id)
        .first()
        is not None
    )


@with_session
def track_championship(db: Session, user_id: int, championship_id: int) -> None:
    """Idempotently add a championship to the user's tracked ones."""
    if not db.get(User, user_id) or not db.get(Championship, championship_id):
        return
    already = (
        db.query(user_championships)
        .filter_by(user_id=user_id, championship_id=championship_id)
        .first()
    )
    if not already:
        db.execute(
            user_championships.insert().values(
                user_id=user_id, championship_id=championship_id
            )
        )


@with_session
def untrack_championship(db: Session, user_id: int, championship_id: int) -> None:
    db.execute(
        user_championships.delete().where(
            (user_championships.c.user_id == user_id)
            & (user_championships.c.championship_id == championship_id)
        )
    )


@with_session
def get_users_tracking_championship(db: Session, championship_id: int):
    return (
        db.query(User)
        .join(user_championships, User.id == user_championships.c.user_id)
        .filter(user_championships.c.championship_id == championship_id)
        .all()
    )


# -------------------
# User team tracking
# -------------------


@with_session
def get_user_teams(db: Session, user_id: int):
    return (
        db.query(Team)
        .join(user_teams, Team.id == user_teams.c.team_id)
        .filter(user_teams.c.user_id == user_id)
        .all()
    )


@with_session
def is_tracking_team(db: Session, user_id: int, team_id: int) -> bool:
    return (
        db.query(user_teams).filter_by(user_id=user_id, team_id=team_id).first()
        is not None
    )


@with_session
def track_team(db: Session, user_id: int, team_id: int) -> None:
    """Idempotently add a team to the user's tracked ones."""
    if not db.get(User, user_id) or not db.get(Team, team_id):
        return
    if not db.query(user_teams).filter_by(user_id=user_id, team_id=team_id).first():
        db.execute(user_teams.insert().values(user_id=user_id, team_id=team_id))


@with_session
def untrack_team(db: Session, user_id: int, team_id: int) -> None:
    db.execute(
        user_teams.delete().where(
            (user_teams.c.user_id == user_id) & (user_teams.c.team_id == team_id)
        )
    )


@with_session
def get_users_tracking_team(db: Session, team_id: int):
    return (
        db.query(User)
        .join(user_teams, User.id == user_teams.c.user_id)
        .filter(user_teams.c.team_id == team_id)
        .all()
    )


# -------------------
# Utilities
# -------------------


@with_session
def get_table(db, championship_id):
    """Return standings with set_ratio and point_ratio calculated in Python."""
    teams = db.query(Team).filter_by(championship_id=championship_id).all()
    results = []
    for t in teams:
        set_ratio = t.sets_won / t.sets_lost if t.sets_lost else None
        point_ratio = t.points_scored / t.points_conceded if t.points_conceded else None
        results.append(
            {
                **t.__dict__,
                "set_ratio": set_ratio,
                "point_ratio": point_ratio,
            }
        )
    results.sort(
        key=lambda x: (x["points"], x["set_ratio"] or 0, x["point_ratio"] or 0),
        reverse=True,
    )
    return results
