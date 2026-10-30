#obliczenia do panelu statystyk

from datetime import date
from typing import Optional, Sequence

from sqlmodel import Session, select

from ..models import DailyLog
from ..schemas.statistics import (
    StatisticsDailyPoint,
    StatisticsPeriod,
    StatisticsResponse,
    StatisticsSummary,
)

def _average(values: Sequence[Optional[float]]) -> Optional[float]:
    existing_values = [value for value in values if value is not None]
    if not existing_values:
        return None

    return round(sum(existing_values) / len(existing_values), 2)


def get_user_sleep_statistics(
    db: Session,
    user_id: int,
    date_from: date,
    date_to: date,
) -> StatisticsResponse:
    statement = (
        select(DailyLog)
        .where(
            DailyLog.user_id == user_id,
            DailyLog.date >= date_from,
            DailyLog.date <= date_to,
        )
        .order_by(DailyLog.date.asc())
    )

    logs = list(db.exec(statement).all())

    daily_points = []

    for log in logs:
        point = StatisticsDailyPoint(
            date=log.date,
            sleep_duration=log.sleep_duration,
            sleep_quality=log.sleep_quality,
            night_awakenings=log.night_awakenings,
            morning_energy=log.morning_energy,
            day_rating=log.day_rating,
            stress_level=log.stress_level,
        )

        daily_points.append(point)
    #liczymy za pomocą funkcji pomocniczej średnią dla każdego parametru w okresie czasu
    summary = StatisticsSummary(
        average_sleep_duration=_average([point.sleep_duration for point in daily_points]),
        average_sleep_quality=_average([point.sleep_quality for point in daily_points]),
        average_morning_energy=_average([point.morning_energy for point in daily_points]),
        average_night_awakenings=_average([point.night_awakenings for point in daily_points]),
        average_day_rating=_average([point.day_rating for point in daily_points]),
        average_stress_level=_average([point.stress_level for point in daily_points]),
    )

    return StatisticsResponse(
        period=StatisticsPeriod(
            date_from=date_from,
            date_to=date_to,
            report_count=len(logs),
        ),
        summary=summary,
        daily=daily_points,
    )