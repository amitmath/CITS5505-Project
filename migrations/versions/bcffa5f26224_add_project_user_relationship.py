"""add project user relationship

Revision ID: bcffa5f26224
Revises: 999d990b49d1
Create Date: 2026-05-04 14:37:23.788471

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'bcffa5f26224'
down_revision = '999d990b49d1'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "project_users",
        sa.Column("project_id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("role", sa.String(length=80), nullable=True),
        sa.Column("assigned_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["project_id"], ["projects.id"]),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("project_id", "user_id")
    )


def downgrade():
    op.drop_table("project_users")
