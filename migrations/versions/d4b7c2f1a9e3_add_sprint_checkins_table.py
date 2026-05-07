"""add sprint checkins table

Revision ID: d4b7c2f1a9e3
Revises: bcffa5f26224
Create Date: 2026-05-04 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "d4b7c2f1a9e3"
down_revision = "bcffa5f26224"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "sprint_checkins",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("sprint_id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("checkin_date", sa.Date(), nullable=False),
        sa.Column("confidence_level", sa.Integer(), nullable=False),
        sa.Column("workload_level", sa.Integer(), nullable=False),
        sa.Column("blockers", sa.Text(), nullable=True),
        sa.Column("needs_help", sa.Boolean(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["sprint_id"], ["sprints.id"]),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "sprint_id",
            "user_id",
            "checkin_date",
            name="uq_sprint_user_checkin_date"
        )
    )


def downgrade():
    op.drop_table("sprint_checkins")
