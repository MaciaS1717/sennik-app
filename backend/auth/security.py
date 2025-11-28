from datetime import datetime, timedelta

from jose import jwt
from passlib.context import CryptContext

from ..config import get_settings

# Inicjalizacja kontekstu haszującego
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
settings = get_settings() # pobieramy ustawienia aplikacji

# hashowanie hasła
def hash_password(password: str) -> str:
    return pwd_context.hash(password)

# weryfikacja hasła
def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

# tworzenie tokenu JWT
def create_access_token(data: dict, expires_delta: timedelta | None = None) -> str: #wartosc domyslna delty none
    """
    data – np. {"sub": email_użytkownika}
    """
    to_encode = data.copy()
    #jesli nie podasz czasu waznosci, to ustawiamy domyslny czas z ustawien env
    if expires_delta is None:
        expires_delta = timedelta(minutes=settings.access_token_expire_minutes)
    # obliczamy czas wygaśnięcia tokenu
    expire = datetime.utcnow() + expires_delta
    to_encode.update({"exp": expire})
    #szyfrujemy token
    encoded_jwt = jwt.encode(
        to_encode,
        settings.jwt_secret,
        algorithm=settings.jwt_algorithm,
    )
    return encoded_jwt