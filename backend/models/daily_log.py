from __future__ import annotations

from datetime import date, datetime
from enum import Enum
from typing import Optional, TYPE_CHECKING

from sqlmodel import SQLModel, Field, Relationship

if TYPE_CHECKING:
    from .user import User


class ScreensLastHour(str, Enum):
    low = "low"
    medium = "medium"
    high = "high"


class NapType(str, Enum):
    none = "none"
    short = "short"
    medium = "medium"
    long = "long"


class DailyLog(SQLModel, table=True):
    __tablename__ = "daily_logs"

    # Identyfikacja
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="users.id", index=True)
    date: date

    # Poranny raport
    sleep_start: Optional[datetime]
    sleep_latency_extra: Optional[int] = Field(default=0)  # minuty
    sleep_end: Optional[datetime]
    sleep_quality: Optional[int]  # 1–10
    night_awakenings: Optional[int]
    morning_energy: Optional[int]  # 1–10 (TARGET1)

    # Wieczorny raport
    day_rating: Optional[int]  # 1–10 (TARGET2)
    stress_level: Optional[int]  # 1–10
    coffee_last_6h: Optional[bool] = Field(default=False)
    alcohol_last_4h: Optional[bool] = Field(default=False)
    screens_last_hour: Optional[ScreensLastHour]
    nap_type: Optional[NapType]

    # Kolumny wyliczane / pomocnicze
    sleep_duration: Optional[float] = None  # godziny
    day_score: Optional[float] = None

    created_at: Optional[datetime] = Field(default_factory=datetime.utcnow)
    updated_at: Optional[datetime] = Field(default_factory=datetime.utcnow)

    # Relacja N -> 1
    user: Optional["User"] = Relationship(back_populates="daily_logs")
