from __future__ import annotations

import json
import sys
from pathlib import Path

from sqlmodel import Session


# Dodaje główny katalog projektu do ścieżki importów Pythona.
PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


from backend.config import get_settings
from backend.crud.daily_logs import _compute_day_score, _compute_sleep_duration
from backend.crud.users import create_user, get_user_by_email
from backend.database import engine
from backend.models import DailyLog
from backend.models.daily_log import NapType, ScreensLastHour
from backend.schemas import UserCreate
from scripts.synthetic_data.generator import generate_history, validate_profile


# Lokalizacja profili JSON oraz środowiska, w których można bezpiecznie dodać dane.
PROFILES_DIR = Path(__file__).resolve().parent / "profiles"
ALLOWED_ENVIRONMENTS = {"dev", "development", "test", "local"}


def enum_or_none(enum_type, value):
    # Zamienia wartość tekstową na enum, pozostawiając brak danych jako None.
    if value is None:
        return None
    return enum_type(value)


def seed_profile(db: Session, path: Path) -> None:
    # Wczytanie i sprawdzenie poprawności profilu użytkownika.
    with path.open("r", encoding="utf-8") as file:
        profile = json.load(file)

    validate_profile(profile)

    account = profile["account"]
    email = account["email"]

    # Pomija profil, jeśli użytkownik o tym adresie już istnieje.
    if get_user_by_email(db, email):
        print(f"SKIP {path.name}: user {email} already exists")
        return

    # Utworzenie użytkownika na podstawie danych z profilu.
    user = create_user(
        db,
        UserCreate(
            email=email,
            password=account["password"],
            name=account["name"],
            gender=account["gender"],
            age=account["age"],
            typical_sleep_latency=account["typical_sleep_latency"],
        ),
    )

    count = 0

    # Generowanie kolejnych raportów i zamiana ich na modele bazy danych.
    for row in generate_history(profile):
        log = DailyLog(
            user_id=user.id,
            date=row["date"],
            sleep_start=row["sleep_start"],
            sleep_latency_extra=row["sleep_latency_extra"],
            sleep_end=row["sleep_end"],
            sleep_quality=row["sleep_quality"],
            night_awakenings=row["night_awakenings"],
            morning_energy=row["morning_energy"],
            day_rating=row["day_rating"],
            stress_level=row["stress_level"],
            coffee_last_6h=row["coffee_last_6h"],
            alcohol_last_4h=row["alcohol_last_4h"],
            screens_last_hour=enum_or_none(
                ScreensLastHour,
                row["screens_last_hour"],
            ),
            nap_type=enum_or_none(NapType, row["nap_type"]),
        )

        # Obliczenie pól, które normalnie wylicza logika backendu.
        log.sleep_duration = _compute_sleep_duration(user, log)
        log.day_score = _compute_day_score(log)

        db.add(log)
        count += 1

    # Zapisanie użytkownika i wszystkich jego raportów w bazie.
    db.commit()
    print(f"OK {path.name}: created user {email} and {count} daily logs")


def main() -> None:
    settings = get_settings()

    # Zabezpieczenie przed przypadkowym dodaniem danych do środowiska produkcyjnego.
    if settings.environment.lower() not in ALLOWED_ENVIRONMENTS:
        raise SystemExit(
            f"Refusing to seed data in environment={settings.environment!r}"
        )

    # Pobranie wszystkich profili JSON znajdujących się w katalogu profiles.
    profiles = sorted(PROFILES_DIR.glob("*.json"))
    if not profiles:
        print(f"No profiles found in {PROFILES_DIR}")
        return

    # Każdy profil jest przetwarzany osobno, aby błąd nie zatrzymał pozostałych.
    with Session(engine) as db:
        for path in profiles:
            try:
                seed_profile(db, path)
            except Exception as exc:
                db.rollback()
                print(f"ERROR {path.name}: {exc}")


# Uruchamia funkcję main tylko po bezpośrednim wywołaniu tego pliku.
if __name__ == "__main__":
    main()