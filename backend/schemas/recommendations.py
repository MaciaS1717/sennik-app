from typing import Literal

from pydantic import BaseModel


class DurationRangeRead(BaseModel):
    low: int                        # minuty snu
    high: int
    source: Literal["dane", "zalecenia"]
    nights: int                     # z ilu pełnych nocy liczony zakres
    note: str | None = None


class RatedOptionRead(BaseModel):
    duration: int                   # minuty snu
    mean_energy: float | None       # średnia energia rano po podobnie długim śnie
    nights: int
    rating: Literal["dobra", "slabsza", "za_malo_danych", "brak_oceny"]


class SleepPlanRead(BaseModel):
    bedtime: str                    # HH:MM
    onset: str
    wake: str
    option: RatedOptionRead


class SleepWindowResponse(BaseModel):
    mode: Literal["wake_time", "bedtime", "best"]
    duration_range: DurationRangeRead
    latency: int                    # czas zasypiania (min)
    latency_source: Literal["dane", "profil"]
    plans: list[SleepPlanRead]
    notes: list[str]
