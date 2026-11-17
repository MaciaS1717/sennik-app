import numpy as np
import pandas as pd
from datetime import date, timedelta

from dataclasses import dataclass
from typing import Literal

# Czynniki: kolumna w ramce -> opis dla człowieka.
FACTORS = {
    "coffee": "kawa w ciągu 6 h przed snem",
    "alcohol": "alkohol w ciągu 4 h przed snem",
    "screens_high": "dużo ekranów w ostatniej godzinie przed snem",
    "nap_long": "długa drzemka w ciągu dnia",
    "stress_high": "wysoki stres wieczorem (7 lub więcej)",
    "is_weekend": "noc przed sobotą lub niedzielą",
    "short_sleep_6h": "sen krótszy niż 6 h",
    "short_sleep_7h": "sen krótszy niż 7 h",
}

# Wyniki: kolumna w ramce -> opis dla człowieka.
OUTCOMES = {
    "latency_extra": "dodatkowy czas zasypiania (min)",
    "awakenings": "liczba wybudzeń w nocy",
    "quality": "jakość snu (1-10)",
    "duration": "długość snu (min)",
    "energy": "energia rano (1-10)",
    "day_rating": "ocena dnia (1-10)",
}

# MID: najmniejsza różnica, którą warto pokazać użytkownikowi (w jednostkach wyniku).
MID = {
    "latency_extra": 5,
    "awakenings": 0.5,
    "quality": 0.5,
    "duration": 15,
    "energy": 0.5,
    "day_rating": 0.5,
}

# Ustawienia metody porównań (plan v3, 4.2).
MIN_NIGHTS = 5              # najmniej nocy w każdej grupie
WINDOWS = (30, 90, "all")   # okna czasu sprawdzane po kolei
N_BOOT = 2000               # liczba losowań w bootstrapie
SEED = 42                   # stałe ziarno: ta sama historia -> ten sam wynik

# Nawyki z wieczoru D-1 (bez weekendu i krótkiego snu, które nie są nawykami).
HABITS = ["coffee", "alcohol", "screens_high", "nap_long", "stress_high"]
START_NIGHTS = 7            # od tylu nocy wnioski są osobiste
SHORT_SLEEP_OUTCOMES = ["energy", "day_rating"]   # krótki sen porównujemy tylko z samopoczuciem
MAX_FINDINGS = 3                                  # najwyżej 3 karty z wnioskami

@dataclass
class Comparison:
    # Wynik porównania: czy `outcome` jest inny w dni z czynnikiem `factor` i bez niego.
    factor: str
    outcome: str
    window: Literal[30, 90, "all"]
    n_with: int
    n_without: int
    mean_with: float | None      # None, gdy za mało danych
    mean_without: float | None
    diff: float | None           # mean_with - mean_without
    ci_low: float | None         # 95% przedział z bootstrapu
    ci_high: float | None
    result: Literal["wniosek", "brak_wniosku", "za_malo_danych"]

def bootstrap_ci(with_factor: pd.Series, without_factor: pd.Series) -> tuple[float, float]:
    # 95% przedział dla różnicy średnich (z czynnikiem - bez czynnika).
    rng = np.random.default_rng(SEED)
    # Losowanie ze zwracaniem: N_BOOT „nowych” prób tej samej wielkości co dane.
    means_with = rng.choice(with_factor.to_numpy(), size=(N_BOOT, len(with_factor))).mean(axis=1)
    means_without = rng.choice(without_factor.to_numpy(), size=(N_BOOT, len(without_factor))).mean(axis=1)
    differences = means_with - means_without
    # Środkowe 95% różnic: odcinamy po 2,5% z każdej strony.
    low, high = np.percentile(differences, [2.5, 97.5])
    return float(low), float(high)

def _last_days(frame: pd.DataFrame, today: date, days) -> pd.DataFrame:
    # Wiersze z ostatnich `days` dni (dziś + days-1 wstecz); "all" = cała historia.
    if days == "all":
        return frame
    return frame[frame["date"] > today - timedelta(days=days)]

def _groups(frame: pd.DataFrame, factor: str, outcome: str, today: date, window) -> tuple[pd.Series, pd.Series]:
    # Wartości wyniku w dni z czynnikiem i bez niego (tylko ostatnie `window` dni, chyba że "all").
    frame = _last_days(frame, today, window)
    # Liczymy tylko dni, w których znamy i czynnik, i wynik.
    known = frame[frame[factor].notna() & frame[outcome].notna()]
    has_factor = known[factor].astype(bool)
    return known.loc[has_factor, outcome], known.loc[~has_factor, outcome]


