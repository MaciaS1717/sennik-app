from datetime import date

import pandas as pd

from sqlmodel import Session, select

from ...models import DailyLog, User

# Pola wpisu dziennego, z których korzysta ramka (nazwy jak w modelu DailyLog).
INPUT_COLUMNS = [
    "date",
    "sleep_start",
    "sleep_end",
    "sleep_latency_extra",
    "sleep_quality",
    "night_awakenings",
    "morning_energy",
    "sleep_duration",
    "day_rating",
    "stress_level",
    "coffee_last_6h",
    "alcohol_last_4h",
    "screens_last_hour",
    "nap_type",
]

def _minutes_from_noon_before(times: pd.Series, days: pd.Series) -> pd.Series:
    # Minuty od 12:00 dnia D-1: oś bez przeskoku o północy (23:30 -> 690, 07:00 -> 1140).
    noon_before = pd.to_datetime(days) - pd.Timedelta(hours=12)
    return (pd.to_datetime(times) - noon_before).dt.total_seconds() / 60

def _evening_factor(frame: pd.DataFrame, column: str, is_yes: pd.Series) -> pd.Series:
    # Czynnik z wieczoru D-1: True / False, a NA, gdy nie było raportu albo pole jest puste.
    known = frame["has_evening_before"] & frame[column].notna()
    return is_yes.astype("boolean").where(known)


def build_frame(rows: list[dict], typical_latency: int, today: date) -> pd.DataFrame:
    # Ramka analityczna: jeden wiersz = dzień D (noc D-1 -> D, wieczór D-1, ocena dnia D).
    frame = pd.DataFrame(rows, columns=INPUT_COLUMNS)

    # Wiersz z przyszłą datą jest niedokończony (np. jutrzejszy wpis z samymi nawykami).
    frame = frame[frame["date"] <= today]

    # Które części dnia D są wypełnione.
    frame["has_night"] = (
        frame[["sleep_start", "sleep_end", "sleep_quality", "morning_energy"]].notna().all(axis=1)
    )
    # Kawy i alkoholu nie sprawdzamy: same nie świadczą o raporcie wieczornym D-1.
    frame["has_evening_before"] = (
        frame[["stress_level", "screens_last_hour", "nap_type"]].notna().any(axis=1)
    )
    frame["has_day"] = frame["day_rating"].notna()

    # Wiersz bez nocy, bez wieczoru D-1 i bez oceny dnia nie wnosi nic do analizy.
    frame = frame[frame["has_night"] | frame["has_evening_before"] | frame["has_day"]]

    # Pora pójścia spać i pobudki na osi od 12:00 dnia D-1.
    frame["bed_min"] = _minutes_from_noon_before(frame["sleep_start"], frame["date"])
    frame["wake_min"] = _minutes_from_noon_before(frame["sleep_end"], frame["date"])

    # Czas zasypiania: typowy z profilu + dodatkowy z raportu porannego (tylko gdy jest noc).
    latency_extra = pd.to_numeric(frame["sleep_latency_extra"]).fillna(0)
    frame["latency_total"] = (typical_latency + latency_extra).where(frame["has_night"])
    # Szacowana chwila zaśnięcia na tej samej osi co bed_min.
    frame["onset_min"] = frame["bed_min"] + frame["latency_total"]
    # Długość snu z bazy (wzór tylko w crud), w minutach.
    frame["duration_min"] = pd.to_numeric(frame["sleep_duration"]) * 60
    # Noce pt -> sob i sob -> nd: dzień D to sobota (5) lub niedziela (6).
    frame["is_weekend"] = pd.to_datetime(frame["date"]).dt.day_of_week >= 5

    # Czynniki z wieczoru D-1 (logika D / D+1): tak / nie / NA.
    frame["coffee"] = _evening_factor(frame, "coffee_last_6h", frame["coffee_last_6h"].eq(True))
    frame["alcohol"] = _evening_factor(frame, "alcohol_last_4h", frame["alcohol_last_4h"].eq(True))
    frame["screens_high"] = _evening_factor(
        frame, "screens_last_hour", frame["screens_last_hour"].eq("high")
    )
    frame["nap_long"] = _evening_factor(frame, "nap_type", frame["nap_type"].eq("long"))
    frame["stress_high"] = _evening_factor(
        frame, "stress_level", pd.to_numeric(frame["stress_level"]) >= 7
    )

    # Krótki sen tej nocy (D-1 -> D): czynnik dla energii rano i oceny dnia D.
    known_duration = frame["duration_min"].notna()
    frame["short_sleep_6h"] = (frame["duration_min"] < 6 * 60).astype("boolean").where(known_duration)
    frame["short_sleep_7h"] = (frame["duration_min"] < 7 * 60).astype("boolean").where(known_duration)

    # Wyniki nocy (NA bez nocy, m.in. przez domyślne 0 w sleep_latency_extra) i ocena dnia D.
    night = frame["has_night"]
    frame["latency_extra"] = latency_extra.where(night)
    frame["awakenings"] = pd.to_numeric(frame["night_awakenings"]).where(night)
    frame["quality"] = pd.to_numeric(frame["sleep_quality"]).where(night)
    frame["duration"] = frame["duration_min"].where(night)
    frame["energy"] = pd.to_numeric(frame["morning_energy"]).where(night)
    frame["day_rating"] = pd.to_numeric(frame["day_rating"])


    return frame.sort_values("date").reset_index(drop=True)

def load_frame(db: Session, user: User, today: date | None = None) -> pd.DataFrame:
    # Jedyne miejsce modułu rekomendacji, które czyta bazę; reszta pracuje na ramce.
    logs = db.exec(select(DailyLog).where(DailyLog.user_id == user.id)).all()
    rows = [log.model_dump(include=set(INPUT_COLUMNS)) for log in logs]
    return build_frame(rows, user.typical_sleep_latency, today or date.today())
