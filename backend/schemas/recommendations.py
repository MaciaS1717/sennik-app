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


class FactRead(BaseModel):
    id: str                         # np. "effect.coffee.latency_extra"
    kind: Literal["effect", "habit_rate", "regularity"]
    text: str                       # gotowe zdanie dla użytkownika
    values: dict[str, str]          # gotowe napisy z liczbami
    nights: int


class CardRead(BaseModel):
    factor: str
    fact: FactRead                  # najsilniejszy wniosek nawyku
    also: list[FactRead]            # pozostałe wnioski tego nawyku


class GuidelineRead(BaseModel):
    id: str
    title: str
    text: str
    sources: list[str]


class InsightsResponse(BaseModel):
    level: Literal["start", "osobisty"]
    nights: int                     # noce z raportem porannym w całej historii
    note: str | None
    cards: list[CardRead]
    facts: list[FactRead]
    guidelines: list[GuidelineRead]


class HabitCellRead(BaseModel):
    outcome: str
    result: Literal["wniosek", "brak_wniosku", "za_malo_danych"]
    diff: str | None                # np. "+21 min"; None przy za małej liczbie nocy
    nights_with: int
    nights_without: int
    window: str


class HabitRowRead(BaseModel):
    factor: str
    label: str
    cells: list[HabitCellRead]


class HabitsTableResponse(BaseModel):
    rows: list[HabitRowRead]
