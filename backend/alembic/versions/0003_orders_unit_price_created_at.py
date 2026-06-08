"""add unit_price to order_items and created_at to orders

Revision ID: 0003_orders_unit_price_created_at
Revises: 0002_product_images
Create Date: 2026-02-21

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "0003_orders_unit_price"
down_revision = "0002_product_images"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # orders.created_at
    op.add_column(
        "orders",
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )

    # order_items.unit_price
    op.add_column(
        "order_items",
        sa.Column("unit_price", sa.Numeric(12, 2), nullable=True),
    )

    # backfill existing rows (if any) from current product price
    op.execute(
        """
        UPDATE order_items oi
        SET unit_price = p.price
        FROM products p
        WHERE oi.product_id = p.id AND oi.unit_price IS NULL
        """
    )

    op.alter_column("order_items", "unit_price", nullable=False)


def downgrade() -> None:
    op.drop_column("order_items", "unit_price")
    op.drop_column("orders", "created_at")
