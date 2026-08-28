from __future__ import annotations

from datetime import date, datetime, time, timedelta
from random import Random
from typing import Any


Profile = dict[str, Any]
LogData = dict[str, Any]

# Stałe sterujące losowym przesunięciem godzin i weekendowym alkoholem.
RANDOM_TIME_SHIFT_MINUTES = 30
WEEKEND_ALCOHOL_BONUS = 0.05


def clamp_int(value: int, minimum: int, maximum: int) -> int:
    return max(minimum, min(maximum, value))


def parse_date(value: str) -> date:
    return date.fromisoformat(value)


def parse_time(value: str) -> time:
    hour, minute = value.split(":")
    return time(int(hour), int(minute))


def is_weekend(day: date) -> bool:
    return day.weekday() >= 5


def chance(rng: Random, probability: float) -> bool:
    return rng.random() < max(0.0, min(1.0, probability))


def weighted_choice(rng: Random, weights: dict[str, float]) -> str:
    # Losuje jedną wartość zgodnie z przypisanymi jej wagami.
    pick = rng.random() * sum(weights.values())
    current = 0.0

    for key, weight in weights.items():
        current += weight
        if pick <= current:
            return key

    return next(reversed(weights))


def active_period(profile: Profile, day: date) -> dict[str, Any] | None:
    # Zwraca okres specjalny obowiązujący danego dnia, jeśli taki istnieje.
    for period in profile.get("periods", []):
        if parse_date(period["from"]) <= day <= parse_date(period["to"]):
            return period
    return None


def validate_weights(name: str, weights: dict[str, float], expected_keys: set[str]) -> None:
    # Sprawdza komplet kluczy oraz poprawność sumy prawdopodobieństw.
    if set(weights) != expected_keys:
        raise ValueError(f"{name} must contain exactly: {sorted(expected_keys)}")

    total = sum(weights.values())
    if abs(total - 1.0) > 0.01:
        raise ValueError(f"{name} probabilities must sum to 1.0")

    for key, value in weights.items():
        if not 0 <= value <= 1:
            raise ValueError(f"{name}.{key} must be between 0 and 1")


def validate_probability(name: str, value: float) -> None:
    if not 0 <= value <= 1:
        raise ValueError(f"{name} must be between 0 and 1")


def validate_profile(profile: Profile) -> None:
    # Sprawdza, czy profil zawiera wszystkie wymagane sekcje i pola.
    for section in ["account", "generation", "baseline", "habits", "weekend"]:
        if section not in profile:
            raise ValueError(f"Missing section: {section}")

    account = profile["account"]
    for field in ["email", "password", "name", "gender", "age", "typical_sleep_latency"]:
        if field not in account:
            raise ValueError(f"Missing account.{field}")

    if account["gender"] not in {"male", "female"}:
        raise ValueError("account.gender must be male or female")

    generation = profile["generation"]
    date_from = parse_date(generation["date_from"])
    date_to = parse_date(generation["date_to"])

    if date_from > date_to:
        raise ValueError("generation.date_from must be before or equal generation.date_to")

    validate_probability("generation.morning_report_probability", generation["morning_report_probability"])
    validate_probability("generation.evening_report_probability", generation["evening_report_probability"])

    parse_time(profile["baseline"]["sleep_start"])
    parse_time(profile["baseline"]["sleep_end"])

    habits = profile["habits"]
    validate_probability("habits.coffee_last_6h_probability", habits["coffee_last_6h_probability"])
    validate_probability("habits.alcohol_last_4h_probability", habits["alcohol_last_4h_probability"])
    validate_weights("habits.screens_last_hour", habits["screens_last_hour"], {"low", "medium", "high"})
    validate_weights("habits.nap_type", habits["nap_type"], {"none", "short", "medium", "long"})

    # Okresy specjalne nie mogą mieć błędnych dat ani nachodzić na siebie.
    periods = []
    for period in profile.get("periods", []):
        start = parse_date(period["from"])
        end = parse_date(period["to"])

        if start > end:
            raise ValueError(f"Period {period['name']}: from must be before or equal to")

        for existing_start, existing_end, existing_name in periods:
            if start <= existing_end and existing_start <= end:
                raise ValueError(f"Periods overlap: {existing_name} and {period['name']}")

        periods.append((start, end, period["name"]))


