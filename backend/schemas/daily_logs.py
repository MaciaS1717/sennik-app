from datetime import date, datetime
from typing import Optional
from sqlmodel import SQLModel
from enum import Enum
from sqlmodel import Field

class ScreensLastHour(str, Enum):
    low = "low"
    medium = "medium"
    high = "high"

class NapType(str, Enum):
    none = "none"
    short = "short"
    medium = "medium"
    long = "long"

# Schemat: PORANNY RAPORT

class DailyLogCreateMorning(SQLModel):
    date: date

    sleep_start: datetime
    sleep_latency_extra: int = Field(ge=0, le=180)
    sleep_end: datetime

    sleep_quality: int  = Field(ge=1, le=10)  # TARGET1
    night_awakenings: int = Field(ge=0, le=10)
    morning_energy: int  = Field(ge=1, le=10)  # TARGET1


# Schemat: WIECZORNY RAPORT

class DailyLogUpdateEvening(SQLModel):
    date: date #dzien D

    day_rating: Optional[int] =  Field(default=None, ge=1, le=10)  # 1–10 (TARGET2)
    stress_level: Optional[int] = Field(default=None, ge=1, le=10)
    coffee_last_6h: Optional[bool] = None
    alcohol_last_4h: Optional[bool] = None
    screens_last_hour: Optional[ScreensLastHour] = None
    nap_type: Optional[NapType] = None



# Schemat: ODCZYT (PEŁNY)

class DailyLogRead(SQLModel):
    id: int
    user_id: int
    date: date

    sleep_start: Optional[datetime]
    sleep_latency_extra: Optional[int]
    sleep_end: Optional[datetime]
    sleep_quality: Optional[int]
    night_awakenings: Optional[int]
    morning_energy: Optional[int]

    day_rating: Optional[int]
    stress_level: Optional[int]
    coffee_last_6h: Optional[bool]
    alcohol_last_4h: Optional[bool]
    screens_last_hour: Optional[ScreensLastHour]
    nap_type: Optional[NapType]

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