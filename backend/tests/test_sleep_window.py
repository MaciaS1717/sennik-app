# Testy kalkulatora snu (services/recommendations/sleep_window.py).
from backend.services.recommendations.frame import build_frame
from backend.services.recommendations.sleep_window import (
    calculate_sleep_window, duration_range, rate_options, sleep_options,
)
import pandas as pd
from datetime import date

def _nights(hours: float, energy: int, count: int) -> list[dict]:
    # `count` nocy o długości `hours` (+10 min, żeby trafić w środek przedziału) i energii `energy`.
    return [{"duration": hours * 60 + 10, "energy": energy}] * count


# sleep_window.duration_range: dobra energia tylko przy 5-6 h, więc po granicy 6 h zakres byłby pusty
# -> zakres z zaleceń i uwaga, a nie „6,0-6,0 h” z danych.
def test_only_very_short_sleep_good_falls_back_with_note():
    frame = pd.DataFrame(_nights(5.0, 8, 5) + _nights(5.5, 8, 5) + _nights(6.5, 5, 10))
    result = duration_range(frame, age=30)

    assert result.source == "zalecenia"
    assert (result.low, result.high) == (7 * 60, 9 * 60)
    assert result.note is not None


# sleep_window.duration_range na danych Anny z generatora: przedział 9 h z 1 nocą (energia 10)
# nie może wygrać; wychodzi 7-9 h jak w symulacji („Uproszczenia” 5.6).
def test_range_for_generated_user(healthy_user):
    frame = build_frame(healthy_user["rows"], healthy_user["typical_latency"], healthy_user["today"])
    result = duration_range(frame, age=30)

    assert (result.source, result.low, result.high) == ("dane", 7 * 60, 9 * 60)

# sleep_window.sleep_options: zakres 8,0-8,5 h nie zawiera pełnego cyklu (7,5 h / 9 h),
# więc zamiast pustej listy (kalkulator bez żadnej godziny) jest środek zakresu: 8 h 15 min.
def test_no_full_cycle_in_range_gives_middle():
    assert sleep_options(8 * 60, 8.5 * 60) == [495]


# sleep_window.rate_options na danych Piotra: po ok. 6 h snu (noce 5,75-6,25 h) energia jest wyraźnie
# niższa niż po 7,5 h, więc 6 h to "slabsza" i trafia na koniec listy.
def test_six_hours_rated_weaker_for_generated_user(coffee_user):
    frame = build_frame(coffee_user["rows"], coffee_user["typical_latency"], coffee_user["today"])
    result = rate_options(frame, [360, 450], "dane")

    assert [(o.duration, o.rating) for o in result] == [(450, "dobra"), (360, "slabsza")]

# Nowy użytkownik bez żadnych wpisów (ramka bez wierszy).
NEW_USER = build_frame([], 15, date(2026, 8, 1))

# sleep_window.calculate_sleep_window, przypadek z planu 5.4: brak danych, „zasypiam o 23:00”
# -> zakres 7-9 h, budzik po 7,5 h i 9 h (górna granica zakresu też się liczy), przejście przez północ.
def test_no_data_falls_asleep_at_23():
    result = calculate_sleep_window(NEW_USER, age=30, profile_latency=15, mode="wake_time", time="23:00")

    assert [plan.wake for plan in result.plans] == ["06:30", "08:00"]


# sleep_window.calculate_sleep_window, przypadek z planu 5.4: brak danych, zasypianie 15 min,
# „wstaję o 8:30” -> połóż się 00:45 (7,5 h) lub 23:15 (9 h), liczenie wstecz przez północ.
def test_no_data_wakes_at_8_30():
    result = calculate_sleep_window(NEW_USER, age=30, profile_latency=15, mode="bedtime", time="08:30")

    assert [plan.bedtime for plan in result.plans] == ["00:45", "23:15"]


# sleep_window: uwaga „o tej porze zwykle nie zasypiasz” liczona na osi od 12:00, więc 00:30
# u Piotra (zwykle zasypia ok. 00:40) to zwykła pora, a 20:00 już nie (pułapka: północ).
def test_unusual_onset_note_handles_midnight(coffee_user):
    frame = build_frame(coffee_user["rows"], coffee_user["typical_latency"], coffee_user["today"])
    after_midnight = calculate_sleep_window(frame, 30, 18, "wake_time", "00:30")
    evening = calculate_sleep_window(frame, 30, 18, "wake_time", "20:00")

    assert not any("zwykle nie zasypiasz" in note for note in after_midnight.notes)
    assert any("zwykle nie zasypiasz" in note for note in evening.notes)
