"""Add job costing fields

Revision ID: 8c3881a36ee0
Revises: 5a7fb81313ea
Create Date: 2026-09-03 13:25:34.736809

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '8c3881a36ee0'
down_revision = '5a7fb81313ea'
branch_labels = None
depends_on = None


def upgrade():

    # =====================================================
    # JOB CARD PART COSTING
    # =====================================================

    with op.batch_alter_table('job_card_part', schema=None) as batch_op:

        batch_op.add_column(
            sa.Column(
                'unit_cost',
                sa.Float(),
                nullable=False,
                server_default='0'
            )
        )

        batch_op.add_column(
            sa.Column(
                'cost_total',
                sa.Float(),
                nullable=False,
                server_default='0'
            )
        )


    # =====================================================
    # JOB CARD LABOUR COSTING
    # =====================================================

    with op.batch_alter_table('job_card_labour', schema=None) as batch_op:

        batch_op.add_column(
            sa.Column(
                'hourly_cost',
                sa.Float(),
                nullable=False,
                server_default='0'
            )
        )

        batch_op.add_column(
            sa.Column(
                'cost_total',
                sa.Float(),
                nullable=False,
                server_default='0'
            )
        )


def downgrade():

    # =====================================================
    # REMOVE JOB CARD LABOUR COSTING
    # =====================================================

    with op.batch_alter_table('job_card_labour', schema=None) as batch_op:

        batch_op.drop_column('cost_total')
        batch_op.drop_column('hourly_cost')


    # =====================================================
    # REMOVE JOB CARD PART COSTING
    # =====================================================

    with op.batch_alter_table('job_card_part', schema=None) as batch_op:

        batch_op.drop_column('cost_total')
        batch_op.drop_column('unit_cost')