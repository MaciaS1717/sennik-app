from dataclasses import dataclass, field
from typing import Literal

from pydantic import BaseModel, Field

from ..insights import Fact

# 6 intencji czatu: o co pyta użytkownik.
Intent = Literal[
    "advice",             # jak poprawić sen albo samopoczucie
    "sleep_window",       # kalkulator snu: o której się położyć / wstać
    "habit_effect",       # jak nawyk (albo weekend) wpływa na mój sen i dzień
    "summary",            # jak spałem w tym tygodniu / miesiącu
    "general_knowledge",  # ogólne pytania o sen i o aplikację
    "off_topic",          # pytanie spoza zakresu aplikacji: stała odmowa
]

# Czynniki do habit_effect: 5 nawyków i weekend, nazwy jak w compare.FACTORS.
HabitName = Literal["coffee", "alcohol", "screens_high", "nap_long", "stress_high", "is_weekend"]

# Godzina "07:00" albo "7:00" (LLM czasem pomija zero, a kalkulator radzi sobie z oboma).
TIME_PATTERN = r"^([01]?\d|2[0-3]):[0-5]\d$"


class IntentResult(BaseModel):
    # Wynik klasyfikatora (LLM nr 1): jedna intencja z listy i jej parametry; niepotrzebne pola = None.
    intent: Intent
    focus: Literal["sleep", "wellbeing"] | None = None          # advice: noc czy samopoczucie w dzień
    # sleep_window, jak w kalkulatorze: CZEGO SZUKAMY.
    # "bedtime" = znam pobudkę, szukam pory snu („muszę wstać o 7”);
    # "wake_time" = znam porę snu, szukam pobudki („zasnę o 23”); "best" = bez godziny.
    mode: Literal["wake_time", "bedtime", "best"] | None = None
    time: str | None = Field(None, pattern=TIME_PATTERN)
    time_type: Literal["falls_asleep", "goes_to_bed"] | None = None   # tylko przy "wake_time"
    habit: HabitName | None = None                              # habit_effect
    period: Literal["week", "month"] | None = None              # summary: 7 albo 30 dni


@dataclass
class FactSheet:
    # Wszystko, co dostaje redaktor (LLM nr 2): z tego i tylko z tego pisze odpowiedź.
    intent: str
    level: str                  # "start" albo "osobisty"
    nights: int                 # noce z raportem porannym w całej historii
    gender: str                 # "male" albo "female": forma gramatyczna odpowiedzi
    facts: list[Fact]           # gotowe zdania i napisy z liczbami (jedyne liczby, które wolno podać)
    guidelines: list[dict]      # pasujące sprawdzone zalecenia
    notes: list[str] = field(default_factory=list)   # dodatkowe uwagi, np. z kalkulatora
