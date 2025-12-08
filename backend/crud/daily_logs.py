from datetime import date, datetime, timedelta
from typing import Optional, Tuple

from sqlmodel import Session, select

from ..models import DailyLog, User
from ..models.daily_log import NapType, ScreensLastHour
from ..schemas.daily_logs import DailyLogCreateMorning, DailyLogUpdateEvening

def _get_daily_log_for_date(db: Session, user_id: int, log__date: date) -> Optional[DailyLog]:
    statement= select(DailyLog).where(
        DailyLog.user_id == user_id,
        DailyLog.date == log__date,
    )
    return db.exec(statement).first()

def _get_or_create_daily_log(db: Session, user_id: int, log__date: date) -> DailyLog:
    log = _get_daily_log_for_date(db, user_id, log__date)
    if log is None:
        log = DailyLog(user_id=user_id, date=log__date)
        db.add(log)
        db.commit()
        db.refresh(log)
    return log

def _compute_sleep_duration(user: User, log: DailyLog) -> Optional[float]:
    if log.sleep_start is None or log.sleep_end is None:
        return None
    
    typical_latency = user.typical_sleep_latency
    extra_latency = log.sleep_latency_extra or 0
    latency_seconds = (typical_latency + extra_latency) * 60
    sleep_time_wit_latency = (log.sleep_end - log.sleep_start).total_seconds()
    total_sleep_time = sleep_time_wit_latency - latency_seconds
    if total_sleep_time < 0:
        return 0.0
    return round(total_sleep_time / 3600, 2)  # godziny z dwoma miejscami po przecinku

def _compute_day_score(log: DailyLog) -> Optional[float]:
    if log.sleep_quality is None or log.morning_energy is None or log.day_rating is None:
        return None
    score = (  #srednia ważona
        log.sleep_quality * 0.25 +
        log.morning_energy * 0.25 +
        log.day_rating * 0.5
    )
    return round(score, 2)

def create_or_update_morning_log(db: Session, user: User, payload: DailyLogCreateMorning) -> DailyLog:
    log= _get_or_create_daily_log(db, user.id, payload.date)

    log.sleep_start = payload.sleep_start
    log.sleep_latency_extra = payload.sleep_latency_extra
    log.sleep_end = payload.sleep_end
    log.sleep_quality = payload.sleep_quality
    log.night_awakenings = payload.night_awakenings
    log.morning_energy = payload.morning_energy

    log.sleep_duration = _compute_sleep_duration(user, log)
    log.day_score = _compute_day_score(log) #może być None jeśli brak danych
    log.updated_at = datetime.utcnow()
    db.add(log)
    db.commit()
    db.refresh(log)
    return log

def create_or_update_evening_log(db: Session, user: User, payload: DailyLogUpdateEvening) -> Tuple[DailyLog, DailyLog]:
    base_date= payload.date
    #dzien D
    today_log= _get_or_create_daily_log(db, user.id, base_date)
    if payload.day_rating is not None:
        today_log.day_rating = payload.day_rating
    today_log.day_score = _compute_day_score(today_log)
    today_log.updated_at = datetime.utcnow()

    #dzien D+1
    next_date= base_date + timedelta(days=1)
    tomorrow_log= _get_or_create_daily_log(db, user.id, next_date)
    if payload.stress_level is not None:
        tomorrow_log.stress_level = payload.stress_level
    if payload.coffee_last_6h is not None:
        tomorrow_log.coffee_last_6h = payload.coffee_last_6h
    if payload.alcohol_last_4h is not None:
        tomorrow_log.alcohol_last_4h = payload.alcohol_last_4h
    if payload.screens_last_hour is not None:
        tomorrow_log.screens_last_hour = ScreensLastHour(payload.screens_last_hour)
    if payload.nap_type is not None:
        tomorrow_log.nap_type = NapType(payload.nap_type)
    
    tomorrow_log.updated_at = datetime.utcnow()
    db.add(today_log)
    db.add(tomorrow_log)
    db.commit()
    db.refresh(today_log)
    db.refresh(tomorrow_log)
    return today_log, tomorrow_log