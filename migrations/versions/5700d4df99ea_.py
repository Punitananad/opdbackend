"""empty message

Revision ID: 5700d4df99ea
Revises: edefacb5d9f7
Create Date: 2024-08-30 14:33:04.268226

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '5700d4df99ea'
down_revision = 'edefacb5d9f7'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('beddb', schema=None) as batch_op:
        batch_op.alter_column('floor_id',
               existing_type=sa.INTEGER(),
               nullable=True)

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('beddb', schema=None) as batch_op:
        batch_op.alter_column('floor_id',
               existing_type=sa.INTEGER(),
               nullable=False)

    # ### end Alembic commands ###
