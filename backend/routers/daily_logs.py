from fastapi import APIRouter, Depends, status
from sqlmodel import Session
from fastapi import HTTPException as HttpException

from ..auth.auth_router import get_current_user
from ..database import get_session
from ..models import User
from ..schemas import (
    DailyLogCreateMorning,
    DailyLogUpdateEvening,
    DailyLogRead,
    DailyLogEveningResponse,
)
from ..crud import (
    create_or_update_morning_log,
    create_or_update_evening_log,
)

router = APIRouter(prefix="/daily-logs", tags=["daily-logs"])

@router.post(
    "/morning",
    response_model=DailyLogRead,
    status_code=status.HTTP_201_CREATED,
)
def create_morning_daly_log(
    payload: DailyLogCreateMorning,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_session),
) -> DailyLogRead:
    """
    Tworzy lub aktualizuje poranny raport dla danego dnia.

    Jeśli log dla (user, date) już istnieje – nadpisujemy/uzupełniamy dane poranne.
    Jeśli nie istnieje – tworzymy nowy rekord.
    """
    # Sprawdzamy, czy czas w łóżku jest sensowny (0-18 godzin)
    deltaSleep = payload.sleep_end - payload.sleep_start
    if deltaSleep.total_seconds() < 0 or deltaSleep.total_seconds() > 18 * 3600:
        raise HttpException(status_code=422, detail="Czas w łóżku musi być między 0 a 18 godzin.")
    log = create_or_update_morning_log(db, current_user, payload)
    return log

@router.post(
    "/evening",
    response_model=DailyLogEveningResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_evening_daily_log(
    payload: DailyLogUpdateEvening,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_session),
) -> DailyLogEveningResponse:
    """
    Tworzy lub aktualizuje wieczorny raport dla danego dnia.

    Jeśli log dla (user, date) już istnieje – nadpisujemy/uzupełniamy dane wieczorne.
    Jeśli nie istnieje – tworzymy nowy rekord.
    """
    today_log, tomorrow_log = create_or_update_evening_log(db, current_user, payload)
    return DailyLogEveningResponse(today=today_log, tomorrow=tomorrow_log)