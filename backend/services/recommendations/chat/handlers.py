from datetime import date

import pandas as pd

from ....models import User
from ..compare import (
    FACTORS, MID, MIN_NIGHTS, OUTCOMES, START_NIGHTS, compare, compare_all, data_level, habit_rates, summary,
    top_findings,
)
from ..guidelines import HABIT_GUIDELINES, load_guidelines
from ..insights import (
    SUMMARY_DAYS, WINDOW_LABELS, Fact, build_insights, effect_fact, format_value, habit_rate_facts,
)
from ..sleep_window import SleepWindow, calculate_sleep_window
from .intents import FactSheet, IntentResult

PERIOD_DAYS = {"week": 7, "month": 30}      # summary: bez okresu w pytaniu bierzemy tydzień

# Części zdania podsumowania; {} = gotowy napis z format_value.
SUMMARY_PARTS = {
    "duration": "średnio {} snu",
    "quality": "jakość snu {}",
    "energy": "energia rano {}",
    "awakenings": "{} wybudzenia na noc",
    "day_rating": "ocena dnia {}",
}
RANGE_SOURCES = {"dane": "z Twoich danych", "zalecenia": "z zaleceń dla Twojego wieku"}
LATENCY_SOURCES = {"dane": "z Twoich ostatnich nocy", "profil": "z profilu"}

# Nazwy wyników w narzędniku: „związek z czasem zasypiania”.
OUTCOME_NAMES = {
    "latency_extra": "czasem zasypiania",
    "awakenings": "liczbą wybudzeń",
    "quality": "jakością snu",
    "duration": "długością snu",
    "energy": "energią rano",
    "day_rating": "oceną dnia",
}
# Czynnik -> zalecenie; weekend (odsypianie) łączymy z zaleceniem o stałych porach snu.
FACTOR_GUIDELINES = {habit: guideline for habit, (guideline, _) in HABIT_GUIDELINES.items()}
FACTOR_GUIDELINES["is_weekend"] = "regular_schedule"
# advice: które wyniki dotyczą nocy, a które samopoczucia w dzień.
FOCUS_OUTCOMES = {
    "sleep": ["latency_extra", "awakenings", "quality", "duration"],
    "wellbeing": ["energy", "day_rating"],
}


def _sheet(intent: str, frame: pd.DataFrame, user: User, facts, guidelines=(), notes=()) -> FactSheet:
    # Wspólna część każdego FactSheet: poziom danych, liczba nocy, forma gramatyczna.
    nights = int(frame["has_night"].sum())
    return FactSheet(intent, data_level(frame), nights, user.gender.value, list(facts), list(guidelines), list(notes))


def _guidelines(*ids: str) -> list[dict]:
    # Sprawdzone zalecenia o podanych id.
    return [g for g in load_guidelines() if g["id"] in ids]


def summary_fact(stats: dict, days: int) -> Fact:
    # „Ostatnie 7 dni: średnio 6 h 23 min snu, jakość snu 5,1 pkt, … (noce z raportem: 7).”
    window = WINDOW_LABELS[days]
    values = {key: format_value(stats[key], key) for key in SUMMARY_PARTS if stats[key] is not None}
    parts = [SUMMARY_PARTS[key].format(values[key]) for key in SUMMARY_PARTS if key in values]
    values |= {"nights": str(stats["nights"]), "window": window}
    if parts:
        text = f"{window.capitalize()}: {', '.join(parts)} (noce z raportem: {stats['nights']})."
    else:
        text = f"{window.capitalize()}: brak raportów."
    return Fact(f"summary.{days}", "summary", text, values, stats["nights"])


def handle_summary(frame: pd.DataFrame, user: User, intent: IntentResult, today: date) -> FactSheet:
    days = PERIOD_DAYS[intent.period or "week"]
    return _sheet("summary", frame, user, [summary_fact(summary(frame, today, days), days)])


