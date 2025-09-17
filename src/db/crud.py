import os
from functools import wraps
from contextlib import contextmanager
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, scoped_session, Session

from db.models import Championship, Team, Match, Standing, User

# -------------------
# Database setup
# -------------------

DATABASE_URL = (
    f"postgresql+psycopg2://{os.getenv('POSTGRES_USER')}:{os.getenv('POSTGRES_PASSWORD')}"
    f"@{os.getenv('POSTGRES_HOST')}/{os.getenv('POSTGRES_DB')}"
)

engine = create_engine(DATABASE_URL, echo=False, future=True)
SessionLocal = scoped_session(sessionmaker(
    bind=engine, autoflush=False, autocommit=False))


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
def create_championship(db, name, url, season, group=None):
    champ = Championship(name=name, url=url, season=season, group=group)
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
    return db.query(Team).join(Standing, Team.id == Standing.team_id).filter(
        Standing.championship_id == championship_id
    ).all()


@with_session
def delete_team(db, team_id):
    team = db.get(Team, team_id)
    if team:
        db.delete(team)


# -------------------
# Matches
# -------------------

@with_session
def create_match(db, championship_id, match_date, home_team_id, away_team_id, result, weekday=None, city=None, address=None):
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
    return db.query(Match).filter(
        (Match.home_team_id == team_id) | (Match.away_team_id == team_id)
    ).all()


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
def get_standings_in_championship(db, championship_id, sorted=True):
    q = db.query(Standing).filter_by(championship_id=championship_id)
    if sorted:
        q = q.order_by(
            Standing.points.desc(),
            Standing.wins.desc(),
            (Standing.sets_won / Standing.sets_lost).desc(),
            (Standing.points_scored / Standing.points_conceded).desc()
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
def create_user(db: Session, id: int, username: str, tracked_championship: int = None, tracked_team: int = None):
    user = User(
        id=id,
        username=username,
        tracked_championship=tracked_championship,
        tracked_team=tracked_team,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@with_session
def get_user(db: Session, user_id: int):
    return db.query(User).filter(User.id == user_id).first()


@with_session
def get_users(db: Session, skip: int = 0, limit: int = 100):
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
        results.append({
            **t.__dict__,
            "set_ratio": set_ratio,
            "point_ratio": point_ratio,
        })
    results.sort(key=lambda x: (
        x["points"], x["set_ratio"] or 0, x["point_ratio"] or 0), reverse=True)
    return results
