from datetime import datetime

from pydantic import BaseModel, Field


class OrderItemIn(BaseModel):
    product_id: int = Field(gt=0)
    quantity: int = Field(gt=0)


class OrderCreate(BaseModel):
    items: list[OrderItemIn] = Field(min_length=1)


class TelegramOrderCreate(BaseModel):
    telegram_id: int = Field(gt=0)
    items: list[OrderItemIn] = Field(min_length=1)


class OrderItemOut(BaseModel):
    product_id: int
    quantity: int


class OrderOut(BaseModel):
    id: int
    user_id: int
    status: str
    items: list[OrderItemOut]


class OrderPageOut(BaseModel):
    items: list[OrderOut]
    total: int
    limit: int
    offset: int


class OrderStatusUpdateIn(BaseModel):
    status: str = Field(min_length=1, max_length=30)


class OrderItemAdminOut(BaseModel):
    product_id: int
    product_name: str
    unit_price: float
    quantity: int
    line_total: float
    image_url: str | None = None


class OrderAdminOut(BaseModel):
    id: int
    user_id: int
    user_email: str
    status: str
    created_at: datetime
    total: float
    items: list[OrderItemAdminOut]


class OrderAdminPageOut(BaseModel):
    items: list[OrderAdminOut]
    total: int
    limit: int
    offset: int