def sleep_datetime(log_date: date, value: str, shift_minutes: int, rng: Random, is_start: bool) -> datetime:
    clock = parse_time(value)

    # Godzina rozpoczęcia snu wieczorem należy do poprzedniego dnia.
    if is_start and clock.hour >= 12:
        base_date = log_date - timedelta(days=1)
    else:
        base_date = log_date

    random_shift = rng.randint(-RANDOM_TIME_SHIFT_MINUTES, RANDOM_TIME_SHIFT_MINUTES)
    return datetime.combine(base_date, clock) + timedelta(minutes=shift_minutes + random_shift)


def rough_sleep_duration(profile: Profile, sleep_start: datetime, sleep_end: datetime, latency_extra: int) -> float:
    # Od czasu w łóżku odejmuje typowy i dodatkowy czas zasypiania.
    latency = profile["account"]["typical_sleep_latency"] + latency_extra
    seconds = (sleep_end - sleep_start).total_seconds() - latency * 60
    return max(0.0, round(seconds / 3600, 2))


def generate_morning(day: date, profile: Profile, previous_evening: LogData, rng: Random) -> LogData:
    baseline = profile["baseline"]
    period = active_period(profile, day)

    # Weekend i okres specjalny modyfikują bazowe godziny oraz jakość snu.
    start_shift = 0
    end_shift = 0
    quality_modifier = 0

    if is_weekend(day):
        start_shift += profile["weekend"]["sleep_start_shift_minutes"]
        end_shift += profile["weekend"]["sleep_end_shift_minutes"]

    if period:
        start_shift += period.get("sleep_start_shift_minutes", 0)
        end_shift += period.get("sleep_end_shift_minutes", 0)
        quality_modifier += period.get("sleep_quality_modifier", 0)

    # Wyznaczenie rzeczywistych godzin snu z niewielkim losowym przesunięciem.
    sleep_start = sleep_datetime(day, baseline["sleep_start"], start_shift, rng, is_start=True)
    sleep_end = sleep_datetime(day, baseline["sleep_end"], end_shift, rng, is_start=False)

    if sleep_end <= sleep_start:
        sleep_end += timedelta(days=1)

    if sleep_end - sleep_start > timedelta(hours=18):
        sleep_start = sleep_end - timedelta(hours=18)

    # Wieczorne nawyki mogą wydłużyć zasypianie.
    latency_extra = rng.randint(0, 10)

    if previous_evening["coffee_last_6h"]:
        latency_extra += rng.randint(10, 25)
    if previous_evening["screens_last_hour"] == "high":
        latency_extra += rng.randint(5, 12)
    if previous_evening["stress_level"] >= 8:
        latency_extra += rng.randint(10, 20)
    if previous_evening["nap_type"] == "long":
        latency_extra += rng.randint(8, 18)

    latency_extra = clamp_int(latency_extra, 0, 180)

    sleep_duration = rough_sleep_duration(profile, sleep_start, sleep_end, latency_extra)

    # Alkohol i wysoki stres zwiększają liczbę nocnych wybudzeń.
    night_awakenings = baseline["night_awakenings"] + rng.choice([-1, 0, 1])
    if previous_evening["alcohol_last_4h"]:
        night_awakenings += 1
    if previous_evening["stress_level"] >= 8:
        night_awakenings += 1
    night_awakenings = clamp_int(night_awakenings, 0, 10)

    # Jakość snu zależy od jego długości, stresu, alkoholu i wybudzeń.
    sleep_quality = baseline["sleep_quality"] + quality_modifier + rng.choice([-1, 0, 1])
    if sleep_duration < 6:
        sleep_quality -= 1
    if previous_evening["stress_level"] >= 8:
        sleep_quality -= 1
    if previous_evening["alcohol_last_4h"]:
        sleep_quality -= 1
    if night_awakenings >= 3:
        sleep_quality -= 1
    sleep_quality = clamp_int(sleep_quality, 1, 10)

    # Poranna energia wynika głównie z długości i jakości snu.
    morning_energy = baseline["morning_energy"] + rng.choice([-1, 0, 1])
    if sleep_quality <= 4:
        morning_energy -= 1
    if sleep_duration < 6:
        morning_energy -= 1
    if sleep_quality >= 8 and sleep_duration >= 7:
        morning_energy += 1
    morning_energy = clamp_int(morning_energy, 1, 10)

    return {
        "sleep_start": sleep_start,
        "sleep_latency_extra": latency_extra,
        "sleep_end": sleep_end,
        "sleep_quality": sleep_quality,
        "night_awakenings": night_awakenings,
        "morning_energy": morning_energy,
    }


