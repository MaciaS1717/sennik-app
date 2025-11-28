from fastapi import FastAPI
from .config import get_settings
from .database import engine
from sqlmodel import SQLModel
from .auth.auth_router import router as auth_router

settings = get_settings()

app = FastAPI(title="Sennik App API")

#dołączamy router auth
app.include_router(auth_router)

@app.get("/")
def read_root():
    return {"message": "Sennik API działa!", "environment": settings.environment}
