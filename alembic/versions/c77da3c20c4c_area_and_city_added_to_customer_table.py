"""area and city added to customer table

Revision ID: c77da3c20c4c
Revises: f54fcf7fcbcf
Create Date: 2024-10-31 13:58:41.858881

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'c77da3c20c4c'
down_revision: Union[str, None] = 'f54fcf7fcbcf'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('customers', sa.Column('area', sa.Integer(), nullable=True))
    op.add_column('customers', sa.Column('city', sa.Integer(), nullable=True))
    op.create_foreign_key(None, 'customers', 'city', ['city'], ['id'], ondelete='CASCADE')
    op.create_foreign_key(None, 'customers', 'area', ['area'], ['id'], ondelete='CASCADE')
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_constraint(None, 'customers', type_='foreignkey')
    op.drop_constraint(None, 'customers', type_='foreignkey')
    op.drop_column('customers', 'city')
    op.drop_column('customers', 'area')
    # ### end Alembic commands ###
