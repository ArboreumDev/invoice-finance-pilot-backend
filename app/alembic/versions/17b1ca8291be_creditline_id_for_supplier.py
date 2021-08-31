"""creditline ID for supplier

Revision ID: 17b1ca8291be
Revises: 120ee536ad0f
Create Date: 2021-08-30 13:11:35.510771

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '17b1ca8291be'
down_revision = '120ee536ad0f'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('supplier', sa.Column('creditline_id', sa.String(length=50), nullable=True))
    op.add_column('supplier', sa.Column('data', sa.Text(), nullable=True))
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('supplier', 'data')
    op.drop_column('supplier', 'creditline_id')
    # ### end Alembic commands ###
