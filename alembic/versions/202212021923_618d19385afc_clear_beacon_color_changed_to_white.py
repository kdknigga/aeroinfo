"""CLEAR beacon color changed to WHITE

Revision ID: 618d19385afc
Revises: 0bf3e62ca4e2
Create Date: 2022-12-02 19:23:34.125444+00:00

"""
from alembic import op

# revision identifiers, used by Alembic.
revision = "618d19385afc"
down_revision = "0bf3e62ca4e2"
branch_labels = None
depends_on = None


def upgrade():
    bind = op.get_bind()
    if bind.engine.name == "postgresql":
        with op.get_context().autocommit_block():
            op.execute("ALTER TYPE beaconcolorenum RENAME VALUE 'CG' TO 'WG'")
            op.execute("ALTER TYPE beaconcolorenum RENAME VALUE 'CY' TO 'WY'")
            op.execute("ALTER TYPE beaconcolorenum RENAME VALUE 'CGY' TO 'WGY'")
            op.execute("ALTER TYPE beaconcolorenum RENAME VALUE 'SCG' TO 'SWG'")
            op.execute("ALTER TYPE beaconcolorenum RENAME VALUE 'C' TO 'W'")


def downgrade():
    bind = op.get_bind()
    if bind.engine.name == "postgresql":
        with op.get_context().autocommit_block():
            op.execute("ALTER TYPE beaconcolorenum RENAME VALUE 'WG' TO 'CG'")
            op.execute("ALTER TYPE beaconcolorenum RENAME VALUE 'WY' TO 'CY'")
            op.execute("ALTER TYPE beaconcolorenum RENAME VALUE 'WGY' TO 'CGY'")
            op.execute("ALTER TYPE beaconcolorenum RENAME VALUE 'SWG' TO 'SCG'")
            op.execute("ALTER TYPE beaconcolorenum RENAME VALUE 'W' TO 'C'")
