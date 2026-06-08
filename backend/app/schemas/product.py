from pydantic import BaseModel, Field

FROM_ATTRIBUTES_TRUE_ = {"from_attributes": True}


class ProductImageOut(BaseModel):
    id: int
    url: str
    is_primary: bool

    model_config = FROM_ATTRIBUTES_TRUE_


class ProductCreate(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    description: str = Field(default="", max_length=1000)
    price: float = Field(ge=0)
    stock: int = Field(default=0, ge=0)


class ProductUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=255)
    description: str | None = Field(default=None, max_length=1000)
    price: float | None = Field(default=None, ge=0)
    stock: int | None = Field(default=None, ge=0)
    in_stock: bool | None = None


class ProductOut(BaseModel):
    id: int
    name: str
    description: str
    price: float
    stock: int
    in_stock: bool
    primary_image_url: str | None = None
    images: list[ProductImageOut] = Field(default_factory=list)

    model_config = {"from_attributes": True}


class ProductPageOut(BaseModel):
    items: list[ProductOut]
    total: int
    limit: int
    offset: int
