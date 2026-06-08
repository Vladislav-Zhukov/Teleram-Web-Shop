from sqlalchemy import String, Integer, Numeric, Boolean
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base

class Product(Base):
    __tablename__ = "products"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(255), index=True)
    description: Mapped[str] = mapped_column(String(1000), default="")
    price: Mapped[float] = mapped_column(Numeric(12, 2))
    stock: Mapped[int] = mapped_column(Integer, default=0)
    in_stock: Mapped[bool] = mapped_column(Boolean, default=True)

    images = relationship("ProductImage", cascade="all, delete-orphan")

    def sync_flags(self) -> None:
        self.in_stock = self.stock > 0

    def primary_image_path(self) -> str | None:
        for img in getattr(self, "images", []) or []:
            if getattr(img, "is_primary", False):
                return img.path
        return None