def sleep_window_facts(window: SleepWindow) -> list[Fact]:
    # Wynik kalkulatora jako fakty: zakres długości, czas zasypiania i plany z godzinami.
    duration_range = window.duration_range
    low = format_value(duration_range.low, "duration")
    high = format_value(duration_range.high, "duration")
    source = RANGE_SOURCES[duration_range.source]
    if duration_range.source == "dane":
        source += f", noce: {duration_range.nights}"
    latency = format_value(window.latency, "duration")
    facts = [
        Fact("sleep_window.range", "sleep_window", f"Długość snu do planu: {low} – {high} ({source}).",
             {"low": low, "high": high, "nights": str(duration_range.nights)}, duration_range.nights),
        Fact("sleep_window.latency", "sleep_window",
             f"Czas zasypiania: ok. {latency} ({LATENCY_SOURCES[window.latency_source]}).",
             {"latency": latency}, duration_range.nights),
    ]
    for number, plan in enumerate(window.plans, start=1):
        option = plan.option
        duration = format_value(option.duration, "duration")
        values = {"bedtime": plan.bedtime, "onset": plan.onset, "wake": plan.wake, "duration": duration}
        text = f"Położenie się o {plan.bedtime}, zaśnięcie ok. {plan.onset}, pobudka o {plan.wake}: {duration} snu."
        if option.rating == "slabsza":
            values["energy"] = format_value(option.mean_energy, "energy")
            text += f" Po podobnie długim śnie masz rano wyraźnie mniej energii (średnio {values['energy']})."
        facts.append(Fact(f"sleep_window.plan.{number}", "sleep_window", text, values, option.nights))
    return facts


def handle_sleep_window(frame: pd.DataFrame, user: User, intent: IntentResult, today: date) -> FactSheet:
    # Bez godziny (LLM jej nie znalazł) liczymy tryb "best" zamiast zwracać błąd.
    mode, time, notes = intent.mode, intent.time, []
    if mode is None or (mode != "best" and time is None):
        mode, time = "best", None
        notes.append("Nie podano godziny, więc pora zaśnięcia pochodzi z Twoich danych.")
    window = calculate_sleep_window(
        frame, user.age, user.typical_sleep_latency, mode, time,
        goes_to_bed=intent.time_type == "goes_to_bed",
    )
    facts = sleep_window_facts(window)
    return _sheet("sleep_window", frame, user, facts, _guidelines("sleep_cycles"), notes + window.notes)


def _factor_name(factor: str) -> str:
    # "kawa w ciągu 6 h przed snem" -> "Kawa w ciągu 6 h przed snem".
    return FACTORS[factor][0].upper() + FACTORS[factor][1:]


def grouped_facts(factor: str, comparisons: list) -> list[Fact]:
    # „Brak wniosku” i „za mało danych” zebrane w dwa zdania zamiast sześciu.
    # Bez liczb przy „brak wniosku”: różnica bez wniosku nie powinna trafić do odpowiedzi.
    facts = []
    no_link = [OUTCOME_NAMES[c.outcome] for c in comparisons if c.result == "brak_wniosku"]
    too_few = [OUTCOME_NAMES[c.outcome] for c in comparisons if c.result == "za_malo_danych"]
    if no_link:
        text = f"{_factor_name(factor)}: nie widać wyraźnego związku z: {', '.join(no_link)}."
        facts.append(Fact(f"no_conclusion.{factor}", "no_conclusion", text, {}, 0))
    if too_few:
        text = (
            f"{_factor_name(factor)}: za mało nocy, żeby ocenić związek z: {', '.join(too_few)} "
            f"(potrzeba co najmniej {MIN_NIGHTS} nocy z tym czynnikiem i {MIN_NIGHTS} bez niego)."
        )
        facts.append(Fact(f"too_few.{factor}", "no_conclusion", text, {"min_nights": str(MIN_NIGHTS)}, 0))
    return facts


