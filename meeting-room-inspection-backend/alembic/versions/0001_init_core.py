"""init core meeting room inspection tables

Revision ID: 0001_init_core
Revises:
Create Date: 2026-09-19
"""

from alembic import op
import sqlalchemy as sa


revision = "0001_init_core"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "meeting_room",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column("room_code", sa.String(50), nullable=False),
        sa.Column("room_name", sa.String(100), nullable=False),
        sa.Column("building", sa.String(100)),
        sa.Column("floor", sa.String(50)),
        sa.Column("location_desc", sa.Text()),
        sa.Column("status", sa.String(20), nullable=False),
        sa.Column("inspection_enabled", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("room_code"),
    )
    op.create_index("ix_meeting_room_room_code", "meeting_room", ["room_code"])
    op.create_index("ix_meeting_room_status", "meeting_room", ["status"])
    op.create_index("ix_meeting_room_inspection_enabled", "meeting_room", ["inspection_enabled"])

    op.create_table(
        "inspection_indicator",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column("indicator_code", sa.String(50), nullable=False),
        sa.Column("indicator_name", sa.String(100), nullable=False),
        sa.Column("category", sa.String(100)),
        sa.Column("description", sa.Text()),
        sa.Column("normal_condition", sa.Text()),
        sa.Column("abnormal_condition", sa.Text()),
        sa.Column("ai_supported", sa.Boolean(), nullable=False),
        sa.Column("enabled", sa.Boolean(), nullable=False),
        sa.Column("sort_order", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("indicator_code"),
    )
    op.create_index("ix_inspection_indicator_indicator_code", "inspection_indicator", ["indicator_code"])
    op.create_index("ix_inspection_indicator_enabled", "inspection_indicator", ["enabled"])

    op.create_table(
        "inspection_period_config",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column("period_code", sa.String(20), nullable=False),
        sa.Column("period_name", sa.String(50), nullable=False),
        sa.Column("start_time", sa.Time(), nullable=False),
        sa.Column("deadline_time", sa.Time(), nullable=False),
        sa.Column("enabled", sa.Boolean(), nullable=False),
        sa.Column("reminder_enabled", sa.Boolean(), nullable=False),
        sa.Column("reminder_minutes", sa.Integer(), nullable=False),
        sa.Column("sort_order", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("period_code"),
    )
    op.create_index("ix_inspection_period_config_period_code", "inspection_period_config", ["period_code"])

    op.create_table(
        "standard_photo",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column("room_id", sa.BigInteger(), sa.ForeignKey("meeting_room.id"), nullable=False),
        sa.Column("photo_type", sa.String(20), nullable=False),
        sa.Column("photo_url", sa.String(500), nullable=False),
        sa.Column("photo_hash", sa.String(128)),
        sa.Column("shoot_position", sa.String(255)),
        sa.Column("camera_direction", sa.String(255)),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.Column("status", sa.String(20), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("room_id", "photo_type", "version", name="uq_standard_photo_version"),
    )
    op.create_index("ix_standard_photo_room_id", "standard_photo", ["room_id"])
    op.create_index("ix_standard_photo_status", "standard_photo", ["status"])

    op.create_table(
        "photo_region",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column("standard_photo_id", sa.BigInteger(), sa.ForeignKey("standard_photo.id"), nullable=False),
        sa.Column("region_code", sa.String(50), nullable=False),
        sa.Column("region_name", sa.String(100), nullable=False),
        sa.Column("x", sa.Numeric(8, 6), nullable=False),
        sa.Column("y", sa.Numeric(8, 6), nullable=False),
        sa.Column("width", sa.Numeric(8, 6), nullable=False),
        sa.Column("height", sa.Numeric(8, 6), nullable=False),
        sa.Column("description", sa.Text()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_photo_region_standard_photo_id", "photo_region", ["standard_photo_id"])

    op.create_table(
        "room_indicator",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column("room_id", sa.BigInteger(), sa.ForeignKey("meeting_room.id"), nullable=False),
        sa.Column("indicator_id", sa.BigInteger(), sa.ForeignKey("inspection_indicator.id"), nullable=False),
        sa.Column("standard_value", sa.Text()),
        sa.Column("region_id", sa.BigInteger(), sa.ForeignKey("photo_region.id")),
        sa.Column("enabled", sa.Boolean(), nullable=False),
        sa.Column("sort_order", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("room_id", "indicator_id", name="uq_room_indicator"),
    )
    op.create_index("ix_room_indicator_room_id", "room_indicator", ["room_id"])
    op.create_index("ix_room_indicator_indicator_id", "room_indicator", ["indicator_id"])
    op.create_index("ix_room_indicator_region_id", "room_indicator", ["region_id"])

    op.create_table(
        "inspection_task",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column("task_no", sa.String(100), nullable=False),
        sa.Column("room_id", sa.BigInteger(), sa.ForeignKey("meeting_room.id"), nullable=False),
        sa.Column("inspection_date", sa.Date(), nullable=False),
        sa.Column("period", sa.String(20), nullable=False),
        sa.Column("inspector_id", sa.String(100)),
        sa.Column("status", sa.String(30), nullable=False),
        sa.Column("due_at", sa.DateTime(timezone=True)),
        sa.Column("started_at", sa.DateTime(timezone=True)),
        sa.Column("completed_at", sa.DateTime(timezone=True)),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("task_no"),
        sa.UniqueConstraint("room_id", "inspection_date", "period", name="uq_inspection_task_room_date_period"),
    )
    op.create_index("ix_inspection_task_task_no", "inspection_task", ["task_no"])
    op.create_index("ix_inspection_task_room_id", "inspection_task", ["room_id"])
    op.create_index("ix_inspection_task_inspection_date", "inspection_task", ["inspection_date"])
    op.create_index("ix_inspection_task_period", "inspection_task", ["period"])
    op.create_index("ix_inspection_task_status", "inspection_task", ["status"])

    op.create_table(
        "inspection_photo",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column("task_id", sa.BigInteger(), sa.ForeignKey("inspection_task.id"), nullable=False),
        sa.Column("photo_type", sa.String(20), nullable=False),
        sa.Column("photo_url", sa.String(500), nullable=False),
        sa.Column("original_filename", sa.String(255)),
        sa.Column("width", sa.Integer()),
        sa.Column("height", sa.Integer()),
        sa.Column("file_size", sa.Integer()),
        sa.Column("quality_status", sa.String(20)),
        sa.Column("quality_reason", sa.String(500)),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("task_id", "photo_type", name="uq_inspection_photo_task_type"),
    )
    op.create_index("ix_inspection_photo_task_id", "inspection_photo", ["task_id"])

    op.create_table(
        "inspection_result",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column("task_id", sa.BigInteger(), sa.ForeignKey("inspection_task.id"), nullable=False),
        sa.Column("indicator_id", sa.BigInteger(), sa.ForeignKey("inspection_indicator.id"), nullable=False),
        sa.Column("ai_status", sa.String(30)),
        sa.Column("ai_confidence", sa.Numeric(5, 4)),
        sa.Column("ai_reason", sa.Text()),
        sa.Column("ai_bbox", sa.JSON()),
        sa.Column("human_status", sa.String(30)),
        sa.Column("human_remark", sa.Text()),
        sa.Column("final_status", sa.String(30)),
        sa.Column("confirmed_by", sa.String(100)),
        sa.Column("confirmed_at", sa.DateTime(timezone=True)),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("task_id", "indicator_id", name="uq_inspection_result_task_indicator"),
    )
    op.create_index("ix_inspection_result_task_id", "inspection_result", ["task_id"])
    op.create_index("ix_inspection_result_indicator_id", "inspection_result", ["indicator_id"])

    op.create_table(
        "ai_analysis_log",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column("task_id", sa.BigInteger(), sa.ForeignKey("inspection_task.id"), nullable=False),
        sa.Column("photo_id", sa.BigInteger(), sa.ForeignKey("inspection_photo.id")),
        sa.Column("model_name", sa.String(100)),
        sa.Column("model_version", sa.String(100)),
        sa.Column("prompt_version", sa.String(100)),
        sa.Column("request_json", sa.JSON()),
        sa.Column("response_json", sa.JSON()),
        sa.Column("latency_ms", sa.BigInteger()),
        sa.Column("token_usage", sa.JSON()),
        sa.Column("status", sa.String(30), nullable=False),
        sa.Column("error_message", sa.Text()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_ai_analysis_log_task_id", "ai_analysis_log", ["task_id"])
    op.create_index("ix_ai_analysis_log_photo_id", "ai_analysis_log", ["photo_id"])
    op.create_index("ix_ai_analysis_log_status", "ai_analysis_log", ["status"])


def downgrade() -> None:
    op.drop_table("ai_analysis_log")
    op.drop_table("inspection_result")
    op.drop_table("inspection_photo")
    op.drop_table("inspection_task")
    op.drop_table("room_indicator")
    op.drop_table("photo_region")
    op.drop_table("standard_photo")
    op.drop_table("inspection_period_config")
    op.drop_table("inspection_indicator")
    op.drop_table("meeting_room")
