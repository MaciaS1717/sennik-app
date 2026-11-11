# Testy ramki analitycznej (services/recommendations/frame.py).
from datetime import date, datetime
from backend.services.recommendations.frame import build_frame
import pandas as pd


# frame.build_frame, filtr date <= today: wiersz z jutrzejszą datą (sam wieczór) odpada.
def test_future_row_is_dropped():
    today = date(2026, 8, 1)
    rows = [
        {"date": today, "day_rating": 7},
        {"date": date(2026, 8, 2), "stress_level": 4, "nap_type": "none"},
    ]
    frame = build_frame(rows, typical_latency=15, today=today)
    assert list(frame["date"]) == [today]


# frame.build_frame, dane z generatora: brak dat po "dziś", wiersze posortowane rosnąco.
def test_frame_from_generator_is_sorted_and_not_in_future(healthy_user):
    frame = build_frame(healthy_user["rows"], healthy_user["typical_latency"], healthy_user["today"])
    assert (frame["date"] <= healthy_user["today"]).all()
    assert frame["date"].is_monotonic_increasing


# frame.build_frame, odrzucanie pustych wierszy: wiersz z samym False kawy (bez stresu,
# ekranów i drzemki) jest pusty i odpada; wiersz z samymi nawykami zostaje.
def test_empty_row_is_dropped_but_habits_only_row_stays():
    today = date(2026, 8, 1)
    rows = [
        {"date": date(2026, 7, 31), "coffee_last_6h": False, "alcohol_last_4h": False},
        {"date": today, "stress_level": 5, "screens_last_hour": "low", "nap_type": "short"},
    ]
    frame = build_frame(rows, typical_latency=15, today=today)
    assert list(frame["date"]) == [today]


# frame.build_frame, bed_min / wake_min: przejście przez północ (jeden z testów "gotowe").
# 23:30 i 00:30 mają leżeć obok siebie na osi, a nie na dwóch końcach doby.
def test_bed_and_wake_minutes_cross_midnight():
    today = date(2026, 8, 1)
    night = {"sleep_quality": 7, "morning_energy": 6}
    rows = [
        {"date": date(2026, 7, 31), "sleep_start": datetime(2026, 7, 30, 23, 30),
         "sleep_end": datetime(2026, 7, 31, 7, 0), **night},
        {"date": today, "sleep_start": datetime(2026, 8, 1, 0, 30),
         "sleep_end": datetime(2026, 8, 1, 7, 0), **night},
    ]
    frame = build_frame(rows, typical_latency=15, today=today)
    assert list(frame["bed_min"]) == [690, 750]
    assert list(frame["wake_min"]) == [1140, 1140]


# frame.build_frame, czynniki wieczorne: pułapka domyślnego False (jeden z testów "gotowe").
# Wiersz z samym porankiem i False kawy/alkoholu w bazie ma mieć NA, a nie "bez kawy".
def test_default_false_without_evening_becomes_na():
    today = date(2026, 8, 1)
    rows = [
        {"date": today, "sleep_start": datetime(2026, 7, 31, 23, 0),
         "sleep_end": datetime(2026, 8, 1, 7, 0), "sleep_quality": 7, "morning_energy": 6,
         "coffee_last_6h": False, "alcohol_last_4h": False},
    ]
    frame = build_frame(rows, typical_latency=15, today=today)
    for factor in ["coffee", "alcohol", "screens_high", "nap_long", "stress_high"]:
        assert pd.isna(frame.loc[0, factor])


# frame.build_frame, kolumny wyników: wyniki nocy tylko przy pełnej nocy (domyślne 0
# w sleep_latency_extra bez nocy ma dać NA), day_rating niezależnie od nocy.
def test_outcomes_masked_without_night():
    today = date(2026, 8, 1)
    rows = [
        {"date": date(2026, 7, 31), "sleep_start": datetime(2026, 7, 30, 23, 0),
         "sleep_end": datetime(2026, 7, 31, 7, 0), "sleep_quality": 7, "morning_energy": 6,
         "sleep_latency_extra": 10, "night_awakenings": 2, "sleep_duration": 7.5},
        # bez nocy, z domyślnym 0 z bazy i z oceną dnia
        {"date": today, "sleep_latency_extra": 0, "day_rating": 8},
    ]
    frame = build_frame(rows, typical_latency=15, today=today)

    with_night, without_night = frame.iloc[0], frame.iloc[1]
    assert with_night["latency_extra"] == 10
    assert with_night["awakenings"] == 2
    assert with_night["quality"] == 7
    assert with_night["duration"] == 450
    assert with_night["energy"] == 6
    assert pd.isna(with_night["day_rating"])

    for outcome in ["latency_extra", "awakenings", "quality", "duration", "energy"]:
        assert pd.isna(without_night[outcome])
    assert without_night["day_rating"] == 8