def generate_evening(day: date, profile: Profile, morning: LogData, rng: Random) -> LogData:
    baseline = profile["baseline"]
    habits = profile["habits"]
    period = active_period(profile, day)

    # Poziom stresu uwzględnia weekend, okres specjalny i losową zmianę.
    stress = baseline["stress_level"]
    if is_weekend(day):
        stress += profile["weekend"]["stress_modifier"]
    if period:
        stress += period.get("stress_modifier", 0)
    stress += rng.choice([-1, 0, 1])
    stress = clamp_int(stress, 1, 10)

    # W weekend prawdopodobieństwo alkoholu jest nieco większe.
    alcohol_probability = habits["alcohol_last_4h_probability"]
    if is_weekend(day):
        alcohol_probability += WEEKEND_ALCOHOL_BONUS

    # Ocena dnia zależy od stresu oraz porannej energii.
    day_rating = baseline["day_rating"] + rng.choice([-1, 0, 1])
    if stress >= 8:
        day_rating -= 1
    if morning["morning_energy"] <= 4:
        day_rating -= 1
    if stress <= 3 and morning["morning_energy"] >= 7:
        day_rating += 1
    day_rating = clamp_int(day_rating, 1, 10)

    return {
        "day_rating": day_rating,
        "stress_level": stress,
        "coffee_last_6h": chance(rng, habits["coffee_last_6h_probability"]),
        "alcohol_last_4h": chance(rng, alcohol_probability),
        "screens_last_hour": weighted_choice(rng, habits["screens_last_hour"]),
        "nap_type": weighted_choice(rng, habits["nap_type"]),
    }


def generate_history(profile: Profile) -> list[LogData]:
    validate_profile(profile)

    # Stały seed pozwala za każdym razem wygenerować te same dane.
    generation = profile["generation"]
    rng = Random(generation["seed"])

    current_date = parse_date(generation["date_from"])
    date_to = parse_date(generation["date_to"])

    # Wartości początkowe potrzebne do wygenerowania pierwszego poranka.
    previous_evening = {
        "stress_level": profile["baseline"]["stress_level"],
        "coffee_last_6h": False,
        "alcohol_last_4h": False,
        "screens_last_hour": "medium",
        "nap_type": "none",
    }

    rows = []

    # Generowanie kolejnych dni z wybranego przedziału.
    while current_date <= date_to:
        morning = generate_morning(current_date, profile, previous_evening, rng)
        evening = generate_evening(current_date, profile, morning, rng)

        # Losowanie, czy użytkownik wypełnił raport poranny i wieczorny.
        has_morning = chance(rng, generation["morning_report_probability"])
        has_evening = chance(rng, generation["evening_report_probability"])

        # Dzień jest zapisywany, jeśli istnieje przynajmniej jeden raport.
        if has_morning or has_evening:
            row = {"date": current_date}

            for field in [
                "sleep_start",
                "sleep_latency_extra",
                "sleep_end",
                "sleep_quality",
                "night_awakenings",
                "morning_energy",
            ]:
                row[field] = morning[field] if has_morning else None

            for field in [
                "day_rating",
                "stress_level",
                "coffee_last_6h",
                "alcohol_last_4h",
                "screens_last_hour",
                "nap_type",
            ]:
                row[field] = evening[field] if has_evening else None

            rows.append(row)

        # Dzisiejszy wieczór wpływa na dane snu następnego dnia.
        previous_evening = evening
        current_date += timedelta(days=1)

    return rows
