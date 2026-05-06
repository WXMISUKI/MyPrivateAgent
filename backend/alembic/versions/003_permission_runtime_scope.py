"""add runtime scope columns to permission requests

Revision ID: 003
Revises: 002
Create Date: 2026-05-05
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "003"
down_revision: Union[str, None] = "002"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("permission_requests", sa.Column("plan_id", sa.Integer(), nullable=True))
    op.add_column("permission_requests", sa.Column("plan_item_id", sa.Integer(), nullable=True))
    op.add_column("permission_requests", sa.Column("run_id", sa.String(length=120), nullable=True))
    op.add_column("permission_requests", sa.Column("parent_run_id", sa.String(length=120), nullable=True))
    op.add_column("permission_requests", sa.Column("child_run_id", sa.String(length=120), nullable=True))
    op.add_column("permission_requests", sa.Column("scheduler_run_id", sa.String(length=120), nullable=True))
    op.add_column("permission_requests", sa.Column("run_kind", sa.String(length=50), nullable=True))
    op.add_column("permission_requests", sa.Column("metadata", sa.JSON(), nullable=True))

    op.create_foreign_key(
        "fk_permission_requests_plan_id_plan_runs",
        "permission_requests",
        "plan_runs",
        ["plan_id"],
        ["id"],
    )
    op.create_foreign_key(
        "fk_permission_requests_plan_item_id_plan_items",
        "permission_requests",
        "plan_items",
        ["plan_item_id"],
        ["id"],
    )

    op.create_index(op.f("ix_permission_requests_plan_id"), "permission_requests", ["plan_id"], unique=False)
    op.create_index(op.f("ix_permission_requests_plan_item_id"), "permission_requests", ["plan_item_id"], unique=False)
    op.create_index(op.f("ix_permission_requests_run_id"), "permission_requests", ["run_id"], unique=False)
    op.create_index(op.f("ix_permission_requests_child_run_id"), "permission_requests", ["child_run_id"], unique=False)
    op.create_index(op.f("ix_permission_requests_scheduler_run_id"), "permission_requests", ["scheduler_run_id"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_permission_requests_scheduler_run_id"), table_name="permission_requests")
    op.drop_index(op.f("ix_permission_requests_child_run_id"), table_name="permission_requests")
    op.drop_index(op.f("ix_permission_requests_run_id"), table_name="permission_requests")
    op.drop_index(op.f("ix_permission_requests_plan_item_id"), table_name="permission_requests")
    op.drop_index(op.f("ix_permission_requests_plan_id"), table_name="permission_requests")

    op.drop_constraint("fk_permission_requests_plan_item_id_plan_items", "permission_requests", type_="foreignkey")
    op.drop_constraint("fk_permission_requests_plan_id_plan_runs", "permission_requests", type_="foreignkey")

    op.drop_column("permission_requests", "metadata")
    op.drop_column("permission_requests", "run_kind")
    op.drop_column("permission_requests", "scheduler_run_id")
    op.drop_column("permission_requests", "child_run_id")
    op.drop_column("permission_requests", "parent_run_id")
    op.drop_column("permission_requests", "run_id")
    op.drop_column("permission_requests", "plan_item_id")
    op.drop_column("permission_requests", "plan_id")
