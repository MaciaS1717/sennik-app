from dataclasses import dataclass
from datetime import date

import pandas as pd

from .compare import (
    FACTORS, Comparison, compare_all, data_level, habit_rates, regularity, summary, top_findings,
)
from .guidelines import IRREGULAR_ONSET_MIN, Situation, load_guidelines, matching_guidelines

# Początek zdania: w jakie dni (czynnik).
FACTOR_PHRASES = {
    "coffee": "Po wieczorach z kawą",
    "alcohol": "Po wieczorach z alkoholem",
    "screens_high": "Gdy przed snem dużo korzystasz z ekranów,",
    "nap_long": "Po dniach z długą drzemką",
    "stress_high": "Po wieczorach z wysokim stresem",
    "is_weekend": "W noce przed sobotą i niedzielą",
    "short_sleep_6h": "Po nocach krótszych niż 6 h",
    "short_sleep_7h": "Po nocach krótszych niż 7 h",
}

# Dalsza część zdania: (gdy wynik jest większy, gdy mniejszy); {diff} = różnica z jednostką.
OUTCOME_PHRASES = {
    "latency_extra": ("zasypiasz średnio o {diff} dłużej", "zasypiasz średnio o {diff} krócej"),
    "awakenings": ("masz w nocy średnio o {diff} wybudzenia więcej", "masz w nocy średnio o {diff} wybudzenia mniej"),
    "quality": ("oceniasz jakość snu średnio o {diff} wyżej", "oceniasz jakość snu średnio o {diff} niżej"),
    "duration": ("śpisz średnio o {diff} dłużej", "śpisz średnio o {diff} krócej"),
    "energy": ("masz rano średnio o {diff} więcej energii", "masz rano średnio o {diff} mniej energii"),
    "day_rating": ("oceniasz dzień średnio o {diff} wyżej", "oceniasz dzień średnio o {diff} niżej"),
}

MINUTE_OUTCOMES = {"latency_extra", "duration"}     # wyniki w minutach; pozostałe w punktach lub sztukach
WINDOW_LABELS = {7: "ostatnie 7 dni", 30: "ostatnie 30 dni", 90: "ostatnie 90 dni", "all": "cała historia"}
SUMMARY_DAYS = 30          # częstości nawyków i regularność z ostatnich 30 dni


@dataclass
class Fact:
    # Jeden fakt o użytkowniku: gotowe zdanie i gotowe napisy (dla karty, tabeli i czatu).
    id: str                     # np. "effect.coffee.latency_extra"
    kind: str                   # "effect", "habit_rate" albo "regularity"
    text: str                   # „Po wieczorach z kawą zasypiasz średnio o 21 min dłużej.”
    values: dict[str, str]      # {"diff": "21 min", "with": "30 min", "without": "9 min", ...}
    nights: int                 # z ilu nocy policzony


def _format_minutes(value: float) -> str:
    # 21.4 -> "21 min", 65 -> "1 h 5 min", 420 -> "7 h".
    hours, minutes = divmod(round(value), 60)
    if hours == 0:
        return f"{minutes} min"
    return f"{hours} h {minutes} min" if minutes else f"{hours} h"


def format_value(value: float, outcome: str) -> str:
    # Liczba po polsku z jednostką: 21.4 -> "21 min", 0.63 -> "0,6 pkt", wybudzenia 1.43 -> "1,4".
    if outcome in MINUTE_OUTCOMES:
        return _format_minutes(value)
    number = f"{value:.1f}".replace(".", ",")
    return number if outcome == "awakenings" else f"{number} pkt"


def effect_fact(comparison: Comparison) -> Fact:
    # Zdanie z porównania z wynikiem "wniosek": kierunek ze znaku różnicy.
    more, less = OUTCOME_PHRASES[comparison.outcome]
    template = more if comparison.diff > 0 else less
    diff = format_value(abs(comparison.diff), comparison.outcome)
    text = f"{FACTOR_PHRASES[comparison.factor]} {template.format(diff=diff)}."
    values = {
        "diff": diff,
        "with": format_value(comparison.mean_with, comparison.outcome),
        "without": format_value(comparison.mean_without, comparison.outcome),
        "nights_with": str(comparison.n_with),
        "nights_without": str(comparison.n_without),
        "window": WINDOW_LABELS[comparison.window],
    }
    nights = comparison.n_with + comparison.n_without
    return Fact(f"effect.{comparison.factor}.{comparison.outcome}", "effect", text, values, nights)


def habit_rate_facts(rates: dict[str, dict[str, int]]) -> list[Fact]:
    # Tryb "start": jak często pojawia się nawyk („Kawa w ciągu 6 h przed snem: 2 z 4 wieczorów.”).
    facts = []
    for habit, counts in rates.items():
        if counts["yes"] == 0:
            continue
        evenings = "wieczoru" if counts["reported"] == 1 else "wieczorów"
        name = FACTORS[habit][0].upper() + FACTORS[habit][1:]
        text = f"{name}: {counts['yes']} z {counts['reported']} {evenings}."
        values = {"yes": str(counts["yes"]), "reported": str(counts["reported"]), "window": WINDOW_LABELS[SUMMARY_DAYS]}
        facts.append(Fact(f"habit_rate.{habit}", "habit_rate", text, values, counts["reported"]))
    return facts


