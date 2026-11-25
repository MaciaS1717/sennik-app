# Testy porównań grup (services/recommendations/compare.py).
from backend.services.recommendations.compare import (
    Comparison, bootstrap_ci, compare, data_level, habit_rates, top_findings,
)
import pandas as pd
from datetime import date, timedelta
from datetime import datetime
from backend.services.recommendations.frame import build_frame



# compare.bootstrap_ci, stałe ziarno: te same dane dają zawsze ten sam przedział.
def test_bootstrap_is_repeatable():
    with_factor = pd.Series([20, 25, 18, 22, 30, 24])
    without_factor = pd.Series([5, 8, 3, 10, 6, 4])

    assert bootstrap_ci(with_factor, without_factor) == bootstrap_ci(with_factor, without_factor)


# compare.bootstrap_ci: wyraźna różnica daje przedział bez zera, podobne grupy przedział z zerem.
def test_bootstrap_separates_effect_from_noise():
    low, high = bootstrap_ci(pd.Series([20, 25, 18, 22, 30, 24]), pd.Series([5, 8, 3, 10, 6, 4]))
    assert low > 0

    low, high = bootstrap_ci(pd.Series([10, 15, 5, 12, 8, 11]), pd.Series([11, 6, 14, 9, 12, 7]))
    assert low < 0 < high

TODAY = date(2026, 8, 1)

def _nights(days_ago: range, coffee: bool | None, latency_extra: float) -> list[dict]:
    # Noce testowe: data = TODAY - n dni, w każdej ta sama kawa i ten sam czas zasypiania.
    return [
        {"date": TODAY - timedelta(days=n), "coffee": coffee, "latency_extra": latency_extra}
        for n in days_ago
    ]


def _frame(*groups: list[dict]) -> pd.DataFrame:
    # Mała ramka z kolumnami jak w frame.py (kawa: tak / nie / NA).
    frame = pd.DataFrame([night for group in groups for night in group])
    frame["coffee"] = frame["coffee"].astype("boolean")
    return frame


# compare.compare, liczność: 4 noce z kawą to za mało nawet w całej historii (noce z NA się nie liczą).
def test_too_few_nights_gives_no_result():
    frame = _frame(
        _nights(range(0, 4), True, 20),
        _nights(range(4, 20), False, 5),
        _nights(range(20, 40), None, 20),
    )
    result = compare(frame, "coffee", "latency_extra", TODAY)

    assert result.result == "za_malo_danych"
    assert result.n_with == 4


# compare.compare: wyraźna różnica (15 min) przy 5 nocach w każdej grupie daje wniosek już w oknie 30 dni.
def test_clear_effect_gives_finding():
    frame = _frame(
        _nights(range(0, 10, 2), True, 20),
        _nights(range(1, 10, 2), False, 5),
    )
    result = compare(frame, "coffee", "latency_extra", TODAY)

    assert result.result == "wniosek"
    assert result.window == 30


# compare.compare, MID: różnica 3 min jest stała (przedział bez zera), ale mniejsza niż MID = 5 min.
def test_difference_below_mid_gives_no_finding():
    frame = _frame(
        _nights(range(0, 10, 2), True, 8),
        _nights(range(1, 10, 2), False, 5),
    )
    result = compare(frame, "coffee", "latency_extra", TODAY)

    assert result.result == "brak_wniosku"


# compare.compare, okno czasu: w 30 dniach są tylko 3 noce z kawą, więc porównanie bierze 90 dni.
def test_window_expands_to_90_days():
    frame = _frame(
        _nights(range(0, 3), True, 20),
        _nights(range(40, 45), True, 20),
        _nights(range(3, 30), False, 5),
    )
    result = compare(frame, "coffee", "latency_extra", TODAY)

    assert result.window == 90
    assert result.n_with == 8

def _morning(n: int) -> dict:
    # Sam raport poranny dnia TODAY - n (noc 23:00 -> 7:00), bez wieczoru D-1.
    day = TODAY - timedelta(days=n)
    return {
        "date": day,
        "sleep_start": datetime.combine(day - timedelta(days=1), datetime.min.time()).replace(hour=23),
        "sleep_end": datetime.combine(day, datetime.min.time()).replace(hour=7),
        "sleep_quality": 7, "morning_energy": 7, "sleep_duration": 7.5,
    }


# compare.data_level, próg 7 nocy: 6 nocy to jeszcze tryb "start", 7 nocy to "osobisty".
def test_data_level_threshold():
    six = build_frame([_morning(n) for n in range(6)], 15, TODAY)
    seven = build_frame([_morning(n) for n in range(7)], 15, TODAY)

    assert data_level(six) == "start"
    assert data_level(seven) == "osobisty"


# compare.habit_rates: dzień z samym raportem porannym nie liczy się jako wieczór „bez kawy”.
def test_habit_rates_skip_days_without_evening():
    rows = [_morning(n) for n in range(5)]
    rows[0].update(stress_level=5, coffee_last_6h=True)
    rows[1].update(stress_level=4, coffee_last_6h=False)
    rows[2].update(coffee_last_6h=False)   # stare dane: domyślne False bez raportu wieczornego
    frame = build_frame(rows, 15, TODAY)

    assert habit_rates(frame, TODAY, 30)["coffee"] == {"yes": 1, "reported": 2}

def _result(factor: str, outcome: str, diff: float, result: str = "wniosek") -> Comparison:
    # Gotowy wynik porównania (bez liczenia): do testów samego rankingu.
    return Comparison(factor, outcome, 30, 10, 20, None, None, diff, None, None, result)


# compare.top_findings: najpierw nawyki, jedna karta na czynnik, "brak_wniosku" nie trafia na karty.
def test_top_findings_order_and_one_card_per_factor():
    comparisons = [
        _result("is_weekend", "duration", 90),          # najsilniejszy, ale nie nawyk
        _result("alcohol", "quality", -2.0),
        _result("alcohol", "duration", -45),            # drugi wynik alkoholu
        _result("coffee", "latency_extra", 10),
        _result("screens_high", "quality", 3.0, "brak_wniosku"),
    ]
    top = top_findings(comparisons)

    assert [(c.factor, c.outcome) for c in top] == [
        ("alcohol", "quality"),
        ("coffee", "latency_extra"),
        ("is_weekend", "duration"),
    ]


