# Wspólne dane do testów: historia osob z generatora (bez bazy), z czasem snu liczonym jak w aplikacji.

import json
from datetime import date
from pathlib import Path
from types import SimpleNamespace

import pytest

from backend.crud.daily_logs import _compute_sleep_duration
from scripts.synthetic_data.generator import generate_history


PROFILES_DIR = Path(__file__).resolve().parents[2] / "scripts" / "synthetic_data" / "profiles"


def load_test_user(file_name: str) -> dict:
    # Dane osob tak, jak trafiłyby do bazy, ale bez bazy.
    with (PROFILES_DIR / file_name).open("r", encoding="utf-8") as file:
        profile = json.load(file)

    user = SimpleNamespace(typical_sleep_latency=profile["account"]["typical_sleep_latency"])
    rows = generate_history(profile)

    # Generator nie liczy czasu snu; robimy to tą samą funkcją co seeder i API.
    for row in rows:
        row["sleep_duration"] = _compute_sleep_duration(user, SimpleNamespace(**row))

    return {
        "rows": rows,
        "typical_latency": user.typical_sleep_latency,
        # „Dziś” = ostatni dzień danych, żeby testy nie zależały od prawdziwej daty.
        "today": date.fromisoformat(profile["generation"]["date_to"]),
    }


@pytest.fixture(scope="session")
def healthy_user() -> dict:
    # Anna (healthy_regular.json): regularny sen, prawie codzienne raporty.
    return load_test_user("healthy_regular.json")