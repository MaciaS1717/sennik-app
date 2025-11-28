from sqlmodel import SQLModel, Field, Relationship
from typing import Optional, TYPE_CHECKING
from datetime import datetime

if TYPE_CHECKING:
    from .user import User


class Entry(SQLModel, table=True):
    __tablename__ = "entries"

    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="users.id")

    date: datetime = Field(default_factory=datetime.utcnow)
    mood: int
    sleep_hours: float
    exercise_minutes: int
    notes: Optional[str] = None

    # Relacja N -> 1
    user: Optional["User"] = Relationship(back_populates="entries")
