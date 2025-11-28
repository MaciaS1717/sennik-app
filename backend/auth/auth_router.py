from datetime import timedelta

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jose import JWTError, jwt
from sqlmodel import Session

from ..config import get_settings
from ..database import get_session
from ..models import User
from ..schemas import UserCreate, UserRead
from ..crud import get_user_by_email, create_user, authenticate_user
from .security import create_access_token

router = APIRouter(prefix="/auth", tags=["auth"])

settings = get_settings()

# FastAPI będzie brało token z nagłówka Authorization: Bearer <token>
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")

#endpoint rejestracji użytkownika
@router.post(
    "/register",
    response_model=UserRead,
    status_code=status.HTTP_201_CREATED,
)
def register_user(data: UserCreate, db: Session = Depends(get_session)):
    existing = get_user_by_email(db, data.email)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Użytkownik z takim e-mailem już istnieje",
        )

    user = create_user(db, data.email, data.password)
    return user


#endpoint logowania użytkownika
@router.post("/login")
def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_session),
):
    # email jest w form_data.username
    user = authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Nieprawidłowy email lub hasło",
        )

    access_token_expires = timedelta(minutes=settings.access_token_expire_minutes)
    access_token = create_access_token(
        data={"sub": user.email},
        expires_delta=access_token_expires,
    )

    return {
        "access_token": access_token,
        "token_type": "bearer",
    }

# funkcja pobierająca aktualnego użytkownika na podstawie tokenu
def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_session),
) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Nie można uwierzytelnić użytkownika",
        headers={"WWW-Authenticate": "Bearer"},
    )
    # dekodowanie tokenu JWT
    try:
        payload = jwt.decode(
            token,
            settings.jwt_secret,
            algorithms=[settings.jwt_algorithm],
        )
        email: str | None = payload.get("sub")
        if email is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    user = get_user_by_email(db, email=email)
    if user is None:
        raise credentials_exception

    return user

@router.get("/me", response_model=UserRead)
def read_me(current_user: User = Depends(get_current_user)):
    return current_user
