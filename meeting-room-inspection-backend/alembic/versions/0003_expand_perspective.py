"""expand indicator perspective length and update defaults

Revision ID: 0003_expand_perspective
Revises: 0002_add_indicator_custom_fields
Create Date: 2026-10-19
"""

from alembic import op
import sqlalchemy as sa


revision = "0003_expand_perspective"
down_revision = "0002_add_indicator_custom_fields"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # 1. Expand column length to 100 for multiple perspective support
    op.alter_column(
        "inspection_indicator",
        "photo_perspective",
        existing_type=sa.String(length=20),
        type_=sa.String(length=100),
        existing_nullable=False,
    )
    # 2. Update default built-in indicators
    op.execute("UPDATE inspection_indicator SET photo_perspective = 'FRONT,REAR' WHERE indicator_code = 'I001'")
    op.execute("UPDATE inspection_indicator SET photo_perspective = 'AC_PANEL' WHERE indicator_code = 'I002'")


def downgrade() -> None:
    op.alter_column(
        "inspection_indicator",
        "photo_perspective",
        existing_type=sa.String(length=100),
        type_=sa.String(length=20),
        existing_nullable=False,
    )
