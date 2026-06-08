from pydantic import BaseModel, EmailStr, Field


class UserOut(BaseModel):
    id: int
    email: EmailStr
    is_admin: bool
    telegram_id: int | None = None

    model_config = {"from_attributes": True}


class TelegramIdIn(BaseModel):
    telegram_id: int = Field(gt=0)


class TelegramBindByCodeIn(TelegramIdIn):
    code: str = Field(min_length=1)
