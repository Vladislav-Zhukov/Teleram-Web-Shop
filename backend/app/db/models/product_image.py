from sqlalchemy import String, Integer, Boolean, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class ProductImage(Base):
    __tablename__ = "product_images"

    id: Mapped[int] = mapped_column(primary_key=True)
    product_id: Mapped[int] = mapped_column(ForeignKey("products.id", ondelete="CASCADE"), index=True)
    path: Mapped[str] = mapped_column(String(500))  # relative path under MEDIA_DIR
    is_primary: Mapped[bool] = mapped_column(Boolean, default=False)

    product = relationship("Product")
