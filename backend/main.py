from fastapi import FastAPI
from .config import get_settings
from .database import engine
from sqlmodel import SQLModel

settings = get_settings()

app = FastAPI(title="Sennik App API")

# Na później: tutaj zaimportujemy modele i zrobimy migracje Alembiciem,
# ale na start możemy zrobić automatyczne tworzenie tabel (tylko tymczasowo!).

@app.get("/")
def read_root():
    return {"message": "Sennik API działa!", "environment": settings.environment}
