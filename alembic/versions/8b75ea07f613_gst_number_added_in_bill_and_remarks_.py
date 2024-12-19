"""gst_number added in bill and remarks added in expense table

Revision ID: 8b75ea07f613
Revises: 7191f4a57234
Create Date: 2024-12-20 00:27:34.785901

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '8b75ea07f613'
down_revision: Union[str, None] = '7191f4a57234'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('bill', sa.Column('gst_bill_number', sa.String(), nullable=True))
    op.add_column('expence', sa.Column('remarks', sa.String(), nullable=True))
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('expence', 'remarks')
    op.drop_column('bill', 'gst_bill_number')
    # ### end Alembic commands ###