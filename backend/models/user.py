from sqlmodel import SQLModel, Field, Relationship
from typing import Optional, List, TYPE_CHECKING

from enum import Enum

class Gender(str, Enum):
    male = "male"
    female = "female"


if TYPE_CHECKING:
    from .daily_log import DailyLog


class User(SQLModel, table=True):
    __tablename__ = "users"

    id: Optional[int] = Field(default=None, primary_key=True)
    email: str = Field(index=True, unique=True)
    hashed_password: str
    name: str
    gender: Gender
    age: int
    typical_sleep_latency: int  # minuty


    # Relacja 1 -> N
    daily_logs: List["DailyLog"] = Relationship(back_populates="user")