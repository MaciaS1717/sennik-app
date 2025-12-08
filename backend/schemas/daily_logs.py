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
    date: date #dzien D

    day_rating: Optional[int] = None  # 1–10 (TARGET2)
    stress_level: Optional[int] = None
    coffee_last_6h: Optional[bool] = None
    alcohol_last_4h: Optional[bool] = None
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
    coffee_last_6h: Optional[bool]
    alcohol_last_4h: Optional[bool]
    screens_last_hour: Optional[str]
    nap_type: Optional[str]

    sleep_duration: Optional[float]
    day_score: Optional[float]

    created_at: datetime
    updated_at: datetime

class DailyLogEveningResponse(SQLModel):
    """Odpowiedź dla raportu wieczornego:
    - today: log dla dnia D (ocena dnia)
    - tomorrow: log dla dnia D+1 (nawyki, które wpłyną na kolejny sen)
    """
    today: DailyLogRead
    tomorrow: DailyLogRead