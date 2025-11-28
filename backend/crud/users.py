from typing import Optional

from sqlmodel import Session, select

from ..models import User
from ..auth.security import hash_password, verify_password


def get_user_by_email(db: Session, email: str) -> Optional[User]: 
    #zwraca usera lub None
    statement = select(User).where(User.email == email)
    return db.exec(statement).first()


def create_user(db: Session, email: str, password: str) -> User: 
    #zwraca usera
    user = User(
        email=email,
        hashed_password=hash_password(password),
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def authenticate_user(db: Session, email: str, password: str) -> Optional[User]:
    #zwraca usera lub None jesli logowanie sie nie powiodlo
    user = get_user_by_email(db, email)
    if not user:
        return None
    if not verify_password(password, user.hashed_password):
        return None
    return user