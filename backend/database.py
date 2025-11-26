from sqlmodel import create_engine, Session
from .config import get_settings

settings = get_settings()

engine = create_engine(
    settings.database_url,
    echo=True,  # na początku przydatne, pokazuje SQL w konsoli
)

def get_session():
    with Session(engine) as session:
        yield session
