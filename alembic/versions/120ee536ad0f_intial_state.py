"""intial state

Revision ID: 120ee536ad0f
Revises: 
Create Date: 2021-07-28 15:10:44.902848

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '120ee536ad0f'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('invoice',
    sa.Column('id', sa.String(length=50), nullable=False),
    sa.Column('order_ref', sa.String(length=50), nullable=False),
    sa.Column('supplier_id', sa.String(length=50), nullable=False),
    sa.Column('purchaser_id', sa.String(length=50), nullable=False),
    sa.Column('shipment_status', sa.String(length=50), nullable=True),
    sa.Column('finance_status', sa.String(length=50), nullable=True),
    sa.Column('apr', sa.Float(), nullable=True),
    sa.Column('tenor_in_days', sa.Integer(), nullable=True),
    sa.Column('data', sa.Text(), nullable=False),
    sa.Column('value', sa.Float(), nullable=True),
    sa.Column('payment_details', sa.Text(), nullable=True),
    sa.Column('delivered_on', sa.DateTime(), nullable=True),
    sa.Column('financed_on', sa.DateTime(), nullable=True),
    sa.Column('updated_on', sa.DateTime(), nullable=True),
    sa.Column('created_on', sa.DateTime(), nullable=True),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('supplier',
    sa.Column('supplier_id', sa.String(length=50), nullable=False),
    sa.Column('name', sa.String(length=50), nullable=False),
    sa.Column('creditline_size', sa.Integer(), nullable=False),
    sa.Column('default_apr', sa.Float(), nullable=True),
    sa.Column('default_tenor_in_days', sa.Integer(), nullable=True),
    sa.PrimaryKeyConstraint('supplier_id')
    )
    op.create_table('users',
    sa.Column('user_id', sa.Integer(), autoincrement=True, nullable=False),
    sa.Column('email', sa.String(length=50), nullable=False),
    sa.Column('username', sa.String(length=50), nullable=False),
    sa.Column('hashed_password', sa.String(length=64), nullable=False),
    sa.Column('role', sa.String(length=50), nullable=False),
    sa.PrimaryKeyConstraint('user_id', 'email'),
    sa.UniqueConstraint('email'),
    sa.UniqueConstraint('username')
    )
    op.create_table('whitelist',
    sa.Column('supplier_id', sa.String(length=50), nullable=False),
    sa.Column('purchaser_id', sa.String(length=50), nullable=False),
    sa.Column('location_id', sa.String(length=50), nullable=False),
    sa.Column('name', sa.String(length=50), nullable=False),
    sa.Column('phone', sa.String(length=50), nullable=False),
    sa.Column('city', sa.String(length=50), nullable=False),
    sa.Column('creditline_size', sa.Integer(), nullable=False),
    sa.Column('apr', sa.Float(), nullable=True),
    sa.Column('tenor_in_days', sa.Integer(), nullable=True),
    sa.PrimaryKeyConstraint('supplier_id', 'purchaser_id')
    )
    op.create_index(op.f('ix_whitelist_location_id'), 'whitelist', ['location_id'], unique=False)
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_index(op.f('ix_whitelist_location_id'), table_name='whitelist')
    op.drop_table('whitelist')
    op.drop_table('users')
    op.drop_table('supplier')
    op.drop_table('invoice')
    # ### end Alembic commands ###