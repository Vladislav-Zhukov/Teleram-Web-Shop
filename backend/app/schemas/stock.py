from pydantic import BaseModel, Field


class StockChangeIn(BaseModel):
    product_id: int = Field(gt=0)
    delta: int