def compare(frame: pd.DataFrame, factor: str, outcome: str, today: date) -> Comparison:
    # Czy `outcome` jest inny w dni z czynnikiem `factor` niż bez niego?

    # 1. Okno czasu: najkrótsze, w którym obie grupy mają co najmniej MIN_NIGHTS nocy.
    for window in WINDOWS:
        with_factor, without_factor = _groups(frame, factor, outcome, today, window)
        enough = len(with_factor) >= MIN_NIGHTS and len(without_factor) >= MIN_NIGHTS
        if enough:
            break

    # 2. Za mało nocy nawet w całej historii: nie liczymy różnicy.
    if not enough:
        return Comparison(
            factor, outcome, window, len(with_factor), len(without_factor),
            None, None, None, None, None, "za_malo_danych",
        )

    # 3. Różnica średnich i 95% przedział z bootstrapu.
    mean_with = float(with_factor.mean())
    mean_without = float(without_factor.mean())
    diff = mean_with - mean_without
    ci_low, ci_high = bootstrap_ci(with_factor, without_factor)

    # 4. Wniosek tylko, gdy przedział nie zawiera zera i różnica jest co najmniej MID.
    ci_without_zero = ci_low > 0 or ci_high < 0
    is_finding = ci_without_zero and abs(diff) >= MID[outcome]

    return Comparison(
        factor, outcome, window, len(with_factor), len(without_factor),
        mean_with, mean_without, diff, ci_low, ci_high,
        "wniosek" if is_finding else "brak_wniosku",
    )

def data_level(frame: pd.DataFrame) -> str:
    # "start": za mało nocy na osobiste wnioski; "osobisty": od 7 nocy.
    nights = int(frame["has_night"].sum())
    return "start" if nights < START_NIGHTS else "osobisty"


def habit_rates(frame: pd.DataFrame, today: date, days) -> dict[str, dict[str, int]]:
    # Ile wieczorów z nawykiem na ile wieczorów z raportem („kawa w 3 z 4 wieczorów”).
    recent = _last_days(frame, today, days)
    rates = {}
    for habit in HABITS:
        known = recent[habit].dropna()
        rates[habit] = {"yes": int(known.sum()), "reported": len(known)}
    return rates


def regularity(frame: pd.DataFrame, today: date, days) -> dict:
    # Jak bardzo „pływa” pora zaśnięcia: odchylenie standardowe onset_min w minutach.
    onsets = _last_days(frame, today, days)["onset_min"].dropna()
    std = onsets.std() if len(onsets) >= 2 else None
    return {"nights": len(onsets), "onset_std_min": None if std is None else float(std)}

def compare_all(frame: pd.DataFrame, today: date) -> list[Comparison]:
    # Wszystkie pary czynnik -> wynik (krótki sen tylko z energią i oceną dnia).
    results = []
    for factor in FACTORS:
        for outcome in OUTCOMES:
            if factor.startswith("short_sleep") and outcome not in SHORT_SLEEP_OUTCOMES:
                continue
            results.append(compare(frame, factor, outcome, today))
    return results


def _rank_key(comparison: Comparison) -> tuple[bool, float]:
    # Najpierw nawyki (False < True), potem od najsilniejszego: |różnica| / MID malejąco.
    strength = abs(comparison.diff) / MID[comparison.outcome]
    return (comparison.factor not in HABITS, -strength)


def top_findings(comparisons: list[Comparison]) -> list[Comparison]:
    # Wnioski na karty: tylko "wniosek", najwyżej jedna karta na czynnik, najwyżej MAX_FINDINGS.
    findings = [c for c in comparisons if c.result == "wniosek"]

    # Oba progi krótkiego snu dla tego samego wyniku: zostaje tylko < 6 h
    outcomes_6h = {c.outcome for c in findings if c.factor == "short_sleep_6h"}
    findings = [
        c for c in findings
        if not (c.factor == "short_sleep_7h" and c.outcome in outcomes_6h)
    ]

    findings.sort(key=_rank_key)

    # Jedna karta na czynnik: jego najsilniejszy wynik (pozostałe zobaczy tabela nawyków).
    top = []
    used_factors = set()
    for comparison in findings:
        if comparison.factor not in used_factors:
            top.append(comparison)
            used_factors.add(comparison.factor)
    return top[:MAX_FINDINGS]
