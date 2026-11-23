from dataclasses import dataclass
from pathlib import Path

import yaml

from .sleep_window import recommended_range

GUIDELINES_PATH = Path(__file__).with_name("guidelines.yaml")

# Nawyk -> (zalecenie, próg): pokazujemy, gdy nawyk był w co najmniej tej części wieczorów z raportem.
HABIT_GUIDELINES = {
    "coffee": ("caffeine_timing", 0.3),
    "alcohol": ("alcohol_evening", 0.2),
    "screens_high": ("screens_evening", 0.3),
    "nap_long": ("nap_length", 0.1),
    "stress_high": ("stress_evening", 0.3),
}
SHORT_SLEEP_FACTORS = {"short_sleep_6h", "short_sleep_7h"}
IRREGULAR_ONSET_MIN = 60    # rozrzut pory zaśnięcia powyżej 60 min = nieregularny sen


@dataclass
class Situation:
    # Co wiemy o użytkowniku z ostatnich 30 dni (wypełnia insights.py).
    rates: dict[str, dict[str, int]]    # z habit_rates: {"coffee": {"yes": 13, "reported": 27}, ...}
    card_factors: set[str]              # czynniki, które mają kartę z wnioskiem
    mean_duration: float | None         # średnia długość snu (min)
    onset_std_min: float | None         # rozrzut pory zaśnięcia (min)
    age: int


def load_guidelines(path: Path = GUIDELINES_PATH) -> list[dict]:
    # Zalecenia z pliku YAML, tylko sprawdzone przez autora (verified: true).
    with path.open(encoding="utf-8") as file:
        guidelines = yaml.safe_load(file)
    return [g for g in guidelines if g.get("verified") is True]


def _habit_rate(rates: dict[str, dict[str, int]], habit: str) -> float:
    # Część wieczorów z nawykiem; bez raportów wieczornych 0, a nie dzielenie przez zero.
    counts = rates[habit]
    return counts["yes"] / counts["reported"] if counts["reported"] else 0.0


def matching_ids(situation: Situation) -> set[str]:
    # Które zalecenia pasują do użytkownika: częsty nawyk albo karta z wnioskiem.
    ids = set()
    for habit, (guideline_id, threshold) in HABIT_GUIDELINES.items():
        if _habit_rate(situation.rates, habit) >= threshold or habit in situation.card_factors:
            ids.add(guideline_id)

    # Długość snu: średnia poza zakresem dla wieku albo karta o krótkim śnie.
    low, high = recommended_range(situation.age)
    outside_range = situation.mean_duration is not None and not low <= situation.mean_duration <= high
    if outside_range or situation.card_factors & SHORT_SLEEP_FACTORS:
        ids.add("sleep_duration_age")

    if situation.onset_std_min is not None and situation.onset_std_min > IRREGULAR_ONSET_MIN:
        ids.add("regular_schedule")
    return ids


def matching_guidelines(situation: Situation, path: Path = GUIDELINES_PATH) -> list[dict]:
    # Sprawdzone zalecenia, które pasują do użytkownika, w kolejności z pliku YAML.
    ids = matching_ids(situation)
    return [g for g in load_guidelines(path) if g["id"] in ids]
