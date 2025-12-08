from fastapi import FastAPI
from .config import get_settings
from .database import engine
from sqlmodel import SQLModel
from .auth.auth_router import router as auth_router
from .routers.daily_logs import router as daily_logs_router

settings = get_settings()

app = FastAPI(title="Sennik App API")

#dołączamy routery
app.include_router(auth_router)
app.include_router(daily_logs_router)


@app.get("/")
def read_root():
    return {"message": "Sennik API działa!", "environment": settings.environment}
