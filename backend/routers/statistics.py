from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlmodel import Session

from ..auth.auth_router import get_current_user
from ..database import get_session
from ..models import User
from ..schemas.statistics import StatisticsResponse
from ..services.statistics_service import get_user_sleep_statistics


router = APIRouter(prefix="/statistics", tags=["statistics"])


@router.get("", response_model=StatisticsResponse)
def read_statistics(
    date_from: date = Query(...),
    date_to: date = Query(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_session),
) -> StatisticsResponse:
    if date_from > date_to:
        raise HTTPException(
            status_code=422,
            detail="date_from nie może być późniejsze niż date_to",
        )

    return get_user_sleep_statistics(
        db=db,
        user_id=current_user.id,
        date_from=date_from,
        date_to=date_to,
    )