from dataclasses import asdict
from datetime import date
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlmodel import Session

from ..auth.auth_router import get_current_user
from ..database import get_session
from ..models import User
from ..schemas.recommendations import HabitsTableResponse, InsightsResponse, SleepWindowResponse
from ..services.recommendations.frame import load_frame
from ..services.recommendations.insights import build_insights, habits_table
from ..services.recommendations.sleep_window import calculate_sleep_window


router = APIRouter(prefix="/recommendations", tags=["recommendations"])


@router.get("", response_model=InsightsResponse)
def read_insights(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_session),
) -> InsightsResponse:
    frame = load_frame(db, current_user)
    insights = build_insights(frame, date.today(), current_user.age)
    return InsightsResponse(**asdict(insights))


@router.get("/habits", response_model=HabitsTableResponse)
def read_habits(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_session),
) -> HabitsTableResponse:
    frame = load_frame(db, current_user)
    rows = habits_table(frame, date.today())
    return HabitsTableResponse(rows=[asdict(row) for row in rows])


@router.get("/sleep-window", response_model=SleepWindowResponse)
def read_sleep_window(
    mode: Literal["wake_time", "bedtime", "best"] = Query(...),
    time: str | None = Query(None, pattern=r"^([01]\d|2[0-3]):[0-5]\d$"),
    time_type: Literal["falls_asleep", "goes_to_bed"] = Query("falls_asleep"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_session),
) -> SleepWindowResponse:
    if mode != "best" and time is None:
        raise HTTPException(
            status_code=422,
            detail="Podaj godzinę (HH:MM) w trybie wake_time i bedtime",
        )

    frame = load_frame(db, current_user)
    window = calculate_sleep_window(
        frame,
        current_user.age,
        current_user.typical_sleep_latency,
        mode,
        time,
        goes_to_bed=time_type == "goes_to_bed",
    )
    return SleepWindowResponse(**asdict(window))