def handle_habit_effect(frame: pd.DataFrame, user: User, intent: IntentResult, today: date) -> FactSheet:
    # Jeden czynnik i wszystkie wyniki: wnioski (od najsilniejszego), brak wniosku, za mało danych,
    # częstość nawyku z ostatnich 30 dni i zalecenie. Bez czynnika w pytaniu: ogólna rada.
    factor = intent.habit
    if factor is None:
        return handle_advice(frame, user, intent, today)
    comparisons = [compare(frame, factor, outcome, today) for outcome in OUTCOMES]
    findings = [c for c in comparisons if c.result == "wniosek"]
    findings.sort(key=lambda c: -abs(c.diff) / MID[c.outcome])
    facts = [effect_fact(c) for c in findings] + grouped_facts(factor, comparisons)
    if factor in HABIT_GUIDELINES:      # weekend nie jest nawykiem: nie ma częstości
        rates = habit_rates(frame, today, SUMMARY_DAYS)
        facts += habit_rate_facts({factor: rates[factor]})
    return _sheet("habit_effect", frame, user, facts, _guidelines(FACTOR_GUIDELINES[factor]))


def handle_advice(frame: pd.DataFrame, user: User, intent: IntentResult, today: date) -> FactSheet:
    # „Jak poprawić sen / samopoczucie?”: to samo co sekcja Wnioski, ale karty tylko dla wyników z pytania.
    insights = build_insights(frame, today, user.age)
    notes = [insights.note] if insights.note else []
    facts = list(insights.facts)        # tryb start: częstości nawyków; zawsze: regularność
    if insights.level == "osobisty":
        outcomes = FOCUS_OUTCOMES[intent.focus or "sleep"]
        findings = top_findings([c for c in compare_all(frame, today) if c.outcome in outcomes])
        facts = [effect_fact(c) for c in findings] + facts
        if not findings:
            notes.append("Twoje dane nie pokazują jeszcze wyraźnych związków dla tego pytania.")
    return _sheet("advice", frame, user, facts, insights.guidelines, notes)


# Stałe odpowiedzi o aplikacji dla general_knowledge (liczby ze stałych, żeby opis nie rozjechał się z kodem).
APP_FACTS = [
    Fact("app.day_score", "app",
         "DayScore to ocena całego dnia w skali 1–10: w 25% jakość snu, w 25% energia rano i w 50% ocena dnia.",
         {}, 0),
    Fact("app.sleep_duration", "app",
         "Czas snu liczymy od położenia się do pobudki, odejmując zwykły czas zasypiania z profilu "
         "i dodatkowy czas zasypiania z raportu porannego.",
         {}, 0),
    Fact("app.findings", "app",
         f"Wniosek z Twoich danych pokazujemy tylko wtedy, gdy w obu grupach jest co najmniej {MIN_NIGHTS} nocy, "
         "95% przedział z bootstrapu nie obejmuje zera, a różnica jest na tyle duża, żeby miała znaczenie "
         f"(np. co najmniej {format_value(MID['latency_extra'], 'latency_extra')} zasypiania "
         f"albo {format_value(MID['quality'], 'quality')} jakości snu). "
         "Najpierw sprawdzamy ostatnie 30 dni, potem 90, a potem całą historię.",
         {}, 0),
    Fact("app.levels", "app",
         f"Osobiste wnioski pojawiają się od {START_NIGHTS} nocy z raportem porannym; "
         "wcześniej opieramy się na zaleceniach ogólnych.",
         {}, 0),
]


def handle_general_knowledge(frame: pd.DataFrame, user: User, intent: IntentResult, today: date) -> FactSheet:
    # Ogólne pytania o sen i o aplikację: wszystkie sprawdzone zalecenia + opisy aplikacji; redaktor wybiera.
    return _sheet("general_knowledge", frame, user, APP_FACTS, load_guidelines())


# Intencja -> handler. off_topic ma stałą odpowiedź (templates.py), więc go tu nie ma.
HANDLERS = {
    "advice": handle_advice,
    "sleep_window": handle_sleep_window,
    "habit_effect": handle_habit_effect,
    "summary": handle_summary,
    "general_knowledge": handle_general_knowledge,
}


def build_fact_sheet(frame: pd.DataFrame, user: User, intent: IntentResult, today: date) -> FactSheet:
    # Jedyne wejście dla pipeline.py: wybiera handler według intencji.
    return HANDLERS[intent.intent](frame, user, intent, today)
