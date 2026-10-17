from sqlalchemy import (
    Column,
    Integer,
    String,
    ForeignKey,
    Table,
    TIMESTAMP,
    UniqueConstraint,
)
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()

# Championships a user receives update notifications for (many-to-many)
user_championships = Table(
    "user_championships",
    Base.metadata,
    Column(
        "user_id",
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        primary_key=True,
    ),
    Column(
        "championship_id",
        Integer,
        ForeignKey("championships.id", ondelete="CASCADE"),
        primary_key=True,
    ),
)

# Teams a user receives match notifications for (many-to-many)
user_teams = Table(
    "user_teams",
    Base.metadata,
    Column(
        "user_id",
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        primary_key=True,
    ),
    Column(
        "team_id",
        Integer,
        ForeignKey("teams.id", ondelete="CASCADE"),
        primary_key=True,
    ),
)


class Championship(Base):
    __tablename__ = "championships"

    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False)
    group_name = Column(String(10))
    url = Column(String(255), nullable=False)
    start_year = Column(Integer, nullable=False)
    end_year = Column(Integer, nullable=False)

    matches = relationship(
        "Match", back_populates="championship", cascade="all, delete-orphan"
    )
    standings = relationship(
        "Standing", back_populates="championship", cascade="all, delete-orphan"
    )

    __table_args__ = (UniqueConstraint("name", "group_name", "start_year", "end_year"),)


class Team(Base):
    __tablename__ = "teams"

    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False)

    home_matches = relationship(
        "Match", foreign_keys="Match.home_team_id", back_populates="home_team"
    )
    away_matches = relationship(
        "Match", foreign_keys="Match.away_team_id", back_populates="away_team"
    )
    standings = relationship(
        "Standing", back_populates="team", cascade="all, delete-orphan"
    )


class Match(Base):
    __tablename__ = "matches"

    id = Column(Integer, primary_key=True)
    championship_id = Column(
        Integer, ForeignKey("championships.id", ondelete="CASCADE"), nullable=False
    )
    match_date = Column(TIMESTAMP, nullable=False)
    weekday = Column(String(10))
    home_team_id = Column(
        Integer, ForeignKey("teams.id", ondelete="CASCADE"), nullable=False
    )
    away_team_id = Column(
        Integer, ForeignKey("teams.id", ondelete="CASCADE"), nullable=False
    )
    result = Column(String(50), nullable=False)  # "3-1" or full set scores
    city = Column(String(100))
    address = Column(String(200))
    maps_url = Column(String(255))

    championship = relationship("Championship", back_populates="matches")
    home_team = relationship(
        "Team", foreign_keys=[home_team_id], back_populates="home_matches"
    )
    away_team = relationship(
        "Team", foreign_keys=[away_team_id], back_populates="away_matches"
    )

    __table_args__ = (
        UniqueConstraint(
            "championship_id", "match_date", "home_team_id", "away_team_id"
        ),
    )


class Standing(Base):
    __tablename__ = "standings"

    id = Column(Integer, primary_key=True)
    championship_id = Column(
        Integer, ForeignKey("championships.id", ondelete="CASCADE"), nullable=False
    )
    team_id = Column(
        Integer, ForeignKey("teams.id", ondelete="CASCADE"), nullable=False
    )
    rank = Column(Integer, default=0)
    points = Column(Integer, default=0)
    matches_won = Column(Integer, default=0)
    matches_lost = Column(Integer, default=0)
    num_3_0 = Column(Integer, default=0)
    num_3_1 = Column(Integer, default=0)
    num_3_2 = Column(Integer, default=0)
    num_2_3 = Column(Integer, default=0)
    num_1_3 = Column(Integer, default=0)
    num_0_3 = Column(Integer, default=0)
    sets_won = Column(Integer, default=0)
    sets_lost = Column(Integer, default=0)
    points_scored = Column(Integer, default=0)
    points_conceded = Column(Integer, default=0)

    __table_args__ = (
        UniqueConstraint("championship_id", "team_id", name="uq_standing"),
    )

    championship = relationship("Championship", back_populates="standings")
    team = relationship("Team", back_populates="standings")


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True)
    username = Column(String(50), nullable=False)

    tracked_championships = relationship(
        "Championship", secondary=user_championships, passive_deletes=True
    )
    tracked_teams = relationship("Team", secondary=user_teams, passive_deletes=True)
