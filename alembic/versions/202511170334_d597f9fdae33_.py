"""
Empty message.

Revision ID: d597f9fdae33
Revises: 618d19385afc
Create Date: 2025-11-17 03:34:55.077865+00:00

"""

from alembic import op

# revision identifiers, used by Alembic.
revision = "d597f9fdae33"
down_revision = "618d19385afc"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create composite indexes to speed up common lookup paths."""
    # Create indexes. Use CONCURRENTLY on Postgres to avoid blocking writes.
    bind = op.get_bind()
    if bind.engine.name == "postgresql":
        with op.get_context().autocommit_block():
            op.execute(
                "CREATE INDEX CONCURRENTLY IF NOT EXISTS ix_airports_faa_effective ON airports (faa_id, effective_date DESC)"
            )
            op.execute(
                "CREATE INDEX CONCURRENTLY IF NOT EXISTS ix_airports_icao_effective ON airports (icao_id, effective_date DESC)"
            )
            op.execute(
                "CREATE INDEX CONCURRENTLY IF NOT EXISTS ix_navaids_ident_type_effective ON navaids (facility_id, facility_type, effective_date DESC)"
            )
            op.execute(
                "CREATE INDEX CONCURRENTLY IF NOT EXISTS ix_runway_ends_facility_name_id ON runway_ends (facility_site_number, runway_name, id)"
            )
    else:
        op.create_index(
            "ix_airports_faa_effective",
            "airports",
            ["faa_id", "effective_date"],
        )
        op.create_index(
            "ix_airports_icao_effective",
            "airports",
            ["icao_id", "effective_date"],
        )
        op.create_index(
            "ix_navaids_ident_type_effective",
            "navaids",
            ["facility_id", "facility_type", "effective_date"],
        )
        op.create_index(
            "ix_runway_ends_facility_name_id",
            "runway_ends",
            ["facility_site_number", "runway_name", "id"],
        )

    # ### end Alembic commands ###


def downgrade() -> None:
    """
    Revert the schema changes applied in :func:`upgrade`.

    Drops the created indexes.
    """
    bind = op.get_bind()
    # Drop indexes concurrently on Postgres to avoid blocking DDL locks.
    if bind.engine.name == "postgresql":
        with op.get_context().autocommit_block():
            op.execute(
                "DROP INDEX CONCURRENTLY IF EXISTS ix_runway_ends_facility_name_id"
            )
            op.execute(
                "DROP INDEX CONCURRENTLY IF EXISTS ix_navaids_ident_type_effective"
            )
            op.execute("DROP INDEX CONCURRENTLY IF EXISTS ix_airports_icao_effective")
            op.execute("DROP INDEX CONCURRENTLY IF EXISTS ix_airports_faa_effective")
    else:
        op.drop_index("ix_runway_ends_facility_name_id", table_name="runway_ends")
        op.drop_index("ix_navaids_ident_type_effective", table_name="navaids")
        op.drop_index("ix_airports_icao_effective", table_name="airports")
        op.drop_index("ix_airports_faa_effective", table_name="airports")

    # ### end Alembic commands ###
