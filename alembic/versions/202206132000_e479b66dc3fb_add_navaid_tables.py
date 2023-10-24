"""Add navaid tables

Revision ID: e479b66dc3fb
Revises: 88479bf118a1
Create Date: 2022-06-13 20:00:17.546076+00:00

"""
import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision = "e479b66dc3fb"
down_revision = "88479bf118a1"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "navaids",
        sa.Column("facility_id", sa.String(length=4), nullable=False),
        sa.Column("facility_type", sa.String(length=20), nullable=False),
        sa.Column("official_facility_id", sa.String(length=4), nullable=True),
        sa.Column("effective_date", sa.Date(), nullable=True),
        sa.Column("name", sa.String(length=30), nullable=True),
        sa.Column("city", sa.String(length=40), nullable=False),
        sa.Column("state_name", sa.String(length=30), nullable=True),
        sa.Column("state_code", sa.String(length=2), nullable=True),
        sa.Column(
            "faa_region",
            sa.Enum(
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
            nullable=True,
        ),
        sa.Column("country", sa.String(length=30), nullable=True),
        sa.Column("country_code", sa.String(length=2), nullable=True),
        sa.Column("owners_name", sa.String(length=50), nullable=True),
        sa.Column("operators_name", sa.String(length=50), nullable=True),
        sa.Column("common_system_usage", sa.String(length=1), nullable=True),
        sa.Column("public_use", sa.String(length=1), nullable=True),
        sa.Column("navaid_class", sa.String(length=11), nullable=True),
        sa.Column("hours_of_operation", sa.String(length=11), nullable=True),
        sa.Column("high_altitude_artcc_id", sa.String(length=4), nullable=True),
        sa.Column("high_altitude_artcc_name", sa.String(length=30), nullable=True),
        sa.Column("low_altitude_artcc_id", sa.String(length=4), nullable=True),
        sa.Column("low_altitude_artcc_name", sa.String(length=30), nullable=True),
        sa.Column("latitude_dms", sa.String(length=14), nullable=True),
        sa.Column("latitude_secs", sa.String(length=11), nullable=True),
        sa.Column("longitude_dms", sa.String(length=14), nullable=True),
        sa.Column("longitude_secs", sa.String(length=11), nullable=True),
        sa.Column(
            "coords_survey_accuracy",
            sa.Enum(
                "ZERO",
                "ONE",
                "TWO",
                "THREE",
                "FOUR",
                "FIVE",
                "SIX",
                "SEVEN",
                name="navaidpositionsurveyaccuracyenum",
            ),
            nullable=True,
        ),
        sa.Column("tacan_only_latitude_dms", sa.String(length=14), nullable=True),
        sa.Column("tacan_only_latitude_secs", sa.String(length=11), nullable=True),
        sa.Column("tacan_only_longitude_dms", sa.String(length=14), nullable=True),
        sa.Column("tacan_only_longitude_secs", sa.String(length=11), nullable=True),
        sa.Column("elevation", sa.Float(precision=1), nullable=True),
        sa.Column("mag_variation", sa.String(length=5), nullable=True),
        sa.Column("mag_variation_year", sa.Integer(), nullable=True),
        sa.Column(
            "simultaneous_voice",
            sa.Enum("Y", "N", "NULL", name="yesnonullenum"),
            nullable=True,
        ),
        sa.Column("power_output_watts", sa.Integer(), nullable=True),
        sa.Column(
            "automatic_voice_id",
            sa.Enum("Y", "N", "NULL", name="yesnonullenum"),
            nullable=True,
        ),
        sa.Column(
            "monitoring_category",
            sa.Enum(
                "ONE",
                "TWO",
                "THREE",
                "FOUR",
                name="navaidmonitoringcategoryenum",
            ),
            nullable=True,
        ),
        sa.Column("radio_voice_call_name", sa.String(length=30), nullable=True),
        sa.Column("tacan_channel", sa.String(length=4), nullable=True),
        sa.Column("frequency", sa.String(length=6), nullable=True),
        sa.Column("transmitted_id", sa.String(length=24), nullable=True),
        sa.Column(
            "fan_marker_type",
            sa.Enum("BONE", "ELLIPTICAL", name="fanmarkertypeenum"),
            nullable=True,
        ),
        sa.Column("fan_marker_true_bearing", sa.Integer(), nullable=True),
        sa.Column(
            "vor_service_volume",
            sa.Enum(
                "T",
                "L",
                "H",
                "VH",
                "VL",
                "DH",
                "DL",
                name="standardservicevolumeenum",
            ),
            nullable=True,
        ),
        sa.Column(
            "dme_service_volume",
            sa.Enum(
                "T",
                "L",
                "H",
                "VH",
                "VL",
                "DH",
                "DL",
                name="standardservicevolumeenum",
            ),
            nullable=True,
        ),
        sa.Column(
            "low_altitude_facility_used_in_high_structure",
            sa.Enum("Y", "N", "NULL", name="yesnonullenum"),
            nullable=True,
        ),
        sa.Column(
            "z_marker_available",
            sa.Enum("Y", "N", "NULL", name="yesnonullenum"),
            nullable=True,
        ),
        sa.Column("tweb_hours", sa.String(length=9), nullable=True),
        sa.Column("tweb_phone_number", sa.String(length=20), nullable=True),
        sa.Column("fss_id", sa.String(length=4), nullable=True),
        sa.Column("fss_name", sa.String(length=30), nullable=True),
        sa.Column("fss_hours_of_operation", sa.String(length=100), nullable=True),
        sa.Column("notam_accountability_code", sa.String(length=4), nullable=True),
        sa.Column(
            "quadrant_id_and_range_leg_bearing",
            sa.String(length=16),
            nullable=True,
        ),
        sa.Column("navaid_status", sa.String(length=30), nullable=True),
        sa.Column(
            "pitch",
            sa.Enum("Y", "N", "NULL", name="yesnonullenum"),
            nullable=True,
        ),
        sa.Column(
            "catch",
            sa.Enum("Y", "N", "NULL", name="yesnonullenum"),
            nullable=True,
        ),
        sa.Column(
            "sua_atcaa",
            sa.Enum("Y", "N", "NULL", name="yesnonullenum"),
            nullable=True,
        ),
        sa.Column(
            "navaid_restriction",
            sa.Enum("Y", "N", "NULL", name="yesnonullenum"),
            nullable=True,
        ),
        sa.Column(
            "hiwas",
            sa.Enum("Y", "N", "NULL", name="yesnonullenum"),
            nullable=True,
        ),
        sa.Column(
            "tweb",
            sa.Enum("Y", "N", "NULL", name="yesnonullenum"),
            nullable=True,
        ),
        sa.PrimaryKeyConstraint("facility_id", "facility_type"),
    )
    op.create_table(
        "navaid_airspace_fixes",
        sa.Column("facility_id", sa.String(length=4), nullable=False),
        sa.Column("facility_type", sa.String(length=20), nullable=False),
        sa.Column("fix", sa.String(length=36), nullable=False),
        sa.Column("more_fixes", sa.String(length=720), nullable=True),
        sa.ForeignKeyConstraint(
            ["facility_id", "facility_type"],
            ["navaids.facility_id", "navaids.facility_type"],
        ),
        sa.PrimaryKeyConstraint("facility_id", "facility_type", "fix"),
    )
    op.create_table(
        "navaid_fan_markers",
        sa.Column("facility_id", sa.String(length=4), nullable=False),
        sa.Column("facility_type", sa.String(length=20), nullable=False),
        sa.Column("fan_marker", sa.String(length=30), nullable=False),
        sa.Column("more_fan_markers", sa.String(length=690), nullable=True),
        sa.ForeignKeyConstraint(
            ["facility_id", "facility_type"],
            ["navaids.facility_id", "navaids.facility_type"],
        ),
        sa.PrimaryKeyConstraint("facility_id", "facility_type", "fan_marker"),
    )
    op.create_table(
        "navaid_holding_patterns",
        sa.Column("facility_id", sa.String(length=4), nullable=False),
        sa.Column("facility_type", sa.String(length=20), nullable=False),
        sa.Column("holding_pattern", sa.String(length=80), nullable=False),
        sa.Column("holding_pattern_pattern", sa.String(length=3), nullable=True),
        sa.Column("more_holding_patterns", sa.String(length=664), nullable=True),
        sa.ForeignKeyConstraint(
            ["facility_id", "facility_type"],
            ["navaids.facility_id", "navaids.facility_type"],
        ),
        sa.PrimaryKeyConstraint("facility_id", "facility_type", "holding_pattern"),
    )
    op.create_table(
        "navaid_remarks",
        sa.Column("facility_id", sa.String(length=4), nullable=False),
        sa.Column("facility_type", sa.String(length=20), nullable=False),
        sa.Column("remark", sa.String(length=600), nullable=False),
        sa.ForeignKeyConstraint(
            ["facility_id", "facility_type"],
            ["navaids.facility_id", "navaids.facility_type"],
        ),
        sa.PrimaryKeyConstraint("facility_id", "facility_type", "remark"),
    )
    op.create_table(
        "navaid_vor_receiver_checkpoints",
        sa.Column("facility_id", sa.String(length=4), nullable=False),
        sa.Column("facility_type", sa.String(length=20), nullable=False),
        sa.Column(
            "air_ground",
            sa.Enum("A", "G", "G1", name="vorreceivercheckpointairgroundcodeenum"),
            nullable=False,
        ),
        sa.Column("bearing", sa.Integer(), nullable=False),
        sa.Column("altitude", sa.Integer(), nullable=True),
        sa.Column("airport_id", sa.String(length=4), nullable=True),
        sa.Column("state", sa.String(length=2), nullable=True),
        sa.Column("air_narrative", sa.String(length=75), nullable=True),
        sa.Column("ground_narrative", sa.String(length=75), nullable=True),
        sa.ForeignKeyConstraint(
            ["facility_id", "facility_type"],
            ["navaids.facility_id", "navaids.facility_type"],
        ),
        sa.PrimaryKeyConstraint(
            "facility_id", "facility_type", "air_ground", "bearing"
        ),
    )


def downgrade():
    op.drop_table("navaid_vor_receiver_checkpoints")
    op.drop_table("navaid_remarks")
    op.drop_table("navaid_holding_patterns")
    op.drop_table("navaid_fan_markers")
    op.drop_table("navaid_airspace_fixes")
    op.drop_table("navaids")
