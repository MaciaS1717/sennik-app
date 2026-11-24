from datetime import date, timedelta
from types import SimpleNamespace

from backend.models.user import Gender
from backend.services.recommendations.chat.handlers import (
    HANDLERS, build_fact_sheet, handle_habit_effect, handle_sleep_window, handle_summary,
)
from backend.services.recommendations.chat.intents import IntentResult
from backend.services.recommendations.frame import build_frame


# chat.handlers, pułapki, które wywracają czat (dane Piotra z generatora):
# - summary w okresie bez raportów: puste średnie (None) nie mogą trafić do format_value;
# - sleep_window bez godziny (LLM jej nie podał): przejście na tryb "best" zamiast błędu w _to_minutes(None).
def test_handlers_empty_period_and_missing_time(coffee_user):
    today = coffee_user["today"]
    frame = build_frame(coffee_user["rows"], coffee_user["typical_latency"], today)
    user = SimpleNamespace(age=37, typical_sleep_latency=coffee_user["typical_latency"], gender=Gender.male)

    empty = handle_summary(frame, user, IntentResult(intent="summary", period="week"), today + timedelta(days=60))
    assert empty.facts[0].text == "Ostatnie 7 dni: brak raportów."

    no_time = handle_sleep_window(frame, user, IntentResult(intent="sleep_window", mode="bedtime"), today)
    assert any(fact.id.startswith("sleep_window.plan") for fact in no_time.facts)
    assert "Nie podano godziny" in no_time.notes[0]


# chat.handlers.handle_habit_effect, pułapki (dane Piotra z generatora):
# - weekend nie jest nawykiem: bez częstości, ale z zaleceniem regular_schedule (inaczej KeyError);
# - pierwsze 20 dni: alkohol ma za mało nocy, więc zdanie „za mało nocy”, a nie wniosek z None;
# - LLM nie podał czynnika: ogólna rada zamiast błędu.
def test_habit_effect_weekend_few_nights_and_missing_habit(coffee_user):
    rows = sorted(coffee_user["rows"], key=lambda row: row["date"])
    user = SimpleNamespace(age=37, typical_sleep_latency=coffee_user["typical_latency"], gender=Gender.male)
    full = build_frame(rows, coffee_user["typical_latency"], coffee_user["today"])
    short_today = rows[19]["date"]
    short = build_frame(rows[:20], coffee_user["typical_latency"], short_today)

    weekend = handle_habit_effect(full, user, IntentResult(intent="habit_effect", habit="is_weekend"), coffee_user["today"])
    assert [g["id"] for g in weekend.guidelines] == ["regular_schedule"]

    alcohol = handle_habit_effect(short, user, IntentResult(intent="habit_effect", habit="alcohol"), short_today)
    assert [f.id for f in alcohol.facts if f.kind == "no_conclusion"] == ["too_few.alcohol"]

    no_habit = handle_habit_effect(full, user, IntentResult(intent="habit_effect"), coffee_user["today"])
    assert no_habit.intent == "advice"


# chat.handlers.build_fact_sheet, nowe konto bez żadnego raportu (pusta ramka):
# - żaden handler się nie wywraca (pandas na pustych danych);
# - advice ma zalecenia podstawowe, bo notka trybu start obiecuje zalecenia ogólne.
def test_fact_sheets_for_new_account():
    today = date(2026, 11, 24)
    frame = build_frame([], 15, today)
    user = SimpleNamespace(age=25, typical_sleep_latency=15, gender=Gender.female)

    for intent in HANDLERS:
        assert build_fact_sheet(frame, user, IntentResult(intent=intent), today).level == "start"

    advice = build_fact_sheet(frame, user, IntentResult(intent="advice"), today)
    assert [g["id"] for g in advice.guidelines] == ["sleep_duration_age", "regular_schedule"]
