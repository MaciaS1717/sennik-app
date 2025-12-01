from datetime import date, datetime
from typing import Optional
from sqlmodel import SQLModel


# Schemat: PORANNY RAPORT

class DailyLogCreateMorning(SQLModel):
    date: date

    sleep_start: datetime
    sleep_latency_extra: int
    sleep_end: datetime

    sleep_quality: int  # 1–10
    night_awakenings: int
    morning_energy: int  # TARGET1


# Schemat: WIECZORNY RAPORT

class DailyLogUpdateEvening(SQLModel):
    day_rating: Optional[int] = None  # 1–10 (TARGET2)
    stress_level: Optional[int] = None
    coffee_after_16: Optional[bool] = None
    alcohol_after_18: Optional[bool] = None
    screens_last_hour: Optional[str] = None  # "low" | "medium" | "high"
    nap_type: Optional[str] = None  # "none" | "short" | "medium" | "long"



# Schemat: ODCZYT (PEŁNY)

class DailyLogRead(SQLModel):
    id: int
    user_id: int
    date: date

    sleep_start: datetime
    sleep_latency_extra: int
    sleep_end: datetime
    sleep_quality: int
    night_awakenings: int
    morning_energy: int

    day_rating: Optional[int]
    stress_level: Optional[int]
    coffee_after_16: Optional[bool]
    alcohol_after_18: Optional[bool]
    screens_last_hour: Optional[str]
    nap_type: Optional[str]

    sleep_duration: Optional[float]
    day_score: Optional[float]

    created_at: datetime
    updated_at: datetime
