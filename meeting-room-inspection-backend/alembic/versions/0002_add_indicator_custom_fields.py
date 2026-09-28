"""add indicator custom fields

Revision ID: 0002_add_indicator_custom_fields
Revises: 0001_init_core
Create Date: 2026-09-27
"""

from alembic import op
import sqlalchemy as sa


revision = "0002_add_indicator_custom_fields"
down_revision = "0001_init_core"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # 检查并添加字段以保证兼容性
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    columns = [c["name"] for c in inspector.get_columns("inspection_indicator")]

    if "photo_perspective" not in columns:
        op.add_column(
            "inspection_indicator",
            sa.Column("photo_perspective", sa.String(length=20), server_default="FRONT", nullable=False),
        )
    if "is_custom" not in columns:
        op.add_column(
            "inspection_indicator",
            sa.Column("is_custom", sa.Boolean(), server_default=sa.text("false"), nullable=False),
        )


def downgrade() -> None:
    op.drop_column("inspection_indicator", "is_custom")
    op.drop_column("inspection_indicator", "photo_perspective")
