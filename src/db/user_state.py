from enum import Enum, auto
from dataclasses import dataclass
from typing import Optional
from db.models import Team, Championship


class UserStateEnum(Enum):
    DEFAULT = auto()
    CHOOSING_CHAMPIONSHIP = auto()
    CHOOSING_TEAM = auto()


@dataclass
class UserState:
    state: UserStateEnum = UserStateEnum.DEFAULT
    championship_selected: Optional[Championship] = None
    team_selected: Optional[Team] = None
