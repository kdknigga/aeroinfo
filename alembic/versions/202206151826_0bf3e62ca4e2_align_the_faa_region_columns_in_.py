"""Align the FAA region columns in airports and navaids so they match

Revision ID: 0bf3e62ca4e2
Revises: e479b66dc3fb
Create Date: 2022-06-15 18:26:48.328814+00:00

"""
import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision = "0bf3e62ca4e2"
down_revision = "e479b66dc3fb"
branch_labels = None
depends_on = None


def upgrade():
    bind = op.get_bind()
    if bind.engine.name == "postgresql":
        op.alter_column(
            "airports",
            "region",
            existing_type=sa.VARCHAR(length=3),
            type_=sa.Enum(
                "AAL",
                "ACE",
                "AEA",
                "AGL",
                "AIN",
                "ANE",
                "ANM",
                "ASO",
                "ASW",
                "AWP",
                name="faaregionenum",
            ),
            existing_nullable=True,
            postgresql_using="region::faaregionenum",
        )
    op.alter_column("navaids", "faa_region", new_column_name="region")


def downgrade():
    bind = op.get_bind()
    op.alter_column("navaids", "region", new_column_name="faa_region")
    if bind.engine.name == "postgresql":
        op.alter_column(
            "airports",
            "region",
            existing_type=sa.Enum(
                "AAL",
                "ACE",
                "AEA",
                "AGL",
                "AIN",
                "ANE",
                "ANM",
                "ASO",
                "ASW",
                "AWP",
                name="faaregionenum",
            ),
            type_=sa.VARCHAR(length=3),
            existing_nullable=True,
        )
