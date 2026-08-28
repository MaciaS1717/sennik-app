from datetime import date
from typing import Optional

from pydantic import BaseModel


class StatisticsPeriod(BaseModel):
    date_from: date
    date_to: date
    report_count: int


class StatisticsSummary(BaseModel):
    average_sleep_duration: Optional[float] = None
    average_sleep_quality: Optional[float] = None
    average_morning_energy: Optional[float] = None
    average_night_awakenings: Optional[float] = None
    average_day_rating: Optional[float] = None
    average_stress_level: Optional[float] = None


class StatisticsDailyPoint(BaseModel):
    date: date
    sleep_duration: Optional[float] = None
    sleep_quality: Optional[int] = None
    night_awakenings: Optional[int] = None
    morning_energy: Optional[int] = None
    day_rating: Optional[int] = None
    stress_level: Optional[int] = None


class StatisticsResponse(BaseModel):
    period: StatisticsPeriod
    summary: StatisticsSummary
    daily: list[StatisticsDailyPoint]