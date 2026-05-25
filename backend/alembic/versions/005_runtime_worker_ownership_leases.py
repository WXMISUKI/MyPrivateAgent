"""add runtime worker ownership leases

Revision ID: 005
Revises: 004
Create Date: 2026-05-23
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "005"
down_revision: Union[str, None] = "004"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "runtime_worker_ownership_leases",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("run_id", sa.String(length=120), nullable=False),
        sa.Column("worker_id", sa.String(length=120), nullable=False),
        sa.Column("lease_id", sa.String(length=160), nullable=False),
        sa.Column("fencing_token", sa.Integer(), nullable=False),
        sa.Column("lease_status", sa.String(length=50), nullable=False),
        sa.Column("claimed_at", sa.DateTime(), nullable=False),
        sa.Column("lease_expires_at", sa.DateTime(), nullable=False),
        sa.Column("last_heartbeat_at", sa.DateTime(), nullable=False),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=True),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_runtime_worker_ownership_leases_id"), "runtime_worker_ownership_leases", ["id"], unique=False)
    op.create_index(op.f("ix_runtime_worker_ownership_leases_run_id"), "runtime_worker_ownership_leases", ["run_id"], unique=True)
    op.create_index(op.f("ix_runtime_worker_ownership_leases_worker_id"), "runtime_worker_ownership_leases", ["worker_id"], unique=False)
    op.create_index(op.f("ix_runtime_worker_ownership_leases_lease_id"), "runtime_worker_ownership_leases", ["lease_id"], unique=False)
    op.create_index(
        op.f("ix_runtime_worker_ownership_leases_lease_expires_at"),
        "runtime_worker_ownership_leases",
        ["lease_expires_at"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_runtime_worker_ownership_leases_lease_expires_at"), table_name="runtime_worker_ownership_leases")
    op.drop_index(op.f("ix_runtime_worker_ownership_leases_lease_id"), table_name="runtime_worker_ownership_leases")
    op.drop_index(op.f("ix_runtime_worker_ownership_leases_worker_id"), table_name="runtime_worker_ownership_leases")
    op.drop_index(op.f("ix_runtime_worker_ownership_leases_run_id"), table_name="runtime_worker_ownership_leases")
    op.drop_index(op.f("ix_runtime_worker_ownership_leases_id"), table_name="runtime_worker_ownership_leases")
    op.drop_table("runtime_worker_ownership_leases")
