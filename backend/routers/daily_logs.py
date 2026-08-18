from fastapi import APIRouter, Depends, status, Query
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
    DailyLogUpdate
)
from ..crud import (
    create_or_update_morning_log,
    create_or_update_evening_log,
    get_user_daily_logs,
    get_user_daily_log_by_id,
    update_user_daily_log
)

router = APIRouter(prefix="/daily-logs", tags=["daily-logs"])

#odczytywanie
@router.get(
    "/",
    response_model=list[DailyLogRead],
)
def read_daily_logs_history(
    include_today: bool = True,
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_session),
) -> list[DailyLogRead]:
    """
    Zwraca historię wpisów aktualnie zalogowanego użytkownika.
    
    """
    logs = get_user_daily_logs(
        db=db,
        user_id=current_user.id,
        include_today=include_today,
        limit=limit,
        offset=offset,
    )
    return list(logs)


@router.get(
    "/{log_id}",
    response_model=DailyLogRead,
)
def read_daily_log_details(
    log_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_session),
) -> DailyLogRead:
    """
    Zwraca pojedynczy wpis dziennika po ID.
    Użytkownik może pobrać tylko własny wpis.
    """
    log = get_user_daily_log_by_id(db, current_user.id, log_id)
    if log is None:
        raise HttpException(status_code=404, detail="Nie znaleziono wpisu dziennika")

    return log


@router.patch(
    "/{log_id}",
    response_model=DailyLogRead,
)
def update_daily_log_details(
    log_id: int,
    payload: DailyLogUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_session),
) -> DailyLogRead:
    """
    Aktualizuje wybrany wpis dziennika.
    Można wysłać tylko część pól, np. samo morning_energy.
    """
    log = get_user_daily_log_by_id(db, current_user.id, log_id)
    if log is None:
        raise HttpException(status_code=404, detail="Nie znaleziono wpisu dziennika")

    try:
        updated_log = update_user_daily_log(db, current_user, log, payload)
    except ValueError as exc:
        raise HttpException(status_code=422, detail=str(exc))

    return updated_log


#zapisywanie
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
    try:
        log = create_or_update_morning_log(db, current_user, payload)
    except ValueError as exc:
        raise HttpException(status_code=422, detail=str(exc))

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
