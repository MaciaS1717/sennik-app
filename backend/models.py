from sqlmodel import SQLModel, Field, Relationship
from typing import Optional, List
from datetime import datetime


class User(SQLModel, table=True):
    __tablename__ = "users"

    id: Optional[int] = Field(default=None, primary_key=True)
    email: str = Field(index=True, unique=True)
    hashed_password: str

    entries: List["Entry"] = Relationship(back_populates="user")


class Entry(SQLModel, table=True):
    __tablename__ = "entries"

    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="users.id")

    date: datetime = Field(default_factory=datetime.utcnow)
    mood: int = Field(description="Skala 1–10, jak się czujesz dzisiaj?")
    sleep_hours: float = Field(description="Ile spałeś godzin?")
    exercise_minutes: int = Field(description="Ile minut ruchu?")
    notes: Optional[str] = None

    user: Optional[User] = Relationship(back_populates="entries")
