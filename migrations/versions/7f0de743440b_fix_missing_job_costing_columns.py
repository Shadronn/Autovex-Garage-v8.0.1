"""Fix missing job costing columns

Revision ID: REPLACE_WITH_GENERATED_REVISION
Revises: 8c3881a36ee0
"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "REPLACE_WITH_GENERATED_REVISION"
down_revision = "8c3881a36ee0"
branch_labels = None
depends_on = None


def upgrade():

    # =====================================================
    # JOB CARD PART COSTING
    # =====================================================

    op.add_column(
        "job_card_part",
        sa.Column(
            "unit_cost",
            sa.Float(),
            nullable=False,
            server_default="0"
        )
    )

    op.add_column(
        "job_card_part",
        sa.Column(
            "cost_total",
            sa.Float(),
            nullable=False,
            server_default="0"
        )
    )

    # =====================================================
    # JOB CARD LABOUR COSTING
    # =====================================================

    op.add_column(
        "job_card_labour",
        sa.Column(
            "hourly_cost",
            sa.Float(),
            nullable=False,
            server_default="0"
        )
    )

    op.add_column(
        "job_card_labour",
        sa.Column(
            "cost_total",
            sa.Float(),
            nullable=False,
            server_default="0"
        )
    )


def downgrade():

    op.drop_column(
        "job_card_labour",
        "cost_total"
    )

    op.drop_column(
        "job_card_labour",
        "hourly_cost"
    )

    op.drop_column(
        "job_card_part",
        "cost_total"
    )

    op.drop_column(
        "job_card_part",
        "unit_cost"
    )