"""add scheduler runtime tables

Revision ID: 002
Revises: 001
Create Date: 2026-05-05
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "002"
down_revision: Union[str, None] = "001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "scheduler_runs",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("scheduler_run_id", sa.String(length=120), nullable=False),
        sa.Column("plan_id", sa.Integer(), nullable=False),
        sa.Column("plan_item_id", sa.Integer(), nullable=False),
        sa.Column("parent_run_id", sa.String(length=120), nullable=True),
        sa.Column("run_kind", sa.String(length=50), nullable=False),
        sa.Column("state", sa.String(length=50), nullable=True),
        sa.Column("merge_strategy", sa.String(length=100), nullable=True),
        sa.Column("merge_status", sa.String(length=100), nullable=True),
        sa.Column("merged_output", sa.Text(), nullable=True),
        sa.Column("policy", sa.JSON(), nullable=True),
        sa.Column("metadata", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=True),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=True),
        sa.Column("last_merge_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["plan_id"], ["plan_runs.id"]),
        sa.ForeignKeyConstraint(["plan_item_id"], ["plan_items.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_scheduler_runs_id"), "scheduler_runs", ["id"], unique=False)
    op.create_index(op.f("ix_scheduler_runs_plan_id"), "scheduler_runs", ["plan_id"], unique=False)
    op.create_index(op.f("ix_scheduler_runs_plan_item_id"), "scheduler_runs", ["plan_item_id"], unique=False)
    op.create_index(op.f("ix_scheduler_runs_scheduler_run_id"), "scheduler_runs", ["scheduler_run_id"], unique=True)

    op.create_table(
        "child_runs",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("child_run_id", sa.String(length=120), nullable=False),
        sa.Column("child_execution_id", sa.String(length=120), nullable=False),
        sa.Column("scheduler_run_ref_id", sa.Integer(), nullable=True),
        sa.Column("scheduler_run_id", sa.String(length=120), nullable=True),
        sa.Column("plan_id", sa.Integer(), nullable=False),
        sa.Column("plan_item_id", sa.Integer(), nullable=False),
        sa.Column("parent_run_id", sa.String(length=120), nullable=True),
        sa.Column("run_id", sa.String(length=120), nullable=False),
        sa.Column("run_kind", sa.String(length=50), nullable=False),
        sa.Column("agent_role", sa.String(length=100), nullable=True),
        sa.Column("agent_id", sa.String(length=120), nullable=True),
        sa.Column("status", sa.String(length=50), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=True),
        sa.Column("summary", sa.Text(), nullable=True),
        sa.Column("error", sa.Text(), nullable=True),
        sa.Column("error_kind", sa.String(length=100), nullable=True),
        sa.Column("retry_count", sa.Integer(), nullable=False),
        sa.Column("model_name", sa.String(length=120), nullable=True),
        sa.Column("provider_name", sa.String(length=120), nullable=True),
        sa.Column("provider_order", sa.JSON(), nullable=True),
        sa.Column("provider_switch_count", sa.Integer(), nullable=False),
        sa.Column("provider_history", sa.JSON(), nullable=True),
        sa.Column("metadata", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=True),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=True),
        sa.Column("started_at", sa.DateTime(), nullable=True),
        sa.Column("completed_at", sa.DateTime(), nullable=True),
        sa.Column("cancelled_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["plan_id"], ["plan_runs.id"]),
        sa.ForeignKeyConstraint(["plan_item_id"], ["plan_items.id"]),
        sa.ForeignKeyConstraint(["scheduler_run_ref_id"], ["scheduler_runs.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("plan_item_id", "child_execution_id", name="uq_child_runs_item_execution"),
    )
    op.create_index(op.f("ix_child_runs_child_execution_id"), "child_runs", ["child_execution_id"], unique=False)
    op.create_index(op.f("ix_child_runs_child_run_id"), "child_runs", ["child_run_id"], unique=True)
    op.create_index(op.f("ix_child_runs_id"), "child_runs", ["id"], unique=False)
    op.create_index(op.f("ix_child_runs_plan_id"), "child_runs", ["plan_id"], unique=False)
    op.create_index(op.f("ix_child_runs_plan_item_id"), "child_runs", ["plan_item_id"], unique=False)
    op.create_index(op.f("ix_child_runs_run_id"), "child_runs", ["run_id"], unique=False)
    op.create_index(op.f("ix_child_runs_scheduler_run_id"), "child_runs", ["scheduler_run_id"], unique=False)
    op.create_index(op.f("ix_child_runs_scheduler_run_ref_id"), "child_runs", ["scheduler_run_ref_id"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_child_runs_scheduler_run_ref_id"), table_name="child_runs")
    op.drop_index(op.f("ix_child_runs_scheduler_run_id"), table_name="child_runs")
    op.drop_index(op.f("ix_child_runs_run_id"), table_name="child_runs")
    op.drop_index(op.f("ix_child_runs_plan_item_id"), table_name="child_runs")
    op.drop_index(op.f("ix_child_runs_plan_id"), table_name="child_runs")
    op.drop_index(op.f("ix_child_runs_id"), table_name="child_runs")
    op.drop_index(op.f("ix_child_runs_child_run_id"), table_name="child_runs")
    op.drop_index(op.f("ix_child_runs_child_execution_id"), table_name="child_runs")
    op.drop_table("child_runs")

    op.drop_index(op.f("ix_scheduler_runs_scheduler_run_id"), table_name="scheduler_runs")
    op.drop_index(op.f("ix_scheduler_runs_plan_item_id"), table_name="scheduler_runs")
    op.drop_index(op.f("ix_scheduler_runs_plan_id"), table_name="scheduler_runs")
    op.drop_index(op.f("ix_scheduler_runs_id"), table_name="scheduler_runs")
    op.drop_table("scheduler_runs")
