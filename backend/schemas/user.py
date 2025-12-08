#walidacja user
from pydantic import BaseModel, EmailStr
from ..models.user import Gender


class UserCreate(BaseModel):
    email: EmailStr
    password: str
    name: str
    gender: Gender
    age: int
    typical_sleep_latency: int  # minuty

class UserRead(BaseModel):
    id: int
    email: EmailStr
    name: str
    gender: Gender
    age: int
    typical_sleep_latency: int  # minuty
    class Config:
        from_attributes = True