def regularity_fact(regularity: dict) -> Fact | None:
    # Fakt o nieregularnym śnie tylko wtedy, gdy pora zaśnięcia „pływa” o więcej niż 60 min.
    std = regularity["onset_std_min"]
    if std is None or std <= IRREGULAR_ONSET_MIN:
        return None
    values = {"std": format_value(std, "duration"), "nights": str(regularity["nights"]), "window": WINDOW_LABELS[SUMMARY_DAYS]}
    text = f"Twoja pora zaśnięcia zmienia się z dnia na dzień zwykle o ok. {values['std']} (ostatnie 30 dni)."
    return Fact("regularity", "regularity", text, values, regularity["nights"])


START_NOTE = (
    "Masz jeszcze mało raportów, więc na razie pokazujemy głównie zalecenia ogólne. "
    "Osobiste wnioski pojawią się od 7 nocy z raportem."
)
BASIC_GUIDELINES = {"sleep_duration_age", "regular_schedule"}   # dla nowego konta bez dopasowań


@dataclass
class Card:
    # Karta nawyku: najsilniejszy wniosek i pozostałe wnioski tego samego czynnika (wariant C).
    factor: str
    fact: Fact
    also: list[Fact]


@dataclass
class Insights:
    # Wszystko, co pokazuje sekcja „Wnioski” na stronie Rekomendacje.
    level: str                  # "start" (< 7 nocy) albo "osobisty"
    nights: int                 # noce z raportem porannym w całej historii
    note: str | None            # wyjaśnienie dla trybu "start"
    cards: list[Card]           # najwyżej 3 karty (tylko tryb "osobisty")
    facts: list[Fact]           # częstości nawyków (tryb "start") i regularność
    guidelines: list[dict]      # sprawdzone zalecenia pasujące do użytkownika


def _cards(comparisons: list[Comparison]) -> list[Card]:
    # Karty z top_findings; do każdej dopisujemy pozostałe wnioski tego czynnika.
    findings = [c for c in comparisons if c.result == "wniosek"]
    cards = []
    for top in top_findings(comparisons):
        also = [effect_fact(c) for c in findings if c.factor == top.factor and c is not top]
        cards.append(Card(top.factor, effect_fact(top), also))
    return cards


def build_insights(frame: pd.DataFrame, today: date, age: int) -> Insights:
    # Sekcja „Wnioski”: tryb danych, karty, fakty i pasujące zalecenia.
    level = data_level(frame)
    rates = habit_rates(frame, today, SUMMARY_DAYS)
    regular = regularity(frame, today, SUMMARY_DAYS)

    if level == "start":
        cards, facts, note = [], habit_rate_facts(rates), START_NOTE
    else:
        cards, facts, note = _cards(compare_all(frame, today)), [], None
    irregular = regularity_fact(regular)
    if irregular:
        facts.append(irregular)

    situation = Situation(
        rates=rates,
        card_factors={card.factor for card in cards},
        mean_duration=summary(frame, today, SUMMARY_DAYS)["duration"],
        onset_std_min=regular["onset_std_min"],
        age=age,
    )
    guidelines = matching_guidelines(situation)
    if level == "start" and not guidelines:
        # Notka trybu start obiecuje zalecenia ogólne, więc nowe konto bez dopasowań dostaje podstawowe.
        guidelines = [g for g in load_guidelines() if g["id"] in BASIC_GUIDELINES]
    nights = int(frame["has_night"].sum())
    return Insights(level, nights, note, cards, facts, guidelines)


@dataclass
class HabitCell:
    # Jedna komórka tabeli wpływu nawyków: czynnik x wynik.
    outcome: str
    result: str                 # "wniosek", "brak_wniosku" albo "za_malo_danych"
    diff: str | None            # różnica ze znakiem, np. "+21 min"; None przy za małej liczbie nocy
    nights_with: int
    nights_without: int
    window: str                 # "ostatnie 30 dni", "ostatnie 90 dni" albo "cała historia"


@dataclass
class HabitRow:
    # Wiersz tabeli: jeden czynnik i jego porównania ze wszystkimi wynikami.
    factor: str
    label: str                  # opis czynnika z compare.FACTORS
    cells: list[HabitCell]


def _signed(diff: float, outcome: str) -> str:
    # Różnica ze znakiem do tabeli: 21.0 -> "+21 min", -1.1 -> "-1,1 pkt", -0.03 -> "0,0" (bez znaku).
    text = format_value(abs(diff), outcome)
    if not any(digit in text for digit in "123456789"):
        return text
    return ("+" if diff > 0 else "-") + text


def habits_table(frame: pd.DataFrame, today: date) -> list[HabitRow]:
    # Tabela wpływu nawyków: wszystkie porównania, także "brak_wniosku" i "za_malo_danych".
    rows = {factor: HabitRow(factor, label, []) for factor, label in FACTORS.items()}
    for comparison in compare_all(frame, today):
        diff = None if comparison.diff is None else _signed(comparison.diff, comparison.outcome)
        cell = HabitCell(
            comparison.outcome, comparison.result, diff,
            comparison.n_with, comparison.n_without, WINDOW_LABELS[comparison.window],
        )
        rows[comparison.factor].cells.append(cell)
    return list(rows.values())
