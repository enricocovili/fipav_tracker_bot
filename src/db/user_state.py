from enum import Enum, auto
from dataclasses import dataclass, field
from typing import Optional


class UserStateEnum(Enum):
    DEFAULT = auto()
    CHOOSING_CHAMPIONSHIP = auto()
    CHOOSING_TEAM = auto()


@dataclass
class UserState:
    state: UserStateEnum = UserStateEnum.DEFAULT
    championship_selected: Optional[str] = None
    team_selected: Optional[str] = None
