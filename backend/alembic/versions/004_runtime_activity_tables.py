"""add background and worktree runtime tables

Revision ID: 004
Revises: 003
Create Date: 2026-05-05
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "004"
down_revision: Union[str, None] = "003"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "background_runs",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("background_run_id", sa.String(length=120), nullable=False),
        sa.Column("plan_id", sa.Integer(), nullable=False),
        sa.Column("plan_item_id", sa.Integer(), nullable=False),
        sa.Column("run_id", sa.String(length=120), nullable=True),
        sa.Column("parent_run_id", sa.String(length=120), nullable=True),
        sa.Column("scheduler_run_id", sa.String(length=120), nullable=True),
        sa.Column("status", sa.String(length=50), nullable=False),
        sa.Column("source", sa.String(length=100), nullable=True),
        sa.Column("event_type", sa.String(length=100), nullable=True),
        sa.Column("title", sa.String(length=255), nullable=True),
        sa.Column("detail", sa.Text(), nullable=True),
        sa.Column("artifact_id", sa.String(length=120), nullable=True),
        sa.Column("artifact_kind", sa.String(length=100), nullable=True),
        sa.Column("metadata", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=True),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=True),
        sa.Column("started_at", sa.DateTime(), nullable=True),
        sa.Column("completed_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["plan_id"], ["plan_runs.id"]),
        sa.ForeignKeyConstraint(["plan_item_id"], ["plan_items.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_background_runs_id"), "background_runs", ["id"], unique=False)
    op.create_index(op.f("ix_background_runs_background_run_id"), "background_runs", ["background_run_id"], unique=True)
    op.create_index(op.f("ix_background_runs_plan_id"), "background_runs", ["plan_id"], unique=False)
    op.create_index(op.f("ix_background_runs_plan_item_id"), "background_runs", ["plan_item_id"], unique=False)
    op.create_index(op.f("ix_background_runs_run_id"), "background_runs", ["run_id"], unique=False)
    op.create_index(op.f("ix_background_runs_scheduler_run_id"), "background_runs", ["scheduler_run_id"], unique=False)
    op.create_index(op.f("ix_background_runs_artifact_id"), "background_runs", ["artifact_id"], unique=False)

    op.create_table(
        "worktree_runs",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("worktree_run_id", sa.String(length=120), nullable=False),
        sa.Column("plan_id", sa.Integer(), nullable=False),
        sa.Column("plan_item_id", sa.Integer(), nullable=False),
        sa.Column("run_id", sa.String(length=120), nullable=True),
        sa.Column("parent_run_id", sa.String(length=120), nullable=True),
        sa.Column("scheduler_run_id", sa.String(length=120), nullable=True),
        sa.Column("status", sa.String(length=50), nullable=False),
        sa.Column("source", sa.String(length=100), nullable=True),
        sa.Column("event_type", sa.String(length=100), nullable=True),
        sa.Column("workspace_path", sa.String(length=500), nullable=True),
        sa.Column("branch_name", sa.String(length=255), nullable=True),
        sa.Column("detail", sa.Text(), nullable=True),
        sa.Column("metadata", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=True),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=True),
        sa.Column("started_at", sa.DateTime(), nullable=True),
        sa.Column("completed_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["plan_id"], ["plan_runs.id"]),
        sa.ForeignKeyConstraint(["plan_item_id"], ["plan_items.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_worktree_runs_id"), "worktree_runs", ["id"], unique=False)
    op.create_index(op.f("ix_worktree_runs_worktree_run_id"), "worktree_runs", ["worktree_run_id"], unique=True)
    op.create_index(op.f("ix_worktree_runs_plan_id"), "worktree_runs", ["plan_id"], unique=False)
    op.create_index(op.f("ix_worktree_runs_plan_item_id"), "worktree_runs", ["plan_item_id"], unique=False)
    op.create_index(op.f("ix_worktree_runs_run_id"), "worktree_runs", ["run_id"], unique=False)
    op.create_index(op.f("ix_worktree_runs_scheduler_run_id"), "worktree_runs", ["scheduler_run_id"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_worktree_runs_scheduler_run_id"), table_name="worktree_runs")
    op.drop_index(op.f("ix_worktree_runs_run_id"), table_name="worktree_runs")
    op.drop_index(op.f("ix_worktree_runs_plan_item_id"), table_name="worktree_runs")
    op.drop_index(op.f("ix_worktree_runs_plan_id"), table_name="worktree_runs")
    op.drop_index(op.f("ix_worktree_runs_worktree_run_id"), table_name="worktree_runs")
    op.drop_index(op.f("ix_worktree_runs_id"), table_name="worktree_runs")
    op.drop_table("worktree_runs")

    op.drop_index(op.f("ix_background_runs_artifact_id"), table_name="background_runs")
    op.drop_index(op.f("ix_background_runs_scheduler_run_id"), table_name="background_runs")
    op.drop_index(op.f("ix_background_runs_run_id"), table_name="background_runs")
    op.drop_index(op.f("ix_background_runs_plan_item_id"), table_name="background_runs")
    op.drop_index(op.f("ix_background_runs_plan_id"), table_name="background_runs")
    op.drop_index(op.f("ix_background_runs_background_run_id"), table_name="background_runs")
    op.drop_index(op.f("ix_background_runs_id"), table_name="background_runs")
    op.drop_table("background_runs")
